"""Exact source paired whole-arm shoulder, preserving elbow shape."""
from pathlib import Path
import hashlib
p=Path('../hvn-c1-right-digit-anatomical-specimen-v1')
seal='42d7b3416fcdbf427cbd14ab2640e7c31d438cd7b34ad95f9332299a04b4dc4e'
assert hashlib.sha256((p/'SHA256SUMS').read_bytes()).hexdigest()==seal
for ln in (p/'SHA256SUMS').read_text().splitlines():
 h,n=ln.split();assert hashlib.sha256((p/n).read_bytes()).hexdigest()==h
last=Path('../hvn-c1-coordinated-open-v1.jbZ4Tz')
sha2='0b6e88b44adb4b6539ca87f087f997586bbe64f3e7b132a1143536772d30f6ab'
assert hashlib.sha256((last/'SHA256SUMS').read_bytes()).hexdigest()==sha2
for ln in (last/'SHA256SUMS').read_text().splitlines():
 sh,n=ln.split();assert hashlib.sha256((last/n).read_bytes()).hexdigest()==sh
planned=__import__('json').loads((last/'result.json').read_text())
prior=(p/'audit.py').read_text()
prefix=prior[:prior.index("# Deliberately minimal fixed sample, no fitting")]
exec(compile(prefix,str(p/'audit.py'),'exec'))
# Pressure UV array immutability: this is a pose author proposal, not an alternate
# bind or intermediate re-tessellation. Existing pressure topology and row weights
# stay exact. Compute the mounted patch's actual affine motion where every
# influential group shares the same rigid forearm/hand displacement.
rids={s0:[ix[n] for n in (f'upper_arm.{s0}',f'forearm.{s0}',f'hand.{s0}',*(f'{d}.{j:02}.{s0}' for d in digs for j in (1,2,3)))] for s0 in ('R','L')}
Rsource=R
movable={s0:np.flatnonzero(np.any(Rsource[:,rids[s0]]>0,axis=1)) for s0 in ('R','L')}
assert not np.intersect1d(movable['R'],movable['L']).size
assert all(P[movable[s0],2].min()>.15 for s0 in ('R','L'))
local_weights=local['weights']
assert np.max(abs(local_weights[:,rids['R']].sum(1)-local_weights.sum(1)))<1e-6
# Tool axial convex support segment; choose a static construction from the complete
# rotation arc inside prescribed analytic aperture below, not an angle sweep.
# Freeze original contact facets and left/right shaft stations pointwise.
shaft=M0=np.array(J['orientation'])
axis_shaft=M0[:,2]
tool_ax=tool@axis_shaft
margin=.003   # authoring-only guard against small approx/deformation error, not contact or animation policy
max_open_rad=np.deg2rad(27) # single construction bracket only; not allowed joint limit
def direction(s0,e,w,n,sh):
 # The previous anatomical open position defines direction, not an allowable
 # wrist radius. Project on the original shoulder/wrist sphere and keep bend.
 dest=np.array(planned['rig_two_hands'][s0]['open_wrist_m'])
 current=unit(w-sh);target=unit(dest-sh)
 k=unit(np.cross(current,target))
 assert np.cross(k,w-sh)@n>0
 return k
def rot_apply(A,e,q):return (q@(A-e).T).T+e
def stationary_linear(x,ang):
 if abs(x)<1e-12:return False
 return (np.rad2deg(x)%360)>1e-12
def arc_on_axis(A,e,k,a):
 rad=A-e
 dot=rad@k
 c=e[None]+dot[:,None]*k
 u=rad-dot[:,None]*k
 v=np.cross(k,u)
 ac=u@a; bs=v@a; dc=c@a
 end=ac*np.cos(max_open_rad)+bs*np.sin(max_open_rad)
 lo=np.minimum(ac,end); hi=np.maximum(ac,end)
 tp=np.arctan2(bs,ac)%(2*np.pi)
 tm=(tp+np.pi)%(2*np.pi)
 mag=np.hypot(ac,bs)
 lo=np.where(tm<=max_open_rad,-mag,lo);hi=np.where(tp<=max_open_rad,mag,hi)
 return float(np.min(lo+dc)),float(np.max(hi+dc))
