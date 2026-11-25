"""Prove piecewise-linear height-order feasibility, with pinned fixed seams."""
from pathlib import Path
from itertools import combinations
import json,hashlib,numpy as np,os
from scipy.optimize import Bounds,LinearConstraint,milp
p=Path(__file__).resolve().parent
source=Path(os.environ['C1_THENAR_DATA'])
sha=lambda t:hashlib.sha256(t.read_bytes()).hexdigest()
assert sha(source/'editable_thenar_join.npz')=='3215b8841c347d1e93c8c5186cf79255e58385a64563229fa6d7ade66089be90'
k=np.load(source/'editable_thenar_join.npz')
V=k['open'];T=k['local_bridge_faces'];bearing=k['actual_pressure_triangle']
origin=V[bearing].mean(0)
unit=lambda a:a/np.linalg.norm(a)
ex=unit(V[bearing[1]]-V[bearing[0]])
n=unit(np.cross(ex,V[bearing[2]]-V[bearing[0]]))
if n[0]<0:n=-n
ey=np.cross(n,ex)
X=1000*(V-origin)@np.column_stack((ex,ey))
Z=1000*(V-origin)@n
gids=k['bridge_authority_vertex_ids'];fixed=set(int(x) for x in np.r_[k['source_web_vertices'],k['source_dorsal_authority_path'],bearing])
free=sorted(set(gids.tolist())-fixed)
assert free==[90,91,92]
assert len(fixed)==10
# Replacing height only; projected boundaries and all barycentric coefficients
# unchanged. Use exact projected lines in mm and deterministic tolerances.
def det(u,v):return float(u[0]*v[1]-u[1]*v[0])
def clip(tr,other):
 P=[z.copy() for z in tr]
 if det(other[1]-other[0],other[2]-other[0])<0:other=other[::-1]
 for a,b in zip(other,np.roll(other,-1,axis=0)):
  if not P:return []
  E=b-a;new=[]
  for q,r in zip(P,P[1:]+P[:1]):
   s=det(E,q-a);t=det(E,r-a)
   if s>=-1e-9:new.append(q)
   if (s>1e-9 and t<-1e-9) or (s<-1e-9 and t>1e-9):new.append(q+s/(s-t)*(r-q))
  P=new
 q=[]
 for x in P:
  if all(np.linalg.norm(x-y)>1e-7 for y in q):q.append(x)
 if len(q)<3:return []
 ar=abs(sum(det(x,y) for x,y in zip(q,q[1:]+q[:1])))*.5
 return q if ar>1e-7 else []
def affine(Ti,q):
 x=X[Ti];a=np.linalg.solve(np.r_[x.T,[[1.,1.,1.]]],np.r_[q,1.])
 # Snapping tiny proportional values is numerical, not movement.
 a[np.abs(a)<1e-10]=0.
 return np.asarray([a[np.flatnonzero(Ti==v)[0]] if v in Ti else 0. for v in free]),sum(a[i]*Z[v] for i,v in enumerate(Ti) if v in fixed)
values=[];over=[];contradict=[];count_lambda=0
for i,j in combinations(range(len(T)),2):
 U,Y=T[i],T[j]
 ov=clip(X[U],X[Y])
 if not ov:continue
 inter=set(U)&set(Y);pair=[];constraints=[]
 for q in ov:
  a,c=affine(U,q);b,d=affine(Y,q)
  coeff=a-b;constant=float(c-d)
  # At actual shared boundary equality is topologically necessary.
  shared=False
  if len(inter)==1:shared=np.linalg.norm(q-X[list(inter)[0]])<1e-7
  if len(inter)==2:
   aa,bb=X[list(inter)];l=bb-aa;t=(q-aa)@l/(l@l)
   shared=-1e-8<t<1+1e-8 and abs(det(l,q-aa))/np.linalg.norm(l)<1e-7
  if shared:
   assert np.linalg.norm(coeff)<1e-8 and abs(constant)<1e-6
  pair.append({'xy_mm':q.tolist(),'constant_height_difference_mm':constant,'height_coefficients':coeff.tolist(),'shared_seam':bool(shared),
   'as_measured_original_difference_mm':float(constant+coeff@Z[free])})
  if not shared:
   constraints.append((coeff,constant))
 if not constraints:continue
 code=(i,j);n0=len(over);over.append({'face_rows':list(code),'triangles':[U.tolist(),Y.tolist()],'shared_topological_vertex_indices':sorted(inter),'polygon_points':pair})
 fixedpos=[q for q in pair if not q['shared_seam'] and np.max(np.abs(q['height_coefficients']))<1e-8 and q['constant_height_difference_mm']>=.000001]
 fixedneg=[q for q in pair if not q['shared_seam'] and np.max(np.abs(q['height_coefficients']))<1e-8 and q['constant_height_difference_mm']<=-.000001]
 if fixedpos and fixedneg:contradict.append({'face_rows':list(code),'positive_endpoint':fixedpos[0],'negative_endpoint':fixedneg[0]})
 for a,c in constraints:values.append((n0,a,c))
