"""Exact-source local DQS differential: separate torso pins from sleeve movement."""
from pathlib import Path
import hashlib
def sealed(path, sh):
 assert hashlib.sha256((path/'SHA256SUMS').read_bytes()).hexdigest()==sh
 for row in (path/'SHA256SUMS').read_text().splitlines():
  a,b=row.split();assert hashlib.sha256((path/b).read_bytes()).hexdigest()==a
author=Path('../hvn-c1-coupled-shoulder-open-v1.Ik28DQ')
asig='0c711d29f9589f4625097e580ed60d8356503c27e4df3431d9e6838b17360c1e'
sealed(author,asig)
ind_packet=Path('../hvn-c1-coupled-shoulder-independent-v1.V6hQUK')
isig='be483b3856160a37232032c60260e9c62d21f1b52d019d9c755501cd8979d2d5'
sealed(ind_packet,isig)
text=(author/'audit.py').read_text()
prefix=text[:text.index('# Full posed character')]
# Capture exact affine transforms freshly reconstructed by the frozen source
# author, local to this process only. No new pose authoring/geometry output.
prefix=prefix.replace('def evaluated_side(side):','frame_maps={}\ndef evaluated_side(side):')
marker="after=dqsk(new)"
assert prefix.count(marker)==1
prefix=prefix.replace(marker,"frame_maps[side]=(transform,new)\n "+marker)
exec(compile(prefix,str(author/'audit.py'),'exec'))
a_res=json.loads((author/'result.json').read_text())
i_res=json.loads((ind_packet/'result.json').read_text())
def digest_array(a):
 return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()
assert digest_array(source_positions)==a_res['original_52j_candidate_positions_sha256']
assert digest_array(right_positions)==a_res['right_patch_candidate_positions_sha256']
assert len(frozen_body_tri)==600396 and int((body_delta>0).sum())==2291
def moving_kind(side,which):
 return rids[side] if which<3 else rids[side][1:]
def qskin(ids,aff):
 Wm=Rsource[ids].astype(float)
 idx=np.flatnonzero(np.any(Wm>0,axis=0))
 assert all(int(k) in aff for k in idx)
 if not len(ids):return np.empty((0,3))
 a,b=map(np.asarray,zip(*(real_dual(*aff[int(k)]) for k in idx)))
 w0=Wm[:,idx]; first=np.argmax(w0>0,axis=1)
 sig=np.sign(a[first]@a.T); assert sig.all()
 w=w0*sig
 qa=w@a;qb=w@b;norm=np.linalg.norm(qa,axis=1)[:,None]
 qa/=norm; qb/=norm
 qc=qa.copy();qc[:,:3]*=-1
 return Rotation.from_quat(qa).apply(P[ids])+2*mul(qb,qc)[:,:3]
def signed_axes(shoulder,e,wrist):
 u=unit(e-shoulder)
 f=unit(wrist-e)
 n=unit(np.cross(u,f))
 v=unit(np.cross(n,u))
 m=np.column_stack((u,v,n))
 assert np.linalg.det(m)>.99999999 and np.max(abs(m.T@m-np.eye(3)))<1e-12
 return (*m.T,n)
def derive(side,kind,rows):
 assert kind in ('exact_held_baseline','whole_arm_open_hypothetical')
 old,new=frame_maps[side]
 Pj=J['sides'][side]
 shoulder=np.array(Pj['shoulder'])
 elbow=np.array(Pj['elbow'])
 wrist=np.array(Pj['wrist'])
 aff=old
 if kind=='whole_arm_open_hypothetical':
  aff=new
  wrist=np.array(Qp[side][0]['open_wrist_m'])
  elbow=np.array(Qp[side][0]['exact_elbow_target_m'])
 p0=qskin(rows,aff)
 actual=V if kind=='exact_held_baseline' else source_positions
 origin_fit=float(np.linalg.norm(p0-actual[rows],axis=1).max())
 assert origin_fit<8e-7,(origin_fit,side,kind)
 axes=signed_axes(shoulder,elbow,wrist)
 def rot_aff(k,eps):
  X=Rotation.from_rotvec(axes[k]*eps).as_matrix()
  pivot=shoulder if k<3 else elbow
  r=aff.copy()
  for j in moving_kind(side,k):
   if j not in r:continue
   m,v=aff[j]
   r[j]=(X@m,X@(v-pivot)+pivot)
  return r
 def FD(eps):
  columns=[]
  for k in range(4):
   P1=qskin(rows,rot_aff(k,eps)); P2=qskin(rows,rot_aff(k,-eps))
   columns.append(((P1-P2)/(2*eps)).ravel())
  return np.column_stack(columns)
 # These are derivatives on conjugate actual joint transforms, not authored
 # posture angle-offset trials. Hold all other transforms, bind and weight rows.
 steps=[2e-5,1e-5,5e-6]
 jac=[FD(q) for q in steps]
 near=max(float(np.max(abs(jac[1]-j))) for j in jac[::2])
 assert near<1e-7,(near,kind,side)
 M=jac[1]
 # Half physical robust witness disjoint from the other half, stable source-ID
 # split; don't claim all pins necessary to witness rank.
 seq=np.arange(len(rows))
 def sv(A):return np.linalg.svd(A,compute_uv=False)
 block= M.reshape(len(rows),3,4)
 parts=[sv(block[g].reshape(-1,4)) for g in (seq%2==0,seq%2==1)]
 val=sv(M)
 assert len(val)==4 and val[2]>1e-3 and val[3]<1e-9
 assert all(p[2]>1e-3 and p[3]<1e-9 for p in parts)
 elbow_mat=np.array(moving_kind(side,3))
 assert np.all(Rsource[rows][:,elbow_mat]==0),(side,kind)
 assert np.count_nonzero(M[:,3])==0
 result={'pose':kind,'rows':len(rows),'joint_angular_coordinate_order':['shoulder_about_upper_longitudinal','shoulder_about_orthogonal_in_bend_plane','shoulder_about_bend_plane_normal','elbow_about_bend_plane_normal'],
    'axis_vectors_actual_source_world':[a.tolist() for a in axes],
    'SVD_raw_m_per_rad':val.tolist(),'SVD_RMS_per_vertex_m_per_rad':(val/np.sqrt(len(rows))).tolist(),
    'parity_half_witness_SVD_raw_m_per_rad':[p.tolist() for p in parts],
    'condition_singular_quotient_nonzero':float(val[0]/val[2]),
    'rank_absolute_1e_minus_6_m_per_rad':int((val>1e-6).sum()),
    'pivot_shoulder_m':shoulder.tolist(),'pivot_elbow_m':elbow.tolist(),'steps_radians':steps,
    'max_entry_cross_step_diff_m_per_rad':near,'no_op_reconstruction_max_m':origin_fit,
    'elbow_column_numerically_zero':True,'elbow_descendant_weight_rows_in_chart':0,
    'positive_shoulder_rows_frozen_bind_AABB_m':[P[rows].min(0).tolist(),P[rows].max(0).tolist()],
    'positive_shoulder_rows_frozen_current_AABB_m':[actual[rows].min(0).tolist(),actual[rows].max(0).tolist()],
    'smallest_source_id_examples':rows[:10].tolist()}
 return result