from scipy.optimize import brentq
def candidate(s0):
 # Actual bulk distal under source original limb. All touched forearm faces are
 # later compared directly and may not rely on this rigid distal criterion.
 WJ=J['sides'][s0]
 shoulder,el,wr,n=map(lambda k:np.array(WJ[k],float),('shoulder','elbow','wrist','outward'))
 n=unit(n); k=direction(s0,el,wr,n,shoulder)
 ids=movable[s0]
 pure=ids[np.abs(Rsource[ids][:,rids[s0]].sum(1)-1)<2e-7]
 cutoff=(P[pure,0]*(-1 if s0=='R' else 1))>.713
 pure=pure[cutoff]
 a=V[pure]
 if s0=='R':a=np.vstack((a,local['vertices']))
 arc_span=arc_on_axis(a,shoulder,k,axis_shaft)
 mask=(tool_ax.max(1)>=arc_span[0])&(tool_ax.min(1)<=arc_span[1])
 # Conservative full vertices of every actual facet that touches the whole swept
 # shaft-axis interval, not an ideal cylinder. Need only one finite endpoint.
 assert mask.sum()>1
 support=float(np.max(tool[mask]@n))
 p0=a@n-support-margin
 u0=a-shoulder; uc=u0-(u0@k)[:,None]*k
 a1=float(shoulder@n)+(u0@k)*(k@n)
 cos=uc@n; sin=np.cross(k,uc)@n
 def residual(th):return float(np.min(a1+cos*np.cos(th)+sin*np.sin(th)-support-margin))
 zero=residual(0.); cap=residual(max_open_rad)
 out={'wrist_elbow_length_m':float(np.linalg.norm(wr-el)),
      'upper_length_m':float(np.linalg.norm(el-shoulder)),
      'construction_at_0_m':zero,'construction_at_cap_m':cap,
      'own_finite_facet':WJ['surface_face_index'],'actual_swept_distal_axial_range_m':arc_span,
      'tested_retained_support_facets_n':int(mask.sum()),'source_distal_pure_rows_n':len(pure),
      'open_axis':k.tolist(),'where_construction_bracket_ends_deg':float(np.rad2deg(max_open_rad)),
      'whole_arm_axis_nonorthogonality_to_original_elbow_subvectors':float(max(abs(k@unit(el-shoulder)),abs(k@unit(wr-el)))), 
      'bracket_not_game_joint_limit':True}
 if zero>=0 or cap<0:
  return out,None
 # Numerically locate only the root of this physical support equation.
 # All calculations at intermediate values are analytic inequalities, not
 # sampled skinned collision offset search. There is no angular score loop.
 selected=brentq(residual,0,max_open_rad,xtol=1e-13)
 selected+=np.deg2rad(.25) # precision guard near endpoint, not joint limit
 assert selected<=max_open_rad and residual(selected)>0
 rot=Rotation.from_rotvec(k*selected).as_matrix()
 station=np.array(WJ['bary'])@tool[WJ['surface_face_index']]
 orig=V[int(WJ['palm_vertex'])]
 aft=rot_apply(orig[None],shoulder,rot)[0]
 rel=aft-station
 nw=rot_apply(wr[None],shoulder,rot)[0]
 ne=rot_apply(el[None],shoulder,rot)[0]
 d0=np.linalg.norm(wr-shoulder); d1=np.linalg.norm(nw-shoulder)
 su=np.linalg.norm(el-shoulder); fo=np.linalg.norm(wr-el)
 assert abs(su-fo)<d1<su+fo
 along=(su*su+d1*d1-fo*fo)/(2*d1)
 pointer=unit(nw-shoulder)
 # Solve genuine two-link sphere intersection in the preserved bend frame,
 # retaining the original elbow-circle azimuth after the whole-arm rotation.
 old=el-shoulder; pure_pole=unit(old-(old@unit(wr-shoulder))*unit(wr-shoulder))
 pole=rot@pure_pole; assert abs(pole@pointer)<1e-10
 reconstructed=shoulder+pointer*along+pole*np.sqrt(su*su-along*along)
 assert np.linalg.norm(ne-reconstructed)<1e-10
 reach=np.linalg.norm(nw-shoulder)
 lengths=np.linalg.norm(wr-el)+np.linalg.norm(el-shoulder)
 out.update({'status':'AUTHORED_OPEN_PENDING_GLOBAL_CHECK','axis_angle_deg':float(np.rad2deg(selected)),
  'pure_distal_certified_support_m':residual(selected)+margin,'rotation':rot.tolist(),
  'translation':(shoulder-rot@shoulder).tolist(),'old_band_station_m':station.tolist(),
  'open_wrist_m':nw.tolist(),'shoulder_to_open_wrist_reserve_m':float(lengths-reach),
  'old_elbow_bend_deg':float(np.rad2deg(np.arccos(np.clip(unit(el-shoulder)@unit(wr-el),-1,1)))),
  'authored_elbow_bend_deg':float(np.rad2deg(np.arccos(np.clip(unit(ne-shoulder)@unit(nw-ne),-1,1)))),
  'maintained_elbow_to_wrist_length_error_m':float(abs(np.linalg.norm(nw-ne)-fo)),
  'maintained_shoulder_to_elbow_length_error_m':float(abs(np.linalg.norm(ne-shoulder)-su)),
  'two_link_sphere_circle_elbow_reconstruction_error_m':float(np.linalg.norm(ne-reconstructed)),
  'exact_elbow_target_m':ne.tolist(),
  'registered_palm_source_right_or_left_index':int(WJ['palm_vertex']),
  'actual_anchor_signed_open_gap_mm':float((rel@n)*1000),
  'actual_anchor_tangent_displacement_to_fixed_contact_station_mm':float(np.linalg.norm(rel-(n@rel)*n)*1000),
  'source_bind_group_matrix_parent_motion_model':'upper arm moves about source shoulder; elbow is exact 2-link sphere/circle solve in preserved bend frame; forearm, hand, digits share its world delta and preserve local quaternions'})
 return out,(rot,shoulder)
