#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];DOCS=ROOT/'Docs'/'Production'
ACTIVE={'ASSIGNED','BUILDING_ISOLATED','BUILT_PENDING_DEPENDENCY','INTEGRATION_READY','INTEGRATING','UNDER_REVIEW','FIX_REQUIRED'}
def load(name): return json.loads((DOCS/name).read_text())
def required_caps(task,profiles,matrix,critics):
    p=profiles['tasks'][task];caps=[];caps+=matrix.get('base_requirements',[]);caps+=matrix.get('mode_requirements',{}).get(p['mode'],[]);caps+=matrix.get('archetype_requirements',{}).get(p['archetype'],[])
    for c in critics['task_applicability'].get(task,[]): caps+=matrix.get('critic_requirements',{}).get(c,[])
    caps+=matrix.get('task_overrides',{}).get(task,{}).get('required',[]);return list(dict.fromkeys(caps))
def classify(task):
    graph=load('DEPENDENCY_GRAPH.json');registry=load('WORKSTREAM_REGISTRY.json');profiles=load('FORWARD_EXECUTION_PROFILES.json');matrix=load('TASK_CAPABILITY_MATRIX.json');status=load('CAPABILITY_STATUS.json');critics=load('CRITIC_MATRIX.json');policy=load('PARALLEL_PREPARATION_POLICY.json')
    row=graph['tasks'][task];ws=next((w for w in registry['workstreams'] if w['task_id']==task),None);dep={d:graph['tasks'][d]['status'] for d in row['dependencies']};deps_ok=all(v=='APPROVED' for v in dep.values());external=[]
    for cap in required_caps(task,profiles,matrix,critics):
        cfg=matrix['catalog'].get(cap,{})
        if cfg.get('kind') in ('external','hardware'):
            st=status['external'].get(cfg.get('status_key'),{}).get('state','UNVERIFIED')
            if st!='READY': external.append(cap)
    lifecycle=(ws or {}).get('status',row.get('status'))
    if lifecycle=='APPROVED': cls='PRESERVE'
    elif lifecycle in ACTIVE: cls='ACTIVE_RUNTIME'
    elif external: cls='BLOCKED_EXTERNAL'
    elif deps_ok: cls='BUILD_WHEN_UNLOCKED'
    elif task in profiles.get('tasks',{}): cls='PREP_NOW'
    else: cls='DO_NOT_TOUCH'
    return {'task_id':task,'classification':cls,'lifecycle_status':lifecycle,'dependency_status':dep,'dependencies_approved':deps_ok,'external_blockers':external,'workstream_present':ws is not None,'safe_work':policy['safe_work'][cls]}
def plan():
    rows=[classify(f'T{i:02d}') for i in range(11,71)];policy=load('PARALLEL_PREPARATION_POLICY.json');counts={k:sum(1 for r in rows if r['classification']==k) for k in policy['classifications']};active=sum(1 for r in rows if r['classification']=='ACTIVE_RUNTIME')
    return {'passed':active<=policy['wip']['max_parallel_runtime_builds'],'schema_version':1,'rows':rows,'counts':counts,'active_runtime_count':active,'runtime_wip_max':policy['wip']['max_parallel_runtime_builds'],'integration_owner_slots':policy['wip']['integration_owner_slots']}
def main():
    ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest='cmd',required=True);sub.add_parser('validate');p=sub.add_parser('plan');p.add_argument('task',nargs='?');a=ap.parse_args();out=plan() if a.cmd=='validate' or not getattr(a,'task',None) else classify(a.task.upper());print(json.dumps(out,indent=2));raise SystemExit(0 if out.get('passed',True) else 2)
if __name__=='__main__':main()
