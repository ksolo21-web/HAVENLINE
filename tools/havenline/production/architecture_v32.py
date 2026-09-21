#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from pathlib import Path
from parallel_preparation_planner import plan as prep_plan,classify
from task_graduation_gate import evaluate as graduation
from timeout_stage_plan import plan as stage_plan
from rolling_canary import validate_policy as validate_canaries,requirements as canary_requirements
from performance_ledger import validate as validate_performance
from branch_budget import validate as validate_branches
ROOT=Path(__file__).resolve().parents[3];DOCS=ROOT/'Docs'/'Production'
def validate():
    errors=[];components={}
    for n in ('PRODUCTION_ARCHITECTURE_V32_STANDARD.md','PARALLEL_PREPARATION_POLICY.json','EXECUTION_CHECKPOINT_SCHEMA.json','TASK_GRADUATION_POLICY.json','EARLY_CANARY_POLICY.json','CUMULATIVE_PERFORMANCE_LEDGER.json','CRITIC_PACKAGE_PREFLIGHT_POLICY.json'):
        if not (DOCS/n).exists(): errors.append('missing '+n)
    components['parallel_preparation']=prep_plan();components['canaries']=validate_canaries();components['performance_ledger']=validate_performance();components['branch_budget']=validate_branches()
    for k,v in components.items():
        if not v.get('passed',True): errors += [k+': '+x for x in v.get('errors',[])]
    t11=graduation('T11','ASSIGNED');components['t11_assignment_graduation']=t11
    if not t11['passed']: errors += ['T11 graduation: '+x for x in t11['errors']]
    resolved=0
    for i in range(11,71):
        t=f'T{i:02d}';classify(t);stage_plan(t);canary_requirements(t);resolved+=1
    return {'passed':not errors,'schema_version':1,'architecture_version':'3.2','task_count':resolved,'components':components,'errors':errors}
def readiness(task):
    return {'schema_version':1,'architecture_version':'3.2','task_id':task,'preparation':classify(task),'graduation_assigned':graduation(task,'ASSIGNED'),'stage_plan':stage_plan(task),'canaries':canary_requirements(task)}
def main():
    ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest='cmd',required=True);sub.add_parser('validate');r=sub.add_parser('readiness');r.add_argument('task');a=ap.parse_args();out=validate() if a.cmd=='validate' else readiness(a.task.upper());print(json.dumps(out,indent=2));raise SystemExit(0 if out.get('passed',True) else 2)
if __name__=='__main__':main()
