import os
import numpy as np,json,hashlib
from pathlib import Path
P=Path(__file__).resolve().parent
D0=Path(os.environ['C1_COLLAR_DATA'])
S0=Path(os.environ['C1_KNEE_DATA'])/'poses.npz'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(D0/'exact-assembled-surface.npz')=='8a7222ecdb893da3da09dba34ac3c56f1f95f7f6e7269f1e9d165eca0ef074f7'
assert sha(S0)=='c16ef2874698851d6a237e14779166f2346ca3d89f4e520738252769664d2ef5'
A=np.load(D0/'exact-assembled-surface.npz')
B=np.load(S0);R=A['v'];T=A['tri'];W=A['w'];UV=A['UV'].reshape(-1,3,2);O=B['source_origin'];S=float(B['scale'])
target=[26992,27689];F=T[target];roi=R[F]
floor=roi.mean((0,1))
def norm(v):return np.linalg.norm(v,axis=-1)
def unit(v):return v/norm(v)
def normal(u):return unit(np.cross(u[1]-u[0],u[2]-u[0]))
def bary(P,A):
 y=P-A[0]; m=(A[1:]-A[0]).T
 d=np.linalg.lstsq(m,y,rcond=None)[0]
 return np.r_[1-d.sum(),d]
def segtri(p,q,T):
 t=normal(T); a=(p-T[0])@t; b=(q-T[0])@t
 if a*b>0 or abs(a-b)<1.e-14:return None
 x=p+(q-p)*a/(a-b); y=bary(x,T)
 if y.min()>=-1e-10:return x
def hits(A,B):
 c=[]
 for p,q in ((A,B),(B,A)):
  for i in range(3):
   x=segtri(p[i],p[(i+1)%3],q)
   if x is not None and all(norm(x-y)>1.e-10 for y in c):c.append(x)
 return c
def segment_dist(P,Q,R,S):
 u=Q-P;v=S-R;w=P-R
 a=u@u;b=u@v;c=v@v;d=u@w;e=v@w
 z=[]
 for x in (0.,1.):
  y=np.clip((e+x*b)/c,0,1);z.append(norm(w+x*u-y*v))
 for y in (0.,1.):
  x=np.clip((y*b-d)/a,0,1);z.append(norm(w+x*u-y*v))
 D=a*c-b*b
 if D>1e-30:
  x=(b*e-c*d)/D;y=(a*e-b*d)/D
  if 0<=x<=1 and 0<=y<=1:z.append(norm(w+x*u-y*v))
 return min(z)
def point_face(x,t):
 y=x-((x-t[0])@normal(t))*normal(t)
 return norm(y-x) if bary(y,t).min()>=-1e-10 else float('inf')
def tri(A,B):
 hit=hits(A,B)
 sd=[point_face(x,B) for x in A]+[point_face(x,A) for x in B]
 sd.extend(segment_dist(A[i],A[(i+1)%3],B[j],B[(j+1)%3]) for i in range(3) for j in range(3))
 return dict(intersections=len(hit),edge_cross_points_mm=[(x*1000).tolist() for x in hit],crossing_span_mm=0 if len(hit)<2 else max(norm(x-y) for x in hit for y in hit)*1000,true_distance_mm=0 if hit else min(sd)*1000,dihedral_normal_angle_deg=float(np.degrees(np.arccos(np.clip(normal(A)@normal(B),-1,1)))),leg_A_signed_to_B_mm=(((A-B[0])@normal(B))*1000).tolist(),leg_B_signed_to_A_mm=(((B-A[0])@normal(A))*1000).tolist())
def bone(p,key):
 q=p/S+O
 M=B['bones'][key,1]
 x=(np.einsum('kij,nj->nki',M[:,:3,:3],q)+M[:,None,:3,3].transpose(1,0,2)-O)*S
 return x
neighbors={}
for j,g in zip(target,F):
 ids=np.flatnonzero((np.isin(T,g).sum(1)>=2)&(np.arange(len(T))!=j))
 neighbors[str(j)]=[dict(face=int(i),source_corner_uv=UV[i].tolist(),posed_group_rest_shin=W[T[i],1].tolist(),adjacent_rest_vertices=T[i].tolist(),rest_normal=normal(R[T[i]]).tolist()) for i in ids]
sel=np.unique(F)
shots=[]
for k in (1,2):
 allbone=bone(R[sel],k); pure=allbone[:,1]
 actual=np.einsum('nki,nk->ni',allbone,W[sel]);ri=np.searchsorted(sel,F)
 data={'t_ms':[0,75,150][k],'actual_existing':tri(*actual[ri]),'pure_shin_counterfactual_diagnostic':tri(*pure[ri]),'non_shin_residual_per_vertex_mm':dict(zip(map(str,sel), (norm(actual-pure)*1000).tolist())),'local_actual_coords_mm':(actual[ri]*1000).tolist()}
 # full rigid inverse of Shin removed (not pose creation): useful source
 # cross-section for seeing offset of only soft transported extra influence.
 M=B['bones'][k,1,1]; act_raw=actual/S+O
 back=((act_raw-M[:3,3])@M[:3,:3]-O)*S
 delta=back-R[sel]
 data['shin_local_rest_equivalent_displacements_mm']=dict(zip(map(str,sel),(delta*1000).tolist()))
 shots.append(data)
r=dict(source={'collar':sha(D0/'SHA256SUMS'),'poses':sha(S0)},face_indices=target,raw_sets=F.tolist(),shared_vertices=int(len(set(F[0])&set(F[1]))),rest=tri(*roi),rest_bounds_mm=(np.stack((roi.min((0,1)),roi.max((0,1))))*1000).tolist(),rest_uv=UV[target].tolist(),source_corner_names=['thigh.R','shin.R','foot.R','toe.R'],rest_weights=W[F].tolist(),adjacent=neighbors,held=shots)
(P/'witness.json').write_text(json.dumps(r,indent=2,default=lambda x:x.item()))
print('rest',r['rest'])
for z in shots:print(z['t_ms'],z['actual_existing'],z['pure_shin_counterfactual_diagnostic'],z['non_shin_residual_per_vertex_mm'])
# Exact one-ring compatibility, no new poses. This is an analytical diagnostic
# only, not substituted skin anywhere. Geometry remains outside work files.
faces=sorted(set(target)|{a['face'] for vs in neighbors.values() for a in vs})
srcV=np.unique(T[faces])
loc=np.searchsorted(srcV,T[faces])
pair=[]
for key in (1,2):
 allb=bone(R[srcV],key)
 actual=np.einsum('nki,nk->ni',allb,W[srcV])
 test=allb[:,1]
 out={}
 for name,P0 in [('immutable',actual),('pure_shin_math_control',test)]:
  q=[]
  for i,f0 in enumerate(faces):
   for j in range(i+1,len(faces)):
    if np.isin(loc[i],loc[j]).any():continue
    obs=hits(P0[loc[i]],P0[loc[j]])
    if obs:q.append([f0,faces[j]])
  out[name]=q
 out['ms']=[0,75,150][key];pair.append(out)
rv=[{ 'face':i,'uv_range':np.ptp(UV[i],axis=0).tolist(),'any_cornerless_than_99pct_shin':bool(np.any(W[T[i],1]<.99))} for i in faces]
(P/'one-ring.json').write_text(json.dumps(dict(neighbor_faces=faces,observed_pair_bands=rv,diagnostic_pairs=pair),indent=2));print(faces,pair)
