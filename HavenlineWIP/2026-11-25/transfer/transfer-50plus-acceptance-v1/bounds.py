"""Non-native 2->52 staging scope; no scheduler/candidate or runtime threshold."""
from pathlib import Path
import hashlib,json,runpy,subprocess,sys
import numpy as np
p=Path(__file__).resolve().parent
root=p.parent
pins={
'hvn-l1-examiner-two-piece-transfer-native-result-v1':'7cfe83f2cdb2c306c7884c1cac2cfaab83e098e4f2f07448bb0232d9b408d051',
'hvn-l1-examiner-two-piece-independent-v1.GVNF27':'492b7dfb638ed663f41cbe03f47d8a46c3941e01bd3458f794a1bd81f9e09656',
'hvn-l1-transfer-volume-fixture-v1':'1217b23b7f17a386f1f7a0b81b3772b8d5c025ee2974defb017b668637e0fb34',
'hvn-l1-transfer-authority-fixture-v2':'c901b967dc8774ac585eadf785a4ec2c2208f403529933b3c4c0e78e5846775b',
'hvn-l1-near-flight-live-body-observer-v1':'7688c8843dc45af01e8212304615e6652841dbbdd49c8b77cc32aba064334f08',
'hvn-l1-near-flight-second-turn-support-v1':'650d0168542c1c419589e93a07d592ee1757212360c35072be13aa572bf11ac4',
}
for name,h in pins.items():
 q=root/name
 assert hashlib.sha256((q/'SHA256SUMS').read_bytes()).hexdigest()==h
 subprocess.run(['sha256sum','-c','--status','SHA256SUMS'],cwd=q,check=True)
def read(name,file,tag):
 rows=[l.split(' ',1)[1] for l in (root/name/file).read_text().splitlines() if l.startswith(tag+' ')]
 assert len(rows)==1
 return json.loads(rows[0])
held=read('hvn-l1-near-flight-live-body-observer-v1','native.txt','EXAM_SUPPORT_INPUT')
done=read('hvn-l1-examiner-two-piece-transfer-native-result-v1','native.log','EXAM_QUALIFIED')
assert done['nominal_ticks']==266 and done['same_two_view_objects'] and done['no_native_book_delta']
assert len(held['plan'])==2 and all(q['age_ticks']==[0,20,110,130] for q in held['plan'])
asset=Path(sys.argv[1])
tri,_=runpy.run_path(str(root/'hvn-l1-transfer-crown-spacing-v1/audit.py'))['decode'](asset)
pts=np.unique(tri.reshape(-1,3),axis=0)
a,b=held['plan']
# One diagnostic comparison only: second starts at 110, no placement or candidate edits.
# Middle turn already ended for first, not yet started for second. Fixed core
# orientations are native dst0/src1. Rest0 descent and source1 outward both
# last 20 ticks, same monotone smoothstep e, so relative center is affine in e.
R0=np.array(a['rest'][1:]).T; R1=np.array(b['source'][1:]).T
af=np.array(a['key'][2:4]); bf=np.array(b['key'][0:2])
def clearance(af,bf,R0,R1,axes):
 ac,bc=pts@R0.T@axes.T,pts@R1.T@axes.T
 relative=(af-bf)@axes.T
 near=(bc.min(0)-ac.max(0)-relative)
 far=(ac.min(0)-bc.max(0)+relative)
 return np.stack((near,far),axis=-1)
world=clearance(af,bf,R0,R1,np.eye(3))
M=np.array(held['mount'][1:]).T
# Unit normals, also correct for measured tiny mount non-orthonormal residue.
Q=np.linalg.inv(M); Q=Q/np.linalg.norm(Q,axis=1)[:,None]
local=clearance(af,bf,R0,R1,Q)
def report(g):return {'endpoint_signed_axis_m':g.reshape(2,6).tolist(),'fixed_face_uncushioned_lower_bound_m':g.min(axis=0).ravel().tolist(),'best_fixed_face_with_44um_reserve_m':float(g.min(axis=0).max()-.000044)}
print(json.dumps({
'existing':{'fixed_step_hz':60,'serial_dwell_ticks':6,'first_piece_ticks':130,'second_piece_ticks':130,'serial_total_ticks':266,
'native_shadow_transferred':done['shadow_stored_wood'],'not_live_gameplay':True},
'one_staged_overlap_hypothesis':{'second_start_tick':110,'concurrent_ticks':20,'nominal_combined_ticks_if_admitted':240,
'fixed_source_path_and_anchors_only':True,'required_existing_needle_m':.00008,
'world_frame':report(world),'mount_frame_normalized':report(local),
'axis_order':['negative_x','positive_x','negative_y','positive_y','negative_z','positive_z'],
'frames':'first key2->3 fixed rest orientation; second key0->1 fixed source orientation; same smoothstep, no changing route/back-row/threshold',
'limits':'fixed-face sufficient pair bound only on interval; no safety/admission, source or camera integration; no stage duration target'},
},indent=2,sort_keys=True))
