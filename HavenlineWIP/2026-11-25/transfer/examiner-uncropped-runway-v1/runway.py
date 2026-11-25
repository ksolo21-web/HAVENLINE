from pathlib import Path
import json,hashlib,subprocess
root=Path(__file__).resolve().parent.parent
pins={
'hvn-l1-near-flight-live-body-observer-v1':'7688c8843dc45af01e8212304615e6652841dbbdd49c8b77cc32aba064334f08',
'hvn-l1-examiner-two-piece-transfer-native-result-v1':'7cfe83f2cdb2c306c7884c1cac2cfaab83e098e4f2f07448bb0232d9b408d051',
'hvn-l1-second-turn-guard-substitution-v1':'f868760e4aa23fa4c7960e30a7ceea98cc96b2f3f6bb5e0ed21a44ac4f258eec'
}
for k,h in pins.items():
 d=root/k
 assert hashlib.sha256((d/'SHA256SUMS').read_bytes()).hexdigest()==h
 subprocess.run(['sha256sum','-c','--status','SHA256SUMS'],cwd=d,check=True)
obs=(root/'hvn-l1-near-flight-live-body-observer-v1/native.txt').read_text().splitlines()
s,=[l.split(' ',1)[1] for l in obs if l.startswith('EXAM_SUPPORT_INPUT ')]
d=json.loads(s)
r=json.loads((root/'hvn-l1-examiner-two-piece-transfer-native-result-v1/result.json').read_text())
sha=hashlib.sha256(s.encode()).hexdigest()
assert r['first_middle']['unchanged_input_sha256']==r['second_middle']['unchanged_input_sha256']==sha
L=d['plan']
assert [p['age_ticks'] for p in L]==[[0,20,110,130],[0,20,110,130]]
off=L[0]['age_ticks'][-1]+6
assert r['qualified']['nominal_ticks']==off+L[1]['age_ticks'][-1]==266
print(json.dumps({
 'matched_input_sha256':sha,'pins':pins,'take_shape':'source-only normal-camera reconstruction, runtime pixels not captured',
 'observed_launch_tick':d['tick'],'stock_camera_launch_transform_origin_xyz_then_basis_cols':d['camera'],
 'stock_viewport_l1':[1280,720],'camera_projection':d['camera_projection'],'camera_size':d['camera_size'],
 'body_mount_launch_transform_origin_xyz_then_basis_cols':d['mount'],'actor_bound_launch_padded_min_max_m':d['body_padded_m'],
 'body_pose_custody':'Whole padded actor bound and held transforms only; complete original continuous body pose or per-frame camera matrices not archived.',
 'plan_matrix_encoding':'source/rest = [world origin XYZ, local basis X as world XYZ, Y, Z]; key = exact world position at each age',
 'plan':L,'delays_ticks':[0,off],'fixed_nominal_sample_rate_hz':60,'last_qualified_nominal_tick':266,
 'easing':'See exact native source Examiner._sample/frame_at_next_fixture_tick; source proper basis then shortest orientation SLERP plus linear source residue, retained end orientation, cubic smoothstep segment by age ticks. No introduced choreographed camera.',
 'screen_geometry_original':r['qualified']['park_view'],'existing_observed_clear_moving_count':r['qualified']['moving_vis_geom_samples']
},indent=2))
