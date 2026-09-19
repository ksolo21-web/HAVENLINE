#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import os
import re
import subprocess

from lib import ROOT, changed_files
from repair_sufficiency_critic import review as review_repair_sufficiency, whole_file_proof_digest

PINNED_INTEGRATION_BRANCH="codex/havenline-sequential-task-01"


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


def _requires_c0r(task:object,plan:dict)->bool:
    if isinstance(task,str) and len(task)==3 and task.startswith("T") and task[1:].isdigit() and int(task[1:])>=10:
        return True
    return isinstance(plan.get("repair_sufficiency"),dict)


def verify_integration_branch(branch:str|None)->list[str]:
    return [] if branch==PINNED_INTEGRATION_BRANCH else ["active integration branch does not match pinned canonical branch"]


def _executable_code(line:str)->str:
    """Remove comments and quoted literals before semantic marker checks."""
    kept=[];quote=None;escaped=False
    for char in line:
        if quote is not None:
            if escaped:escaped=False
            elif char=="\\":escaped=True
            elif char==quote:quote=None
            kept.append(" ")
            continue
        if char in {'"', "'"}:
            quote=char;kept.append(" ");continue
        if char=="#":break
        kept.append(char)
    return "".join(kept)


SCALAR_NAME=re.compile(r"(?i)(?:size|width|height|scale|factor|ratio|coefficient|threshold|timeout|limit|offset|slack|inset|clearance|dimension|footprint)")


def _diff_statements(diff:str,prefix:str)->list[str]:
    statements=[];buffer=[];depth=0
    def flush():
        nonlocal buffer,depth
        if buffer:statements.append(" ".join(buffer))
        buffer=[];depth=0
    in_hunk=False
    for raw in diff.splitlines():
        if raw.startswith("@@"):
            flush();in_hunk=True;continue
        if raw.startswith(("diff --git ","index ","--- ","+++ ")):continue
        include=(raw.startswith(prefix) and not raw.startswith(prefix*3)) or (in_hunk and raw.startswith(" "))
        if not include:
            # Opposite-side replacement lines are omitted without breaking a
            # multiline statement reconstructed from unchanged hunk context.
            continue
        line=raw[1:]
        code=_executable_code(line)
        if not code.strip():continue
        buffer.append(line.strip())
        depth+=sum(code.count(char) for char in "([{")-sum(code.count(char) for char in ")]}" )
        if depth<=0 and not code.rstrip().endswith((",","\\")):
            flush()
    flush()
    return statements


def _scalar_statement_effect(statement:str)->tuple[str,str]:
    code=_executable_code(statement)
    generic=re.search(r"\b((?:[A-Za-z_][A-Za-z0-9_]*\.)*)set\s*\(\s*[\"']([^\"']+)[\"']\s*,\s*(.*?)\)\s*$",statement)
    if generic and SCALAR_NAME.search(generic.group(2)):
        return (generic.group(1)+generic.group(2)).rstrip("."),re.sub(r"\s+","",generic.group(3))
    setter=re.search(r"\b((?:[A-Za-z_][A-Za-z0-9_]*\.)*)set_([A-Za-z_][A-Za-z0-9_]*)\s*\((.*?)\)\s*$",code)
    if setter and SCALAR_NAME.search(setter.group(2)):
        return (setter.group(1)+setter.group(2)).rstrip("."),re.sub(r"\s+","",setter.group(3))
    source=statement.split("#",1)[0]
    if re.match(r"^\s*(?:def|func)\b",source):return "",""
    assignment=re.match(r"^\s*(?:const\s+|var\s+)?(.+?)\s*(?::=|(?<![<>=!])=(?!=))\s*(.*)$",source)
    if not assignment:return "",""
    lhs=re.sub(r"\s+","",assignment.group(1));rhs=_executable_code(assignment.group(2))
    normalized_rhs=re.sub(r"\s+","",assignment.group(2))
    if SCALAR_NAME.search(lhs) and ("." in lhs or "[" in lhs or lhs.upper()==lhs):return lhs,normalized_rhs
    qualified=re.search(r"\b((?:[A-Za-z_][A-Za-z0-9_]*\.)+[A-Za-z_][A-Za-z0-9_]*)\b(?!\s*\()",rhs)
    if qualified and SCALAR_NAME.search(qualified.group(1)):
        return lhs+"->"+qualified.group(1),normalized_rhs
    return "",""


