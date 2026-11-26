from pathlib import Path
import hashlib,sys,json
import numpy as np
P=Path(sys.argv[1]);O=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(P/'SHA256SUMS')=='1fbf8d5faeba4637979e97d6558dc719a61c897f17ad26a3156c23d7e6b2295f'
for l in (P/'SHA256SUMS').read_text().splitlines():
 h,n=l.split(maxsplit=1);assert sha(P/n)==h
b=P/'candidate'; f=b/'Fence18595V2.obj';lines=f.read_text().splitlines()
V=np.asarray([tuple(map(float,l.split()[1:])) for l in lines if l.startswith('v ')])
N=np.asarray([tuple(map(float,l.split()[1:])) for l in lines if l.startswith('vn ')])
F={};g='';vert_rows=[];norm_rows=[]
for i,l in enumerate(lines):
 a=l.split()
 if not a:continue
 if a[0]=='v':vert_rows.append(i)
 if a[0]=='vn':norm_rows.append(i)
 if a[0]=='usemtl':g=a[1];F[g]=[]
 if a[0]=='f':
  pairs=[tuple(int(p)-1 for p in t.split('//')) for t in a[1:]]
  assert all(x==y for x,y in pairs)
  F[g].append([x for x,y in pairs])
W=V.copy();D=N.copy();reports={}
for mat,peak,side in [('cream_hemp',4,1),('warm_hemp',12,-1)]:
 A=np.array(F[mat])
 for k in range(20):
  faces=A[k*128:(k+1)*128]; idx=faces.reshape(16,8,3)[:,::2,0]
  assert len(np.unique(V[idx].reshape(-1,3),axis=0))==64
  rings={tuple(V[v]):i for i,ring in enumerate(idx) for v in ring}
  assert all(tuple(V[i]) in rings for i in faces.ravel())
  amount={peak-1:.00105,peak:.0042,peak+1:.00105}
  indices=faces.ravel()
  dz=np.array([-side*amount.get(rings[tuple(V[i])],0) for i in indices])
  W[indices,2]+=dz
  before=V[faces];after=W[faces]
  norm=lambda t: np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0])
  n,m=norm(before),norm(after)
  assert np.all(np.einsum('ij,ij->i',n,m)>0)
  acc={};affected=set()
  for t,old_face,a in zip(faces,n,m):
   for row in t:
    key=tuple(W[row]);acc[key]=acc.get(key,np.zeros(3))+a
    if tuple(old_face)!=tuple(a):affected.add(key)
  for row in indices:
   key=tuple(W[row])
   if key in affected:D[row]=acc[key]/np.linalg.norm(acc[key])
  reports[mat+'-'+str(k)]={'changed_vertex_rows':int(sum(dz!=0)),'normal_min_before_after_dot':float(min(np.einsum('ij,ij->i',n,m)/np.linalg.norm(n,axis=1)/np.linalg.norm(m,axis=1)))}
changed=np.any(V!=W,axis=1);nchg=np.any(N!=D,axis=1)
assert np.array_equal(V[:,:2],W[:,:2])
assert np.array_equal(V.min(0),W.min(0)) and np.array_equal(V.max(0),W.max(0))
for i in np.flatnonzero(changed):lines[vert_rows[i]]='v %.9f %.9f %.9f'%tuple(W[i])
for i in np.flatnonzero(nchg):lines[norm_rows[i]]='vn %.9f %.9f %.9f'%tuple(D[i])
(O/'candidate').mkdir(exist_ok=True)
out=O/'candidate'/f.name
out.write_text('\n'.join(lines)+'\n')
mtl=(b/'Fence18595V2.mtl').read_bytes();(out.parent/'Fence18595V2.mtl').write_bytes(mtl)
print(json.dumps({'source':sha(f),'output':sha(out),'mtl_sha256':sha(out.parent/'Fence18595V2.mtl'),'changed_vertex_rows':int(sum(changed)),'changed_normal_rows':int(sum(nchg)),'individual':reports},indent=2))
