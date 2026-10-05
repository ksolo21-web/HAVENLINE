#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];DOCS=ROOT/'Docs'/'Production'
def load(n): return json.loads((DOCS/n).read_text())
def validate():
    graph=load('DEPENDENCY_GRAPH.json');reg=load('WORKSTREAM_REGISTRY.json');errors=[];rows=[]
    for w in reg['workstreams']:
        t=w.get('task_id')
        if t not in graph['tasks']: continue
        gs=graph['tasks'][t]['status'];rs=w.get('status');rows.append({'task_id':t,'graph_status':gs,'registry_status':rs,'candidate_commit':w.get('candidate_commit')})
        if gs!=rs: errors.append(f'{t} lifecycle mismatch graph={gs} registry={rs}')
        if rs=='APPROVED' and not w.get('candidate_commit'): errors.append(t+' approved without candidate_commit')
        if rs!='APPROVED' and w.get('integration_status','').startswith('APPROVED'): errors.append(t+' non-approved lifecycle has approved integration_status')
    return {'passed':not errors,'checked':len(rows),'rows':rows,'errors':errors}
def main():
    out=validate();print(json.dumps(out,indent=2));raise SystemExit(0 if out['passed'] else 2)
if __name__=='__main__':main()
