import os
import numpy as np,json,hashlib
from pathlib import Path
from scipy.spatial.transform import Rotation,Slerp
P=Path(__file__).resolve().parent
A=Path(os.environ['C1_APPROVED_REAR_DATA']); B=(Path(os.environ['C1_KNEE_DATA'])/'poses.npz')
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert h(A/'SHA256SUMS')=='1a64d744fc99d4b3cc1af7e7e4d790aa1611fc0b9b929f1659c7c33c5a348e30'
assert h(B)=='c16ef2874698851d6a237e14779166f2346ca3d89f4e520738252769664d2ef5'
d=np.load(A/'new-rear-panel.npz');m=np.load(B)
v=d['v']; T=d['tri'];W=d['w'];UV=d['u']; newix=d['region']; spine=np.asarray(json.loads((A/'build.json').read_text())['outline_carrier_edges']).ravel()
S=float(m['scale']); O=m['source_origin']
lo,hi=.411,.463
region=np.zeros(len(T),bool);region[newix]=True
# Do not split fixed stitched outer edges: leave faces containing such
# edges as continuous old leather/cloth and use only interior structural panel.
boundary=set(d['boundary'].tolist())|set(spine.tolist())
cut=region & np.array([sum(j in boundary for j in t)<2 for t in T])
assert cut.any()
# Use graph on edges; clipping only if both incident faces in selected patch
# so no T-junction opens retained cloth at panel outskirts. Manual corridor
# split band excludes faces crossing a hard boundary edge.
allref=T[cut]
E=np.sort(allref[:,((0,1),(1,2),(2,0))].reshape(-1,2),axis=1)
uu,ct=np.unique(E,axis=0,return_counts=True)
critical=set(map(tuple,uu[ct==1].tolist()))
for z in (lo,hi):
 for aa,bb in list(critical):
  if (v[aa,2]-z)*(v[bb,2]-z)<0:
   # We cannot not split outside connected source; record conditional
   # contour need instead of introducing T-junction.
   pass
# Permit exact same-material splits on either side of a selected interface,
# making a single shared vertex for each edge/band. All outside child
# triangles reconstructed from same original plane and carry original geometry.
V=v.tolist(); weights=W.tolist(); pool={}; split=[]
def crossing(a,b,t):
 # Represent a vertex by exact source triangle barycentric terms.
 x=(t-a[2])/(b[2]-a[2]); return a+x*(b-a)
# first find explicit seam split coordinates on every measured corridor edge
for f in T[cut]:
 for aa,bb in zip(f,np.roll(f,-1)):
  i,j=sorted((int(aa),int(bb)))
  for zz in (lo,hi):
   if (v[i,2]-zz)*(v[j,2]-zz)<0:
    k=(i,j,zz)
    if k in pool:continue
    t=(zz-v[i,2])/(v[j,2]-v[i,2]);X=v[i]+t*(v[j]-v[i])
    pool[k]=len(V);V.append(X.tolist());weights.append(((1-t)*W[i]+t*W[j]).tolist());split.append([i,j,zz,pool[k]])
assert len(pool)
# Plane clipping into measured bands in barycentric coordinates with shared cut vertices.
def polyclip(p,xyz,z,sgn):
 q=[]
 for i,P in enumerate(p):
  Q=p[(i+1)%len(p)];a=(P@xyz[:,2]-z)*sgn;b=(Q@xyz[:,2]-z)*sgn
  if a>=-1.e-10:q.append(P)
  if a*b<-1.e-20:q.append(P+a/(a-b)*(Q-P))
 return q
keys={tuple(sorted((i,j))) for i,j,z,k in split}
faces=[]; uv=[]; prov=[]; layers=[]
for i,t in enumerate(T):
 f=v[t]; overlaps=any(tuple(sorted((int(a),int(b)))) in keys for a,b in zip(t,np.roll(t,-1)))
 if not overlaps:
  faces.append(t);uv.append(UV[i]);prov.append(i);layers.append(('shin' if f[:,2].mean()<lo else ('thigh' if f[:,2].mean()>hi else 'gusset')) if cut[i] else 'original')
  continue
 if cut[i]:
  points=[]
  for l,bb in [('shin',[(lo,-1)]),('gusset',[(lo,1),(hi,-1)]),('thigh',[(hi,1)])]:
   q=list(np.eye(3))
   for z,sgn in bb:q=polyclip(q,f,z,sgn) if q else []
   if len(q)>=3:points.append((l,q))
 else:
  # Shared seam transition triangles: surface/UV retained exactly; only add
  # legal subdivisions where corresponding edge actually split. No posing edits.
  q=[]
  for k in range(3):
   a0,b0=sorted((int(t[k]),int(t[(k+1)%3])))
   q.append(np.eye(3)[k]);tmp=[]
   for z in (lo,hi):
    if (a0,b0,z) in pool:
     x=(z-f[k,2])/(f[(k+1)%3,2]-f[k,2]);tmp.append((x,(1-x)*np.eye(3)[k]+x*np.eye(3)[(k+1)%3]))
   q.extend([a for x,a in sorted(tmp,key=lambda t:t[0])])
  points=[('unchanged sewing transition',q)]
 for l,q in points:
  # Clip outside face can have seam points on only subset edges, fan uses
  # one new exact source barycentric central knot to avoid degenerate ears.
  ids=[]
  for u in q:
   k=np.flatnonzero(u>1e-8)
   if len(k)==1:ids.append(int(t[k[0]]));continue
   assert len(k)==2
   a0,b0=sorted(t[k].tolist()); z=min((lo,hi),key=lambda g:abs(g-u@f[:,2]))
   assert (a0,b0,z) in pool
   ids.append(pool[(a0,b0,z)])
  if len(set(ids))<3:continue
  if len(ids)>3:
   u=np.mean(q,axis=0);ni=len(V);V.append((u@f).tolist());weights.append((u@W[t]).tolist())
   for j in range(len(q)):
    k=(j+1)%len(q)
    faces.append([ids[j],ids[k],ni]);uv.append(np.array([q[j],q[k],u])@UV[i]);prov.append(i);layers.append(l)
  else:
   faces.append(ids);uv.append(np.array(q)@UV[i]);prov.append(i);layers.append(l)
