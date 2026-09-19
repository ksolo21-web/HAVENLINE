#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import os
import subprocess

from lib import ROOT, changed_files


def digest(path:pathlib.Path)->str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path:pathlib.Path)->dict:
    return json.loads(path.read_text())


def _inherited_noncausal(plan:dict)->list[str]:
    rows=plan.get("inherited_noncausal_files",[])
    return [str(path) for path in rows] if isinstance(rows,list) else []


def verify_inherited_noncausal(plan:dict,head:str,integration_head:str|None,read_ref=None,is_ancestor=None)->list[str]:
    inherited=_inherited_noncausal(plan)
    if not inherited:return []
    errors=[]
    source=plan.get("reconciled_integration_head")
    if not isinstance(source,str) or len(source)!=40:
        return ["inherited noncausal files require exact reconciled_integration_head"]
    if not isinstance(integration_head,str) or len(integration_head)!=40 or source!=integration_head:
        errors.append("reconciled integration head does not match active integration head")
    if read_ref is None:
        def read_ref(ref,path):
            return subprocess.check_output(["git","show",f"{ref}:{path}"])
    if is_ancestor is None:
        def is_ancestor(ancestor,descendant):
            return subprocess.run(["git","merge-base","--is-ancestor",ancestor,descendant],check=False).returncode==0
    if integration_head and not is_ancestor(source,head):
        errors.append("reconciled integration head is not an ancestor of repair candidate")
    for path in inherited:
        try:
            source_bytes=read_ref(source,path);head_bytes=read_ref(head,path)
        except Exception:
            errors.append("inherited noncausal file missing at integration/head: "+path);continue
        if source_bytes!=head_bytes:
            errors.append("inherited noncausal file differs from exact integration bytes: "+path)
    return errors


