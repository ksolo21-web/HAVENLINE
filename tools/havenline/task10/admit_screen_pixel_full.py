"""Exact canonical admission for one hosted complete T10 screen-pixel proof."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import urllib.parse
import urllib.request

BRANCH='havenline/governance-T10-screen-pixel-full'
WORKFLOW='.github/workflows/havenline-rendered-clearance-t10-screen-pixel-full.yml'
AUTH_PATH='Docs/Production/ChangeRequests/T10-screen-pixel-full-one-shot.json'
KIND='T10_SCREEN_PIXEL_FULL_ONE_SHOT'
DEVICES=('phone_16_9','phone_20_9','tablet_16_10','tablet_4_3','foldable_outer','foldable_inner')
PROFILES=[f'{d}__{scale}' for d in DEVICES for scale in (1.0,0.85,1.35)]+['native4k_full']
FILES=['HavenlineGodot/scripts/world_transform_view.gd','HavenlineGodot/tests/capture_task10_world_transform.gd','tools/havenline/task10/verify_screen_pixel_clearance.py','tools/havenline/task10/run_screen_pixel_canary.py','HavenlineGodot/assets/world_transform_v1/resource_symbols.tres','tools/havenline/production/c0_root_cause_advisor.py','tools/havenline/production/tests/test_c0_builder.py',WORKFLOW,'tools/havenline/task10/admit_screen_pixel_full.py','tools/havenline/task10/tests/test_admit_screen_pixel_full.py','tools/havenline/task10/tests/test_verify_screen_pixel_clearance.py','tools/havenline/task10/preflight_feedback_layout.gd']

def validate(auth,actual,payload,run_id,attempt,canary):
    required={'id':35483383557,'head_sha':'31f08a6830dcb55855f5c7ef2a54ddb773e99b97','status':'completed','conclusion':'success','run_attempt':1}
    if any(canary.get(k)!=v or type(canary.get(k)) is not type(v) for k,v in required.items()):raise ValueError('prerequisite canary is not exact completed PASS')
    prerequisite=auth.get('prerequisite_canary',{})
    if prerequisite.get('run_id')!=required['id'] or prerequisite.get('source')!=required['head_sha'] or prerequisite.get('passed') is not True:raise ValueError('missing accepted canary result')
    for key in ['artifact_zip_sha256','independent_result_review_sha256']:
        value=prerequisite.get(key)
        if not isinstance(value,str) or len(value)!=64 or any(c not in '0123456789abcdef' for c in value):raise ValueError('missing canary proof hash '+key)
    if attempt!='1':raise ValueError('rerun forbidden')
    for key,value in {'task_id':'T10','authorization_kind':KIND,'disposition':'AUTHORIZED_FOR_ONE_DIAGNOSTIC_EXECUTION','diagnostic_execution_authorized':True,'max_runs':1,'domain_cases':684,'task_approved':False,'profiles':PROFILES}.items():
        if auth.get(key)!=value or type(auth.get(key)) is not type(value):raise ValueError('authorization mismatch '+key)
    if actual['ref']!='refs/heads/'+BRANCH or actual['event']!='push':raise ValueError('wrong trigger')
    if auth.get('probe')!=actual:raise ValueError('exact source authorization mismatch')
    count=payload.get('total_count');runs=payload.get('workflow_runs')
    if type(count) is not int or not 0<=count<=100 or not isinstance(runs,list) or len(runs)!=count:raise ValueError('incomplete run history')
    matching=[r for r in runs if r.get('path')==WORKFLOW and r.get('head_sha')==actual['commit'] and r.get('head_branch')==BRANCH and r.get('event')=='push']
    if len(matching)!=1 or str(matching[0].get('id'))!=str(run_id) or (type(matching[0].get('run_attempt')) is not int or matching[0].get('run_attempt')!=1):raise ValueError('one-shot already attempted or current run missing')
    return {'admitted':True,'source':actual['commit'],'tree':actual['tree'],'matching_runs':1,'task_approved':False}

def main():
    out=Path('screen-full/admission');out.mkdir(parents=True,exist_ok=True)
    canonical=subprocess.check_output(['git','rev-parse','origin/codex/havenline-sequential-task-01'],text=True).strip()
    raw=subprocess.check_output(['git','show',canonical+':'+AUTH_PATH]);(out/'canonical-authorization.json').write_bytes(raw)
    auth=json.loads(raw)
    actual={'commit':os.environ['GITHUB_SHA'],'tree':subprocess.check_output(['git','rev-parse','HEAD^{tree}'],text=True).strip(),'ref':os.environ['GITHUB_REF'],'event':os.environ['GITHUB_EVENT_NAME'],'workflow_path':WORKFLOW,'files_sha256':{p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in FILES}}
    query=urllib.parse.urlencode({'branch':BRANCH,'event':'push','head_sha':actual['commit'],'per_page':100})
    url=f"{os.environ['GITHUB_API_URL']}/repos/{os.environ['GITHUB_REPOSITORY']}/actions/runs?{query}"
    req=urllib.request.Request(url,headers={'Accept':'application/vnd.github+json','Authorization':'Bearer '+os.environ['GH_TOKEN'],'X-GitHub-Api-Version':'2022-11-28'})
    with urllib.request.urlopen(req,timeout=30) as response:data=response.read(2_000_001)
    if len(data)>2_000_000:raise ValueError('run history response too large')
    (out/'workflow-runs-api.json').write_bytes(data)
    canary_url=f"{os.environ['GITHUB_API_URL']}/repos/{os.environ['GITHUB_REPOSITORY']}/actions/runs/35483383557"
    canary_request=urllib.request.Request(canary_url,headers=dict(req.header_items()))
    with urllib.request.urlopen(canary_request,timeout=30) as response:canary_raw=response.read(2_000_001)
    if len(canary_raw)>2_000_000:raise ValueError('canary response too large')
    (out/'prerequisite-canary-run.json').write_bytes(canary_raw)
    result=validate(auth,actual,json.loads(data),os.environ['GITHUB_RUN_ID'],os.environ['GITHUB_RUN_ATTEMPT'],json.loads(canary_raw))
    result['prerequisite_canary_api_sha256']=hashlib.sha256(canary_raw).hexdigest()
    result.update(canonical_commit=canonical,authorization_sha256=hashlib.sha256(raw).hexdigest(),history_sha256=hashlib.sha256(data).hexdigest())
    (out/'summary.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
