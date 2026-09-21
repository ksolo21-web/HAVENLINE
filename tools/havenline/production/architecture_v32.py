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
from authority_consistency import validate as validate_authority
from forward_prep_contract import validate as validate_forward_prep
from v32_forward_prep_harness import validate_all as validate_forward_harness
from opening_loop_canary import validate as validate_opening_loop
from external_readiness import evaluate as validate_external_readiness
from forward_task_control import validate_all as validate_forward_control
import re
ROOT=Path(__file__).resolve().parents[3];DOCS=ROOT/'Docs'/'Production'
def validate_workflows_and_consumption():
    errors=[]
    workflows={
      'task_preflight':ROOT/'.github/workflows/havenline-v32-task-preflight.yml',
      'specialist_fanout':ROOT/'.github/workflows/havenline-v32-specialist-fanout.yml'
    }
    for name,p in workflows.items():
        if not p.exists(): errors.append('missing workflow '+name);continue
        body=p.read_text()
        for m in re.finditer(r'uses:\s*(actions/[^@\s]+)@([^\s]+)',body):
            if not re.fullmatch(r'[0-9a-f]{40}',m.group(2)): errors.append(name+' mutable/unpinned action '+m.group(0))
    if workflows['task_preflight'].exists():
        body=workflows['task_preflight'].read_text()
        for token in ('architecture_v32.py','task_graduation_gate.py','timeout_stage_plan.py','forward_task_control.py','execution_checkpoint.py','critic_package_preflight.py','havenline-v32-specialist-fanout.yml','havenline-c0-root-cause.yml','cancel-in-progress: false'):
            if token not in body: errors.append('task preflight missing '+token)
    if workflows['specialist_fanout'].exists():
        body=workflows['specialist_fanout'].read_text()
        if 'fail-fast: false' not in body: errors.append('specialist fanout must use fail-fast false')
        if 'havenline-specialist-critic.yml' not in body: errors.append('specialist fanout not bound to reusable critic')
    packet=(ROOT/'tools/havenline/production/task_packet.py').read_text()
    agents=(ROOT/'AGENTS.md').read_text()
    for token in ('Production Architecture V3.2','task_graduation_gate.py','execution_checkpoint.py','blocker_family_gate.py','critic_invalidation.py'):
        if token not in packet: errors.append('task packet consumption missing '+token)
    if 'Production Architecture V3.2 parallel/resumable rule' not in agents: errors.append('AGENTS missing V3.2 mandatory rule')
    fi=json.loads((DOCS/'FAILURE_INTELLIGENCE.json').read_text());ids={x.get('id') for x in fi.get('records',[])}
    for rid in ('FI-T10-001','FI-T10-002','FI-T10-003','FI-T10-004','FI-T10-005','FI-T10-006'):
        if rid not in ids: errors.append('missing promoted T10 lesson '+rid)
    return {'passed':not errors,'errors':errors}

def validate():
    errors=[];components={}
    for n in ('PRODUCTION_ARCHITECTURE_V32_STANDARD.md','PARALLEL_PREPARATION_POLICY.json','EXECUTION_CHECKPOINT_SCHEMA.json','TASK_GRADUATION_POLICY.json','EARLY_CANARY_POLICY.json','CUMULATIVE_PERFORMANCE_LEDGER.json','CRITIC_PACKAGE_PREFLIGHT_POLICY.json','V32_FORWARD_PREP_CONTRACTS.json','V32_FORWARD_PREP_CANARIES.json'):
        if not (DOCS/n).exists(): errors.append('missing '+n)
    components['parallel_preparation']=prep_plan();components['canaries']=validate_canaries();components['performance_ledger']=validate_performance();components['branch_budget']=validate_branches();components['authority_consistency']=validate_authority();components['forward_prep_contract']=validate_forward_prep();components['forward_prep_harness']=validate_forward_harness();components['opening_loop_canary']=validate_opening_loop();components['external_readiness']=validate_external_readiness();components['forward_task_control']=validate_forward_control();components['workflow_consumption']=validate_workflows_and_consumption()
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