def _changed_scalar_assignments(diff:str)->dict[str,set[str]]:
    tables=[]
    for prefix in ("-","+"):
        table:dict[str,set[str]]={}
        for statement in _diff_statements(diff,prefix):
            target,rhs=_scalar_statement_effect(statement)
            if target:table.setdefault(target,set()).add(rhs)
        tables.append(table)
    removed,added=tables
    changed={target:added[target]-removed[target] for target in set(removed)&set(added) if removed[target]!=added[target]}
    # A newly introduced write to a qualified scalar sink or setter is itself a
    # parameter effect and must be declared, even when no old statement existed.
    changed.update({target:added[target] for target in set(added)-set(removed) if "." in target and "->" not in target})
    return changed


def implementation_diff_errors(
    plan:dict,
    actual_changed:list[str],
    actual_diff_by_file:dict[str,str]|None,
    actual_source_by_file:dict[str,str]|None=None,
    trusted_proofs:dict[str,dict]|None=None,
)->list[str]:
    errors=[]
    for group in plan.get("repair_sufficiency",{}).get("repair_groups",[]):
        if not isinstance(group,dict) or not isinstance(group.get("same_family_attempt_count"),int) or group.get("same_family_attempt_count",0)<2:
            continue
        group_id=str(group.get("group_id") or "<missing-group>")
        contract=group.get("implementation_diff_contract",{})
        files=contract.get("causal_files",[]) if isinstance(contract,dict) else []
        markers=contract.get("required_added_markers",[]) if isinstance(contract,dict) else []
        comparison_base=contract.get("comparison_base") if isinstance(contract,dict) else None
        if not isinstance(files,list) or not files or not isinstance(markers,list) or not markers or not isinstance(comparison_base,str) or len(comparison_base)!=40:
            errors.append(group_id+" repeated repair lacks implementation diff contract");continue
        if not set(files)<=set(actual_changed):
            errors.append(group_id+" architectural causal files did not change")
        if actual_diff_by_file is None:
            errors.append(group_id+" implementation diff evidence missing");continue
        added_code=[
            _executable_code(line[1:]) for path in files for line in actual_diff_by_file.get(path,"").splitlines()
            if line.startswith("+") and not line.startswith("+++")
        ]
        for marker in markers:
            if not isinstance(marker,dict):
                errors.append(group_id+" architectural diff marker invalid: "+str(marker));continue
            kind=marker.get("kind");value=marker.get("value")
            if not isinstance(value,str) or re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*",value) is None:
                errors.append(group_id+" architectural diff marker invalid: "+str(marker));continue
            if kind=="FUNCTION_DEFINITION":
                definition=any(re.match(r"^\s*(?:def|func)\s+"+re.escape(value)+r"\s*\(",line) for line in added_code)
                reachable=any(re.search(r"\b"+re.escape(value)+r"\s*\(",line) and not re.match(r"^\s*(?:def|func)\s+",line) for line in added_code)
                found=definition and reachable
            elif kind=="CODE_IDENTIFIER":
                found=any(re.search(r"\b"+re.escape(value)+r"\b",line) for line in added_code)
            else:
                found=False
            if not found:errors.append(group_id+" architectural executable marker missing: "+value)
        effects={}
        for path in files:effects.update(_changed_scalar_assignments(actual_diff_by_file.get(path,"")))
        declared=group.get("scalar_parameters_changed",[])
        declarations={str(row.get("target")):row for row in declared if isinstance(row,dict) and row.get("target")} if isinstance(declared,list) else {}
        if set(effects)!=set(declarations):
            missing=set(effects)-set(declarations);unused=set(declarations)-set(effects)
            if missing:errors.append(group_id+" undeclared scalar assignment changes: "+",".join(sorted(missing)))
            if unused:errors.append(group_id+" declared scalar effects absent from implementation: "+",".join(sorted(unused)))
        for target in set(effects)&set(declarations):
            expected=declarations[target].get("normalized_rhs")
            if effects[target]!={expected}:
                errors.append(group_id+" scalar implementation does not match declared derived expression: "+target)
        if declarations:
            family=group.get("failure_family",{}) if isinstance(group.get("failure_family"),dict) else {}
            family_id=family.get("id")
            trusted=(trusted_proofs or {}).get(family_id,{}) if isinstance(family_id,str) else {}
            proof_mode=trusted.get("proof_slice_mode") if isinstance(trusted,dict) else None
            ignored_lines=trusted.get("proof_irrelevant_exact_lines",[]) if isinstance(trusted,dict) else []
            proof_path=contract.get("proof_source_path") if isinstance(contract,dict) else None
            expected_digest=trusted.get("proof_relevant_sha256") if isinstance(trusted,dict) else None
            plan_policy={
                "proof_slice_mode":contract.get("proof_slice_mode") if isinstance(contract,dict) else None,
                "proof_irrelevant_exact_lines":contract.get("proof_irrelevant_exact_lines") if isinstance(contract,dict) else None,
                "proof_relevant_sha256":contract.get("proof_relevant_sha256") if isinstance(contract,dict) else None,
            }
            trusted_policy={key:trusted.get(key) for key in plan_policy} if isinstance(trusted,dict) else {}
            source=actual_source_by_file.get(proof_path,"") if isinstance(actual_source_by_file,dict) and isinstance(proof_path,str) else ""
            if (
                plan_policy!=trusted_policy
                or proof_mode!="WHOLE_FILE_EXCEPT_EXACT_METADATA_LINES"
                or not isinstance(ignored_lines,list)
                or whole_file_proof_digest(source,[str(value) for value in ignored_lines])!=expected_digest
            ):
                errors.append(group_id+" current proof-relevant implementation differs from proven source")
    return errors