def support_for_pair():
 # Prove both triangles have zero relevant elbow dependence from their
 # actual indices/weights; no penetration-distance approximation.
 pair=(556546,674738)
 tri=F[list(pair)]
 influence=[]
 for i,m in zip(pair,tri):
  ww=Rsource[m]; v=np.flatnonzero(ww.max(0)>0)
  influence.append(dict(face=i,vertex_ids=m.tolist(),weights_by_joint={str(names[j]):ww[:,j].tolist() for j in v}))
 assert not np.any(Rsource[tri][:,:,moving_kind('L',3)])
 assert not np.any(Rsource[tri][:,:,moving_kind('R',0)])
 assert np.all(Rsource[tri[0]][:,moving_kind('L',0)]==0)
 assert np.all(Rsource[tri[1],ix['upper_arm.L']]==1)
 assert crosses(source_positions[tri[0]],source_positions[tri[1]]) or crosses(source_positions[tri[1]],source_positions[tri[0]])
 wc=[r for r in i_res['independent_named_pair_controls'] if tuple(r['source_faces'])==pair]
 assert len(wc)==1 and wc[0]['baseline_strict_overlap_mm']==0 and wc[0]['whole_arm_strict_overlap_mm']>0
 WJ=J['sides']['L']; shoulder=np.array(WJ['shoulder'])
 elbows=np.array(Qp['L'][0]['exact_elbow_target_m']); wrists=np.array(Qp['L'][0]['open_wrist_m'])
 axes=np.array(signed_axes(shoulder,elbows,wrists)[:3])
 # All three sleeve rows are pure upper-arm. Direct derivative for those
 # points about actual shoulder is the purely rigid cross-product term,
 # independent of recovered mixing transforms or central quotient.
 positive=np.cross(axes[:,None],source_positions[tri[1]][None]-shoulder)
 assert np.linalg.norm(positive,axis=2).max()>.09
 # Report exact baseline with the same finite test, not a derived angle hint.
 assert not(crosses(V[tri[0]],V[tri[1]]) or crosses(V[tri[1]],V[tri[0]]))
 return {'named_pair_exact':list(pair),'attached_joints_by_indexed_triangle':influence,
    'strict_overlap_in_open':True,'strict_overlap_in_prior_held':False,
    'independent_held_to_open_finite_segment_mm':wc[0]['whole_arm_strict_overlap_mm'],
    'analytic_nonzero_sleeve_sensitivity_mm_per_rad_if_left_shoulder_were_free':float(np.linalg.norm(positive,axis=2).max()*1000),
    'same_weights_means_all_allowed_elbow_directions_leave_both_exact_triangles_unchanged':True}
p_pair=support_for_pair()
result={'status':'HOLD_LOCAL_NO_PIN_CONFORMING_PAIR_SEPARATION',
  'author_manifest':asig,'independent_manifest':isig,
  'exact_original_chest_author_guard_faces':len(frozen_body_tri),
  'authorized_chart_not_appearance_mask':True,
  'exact_original_center_core_unchanged':len(frozen_core),
  'named_sleeve_pair':p_pair,'fits':{side:[derive(side,k,mix0[side]) for k in ('exact_held_baseline','whole_arm_open_hypothetical')] for side in ('L','R')},
  'scope':'regular local tangent in source shoulder ball plus anatomical elbow hinge; upper torso/clavicle, geometry, weights, true link lengths, original tool/bands and identity fixed; no global reach or all-pose statement'}
print(json.dumps(result,indent=2,sort_keys=True))
