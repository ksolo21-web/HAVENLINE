#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];DOCS=ROOT/'Docs'/'Production'
from forward_execution import resolve_task
def load(n): return json.loads((DOCS/n).read_text())
def plan(task):
    f=resolve_task(task);critics=load('CRITIC_MATRIX.json')['task_applicability'].get(task,[]);gates=f['ordered_gates'];groups=[('preflight',['scope_dependency','ownership','reference_lock','source_contract','focused_unit','task_sentinel']),('domain',['motion_preflight','progression_sim','economy_sim','save_matrix','device_matrix','security_attack','liveops_sim']),('regression_performance',['impacted_regression','performance']),('evidence',['visual_evidence'])];shards=[];prev=None
    for name,names in groups:
        present=[g for g in names if g in gates]
        if not present: continue
        sid='S'+str(len([x for x in shards if x['id'].startswith('S')])+1);shards.append({'id':sid,'name':name,'gates':present,'depends_on':([prev] if prev else []),'target_minutes':12,'checkpoint_after':True});prev=sid
    critic_shards=[]
    for c in critics:
        sid='C-'+c;critic_shards.append({'id':sid,'critic_id':c,'depends_on':([prev] if prev else []),'single_purpose':True,'parallel_group':'critics','checkpoint_after':True})
    shards+=critic_shards;critic_ids=[x['id'] for x in critic_shards]
    if 'integration' in gates:
        sid='S'+str(len([x for x in shards if x['id'].startswith('S')])+1);shards.append({'id':sid,'name':'integration','gates':['integration'],'depends_on':critic_ids or ([prev] if prev else []),'target_minutes':12,'checkpoint_after':True});prev=sid
    post=[g for g in ('post_integration_regression','closeout','release_manifest','physical_device') if g in gates]
    if post:
        sid='S'+str(len([x for x in shards if x['id'].startswith('S')])+1);shards.append({'id':sid,'name':'terminal','gates':post,'depends_on':([prev] if prev else critic_ids),'target_minutes':12,'checkpoint_after':True})
    return {'passed':True,'task_id':task,'candidate_policy':'finish_running_sha','timeout_is_product_judgment':False,'shards':shards,'critic_parallelism':len(critic_shards)}
def main():
    ap=argparse.ArgumentParser();ap.add_argument('task');a=ap.parse_args();print(json.dumps(plan(a.task.upper()),indent=2))
if __name__=='__main__':main()
