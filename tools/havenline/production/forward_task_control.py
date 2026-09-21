#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,re,subprocess
from pathlib import Path
from forward_execution import DOCS,ROOT,resolve_task
from task_graduation_gate import evaluate as graduation
from timeout_stage_plan import plan as stage_plan
from rolling_canary import requirements as canary_requirements
from performance_ledger import validate as validate_performance
from branch_budget import validate as validate_branches
from contract_compatibility import contracts_for_task,affected_contracts,evaluate_change
from gate_fingerprint import lookup
from synthetic_merge_forecast import forecast

SHA40=re.compile(r'^[0-9a-f]{40}$')
REFERENCE={'C1','C2'}
DETERMINISTIC={'C6','C9'}

def load(path): return json.loads(Path(path).read_text())

def _commit_available(sha):
    if not SHA40.fullmatch(str(sha or '')): return False
    return subprocess.run(['git','cat-file','-e',f'{sha}^{{commit}}'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0

def critic_plan(task_id):
    forward=resolve_task(task_id);policy=load(DOCS/'TASK_GRADUATION_POLICY.json')
    specialist_set=set(policy.get('specialist_fanout_critics',[]));allc=list(forward['critics'])
    specialist=[c for c in allc if c in specialist_set]
    reference=[c for c in allc if c in REFERENCE]
    deterministic=[c for c in allc if c in DETERMINISTIC]
    unknown=[c for c in allc if c not in specialist_set|REFERENCE|DETERMINISTIC]
    return {'all':allc,'reference_specific':reference,'specialist_fanout':specialist,'deterministic':deterministic,'unclassified':unknown}

def _contract_validation(task_id,candidate_files):
    affected=affected_contracts(candidate_files)
    if not affected:return {'required':False,'affected_contracts':[],'descriptor':None,'results':[],'passed':True,'errors':[]}
    path=DOCS/task_id/'CONTRACT_CHANGES.json';errors=[];results=[]
    if not path.is_file():
        return {'required':True,'affected_contracts':affected,'descriptor':str(path.relative_to(ROOT)),'results':[],'passed':False,'errors':['affected contract paths require '+str(path.relative_to(ROOT))]}
    data=load(path);changes=data.get('changes') if isinstance(data,dict) else None
    if not isinstance(changes,list):return {'required':True,'affected_contracts':affected,'descriptor':str(path.relative_to(ROOT)),'results':[],'passed':False,'errors':['CONTRACT_CHANGES.json changes must be a list']}
    by={}
    for row in changes:
        if isinstance(row,dict) and row.get('contract_id'):by.setdefault(row['contract_id'],[]).append(row)
    for cid in affected:
        rows=by.get(cid,[])
        if len(rows)!=1:
            errors.append(f'{cid} requires exactly one change descriptor');continue
        result=evaluate_change(rows[0]);results.append(result)
        if not result.get('passed'):errors += [cid+': '+x for x in result.get('errors',[])]
    extras=sorted(set(by)-set(affected))
    if extras:errors.append('descriptors without affected watched paths: '+','.join(extras))
    return {'required':True,'affected_contracts':affected,'descriptor':str(path.relative_to(ROOT)),'results':results,'passed':not errors,'errors':errors}

def plan(task_id,target='ASSIGNED',candidate=None,integration=None,inventory=None,builder=None):
    task_id=task_id.upper();errors=[]
    if target not in ('ASSIGNED','BUILDING_ISOLATED'):errors.append('target must be ASSIGNED or BUILDING_ISOLATED')
    try:forward=resolve_task(task_id)
    except Exception as exc:return {'passed':False,'task_id':task_id,'target':target,'errors':['forward plan: '+str(exc)]}
    builder_for_gate=builder or candidate
    grad=graduation(task_id,target,builder_for_gate,integration)
    if not grad.get('passed'):errors += ['graduation: '+x for x in grad.get('errors',[])]
    branches=validate_branches(task_id,inventory)
    if not branches.get('passed'):errors += ['branch budget: '+x for x in branches.get('errors',[])]
    perf=validate_performance()
    if not perf.get('passed'):errors += ['performance policy: '+x for x in perf.get('errors',[])]
    critics=critic_plan(task_id)
    if critics['unclassified']:errors.append('unclassified critics: '+','.join(critics['unclassified']))
    stages=stage_plan(task_id);canaries=canary_requirements(task_id);contracts=contracts_for_task(task_id)
    source_bound=None
    if target=='BUILDING_ISOLATED':
        if not candidate or not SHA40.fullmatch(str(candidate)):errors.append('BUILDING_ISOLATED requires explicit exact candidate SHA')
        elif not _commit_available(candidate):errors.append('candidate commit unavailable locally')
        if not integration or not SHA40.fullmatch(str(integration)):errors.append('BUILDING_ISOLATED requires explicit exact integration SHA')
        elif not _commit_available(integration):errors.append('integration commit unavailable locally')
        if candidate and integration and _commit_available(candidate) and _commit_available(integration):
            proof={};proof_errors=[]
            for gate in forward['ordered_gates']:
                try:proof[gate]=lookup(task_id,gate,candidate)
                except Exception as exc:proof_errors.append(gate+': '+str(exc))
            merge=forecast(candidate,integration)
            if merge.get('requires_reconcile'):proof_errors.append('synthetic merge requires reconciliation: '+str(merge.get('risk')))
            contract_validation=_contract_validation(task_id,merge.get('candidate_files',[]))
            if not contract_validation['passed']:proof_errors += ['contract: '+x for x in contract_validation['errors']]
            source_bound={'candidate':candidate,'integration':integration,'proof_decisions':proof,'synthetic_merge':merge,'contract_validation':contract_validation,'errors':proof_errors}
            errors += ['source-bound: '+x for x in proof_errors]
    return {'passed':not errors,'schema_version':1,'task_id':task_id,'target':target,'forward':forward,'graduation':grad,'branch_budget':branches,'stage_plan':stages,'canaries':canaries,'performance_policy':perf,'contracts':contracts,'critic_plan':critics,'source_bound':source_bound,'finish_running_sha':True,'automatic_c0_failure_mode':True,'quality_thresholds_unchanged':True,'errors':errors}

def validate_all():
    errors=[];count=0
    for i in range(11,71):
        task=f'T{i:02d}'
        try:
            resolve_task(task);stage_plan(task);canary_requirements(task);cp=critic_plan(task)
            if cp['unclassified']:errors.append(task+' has unclassified critics '+','.join(cp['unclassified']))
            count+=1
        except Exception as exc:errors.append(task+': '+str(exc))
    return {'passed':not errors,'task_count':count,'errors':errors}

def main():
    ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest='cmd',required=True);sub.add_parser('validate')
    c=sub.add_parser('critics');c.add_argument('task_id')
    p=sub.add_parser('plan');p.add_argument('task_id');p.add_argument('--target',choices=['ASSIGNED','BUILDING_ISOLATED'],default='ASSIGNED');p.add_argument('--candidate');p.add_argument('--integration');p.add_argument('--builder');p.add_argument('--inventory');p.add_argument('--output')
    a=ap.parse_args()
    if a.cmd=='validate':out=validate_all()
    elif a.cmd=='critics':out={'passed':True,'task_id':a.task_id.upper(),'critic_plan':critic_plan(a.task_id.upper()),'errors':[]}
    else:out=plan(a.task_id,a.target,a.candidate,a.integration,a.inventory,a.builder)
    text=json.dumps(out,indent=2)+'\n'
    if getattr(a,'output',None):Path(a.output).write_text(text)
    print(text,end='');raise SystemExit(0 if out.get('passed') else 2)
if __name__=='__main__':main()
