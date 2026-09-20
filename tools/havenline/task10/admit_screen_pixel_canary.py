"""Exact canonical admission for one hosted T10 screen-pixel diagnostic."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import urllib.parse
import urllib.request

BRANCH='havenline/governance-T10-screen-pixel-canary'
WORKFLOW='.github/workflows/havenline-rendered-clearance-t10-screen-pixel-canary.yml'
AUTH_PATH='Docs/Production/ChangeRequests/T10-screen-pixel-canary-one-shot.json'
KIND='T10_SCREEN_PIXEL_CANARY_ONE_SHOT'
PROFILES=['phone_16_9__0.85','phone_16_9__1.0','phone_16_9__1.35','native4k_full','foldable_inner__1.35']
FILES=['HavenlineGodot/scripts/world_transform_view.gd','HavenlineGodot/tests/capture_task10_world_transform.gd','tools/havenline/task10/verify_screen_pixel_clearance.py','tools/havenline/task10/run_screen_pixel_canary.py','HavenlineGodot/assets/world_transform_v1/resource_symbols.tres','tools/havenline/production/c0_root_cause_advisor.py','tools/havenline/production/tests/test_c0_builder.py',WORKFLOW,'tools/havenline/task10/admit_screen_pixel_canary.py','tools/havenline/task10/tests/test_admit_screen_pixel_canary.py','tools/havenline/task10/tests/test_verify_screen_pixel_clearance.py']

def validate(auth,actual,payload,run_id,attempt):
    if attempt!='1':raise ValueError('rerun forbidden')
    for key,value in {'task_id':'T10','authorization_kind':KIND,'disposition':'AUTHORIZED_FOR_ONE_DIAGNOSTIC_EXECUTION','diagnostic_execution_authorized':True,'max_runs':1,'domain_cases':180,'task_approved':False,'profiles':PROFILES}.items():
        if auth.get(key)!=value or type(auth.get(key)) is not type(value):raise ValueError('authorization mismatch '+key)
    if actual['ref']!='refs/heads/'+BRANCH or actual['event']!='push':raise ValueError('wrong trigger')
    if auth.get('probe')!=actual:raise ValueError('exact source authorization mismatch')
    count=payload.get('total_count');runs=payload.get('workflow_runs')
    if type(count) is not int or not 0<=count<=100 or not isinstance(runs,list) or len(runs)!=count:raise ValueError('incomplete run history')
    matching=[r for r in runs if r.get('path')==WORKFLOW and r.get('head_sha')==actual['commit'] and r.get('head_branch')==BRANCH and r.get('event')=='push']
    if len(matching)!=1 or str(matching[0].get('id'))!=str(run_id) or (type(matching[0].get('run_attempt')) is not int or matching[0].get('run_attempt')!=1):raise ValueError('one-shot already attempted or current run missing')
    return {'admitted':True,'source':actual['commit'],'tree':actual['tree'],'matching_runs':1,'task_approved':False}

def main():
    out=Path('screen-canary/admission');out.mkdir(parents=True,exist_ok=True)
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
    result=validate(auth,actual,json.loads(data),os.environ['GITHUB_RUN_ID'],os.environ['GITHUB_RUN_ATTEMPT'])
    result.update(canonical_commit=canonical,authorization_sha256=hashlib.sha256(raw).hexdigest(),history_sha256=hashlib.sha256(data).hexdigest())
    (out/'summary.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
