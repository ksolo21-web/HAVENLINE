"""Read-only supplemental checks on exact archived owner geometry."""
import contextlib, io, json, sys
import numpy as np
from collections import Counter
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
with contextlib.redirect_stdout(io.StringIO()):
 import volume as m
def bary(tri,p):
 x=np.linalg.solve((tri[1:]-tri[0]).T,p-tri[0]); return np.r_[1-x.sum(),x]
def perp(a,b):return a[0]*b[1]-a[1]*b[0]
def intersections(a,b):
 yield from (v for v in a if min(bary(b,v))>=-1e-10)
 yield from (v for v in b if min(bary(a,v))>=-1e-10)
 for x,y in zip(a,np.roll(a,-1,axis=0)):
  for u,v in zip(b,np.roll(b,-1,axis=0)):
   D=perp(y-x,v-u)
   if abs(D)<1e-16: continue
   t=perp(u-x,v-u)/D; s=perp(u-x,y-x)/D
   if -1e-10<=t<=1.+1e-10 and -1e-10<=s<=1.+1e-10:yield x+t*(y-x)
j=127; ft=m.tool[j]; qb=m.proj(ft); dz=(ft-m.ref)@m.n
worst=[]
for i in np.flatnonzero(m.parents==16686):
 tri=m.tris[i]; qa=m.proj(m.pt[tri]); dd=(m.pt[tri]-m.ref)@m.n
 for p in intersections(qa,qb):
  w=bary(qa,p); z=bary(qb,p)@dz; rhs=z+.000075-w@dd
  editable=sum(w[k] for k,x in enumerate(tri) if x not in m.fixed)
  if editable>1e-10: worst.append((rhs/editable,int(i),rhs,editable))
v,i,r,e=max(worst)
assert abs(v*1000-22.031479)<1e-6 and v>.006
E=[k for k,n in m.edges_all.items() if n==1]
assert len(E)==57 and set(Counter(np.ravel(E)).values())=={2}
tool=m.tool; AB=tool[:,1]-tool[:,0]; AC=tool[:,2]-tool[:,0]
N=np.cross(AB,AC); N/=np.linalg.norm(N,axis=1)[:,None]
def finite_edge(a,b, strict=True):
 aa=np.einsum('ij,ij->i',a-tool[:,0],N); bb=np.einsum('ij,ij->i',b-tool[:,0],N)
 candidates=np.flatnonzero((abs(aa-bb)>1e-14)&(aa*bb<=1e-22))
 out=[]
 for j in candidates:
  x=aa[j]/(aa[j]-bb[j]); p=a+x*(b-a)
  u,v=np.linalg.lstsq(np.array([AB[j],AC[j]]).T,p-tool[j,0],rcond=None)[0]
  if strict and min(x,1-x,u,v,1-u-v)>1e-9: out.append(int(j))
  if not strict and min(x,1-x,u,v,1-u-v)>-1e-9: out.append(int(j))
 return out
assert finite_edge(*m.V[[8768,8741]])==[125] and finite_edge(*m.V[[9667,9605]])==[127]
assert all(not finite_edge(*m.V[list(edge)],strict=False) for edge in E)
# Independent exterior cross-check: two oblique ray parity checks, rather
# than centering the test on the same solid-angle vertex/midpoint routine.
# Ignore shared-edge ambiguities by asserting there are none for these rays.
counts=[]
for direction in ([1.,.573,.317],[-.271,.811,1.]):
 counts.append([])
 for pos in np.r_[m.V[np.unique(E)],m.V[np.array(E)].mean(1)]:
  n=len(finite_edge(pos,pos+100*np.array(direction),strict=False))
  assert n%2==0; counts[-1].append(n)
print(json.dumps({'cut_faces':len(m.patch),'check_facets':len(tool),'cut_edges_without_detected_contact':len(E),'ray_even_exterior_checks':sum(map(len,counts)),
 'positive_controls':[125,127],'cap_witness':{'m':v,'child':i,'parent':16686,'tool_facet':j,'rhs_mm':r*1000,'editable_weight':e},
 'old_direction_limit_only':True,'status':'HOLD'},indent=2,sort_keys=True))
