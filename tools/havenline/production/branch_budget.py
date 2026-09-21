#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];DOCS=ROOT/'Docs'/'Production'
def load(n): return json.loads((DOCS/n).read_text())
def validate(task=None,inventory=None):
    reg=load('WORKSTREAM_REGISTRY.json');policy=load('PARALLEL_PREPARATION_POLICY.json')['branch_budget'];errors=[]
    tasks=[task] if task else sorted({w['task_id'] for w in reg['workstreams'] if w['task_id'].startswith('T') and int(w['task_id'][1:])>=11})
    for t in tasks:
        rows=[w for w in reg['workstreams'] if w['task_id']==t]
        if len(rows)>policy['authoritative_task_branches']: errors.append(t+' has multiple authoritative workstream branches')
    details={'authoritative_registry_tasks':tasks}
    if inventory:
        names=json.loads(Path(inventory).read_text())
        for t in tasks:
            prefix='havenline/'+t+'-';matching=[x for x in names if x.startswith(prefix)]
            repair=[x for x in matching if 'repair' in x.lower()]
            if len(repair)>policy['active_bounded_repair_branches']: errors.append(t+' exceeds active repair branch budget')
        details['inventory_checked']=True
    return {'passed':not errors,'policy':policy,'details':details,'errors':errors}
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--task');ap.add_argument('--inventory');a=ap.parse_args();out=validate(a.task.upper() if a.task else None,a.inventory);print(json.dumps(out,indent=2));raise SystemExit(0 if out['passed'] else 2)
if __name__=='__main__':main()