# Torso above uses EXACT original chest source author chart (non-arm/clav
# dominant, and corners inside abs X=.48) and independent centerline lock.
old_dominant=np.asarray(names)[W.argmax(1)]
author_arm=[f'{b}.{side}' for side in ('R','L') for b in ('upper_arm','forearm','hand','clavicle')]
exclude=np.isin(old_dominant,author_arm)|(abs(P[:,0])>.48)
frozen_body_tri=np.flatnonzero(~exclude[F].any(1))
frozen_body_rows=np.unique(F[frozen_body_tri])
mix0={side:np.intersect1d(frozen_body_rows,movable[side]) for side in ('R','L')}
frozen_core=np.flatnonzero(abs(P[:,0])<.175)
assert not any(np.intersect1d(frozen_core,movable[side]).size for side in ('R','L'))
# Actual source supports exact floats in input and later preliminary bounds.
Qp={s0:candidate(s0) for s0 in ('R','L')}
if any(m is None for _,m in Qp.values()):
 print(json.dumps({'status':'HOLD_SUPPORT_FEASIBILITY_NO_CANDIDATE','rig_two_hands':{k:r for k,(r,_) in Qp.items()},'immutable_torso_mixed_rows_geometric_preflight':{k:len(v) for k,v in mix0.items()}},indent=2,sort_keys=True));raise SystemExit(0)
