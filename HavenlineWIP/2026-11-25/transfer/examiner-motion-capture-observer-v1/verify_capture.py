"""Runtime verifier. Full captures stay in disposable private profile."""
import json,math,hashlib,sys,re
from pathlib import Path
p=Path(__file__).resolve().parent
baseline=p.parent/'hvn-l1-examiner-two-piece-transfer-native-result-v1'
runway=p.parent/'hvn-l1-examiner-uncropped-runway-v1'
R=json.loads((runway/'runway.json').read_text())
full=Path(sys.argv[1]).read_text()
rows=full.splitlines()
def pfx(label):
 return [x.split(' ',1)[1] for x in rows if x.startswith(label+' ')]
assert not any(r.startswith(('ERROR','WARNING','SCRIPT ERROR','FATAL','EXAM_HOLD','FAIL ')) for r in rows)
obs=[x for x in rows if x.startswith('PFX_OBS ')]
assert len(obs)==57 and obs==[x for x in (baseline/'native.log').read_text().splitlines() if x.startswith('PFX_OBS ')]
native=json.loads(pfx('EXAM_QUALIFIED')[0]); expected=json.loads((baseline/'result.json').read_text())
assert native==expected['qualified'] and len(pfx('EXAM_QUALIFIED'))==1
S,=map(json.loads,pfx('CAP_PRIVATE_START'))
F=list(map(json.loads,pfx('CAP_PRIVATE_FRAME')))
assert len(F)==134 and S['tick']==1333 and S['owns_mounted'] and [r['age'] for r in F]==list(range(0,267,2))
assert [r['tick'] for r in F]==list(range(1333,1600,2))
assert len(S['bindings'])==66 and len(S['surface_roles'])>0 and S['native_floor_provenance']['is_native_visible']
assert [b['slot'] for b in S['bindings']]==list(range(66))
assert all(re.fullmatch('[A-Za-z0-9_]+',n['role']) for n in S['carry'])
def tf(T):
 return len(T)==4 and all(len(v)==3 and all(math.isfinite(x) for x in v) for v in T)
def near(A,B,tol=3e-6):
 assert tf(A) and tf(B)
 return max(abs(x-y) for a,b in zip(A,B) for x,y in zip(a,b))<tol
assert len(S['sparse_native_uv_weight_basis_checks'])==5*len(S['surface_roles'])
assert all(re.fullmatch('[0-9a-f]{64}',d['native_import_packed_godot_variant_sha256']) for d in S['surface_roles'])
assert all(tf(b['bind_inverse']) and tf(b['bone_rest_local']) for b in S['bindings'])
assert S['character']==F[0]['character'] and near(S['camera'],R['stock_camera_launch_transform_origin_xyz_then_basis_cols'])
assert F[0]['camera']==S['camera'] and F[-1]['camera']!=F[0]['camera']
assert any(q['character']['poses_by_skin_binding_slot']!=S['character']['poses_by_skin_binding_slot'] for q in F[1:])
for j,c in enumerate(S['carry']):
 assert c['slot']==j and c['visible'] and c['source_owner']
 assert near(c['matrix'],R['plan'][j]['source']) and near(c['matrix'],F[0]['subject'][j]['matrix'])
 assert near(F[-1]['subject'][j]['matrix'],R['plan'][j]['rest'])
who=[r['role'] for r in S['carry']]
for t,q in enumerate(F):
 age=t*2
 assert abs(q['nominal_time_s']-age/60)<1e-8 and q['projection']==1 and q['camera_size']==13 and tf(q['camera'])
 e=q['evaluated_sparse_native_markers']
 if age in (0,40,100,266):
  assert [(d['surface'],d['row']) for d in e]==[(d['surface'],d['row']) for d in S['sparse_native_uv_weight_basis_checks']]
  assert all(len(d['world'])==3 and all(math.isfinite(v) for v in d['world']) for d in e)
 else:
  assert e==[]
 J=q['character']
 assert len(J['poses_by_skin_binding_slot'])==66 and all(tf(x) for x in J['poses_by_skin_binding_slot'])
 assert tf(J['mesh_world']) and tf(J['skeleton_world']) and J['visibility']
 for j,rr in enumerate(q['subject']):
  d=R['delays_ticks'][j]
  bracket='queued_at_exact_launch' if age<=d else ('parked' if age>=d+130 else 'in_flight')
  assert rr['slot']==j and rr['role']==who[j] and rr['visible'] and rr['identity_continues'] and rr['one_fixture_owner']
  assert rr['state']==bracket and rr['flight_age']==max(0,min(130,age-d)) and tf(rr['matrix'])
for j,t in enumerate((65,133)):
 assert F[t]['subject'][j]['state']=='parked' and near(F[t]['subject'][j]['matrix'],R['plan'][j]['rest'])
assert F[68]['subject'][1]['state']=='queued_at_exact_launch' and F[69]['subject'][1]['state']=='in_flight'
print(json.dumps({'mode':'native data only, not rendered or published', 'observed_frames':len(F),'capture_hz_nominal':30,
 'last_native_age':F[-1]['age'],'two_original_ids_certified_and_raw_ids_not_exported':True,'per_frame_native_hero_bind_pose_slots':66,
 'validated_original_qualifier':True,'planned_graphics_scope':'exact normal-camera floor-stage reconstruction unless surrounding native camp models/shaders independently obtained; diagnostic art is not a native runtime placed marker', 'private_data_sha256':hashlib.sha256('\n'.join(pfx('CAP_PRIVATE_START')+pfx('CAP_PRIVATE_FRAME')).encode()).hexdigest()},indent=2))
