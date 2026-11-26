from pathlib import Path
from hashlib import sha256
import json,struct,math
P=Path(__file__).resolve().parent
H=P.parent
R=H/'t05-integration-proof'
S=H/'hvn-l1-owner-gate-33035-v4-native-preflight-v1/staged/HavenlineLevel1'
A=R/'desktop/HavenlineGodot/assets/stations_v2/review/cooker_v18.glb'
def sha(path):return sha256(path.read_bytes()).hexdigest()
def root_pin(p,d):
 assert sha(p)==d
 for l in p.read_text().splitlines():
  x,y=l.split(maxsplit=1); assert sha(p.parent/y.removeprefix('*'))==x
root_pin(R/'SHA256SUMS.txt','6fe25d963334e4a84bf1f838987c2c9fe6a30e1422ea5ba5d2d7e7c909c2a2fb')
assert sha(A)=='1173994824998d02c1d2cfa86ac4f0f7c88381eddc1715d81680a11c68cdcbba'
raw=A.read_bytes()
m,ver,length,n,j=struct.unpack_from('<4sIIII',raw)
assert (m,ver,length,j)==(b'glTF',2,len(raw),0x4e4f534a)
d=json.loads(raw[20:20+n])
model_tri=0
for mesh in d['meshes']:
 for p in mesh['primitives']:
  assert p.get('mode',4)==4
  a=d['accessors'][p['indices'] if 'indices' in p else p['attributes']['POSITION']]
  assert a['count']%3==0
  model_tri+=a['count']//3
assert model_tri==251167 and len(d['materials'])==56
counts={k:len(d.get(k,[])) for k in ('nodes','meshes','materials','animations','images')}
r=json.loads([l for l in (R/'scale-review/bounds.jsonl').read_text().splitlines() if l.startswith('{')][0])
layout=json.loads((S/'layout.json').read_text())
assert r['character_authored_normalized_height']==layout['actor_height']==1.75
assert layout['furnace_xz']==[0,0] and layout['furnace_cost']=={'wood':3}
assert layout['pad_xz']==[0,2.4] and layout['actor_radius']==.31
opening=(S/'opening.gd').read_text()
assert 'model(HERO, actor, float(layout.actor_height))' in opening and opening.count('res://assets/studio/hearth_trial_02.glb')==1
assert "model(HEARTH, vessel_root, 1.8)" in opening
assert 'cooker_v18.glb' not in opening
assert all(x['id']==y for x,y in zip(layout['gates'],['gate-south','gate-east']))
def scale(xyz,k):return [v*k for v in xyz]
def decide(dim,roles,authority=False):
 # Fixture only. A caller can never authorize processing or mounting from this tool.
 if len(dim)!=3 or any(type(a) not in (int,float) or not math.isfinite(a) or a<=0 for a in dim):
  return 'reject-bad-dimensions'
 if len(roles)!=len(set(roles)) or roles: return 'reject-new-socket-input-or-recipe-authority'
 if authority is not False:return 'reject-non-fixture'
 if dim[2]>2.300001: return 'reject-historical-frozen-depth-envelope'
 return 'historical-fit-only-native-current-site-unwitnessed'
v=r['meshes']['new_v18']['size_xyz']; conv=r['meshes']['conveyor_straight']['size_xyz'][1]
tests={}
for name,k in [('historical_fit',1.0),('historical_test_+25_percent',1.25),('match_historical_conveyor_height',conv/v[1]),('match_current_hero_height',layout['actor_height']/v[1])]:
 xyz=scale(v,k);tests[name]={'world_xyz_m':xyz,'height_to_character1_target':xyz[1]/layout['actor_height'],
  'legacy_socket_plane_delta_on_either_z_end_positive_is_overhang_m':xyz[2]/2-1.35,'decision':decide(xyz,[])}
assert tests['historical_fit']['decision'].startswith('historical-fit-only')
assert all(tests[a]['decision']=='reject-historical-frozen-depth-envelope' for a in tests if a!='historical_fit')
assert decide(v,['fish'])=='reject-new-socket-input-or-recipe-authority'
assert decide(v,['use_interact'])=='reject-new-socket-input-or-recipe-authority'
assert decide(v,[],True)=='reject-non-fixture'
assert decide([0,1,2],[])=='reject-bad-dimensions'
assert decide([1,1,float('nan')],[])=='reject-bad-dimensions'
assert decide([1,1,2.3001],[])=='reject-historical-frozen-depth-envelope'
v18=H/'t05-fresh-v18-stage/T05_V18_EXACT_LIT_GLB_BATCH_UNAPPROVED.glb'
assert sha(v18)==sha(A)
print(json.dumps({'scope':'Offline fixture-only source check; no model import, station placement, authorizations, material approval or gameplay verified',
 'cooker_exact_sha256':sha(A),'fixture_knows_art_archive_alias_sha256':sha(v18),
 'legacy_base_revision':'5abfc29f1c3c51bef99247641cf1131581899942','source_triangles':model_tri,'glb_counts':counts,
 'current_level1_exact_checked_source':{str(f):sha(S/f) for f in [Path('opening.gd'),Path('layout.json'),Path('assets/characters/Character1.glb'),Path('assets/studio/hearth_trial_02.glb'),Path('resources/cooker_station_interface.gd')]},
 'placement':'No current qualified T05 station anchor, route clearance or sockets supplied. Current center hearth remains protected. Legacy site result cannot be transferred.',
 'current_hearth_authored_height_target_m':1.8,'historical_cooker_height_to_current_hearth_target':v[1]/1.8,'scale_comparisons':tests,'no_authority_controls':6},indent=2))
