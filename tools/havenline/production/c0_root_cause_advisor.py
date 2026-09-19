#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import re
import subprocess
import time
import urllib.error
import urllib.request
from typing import Any

from lib import ROOT, DOCS, load_json

CLASSES={
    "PRODUCT_DEFECT","TOOLING_DEFECT","GOVERNANCE_DEFECT","EVIDENCE_DEFECT",
    "INFRASTRUCTURE_FAILURE","SUPERSEDED","MIXED",
}
BLOCKER_CLASSES=CLASSES-{"MIXED"}
ACTIONS={"REPAIR","RETRY_INFRA","NO_PRODUCT_CHANGE","FREEZE_AND_VALIDATE","BLOCKED"}
C0_CONTEXT_TOKENS=16384
C0_MAX_TOKENS=2200
C0_SAFETY_TOKENS=512
# Every tokenizer token represents at least one input byte. Keeping the complete
# serialized request below this byte ceiling is therefore a conservative,
# tokenizer-independent upper bound that leaves both completion and safety
# reserves inside the pinned context window.
C0_MAX_REQUEST_BYTES=C0_CONTEXT_TOKENS-C0_MAX_TOKENS-C0_SAFETY_TOKENS
FAIL_CONCLUSIONS={"failure","timed_out","cancelled","action_required","startup_failure"}
TERMINAL_SIGNAL_RE=re.compile(r'(?i)(projected(?: device)? readability failed|assertionerror|assert(?:ion)? failed|script error|parse error|traceback|fatal(?: error)?|runtime error|process completed with exit code [1-9]|"passed"\\s*:\\s*false)')
C0_DIAGNOSTIC_JOB_MARKERS=("c0 diagnosis after failed","c0 non-voting root-cause diagnosis","c0 root-cause advisor")
ANSI_RE=re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
SIGNAL_RE=re.compile(r"(?i)(critic|score|defect|error|fail|fatal|traceback|assert|coverage|confidence|timeout|exceed|blocked|unexecuted)")


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


def stable_json_digest(value:Any)->str:
    raw=json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
    return hashlib.sha256(raw).hexdigest()


def bounded_lines(text:str,limit:int)->dict:
    """Retain whole informative lines and explicit omission metadata."""
    raw=text.encode("utf-8",errors="replace")
    lines=[];used=0
    for source in text.splitlines():
        line=ANSI_RE.sub("",source).strip()
        if not line or not SIGNAL_RE.search(line):continue
        encoded=line.encode("utf-8",errors="replace")
        if used+len(encoded)+1>limit:continue
        lines.append(line);used+=len(encoded)+1
    return {
        "source_bytes":len(raw),"source_sha256":hashlib.sha256(raw).hexdigest(),
        "retained_lines":lines,"retained_bytes":used,
        "truncated":used<len(raw),
    }


def terminal_bounded_lines(text:str,limit:int)->dict:
    """Prioritize the latest terminal failure signal and its local source context."""
    raw=text.encode("utf-8",errors="replace")
    source=[]
    for line_number,raw_line in enumerate(text.splitlines(),1):
        line=ANSI_RE.sub("",raw_line).strip()
        if line:
            source.append((line_number,line))
    terminal=[index for index,(_,line) in enumerate(source) if TERMINAL_SIGNAL_RE.search(line)]
    if not terminal:
        fallback=bounded_lines(text,limit)
        fallback["selection_policy"]="generic_signal_fallback"
        fallback["terminal_signal_count"]=0
        return fallback
    selected=[];seen=set()
    # Start with the latest terminal region because CI logs often contain earlier
    # negative fixtures or setup noise that are not the terminal cause.
    for index in reversed(terminal):
        window=[index]
        window.extend(range(max(0,index-3),index))
        window.extend(range(index+1,min(len(source),index+5)))
        for item in window:
            if item not in seen:
                seen.add(item);selected.append(item)
    lines=[];used=0
    for index in selected:
        _,line=source[index]
        encoded=line.encode("utf-8",errors="replace")
        if used+len(encoded)+1>limit:
            continue
        lines.append(line);used+=len(encoded)+1
    return {
        "source_bytes":len(raw),"source_sha256":hashlib.sha256(raw).hexdigest(),
        "retained_lines":lines,"retained_bytes":used,"truncated":used<len(raw),
        "selection_policy":"latest_terminal_signal_windows_first",
        "terminal_signal_count":len(terminal),
    }


