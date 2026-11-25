from pathlib import Path
import json,hashlib,subprocess
R=Path(__file__).resolve().parent.parent
for n,h in [('candidate','bfcfadd07231f2ba40c2f206a30347c41b613e23b845fec807a161305bce6f6c'),('first-result','100ff1cb0f912f7a15e36c63084c38c85ab757aca486593d1bfa07eab17e2369')]:
 p=R/f'hvn-l1-actual-near-flight-{n}-v1'
 assert hashlib.sha256((p/'SHA256SUMS').read_bytes()).hexdigest()==h
 subprocess.run(['sha256sum','-c','--status','SHA256SUMS'],cwd=p,check=True)
f=(p/'native.log').read_text().splitlines()
def rows(n):return [x[len(n)+1:] for x in f if x.startswith(n+' ')]
near,=map(json.loads,rows('PFX_NEAR')); stage,=map(json.loads,rows('EXAM_ADMISSION_PREFIX'))
ix,k,arr=rows('EXAM_FLIGHT_GEOM_HOLD')[0].split(' ',2); signed=json.loads(arr)
assert (int(ix),int(k))==(0,1) and signed[1]<0 and all(x>0 for x in [signed[0],*signed[2:]])
assert stage['prefix']==57 and stage['request_dispatched'] is False and near['t']==1333
assert not {'body_aabb','actor_basis','mount','source_transforms','path_keys','padded_actor_sides'}&near.keys()
assert all(len(x.split())==2 for x in rows('PFX_OBS')) # only tick and digest, no pose reconstruction
g=(R/'hvn-l1-actual-near-flight-candidate-v1/guard.gdfrag').read_text()
assert 'BODY_PAD := Vector3(.025,.025,.025)' in g and 'NEEDLE := .00008' in g
assert 'gap_box(fitted[k],expected_body)' in g and 'expected_body=grown_box(live_box[0],BODY_PAD)' in g
print(json.dumps({'status':'HOLD: original live support inputs absent','signed_old_max_axis_gap_mm':1000*signed[1],
'minimum_improvement_at_the_unlogged_old_best_face_mm':1000*(.00008-signed[1]),'phase_b_near_no_dispatch':True,
'own_exact_crown_source_available_but_unlogged_live_mount_and_body_box':True,'pose_hash_not_invertible_witness':True},indent=2))
