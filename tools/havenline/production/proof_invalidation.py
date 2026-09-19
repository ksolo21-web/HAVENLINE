#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,re,subprocess
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
def _expand_range(pair,graph):
    if not isinstance(pair,list) or len(pair)!=2:return set()
    a,b=pair
    ma=re.fullmatch(r'T(\d{2})',str(a));mb=re.fullmatch(r'T(\d{2})',str(b))
    if not ma or not mb:return set()
    lo,hi=int(ma.group(1)),int(mb.group(1));return {f'T{i:02d}' for i in range(lo,hi+1) if f'T{i:02d}' in graph['tasks']}
def _contract_roots(row,graph):
    owner=row.get('owner') or row.get('owner_task')
    if not owner:raise ValueError('contract missing owner')
    roots={owner}|{x for x in row.get('consumers',[]) if x in graph['tasks']}
    for pair in row.get('consumer_ranges',[]):roots|=_expand_range(pair,graph)
    return roots
def invalidate_task(task_id:str):
    graph=load('DEPENDENCY_GRAPH.json');policy=load('PROOF_INVALIDATION_POLICY.json');tasks={task_id}|descendants(task_id,graph);gates=set(policy['default_invalidated_gates']);return _report('task',task_id,tasks,gates)
def _invalidate_contract_row(contract_id:str,row:dict):
    graph=load('DEPENDENCY_GRAPH.json');policy=load('PROOF_INVALIDATION_POLICY.json');roots=_contract_roots(row,graph);tasks=set(roots)
    for t in list(roots):tasks|=descendants(t,graph)
    gates=set(policy.get('contract_gate_overrides',{}).get(contract_id,policy['default_invalidated_gates']))
    return _report('contract',contract_id,tasks,gates)
def invalidate_contract(contract_id:str):
    reg=load('CONTRACT_REGISTRY.json');row=reg['contracts'].get(contract_id)
    if not row:raise ValueError('unknown contract '+contract_id)
    return _invalidate_contract_row(contract_id,row)
def _report(kind,key,tasks,gates):
    policy=load('PROOF_INVALIDATION_POLICY.json');index=load('GATE_RESULT_INDEX.json');records=[]
    for r in index.get('records',[]):
        if r.get('task_id') in tasks and r.get('gate') in gates:records.append({'task_id':r.get('task_id'),'gate':r.get('gate'),'candidate':r.get('candidate'),'fingerprint':r.get('fingerprint')})
    return {'schema_version':1,'trigger_kind':kind,'trigger':key,'invalidated_tasks':sorted(tasks),'invalidated_gates':sorted(gates),'invalidated_index_records':records,'proof_reuse_blocked':True,'automatic_approval_revocation':False,'integration_owner_disposition_required':True,'reason':'approved dependency/contract changed; downstream proof using affected assumptions must be regenerated or explicitly revalidated'}
def diff_contract_sets(base_contracts:dict,head_contracts:dict):
    changed=sorted(cid for cid in set(base_contracts)|set(head_contracts) if base_contracts.get(cid)!=head_contracts.get(cid))
    reports=[];tasks=set();gates=set();records=[]
    for cid in changed:
        # For removals use the base row so former consumers are still invalidated.
        row=head_contracts.get(cid) or base_contracts.get(cid)
        report=_invalidate_contract_row(cid,row)
        reports.append(report);tasks.update(report['invalidated_tasks']);gates.update(report['invalidated_gates']);records.extend(report['invalidated_index_records'])
    unique_records=[];seen=set()
    for row in records:
        key=(row.get('task_id'),row.get('gate'),row.get('candidate'),row.get('fingerprint'))
        if key not in seen:seen.add(key);unique_records.append(row)
    return {'schema_version':1,'passed':True,'changed_contracts':changed,'contract_change_detected':bool(changed),'invalidated_tasks':sorted(tasks),'invalidated_gates':sorted(gates),'invalidated_index_records':unique_records,'proof_reuse_blocked':bool(changed),'automatic_approval_revocation':False,'integration_owner_disposition_required':bool(changed),'reports':reports}
def _contracts_at(ref:str):
    proc=subprocess.run(['git','show',f'{ref}:Docs/Production/CONTRACT_REGISTRY.json'],cwd=ROOT,text=True,capture_output=True)
    if proc.returncode!=0:return {}
    value=json.loads(proc.stdout);return value.get('contracts',{}) if isinstance(value,dict) else {}
def diff_refs(base:str,head:str='HEAD'):
    base_sha=subprocess.check_output(['git','rev-parse',f'{base}^{{commit}}'],cwd=ROOT,text=True).strip();head_sha=subprocess.check_output(['git','rev-parse',f'{head}^{{commit}}'],cwd=ROOT,text=True).strip()
    report=diff_contract_sets(_contracts_at(base_sha),_contracts_at(head_sha));report.update({'base':base_sha,'head':head_sha});return report
def validate_policy():
    p=load('PROOF_INVALIDATION_POLICY.json');reg=load('CONTRACT_REGISTRY.json');errors=[]
    if p.get('invalidated_proof_may_be_reused') is not False:errors.append('invalidated proof reuse must be forbidden')
    if p.get('automatic_approval_revocation') is not False:errors.append('invalidation must not auto-revoke approval')
    if p.get('uncertainty_policy')!='INVALIDATE':errors.append('uncertainty must invalidate conservatively')
    unknown=sorted(set(p.get('contract_gate_overrides',{}))-set(reg.get('contracts',{})))
    if unknown:errors.append('proof invalidation overrides reference unknown contracts: '+', '.join(unknown))
    graph=load('DEPENDENCY_GRAPH.json')
    for cid,row in reg.get('contracts',{}).items():
        try:_contract_roots(row,graph)
        except Exception as exc:errors.append(f'{cid}: {exc}')
    return {'passed':not errors,'errors':errors,'contract_override_count':len(p.get('contract_gate_overrides',{}))}
def main():
    ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest='cmd',required=True);sub.add_parser('validate');t=sub.add_parser('task');t.add_argument('task_id');c=sub.add_parser('contract');c.add_argument('contract_id');d=sub.add_parser('diff');d.add_argument('--base',required=True);d.add_argument('--head',default='HEAD');d.add_argument('--output');a=ap.parse_args()
    if a.cmd=='validate':r=validate_policy()
    elif a.cmd=='task':r=invalidate_task(a.task_id)
    elif a.cmd=='contract':r=invalidate_contract(a.contract_id)
    else:r=diff_refs(a.base,a.head)
    text=json.dumps(r,indent=2)+'\n';print(text,end='')
    if getattr(a,'output',None):(ROOT/a.output).resolve().write_text(text)
    raise SystemExit(0 if r.get('passed',True) else 2)
if __name__=='__main__':main()
