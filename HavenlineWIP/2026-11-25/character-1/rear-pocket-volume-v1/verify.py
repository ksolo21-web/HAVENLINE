import json,itertools,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import closest_point_on_tri
from pathlib import Path
P=Path(__file__).resolve().parent
A=np.load(P/'pocket-solids.npz')
def seg(a,b,c,d):
 u=b-a;v=d-c; w=a-c
 aa=u@u;bb=u@v;cc=v@v;dd=u@w;ee=v@w
 D=aa*cc-bb*bb
 vals=[]
 # all four constrained rectangle edges and the unconstrained interior stationary point
 for s in (0.,1.):
  t=np.clip((ee+s*bb)/max(cc,1e-30),0,1); vals.append(np.linalg.norm(w+s*u-t*v))
 for t in (0.,1.):
  s=np.clip((t*bb-dd)/max(aa,1e-30),0,1); vals.append(np.linalg.norm(w+s*u-t*v))
 if D>1e-30:
  s=(bb*ee-cc*dd)/D;t=(aa*ee-bb*dd)/D
  if 0<s<1 and 0<t<1:vals.append(np.linalg.norm(w+s*u-t*v))
 return min(vals)
def dist(A,B):
 a=[Vector(x) for x in A];b=[Vector(x) for x in B]
 values=[(x-closest_point_on_tri(x,*b)).length for x in a]+[(x-closest_point_on_tri(x,*a)).length for x in b]
 values.extend(seg(A[i],A[(i+1)%3],B[j],B[(j+1)%3]) for i in range(3) for j in range(3))
 return min(values)
# Full meshes are BVH tested; distance explicitly covers all geometrically
# plausible close pairs between whole independent surfaces, and new named
# patch faces vs entire retained basemesh excluding shared vertices.
def margin(PA,PB,iA=None,iB=None):
 lo=PB.min(1);hi=PB.max(1);best=.006;pair=None;cc=0
 for i,X in enumerate(PA):
  hu=X.max(0);lu=X.min(0)
  m=np.where(np.all(hi>=lu-best,axis=1)&np.all(lo<=hu+best,axis=1))[0]
  for j in m:
   if iA is not None and np.isin(iA[i],iB[j]).any():continue
   di=dist(X,PB[j]);cc+=1
   if di<best:best=di;pair=[i,int(j)]
 return {'minimum_or_lower_bound_mm':best*1000,'number_exact_pairs':cc,'observed_pair':pair}
names=('shin','thigh','roll','retained')
meshes={k:np.asarray(A[k+'_tri'] if k!='retained' else A['shell_tri'],int) for k in names}
# Closed volumes under each exact forward sweep, no thin surfaces.
def check_closed(T):
 e=T[:,((0,1),(1,2),(2,0))].reshape(-1,2); raw=np.sort(e,axis=1)
 _,i,c=np.unique(raw,axis=0,return_inverse=True,return_counts=True)
 sign=np.bincount(i,weights=np.where(e[:,0]>e[:,1],1,-1),minlength=len(c))
 return bool(np.all(c==2)&np.all(sign==0))
assert all(check_closed(meshes[n]) for n in names[:-1])
def bvh(v,T):return BVHTree.FromPolygons(v.tolist(),T.tolist(),all_triangles=True,epsilon=0.)
def contain(p,b):
 # Whole-closed-solid containment double direction. Ambiguous parity does
 # not certify positive gap; a positive crossing remains a hard fail.
 votes=[]
 for q in ((.278,.193,.939),(.471,.682,.557),(.139,.972,.188)):
  d=Vector(q).normalized();pt=Vector(p);hits=0
  for i in range(100):
   x,n,j,w=b.ray_cast(pt,d,2.)
   if x is None:break
   hits+=1;pt=x+d*1e-8
  votes.append(hits%2==1)
 return votes
ET=np.unique(np.sort(meshes['retained'][:,((0,1),(1,2),(2,0))].reshape(-1,2),axis=1),axis=0)
def extent_test(X,points):
 e=X[ET];lo=e[:,:,2].min(1);hi=e[:,:,2].max(1)
 greatest=0.;find=None
 for i,p in enumerate(points):
  z=p[2];q=e[(lo<=z)&(hi>=z)&(hi>lo)]
  if not len(q):return 1e6,i
  a=(z-q[:,0,2])/(q[:,1,2]-q[:,0,2]);yy=q[:,0,:2]+a[:,None]*(q[:,1,:2]-q[:,0,:2])
  b=max(0.,float(np.max(p[:2]-yy.max(0))),float(np.max(yy.min(0)-p[:2])))
  if b>greatest:find=i;greatest=b
 return greatest*1e3,find
out=[]
for k in range(len(A['shin'])):
 V={n:A[n][k] for n in names}
 B={n:bvh(V[n],meshes[n]) for n in names}
 sum0={}
 for n in names[:-1]:
  F=V[n][meshes[n]]
  sum0[n+'_min_double_area_m2']=float(np.linalg.norm(np.cross(F[:,1]-F[:,0],F[:,2]-F[:,0]),axis=1).min())
  vol=float(np.einsum('ni,ni->n',F[:,0],np.cross(F[:,1],F[:,2])).sum()/6)
  sum0[n+'_invalid_nonpositive_volume']=vol<=0
  sum0[n]=(vol*1e9)
  nt=meshes[n]
  res=[(i,j) for i,j in B[n].overlap(B[n]) if i<j and not np.isin(nt[i],nt[j]).any()]
  sum0[n+'_nonadjacent_self']=len(res)
 pairs={}
 for q,p in itertools.combinations(names,2):
  ints=B[q].overlap(B[p]);pair_key=q+'/'+p
  r={'cross':len(ints),'first_exact_triangle_pair':list(ints[0]) if ints else None,'whole_feature_distance_mm':None}
  if ints:r['whole_feature_distance_mm']=0.
  else:
   if p!='retained':
    vv=contain(V[q][0],B[p]);ww=contain(V[p][0],B[q])
    r['closed_containment_votes']=vv+ww
    if any(vv+ww):r['whole_feature_distance_mm']=0.
   if r['whole_feature_distance_mm'] is None and k in (0,16):
    d=margin(V[q][meshes[q]],V[p][meshes[p]])
    r['whole_feature_distance_mm']=float(d['minimum_or_lower_bound_mm'])
    r['dist_exact_features_checked']=d['number_exact_pairs']
  pairs[pair_key]=r
 z=np.concatenate([V[n] for n in names[:-1]])
 ex,where=extent_test(V['retained'],z)
 out.append({'normalized_lambda':k/16,'signed_volumes_mm3':sum0,'pair_checks':pairs,'extent_excess_mm':ex,'extent_excess_vertex':where})
 print(k,{p:(z['cross'],z['whole_feature_distance_mm']) for p,z in pairs.items()},'delta ext',ex,flush=True)
(P/'volume-qa.json').write_text(json.dumps(out,indent=2,default=lambda x:x.item()))
