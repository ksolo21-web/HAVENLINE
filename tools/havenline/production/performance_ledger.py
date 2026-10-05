#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];DOCS=ROOT/'Docs'/'Production'
def load(n): return json.loads((DOCS/n).read_text())
def validate():
    led=load('CUMULATIVE_PERFORMANCE_LEDGER.json');bud=load('PERFORMANCE_BUDGETS.json');errors=[]
    if led.get('budget_source')!='Docs/Production/PERFORMANCE_BUDGETS.json': errors.append('wrong budget source')
    if set(led.get('additive_metrics',[]))-set(bud['global_soft_budgets']): errors.append('unknown additive metrics')
    seen=set()
    for e in led.get('entries',[]):
        key=(e.get('task_id'),e.get('candidate_sha'))
        if key in seen: errors.append('duplicate task/candidate entry '+str(key))
        seen.add(key)
    return {'passed':not errors,'entry_count':len(led.get('entries',[])),'errors':errors}
def evaluate_record(path):
    led=load('CUMULATIVE_PERFORMANCE_LEDGER.json');bud=load('PERFORMANCE_BUDGETS.json');rec=json.loads(Path(path).read_text());errors=[];pressure={}
    for m in led['additive_metrics']:
        if m not in rec: continue
        limit=bud['global_soft_budgets'][m];value=rec[m];pressure[m]={'value':value,'global_soft_budget':limit,'remaining':limit-value}
        if value>limit: errors.append(m+' exceeds global soft budget')
    return {'passed':not errors,'task_id':rec.get('task_id'),'candidate_sha':rec.get('candidate_sha'),'pressure':pressure,'errors':errors}
def main():
    ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest='cmd',required=True);sub.add_parser('validate');e=sub.add_parser('evaluate');e.add_argument('record');a=ap.parse_args();out=validate() if a.cmd=='validate' else evaluate_record(a.record);print(json.dumps(out,indent=2));raise SystemExit(0 if out['passed'] else 2)
if __name__=='__main__':main()