def compact_failure_records(packet:dict,detail:int=2)->list[dict]:
    rows=packet.get("structured_failure_records",[])
    if not isinstance(rows,list):return []
    compact=[]
    for row in rows:
        if not isinstance(row,dict):continue
        source_groups=row.get("groups",[]) if isinstance(row.get("groups"),list) else []
        groups=[];group_counts={}
        for group in source_groups:
            if not isinstance(group,dict):continue
            disposition="pass" if group.get("passed") is True else "fail"
            group_counts[disposition]=group_counts.get(disposition,0)+1
            if group.get("passed") is True:continue
            group_row={
                "group":group.get("group"),"passed":group.get("passed"),
                "lowest_score":group.get("lowest_score"),
            }
            if detail:group_row["errors"]=group.get("errors",[])
            groups.append(group_row)
        record={
            "path":row.get("path"),"sha256":row.get("sha256"),"bytes":row.get("bytes"),
            "critic_id":row.get("critic_id"),
            "candidate_hash":row.get("candidate_hash"),"passed":row.get("passed"),
            "scores":row.get("scores",{}),"defects":row.get("defects",[]),
            "coverage_complete":row.get("coverage_complete"),"confidence":row.get("confidence"),
            "fatal_error":row.get("fatal_error"),"group_count":len(source_groups),
            "group_dispositions":group_counts,"groups_sha256":stable_json_digest(source_groups),
            "failed_groups":groups,
        }
        if detail==0:
            for key in ("path","bytes","candidate_hash","group_count","group_dispositions","groups_sha256"):record.pop(key,None)
        compact.append(record)
    return compact


def compact_paths(paths:Any,detail:int=2)->dict:
    rows=[str(path) for path in paths] if isinstance(paths,list) else []
    def priority(path:str)->tuple:
        order=("HavenlineGodot/scripts/","HavenlineGodot/data/","HavenlineGodot/assets/world_transform_v1/","tools/havenline/task","tools/havenline/production/","HavenlineGodot/tests/",".github/workflows/","Docs/")
        return (next((i for i,prefix in enumerate(order) if path.startswith(prefix)),len(order)),path)
    retained=sorted(rows,key=priority)[:({2:10,1:5}.get(detail,0))]
    omitted=sorted(set(rows)-set(retained))
    roots={}
    for path in rows:
        root=path.split("/",1)[0];roots[root]=roots.get(root,0)+1
    return {"count":len(rows),"all_paths_sha256":stable_json_digest(rows),"root_counts":roots,
            "diagnostic_paths":retained,"omitted_count":len(omitted),"omitted_paths_sha256":stable_json_digest(omitted)}


def compact_history(value:Any,detail:int=2)->dict:
    if not isinstance(value,dict):return {}
    rows=[]
    for match in value.get("matches",[]) if isinstance(value.get("matches"),list) else []:
        if not isinstance(match,dict):continue
        keys=("id","classification","root_cause") if detail else ("id","classification")
        rows.append({key:match.get(key) for key in keys})
    return {"matches":rows,"historical_match_is_advisory_only":value.get("historical_match_is_advisory_only")}


def _artifact_diagnostic_priority(row:dict)->tuple:
    """Rank exact terminal evidence ahead of generic successful context."""
    lines=row.get("retained_lines",[]) if isinstance(row.get("retained_lines"),list) else []
    terminal=sum(
        1 for item in lines
        if isinstance(item,dict) and TERMINAL_SIGNAL_RE.search(str(item.get("text","")))
    )
    path=str(row.get("path") or "").lower()
    terminal_path=any(token in path for token in ("capture.log","integration.log","benchmark.log","domain.log","import.log"))
    return (-terminal,0 if terminal_path else 1,path)


def artifact_diagnostic_projection(packet:dict,excerpt_bytes:int,detail:int)->dict:
    value=packet.get("artifact_diagnostics",{})
    rows=value.get("records",[]) if isinstance(value,dict) else []
    limit=max(512,excerpt_bytes*2);used=0;retained=[]
    row_limit={2:8,1:4,0:2}.get(detail,2)
    ordered=sorted((row for row in rows if isinstance(row,dict)),key=_artifact_diagnostic_priority)
    for row in ordered[:row_limit]:
        source_lines=row.get("retained_lines",[]) if isinstance(row.get("retained_lines"),list) else []
        ordered_lines=sorted(
            (item for item in source_lines if isinstance(item,dict)),
            key=lambda item:(0 if TERMINAL_SIGNAL_RE.search(str(item.get("text",""))) else 1,str(item.get("line",""))),
        )
        lines=[]
        for item in ordered_lines:
            text=str(item.get("text", ""));size=len(text.encode("utf-8",errors="replace"))+32
            if not text or used+size>limit:continue
            lines.append({"line":item.get("line"),"text":text});used+=size
        if lines:
            retained.append({"path":row.get("path"),"bytes":row.get("bytes"),"sha256":row.get("sha256"),"retained_lines":lines})
    return {
        "record_count":value.get("record_count",len(rows)) if isinstance(value,dict) else 0,
        "records_sha256":stable_json_digest(rows),"records":retained,
        "retained_bytes":used,"truncated":len(retained)<len(rows),
        "selection_policy":"terminal_signal_first_then_diagnostic_path",
        "terminal_evidence_priority":True,
    }


