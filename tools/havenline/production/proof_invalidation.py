#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];DOCS=ROOT/'Docs/Production'
def load(name):return json.loads((DOCS/name).read_text())
def descendants(task_id,graph):
    reverse={k:set() for k in graph['tasks']}
    for t,row in graph['tasks'].items():
        for d in row.get('dependencies',[]):reverse.setdefault(d,set()).add(t)
    seen=set();stack=[task_id]
    while stack:
        cur=stack.pop()
        for nxt in reverse.get(cur,set()):
            if nxt not in seen:seen.add(nxt);stack.append(nxt)
    return seen
def invalidate_task(task_id:str):
    graph=load('DEPENDENCY_GRAPH.json');policy=load('PROOF_INVALIDATION_POLICY.json');tasks={task_id}|descendants(task_id,graph);gates=set(policy['default_invalidated_gates']);return _report('task',task_id,tasks,gates)
def invalidate_contract(contract_id:str):
    reg=load('CONTRACT_REGISTRY.json');graph=load('DEPENDENCY_GRAPH.json');policy=load('PROOF_INVALIDATION_POLICY.json');row=reg['contracts'].get(contract_id)
    if not row:raise ValueError('unknown contract '+contract_id)
    roots={row['owner_task']}|set(row.get('consumers',[]));tasks=set(roots)
    for t in roots:tasks|=descendants(t,graph)
    gates=set(policy.get('contract_gate_overrides',{}).get(contract_id,policy['default_invalidated_gates']))
    return _report('contract',contract_id,tasks,gates)
def _report(kind,key,tasks,gates):
    policy=load('PROOF_INVALIDATION_POLICY.json');index=load('GATE_RESULT_INDEX.json');records=[]
    for r in index.get('records',[]):
        if r.get('task_id') in tasks and r.get('gate') in gates:records.append({'task_id':r.get('task_id'),'gate':r.get('gate'),'candidate':r.get('candidate'),'fingerprint':r.get('fingerprint')})
    return {'schema_version':1,'trigger_kind':kind,'trigger':key,'invalidated_tasks':sorted(tasks),'invalidated_gates':sorted(gates),'invalidated_index_records':records,'proof_reuse_blocked':True,'automatic_approval_revocation':False,'integration_owner_disposition_required':True,'reason':'approved dependency/contract changed; downstream proof using affected assumptions must be regenerated or explicitly revalidated'}
def validate_policy():
    p=load('PROOF_INVALIDATION_POLICY.json');errors=[]
    if p.get('invalidated_proof_may_be_reused') is not False:errors.append('invalidated proof reuse must be forbidden')
    if p.get('automatic_approval_revocation') is not False:errors.append('invalidation must not auto-revoke approval')
    if p.get('uncertainty_policy')!='INVALIDATE':errors.append('uncertainty must invalidate conservatively')
    return {'passed':not errors,'errors':errors}
def main():
    ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest='cmd',required=True);sub.add_parser('validate');t=sub.add_parser('task');t.add_argument('task_id');c=sub.add_parser('contract');c.add_argument('contract_id');a=ap.parse_args();r=validate_policy() if a.cmd=='validate' else (invalidate_task(a.task_id) if a.cmd=='task' else invalidate_contract(a.contract_id));print(json.dumps(r,indent=2));raise SystemExit(0 if r.get('passed',True) else 2)
if __name__=='__main__':main()
