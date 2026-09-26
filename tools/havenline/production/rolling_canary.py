#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];DOCS=ROOT/'Docs'/'Production'
def load(): return json.loads((DOCS/'EARLY_CANARY_POLICY.json').read_text())
def num(t): return int(str(t).split('/')[0].replace('T',''))
def requirements(task):
    n=num(task);cfg=load();rows=[]
    for cid,c in cfg['canaries'].items():
        if cid=='physical_reconnaissance':
            if task in c['checkpoints']: rows.append({'canary':cid,'mode':'reconnaissance','rule':c['rule']})
            continue
        if n>=num(c['starts_at']): rows.append({'canary':cid,'mode':c.get('mode','required_when_applicable'),'conditional_on':c.get('conditional_on',[]),'rule':c['rule']})
    return {'passed':True,'task_id':task,'canaries':rows}
def validate_policy():
    cfg=load();errors=[]
    for k,v in cfg.get('canaries',{}).items():
        if 'rule' not in v: errors.append(k+' missing rule')
        if 'starts_at' not in v and 'checkpoints' not in v: errors.append(k+' missing activation')
    return {'passed':not errors,'canary_count':len(cfg.get('canaries',{})),'errors':errors}
def main():
    ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest='cmd',required=True);sub.add_parser('validate');r=sub.add_parser('requirements');r.add_argument('task');a=ap.parse_args();out=validate_policy() if a.cmd=='validate' else requirements(a.task.upper());print(json.dumps(out,indent=2));raise SystemExit(0 if out['passed'] else 2)
if __name__=='__main__':main()