def _is_c0_diagnostic_job(name:Any)->bool:
    normalized=str(name or "").strip().lower()
    return any(marker in normalized for marker in C0_DIAGNOSTIC_JOB_MARKERS)


def subject_execution(packet:dict)->tuple[list[dict],list[str],list[str]]:
    """Exclude the live C0 advisory job from the failed subject's execution picture."""
    source_steps=packet.get("steps",[])
    steps=[];excluded_jobs=set()
    for row in source_steps if isinstance(source_steps,list) else []:
        if not isinstance(row,dict):continue
        name=str(row.get("job") or "unknown")
        if _is_c0_diagnostic_job(name):
            excluded_jobs.add(name);continue
        steps.append(row)
    source_unexecuted=packet.get("unexecuted_checks",[])
    unexecuted=[]
    for item in source_unexecuted if isinstance(source_unexecuted,list) else []:
        text=str(item)
        job=text.split(":",1)[0].strip()
        if _is_c0_diagnostic_job(job):
            excluded_jobs.add(job);continue
        unexecuted.append(text)
    return steps,unexecuted,sorted(excluded_jobs)


def failure_log_projection(packet:dict,excerpt_bytes:int)->dict:
    value=packet.get("failed_logs","")
    if not isinstance(value,str):value=""
    raw=value.encode("utf-8",errors="replace")
    projection={
        "envelope_bytes":len(raw),"envelope_sha256":hashlib.sha256(raw).hexdigest(),
        "declared_bytes":packet.get("failed_logs_bytes"),
        "declared_sha256":packet.get("failed_logs_sha256"),"valid_envelope":False,"jobs":[],
    }
    if projection["declared_bytes"] is not None and projection["declared_bytes"]!=len(raw):
        raise ValueError("failed log envelope byte count mismatch")
    if projection["declared_sha256"] is not None and projection["declared_sha256"]!=projection["envelope_sha256"]:
        raise ValueError("failed log envelope digest mismatch")
    try:envelope=json.loads(value)
    except Exception:
        projection["legacy_truncated_excerpt"]=bounded_lines(value,excerpt_bytes)
        return projection
    if not isinstance(envelope,dict) or not isinstance(envelope.get("jobs"),list):
        raise ValueError("invalid failed log envelope")
    projection["valid_envelope"]=True
    projection["run_id"]=envelope.get("run_id")
    projection["run_status"]=envelope.get("run_status")
    projection["run_conclusion"]=envelope.get("run_conclusion")
    projection["diagnostic_marker"]=envelope.get("diagnostic_marker")
    for job in envelope["jobs"]:
        if not isinstance(job,dict):raise ValueError("invalid failed log job")
        raw_log=job.get("raw_log","")
        if not isinstance(raw_log,str):raise ValueError("invalid failed log text")
        projection["jobs"].append({
            "job_id":job.get("job_id"),"name":job.get("name"),"conclusion":job.get("conclusion"),
            "log_bytes":job.get("log_bytes"),"log_sha256":job.get("log_sha256"),
            "excerpt":terminal_bounded_lines(raw_log,excerpt_bytes),
        })
    return projection


