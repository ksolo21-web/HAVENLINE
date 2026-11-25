import os
from pathlib import Path
import numpy as np, hashlib,json,itertools
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parent
B=Path(os.environ['C1_REAR_POCKET_DATA'])
H=Path(os.environ['C1_APPROVED_REAR_DATA'])
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert h(B/'pocket-solids.npz')=='9e5aa05dcd139dcfecad78ef790af5b8d612067137cf43ee87612a75b74f9038'
assert h(H/'new-rear-panel.npz')=='023ed33af9ac04e8c6223fb6abfd2f2002d3b3b8a06c00b50dba0b581ad389bf'
a=np.load(H/'new-rear-panel.npz'); v,t,reg,w=(a[k] for k in ('v','tri','region','w'))
a0=np.load(B/'pocket-solids.npz')
stock=a0['retained']
# Analyze inherited crossings against original IDs before cutting, using exact held/rest inputs.
def tree(v,t):return BVHTree.FromPolygons(v.tolist(),t.tolist(),all_triangles=True,epsilon=0)
oparts={n:(a0[n],a0[n+'_tri']) for n in ('shin','thigh','roll')}
# Strict authorized rectangle, never remove an unapproved face.
xmin,xmax,zmin,zmax=-.151,-.089,.402,.425
lims=((0,xmin,True),(0,xmax,False),(2,zmin,True),(2,zmax,False))
def split(arr,axis,val,positive):
 # rows barycentric XYZ with coordinate projected from original rest face
 poly=[]; out=[]
 for A,C in zip(arr,np.roll(arr,-1,axis=0)):
  aa=(A[axis]-val)*(1 if positive else -1); cc=(C[axis]-val)*(1 if positive else -1)
  (poly if aa>=-1e-11 else out).append(A)
  if aa*cc<0 and abs(aa)>1e-11 and abs(cc)>1e-11:
   z=A+(C-A)*aa/(aa-cc);poly.append(z);out.append(z)
 return np.array(poly),np.array(out)
def fans(x):
 if len(x)<3:return []
 return [np.array([x[0],x[i],x[i+1]]) for i in range(1,len(x)-1) if np.linalg.norm(np.cross(x[i,:3]-x[0,:3],x[i+1,:3]-x[0,:3]))>1e-13]
pieces=[]; freed=[]; scope=set()
protected=set(map(int,a['boundary']))
for n in reg:
 X=np.c_[v[t[n]],np.eye(3)]; left=X.copy(); retain=[]
 for rule in lims:
  if len(left)<3:break
  left,other=split(left,*rule);retain+=fans(other)
 cut=fans(left)
 if not cut:continue
 assert not any((xmin+1e-8<v[j,0]<xmax-1e-8 and zmin+1e-8<v[j,2]<zmax-1e-8) for j in t[n] if j in protected)
 scope.add(int(n));pieces.extend((int(n),p) for p in retain);freed.extend((int(n),p) for p in cut)
keep=np.array([n for n in range(len(t)) if n not in scope])
st=np.array([n for n,p in pieces]); sb=np.array([p[:,3:] for n,p in pieces])
def retained(q):
 nv=np.einsum('nij,njk->nik',sb,stock[q][t[st]]).reshape(-1,3)
 return np.r_[stock[q],nv],np.r_[t[keep], np.arange(len(nv)).reshape(-1,3)+len(v)]
# Explicit material mapping for authored candidate with distinct rail positions at the measured entry and pocket.
# Boundary correspondences inherited from source triangles, not arbitrary y offsets.
rv=v[t[reg]]; A=rv[:,0][:,[0,2]]; u=(rv[:,1]-rv[:,0])[:,[0,2]]; d=(rv[:,2]-rv[:,0])[:,[0,2]]
def src(x,z):
 e=np.array([x,z])-A
 det=u[:,0]*d[:,1]-u[:,1]*d[:,0]
 with np.errstate(divide='ignore',invalid='ignore'):
  c=(e[:,0]*d[:,1]-e[:,1]*d[:,0])/det
  b=(u[:,0]*e[:,1]-u[:,1]*e[:,0])/det
 Q=np.c_[1-c-b,c,b]; j=np.nanargmax(np.nan_to_num(Q.min(1),nan=-1e9));assert Q[j].min()>-1e-7,(x,z)
 return int(reg[j]),Q[j],Q[j]@rv[j]
xs=np.linspace(xmin+.0015,xmax-.0015,7)
rows={'entry':(.402,.4045,.407),'pocket':(.420,.4225,.425)}
maps={tag:[[src(x,z) for x in xs] for z in zz] for tag,zz in rows.items()}
# Extract fixed transport at all original sweep states and no skin edits.
# Neighboring mapping represents retained rail motion; station and UV fixed.
def rail(tag,q):
 return np.array([[b@stock[q][t[n]] for n,b,_ in line] for line in maps[tag]])
