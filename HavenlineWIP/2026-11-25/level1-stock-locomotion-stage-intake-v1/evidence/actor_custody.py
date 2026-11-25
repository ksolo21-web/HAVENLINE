"""Build normalization inputs only; known-custody source weights, no animation change."""
from pathlib import Path
import json,hashlib,sys,shutil
current,earlier,stage,output=map(Path,sys.argv[1:])
prior=json.loads((earlier/'frames.LOCAL.json').read_bytes())
digest=lambda x:hashlib.sha256(x.read_bytes()).hexdigest()
assert digest(current)=='5d74b695b85eaf088efe4800643cee2bcd750eef91a904ff45b002c21c75a77a'
d,=[json.loads(l.split(' ',1)[1]) for l in current.open() if l.startswith('STOCK_PRIVATE_START ')]
a,=d['surface_roles']; assert a['native_import_packed_godot_variant_sha256']=='40e5a494bcf7c8df60cfe0ce6b2716f2f72c25f979cb8c8a354f00874633c449'
assert d['bones']==66 and a['vertices']==52898 and a['indices']==288003
assert [x['bind_inverse'] for x in d['bindings']]==prior['bind_inverse_by_slot']
assert len({x['bone'] for x in d['bindings']})==66
for prop in ['albedo_texture','normal_texture','roughness_texture','metallic_texture']:
 assert [a[prop]['width'],a[prop]['height']]==[4096,4096]
weights=earlier/prior['native_weights_relative']; assert digest(weights)==prior['native_weights_sha256']
samples=json.loads((stage/'poses-LOCAL.json').read_bytes())
assert len(samples)==45 and set(s['phase'] for s in samples)=={'idle','walk','run','turn','stop'}
for s in samples:
 c=s['character']; assert c['visibility'] and len(c['poses_by_skin_binding_slot'])==66 and c['clip']==s['clip'] and c['clip_t']==s['clip_t']
# The same hash binds the exact array, not a fallback rig. Previous native sparse
# world vertex markers were from transfer poses only: do not mark them as current.
j=output/'stock-bearing-manifest-LOCAL.json'; assert not j.exists(); output.mkdir(mode=0o700)
p=output/'stock-native-weights-LOCAL.bin'; assert not p.exists(); shutil.copyfile(weights,p); p.chmod(0o600)
payload={'source_actor_glb_sha256':prior['actor_source_glb_sha256'],'native_array_sha256':a['native_import_packed_godot_variant_sha256'],
'actor_provenance':'same original current stock geometry and native full skin array; current per-frame bone poses; no independent per-frame world vertices in stock capture','fresh_world_vertex_controls':False,
'bind_inverse_by_slot':prior['bind_inverse_by_slot'],'verified_glb_joint_to_native_slot':prior['verified_glb_joint_to_native_slot'],
'native_weights_relative':p.name,'native_weights_sha256':digest(p),'samples':samples}
with j.open('x') as f:json.dump(payload,f,separators=(',',':'))
j.chmod(0o600)
print(json.dumps({'same_exact_canonical_actor':True,'same_native_array_sha256':a['native_import_packed_godot_variant_sha256'],'source_original_glb_sha256':prior['actor_source_glb_sha256'],
 'compatible_poses_selected':len(samples),'fresh_world_point_controls':False,'prepped_private_inputs_sha256':digest(j),'graphics':False},indent=2))