def model_projection(packet:dict,packet_sha256:str,excerpt_bytes:int=640,detail:int=2)->dict:
    all_steps=packet.get("steps",[])
    steps,unexecuted,excluded_diagnostic_jobs=subject_execution(packet)
    failed=[];jobs={};counts={}
    for row in steps:
        if not isinstance(row,dict):continue
        conclusion=row.get("conclusion")
        counts[str(conclusion)]=counts.get(str(conclusion),0)+1
        name=str(row.get("job") or "unknown")
        summary=jobs.setdefault(name,{"step_count":0,"conclusions":{}})
        summary["step_count"]+=1;summary["conclusions"][str(conclusion)]=summary["conclusions"].get(str(conclusion),0)+1
        if conclusion in FAIL_CONCLUSIONS:failed.append(row)
    changed=packet.get("changed_files",[])
    protected=packet.get("protected_files",[])
    scope=str(packet.get("task_scope") or "")
    ledger=str(packet.get("defect_ledger") or "")
    history=packet.get("historical_failure_intelligence",{})
    return {
        "schema_version":1,
        "identity":{key:packet.get(key) for key in ("task_id","failed_run_id","failed_candidate","integration_head","integration_branch","task_branch","current_branch_head","run_conclusion","run_status","workflow_name","event")},
        "source_bindings":{
            "failure_packet_sha256":packet_sha256,
            "steps_sha256":stable_json_digest(all_steps),"subject_steps_sha256":stable_json_digest(steps),"changed_files_sha256":stable_json_digest(changed),
            "protected_files_sha256":stable_json_digest(protected),"task_scope_sha256":hashlib.sha256(scope.encode()).hexdigest(),
            "defect_ledger_sha256":hashlib.sha256(ledger.encode()).hexdigest(),"historical_failure_intelligence_sha256":stable_json_digest(history),
        },
        "execution":{
            "step_count":len(steps),"packet_step_count":len(all_steps) if isinstance(all_steps,list) else 0,
            "step_disposition_counts":counts,"all_steps_sha256":stable_json_digest(all_steps),"subject_steps_sha256":stable_json_digest(steps),
            "failed_terminal_steps":failed,"job_dispositions":jobs,
            "unexecuted_checks":unexecuted,
            "excluded_diagnostic_jobs":excluded_diagnostic_jobs,
        },
        "change_surface":{"changed_files":compact_paths(changed,detail),"protected_files":compact_paths(protected,detail)},
        "structured_failure_records":compact_failure_records(packet,detail),
        "failure_logs":failure_log_projection(packet,excerpt_bytes),
        "artifact_diagnostics":artifact_diagnostic_projection(packet,excerpt_bytes,detail),
        "task_scope_excerpt":bounded_lines(scope,excerpt_bytes),
        "defect_ledger_excerpt":bounded_lines(ledger,excerpt_bytes),
        "historical_failure_intelligence":compact_history(history,detail),
        "projection_contract":{
            "authoritative_packet_preserved_separately":True,"semantic_json_only":True,
            "arbitrary_character_slice_used":False,"all_failed_terminal_steps_retained":True,
            "all_unexecuted_checks_retained":True,"complete_change_surface_bound_by_digest":True,
            "bounded_excerpts_have_source_hash_and_truncation_metadata":True,
            "artifact_diagnostics_are_source_hashed":True,
            "terminal_artifact_evidence_prioritized":True,
            "terminal_job_log_evidence_prioritized":True,
            "c0_advisory_job_excluded_from_subject_execution":True,
            "historical_failure_intelligence_is_advisory_only":True,
        },
    }


