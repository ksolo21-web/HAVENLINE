#!/usr/bin/env python3
from __future__ import annotations
import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];DOCS=ROOT/'Docs'/'Production'
TASK_RE=re.compile(r'^T(?:1[2-9]|[2-6][0-9]|70)$')
def load(n): return json.loads((DOCS/n).read_text())
def num(t): return int(t[1:])
def validate():
    p=load('V32_FORWARD_PREP_ROADMAP.json');contracts=load('V32_FORWARD_PREP_CONTRACTS.json')['contracts'];caps=load('CAPABILITY_STATUS.json')['external'];errors=[];seen=set()
    allowed={'forward_preparation','asset_content_readiness','infrastructure'}
    for row in p.get('immediate_parallel_prep',[]):
        if row.get('lane') not in allowed: errors.append('invalid lane '+str(row.get('lane')))
        if not row.get('deliverables'): errors.append('prep row missing deliverables')
        if not row.get('forbidden'): errors.append('prep row missing forbidden boundaries')
        for t in row.get('tasks',[]):
            if not TASK_RE.fullmatch(t): errors.append('prep task outside T12-T70: '+str(t))
            if t in seen: errors.append('task appears in multiple immediate prep rows: '+t)
            seen.add(t)
    expected={f'T{i:02d}' for i in range(12,71)}
    missing=sorted(expected-seen);extra=sorted(seen-expected)
    if missing: errors.append('future prep coverage missing: '+','.join(missing))
    if extra: errors.append('unexpected future prep tasks: '+','.join(extra))
    valid_domains=set(contracts)
    mapped=p.get('task_canary_domains',{})
    for t,domains in mapped.items():
        if t not in expected: errors.append('canary mapping task outside T12-T70: '+t)
        for domain in domains:
            if domain not in valid_domains: errors.append(t+' references unknown canary domain '+domain)
    milestones=p.get('external_capability_milestones',{})
    for cap,cfg in milestones.items():
        if cap not in caps: errors.append('external milestone unknown capability '+cap);continue
        try: prep=num(cfg['prepare_by']);required=[num(x) for x in cfg['required_by']]
        except Exception: errors.append('invalid external milestone task id '+cap);continue
        if not required or prep>=min(required): errors.append('external milestone prepare_by must precede required_by: '+cap)
        if not cfg.get('reason'): errors.append('external milestone missing reason: '+cap)
    for name,fields in p.get('required_shared_contracts',{}).items():
        if len(fields)!=len(set(fields)) or not fields: errors.append('invalid shared contract '+name)
    packet=p.get('packet_policy',{})
    for key in ('dynamic_generated_not_lifecycle_authority','may_not_change_task_status','may_not_grant_ownership','may_not_integrate_runtime','strict_quality_rule_preserved'):
        if packet.get(key) is not True: errors.append('packet policy must enforce '+key)
    return {'passed':not errors,'prep_task_count':len(seen),'expected_prep_task_count':len(expected),'canary_mapping_count':len(mapped),'external_milestone_count':len(milestones),'shared_contract_count':len(p.get('required_shared_contracts',{})),'errors':errors}
if __name__=='__main__':
    out=validate();print(json.dumps(out,indent=2));raise SystemExit(0 if out['passed'] else 2)
