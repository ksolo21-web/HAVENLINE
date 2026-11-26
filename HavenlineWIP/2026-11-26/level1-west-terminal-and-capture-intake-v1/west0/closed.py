import numpy as np
from collections import Counter
from components import components
def tup(p):return tuple(np.around(p,10))
def area(t):
 a,b,c=np.asarray(t,float);return np.linalg.norm(np.cross(b-a,c-a))*.5
def edge_state(T):
 d=Counter()
 for t in T:
  for a,b in zip(t,np.roll(t,-1,axis=0)):
   d[(tup(a),tup(b))]+=1
 return d
def loops(T):
 d=edge_state(T)
 assert all(v==1 for v in d.values()), 'duplicate directed boundary edge'
 unpaired={b:a for a,b in d if (b,a) not in d}
 assert len(unpaired)==sum((b,a) not in d for a,b in d),'branching boundary'
 result=[]
 while unpaired:
  a=next(iter(unpaired));q=[a];b=unpaired.pop(a)
  while b!=a:
   q.append(b);b=unpaired.pop(b)
  assert len(q)>=3;result.append(np.array(q))
 return result
def orient2(a,b,c):
 u=b-a;v=c-a;return u[0]*v[1]-u[1]*v[0]
def cap(poly):
 # Keep exact boundary point IDs including collinear clipped triangle-line points.
 keep=[i for i in range(3) if np.ptp(poly,axis=0)[i]>1e-8]
 assert len(keep)==2, 'nonplanar boundary'
 xy=poly[:,keep]
 sign=np.sign(sum(a[0]*b[1]-a[1]*b[0] for a,b in zip(xy,np.roll(xy,-1,axis=0))))
 assert sign
 work=list(range(len(poly)));out=[]
 while len(work)>3:
  for k,b in enumerate(work):
   a,c=work[k-1],work[(k+1)%len(work)]
   if orient2(xy[a],xy[b],xy[c])*sign<=1e-13:continue
   blocked=False
   for j in set(work)-{a,b,c}:
    v=[orient2(xy[p],xy[q],xy[j])*sign for p,q in [(a,b),(b,c),(c,a)]]
    if min(v)>-1e-12:blocked=True;break
   if blocked:continue
   out.append([poly[a],poly[b],poly[c]]);work.remove(b);break
  else:raise AssertionError('could not close polygon with nondegenerate ears')
 out.append(poly[work]);assert all(area(t)>1e-13 for t in out)
 return out
def clip(T,z):
 out=[]
 for tri in T:
  q=[]
  for a,b in zip(tri,np.roll(tri,-1,axis=0)):
   aa=a[2]-z;bb=b[2]-z
   if aa<=0:q.append(a)
   if aa*bb<0:
    v=a+(b-a)*(-aa/(bb-aa));v[2]=z;q.append(v)
  for k in range(1,len(q)-1):
   tri=[q[0],q[k],q[k+1]]
   if area(tri)>1e-13:out.append(tri)
 return np.asarray(out)
def check(T):
 d=edge_state(T)
 assert all(v==1 and d[(b,a)]==1 for (a,b),v in d.items())
 assert min(area(t) for t in T)>1e-13
 x=T-np.mean(T.reshape(-1,3),axis=0)
 volume=float(np.einsum('ij,ij->',x[:,0],np.cross(x[:,1],x[:,2]))/6)
 assert abs(volume)>1e-8
 return volume
def orient(T):return T if check(T)>0 else T[:,[0,2,1]]
