#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];DOCS=ROOT/'Docs'/'Production'
SEGMENTS=[
 ('move',['T06']),('auto_interact',['T07']),('gather',['T09']),('visible_carry',['T08']),
 ('deliver',['T08']),('transform',['T10']),('build_upgrade',['T11']),('save_reload',['T14']),
 ('customer_service',['T17']),('defend',['T21','T22']),('rescue',['T23'])
]
def load(n): return json.loads((DOCS/n).read_text())
def validate():
    graph=load('DEPENDENCY_GRAPH.json');reg=load('WORKSTREAM_REGISTRY.json');errors=[];rows=[];first_pending=None
    by_task={w.get('task_id'):w for w in reg.get('workstreams',[]) if w.get('task_id')}
    legacy=reg.get('legacy_approvals',{})
    for name,tasks in SEGMENTS:
        states={t:graph['tasks'][t]['status'] for t in tasks}
        available=all(v=='APPROVED' for v in states.values())
        authorities={}
        for t,state in states.items():
            if state!='APPROVED': continue
            if t in legacy: authorities[t]=legacy[t].get('accepted_source')
            else:
                w=by_task.get(t)
                if not w or w.get('status')!='APPROVED' or not w.get('candidate_commit'):
                    errors.append(name+' approved graph state lacks matching registry authority for '+t)
                    authorities[t]=None
                else: authorities[t]=w.get('candidate_commit')
        if not available and first_pending is None: first_pending={'segment':name,'tasks':tasks,'states':states}
        rows.append({'segment':name,'tasks':tasks,'states':states,'available':available,'authoritative_sources':authorities})
    implemented=[r['segment'] for r in rows if r['available']]
    pending=[r['segment'] for r in rows if not r['available']]
    return {'passed':not errors,'implemented_segments':implemented,'pending_segments':pending,'next_missing_segment':first_pending,'segments':rows,'formal_acceptance_task':'T32','this_is_readiness_not_formal_acceptance':True,'errors':errors}
if __name__=='__main__':
    out=validate();print(json.dumps(out,indent=2));raise SystemExit(0 if out['passed'] else 2)