def validate_c0r(c0:dict,plan:dict,c0r:dict|None,c0_sha256:str|None,plan_sha256:str|None)->list[str]:
    if not _requires_c0r(c0.get("task_id"),plan):
        return []
    errors=[]
    task=c0.get("task_id")
    canonical_c0=f"Docs/Production/{task}/C0_ROOT_CAUSE.json"
    canonical_plan=f"Docs/Production/{task}/REPAIR_PLAN.json"
    if not isinstance(plan.get("repair_sufficiency"),dict):
        errors.append("T10+ repair plan requires repair_sufficiency")
    if not isinstance(c0r,dict):
        return errors+["canonical C0R repair-sufficiency report required"]
    expected_fields={
        "critic_id":"C0R",
        "non_voting":True,
        "approval_critic":False,
        "read_only":True,
        "outcome":"REPAIR_PLAN_ACCEPTED",
        "builder_action":"BUILD_BOUNDED_REPAIR",
        "passed":True,
        "full_blocker_coverage":True,
        "thresholds_unchanged":True,
        "may_approve_task":False,
        "may_score_gameplay":False,
        "may_lower_C1_C11_thresholds":False,
    }
    for key,value in expected_fields.items():
        if c0r.get(key)!=value:
            errors.append(f"C0R {key} does not authorize bounded repair")
    if c0r.get("task_id")!=task or c0r.get("diagnosis_id")!=c0.get("diagnosis_id") or c0r.get("failed_candidate")!=c0.get("failed_candidate"):
        errors.append("C0R task/diagnosis/candidate binding mismatch")
    if c0r.get("rejections") not in ([],None) or c0r.get("evidence_gaps") not in ([],None):
        errors.append("C0R contains unresolved rejection or evidence gap")
    bindings=c0r.get("input_bindings",{})
    if not isinstance(bindings,dict):
        errors.append("C0R input bindings missing")
        bindings={}
    if bindings.get("c0_path")!=canonical_c0 or bindings.get("plan_path")!=canonical_plan:
        errors.append("C0R canonical input paths mismatch")
    if not isinstance(c0_sha256,str) or len(c0_sha256)!=64 or bindings.get("c0_sha256")!=c0_sha256:
        errors.append("C0R exact C0 hash mismatch")
    if not isinstance(plan_sha256,str) or len(plan_sha256)!=64 or bindings.get("plan_sha256")!=plan_sha256:
        errors.append("C0R exact repair-plan hash mismatch")
    if isinstance(c0_sha256,str) and len(c0_sha256)==64:
        expected=review_repair_sufficiency(c0,plan,c0_sha256)
        actual={key:value for key,value in c0r.items() if key!="input_bindings"}
        if actual!=expected:
            errors.append("canonical C0R report does not match deterministic recomputation")
    return errors