def evaluated_side(side):
 ids=movable[side]; mtx,e=Qp[side][1]
 cols=np.flatnonzero(np.any(Rsource[ids]>0,axis=0))
 common=fit('hand.'+side)
 transform={}
 for j in cols:
  name=str(names[j])
  if name.split('.')[0] in digs :
   # Only shoulder/forearm/wrist are authored in pinned held input. Independent
   # registration on all listed pure or dominant bind/held rows confirms idle
   # digit inheritance, not authority to substitute unrelated motion.
   weights=Rsource[:,j]
   sample=np.flatnonzero((weights>=.30)&(Rsource.argmax(1)==j)&(Rsource[:,rids[side][2:]].sum(1)>.999999))
   assert len(sample)>18,(name,len(sample))
   aa=common
   assert np.linalg.norm(P[sample]@aa[0].T+aa[1]-V[sample],axis=1).max()<5e-7,(name, np.linalg.norm(P[sample]@aa[0].T+aa[1]-V[sample],axis=1).max())
  elif name in ('neck','clavicle.L','clavicle.R'):
   # Native source applies chest twist and only R clavicle about source Z.
   aa=fit('chest')
   if name=='clavicle.R':
    q=check(Path('hvn-t09-narrow-ready-witness.yFldwO/intent.json'),'74ade95390baae7c973b6de04667d5341f96ee00b468e803182342b0ef909b14')
    cfg=json.loads(q.read_text()); assert cfg['clavicle_right_z_deg']==8
    H=np.array([-.045,0.,.405]) # exact pinned original source right clavicle bind head
    Q=Rotation.from_euler('z',cfg['clavicle_right_z_deg'],degrees=True).as_matrix()
    aa=(aa[0]@Q,aa[1]+aa[0]@(H-Q@H))
  else:aa=fit(name)
  transform[int(j)]=aa[:2]
 def dqsk(t):
  qa,qd=map(np.asarray,zip(*(real_dual(*t[int(j)]) for j in cols)))
  w=Rsource[ids][:,cols].astype(float)
  ix0=np.argmax(w>0,axis=1)
  Sg=np.sign(qa[ix0]@qa.T); assert np.all(Sg)
  real=(w*Sg)@qa; dual=(w*Sg)@qd; length=np.linalg.norm(real,axis=1)[:,None]
  real/=length;dual/=length
  qc=real.copy();qc[:,:3]*=-1
  return Rotation.from_quat(real).apply(P[ids])+2*mul(dual,qc)[:,:3]
 before=dqsk(transform)
 e0=float(np.linalg.norm(before-V[ids],axis=1).max())
 assert e0<8e-7,(side,e0)
 # Publish explicit armature-space deltas and correct same-motion descendants.
 forearm_bind=fit('forearm.'+side)
 WJ=J['sides'][side]
 forearm_origin=np.array(WJ['elbow'])
 old_forearm_axis=np.array(WJ['wrist'])-forearm_origin
 old_forearm_axis/=np.linalg.norm(old_forearm_axis)
 idx0=np.flatnonzero(cols==ix['forearm.'+side]);assert len(idx0)==1
 new=transform.copy()
 for j in rids[side]:
  if j not in transform: continue
  a,b=transform[j];new[j]=(mtx@a,mtx@(b-e)+e)
 after=dqsk(new)
 actual=V[ids]+after-before
 # Hard frozen local cuffs: endpoints now live in new limb space, not pinned
 # to old world coordinates. All actual indexed cuff source edge rows inherit
 # one and the same rigid transform, tested separately from extrapolation.
 cu=np.unique(s[side+'_loop_source_vertex_edges'])
 spot=np.searchsorted(ids,cu)
 assert np.all(ids[spot]==cu)
 err=float(np.linalg.norm(actual[spot]-rot_apply(V[cu],e,mtx),axis=1).max())
 assert err<8e-7,(err,side)
 side_report={'affected_rows':len(ids),'cuff_pure_under_forearm':int((abs(Rsource[cu][:,rids[side]].sum(1)-1)<2e-7).sum()),
   'cuff_endpoint_rows':len(cu),'cuff_expected_rigid_relative_local_max_error_m':err,
   'actual_v2_dqs_unchanged_pose_readback_max_error_m':e0,'no_default_thumb_inner_modification':True,
   'min_source_abs_x_of_affected':float(abs(P[ids,0]).min()),
   'joints_shared_delta':list(map(lambda j:str(names[j]),rids[side]))}
 if side=='R':
  spot=np.searchsorted(ids,se)
  assert np.all(ids[spot]==se)
  slip=float(np.linalg.norm(actual[spot]-rot_apply(V[se],e,mtx),axis=1).max())
  side_report['right_existing_57_seam_rigid_max_error_m']=slip
  assert slip<8e-7
 return ids,actual,side_report
