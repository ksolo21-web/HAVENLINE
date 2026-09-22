#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,subprocess
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
from gate_result_recorder import validate_index as validate_gate_recording
from failure_learning import validate_tool as validate_failure_learning
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
        for token in ('architecture_v32.py','task_graduation_gate.py','control_plane_lineage.py','timeout_stage_plan.py','forward_task_control.py','execution_checkpoint.py','critic_package_preflight.py','gate_result_recorder.py','havenline-v32-specialist-fanout.yml','havenline-c0-root-cause.yml','cancel-in-progress: false'):
            if token not in body: errors.append('task preflight missing '+token)
    if workflows['specialist_fanout'].exists():
        body=workflows['specialist_fanout'].read_text()
        if 'fail-fast: false' not in body: errors.append('specialist fanout must use fail-fast false')
        if 'havenline-specialist-critic.yml' not in body: errors.append('specialist fanout not bound to reusable critic')
        if 'havenline-v32-independent-specialist-batch' not in body or 'cancel-in-progress: false' not in body: errors.append('specialist fanout missing batch capacity concurrency')
    packet=(ROOT/'tools/havenline/production/task_packet.py').read_text()
    agents=(ROOT/'AGENTS.md').read_text()
    for token in ('Production Architecture V3.2','task_graduation_gate.py','control_plane_lineage.py','v32_assignment_claim.py','execution_checkpoint.py','blocker_family_gate.py','critic_invalidation.py'):
        if token not in packet: errors.append('task packet consumption missing '+token)
    if 'Production Architecture V3.2 parallel/resumable rule' not in agents: errors.append('AGENTS missing V3.2 mandatory rule')
    shared_control=(ROOT/'.github/workflows/havenline-v32-task-preflight.yml').read_text()
    if 'failure_learning.py propose' not in shared_control or 'failure-learning-after-c0' not in shared_control: errors.append('shared control missing post-C0 failure-learning staging')
    governance_path=ROOT/'.github/workflows/havenline-production-governance.yml'
    if not governance_path.exists():
        errors.append('missing top-level production governance workflow')
    else:
        governance=governance_path.read_text()
        for token in ('t11_lineage_builder','lineage_integration_sha','t11_assignment_sha','task_graduation_gate.py T11 --target ASSIGNED --builder-head "$t11_lineage_builder" --integration-head "$lineage_integration_sha"','forward_task_control.py plan T11 --target ASSIGNED --builder "$t11_lineage_builder" --integration "$lineage_integration_sha"'):
            if token not in governance: errors.append('top-level governance missing exact T11 lineage binding: '+token)
    fi=json.loads((DOCS/'FAILURE_INTELLIGENCE.json').read_text());ids={x.get('id') for x in fi.get('records',[])}
    for rid in ('FI-T10-001','FI-T10-002','FI-T10-003','FI-T10-004','FI-T10-005','FI-T10-006'):
        if rid not in ids: errors.append('missing promoted T10 lesson '+rid)
    return {'passed':not errors,'errors':errors}

def validate():
    errors=[];components={}
    for n in ('PRODUCTION_ARCHITECTURE_V32_STANDARD.md','PARALLEL_PREPARATION_POLICY.json','EXECUTION_CHECKPOINT_SCHEMA.json','TASK_GRADUATION_POLICY.json','EARLY_CANARY_POLICY.json','CUMULATIVE_PERFORMANCE_LEDGER.json','CRITIC_PACKAGE_PREFLIGHT_POLICY.json','V32_FORWARD_PREP_CONTRACTS.json','V32_FORWARD_PREP_CANARIES.json'):
        if not (DOCS/n).exists(): errors.append('missing '+n)
    components['parallel_preparation']=prep_plan();components['canaries']=validate_canaries();components['performance_ledger']=validate_performance();components['branch_budget']=validate_branches();components['authority_consistency']=validate_authority();components['forward_prep_contract']=validate_forward_prep();components['forward_prep_harness']=validate_forward_harness();components['opening_loop_canary']=validate_opening_loop();components['external_readiness']=validate_external_readiness();components['forward_task_control']=validate_forward_control();components['gate_result_recording']=validate_gate_recording();components['failure_learning']=validate_failure_learning();components['workflow_consumption']=validate_workflows_and_consumption()
    for k,v in components.items():
        if not v.get('passed',True): errors += [k+': '+x for x in v.get('errors',[])]
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    graph=json.loads((DOCS/'DEPENDENCY_GRAPH.json').read_text())
    t11_status=graph.get('tasks',{}).get('T11',{}).get('status')
    if t11_status in ('PREPARED','ASSIGNED'):
        t11=graduation('T11','ASSIGNED',head,head)
        components['t11_assignment_graduation']=t11
        if not t11['passed']: errors += ['T11 graduation: '+x for x in t11['errors']]
    else:
        components['t11_assignment_graduation']={'passed':True,'not_applicable':True,'lifecycle_status':t11_status}
    resolved=0
    for i in range(11,71):
        t=f'T{i:02d}';classify(t);stage_plan(t);canary_requirements(t);resolved+=1
    return {'passed':not errors,'schema_version':1,'architecture_version':'3.2','task_count':resolved,'components':components,'errors':errors}
def readiness(task,builder_head=None,integration_head=None,target='ASSIGNED'):
    grad=graduation(task,target,builder_head,integration_head)
    return {'schema_version':1,'architecture_version':'3.2','task_id':task,'preparation':classify(task),'graduation':grad,'graduation_assigned':grad if target=='ASSIGNED' else None,'graduation_target':target,'stage_plan':stage_plan(task),'canaries':canary_requirements(task)}
def main():
    ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest='cmd',required=True);sub.add_parser('validate');r=sub.add_parser('readiness');r.add_argument('task');r.add_argument('--builder-head');r.add_argument('--integration-head');r.add_argument('--target',choices=['ASSIGNED','BUILDING_ISOLATED'],default='ASSIGNED');a=ap.parse_args();out=validate() if a.cmd=='validate' else readiness(a.task.upper(),a.builder_head,a.integration_head,a.target);print(json.dumps(out,indent=2));raise SystemExit(0 if out.get('passed',True) else 2)
if __name__=='__main__':main()
