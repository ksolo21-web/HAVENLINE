"""Detached right-thumb pose specimen; source-bound analysis, not native animation."""
from source import *
import ast
from scipy.sparse import diags
from scipy.spatial.transform import Rotation
from scipy.spatial import ConvexHull
root=Path('..')
def check(path,sha):
 p=root/path; assert digest(p)==sha, (p,digest(p)); return p
src=check(Path('c1-full-detail-rig-witness-v1/build.py'),'d9dc82bcdd279b557a76277a24b500f3117ccfde293b921784623533207fd04b')
check(Path('c1-full-detail-rig-witness-repair-v2/repair.py'),'3cd5ec5ef1ea97dc8c898428fd52b5cba48d4024ef9cda82c94cf82379f74d53')
uvdir=root/'hvn-c1-owner-right-palm-uv-v1'
check(Path('hvn-c1-owner-right-palm-uv-v1/result.json'),'7347ad773b7fcc0b8012cb742fb9f98620705b2c106f5c4820a835e234b93d41')
off=root/'hvn-c1-right-offband-preflight-v1'
assert digest(off/'SHA256SUMS')=='6b3094a66507c47ded1ff2ce61fdf279cb3da9056e99c455dcdd5da5ecb54ed7'
for ln in (off/'SHA256SUMS').read_text().splitlines():
 sh,n=ln.split(); assert digest(off/n)==sh
offr=json.loads((off/'result.json').read_text()); off_pairs=np.array(offr['indices'][0]['raw_pairs'])
assert off_pairs.shape==(206,2)
local=np.load(uvdir/'reauthored-review-LOCAL.npz',allow_pickle=False)
uvj=json.loads((uvdir/'result.json').read_text())
for k,sh in uvj['base_local_candidate_array_SHA256'].items():
 assert hashlib.sha256(np.ascontiguousarray(local[k]).tobytes()).hexdigest()==sh
P=P.astype(np.float64)
ix={str(n):i for i,n in enumerate(names)}
bind_digs=next(ast.literal_eval(x.value) for x in ast.parse(src.read_text()).body if isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='DIGS' for t in x.targets))
# Weight repair v2 port. No weight mutation on the source/any artifact.
Q,ind,inv=np.unique(P.astype(np.float32).round(6),axis=0,return_index=True,return_inverse=True)
C=(W[ind]/1000).astype('float32')
assert np.array_equal(W,W[ind][inv])
E=np.unique(np.sort(inv[bis],axis=1),axis=0); E=E[E[:,0]!=E[:,1]]
def smooth(t,a,b):
 k=np.clip((t-a)/(b-a),0,1);return k*k*(3-2*k)
R=C.copy()
digs=('index','middle','ring','pinky','thumb')
for side,si in [('L',1),('R',-1)]:
 X,Y,Z=Q.T; X=X*si
 env=smooth(X,.731,.750)*(1-smooth(X,.848,.875))*smooth(Z,.355,.385)*(1-smooth(Z,.506,.535))
 region=(X>.730)&(X<.889)&(Z>.345)&(Z<.545)
 ee=E[np.all(region[E],axis=1)]
 ii,k=np.unique(ee,return_inverse=True); k=k.reshape(-1,2)
 w=np.clip(.0028/np.maximum(np.linalg.norm(Q[ee[:,0]]-Q[ee[:,1]],axis=1),.0005),.5,2.2)
 adj=coo_matrix((np.r_[w,w],(np.r_[k[:,0],k[:,1]],np.r_[k[:,1],k[:,0]])),shape=(len(ii),len(ii))).tocsr()
 M=diags(1/np.maximum(np.asarray(adj.sum(1)).ravel(),1e-10))@adj
 pcs=[ix['hand.'+side]]+[ix[f'{d}.{j:02}.{side}'] for d in digs for j in (1,2,3)]
 assert np.max(1-C[ii][:,pcs].sum(1))<1e-5
 yy=C[np.ix_(ii,pcs)].astype(float); b0=yy.copy()
 for _ in range(28): yy=yy*.45+(M@yy)*.55
 cnt=np.sort(yy[:,1:].reshape(len(ii),5,3).sum(2),axis=1)[:,-2:]
 damp=.48*smooth(cnt[:,0]/np.maximum(cnt[:,1],1e-10),.10,.68)
 yy[:,0]+=(yy[:,1:]*damp[:,None]).sum(1); yy[:,1:]*=(1-damp[:,None])
 q=env[ii]; yy=b0*(1-q[:,None])+yy*q[:,None]
 jj=np.argpartition(yy,-4,axis=1)[:,-4:]; vals=np.take_along_axis(yy,jj,axis=1)
 vals/=vals.sum(1)[:,None]; it=np.round(vals*10000).astype(np.int16); it[np.arange(len(ii)),vals.argmax(1)]+=10000-it.sum(1)
 out=np.zeros_like(yy);np.put_along_axis(out,jj,it/10000,axis=1)
 R[np.ix_(ii[q>0],pcs)]=out[q>0]
