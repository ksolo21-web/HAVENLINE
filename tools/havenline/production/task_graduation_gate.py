#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from pathlib import Path
from parallel_preparation_planner import classify
ROOT=Path(__file__).resolve().parents[3];DOCS=ROOT/'Docs'/'Production'
def load(p): return json.loads(Path(p).read_text())
def exists_any(paths): return next((p for p in paths if p.exists()),None)
def evaluate(task,target):
    task=task.upper();graph=load(DOCS/'DEPENDENCY_GRAPH.json');registry=load(DOCS/'WORKSTREAM_REGISTRY.json');ownership=load(DOCS/'PATH_OWNERSHIP.json');policy=load(DOCS/'TASK_GRADUATION_POLICY.json');critics=load(DOCS/'CRITIC_MATRIX.json');ws=next((w for w in registry['workstreams'] if w['task_id']==task),None);errors=[];checks={}
    def ck(name,value,detail=''):
        checks[name]=bool(value)
        if not value: errors.append(name+((': '+detail) if detail else ''))
    deps=graph['tasks'][task]['dependencies'];ck('dependencies_approved',all(graph['tasks'][d]['status']=='APPROVED' for d in deps));packet=exists_any([DOCS/task/'TASK_PACKET.md',DOCS/'Evidence'/task/'TASK_PACKET.md']);ck('canonical_packet',packet is not None);ck('frozen_scope',(DOCS/task/'FROZEN_SCOPE.md').exists());ck('registered_workstream',ws is not None)
    if ws:
        ck('owner',bool(ws.get('owner')));ck('isolated_branch',str(ws.get('branch','')).startswith('havenline/'));aliases=ownership.get('aliases',{});owned=ws.get('owned_paths',[]);ck('owned_path_reservation',bool(owned) and all(x in aliases for x in owned));ck('critic_contract',set(ws.get('critic_requirements',[]))==set(critics['task_applicability'].get(task,[])));activation=DOCS/task/'ACTIVATION_CHECKLIST.json';ck('activation_checklist',activation.exists())
        if activation.exists():
            a=load(activation);ck('activation_task_identity',a.get('task_id')==task);ck('activation_branch_identity',a.get('builder_branch')==ws.get('branch'))
    else:
        for name in ('owner','isolated_branch','owned_path_reservation','critic_contract','activation_checklist'): ck(name,False)
    prep=classify(task);ck('no_required_external_blocker',not prep.get('external_blockers'));assigned_pass=not errors
    if target=='BUILDING_ISOLATED':
        ck('assigned_gate_pass',assigned_pass);manifest=DOCS/task/'GRADUATION.json';ck('graduation_manifest',manifest.exists())
        if manifest.exists():
            g=load(manifest)
            for f in policy['graduation_manifest_fields']: ck('graduation_'+f,f in g and bool(g[f]))
            for key in ('sentinel_adapter','focused_tests','task_workflow','checkpoint_path'):
                if g.get(key): ck(key+'_exists',(ROOT/g[key]).exists(),g[key])
            wf=(ROOT/g['task_workflow']) if g.get('task_workflow') else None
            if wf and wf.exists():
                body=wf.read_text()
                for token in policy.get('workflow_required_tokens',[]): ck('workflow_token_'+token,token in body)
                required=set((ws or {}).get('critic_requirements',[]))
                if required.intersection(policy.get('specialist_fanout_critics',[])):
                    ck('workflow_specialist_review',all(token in body for token in policy.get('specialist_review_tokens',[])))
                if policy.get('performance_ledger_required_when_critic') in required: ck('workflow_performance_ledger','performance_ledger.py' in body)
            if g.get('checkpoint_path') and (ROOT/g['checkpoint_path']).exists():
                from execution_checkpoint import validate_record
                ck('execution_checkpoint',validate_record(load(ROOT/g['checkpoint_path']))['passed'])
    return {'passed':not errors,'task_id':task,'target':target,'checks':checks,'classification':prep['classification'],'errors':errors}
def main():
    ap=argparse.ArgumentParser();ap.add_argument('task');ap.add_argument('--target',choices=['ASSIGNED','BUILDING_ISOLATED'],default='ASSIGNED');a=ap.parse_args();out=evaluate(a.task,a.target);print(json.dumps(out,indent=2));raise SystemExit(0 if out['passed'] else 2)
if __name__=='__main__':main()
