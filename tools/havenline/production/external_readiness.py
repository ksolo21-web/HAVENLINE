#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];DOCS=ROOT/'Docs'/'Production'
TASK_RE=re.compile(r'^T(\d{2})$')
def load(n): return json.loads((DOCS/n).read_text())
def num(t):
    m=TASK_RE.fullmatch(str(t))
    if not m: raise ValueError('invalid task id '+str(t))
    return int(m.group(1))
def frontier(graph):
    last=0
    for i in range(1,71):
        t=f'T{i:02d}'
        if graph['tasks'][t]['status']=='APPROVED': last=i
        else: break
    return f'T{last:02d}' if last else 'T00'
def evaluate(frontier_task=None):
    roadmap=load('V32_FORWARD_PREP_ROADMAP.json');status=load('CAPABILITY_STATUS.json');graph=load('DEPENDENCY_GRAPH.json');errors=[];rows=[]
    fnum=num(frontier_task) if frontier_task else num(frontier(graph));front=f'T{fnum:02d}'
    for cap,cfg in roadmap.get('external_capability_milestones',{}).items():
        if cap not in status.get('external',{}):
            errors.append('milestone references unknown capability '+cap);continue
        prep=num(cfg['prepare_by']);required=[num(x) for x in cfg['required_by']]
        if not required: errors.append(cap+' has no required_by');continue
        if prep>=min(required): errors.append(cap+' prepare_by must precede first required_by')
        row=status['external'][cap];state=row.get('state');evidence=row.get('evidence')
        if state=='READY' and not evidence: errors.append(cap+' READY without evidence')
        if state=='READY': phase='READY'
        elif fnum<prep: phase='NOT_DUE'
        elif fnum>=min(required)-1: phase='ACTIVATION_BLOCKER'
        else: phase='PREP_DUE'
        rows.append({'capability':cap,'state':state,'phase':phase,'prepare_by':cfg['prepare_by'],'required_by':cfg['required_by'],'evidence':evidence,'reason':cfg.get('reason')})
    return {'passed':not errors,'frontier':front,'ready':[x['capability'] for x in rows if x['phase']=='READY'],'preparation_due':[x['capability'] for x in rows if x['phase']=='PREP_DUE'],'activation_blockers':[x['capability'] for x in rows if x['phase']=='ACTIVATION_BLOCKER'],'not_due':[x['capability'] for x in rows if x['phase']=='NOT_DUE'],'rows':rows,'errors':errors}
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--frontier');a=ap.parse_args();out=evaluate(a.frontier);print(json.dumps(out,indent=2));raise SystemExit(0 if out['passed'] else 2)
if __name__=='__main__':main()
