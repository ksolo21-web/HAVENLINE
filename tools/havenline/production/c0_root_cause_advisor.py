#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import subprocess
import time
import urllib.request
from typing import Any

from lib import ROOT, DOCS, load_json

CLASSES={
    "PRODUCT_DEFECT","TOOLING_DEFECT","GOVERNANCE_DEFECT","EVIDENCE_DEFECT",
    "INFRASTRUCTURE_FAILURE","SUPERSEDED","MIXED",
}
BLOCKER_CLASSES=CLASSES-{"MIXED"}
ACTIONS={"REPAIR","RETRY_INFRA","NO_PRODUCT_CHANGE","FREEZE_AND_VALIDATE","BLOCKED"}


def digest(path:pathlib.Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda:stream.read(4*1024*1024),b""):
            h.update(block)
    return h.hexdigest()


def load_packet(path:pathlib.Path)->dict:
    data=json.loads(path.read_text())
    required={"task_id","failed_run_id","failed_candidate","integration_head","run_conclusion","steps","changed_files"}
    missing=required-set(data)
    if missing:raise SystemExit("C0 packet missing: "+",".join(sorted(missing)))
    if not isinstance(data["failed_run_id"],int) or data["failed_run_id"]<=0:raise SystemExit("invalid failed_run_id")
    for key in ("failed_candidate","integration_head"):
        if not isinstance(data[key],str) or len(data[key])!=40:raise SystemExit(key+" must be exact 40-char commit")
    if not isinstance(data["steps"],list) or not isinstance(data["changed_files"],list):raise SystemExit("invalid packet collections")
    return data


def validate_report(report:dict,packet:dict)->list[str]:
    schema=load_json(DOCS/"C0_REPORT_SCHEMA.json");errors=[]
    required=set(schema["required_report_fields"])
    if not required<=set(report):errors.append("missing report fields: "+",".join(sorted(required-set(report))))
    if report.get("schema_version")!=1 or report.get("critic_id")!="C0" or report.get("non_voting") is not True:errors.append("C0 identity/non-voting contract invalid")
    if report.get("task_id")!=packet["task_id"] or report.get("failed_candidate")!=packet["failed_candidate"] or report.get("failed_run_id")!=packet["failed_run_id"] or report.get("integration_head")!=packet["integration_head"]:errors.append("C0 report source binding mismatch")
    if report.get("diagnosis_status") not in schema["diagnosis_status_values"]:errors.append("invalid diagnosis_status")
    if report.get("terminal_class") not in CLASSES:errors.append("invalid terminal_class")
    if report.get("builder_action") not in ACTIONS:errors.append("invalid builder_action")
    if report.get("confidence") not in ("low","medium","high"):errors.append("invalid confidence")
    blockers=report.get("blockers",[])
    if not isinstance(blockers,list):errors.append("blockers must be list");blockers=[]
    seen=set()
    for row in blockers:
        rid=row.get("id")
        if not rid or rid in seen:errors.append("blocker ids must be unique/non-empty")
        seen.add(rid)
        missing=set(schema["required_blocker_fields"])-set(row)
        if missing:errors.append(f"{rid or 'blocker'} missing fields: "+",".join(sorted(missing)))
        if row.get("classification") not in BLOCKER_CLASSES:errors.append(f"{rid} invalid classification")
        for key in ("evidence","files_to_change","files_not_to_change","verification"):
            if not isinstance(row.get(key),list):errors.append(f"{rid} {key} must be list")
        if row.get("classification") in {"TOOLING_DEFECT","GOVERNANCE_DEFECT","EVIDENCE_DEFECT","INFRASTRUCTURE_FAILURE","SUPERSEDED"} and row.get("affected_object","").lower().startswith("shipping product") and not row.get("evidence"):
            errors.append(f"{rid} unsupported product attribution")
    freeze=report.get("candidate_freeze",{})
    if freeze.get("required") is not True or freeze.get("validation_concurrency_policy")!="finish_running_sha" or freeze.get("cancelled_run_product_judgment") is not False:errors.append("candidate freeze contract invalid")
    if report.get("diagnosis_status")=="DIAGNOSIS_COMPLETE":
        if report.get("complete_known_blocker_set") is not True:errors.append("complete diagnosis must declare complete_known_blocker_set")
        if report.get("confidence") not in ("medium","high"):errors.append("complete diagnosis requires medium/high confidence")
        if packet.get("run_conclusion") not in ("success","cancelled") and not blockers:errors.append("failed run complete diagnosis requires at least one blocker")
    if report.get("terminal_class")=="SUPERSEDED" and report.get("builder_action") not in {"FREEZE_AND_VALIDATE","NO_PRODUCT_CHANGE"}:errors.append("superseded run cannot authorize product repair")
    return errors


