#!/usr/bin/env python3
"""Publish ONLY verified R38 review assets via GitHub Git Data REST API.

Avoid Git LFS checkout dirty-state when tracked binary blobs and filters differ.
Creates real Git blobs; no direct writes to HavenlineGodot/ shipping assets.
Requires GitHub Actions GITHUB_TOKEN with contents:write.
"""
import base64,hashlib,json,os,sys,time,urllib.request,urllib.error
from pathlib import Path

ROOT=Path(os.environ.get('R38_STAGED_DIR','Docs/Production/T05/NeuralTrials/R38'))
BRANCH=os.environ['GITHUB_REF_NAME']
REPO=os.environ['GITHUB_REPOSITORY']
TOKEN=os.environ['GH_TOKEN']
PREFIX='Docs/Production/T05/NeuralTrials/R38/'
NAMES=['STATUS.json','T05_R38_3_OWNER_VIEWS_EDITABLE.blend',
       'T05_R38_SOURCE_PROJECTED_UNAPPROVED.glb',
       'NativeGodot/r38_front.png','NativeGodot/r38_side.png',
       'NativeGodot/r38_rear.png','NativeGodot/r38_unobserved_left.png']
API='https://api.github.com/repos/'+REPO

def request(method,path,payload=None):
    data=None if payload is None else json.dumps(payload).encode()
    headers={'Authorization':'Bearer '+TOKEN,
      'Accept':'application/vnd.github+json',
      'X-GitHub-Api-Version':'2022-11-28',
      'Content-Type':'application/json',
      'User-Agent':'HAVENLINE-T05-R38-Verified-Git-Artifact-Commit'}
    req=urllib.request.Request(API+path,data=data,method=method,headers=headers)
    with urllib.request.urlopen(req,timeout=120) as response:
        return json.load(response)

audit=json.loads((ROOT/'STATUS.json').read_text())
assert not audit['art_critic_passed'] and not audit['shipping_asset_modified']
assert audit['triangles']==203064
assert len(audit['owner_original_sha256'])==3
entries=[]
for relative in NAMES:
    path=ROOT/relative;blob=path.read_bytes()
    if relative.endswith(('.blend','.glb','.png')):
        assert len(blob)>10000
    if relative.endswith('.png'):
        assert blob[:8]==b'\x89PNG\r\n\x1a\n'
    if relative.endswith('.glb'):
        assert blob[:4]==b'glTF' and hashlib.sha256(blob).hexdigest()==audit['model_sha256']
    print('Uploading verified real blob',relative,len(blob),hashlib.sha256(blob).hexdigest(),flush=True)
    sha=request('POST','/git/blobs',{'content':base64.b64encode(blob).decode(),'encoding':'base64'})['sha']
    entries.append({'path':PREFIX+relative,'type':'blob','mode':'100644','sha':sha})
for attempt in range(4):
    ref=request('GET','/git/ref/heads/'+BRANCH)
    parent=ref['object']['sha']
    current=request('GET','/git/commits/'+parent)
    tree=request('POST','/git/trees',{'base_tree':current['tree']['sha'],'tree':entries})['sha']
    commit=request('POST','/git/commits',{
      'message':'T05 R38: retain real packed Blender reference workbench, owner-image volumetric GLB and native four-angle critic FAIL',
      'tree':tree,'parents':[parent]})['sha']
    try:
        request('PATCH','/git/refs/heads/'+BRANCH,{'sha':commit,'force':False})
        print(json.dumps({'status':'SUCCESS_REAL_ARTIFACTS_COMMITTED','commit':commit,
          'files':len(entries),'source_images':3,'visual_critic_pass':False,
          'shipping_asset_modified':False},indent=2),flush=True)
        sys.exit(0)
    except urllib.error.HTTPError as ex:
        if ex.code not in (409,422) or attempt==3:
            raise
        print('Branch moved; retrying on latest head',attempt+1,flush=True)
        time.sleep(2)
raise RuntimeError('Failed after 4 fast-forward attempts')