def validate(c0:dict,plan:dict,actual_changed:list[str]|None=None,actual_base:str|None=None,c0r:dict|None=None,c0_sha256:str|None=None,plan_sha256:str|None=None,actual_diff_by_file:dict[str,str]|None=None,actual_source_by_file:dict[str,str]|None=None)->list[str]:
    errors=[]
    task=c0.get("task_id")
    canonical_c0=f"Docs/Production/{task}/C0_ROOT_CAUSE.json"
    canonical_plan=f"Docs/Production/{task}/REPAIR_PLAN.json"
    canonical_c0r=f"Docs/Production/{task}/C0R_REPAIR_SUFFICIENCY.json"
    bookkeeping={canonical_c0,canonical_plan,canonical_c0r}
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
    errors.extend(validate_c0r(c0,plan,c0r,c0_sha256,plan_sha256))
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
        trusted_proofs={
            str(row.get("failure_family_id")):row.get("proof",{})
            for row in c0.get("full_domain_proofs",[])
            if isinstance(row,dict) and row.get("failure_family_id") and isinstance(row.get("proof"),dict)
        }
        errors.extend(implementation_diff_errors(plan,actual_changed,actual_diff_by_file,actual_source_by_file,trusted_proofs))
    return errors


def main()->int:
    ap=argparse.ArgumentParser();ap.add_argument("--c0",required=True);ap.add_argument("--plan",required=True);ap.add_argument("--base");ap.add_argument("--head",default="HEAD");ap.add_argument("--output");a=ap.parse_args()
    c0_path=(ROOT/a.c0).resolve();plan_path=(ROOT/a.plan).resolve();c0=load(c0_path);plan=load(plan_path)
    c0_sha256=digest(c0_path);plan_sha256=digest(plan_path)
    c0_copy=dict(c0);c0_copy["report_sha256"]=c0_sha256
    if "c0_report_sha256" not in plan:plan["c0_report_sha256"]=""
    task=c0.get("task_id")
    c0r_path=(ROOT/f"Docs/Production/{task}/C0R_REPAIR_SUFFICIENCY.json").resolve()
    c0r=load(c0r_path) if c0r_path.exists() else None
    actual=changed_files(a.base,a.head) if a.base else None
    actual_diff_by_file=None
    actual_source_by_file=None
    if a.base:
        actual_diff_by_file={}
        actual_source_by_file={}
        for group in plan.get("repair_sufficiency",{}).get("repair_groups",[]):
            contract=group.get("implementation_diff_contract",{}) if isinstance(group,dict) else {}
            for path in contract.get("causal_files",[]) if isinstance(contract,dict) and isinstance(contract.get("causal_files",[]),list) else []:
                comparison_base=contract.get("comparison_base")
                if isinstance(comparison_base,str) and len(comparison_base)==40:
                    actual_diff_by_file[path]=subprocess.check_output(["git","diff","--unified=100000",comparison_base,a.head,"--",path],text=True)
                actual_source_by_file[path]=subprocess.check_output(["git","show",f"{a.head}:{path}"],text=True)
    errors=validate(c0_copy,plan,actual,a.base,c0r=c0r,c0_sha256=c0_sha256,plan_sha256=plan_sha256,actual_diff_by_file=actual_diff_by_file,actual_source_by_file=actual_source_by_file)
    inherited_errors=verify_inherited_noncausal(plan,a.head,os.environ.get("INTEGRATION_HEAD")) if actual is not None else []
    errors.extend(inherited_errors)
    if actual is not None:errors.extend(verify_integration_branch(os.environ.get("INTEGRATION_BRANCH")))
    result={"schema_version":1,"task_id":c0.get("task_id"),"diagnosis_id":c0.get("diagnosis_id"),"passed":not errors,"mode":"post-build" if actual is not None else "pre-build","repair_base":plan.get("repair_base"),"c0r_required":_requires_c0r(task,plan),"c0r_path":f"Docs/Production/{task}/C0R_REPAIR_SUFFICIENCY.json","c0r_sha256":digest(c0r_path) if c0r_path.exists() else None,"c0r_outcome":c0r.get("outcome") if isinstance(c0r,dict) else None,"reconciled_integration_head":plan.get("reconciled_integration_head"),"inherited_noncausal_files":_inherited_noncausal(plan),"actual_changed_files":actual or [],"errors":errors}
    text=json.dumps(result,indent=2)+"\n"
    if a.output:
        p=(ROOT/a.output).resolve();p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)
    print(text,end="");return 0 if not errors else 2

if __name__=="__main__":raise SystemExit(main())
