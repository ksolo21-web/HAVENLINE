"""One exact source-bound right boot transition weight correction, no mesh edits."""
import json, hashlib, importlib.util
from collections import Counter
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from intake import f,P,T,F,V,M,legacy,sha

arch=Path('../level1-c1-fastener-mounts-v1/cavity-assess.py').resolve()
assert sha(arch)=='cdf0184300e21eca848a1f5271f2473889fffe1b6d32a055215d99c214cabe2b'
s=importlib.util.spec_from_file_location('plane_witness',arch);mod=importlib.util.module_from_spec(s);s.loader.exec_module(mod)
assert len(f.P)==len(V)==52898 and len(F)==96001
a,b=F[[8677,8892]]
i=3777
assert i in b and i not in a
assert (f.tags==f.tags[i]).sum()==1
keep=f.slots.index('RCollarFlex');host=f.slots.index('RHeel')
j=f.J[i];w=f.W[i].copy()
fr=int(np.flatnonzero(j==keep)[0]);to=int(np.flatnonzero(j==host)[0])
active_bones=[f.slots[int(n)] for n,m in zip(j,w) if m>0]
assert len(active_bones)==4 and max(w)<.90 and keep!=host and w[fr]>.7 and w[to]>0
assert not any(x in active_bones for x in ['RBall','LBall','LHeel'])
assert not any(float(w[k])>=.96 for k,x in enumerate(active_bones) if 'Rigid' in x or 'Heel' in x)
# Pure original/native visible fastener cores are not permitted to move.
assert all(np.where(f.J[i]==x,f.W[i],0).sum()<.9999 for x,k in enumerate(f.slots) if 'Rigid_R_BootFastener' in k)
row_faces=np.flatnonzero((F==i).any(1))
assert len(row_faces)>=3 and not any(i in f.bounds[z]['faces'] for z in 'LR')
ref=P[a];tri=P[b]
n=np.cross(ref[1]-ref[0],ref[2]-ref[0]);n/=np.linalg.norm(n)
signs=(tri-ref[0])@n
k=int(np.flatnonzero(b==i)[0])
assert np.sum(signs<0)==1 and signs[k]<0
original_span=mod.proper_span(ref,tri)
assert original_span is not None
v=((M[host]-M[keep])@f.X[i])[:3]*f.S
effect=float(v@n)
assert effect>0
# One analytical correction to a predeclared physical separator. No loop,
# candidate backtracking, floor fitting, or neighboring weights changed.
margin=.0002
dose=(margin-signs[k])/effect
assert .0<dose<w[fr]
revised=w.copy()
revised[fr]-=dose; revised[to]+=dose
assert (0<=revised).all() and abs(revised.sum()-w.sum())<1e-15
X=np.concatenate([f.X[i,:3],[1.]])
new=f.V.astype(float)*f.S+f.base
def ensure_ground(P0):
 out={}
 for side,g in f.bounds.items():
  a=np.flatnonzero(g['leg']);xs=f.distance(P0,a)
  ar=P0[:,[0,2,1]].copy();ar[a,2]=xs
  sup=f.connected(ar,g['faces'],f.tags)
  out[side]={'true_sole_min_mm':float(xs.min()*1000),'support':sup,'selected_foot_row':g['anchor'],
             'selected_marker_gap_mm':float(f.distance(P0,[g['anchor']])[0]*1000)}
 return out
