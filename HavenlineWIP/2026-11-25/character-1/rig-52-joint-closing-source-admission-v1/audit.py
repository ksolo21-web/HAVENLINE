import hashlib,json,struct,subprocess,sys
from pathlib import Path
import numpy as np
def glb(b):
 n,tag=struct.unpack_from('<II',b,12); assert tag==0x4e4f534a
 d=json.loads(b[20:20+n]); skins=d.get('skins',[])
 joints=set(j for skin in skins for j in skin['joints'])
 return {'sha256':hashlib.sha256(b).hexdigest(),'skins_joint_counts':[len(s['joints']) for s in skins],'animation_tracks':[{ 'name':a.get('name'),'channels':len(a['channels']),'joint_rotation_channels':sum(c['target'].get('node') in joints and c['target']['path']=='rotation' for c in a['channels'])} for a in d.get('animations',[])]}
p=Path('..'); repo=sys.argv[1]; git=lambda *a:subprocess.check_output(['git','-C',repo,*a]); owner=(p/'c1-nov24-owner-v2/c1-meshy-ultra-multiview.glb').read_bytes()
variants={'owner_geometry':glb(owner)}
assert variants['owner_geometry']['sha256']=='7e3ed20e3cb494415c07c3f85611f6fdafbc0cca53bb972206df26a57b539ffb' and not variants['owner_geometry']['skins_joint_counts'] and not variants['owner_geometry']['animation_tracks']
for rev in ('11c14a1c41971067c7dc97db69375f720a408f68','48c6c53a0dfda117ef12c68b32cfe2b3732d5239'):
 endpoint=rev+':HavenlineLevel1/assets/characters/Character1.glb'
 variants[rev]=glb(git('show',endpoint));variants[rev]['git_blob']=git('rev-parse',endpoint).decode().strip()
rig=p/'c1-full-detail-rig-witness-v1'; rigsha=hashlib.sha256((rig/'bind-evidence.npz').read_bytes()).hexdigest()
with np.load(rig/'bind-evidence.npz') as n:
 assert len(n['names'])==51 and 'hand.R' in n['names']
 schema=n.files
w=p/'hvn-l1-c1-axe-open-close-v1/witness.py'; text=w.read_text()
assert 'not bpy.data.actions' in text and 'Quaternion((1,0,0),math.radians(dg))' in text
ready=p/'hvn-t09-narrow-ready-witness.yFldwO/HANDOFF.md'
assert 'No adjacent poses, action, tool, grip' in ready.read_text()
print(json.dumps({'glb_manifest':variants,'detached_bind_npz_sha256':rigsha,'detached_bind_npz_fields':schema,'detached_closing_diagnostic_sha256':hashlib.sha256(w.read_bytes()).hexdigest(),'body_only_handoff_sha256':hashlib.sha256(ready.read_bytes()).hexdigest(),'signed_binding_authority_found':False},indent=2))