source_positions=V.copy()
checks={}
for h0 in ('R','L'):
 ii,new,q=evaluated_side(h0);source_positions[ii]=new;checks[h0]=q
changed=np.unique(np.r_[movable['R'],movable['L']])
unchanged=np.setdiff1d(np.arange(len(P)),changed)
assert np.array_equal(source_positions[unchanged],V[unchanged])
assert np.array_equal(source_positions[P[:,2]<-.2],V[P[:,2]<-.2])
assert np.array_equal(source_positions[frozen_core],V[frozen_core])
body_delta=np.linalg.norm(source_positions[frozen_body_rows]-V[frozen_body_rows],axis=1)
torso={'exact_pinned_chest_author_frozen_torso_faces':len(frozen_body_tri),'source_core_rows_inside_x_175mm':len(frozen_core),'exact_guard_hit_count':int(np.sum(body_delta>0.)),
       'max_original_nondominant_arm_torso_moved_mm':float(body_delta.max()*1000),
       'first_moved_row_ids':frozen_body_rows[body_delta>0.][:20].tolist(),
       'strict_torso_identity_required':True,'mixed_scope_varied_only_by_actual_skinning_not_weight_edit':True}

rightmat,rightel=Qp['R'][1]
right_positions=rot_apply(local['vertices'],rightel,rightmat)
# The sealed predecessor stores appended vertices only; patch triangles are GLOBAL
# indices into retained original rows and appended rows, not local mesh tri indices.
pface=local['faces']; pn=len(V); p_original=np.unique(pface[pface<pn])
assert np.isin(se,p_original).all()
p_error=float(np.linalg.norm(source_positions[se]-rot_apply(V[se],rightel,rightmat),axis=1).max())
assert p_error<8e-7
# Full posed character plus exact right patch compared to full tool; retain exact
# baseline names (no default excluded world groups). Both shaft and head tested.
def aabb_scan(tri_A,tri_B):
 lo,hi=tri_B.min(axis=(0,1)),tri_B.max(axis=(0,1))
 A0,A1=tri_A.min(1),tri_A.max(1)
 use=np.flatnonzero(((A0<=hi)&(A1>=lo)).all(1))
 QA,QB=tri_B.min(1),tri_B.max(1)
 hit=[]
 for i in range(0,len(use),256):
  us=use[i:i+256]
  near=np.argwhere(((A0[us,None]<=QB[None])&(A1[us,None]>=QA[None])).all(2))
  for k,j in near:
   idx=int(us[k]);j=int(j)
   if crosses(tri_A[idx],tri_B[j]) or crosses(tri_B[j],tri_A[idx]):hit.append((idx,j))
 return hit,len(use)