def slab(top,bot):
 ny,nx=top.shape[:2];s=ny*nx;F=[]
 for j in range(ny-1):
  for i in range(nx-1):
   a=j*nx+i;b=a+1;c=b+nx;d=c-1
   F += [(a,b,c),(a,c,d),(a+s,c+s,b+s),(a+s,d+s,c+s)]
 r=list(range(nx))+[j*nx+nx-1 for j in range(1,ny)]+[(ny-1)*nx+i for i in range(nx-2,-1,-1)]+[j*nx for j in range(ny-2,0,-1)]
 for i,j in zip(r,r[1:]+r[:1]): F += [(j,i,i+s),(j,i+s,j+s)]
 return np.r_[top.reshape(-1,3),bot.reshape(-1,3)],np.array(F)[:,[0,2,1]]
# True thickness; no promise of finished exterior. Hold inner rail geometry separate from outer skin.
def new_parts(q):
 E=rail('entry',q);K=rail('pocket',q)
 inward=np.array([0.,-1.,0.]); sun=.0008;th=.00055
 parts={n:slab(g+sun*inward,g+(sun+th)*inward) for n,g in [('entry-liner',E),('pocket-liner',K)]}
 # Chord between inner attachment lines with rolling relief. Ends separated
 # physically from backing panels; held sewing carrier must be independently valid.
 tt=np.linspace(.025,.975,17)[:,None,None]
 center=(1-tt)*E[-1]+tt*K[0]
 top=center+inward*(sun+.0014*np.sin(np.pi*tt))
 parts['rolled-return']=slab(top,top+.00050*inward)
 return parts
def obj(file,q,parts):
 off=1
 with file.open('w') as f:
  FF=[('replacement-hole-retained',retained(q))]+[(tag,value) for tag,value in parts.items()]
  for name,(X,T) in FF:
   f.write('o '+name+'\n')
   for p in X:f.write('v '+' '.join('%.10f'%c for c in p)+'\n')
   for face in T:f.write('f '+' '.join(str(i+off) for i in face)+'\n')
   off+=len(X)
def vol(V,T):
 F=V[T];return float(np.einsum('ni,ni->n',F[:,0],np.cross(F[:,1],F[:,2])).sum()/6*1e9)
def sewing_edge(x):
 out=[]
 for q in (0,16):
  y=x(q)
  out.append([float(np.min(np.linalg.norm(y[0]-y[1],axis=-1)))*1000, float(np.max(np.linalg.norm(y[0]-y[1],axis=-1)))*1000])
 return out
R=[]
for q in range(17):
 x,T=retained(q); s=tree(x,T); rtree=tree(stock[q],t)
 parent=np.r_[keep,st]
 inherited={}
 if q in (0,16):
  for n,(U,tt) in oparts.items():
   o=tree(U[q],tt); orig=o.overlap(rtree); rem=o.overlap(s)
   inherited[n]={'original_total':len(orig),'original_on_untouched_faces':sum(j not in scope for i,j in orig),'original_touched_faces':sorted({j for i,j in orig if j in scope}),'surviving':len(rem),'surviving_pairs_full_source_ids':[[int(i),int(parent[j])] for i,j in rem]}
 pp=new_parts(q);bb={n:tree(*g) for n,g in pp.items()}
 record=dict(q=q,inherited=inherited, liner={})
 for n,b in bb.items():
  hits=b.overlap(s)
  U,tt=pp[n];selfpair=[(i,j) for i,j in b.overlap(b) if i<j and not np.isin(tt[i],tt[j]).any()]
  record['liner'][n]={'signed_mm3':vol(U,tt),'retained_pairs':len(hits),'protected_source_faces':sorted({int(parent[j]) for i,j in hits if parent[j] not in scope}),'cut_neighbour_source_faces':sorted({int(parent[j]) for i,j in hits if parent[j] in scope}),'self':len(selfpair)}
 record['interpart']={a+'/'+b:len(bb[a].overlap(bb[b])) for a,b in itertools.combinations(bb,2)}
 R.append(record)
 if q in (0,16):obj(P/('proof-neutral.obj' if q==0 else 'proof-held.obj'),q,pp)
 print(q,[(k,v['retained_pairs'],round(v['signed_mm3'],2)) for k,v in record['liner'].items()],record['interpart'],flush=True)
# Topological sewing proof is prerequisite for any positive clearance assertion.
rr=[(n,[{'face':j,'bary':b.tolist(),'xyz':p.tolist()}for row in rs for j,b,p in row])for n,rs in maps.items()]
(P/'measurements.json').write_text(json.dumps({'bounds_m':[[xmin,xmax],[zmin,zmax]],'partition_source_face_ids':sorted(scope),'kept_remainder_triangles':len(pieces),'actual_removed_triangles':len(freed),'unchanged_source_faces':len(keep),'rail_source':dict(rr),'frames':R,'negative_only':'Open seam gap and triangle crossings rule out certification; no interval clearance claim.'},indent=2))
