from source import *
from scipy.spatial.transform import Rotation
root=Path('../hvn-c1-right-offband-preflight-v1')
assert digest(root/'SHA256SUMS')=='6b3094a66507c47ded1ff2ce61fdf279cb3da9056e99c455dcdd5da5ecb54ed7'
for row in (root/'SHA256SUMS').read_text().splitlines():
 d,name=row.split(); assert digest(root/name)==d
scope=json.loads((root/'result.json').read_text())
uvp=Path('../hvn-c1-owner-right-palm-uv-v1')
m=np.load(uvp/'reauthored-review-LOCAL.npz',allow_pickle=False)
uvq=json.loads((uvp/'result.json').read_text())
for k,d in uvq['base_local_candidate_array_SHA256'].items():assert hashlib.sha256(np.ascontiguousarray(m[k]).tobytes()).hexdigest()==d
def seam(f):
 e=np.sort(np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]),axis=1)
 x,c=np.unique(e,axis=0,return_counts=True); return np.unique(x[c==1])
se=seam(F[m['removed']]); assert len(se)==57
r=np.asarray(J['sides']['R']['wrist'])
right=['hand.R']+[str(k) for k in names if str(k).endswith('.R') and str(k).split('.')[0] in ('index','middle','ring','pinky','thumb')]
idx=np.flatnonzero(np.isin(names,right)); fx=np.setdiff1d(np.arange(len(names)),idx)
fully=se[(abs(W[se][:,fx]).sum(1)<1e-10)&(abs(W[se][:,idx].sum(1)-W[se].sum(1))<1e-6)]
# All descendants and the wrist itself get one common rigid motion under a wrist-only delta.
rad=V[fully]-r; singular=np.linalg.svd(rad,compute_uv=False)
def cross_matrix(x):
 a,b,c=x;return np.array([[0,-c,b],[c,0,-a],[-b,a,0]])
jr=np.concatenate([-cross_matrix(v) for v in rad],axis=0)
js=np.linalg.svd(jr,compute_uv=False)
# Independent fixture control: any test delta around one lock ray preserves that ray,
# but the distinct seam rays measure residual (diagnostic, not authored pose).
axis=rad[np.argmax(np.linalg.norm(rad,axis=1))]
one=Rotation.from_rotvec(axis/np.linalg.norm(axis)*.01)
d=np.linalg.norm(one.apply(rad)-rad,axis=1)
# If both existing finite witness stations AND one normal are pointwise frozen,
# handle rigid transform has no remaining freedom. Bands alone impose inequalities,
# not these same pose-dependent equalities.
p,q=[np.asarray(J['sides'][s]['bary'])@tool[J['sides'][s]['surface_face_index']] for s in ('L','R')]
tri=tool[J['sides']['L']['surface_face_index']]
n=np.cross(tri[1]-tri[0],tri[2]-tri[0]); n/=np.linalg.norm(n)
lever=q-p; Jh=np.vstack((np.c_[np.eye(3),np.zeros((3,3))],np.c_[np.eye(3),-cross_matrix(lever)],np.c_[np.zeros((3,3)),-cross_matrix(n)]))
sv=np.linalg.svd(Jh,compute_uv=False)
# Reading LBS influence, not allowing edits or assuming a valid finger pose.
ids=np.unique(F[np.unique(np.array(scope['indices'][0]['raw_pairs'])[:,0])]); handidx=int(np.flatnonzero(names=='hand.R')[0]); digits=idx[idx!=handidx]
newids=np.flatnonzero(m['weights'][:,digits].sum(1)>1e-8)
def winding(x):
 a,b,c=(tool-x).transpose(1,0,2)
 A,B,C=(np.linalg.norm(k,axis=1) for k in (a,b,c))
 den=A*B*C+(a*b).sum(1)*C+(a*c).sum(1)*B+(b*c).sum(1)*A
 return float(np.arctan2((np.cross(a,b)*c).sum(1),den).sum()/(2*np.pi))
nod=ids[W[ids][:,digits].sum(1)<=1e-8]
fixed_buried=[int(i) for i in nod if abs(winding(V[i]))>.5]
report={'fixed_buried_without_digit_influence':fixed_buried,'seam_rows' :len(se),'rigid_wrist_descendant_only_rows':len(fully),'held_relative_pin_vectors_singular_m':singular.tolist(),'wrist_fixed_pin_jacobian_singular_m':js.tolist(),'control_axis_pin_error_mm':float(d[np.argmax(np.linalg.norm(rad,axis=1))]*1000),'control_other_seam_error_mm':float(d.max()*1000),'pointwise_bilateral_handle_rank':int(np.linalg.matrix_rank(Jh)),'pointwise_handle_jacobian_singular':sv.tolist(),'station_separation_mm':float(np.linalg.norm(lever)*1000),'normal_station_angle_deg':float(np.degrees(np.arccos(abs(n@lever)/np.linalg.norm(lever)))),'distal_collision_face_vertices':len(ids),'distal_with_digit_influence':int(np.count_nonzero(W[ids][:,digits].sum(1)>1e-8)),'distal_without_digit_influence':int(np.count_nonzero(W[ids][:,digits].sum(1)<=1e-8)),'locked_seam_rows_with_digit_influence':int(np.count_nonzero(W[se][:,digits].sum(1)>1e-8)),'authored_new_palm_rows_with_digit_influence':len(newids),'influence_is_not_a_pose_witness':True}
assert np.linalg.matrix_rank(jr)==3 and np.linalg.matrix_rank(Jh)==6
print(json.dumps(report,indent=2,sort_keys=True))