R=R[inv]
changed_w=np.count_nonzero(np.any(R!=(W/1000).astype(np.float32),axis=1))
assert changed_w==11714,(changed_w,)
# Read transform from actual single-weight physical landmarks, with rank and error gates.
def fit(name):
 ids=np.flatnonzero(R[:,ix[name]]==1)
 assert len(ids)>8,(name,len(ids))
 x=P[ids];y=V[ids]; xc=x-x.mean(0);yc=y-y.mean(0)
 u,sv,v=np.linalg.svd(xc.T@yc)
 rot=v.T@u.T; assert np.linalg.det(rot)>0.999999 and min(sv)>1e-7
 t=y.mean(0)-rot@x.mean(0)
 err=np.max(np.linalg.norm(x@rot.T+t-y,axis=1))
 assert err<2e-7,(name,err)
 return rot,t,ids,sv,err
def unit(v):
 assert np.linalg.norm(v)>1e-7
 return v/np.linalg.norm(v)
thumb=['thumb.02.R','thumb.03.R']; selected='thumb.03.R'; chosen=[ix[selected]]
move=np.flatnonzero(np.any(R[:,chosen]>0,axis=1))
wrist=ix['hand.R']
assert len(move)>100 and (P[move,0]<-.69).all(), (len(move),P[move].min(0),P[move].max(0))
adj=F[local['removed']]
e=np.sort(np.concatenate([adj[:,[0,1]],adj[:,[1,2]],adj[:,[2,0]]]),axis=1)
e,c=np.unique(e,axis=0,return_counts=True)
se=np.unique(e[c==1]); assert len(se)==57
# Exact original indexed cuff-edge vertices; even tiny weight is a hard stop.
cu=np.unique(s['R_loop_source_vertex_edges'])
pin_counts={n:{'cuff':int(np.count_nonzero(R[cu,ix[n]])),'seam':int(np.count_nonzero(R[se,ix[n]])),'palm':int(np.count_nonzero(local['weights'][:,ix[n]]))} for n in thumb}; assert pin_counts['thumb.02.R']['seam']==4
assert np.intersect1d(move,cu).size==0 and np.intersect1d(move,se).size==0
assert np.all(local['weights'][:,chosen]==0)
# Preserve exact authored web incidence and its endpoints as the independent read-only right chart record.
web=np.array([7002,7333,7699,7754,8224,8284,10268,10274],int)
assert np.intersect1d(move,web).size==0
relevant=np.flatnonzero(np.any(R[move]>0,axis=0))
frames={}
inferred_idle_digit=[]
rh,th,*_=fit('hand.R')
for j in sorted(set(relevant)|{ix[n] for n in ('hand.R','thumb.02.R','index.02.R','middle.02.R')}):
 n=str(names[j])
 if (R[:,j]==1).sum()<=8:
  assert n.startswith(('thumb.','index.','middle.')) and n.endswith('.R'),n
  # Chest author only rotates shoulder/forearm/wrist, no independent digit pose.
  # Check dominant indexed rows directly under inherited rigid matrix, then
  # validate all relevant mixed rows against exact held before any movement.
  ids=np.flatnonzero((R[:,j]>.30)&(R.argmax(1)==j))
  assert len(ids)>18,(n,len(ids))
  vv=P[ids]-P[ids].mean(0); sv=np.linalg.svd(vv.T@vv,compute_uv=False)
  er=float(np.linalg.norm(P[ids]@rh.T+th-V[ids],axis=1).max())
  assert er<5e-7 and sv[-1]>1e-7,(n,er,sv)
  frames[n]=(rh,th,ids,sv,er); inferred_idle_digit.append(n)
 else: frames[n]=fit(n)