def superseded_report(packet:dict)->dict:
    current=packet.get("current_branch_head")
    moved=isinstance(current,str) and len(current)==40 and current!=packet["failed_candidate"]
    reason="newer branch SHA superseded the validation" if moved else "validation was cancelled before a product judgment completed"
    return {
        "schema_version":1,"critic_id":"C0","non_voting":True,
        "diagnosis_id":f"C0-{packet['task_id']}-{packet['failed_run_id']}",
        "task_id":packet["task_id"],"failed_candidate":packet["failed_candidate"],"failed_run_id":packet["failed_run_id"],"integration_head":packet["integration_head"],
        "diagnosis_status":"DIAGNOSIS_COMPLETE","terminal_class":"SUPERSEDED","complete_known_blocker_set":True,
        "blockers":[{
            "id":"C0-B001","classification":"SUPERSEDED","symptom":"Validation ended as cancelled before all mandatory gates completed.",
            "evidence":[f"workflow conclusion={packet.get('run_conclusion')}",f"failed candidate={packet['failed_candidate']}",f"current branch head={current or 'unknown'}"],
            "root_cause":reason,"affected_object":"validation orchestration, not shipping product",
            "causal_fix":"Allow the frozen SHA to finish validation; queue newer candidates instead of cancelling the running judgment.",
            "files_to_change":[],"files_not_to_change":packet.get("protected_files",[]),
            "verification":["Run the exact frozen SHA to a terminal validation conclusion.","Do not interpret this cancelled run as a product or critic failure."]
        }],
        "unexecuted_checks":[str(x) for x in packet.get("unexecuted_checks",[])],
        "builder_action":"FREEZE_AND_VALIDATE","candidate_freeze":{"required":True,"validation_concurrency_policy":"finish_running_sha","cancelled_run_product_judgment":False},
        "summary":reason+" No product change is authorized from this run alone.","confidence":"high"
    }


def start_runtime(out:pathlib.Path):
    execution=load_json(DOCS/"CRITIC_EXECUTION.json");runtime=execution["local_independent_runtime"]
    cache=pathlib.Path(os.path.expanduser(os.environ.get("HAVENLINE_SPECIALIST_CACHE",runtime["cache_path"])))
    manifest=json.loads((cache/"manifest.json").read_text())
    if manifest.get("publisher")!=runtime["provider"] or manifest.get("base_model")!=runtime["base_model"] or manifest.get("revision")!=runtime["model_revision"]:raise SystemExit("C0 reviewer runtime identity mismatch")
    for item in manifest["files"]:
        if digest(cache/item["filename"])!=item["sha256"]:raise SystemExit("C0 reviewer runtime hash mismatch "+item["filename"])
    servers=list((cache/"runtime").rglob("llama-server"))
    if len(servers)!=1:raise SystemExit("exact llama-server runtime not found")
    server=servers[0];env=dict(os.environ);env["LD_LIBRARY_PATH"]=str(server.parent)+":"+env.get("LD_LIBRARY_PATH","")
    log=(out/"runtime.log").open("w")
    cmd=[str(server),"-m",str(cache/manifest["model_file"]),"--mmproj",str(cache/manifest["projector_file"]),"--host","127.0.0.1","--port","8080","-c","16384","-t","4","-tb","4","-ngl","0","--no-mmproj-offload","--parallel","1","--jinja"]
    proc=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,env=env)
    for _ in range(180):
        if proc.poll() is not None:raise RuntimeError("C0 local reviewer runtime exited")
        try:
            with urllib.request.urlopen("http://127.0.0.1:8080/health",timeout=3) as response:
                if json.load(response).get("status")=="ok":return proc,log,manifest
        except Exception:pass
        time.sleep(2)
    raise RuntimeError("C0 local reviewer runtime not ready")


