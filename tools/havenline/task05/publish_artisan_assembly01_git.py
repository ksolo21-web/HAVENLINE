#!/usr/bin/env python3
"""GitHub-only atomic publication of T05 Assembly01's REAL source binary files.

Called after exact Godot corrected view audit. This bypasses checkout Git-LFS
dirty-state and writes direct Git blobs only under the unapproved T05 directory.
No shipping assets, PR merge, critic pass, or new accounts.
"""
import base64,hashlib,json,os,sys,time,urllib.request,urllib.error
from pathlib import Path

ROOT=Path(os.environ['T05_ASSEMBLY_ROOT'])
REPO=os.environ['GITHUB_REPOSITORY']
BRANCH=os.environ['GITHUB_REF_NAME']
TOKEN=os.environ['GH_TOKEN']
PREFIX="Docs/Production/T05/ArtisanMaster/Assembly01/"
NAMES=[
 "STATUS.json",
 "T05_ARTISAN_ASSEMBLY_01_SAW_BLUE_WOOD.blend",
 "T05_ASSEMBLY_01_SAW_BLUE_WOOD_UNAPPROVED.glb",
 "ASSEMBLY_owner_three_quarter.png","ASSEMBLY_saw_mount_front.png",
 "ASSEMBLY_right_side.png","ASSEMBLY_rear_joinery.png",
 "ASSEMBLY_low_timber_fit.png",
 "NativeGodot/godot_source_three_quarter.png",
 "NativeGodot/godot_saw_front.png",
 "NativeGodot/godot_right_side.png",
 "NativeGodot/godot_rear.png",
 "NativeGodot/godot_underframe.png",
 "NativeGodot/godot_receipt.json"]
s=json.loads((ROOT/'STATUS.json').read_text())
assert s['saw_source_geometry_and_transforms_untouched']
assert s['saw_meshes']>=12 and s['new_wood_objects']>=40
assert s['native_godot_4_7_2_5_views_verified']
assert not s['independent_visual_critic_passed'] and not s['owner_approved']
assert not s['shipping_asset_modified']
for name in ['T05_ARTISAN_ASSEMBLY_01_SAW_BLUE_WOOD.blend','T05_ASSEMBLY_01_SAW_BLUE_WOOD_UNAPPROVED.glb']:
    assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==s[name+'_sha256']
for name,sha in s['native_images_sha256'].items():
    assert hashlib.sha256((ROOT/'NativeGodot'/name).read_bytes()).hexdigest()==sha
for filename,sha in s['source_originals_sha256'].items():
    assert hashlib.sha256((Path('Docs/Art/SourceReferences/T05')/filename).read_bytes()).hexdigest()==sha
assert len(s['native_images_sha256'])==5

def gitreq(method,path,payload=None):
    body=None if payload is None else json.dumps(payload).encode('utf8')
    headers={'Authorization':'Bearer '+TOKEN,'Accept':'application/vnd.github+json',
             'X-GitHub-Api-Version':'2022-11-28','Content-Type':'application/json',
             'User-Agent':'HAVENLINE-T05-Artisan-Assembly01-Real-Binary-Publisher'}
    request=urllib.request.Request('https://api.github.com/repos/'+REPO+path,headers=headers,data=body,method=method)
    with urllib.request.urlopen(request,timeout=130) as response:
        return json.load(response)
entries=[]
for name in NAMES:
    data=(ROOT/name).read_bytes()
    if name.endswith('.png'):
        assert data[:8]==b'\x89PNG\r\n\x1a\n' and len(data)>15000
    elif name.endswith(('.blend','.glb')):
        assert len(data)>250000
    sha=gitreq('POST','/git/blobs',{'encoding':'base64','content':base64.b64encode(data).decode()})['sha']
    entries.append({'path':PREFIX+name,'mode':'100644','type':'blob','sha':sha})
    print('T05 real source blob:',name,len(data),sha,flush=True)
for attempt in range(5):
    ref=gitreq('GET','/git/ref/heads/'+BRANCH)
    head=ref['object']['sha']
    base=gitreq('GET','/git/commits/'+head)['tree']['sha']
    tree=gitreq('POST','/git/trees',{'base_tree':base,'tree':entries})['sha']
    commit=gitreq('POST','/git/commits',{
      'message':'T05 artisan assembly01: retain unaltered saw, editable blue/wood housing and five corrected native Godot visual FAIL evidence',
      'tree':tree,'parents':[head]})['sha']
    try:
        gitreq('PATCH','/git/refs/heads/'+BRANCH,{'sha':commit,'force':False})
        print(json.dumps({'status':'REAL_BINARIES_IN_GIT_VERIFIED',
          'commit':commit,'files':len(entries),'saw_source_preserved':True,
          'native_5_corrected_views':True,'visual_critic_pass':False,
          'shipping_asset_modified':False},indent=2))
        sys.exit(0)
    except urllib.error.HTTPError as exc:
        if exc.code not in (409,422) or attempt==4:raise
        time.sleep(1.5)
raise RuntimeError("Could not update review-only Git branch")