def section(n,sel,dir_hint):
 # Keep actual indexed samples but collapse exact split positions for centroid weighting.
 rr,tt,ids,sv,err=frames[n]
 line=unit(dir_hint)
 tau=P[ids]@line; a,b=np.quantile(tau,[.32,.68])
 lo=ids[tau<=a];hi=ids[tau>=b]; assert len(lo)>8 and len(hi)>8
 def ctr(v):
  _,i=np.unique(P[v],axis=0,return_index=True)
  v=v[i];return P[v].mean(0),V[v].mean(0),v
 p0,h0,i0=ctr(lo);p1,h1,i1=ctr(hi)
 bind=unit(p1-p0);held=unit(h1-h0)
 assert bind@line>.75 and held@(rr@bind)>.99999
 return bind,held,p0,p1,h0,h1,i0,i1
normal=unit(-np.array(J['sides']['R']['outward']))
hand_r,hand_t,hi,_,_=frames['hand.R']
idxp=J["sides"]["R"]["palm_vertex"]; palm=np.flatnonzero((np.linalg.norm(P-P[idxp],axis=1)<.018)&(R[:,wrist]>.45))
assert len(palm)>12
# Pick actual shaft-facing palm rows in upper quantile of signed projected depth.
score=V[palm]@normal
palm=palm[score>=np.quantile(score,.65)]
palm_w=V[palm].mean(0); palm_b=P[palm].mean(0)
pa=V[F[(np.isin(F,palm).sum(1)>=2)]]
pn=np.cross(pa[:,1]-pa[:,0],pa[:,2]-pa[:,0])
pn=pn[np.linalg.norm(pn,axis=1)>1e-12]
pn_dot=pn@normal/np.linalg.norm(pn,axis=1)
assert len(pn_dot)>10

assert len(palm)>5
axes={}; deltas={}
for nd,i in [('thumb.02.R',1),('thumb.03.R',2),('index.02.R',1),('middle.02.R',1)]:
 dg=nd.split('.')[0]
 knots=np.array(bind_digs[dg]);knots[:,0]*=-1
 rr,tt,ids,sv,err=frames[nd]
 bone_axis=unit(knots[i+1]-knots[i])
 tb,t,p0,p1,h0,h1,a0,a1=section(nd,ids,bone_axis)
 pivot=rr@knots[i]+tt
 if dg=='thumb':
  inward=palm_w-h1
 else:
  inward=normal
 o=inward-t*(t@inward)
 assert np.linalg.norm(o)>.005 if dg=='thumb' else np.linalg.norm(o)>.25
 curl_n=unit(o); axis=unit(np.cross(t,curl_n)); bind_axis=rr.T@axis
 # Independent sign: existing material section's forward chord must curl toward traced palm
 # for positive rotation, away for negative. Reversing either sign or axis is rejected.
 k=np.dot(np.cross(axis,t),curl_n)
 assert k>.99999 and np.dot(np.cross(-axis,t),curl_n)<-.99999
 axes[nd]={'held_axis':axis.tolist(),'bind_reference_axis':bind_axis.tolist(),'signed_held_closing_direction':curl_n.tolist(),'anatomical_sample_chord_dot_original_bone_direction':float(tb@bone_axis),'paired_sample_sizes':[len(a0),len(a1)],'fit_or_inherited_dominant_rows':len(ids),'frame_was_inherited_and_verified':nd in inferred_idle_digit,'frame_max_error_m':err,'frame_min_sv':float(min(sv)),'sign_control_score':k,'pivot_held':pivot.tolist()}
 if nd in thumb: deltas[nd]=(rr,tt,axis,pivot)