def model_report(packet:dict,out:pathlib.Path)->dict:
    if os.environ.get("HAVENLINE_C0_INDEPENDENT_JOB")!="1":raise SystemExit("C0 model diagnosis must run in its separately declared advisory job")
    proc=log=manifest=None
    try:
        proc,log,manifest=start_runtime(out)
        blocker_props={
            "id":{"type":"string"},"classification":{"type":"string","enum":sorted(BLOCKER_CLASSES)},"symptom":{"type":"string"},
            "evidence":{"type":"array","items":{"type":"string"},"minItems":1,"maxItems":8},"root_cause":{"type":"string"},"affected_object":{"type":"string"},
            "causal_fix":{"type":"string"},"files_to_change":{"type":"array","items":{"type":"string"},"maxItems":20},"files_not_to_change":{"type":"array","items":{"type":"string"},"maxItems":20},
            "verification":{"type":"array","items":{"type":"string"},"minItems":1,"maxItems":12},
        }
        schema={"type":"object","properties":{
            "diagnosis_status":{"type":"string","enum":["DIAGNOSIS_COMPLETE","INSUFFICIENT_EVIDENCE"]},
            "terminal_class":{"type":"string","enum":sorted(CLASSES)},"complete_known_blocker_set":{"type":"boolean"},
            "blockers":{"type":"array","items":{"type":"object","properties":blocker_props,"required":list(blocker_props),"additionalProperties":False},"maxItems":12},
            "unexecuted_checks":{"type":"array","items":{"type":"string"},"maxItems":20},"builder_action":{"type":"string","enum":sorted(ACTIONS)},
            "summary":{"type":"string"},"confidence":{"type":"string","enum":["low","medium","high"]}
        },"required":["diagnosis_status","terminal_class","complete_known_blocker_set","blockers","unexecuted_checks","builder_action","summary","confidence"],"additionalProperties":False}
        packet_text=json.dumps(packet,indent=2,sort_keys=True)
        prompt="""You are C0, Havenline's non-voting Root-Cause Advisor. Diagnose the complete available failed run before any builder changes code. Do not score gameplay and do not approve the task. Distinguish PRODUCT_DEFECT, TOOLING_DEFECT, GOVERNANCE_DEFECT, EVIDENCE_DEFECT, INFRASTRUCTURE_FAILURE and SUPERSEDED. A red CI state is not a diagnosis. Inspect successful upstream steps as evidence too. Return every currently observable independent blocker, not only the first red line. Mark downstream steps that never executed as unexecuted_checks; do not invent their results. Protect already-approved work: if a harness/test/governance defect is supported and the product is not disproven, explicitly keep the approved production files in files_not_to_change. For every blocker give concrete evidence, root cause, smallest causal fix, exact files_to_change/files_not_to_change and dependency-ordered verification. Prefer a complete blocker set over serial symptom fixing. If evidence is insufficient, say so rather than guessing. Candidate validation must use finish_running_sha: a newer commit queues and does not cancel the running SHA."""
        body={"model":"havenline-c0-local","messages":[{"role":"user","content":prompt+"\n\nFAILURE PACKET:\n"+packet_text[:60000]}],"max_tokens":2200,"temperature":0.1,"top_p":0.9,"seed":20260917,"chat_template_kwargs":{"enable_thinking":False},"response_format":{"type":"json_object","schema":schema},"cache_prompt":False}
        (out/"request.json").write_text(json.dumps(body,indent=2)[:250000])
        req=urllib.request.Request("http://127.0.0.1:8080/v1/chat/completions",data=json.dumps(body).encode(),headers={"Content-Type":"application/json"},method="POST")
        with urllib.request.urlopen(req,timeout=1200) as response:raw=json.load(response)
        (out/"raw-response.json").write_text(json.dumps(raw,indent=2))
        choice=raw["choices"][0]
        if choice.get("finish_reason")!="stop":raise RuntimeError("incomplete C0 response")
        core=json.loads(choice["message"]["content"])
        core.update({
            "schema_version":1,"critic_id":"C0","non_voting":True,"diagnosis_id":f"C0-{packet['task_id']}-{packet['failed_run_id']}",
            "task_id":packet["task_id"],"failed_candidate":packet["failed_candidate"],"failed_run_id":packet["failed_run_id"],"integration_head":packet["integration_head"],
            "candidate_freeze":{"required":True,"validation_concurrency_policy":"finish_running_sha","cancelled_run_product_judgment":False},
            "provider":manifest.get("publisher"),"model_revision":manifest.get("revision"),
        })
        return core
    finally:
        if proc is not None:
            proc.terminate()
            try:proc.wait(timeout=10)
            except Exception:proc.kill()
        if log is not None:log.close()


def main()->int:
    ap=argparse.ArgumentParser();ap.add_argument("--packet",required=True);ap.add_argument("--out",required=True);a=ap.parse_args()
    packet_path=(ROOT/a.packet).resolve();out=(ROOT/a.out).resolve();out.mkdir(parents=True,exist_ok=True)
    packet=load_packet(packet_path)
    report=superseded_report(packet) if packet.get("run_conclusion")=="cancelled" else model_report(packet,out)
    errors=validate_report(report,packet);report["validation_errors"]=errors;report["validated"]=not errors;report["input_packet_sha256"]=digest(packet_path)
    path=out/"c0-report.json";path.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))
    return 0 if not errors else 2

if __name__=="__main__":raise SystemExit(main())
