#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from architecture_v3 import task_readiness as v3_readiness, validate as validate_v3
from flake_intelligence import validate as validate_flakes
from pipeline_telemetry import validate as validate_telemetry
from ci_toolchain_lock import validate as validate_toolchain
from evidence_retention import validate_policy as validate_retention
from runtime_dependency_learning import validate as validate_runtime_dependencies
from task_state_snapshot import snapshot,validate as validate_snapshot
from mutation_canary import run_canaries
from proof_invalidation import validate_policy as validate_invalidation

ACTIVE_RUNTIME_STATES={'ASSIGNED','BUILDING_ISOLATED','BUILT_PENDING_DEPENDENCY','INTEGRATION_READY','INTEGRATING','UNDER_REVIEW' ,'FIX_REQUIRED'}

def task_readiness(task_id:str):
    task_id=task_id.upper();v3=v3_readiness(task_id);state=snapshot(task_id)
    capability_ready=bool(v3.get('runtime_activation_allowed'))
    packet_ready=bool(v3.get('feasibility',{}).get('canonical_packet_present'))
    lifecycle_ready=state.get('lifecycle_status') in ACTIVE_RUNTIME_STATES
    ownership_ready=bool(state.get('task_branch')) and bool(state.get('owned_paths'))
    blockers=[]
    if not capability_ready:blockers.append('v3_capability_or_dependency_not_ready')
    if not packet_ready:blockers.append('canonical_packet_missing')
    if not lifecycle_ready:blockers.append('lifecycle_not_activated')
    if not ownership_ready:blockers.append('ownership_not_assigned')
    return {'schema_version':1,'task_id':task_id,'v3':v3,'task_state':state,'v31_controls':{'flake_intelligence':'ENABLED','pipeline_telemetry':'ENABLED','ci_toolchain_lock':'ENFORCED','evidence_retention':'ENFORCED','runtime_dependency_learning':'ADDITIVE_ONLY','canonical_task_state':'ENABLED','mutation_canaries':'ENFORCED','transitive_proof_invalidation':'ENFORCED'},'activation_blockers':blockers,'runtime_activation_allowed':not blockers}
def validate():
    components={'v3':validate_v3(),'flake':validate_flakes(),'telemetry':validate_telemetry(),'toolchain':validate_toolchain(),'retention':validate_retention(),'runtime_dependencies':validate_runtime_dependencies(),'mutation_canaries':run_canaries(),'proof_invalidation':validate_invalidation()};errors=[]
    for name,row in components.items():
        if not row.get('passed',True):errors.append(name+': '+', '.join(row.get('errors',[])))
    snapshots=[]
    for i in range(9,71):
        s=snapshot(f'T{i:02d}');v=validate_snapshot(s);snapshots.append(s)
        if not v['passed']:errors.append(f'T{i:02d} task snapshot invalid: '+', '.join(v['errors']))
    return {'passed':not errors,'schema_version':1,'task_count':62,'components':components,'snapshot_count':len(snapshots),'errors':errors}
def main():
    ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest='cmd',required=True);sub.add_parser('validate');r=sub.add_parser('readiness');r.add_argument('task_id');a=ap.parse_args();out=validate() if a.cmd=='validate' else task_readiness(a.task_id);print(json.dumps(out,indent=2));raise SystemExit(0 if out.get('passed',True) else 2)
if __name__=='__main__':main()