Q=P.copy()
Q[i]=sum(((M[n]@X)[:3]*m for n,m in zip(j,revised)))*f.S+f.base
control_replay=sum(((M[n]@X)[:3]*m for n,m in zip(j,w)))*f.S+f.base
assert np.max(np.abs(control_replay-P[i]))<1e-14
assert np.flatnonzero(np.any(Q!=P,axis=1)).tolist()==[i]
# Reference protected rest position remains identical (same total skin mass).
N=Q.copy();N[i]=new[i]
neutral_original=(sum((np.eye(4)@X)[:3]*m for m in w))*f.S+f.base
neutral_revised=(sum((np.eye(4)@X)[:3]*m for m in revised))*f.S+f.base
assert np.max(np.abs(neutral_original-neutral_revised))<1e-14
new_signs=(Q[b]-ref[0])@n
assert new_signs.min()>=margin-1e-12
assert mod.proper_span(ref,Q[b]) is None
gt0,gt1=ensure_ground(P),ensure_ground(Q)
# Finite real plane-line intersections across all neighbors of the changed
# indexed one-ring, not an isolated ray-to-point or a target-only assertion.
def intersections(A):
 xyz=A[F];lo=xyz.min(1);hi=xyz.max(1);cent=(lo+hi)*.5
 radius=np.linalg.norm(hi-cent,axis=1)
 tree=cKDTree(cent)
 seen=set();hits={}
 for x in row_faces:
  elig=np.array(tree.query_ball_point(cent[x],radius[x]+radius.max()+1e-10),int)
  elig=elig[((lo[elig]<=hi[x]+1e-10)&(hi[elig]>=lo[x]-1e-10)).all(1)]
  elig=elig[~np.isin(f.tags[F[elig]],f.tags[F[x]]).any(1)]
  for y in elig:
   pair=tuple(sorted((int(x),int(y))))
   if pair in seen:continue
   seen.add(pair)
   span=mod.proper_span(xyz[pair[0]],xyz[pair[1]])
   if span is not None:hits[pair]=span
 return seen,hits
ck0,c0=intersections(P);ck1,c1=intersections(Q)
assert (8677,8892) in c0 and (8677,8892) not in c1
def normals(A,nw):
 ids=F[row_faces]
 pose=A[ids];rest=new[ids]
 pose_n=np.cross(pose[:,1]-pose[:,0],pose[:,2]-pose[:,0])
 neutral_n=np.cross(rest[:,1]-rest[:,0],rest[:,2]-rest[:,0])
 D=sum(M[f.J[:,k],:3,:3]*f.W[:,k,None,None] for k in range(4))
 D[i]=sum(M[k,:3,:3]*m for k,m in zip(j,nw))
 x=(D[ids].mean(1)@neutral_n[:,:,None])[:,:,0]
 val=(x*pose_n).sum(1)
 return {int(a):float(b) for a,b in zip(row_faces,val) if b<=0}
o0=normals(P,w);o1=normals(Q,revised)
adj=np.unique(F[row_faces]);adj=adj[adj!=i]
edge=lambda X:np.linalg.norm(X[adj]-X[i],axis=1)
rat0=edge(P)/edge(new);rat1=edge(Q)/edge(new)
escaped={int(z) for z,r in zip(adj,rat0) if .5<=r<=2}
new_edge_fail=[int(z) for z,r in zip(adj,rat1) if int(z) in escaped and (r<.5 or r>2)]
fmt=lambda d:[{'faces':list(k),'proper_interval_mm':v*1000} for k,v in sorted(d.items())]
result=dict(status='HOLD_NO_GAIT',source_pose_seal='25fab394cfe7a4ea7a32e7b37faadebdd9bc6e3ae5ae54c9e07abed2e3ead393',local_scope='one right boot collar transition vertex adjacent to retained fastener',
 chosen_raw_row=i,pose_unchanged_rig_or_bones=True,mesh_or_outline_material_or_glb_changed=False,candidate_private_weights_only=True,
 funded_by=f.slots[keep],transferred_to=f.slots[host],
 dose_fraction=float(dose),neutral_delta_m=float(np.max(np.abs(neutral_original-neutral_revised))),
 rigid_fastener_core_and_source_sole_unchanged=True, sole_and_held_marker_before=gt0,sole_and_held_marker_after=gt1,
 moved_max_world_mm=float(np.linalg.norm(Q[i]-P[i])*1000),scoped_faces=row_faces.tolist(),target_pair=dict(faces=[8677,8892],interval_before_mm=original_span*1000,interval_after_mm=0,positive_target_same_side_margin_mm=float(new_signs.min()*1000)),
    candidate_check_count_before_after=[len(ck0),len(ck1)],changed_face_strict_pairs_before=fmt(c0),changed_face_strict_pairs_after=fmt(c1),
    newly_intersecting_pairs=fmt({k:c1[k] for k in c1.keys()-c0.keys()}),
    oriented_fail_before=o0,oriented_fail_after=o1,neighbor_length_ratio_range_before=[float(rat0.min()),float(rat0.max())],
    neighbor_length_ratio_range_after=[float(rat1.min()),float(rat1.max())],new_edges_failing_pointwise=sorted(new_edge_fail),
    native_raster_or_full_gait_qualified=False)
print(json.dumps(result,indent=2))