def tool_inside(points):
 lo,hi=tool.min(axis=(0,1)),tool.max(axis=(0,1))
 u=points[((points<=hi)&(points>=lo)).all(1)]
 tot=0
 for n in range(0,len(u),256):
  a,b,c=np.moveaxis(tool[None]-u[n:n+256,None,None],2,0)
  A,B,C=[np.linalg.norm(z,axis=2) for z in (a,b,c)]
  den=A*B*C+(a*b).sum(2)*C+(a*c).sum(2)*B+(b*c).sum(2)*A
  wind=np.arctan2((np.cross(a,b)*c).sum(2),den).sum(1)/(2*np.pi)
  tot+=int(np.sum(abs(wind)>.99))
 return tot,len(u)
keep_face=np.setdiff1d(np.arange(len(F)),local['removed'])
remain=F[keep_face]
source_ids_used=np.unique(remain)
old_c,old_cand=aabb_scan(V[remain],tool)
new_c,new_cand=aabb_scan(source_positions[remain],tool)
old_q,old_qcand=aabb_scan(np.vstack((V,local['vertices']))[pface],tool)
new_q,new_qcand=aabb_scan(np.vstack((source_positions,right_positions))[pface],tool)
assert len(old_c)==298 and len(old_q)==0,(len(old_c),len(old_q))
before_contain, baseline_near=tool_inside(np.vstack((V[source_ids_used],local['vertices'])))
after_contain, candidate_near=tool_inside(np.vstack((source_positions[source_ids_used],right_positions)))
# Retained-side and elbow transition checks: AABB/cKDTree broadphase and
# vectorized finite strict edge/triangle predicate, both original and open.
# Exclude only adjacent physical source faces and relative-rigid internal pairs
# (unchanged by the declared smooth skinning delta within measured tolerance).
from scipy.spatial import cKDTree
full_faces=np.vstack((remain,pface))
nm=len(V); add_n=len(local['vertices'])
old_full=np.vstack((V,local['vertices'])); new_full=np.vstack((source_positions,right_positions))
labels=np.zeros(nm+add_n,np.int16)
for typ, side in [(1,'R'),(2,'L')]:
 ii=movable[side]
 sums=Rsource[ii][:,rids[side]].sum(1)
 labels[ii]=np.where(abs(sums-1)<2e-7,typ,3)
labels[nm:]=1
fl=labels[full_faces]
face_type=np.where(np.all(fl==fl[:,:1],axis=1),fl[:,0],3)
face_type[face_type<0]=3
canon=np.r_[inv,np.arange(inv.max()+1,inv.max()+1+add_n)][full_faces]
from itertools import product
def narrow(first,second):
 x=first; y=np.roll(first,-1,axis=1)
 dv=y-x; e1=second[:,1]-second[:,0];e2=second[:,2]-second[:,0]
 h=np.cross(dv,e2[:,None]);det=(e1[:,None]*h).sum(2)
 good=abs(det)>1e-15
 w=np.where(good,det,1)
 n=x-second[:,0,None];q=np.cross(n,e1[:,None])
 u=(n*h).sum(2)/w;v=(dv*q).sum(2)/w;t=(e2[:,None]*q).sum(2)/w
 return (good&(u>1e-8)&(v>1e-8)&(1-u-v>1e-8)&(t>1e-8)&(1-t>1e-8)).any(1)
