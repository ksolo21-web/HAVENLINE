"""Proof whether the measured collar patch can preserve its entire fixed rim under load."""
from collections import defaultdict,deque
import contextlib,io,json
import numpy as np
with contextlib.redirect_stdout(io.StringIO()):
 from scope import A,rim,rim_faces,edge_face,F,Qf,R,P,f,cnt,rt
from scipy.spatial import cKDTree
boundary={edge for edge,_,_ in rim_faces}
neighbors=defaultdict(set)
for a,b in boundary:
 neighbors[a].add(b);neighbors[b].add(a)
sets=set(neighbors)
components=[]
while sets:
 front={sets.pop()}; seen=front.copy()
 while front:
  front=set.union(*(neighbors[z] for z in front))&sets
  seen|=front;sets-=front
 components.append(len(seen))
orig_u={x:int(np.flatnonzero(f.tags==x)[0]) for x in neighbors}
def compare(X):
 t=X[F];lo=t.min(1);hi=t.max(1);c=(lo+hi)*.5;rad=np.linalg.norm(hi-c,axis=1)
 kd=cKDTree(c)
 out=[]
 for a,b in sorted(boundary):
  i,j=orig_u[a],orig_u[b];u,v=X[[i,j]]; d=v-u
  center=(u+v)/2; rr=np.linalg.norm(d)/2+rad.max()
  ids=[z for z in kd.query_ball_point(center,rr+1e-10) if z not in A and a not in Qf[z] and b not in Qf[z]]
  for z in ids:
   n0,n1,n2=t[z]; e=n1-n0; g=n2-n0
   p=np.cross(d,g);den=e@p
   if abs(den)<1e-13:continue
   r=u-n0; q=np.cross(r,e)
   baryone=float(r@p/den);barytwo=float(d@q/den);tt=float(g@q/den)
   low=min(baryone,barytwo,1-baryone-barytwo,tt,1-tt)
   if low>1e-7:
    normal=np.cross(e,g);normal/=np.linalg.norm(normal)
    signed=np.array([(u-n0)@normal,(v-n0)@normal])
    out.append(dict(boundary_raw_edge=[i,j],protected_opponent_source_face=z,
      incident_patch_faces=[f for f,*_ in edge_face[(a,b)] if f in A],
      actual_finite_barycentric_min=low,strict_edge_fraction=tt,opposed_signed_end_distance_mm=(signed*1000).tolist()))
 return out
out={'closed_boundary_cycles':components,'patch_euler_characteristic':len({x for face in A for x in Qf[face]})-len(cnt)+len(A),
     'patch_source_face_ids':sorted(A),'immutable_boundary_pierces_protected_neutral':compare(R),
     'immutable_boundary_pierces_protected_loaded':compare(P),'no_source_edits':True}
print(json.dumps(out,indent=2))
