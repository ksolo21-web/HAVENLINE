from pathlib import Path
import sys,hashlib,json
from collections import Counter,defaultdict
import numpy as np
dst=Path(__file__).resolve().parent
src,crit,proof=map(Path,sys.argv[1:4])
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(proof/'SHA256SUMS')=='bc25a6d1323e50ae480cf1690318e39411dbd64ca4d37bd889b6e643ac791911'
assert sha(src/'SHA256SUMS')=='66a34c258ae60d534de8569e80466055826988b7ee20291ea45d6bd1c7ce1e12'
assert sha(crit/'SHA256SUMS')=='65aa400c4e8639953f29b3607ed51a40ed08312cefa50f3812165a98b5a4f3f0'
for node in (proof,crit,src):
 for l in (node/'SHA256SUMS').read_text().splitlines():
  h,n=l.split(maxsplit=1);assert sha(node/n)==h
Q=json.loads((proof/'result.json').read_text())['post_group_conservative_bounds_m']
witness=json.loads((crit/'result.json').read_text())['results']
margin=.002
orange=(min(v['post_minus_hinge_height_m'] for v in witness.values())+Q['orange']['height_unseated_bounds'][0],max(v['post_minus_hinge_height_m'] for v in witness.values())+Q['orange']['height_unseated_bounds'][1])
Ylo,Yhi=orange[0]-.0025,orange[1]+.0025
X=.191;Xout=.229
def read(p,s):
 v=[];xs={}
 for l in p.read_text().splitlines():
  a=l.split()
  if a[0]=='v':v.append(np.array(tuple(map(float,a[1:])))*[s,1,1])
  if a[0]=='g':g=a[1];xs[g]=dict(f=[],mat=None)
  if a[0]=='usemtl':xs[g]['mat']=a[1]
  if a[0]=='f':xs[g]['f'].append(np.array([v[int(t)-1] for t in a[1:]]))
 return xs
def split(poly,axis,bound):
 vals=poly[:,axis]-bound; eps=1e-10
 if vals.min()>=-eps or vals.max()<=eps: return [poly]
 sides=[[],[]]
 for a,b,da,db in zip(poly,np.roll(poly,-1,axis=0),vals,np.roll(vals,-1)):
  if da<=eps:sides[0].append(a.copy())
  if da>=-eps:sides[1].append(a.copy())
  if da*db<0 and min(abs(da),abs(db))>eps:
   v=a+(b-a)*(da/(da-db));v[axis]=bound
   for s in sides:s.append(v.copy())
 return [np.array(a) for a in sides if len(a)>=3]
def sub(t,cuts):
 c=[t]
 for a,u in cuts:c=[q for p in c for q in split(p,a,u)]
 return c
def limits(y):
 # Timber fits at original full scale beyond local foot; shape only the exposed rear.
 h=np.clip(np.minimum((y-(Ylo-.018))/.018,((Yhi+.018)-y)/.018),0,1)
 return -.0205+.01455*h
def transform(poly,name):
 if not name.startswith('inward_') and name not in {'carved_board_1','continuous_snow_crown'}:return [poly]
 if name=='inward_tip_stile' or name=='inward_latch_housing':return [poly]
 if name.startswith(('inward_hinge_strap','inward_strap_pin','inward_hinge_rope')):
  return [poly+np.array([.158,0,.018])]
 if poly[:,0].min() >= Xout-1e-10 or poly[:,2].min()>=-1e-10:return [poly]
 # Partition original faces so all protected bands can be proven over full triangles.
 parts=sub(poly,[(0,X),(0,Xout),(1,Ylo-.018),(1,Ylo),(1,Yhi),(1,Yhi+.018),(2,0.)])
 ret=[]
 for p in parts:
  q=p.copy();u,y,z=p.T;k=np.clip((Xout-u)/(Xout-X),0,1);limit=limits(y)
  if name.startswith('inward_'):
   # Load-bearing timber flange: seat through opposing face, not a crushed back slab.
   near=limit+(z+.057)*(.027-limit)/.032
  else:
   floor=-.030 if name=='carved_board_1' else -.063
   near=z*limit/floor
  q[:,2]=np.where(z<0,z+(near-z)*k,z);ret.append(q)
 return ret