def body_pairs(positions):
 tr=positions[full_faces]; aa=tr.min(1);bb=tr.max(1); mid=(aa+bb)*.5;rad=np.linalg.norm(bb-mid,axis=1)
 own=np.flatnonzero(face_type!=0)
 lomax=aa[own].min(0);himax=bb[own].max(0)
 eligible=np.flatnonzero(((aa<=himax)&(bb>=lomax)).all(1))
 trees=[]
 bins=(0,.0015,.003,.006,.012,.024,.045,float('inf'))
 for mi,ma in zip(bins[:-1],bins[1:]):
  group=eligible[(rad[eligible]>=mi)&(rad[eligible]<ma)]
  if len(group): trees.append((group,cKDTree(mid[group]),rad[group].max()))
 hit=set(); nb=0
 for start in range(0,len(own),384):
  sel=own[start:start+384]
  for group,tree,r in trees:
   idx=tree.query_ball_point(mid[sel],rad[sel]+r+1e-10,workers=1)
   sz=np.array([len(b) for b in idx]);ii=np.repeat(sel,sz)
   if not ii.size:continue
   jj=group[np.concatenate(idx).astype(int)]
   typ_i=face_type[ii];typ_j=face_type[jj]
   valid=(ii!=jj)&((ii<jj)|(typ_j==0))&((typ_i!=typ_j)|(typ_i==3))
   valid&=((aa[ii]<=bb[jj]+1e-10)&(bb[ii]+1e-10>=aa[jj])).all(1)
   ii=ii[valid];jj=jj[valid]
   if not ii.size:continue
   valid=~(canon[ii,:,None]==canon[jj,None,:]).any((1,2))
   ii=ii[valid];jj=jj[valid]; nb+=len(ii)
   if not len(ii):continue
   ok=narrow(tr[ii],tr[jj])|narrow(tr[jj],tr[ii])
   hit.update(tuple(sorted((int(a),int(b)))) for a,b in zip(ii[ok],jj[ok]))
 return hit,nb
old_body,obn=body_pairs(old_full)
new_body,nbn=body_pairs(new_full)
new_only=sorted(new_body-old_body)
body={'relative_rigid_body_checks':'both source position sets; strict nonadjacent actor-vs-self only on changing relative pairs; no coplanar contact/seam strain/dynamic proof',
      'face_types':['unchanged','rigid R','rigid L','transition'],'faces_per_type':np.bincount(face_type,minlength=4).tolist(),
      'baseline_broadphase_tests':obn,'candidate_broadphase_tests':nbn,
      'original_strict_pairs_relative_faces':len(old_body),'candidate_strict_pairs_relative_faces':len(new_body),
      'new_strict_pairs':len(new_only),'cleared_strict_pairs':len(old_body-new_body),
      'first_20_new_face_indices_and_relative_types':[[i,j,int(face_type[i]),int(face_type[j])] for i,j in new_only[:20]]}
stat='HOLD_EXACT_STATIC_TOOL_OR_BODY_CLIP' if (new_c or new_q or after_contain or new_only or torso['exact_guard_hit_count']) else 'STATIC_TOOL_AND_BODY_NO_NEW_STRICT_HITS_NEEDS_INDEPENDENT_CONTACT_AND_MOTION'
# Emit pose reconstruction fingerprint, not an asset or animation.
report={'status':stat,'rig_two_hands':{k:r for k,(r,_) in Qp.items()},'source_apply':checks,'torso_guard':torso,'prior_source_anatomical_seal':sha2,'body_self_clearance':body,
        'right_authored_pressure_patch_source_geometry_indices_weights_unchanged':True,
        'right_authored_pressure_patch_relative_seam_max_error_m':p_error,
        'untouched_original_source_rows':len(unchanged),'strict_baseline_retained_tool_pairs':len(old_c),
        'strict_candidate_retained_tool_pairs':len(new_c),'strict_candidate_retained_source_face_tool_indices':[[int(keep_face[i]),j] for i,j in new_c],
        'strict_baseline_new_palm_tool_pairs':len(old_q),
        'strict_candidate_new_palm_tool_pairs':len(new_q),'before_source_or_new_patch_vertices_inside_tool':before_contain,
        'after_source_or_new_patch_vertices_inside_tool':after_contain,
        'before_inside_broadphase_n':baseline_near,'after_inside_broadphase_n':candidate_near,
        'original_52j_candidate_positions_sha256':hashlib.sha256(np.ascontiguousarray(source_positions).tobytes()).hexdigest(),
        'right_patch_candidate_positions_sha256':hashlib.sha256(np.ascontiguousarray(right_positions).tobytes()).hexdigest(),
        'alternate_equipment_or_joint_limits_authored':False}
print(json.dumps(report,indent=2,sort_keys=True))

