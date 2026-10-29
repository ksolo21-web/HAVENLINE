#!/usr/bin/env python3
"""Publish ONLY verified artisan saw review assets via GitHub Git Data REST API.

Avoid Git LFS checkout dirty-state when tracked binary blobs and filters differ.
Creates real Git blobs; no direct writes to HavenlineGodot/ shipping assets.
Requires GitHub Actions GITHUB_TOKEN with contents:write.
"""
import base64,hashlib,json,os,sys,time,urllib.request,urllib.error
from pathlib import Path

ROOT=Path(os.environ.get('artisan saw_STAGED_DIR','Docs/Production/T05/NeuralTrials/artisan saw'))
BRANCH=os.environ['GITHUB_REF_NAME']
REPO=os.environ['GITHUB_REPOSITORY']
TOKEN=os.environ['GH_TOKEN']
PREFIX='Docs/Production/T05/ArtisanMaster/SawWIP/'
NAMES=['STATUS.json','checks.json',
       'T05_SAW_ARTISAN_MASTER.blend','T05_SAW_ARTISAN_MODULE.glb',
       'T05_SAW_FRONT_TRACE.png','T05_SAW_RIGHT_HYPOTHESIS.png',
       'T05_SAW_REAR_HYPOTHESIS.png','T05_SAW_ORBIT_CRITIQUE.png']
API='https://api.github.com/repos/'+REPO

def request(method,path,payload=None):
    data=None if payload is None else json.dumps(payload).encode()
    headers={'Authorization':'Bearer '+TOKEN,
      'Accept':'application/vnd.github+json',
      'X-GitHub-Api-Version':'2022-11-28',
      'Content-Type':'application/json',
      'User-Agent':'HAVENLINE-T05-artisan saw-Verified-Git-Artifact-Commit'}
    req=urllib.request.Request(API+path,data=data,method=method,headers=headers)
    with urllib.request.urlopen(req,timeout=120) as response:
        return json.load(response)

audit=json.loads((ROOT/'STATUS.json').read_text())
checks=json.loads((ROOT/'checks.json').read_text())
assert audit['original_sources_verified']==3
assert audit['separate_mesh_objects']>=15
assert not audit['visual_critic_pass'] and not audit['shipping_asset_modified']
assert not audit['whole_cooker_complete'] and not audit['owner_approved']
assert checks['status']=='ACTUAL_BLENDER_SAW_ART_GEOMETRY_AND_4_FRAMES_TECHNICAL_PASS'
entries=[]
for relative in NAMES:
    path=ROOT/relative;blob=path.read_bytes()
    if relative.endswith(('.blend','.glb','.png')):
        assert len(blob)>10000
    if relative.endswith('.png'):
        assert blob[:8]==b'\x89PNG\r\n\x1a\n'
    if relative.endswith('.blend'):
        assert blob[:8]==b'BLENDER-' and hashlib.sha256(blob).hexdigest()==checks['blender_sha256']
    if relative.endswith('.glb'):
        assert blob[:4]==b'glTF' and hashlib.sha256(blob).hexdigest()==checks['glb_sha256']
    print('Uploading verified real blob',relative,len(blob),hashlib.sha256(blob).hexdigest(),flush=True)
    sha=request('POST','/git/blobs',{'content':base64.b64encode(blob).decode(),'encoding':'base64'})['sha']
    entries.append({'path':PREFIX+relative,'type':'blob','mode':'100644','sha':sha})
for attempt in range(4):
    ref=request('GET','/git/ref/heads/'+BRANCH)
    parent=ref['object']['sha']
    current=request('GET','/git/commits/'+parent)
    tree=request('POST','/git/trees',{'base_tree':current['tree']['sha'],'tree':entries})['sha']
    commit=request('POST','/git/commits',{
      'message':'T05 artisan master: save source-traced physical saw WIP, editable Blender rig, GLB, four truthful views (not approved)',
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
