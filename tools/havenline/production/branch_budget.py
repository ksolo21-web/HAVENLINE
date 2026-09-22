#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];DOCS=ROOT/'Docs'/'Production'
TASK_BRANCH_RE=re.compile(r'^havenline/(T(?:1[1-9]|[2-6][0-9]|70))-(.+)$')
ACTIVE={'PREPARED','ASSIGNED','BUILDING_ISOLATED','BUILT_PENDING_DEPENDENCY','INTEGRATION_READY','INTEGRATING','UNDER_REVIEW','FIX_REQUIRED','BLOCKED'}
def load(n): return json.loads((DOCS/n).read_text())
def authorized_preactivation_branches():
    allowed={}
    for checklist_path in sorted(DOCS.glob('T[0-9][0-9]/ACTIVATION_CHECKLIST.json')):
        try:
            checklist=json.loads(checklist_path.read_text())
        except Exception:
            continue
        task_id=str(checklist.get('task_id','')).upper()
        branch=checklist.get('builder_branch') or checklist.get('future_builder_branch')
        if not re.fullmatch(r'T(?:1[1-9]|[2-6][0-9]|70)',task_id) or not isinstance(branch,str):
            continue
        explicitly_allowed=(
            checklist.get('isolated_build_allowed_before_all_dependencies_approved') is True
            and checklist.get('built_pending_dependency_allowed') is True
            and checklist.get('integration_allowed_before_activation') is False
            and checklist.get('maximum_state_before_dependency_approval')=='BUILT_PENDING_DEPENDENCY'
        )
        policy=checklist.get('preactivation_build_policy',{})
        if explicitly_allowed and isinstance(policy,dict):
            explicitly_allowed=(
                policy.get('maximum_state')=='BUILT_PENDING_DEPENDENCY'
                and policy.get('may_integrate') is False
                and policy.get('may_claim_integration_ready') is False
                and policy.get('may_approve') is False
            )
        if explicitly_allowed:
            allowed[task_id]=branch
    return allowed
def validate(task=None,inventory=None):
    reg=load('WORKSTREAM_REGISTRY.json');policy=load('PARALLEL_PREPARATION_POLICY.json')['branch_budget'];errors=[]
    preactivation=authorized_preactivation_branches()
    rows_by_task={}
    for w in reg['workstreams']:
        tid=w.get('task_id','')
        if re.fullmatch(r'T(?:1[1-9]|[2-6][0-9]|70)',tid):
            rows_by_task.setdefault(tid,[]).append(w)
    tasks=[task] if task else sorted(rows_by_task)
    for t in tasks:
        rows=rows_by_task.get(t,[])
        if len(rows)>policy['authoritative_task_branches']: errors.append(t+' has multiple authoritative workstream rows')
    details={'authoritative_registry_tasks':tasks,'authorized_preactivation_branches':preactivation,'inventory_checked':False}
    if inventory:
        names=json.loads(Path(inventory).read_text())
        if not isinstance(names,list) or any(not isinstance(x,str) for x in names):
            errors.append('inventory must be a JSON list of branch names');names=[]
        found={}
        for name in names:
            m=TASK_BRANCH_RE.fullmatch(name)
            if m: found.setdefault(m.group(1),[]).append(name)
        details['inventory_checked']=True;details['forward_task_branches']=found
        for t,names_for_task in sorted(found.items()):
            rows=rows_by_task.get(t,[])
            if not rows:
                allowed_branch=preactivation.get(t)
                if allowed_branch:
                    normal=[x for x in names_for_task if 'repair' not in x.lower()]
                    repair=[x for x in names_for_task if x not in normal]
                    if len(repair)>policy['active_bounded_repair_branches']:
                        errors.append(t+' exceeds active bounded repair branch budget')
                    if normal != [allowed_branch]:
                        errors.append(t+' preactivation branch inventory must contain only authorized branch '+allowed_branch+': '+','.join(sorted(normal)))
                    continue
                errors.append(t+' has unregistered forward task branch(es): '+','.join(sorted(names_for_task)));continue
            if len(rows)!=1: continue
            row=rows[0];authoritative=row.get('branch');repair=[x for x in names_for_task if 'repair' in x.lower()]
            normal=[x for x in names_for_task if x not in repair]
            if len(repair)>policy['active_bounded_repair_branches']:
                errors.append(t+' exceeds active bounded repair branch budget')
            if len(normal)>policy['authoritative_task_branches']:
                errors.append(t+' has extra non-repair/prototype task branches: '+','.join(sorted(normal)))
            if normal and authoritative not in normal:
                errors.append(t+' live authoritative branch does not match registry: '+str(authoritative))
            extras=[x for x in normal if x!=authoritative]
            if extras: errors.append(t+' unregistered prototype branch(es): '+','.join(sorted(extras)))
        for t,rows in rows_by_task.items():
            if len(rows)!=1: continue
            row=rows[0]
            if row.get('status') in ACTIVE:
                names_for_task=found.get(t,[])
                if row.get('branch') not in names_for_task:
                    errors.append(t+' active/prepared authoritative branch missing from remote inventory: '+str(row.get('branch')))
    return {'passed':not errors,'policy':policy,'details':details,'errors':errors}
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--task');ap.add_argument('--inventory');a=ap.parse_args();out=validate(a.task.upper() if a.task else None,a.inventory);print(json.dumps(out,indent=2));raise SystemExit(0 if out['passed'] else 2)
if __name__=='__main__':main()
