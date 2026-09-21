#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];DOCS=ROOT/'Docs'/'Production'
def validate():
    p=json.loads((DOCS/'V32_FORWARD_PREP_ROADMAP.json').read_text());errors=[];seen=set()
    allowed={'forward_preparation','asset_content_readiness','infrastructure'}
    for row in p.get('immediate_parallel_prep',[]):
        if row.get('lane') not in allowed: errors.append('invalid lane '+str(row.get('lane')))
        if not row.get('deliverables'): errors.append('prep row missing deliverables')
        if not row.get('forbidden'): errors.append('prep row missing forbidden boundaries')
        for t in row.get('tasks',[]):
            if t in seen: errors.append('task appears in multiple immediate prep rows: '+t)
            seen.add(t)
    for name,fields in p.get('required_shared_contracts',{}).items():
        if len(fields)!=len(set(fields)) or not fields: errors.append('invalid shared contract '+name)
    return {'passed':not errors,'prep_task_count':len(seen),'shared_contract_count':len(p.get('required_shared_contracts',{})),'errors':errors}
if __name__=='__main__':
    out=validate();print(json.dumps(out,indent=2));raise SystemExit(0 if out['passed'] else 2)