# Quaternion dual-quat skinning. Only evaluate exact source rows influenced by one staged
# rotation; every other row remains byte-identical by membership rather than pinning a solved result.
def mul(a,b):
 x,y,z,w=np.moveaxis(a,-1,0); X,Y,Z,W0=np.moveaxis(b,-1,0)
 return np.stack([w*X+x*W0+y*Z-z*Y,w*Y-x*Z+y*W0+z*X,w*Z+x*Y-y*X+z*W0,w*W0-x*X-y*Y-z*Z],axis=-1)
def real_dual(rot,t):
 q=Rotation.from_matrix(rot).as_quat(); return q,.5*mul(np.r_[t,0.],q)
def skin(fs):
 a,b=zip(*(real_dual(*fs[str(names[j])][:2]) for j in relevant))
 a=np.array(a);b=np.array(b)
 z=R[move][:,relevant].astype(float)
 first=np.argmax(z>0,axis=1)
 signs=np.sign(a[first]@a.T)
 assert (signs!=0).all()
 wz=z*signs
 q=wz@a; d=wz@b; norm=np.linalg.norm(q,axis=1)[:,None];q=q/norm;d=d/norm
 cq=q.copy();cq[:,:3]*=-1
 turn=Rotation.from_quat(q).apply(P[move])
 return turn + 2*mul(d,cq)[:,:3]