def validate(c0:dict,plan:dict,actual_changed:list[str]|None=None,actual_base:str|None=None)->list[str]:
    errors=[]
    task=c0.get("task_id")
    canonical_c0=f"Docs/Production/{task}/C0_ROOT_CAUSE.json"
    canonical_plan=f"Docs/Production/{task}/REPAIR_PLAN.json"
    bookkeeping={canonical_c0,canonical_plan}
    inherited=_inherited_noncausal(plan)
    if plan.get("inherited_noncausal_files",[]) is not None and not isinstance(plan.get("inherited_noncausal_files",[]),list):
        errors.append("inherited_noncausal_files must be list")
    if len(inherited)!=len(set(inherited)) or any(not path or path.startswith("/") or ".." in pathlib.PurePosixPath(path).parts for path in inherited):
        errors.append("inherited noncausal file paths must be unique safe repository paths")
    if inherited and (not isinstance(plan.get("reconciled_integration_head"),str) or len(plan.get("reconciled_integration_head"))!=40):
        errors.append("inherited noncausal files require exact reconciled_integration_head")
    if set(inherited)&bookkeeping:
        errors.append("canonical repair bookkeeping cannot be inherited noncausal")
    if plan.get("c0_report_path")!=canonical_c0 or plan.get("plan_path")!=canonical_plan:
        errors.append("canonical C0 and repair plan paths required")
    if c0.get("critic_id")!="C0" or c0.get("non_voting") is not True or c0.get("validated") is not True:
        errors.append("validated non-voting C0 report required")
    if c0.get("diagnosis_status")!="DIAGNOSIS_COMPLETE" or c0.get("complete_known_blocker_set") is not True:
        errors.append("C0 diagnosis is incomplete")
    if c0.get("terminal_class")=="SUPERSEDED":
        errors.append("superseded run does not authorize a repair candidate")
    if c0.get("builder_action") not in {"REPAIR","FREEZE_AND_VALIDATE"}:
        errors.append("C0 builder_action does not authorize code repair")
    if plan.get("schema_version")!=1 or plan.get("task_id")!=c0.get("task_id") or plan.get("failed_candidate")!=c0.get("failed_candidate"):
        errors.append("repair plan source/task binding mismatch")
    if plan.get("diagnosis_id")!=c0.get("diagnosis_id"):
        errors.append("repair plan diagnosis id mismatch")
    if plan.get("c0_report_sha256")!=c0.get("report_sha256"):
        errors.append("repair plan C0 hash mismatch")
    repair_base=plan.get("repair_base")
    if not isinstance(repair_base,str) or len(repair_base)!=40:
        errors.append("repair plan repair_base must be an exact 40-char SHA")
    if actual_base is not None and repair_base!=actual_base:
        errors.append("post-build validation base does not match repair plan repair_base")
    if plan.get("full_blocker_set_acknowledged") is not True:
        errors.append("repair plan must acknowledge full blocker set")
    if plan.get("candidate_freeze_after_build") is not True or plan.get("validation_concurrency_policy")!="finish_running_sha":
        errors.append("repair plan must freeze candidate and finish running SHA")
    fixes=plan.get("fixes",[])
    if not isinstance(fixes,list):errors.append("repair fixes must be list");fixes=[]
    blockers={b.get("id"):b for b in c0.get("blockers",[]) if b.get("id")}
    mapped={f.get("blocker_id") for f in fixes if f.get("blocker_id")}
    if mapped!=set(blockers):
        errors.append("repair plan must map every C0 blocker exactly once")
    if len(mapped)!=len(fixes):errors.append("duplicate or missing blocker mapping in repair fixes")
    must_not=set(plan.get("must_not_change",[]))|{p for b in blockers.values() for p in b.get("files_not_to_change",[])}
    allowed=set()
    for fix in fixes:
        bid=fix.get("blocker_id");blocker=blockers.get(bid,{})
        files=fix.get("files",[]);proof=fix.get("verification",[])
        if not isinstance(files,list) or not files:errors.append(f"{bid} repair files missing")
        if set(files)&bookkeeping:errors.append(f"{bid} bookkeeping cannot be causal files")
        causal_files=set(files)-bookkeeping
        if not causal_files:errors.append(f"{bid} non-bookkeeping causal files required")
        if not fix.get("causal_change"):errors.append(f"{bid} causal_change missing")
        if not isinstance(proof,list) or not proof:errors.append(f"{bid} verification missing")
        authorized=set(blocker.get("files_to_change",[]))
        if authorized and not set(files)<=authorized:errors.append(f"{bid} repair exceeds C0 files_to_change")
        if set(files)&must_not:errors.append(f"{bid} repair touches must_not_change")
        allowed.update(causal_files)
    inherited_set=set(inherited)
    if inherited_set&allowed:
        errors.append("inherited noncausal files cannot also be blocker causal files")
    blast=plan.get("blast_radius_checks",[])
    if not isinstance(blast,list) or not blast:errors.append("blast_radius_checks required")
    if actual_changed is not None:
        allowed_actual=set(allowed)|bookkeeping|set(inherited)
        extra=set(actual_changed)-allowed_actual
        if extra:errors.append("actual repair diff exceeds authorized surface: "+",".join(sorted(extra)))
        for fix in fixes:
            if not (set(fix.get("files",[]))-bookkeeping)&set(actual_changed):errors.append(f"{fix.get('blocker_id')} causal files did not change")
        touched=set(actual_changed)&must_not
        if touched:errors.append("actual repair changed protected files: "+",".join(sorted(touched)))
    return errors


def main()->int:
    ap=argparse.ArgumentParser();ap.add_argument("--c0",required=True);ap.add_argument("--plan",required=True);ap.add_argument("--base");ap.add_argument("--head",default="HEAD");ap.add_argument("--output");a=ap.parse_args()
    c0_path=(ROOT/a.c0).resolve();plan_path=(ROOT/a.plan).resolve();c0=load(c0_path);plan=load(plan_path)
    c0_copy=dict(c0);c0_copy["report_sha256"]=digest(c0_path)
    if "c0_report_sha256" not in plan:plan["c0_report_sha256"]=""
    actual=changed_files(a.base,a.head) if a.base else None
    errors=validate(c0_copy,plan,actual,a.base)
    inherited_errors=verify_inherited_noncausal(plan,a.head,os.environ.get("INTEGRATION_HEAD")) if actual is not None else []
    errors.extend(inherited_errors)
    result={"schema_version":1,"task_id":c0.get("task_id"),"diagnosis_id":c0.get("diagnosis_id"),"passed":not errors,"mode":"post-build" if actual is not None else "pre-build","repair_base":plan.get("repair_base"),"reconciled_integration_head":plan.get("reconciled_integration_head"),"inherited_noncausal_files":_inherited_noncausal(plan),"actual_changed_files":actual or [],"errors":errors}
    text=json.dumps(result,indent=2)+"\n"
    if a.output:
        p=(ROOT/a.output).resolve();p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)
    print(text,end="");return 0 if not errors else 2

if __name__=="__main__":raise SystemExit(main())