# One strict-order decision variable per planar overlap polygon. Fixed
# shared seam equality excluded only at the precise bounded shared vertex or segment.
m=len(over);margin=.03;big=1000.
Ab=[];yb=[]
for u,a,c in values:
 # either a*h+c >= margin (s=1) or <= -margin (s=0)
 f=np.zeros(3+m);f[:3]=a;f[3+u]=-big
 Ab.append(f);yb.append(-margin-c)
 f=np.zeros(3+m);f[:3]=-a;f[3+u]=big
 Ab.append(f);yb.append(big-margin+c)
lb=np.r_[np.zeros(3),np.zeros(m)]
ub=np.r_[np.full(3,140.),np.ones(m)]
res=milp(np.zeros(m+3),integrality=np.r_[np.zeros(3),np.ones(m)],bounds=Bounds(lb,ub),constraints=LinearConstraint(np.asarray(Ab),-np.inf,np.asarray(yb)),options={'time_limit':20.})
# Negatives check clipping + endpoint authority. Convex triangle test
# overlap must detect straddling at both fixed points; parted layers must not.
one=np.array([[0.,0.],[3.,0.],[0.,3.]])
two=np.array([[.50,.50],[1.90,.45],[.40,1.90]])
assert len(clip(one,two))>=3 and not clip(one,two+3)
for conflict in contradict:
 i,j=conflict['face_rows'];A=T[i];B=T[j]
 hp,hn=conflict['positive_endpoint'],conflict['negative_endpoint']
 for r0 in (hp,hn):
  q=np.array(r0['xy_mm'])
  phi=lambda t:np.linalg.solve(np.r_[X[t].T,[[1.,1.,1.]]],np.r_[q,1.])
  r0['fixed_source_support_A']=[int(v) for v,w in zip(A,phi(A)) if w>1e-8]
  r0['fixed_source_support_B']=[int(v) for v,w in zip(B,phi(B)) if w>1e-8]
  assert set(r0['fixed_source_support_A']+r0['fixed_source_support_B'])<=fixed
 u=hp['constant_height_difference_mm']/(hp['constant_height_difference_mm']-hn['constant_height_difference_mm'])
 z=np.array(hp['xy_mm'])*(1-u)+np.array(hn['xy_mm'])*u
 X0=np.linalg.solve(np.r_[X[A].T,[[1.,1.,1.]]],np.r_[z,1.])@V[A]
 X1=np.linalg.solve(np.r_[X[B].T,[[1.,1.,1.]]],np.r_[z,1.])@V[B]
 assert np.linalg.norm(X0-X1)<1e-9
 conflict['invariant_geometric_crossing_world_m']=X0.tolist()
if contradict:assert not res.success
out={'status':'STRICT_LAYER_FEASIBLE_NATIVE_REQUIRED' if res.success else 'HOLD_INCONSISTENT_FIXED_SECTOR_ORDER',
 'feasible':bool(res.success),'solver_status':int(res.status),'solver_message':res.message,
 'exact_preserved_shared_edges':8,'fixed_vertices':sorted(fixed),'free_wing_vertices':free,
 'minimum_nonshared_polygon_vertex_margin_mm':margin,'height_bound_mm':[0,140],
 'positive_area_overlap_polygons':m,'explicit_inequalities_count':len(Ab),'direct_fixed_endpoint_contradictions':contradict,'polygon_evidence':over,
 'native_authoring_attempted':False,'collision_clearance_claim':False}
if res.success:
 out['solved_free_heights_mm']=res.x[:3].tolist()
 out['solved_over_above_order']=np.rint(res.x[3:]).astype(int).tolist()
 arr=V.copy();arr[free]+=((res.x[:3]-Z[free])/1000.)[:,None]*n
 np.savez_compressed(p/'height_proposal.npz',open=arr,unchanged_faces=k['faces'],free_wing_indices=free)
(p/'result.json').write_text(json.dumps(out,indent=2,default=lambda v:v.item())+'\n')
print(json.dumps({a:x for a,x in out.items() if a not in ('polygon_evidence',)},indent=2,default=lambda v:v.item()))