def support(side):
 # Real closed bevel-edged back saddle at first two timbers. Shallow bronze binding
 # extends underneath relocated rope at z≈-49mm while front key seats into board.
 ylo,yhi=.358,.419;u0,u1=.178,.292;b=.006
 ring=np.array([[u0+b,ylo],[u1-b,ylo],[u1,ylo+b],[u1,yhi-b],[u1-b,yhi],[u0+b,yhi],[u0,yhi-b],[u0,ylo+b]])
 a=np.c_[ring,np.full(8,-.0455)];b=np.c_[ring,np.full(8,-.018)]
 ps=[a[::-1],b]+[np.array([a[i],a[(i+1)%8],b[(i+1)%8],b[i]]) for i in range(8)]
 return ps if side==1 else [f[::-1] for f in ps]
# For exact unchanged source (some source faces are planar N-gons) use fan only after
# global split lines. These cuts must refine all faces in every modified component,
# including faces whose positions are unchanged, to maintain closed topology.
def tris(poly):
 for i in range(1,len(poly)-1):
  t=poly[[0,i,i+1]]
  if np.linalg.norm(np.cross(t[1]-t[0],t[2]-t[0]))>1e-12:yield t
def tri_closed(p):
 if len(p)==3:
  yield p
 else:
  c=np.mean(p,axis=0)
  for k in range(len(p)):
   t=np.array([c,p[k],p[(k+1)%len(p)]])
   if np.linalg.norm(np.cross(t[1]-t[0],t[2]-t[0]))>1e-12:yield t
def close(q):
 def key(v):return tuple(np.round(v,7))
 n=Counter(); d=Counter()
 for t in q:
  k=list(map(key,t))
  for i in range(3):
   a,b=k[i],k[(i+1)%3];ab=tuple(sorted((a,b)));n[ab]+=1;d[ab]+=1 if a<b else -1
 return int(sum(c!=2 or d[e]!=0 for e,c in n.items()))
stats={}
for side,n in [(1,'GateLeaf.obj'),(-1,'GateLeaf_Right.obj')]:
 groups=read(src/'donor'/n,side); smooth=[]
 for name,item in groups.items():
  data=item['f']
  item['source']=list(t for p in data for t in tris(p))
  influence=(name.startswith('inward_') and not name.startswith(('inward_tip_stile','inward_latch_housing','inward_hinge_strap','inward_strap_pin','inward_hinge_rope'))) or name in {'carved_board_1','continuous_snow_crown'}
  if influence:
   # Unconditional cuts on each affected solid prevent T joints at matching edges.
   cuts=[(0,X),(0,Xout),(1,Ylo-.018),(1,Ylo),(1,Yhi),(1,Yhi+.018),(2,0.)]
   data=[c for p in data for t in tris(p) for c in sub(t,cuts)]
  item['t']=list(t for p in data for q in transform(p,name) for t in (tri_closed(q) if influence else tris(q)))
 groups['rear_beveled_wood_saddle']={'mat':'beam','source':[],'t':[t for p in support(side) for t in tris(p)]}
 # Preserve actual mirrored input topology and source group/material IDs. 
 lines=['# Detached exact-custody rabbet study, not installed','mtllib GateLeaf.mtl','o GateLeaf_Detached_Rabbet']
 s=[]
 for name,item in groups.items():
  T=np.asarray(item['t']);A=np.asarray(item['source'])
  assert T.size and min(np.linalg.norm(np.cross(T[:,1]-T[:,0],T[:,2]-T[:,0]),axis=1))>1e-12
  q=np.round(T,7);w=close(q)
  s.append(dict(group=name,changed=bool(A.shape!=T.shape or np.any(A!=T)),triangle_count=len(T),original_triangle_count=len(A),nonmanifold_or_same_direction=w))
  smooth.append((name,item,q))
 for name,item,T in smooth:
  lines+=['g '+name,'usemtl '+item['mat']]
  # Reuse welded indexes within each component.
  row={}
  for t in T*np.array([side,1,1]):
   ids=[]
   for p in t:
    k=tuple(p)
    if k not in row:
     lines.append('v %.7f %.7f %.7f'%k);row[k]=sum(1 for l in lines if l.startswith('v '))
    ids.append(row[k])
   lines.append('f %d %d %d'%tuple(ids))
 (dst/'donor').mkdir(exist_ok=True)
 (dst/'donor'/n).write_text('\n'.join(lines)+'\n')
 stats[n]=s
(dst/'donor'/'GateLeaf.mtl').write_bytes((src/'donor'/'GateLeaf.mtl').read_bytes())
print(json.dumps(dict(post_y_orange=orange,margin=margin,groups=stats,donors={n:sha(dst/'donor'/n) for n in [*stats,'GateLeaf.mtl']}),indent=2))
