import contextlib,io,runpy,json, numpy as np
from scipy.spatial.transform import Rotation
with contextlib.redirect_stdout(io.StringIO()):s=runpy.run_path('hvn-l1-c1-fingered-harvest-authority-v1/check.py')
V,F,W,G,walk=s['V'],s['faces'],s['W'],s['G'],s['walk']
I=s['a'](s['d']['skins'][0]['inverseBindMatrices']).reshape((-1,4,4)).transpose((0,2,1)); J=s['j']
# Recompute bind through the original model and all 12 influence columns.
parts=(G[J]@I)
raw=np.c_[V,np.ones(len(V))]
B=np.zeros_like(V,dtype=float)
for k,m in zip(J,parts):B+=(raw@m.T)[:,:3]*W[:,k,None]
def unit(v):return v/np.linalg.norm(v)
def norm(t):
 r=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]);return r/np.maximum(np.linalg.norm(r,axis=1)[:,None],1e-30)
def crossing(t,u):
 def one(a,b):
  n=np.cross(b[:,1]-b[:,0],b[:,2]-b[:,0]); ab=b[:,1]-b[:,0]; ac=b[:,2]-b[:,0]
  area=np.linalg.norm(n,axis=1); eps=1e-9*area
  out=np.zeros(len(a),bool)
  for i in range(3):
   p=a[:,i];q=a[:,(i+1)%3]; v=q-p
   sd=np.einsum('bi,bi->b', p-b[:,0],n); ed=np.einsum('bi,bi->b',q-b[:,0],n)
   ix=((sd>eps)&(ed<-eps))|((sd<-eps)&(ed>eps))
   if not ix.any():continue
   c=p[ix]+v[ix]*(sd[ix]/(sd[ix]-ed[ix]))[:,None]-b[ix,0]
   u=np.einsum('bi,bi->b',np.cross(c,ac[ix]),n[ix])/area[ix]**2
   w=np.einsum('bi,bi->b',np.cross(ab[ix],c),n[ix])/area[ix]**2
   out[ix]|=(u>1e-7)&(w>1e-7)&(u+w<1-1e-7)
  return out
 return one(t,u)|one(u,t)
frames=json.load(open('hvn-l1-c1-73-provisional-flex-screen-v1/readout.json'))
surf=B[F]; center=surf.mean(1); normals=norm(surf); fl=surf.min(1);fh=surf.max(1)
out={}
for wrist,parent,hinge,tip,thumb,sgn in [(27,25,24,23,10,1),(52,46,45,44,35,-1)]:
 side=np.array(frames[str(wrist)]['test_cross'])*sgn
 e=unit(G[tip,:3,3]-G[hinge,:3,3]); axis=unit(np.cross(e,side))
 pivot=G[hinge,:3,3]; D=walk(hinge); own=W[:,D].sum(1)
 mean=own[F].mean(1); candidates=np.where((mean>.1)&((normals@side)>.3)&((center-pivot)@e>0))[0]
 if len(candidates)==0:
  eligible=np.where((mean>.1)&((center-pivot)@e>0))[0]
  distal=np.where(((center-pivot)@e>0)&(mean>0))[0]
  out[wrist]={'failure':'no distal landmark passed influence and sidedness gates','all_affected_faces':int(np.any(own[F]>0,axis=1).sum()),'distal_faces_with_positive_influence':len(distal),'distal_mean_gt_point1_faces':len(eligible),'eligible_max_inward_dot':float((normals[eligible]@side).max()) if len(eligible) else None,'max_distal_face_mean':float(mean[distal].max()) if len(distal) else None};continue
 # Pick the strongest side-facing isolated pad nearby, not a post-treatment selection.
 top=candidates[np.argsort(-mean[candidates])[:25]]; i=int(top[np.argmax(normals[top]@side)])
 tw=W[:,walk(thumb)].sum(1); near=np.flatnonzero((tw[F].min(1)>=.90)&((normals@unit(center[i]-G[thumb,:3,3]))>.25))
 dist=np.linalg.norm(center[near]-center[i],axis=1); k=int(near[np.argmin(dist)])
 affected=np.where(np.any(own[F]>0,axis=1))[0]; rows=np.unique(F[affected]); first=np.flatnonzero(np.isin(F,rows).any(1))
 inner={}
 def pairs(X):
  A=X[F]; lo=A.min(1);hi=A.max(1); fresh=set()
  for a in affected:
   j=np.flatnonzero(np.all((lo<=hi[a]+1e-10)&(hi>=lo[a]-1e-10),axis=1))
   j=j[(j!=a)&~np.isin(s['wf'][j],s['wf'][a]).any(1)]
   if len(j):
    hit=crossing(np.broadcast_to(A[a],A[j].shape),A[j])
    fresh.update(tuple(sorted((int(a),int(q)))) for q in j[hit])
  return fresh
 old=pairs(B)
 for sign in [-1,1]:
  R=Rotation.from_rotvec(axis*np.deg2rad(sign*5)).as_matrix(); X=B.copy()
  for node in D:
   L=(raw@(G[node]@I[J.index(node)]).T)[:,:3]
   X+=(((L-pivot)@R.T+pivot)-L)*W[:,node,None]
  change=np.linalg.norm(X[F[i]].mean(0)-X[F[k]].mean(0))-np.linalg.norm(center[i]-center[k])
  dots=np.einsum('bi,bi->b',norm(X[F[first]]),normals[first]);new=pairs(X)-old
  inner[sign]={'change_to_thumb_mm':float(1000*change),'first_ring_min_dot':float(dots.min()),'first_ring_flips':int((dots<=0).sum()),'new_strict_pairs':len(new),'first_new_pairs':sorted(new)[:12]}
 out[wrist]=dict(index_face=i,index_indices=F[i].tolist(),index_face_weight=float(mean[i]),index_face_sided_normal=normals[i].tolist(),thumb_face=k,thumb_indices=F[k].tolist(),thumb_face_weight=float(tw[F[k]].min()),axis=axis.tolist(),hinge=hinge,faces_affected=len(affected),first_ring=len(first),baseline_strict_pairs=len(old),tests=inner)
print(json.dumps(out,indent=2))