base=skin(frames)
base_err=np.linalg.norm(base-V[move],axis=1)
assert base_err.max()<5e-7,base_err.max()
def pose_test(spec):
 # One diagnostic perturbation at a derived anatomical joint. Changing only
 # parent .02 rotates both .02 and .03; .01 is held fixed by explicit grip seams.
 nd,theta=spec
 fs=frames.copy(); r,c,ax,pivot=deltas[nd]
 X=Rotation.from_rotvec(ax*np.deg2rad(theta)).as_matrix()
 for n in thumb[thumb.index(nd):]:
  rt,tt,*_=frames[n];fs[n]=(X@rt,pivot+X@(tt-pivot))
 nxt=skin(fs)
 # A signed normal formula alone can conceal a sign or skin transport error.
 # Re-skin the same actual pure distal landmarks under the reversed axis.
 inv=X.T; f_rev=frames.copy()
 for n in thumb[thumb.index(nd):]:
  rt,tt,*_=frames[n];f_rev[n]=(inv@rt,pivot+inv@(tt-pivot))
 back=skin(f_rev)
 phys=frames[nd][2]
 support_idx=np.flatnonzero(np.isin(move,phys))
 rail=V[move[support_idx]]
 l=rail@unit(np.cross(axes[nd]['signed_held_closing_direction'],ax))
 support_idx=support_idx[l>=np.quantile(l,.75)]
 toward=np.array(axes[nd]['signed_held_closing_direction'])
 sign_pos=float(np.median((nxt-base)[support_idx]@toward))
 sign_neg=float(np.median((back-base)[support_idx]@toward))
 assert sign_pos>5e-5 and sign_neg<-5e-5,(sign_pos,sign_neg)
 actual=np.array(V); actual[move]+=nxt-base
 before=V[move];h=actual[move]
 md=np.linalg.norm(h-before,axis=1)
 keep=np.flatnonzero(~np.isin(np.arange(len(P)),move))
 assert np.array_equal(V[keep],actual[keep])
 # Record exact source-space motion and hierarchy; negative control will reject
 # an axis sign reversal using constrained distal meridian chord.
 affected=np.flatnonzero(np.any(np.isin(F,move),axis=1) & ~np.isin(np.arange(len(F)),local['removed']))
 atr=actual[F[affected]]; base_tr=V[F[affected]]
 lo,hi=tool.min(1),tool.max(1)
 def strict_count(t):
  near=np.argwhere(((t.max(1)[:,None]>=lo[None])&(t.min(1)[:,None]<=hi[None])).all(2))
  hits=[]
  for i,j in near.tolist():
   if crosses(t[i],tool[j]) or crosses(tool[j],t[i]):hits.append((int(affected[i]),j))
  return set(hits)
 old=strict_count(base_tr); new=strict_count(atr)
 # Full shaft enclosure of moved originally impacted rows, not just facet strict hits.
 def winding(arr):
  t=tool[None]-arr[:,None,None]
  a,b,c=np.moveaxis(t,2,0); A,B,C=map(lambda z:np.linalg.norm(z,axis=2),(a,b,c))
  den=A*B*C+(a*b).sum(2)*C+(a*c).sum(2)*B+(b*c).sum(2)*A
  return np.arctan2((np.cross(a,b)*c).sum(2),den).sum(1)/(2*np.pi)
 offids=np.unique(F[np.unique(off_pairs[:,0])])
 a=winding(V[offids]);b=winding(actual[offids])
 return {'joint':nd,'distal_actual_index_samples_for_sign':int(len(support_idx)),'positive_palmward_median_mm':sign_pos*1000,'reversed_axis_palmward_median_mm':sign_neg*1000,'positive_angle_deg_diagnostic_only':theta,'max_moved_original_vertex_mm':float(md.max()*1000),'unchanged_outside_selected_influences':int(len(keep)),'strict_full_tool_pairs_affected_face_base':len(old),'strict_full_tool_pairs_affected_face_candidate':len(new),'removed_strict_pairs':len(old-new),'new_strict_pairs':len(new-old),'offband_source_rows_inside_tool_before':int((abs(a)>.5).sum()),'offband_source_rows_inside_tool_after':int((abs(b)>.5).sum()),'held_positions_sha256':hashlib.sha256(np.ascontiguousarray(actual).tobytes()).hexdigest()}
# Deliberately minimal fixed sample, no fitting, schedule ramp, or accepted angular limit.
straight=pose_test((selected,3.))
assert straight['strict_full_tool_pairs_affected_face_base']==206
report={'status':'HOLD_DIAGNOSTIC_NO_NATIVE_CLOSURE','exact_v2_weight_reproduced_changed_rows':int(changed_w),'missing_pure_idle_frame_using_frozen_hand_and_validated_against_all_mix_rows':inferred_idle_digit,'base_dqs_validation_count':len(move),'base_dqs_max_error_mm':float(base_err.max()*1000),'affected_only_chosen_digit_chain':[selected],'repaired_v2_seam_influence':pin_counts,'maximal_name_derived_noise_note':'source labels identify topology; signs derived from paired indexed centroids, measured palm and anatomy', 'palm_observed_vertices':len(palm),'palm_incident_outward_normals_n':len(pn_dot),'palm_incident_oriented_normal_median_cos_vs_fixed_shaft_direction':float(np.median(pn_dot)),'palm_incident_oriented_normal_positive_fraction':float(np.mean(pn_dot>0)),'signed_axes':axes,'zero_motion_control':np.array_equal(V[move]+(skin(frames)-base),V[move]),'locked_right_seam_count':len(se),'protected_right_cuff_edge_vertices':len(cu),'explicit_right_web_alias_and_join_vertices':web.tolist(),'locked_new_palm_local_rows':len(local['vertices']),'sole_static_specimen':straight,'limits_or_bilateral_authority_admitted':False}
print(json.dumps(report,indent=2,sort_keys=True))