def build_model_request(packet:dict,packet_sha256:str,prompt:str,schema:dict)->tuple[dict,bytes,dict,dict]:
    last=None
    for excerpt_bytes,detail in ((640,2),(320,1),(0,0)):
        projection=model_projection(packet,packet_sha256,excerpt_bytes,detail)
        content=prompt+"\n\nFAILURE PACKET MODEL PROJECTION:\n"+json.dumps(projection,sort_keys=True,separators=(",",":"),ensure_ascii=False)
        body={"model":"havenline-c0-local","messages":[{"role":"user","content":content}],"max_tokens":C0_MAX_TOKENS,"temperature":0.1,"top_p":0.9,"seed":20260917,"chat_template_kwargs":{"enable_thinking":False},"response_format":{"type":"json_object","schema":schema},"cache_prompt":False}
        request_bytes=json.dumps(body,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
        budget={
            "context_tokens":C0_CONTEXT_TOKENS,"max_completion_tokens":C0_MAX_TOKENS,
            "safety_tokens":C0_SAFETY_TOKENS,"request_bytes":len(request_bytes),
            "max_request_bytes":C0_MAX_REQUEST_BYTES,"token_upper_bound":len(request_bytes),
            "within_budget":len(request_bytes)<=C0_MAX_REQUEST_BYTES,"excerpt_bytes_per_source":excerpt_bytes,
            "request_sha256":hashlib.sha256(request_bytes).hexdigest(),"projection_detail":detail,
        }
        last=(body,request_bytes,budget,projection)
        if budget["within_budget"]:return last
    raise RuntimeError("C0_REQUEST_BUDGET_EXCEEDED "+json.dumps(last[2],sort_keys=True))


def retain_http_error(exc:urllib.error.HTTPError,out:pathlib.Path)->None:
    limit=8192;body=exc.read(limit+1);kept=body[:limit]
    allowed={"content-type","content-length","retry-after","server","date"}
    headers={str(k).lower():str(v) for k,v in exc.headers.items() if str(k).lower() in allowed} if exc.headers else {}
    report={
        "status":exc.code,"reason":str(exc.reason),"headers":headers,
        "body_bytes_retained":len(kept),"body_truncated":len(body)>limit,
        "body_sha256_retained":hashlib.sha256(kept).hexdigest(),
        "body":kept.decode("utf-8",errors="replace"),
    }
    (out/"http-error.json").write_text(json.dumps(report,indent=2)+"\n")


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
    strict_grounding=packet.get("strict_evidence_grounding") is True
    repository_paths=set(packet.get("repository_paths",[])) if isinstance(packet.get("repository_paths"),list) else set()
    grounding={
        "failure_logs":ANSI_RE.sub("",str(packet.get("failed_logs", ""))),
        "task_scope":str(packet.get("task_scope", "")),
        "defect_ledger":str(packet.get("defect_ledger", "")),
        "historical_failure_intelligence":json.dumps(packet.get("historical_failure_intelligence",{}),sort_keys=True),
    }
    for item in packet.get("structured_failure_records",[]) if isinstance(packet.get("structured_failure_records"),list) else []:
        if isinstance(item,dict) and item.get("path"):
            grounding["structured_failure_records:"+str(item["path"])]=json.dumps(item,sort_keys=True)
    diagnostics=packet.get("artifact_diagnostics",{})
    for item in diagnostics.get("records",[]) if isinstance(diagnostics,dict) and isinstance(diagnostics.get("records"),list) else []:
        if not isinstance(item,dict) or not item.get("path"):continue
        for line in item.get("retained_lines",[]) if isinstance(item.get("retained_lines"),list) else []:
            if isinstance(line,dict):grounding[f"artifact_diagnostics:{item['path']}#L{line.get('line')}"]=str(line.get("text", ""))
    for row in blockers:
        rid=row.get("id")
        if not rid or rid in seen:errors.append("blocker ids must be unique/non-empty")
        seen.add(rid)
        missing=set(schema["required_blocker_fields"])-set(row)
        if missing:errors.append(f"{rid or 'blocker'} missing fields: "+",".join(sorted(missing)))
        if row.get("classification") not in BLOCKER_CLASSES:errors.append(f"{rid} invalid classification")
        for key in ("evidence","files_to_change","files_not_to_change","verification"):
            if not isinstance(row.get(key),list):errors.append(f"{rid} {key} must be list")
        if strict_grounding:
            for evidence in row.get("evidence",[]) if isinstance(row.get("evidence"),list) else []:
                if not isinstance(evidence,str) or " | " not in evidence:
                    errors.append(f"{rid} evidence lacks source-bound quote");continue
                source,quote=evidence.split(" | ",1)
                if source not in grounding or len(quote.strip())<8 or quote not in grounding.get(source,""):
                    errors.append(f"{rid} evidence is not an exact retained source excerpt: {source}")
            for path in row.get("files_to_change",[]) if isinstance(row.get("files_to_change"),list) else []:
                if path not in repository_paths:errors.append(f"{rid} proposed causal file is not an exact repository path: {path}")
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


def c0_response_schema(strict_grounding:bool=False)->dict:
    evidence_item={"type":"string"}
    if strict_grounding:
        evidence_item["pattern"]=r"^(failure_logs|task_scope|defect_ledger|historical_failure_intelligence|artifact_diagnostics:[^|]+|structured_failure_records:[^|]+) \| .{8,}$"
    blocker_props={
        "id":{"type":"string"},"classification":{"type":"string","enum":sorted(BLOCKER_CLASSES)},"symptom":{"type":"string"},
        "evidence":{"type":"array","items":evidence_item,"minItems":1,"maxItems":8},"root_cause":{"type":"string"},"affected_object":{"type":"string"},
        "causal_fix":{"type":"string"},"files_to_change":{"type":"array","items":{"type":"string"},"maxItems":20},"files_not_to_change":{"type":"array","items":{"type":"string"},"maxItems":20},
        "verification":{"type":"array","items":{"type":"string"},"minItems":1,"maxItems":12},
    }
    return {"type":"object","properties":{
        "diagnosis_status":{"type":"string","enum":["DIAGNOSIS_COMPLETE","INSUFFICIENT_EVIDENCE"]},
        "terminal_class":{"type":"string","enum":sorted(CLASSES)},"complete_known_blocker_set":{"type":"boolean"},
        "blockers":{"type":"array","items":{"type":"object","properties":blocker_props,"required":list(blocker_props),"additionalProperties":False},"maxItems":12},
        "unexecuted_checks":{"type":"array","items":{"type":"string"},"maxItems":20},"builder_action":{"type":"string","enum":sorted(ACTIONS)},
        "summary":{"type":"string"},"confidence":{"type":"string","enum":["low","medium","high"]}
    },"required":["diagnosis_status","terminal_class","complete_known_blocker_set","blockers","unexecuted_checks","builder_action","summary","confidence"],"additionalProperties":False}


def model_report(packet:dict,out:pathlib.Path,packet_sha256:str)->dict:
    if os.environ.get("HAVENLINE_C0_INDEPENDENT_JOB")!="1":raise SystemExit("C0 model diagnosis must run in its separately declared advisory job")
    proc=log=manifest=None
    try:
        proc,log,manifest=start_runtime(out)
        strict_grounding=packet.get("strict_evidence_grounding") is True
        schema=c0_response_schema(strict_grounding)
        prompt="""You are C0, Havenline's non-voting Root-Cause Advisor. Diagnose the complete available failed run before any builder changes code. Do not score gameplay and do not approve the task. Distinguish PRODUCT_DEFECT, TOOLING_DEFECT, GOVERNANCE_DEFECT, EVIDENCE_DEFECT, INFRASTRUCTURE_FAILURE and SUPERSEDED. A red CI state is not a diagnosis. Inspect successful upstream steps as evidence too. Return every currently observable independent blocker, not only the first red line. Mark downstream steps that never executed as unexecuted_checks; do not invent their results. Protect already-approved work: if a harness/test/governance defect is supported and the product is not disproven, explicitly keep the approved production files in files_not_to_change. For every blocker give concrete evidence, root cause, smallest causal fix, exact files_to_change/files_not_to_change and dependency-ordered verification. Prefer a complete blocker set over serial symptom fixing. If evidence is insufficient, say so rather than guessing. Candidate validation must use finish_running_sha: a newer commit queues and does not cancel the running SHA."""
        if strict_grounding:
            prompt += " Every evidence item must be SOURCE | EXACT_QUOTE using an exact retained source label and verbatim excerpt from the projection. Never infer an empty collection from a populated one. Every files_to_change value must be an exact path from repository_paths; if the source does not support a causal repair, return INSUFFICIENT_EVIDENCE instead of inventing a path."
        try:body,request_bytes,budget,projection=build_model_request(packet,packet_sha256,prompt,schema)
        except RuntimeError as exc:
            diagnostic={"passed":False,"error":"request_budget_exceeded","detail":str(exc),"context_tokens":C0_CONTEXT_TOKENS,"max_completion_tokens":C0_MAX_TOKENS,"safety_tokens":C0_SAFETY_TOKENS,"max_request_bytes":C0_MAX_REQUEST_BYTES}
            (out/"request-budget.json").write_text(json.dumps(diagnostic,indent=2)+"\n")
            raise
        (out/"model-projection.json").write_text(json.dumps(projection,sort_keys=True,separators=(",",":"),ensure_ascii=False))
        (out/"request-budget.json").write_text(json.dumps(budget,indent=2)+"\n")
        (out/"request.json").write_bytes(request_bytes)
        req=urllib.request.Request("http://127.0.0.1:8080/v1/chat/completions",data=request_bytes,headers={"Content-Type":"application/json"},method="POST")
        try:
            with urllib.request.urlopen(req,timeout=1200) as response:raw=json.load(response)
        except urllib.error.HTTPError as exc:
            retain_http_error(exc,out)
            raise RuntimeError(f"C0 model request HTTP {exc.code}; retained http-error.json") from exc
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
    packet_sha256=digest(packet_path)
    report=superseded_report(packet) if packet.get("run_conclusion")=="cancelled" else model_report(packet,out,packet_sha256)
    errors=validate_report(report,packet);report["validation_errors"]=errors;report["validated"]=not errors;report["input_packet_sha256"]=digest(packet_path)
    path=out/"c0-report.json";path.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))
    return 0 if not errors else 2

if __name__=="__main__":raise SystemExit(main())
