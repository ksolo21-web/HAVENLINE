from pathlib import Path
import json,itertools,numpy as np
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parent
def parse(p):
 V=[];T={}
 for ln in p.read_text().splitlines():
  c=ln.split()
  if c[0]=='o':tag=c[1];T[tag]=[]
  elif c[0]=='v':V.append(tuple(map(float,c[1:])))
  else:T[tag].append(tuple(int(i)-1 for i in c[1:]))
 return np.array(V),{k:np.array(t) for k,t in T.items()}
def edge(A,B,C):
 D=B[0]-A[0]; e=C[1]-C[0]; f=C[2]-C[0]
 q=np.cross(D,f);den=e@q
 if abs(den)<1e-16:return None
 v=A[0]-C[0]; b=v@q/den; r=np.cross(v,e); c=D@r/den; u=f@r/den
 if min(b,c,1-b-c,u,1-u)>1e-6:return (A[0]+D*u).tolist()
def proper(A,B):
 for X,Y in [(A,B),(B,A)]:
  for i in range(3):
   z=edge([X[i]],[X[(i+1)%3]],Y)
   if z is not None:return z
R={}
for label in ('neutral','held'):
 V,T=parse(P/f'proof-{label}.obj')
 trees={n:BVHTree.FromPolygons(V.tolist(),t.tolist(),all_triangles=True) for n,t in T.items()}
 out={}
 for a,b in itertools.combinations(T,2):
  hits=trees[a].overlap(trees[b]); good=[]
  for i,j in hits:
   p=proper(V[T[a][i]],V[T[b][j]])
   if p is not None:good.append([i,j,p])
  out[a+'/'+b]=dict(candidates=len(hits),strict_proper_crossings=len(good),first_proper=good[0] if good else None)
 for a in T:
  if a=='replacement-hole-retained':continue
  t=T[a];e=t[:,((0,1),(1,2),(2,0))].reshape(-1,2);_,i,c=np.unique(np.sort(e,1),axis=0,return_counts=True,return_inverse=True)
  out[a+'_closed_consistent']=bool((c==2).all() and not np.bincount(i,weights=np.where(e[:,0]>e[:,1],1,-1)).any())
 R[label]=out
print(json.dumps(R,indent=2))
(P/'independent-kernel.json').write_text(json.dumps(R,indent=2))