x=np.array(V);w=np.array(weights);ff=np.array(faces);u=np.array(uv)
def topo(t):
 e=t[:,((0,1),(1,2),(2,0))].reshape(-1,2);f=np.sort(e,axis=1)
 _,ii,ct=np.unique(f,axis=0,return_inverse=True,return_counts=True)
 dr=np.bincount(ii,np.where(e[:,1]>e[:,0],1,-1),minlength=len(ct))
 return (int(sum(ct==1)),int(sum(ct>2)),int(sum((ct==2)&(dr!=0))))
assert topo(ff)==topo(T)==(162,0,0),topo(ff)
defs=np.array(layers)
active=np.isin(defs,['shin','gusset','thigh'])
vsel=np.unique(ff[active])
lids={k:np.flatnonzero(defs==k) for k in ('shin','gusset','thigh','unchanged sewing transition')}
# Read-only preliminary 0ms physical design and native full witness as
# different steps. Preserve exact hard seam and neighbor vertices.
M=m['bones'][0,1]; a=np.einsum('ni,ijk->njk',w,M)
def bind(y):
 q=y/S+O; return (np.einsum('nij,nj->ni',a[:,:3,:3],q)+a[:,:3,3]-O)*S
def trans(z,mat):
 q=z/S+O
 return (q@mat[:3,:3].T+mat[:3,3]-O)*S
current=bind(x)
g=x[vsel]
wv=np.linspace(0,1,3); xx=np.clip((g[:,2]-lo)/(hi-lo),0,1)
# Rolling/sliding section: map both independent attachment endpoints in
# measured geometry, then ruled bridge with neutral embedding retained.
lower=g.copy();upper=g.copy();lower[:,2]=lo;upper[:,2]=hi
Q0=trans(lower,M[1]);Q1=trans(upper,M[0])
midrot=Slerp([0,1],Rotation.from_matrix(M[[1,0],:3,:3]))(xx).as_matrix()
rx=Q1-Q0
mid=Q0+(Q1-Q0)*xx[:,None]
ret=np.zeros_like(g)
fn=g[:,2]<lo;up=g[:,2]>hi;cen=~fn&~up
ret[fn]=trans(g[fn],M[1]);ret[up]=trans(g[up],M[0])
# Interior fold smoothly bows inward only by loaded seam compression,
# no baseline parameter fit. Shared endpoints meet exactly.
loss=np.maximum(0.,hi-lo-np.linalg.norm(rx,axis=1))
inward=np.einsum('nij,j->ni',midrot,np.array([0.,-1.,0.]))
ret[cen]=mid[cen]+inward[cen]*np.sin(np.pi*xx[cen])[:,None]*(loss[cen]*.25)[:,None]
n=lambda p:np.linalg.norm(p,axis=-1)
# Zero toward the sewn outer exact rim, exact outline carriers, and all
# untouched triangles not in the authored three-section insert.
protected=set(ff[~active].ravel().tolist())|boundary
select=np.array([i not in protected for i in vsel])
g0=g[:,[0,2]]
if len(d['boundary']):
 p=v[d['boundary']][:,[0,2]]
 u=(p[None]-g0[:,None]);dist=np.min(np.linalg.norm(u,axis=2),axis=1)
else:dist=np.zeros(len(g))
alpha=np.clip(dist/.014,0,1);alpha=alpha*alpha*(3-2*alpha);alpha*=select
Y=current.copy(); delta=(ret-current[vsel])*alpha[:,None];Y[vsel]+=delta
stockW=np.linalg.solve(a[vsel,:3,:3],(delta/S)[...,None]).squeeze(-1)
dv=np.zeros_like(x);dv[vsel]=stockW
assert np.max(n(bind(x+dv*S)-Y))<1e-10
r={'main_rest_topology':topo(ff),'old_rest_topology':topo(T),'authored_layers':{k:len(v) for k,v in lids.items()},'new_shared_seam_vertices':len(pool),'held_pose_candidate_vertices':int(sum(alpha>1e-9)), 'original_vertices_at_rest_exact':bool(np.array_equal(x[:len(v)],v)), 'min_attachment_interlayer_chord_mm':float(np.min(n(rx[cen]))*1000),'max_mechanical_inswing_delta_mm':float(n(delta).max()*1000)}
(P/'design.json').write_text(json.dumps(r,indent=2));print(r)
np.savez_compressed(P/'gusset.npz',v=x,tri=ff,uv=np.array(uv),w=w,labels=defs,scope=active,src_face=prov,native0=Y,delta=dv,trim0=np.array(0))
