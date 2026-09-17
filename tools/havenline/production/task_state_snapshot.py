#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from pathlib import Path
from lib import DOCS,load_json,expand_alias
try:
    from architecture_v3 import task_readiness
except Exception:
    task_readiness=None
ROOT=Path(__file__).resolve().parents[3]

def snapshot(task_id:str,last_gate:str='UNKNOWN',candidate:str|None=None):
    task_id=task_id.upper();reg=load_json(DOCS/'WORKSTREAM_REGISTRY.json');graph=load_json(DOCS/'DEPENDENCY_GRAPH.json');own=load_json(DOCS/'PATH_OWNERSHIP.json');contracts=load_json(DOCS/'CONTRACT_REGISTRY.json') if (DOCS/'CONTRACT_REGISTRY.json').exists() else {'contracts':{}}
    node=graph['tasks'][task_id];ws=next((w for w in reg['workstreams'] if w.get('task_id')==task_id),{})
    owned=expand_alias(ws.get('owned_paths',[]),own) if ws else []
    produced=[k for k,v in contracts.get('contracts',{}).items() if v.get('owner_task')==task_id]
    consumed=[k for k,v in contracts.get('contracts',{}).items() if task_id in v.get('consumers',[])]
    blockers=list(ws.get('known_blockers',[])) if ws else []
    v3=task_readiness(task_id) if task_readiness and task_id.startswith('T') and task_id[1:].isdigit() and int(task_id[1:])>=10 else None
    if v3 and not v3.get('activation_ready',False):blockers+=v3.get('blockers',[])
    next_action=ws.get('next_action') if ws else ('Generate/freeze task packet and claim ownership when dependencies/capabilities permit.' if node['status']=='LOCKED' else 'Resolve current lifecycle state.')
    return {
      'schema_version':1,'task_id':task_id,'lifecycle_status':node['status'],'integration_branch':reg['integration_branch'],'task_branch':ws.get('branch'),'base_commit':ws.get('base_commit'),'candidate_commit':candidate or ws.get('candidate_commit'),'dependencies':{d:graph['tasks'][d]['status'] for d in node.get('dependencies',[])},'owned_paths':owned,'last_verified_gate':last_gate,'blockers':sorted(set(blockers)),'v3_readiness':v3,'contracts':{'produces':produced,'consumes':consumed},'next_executable_action':next_action,'snapshot_is_derived_not_authority':True
    }

def validate(data:dict):
    schema=load_json(DOCS/'TASK_STATE_SCHEMA.json');missing=set(schema['required_fields'])-set(data);errors=[]
    if missing:errors.append('missing fields: '+','.join(sorted(missing)))
    if data.get('snapshot_is_derived_not_authority') is not True:errors.append('snapshot must remain derived')
    return {'passed':not errors,'errors':errors}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('task');ap.add_argument('--last-gate',default='UNKNOWN');ap.add_argument('--candidate');ap.add_argument('--output');a=ap.parse_args();r=snapshot(a.task,a.last_gate,a.candidate);v=validate(r);r['validation']=v;text=json.dumps(r,indent=2)+'\n';print(text,end='');
    if a.output:(ROOT/a.output).resolve().write_text(text)
    raise SystemExit(0 if v['passed'] else 2)
if __name__=='__main__':main()
