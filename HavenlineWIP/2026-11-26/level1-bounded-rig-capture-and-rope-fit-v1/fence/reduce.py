from pathlib import Path
from collections import Counter
import hashlib,json,numpy as np
R=Path(__file__).resolve().parent;P=R.parent
S=P/'hvn-l1-fence-33036-seated-weave-proof-v1'
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
assert sha(S/'SHA256SUMS')=='e75b705341392fa8403fa6d29f847137c55027b4fe57a1c2d97aa293d6e5494e'
for a in (S/'SHA256SUMS').read_text().splitlines():
 h,n=a.split(maxsplit=1);assert sha(S/n)==h
V=P/'hvn-l1-fence-33036-full-perimeter-repair-bound-v1/verify.py'
NP=P/'hvn-l1-fence-33036-explicit-import-probe-v1/private-uncompressed-iTjqXRVx/ExplicitSourceBasis.npz'
assert sha(V)=='563eede4d8a21ef48ab39cee109a8a0f83f18f5f1b3ef443cb3fd17d76f81989'
assert sha(NP)=='e666ea5a9b6566a3ba168d3a2c3274dcbf6b2c44133cbe8f2f613843be452c5f'
# Copy the validated collision helpers only; never rerun parent builder or write into it.
z=(S/'build.py').read_text()
pre={'np':np,'P':P}
from scipy.spatial import cKDTree
pre['cKDTree']=cKDTree
exec(z[z.index("verify=P/'hvn-l1"):z.index("res={'rope_vertices'")],pre)
pairs=pre['pairs']; verts=[]; g={}; name=None
for l in (S/'LocallySeatedWeave_SourceOnly.obj').read_text().splitlines():
 if l.startswith('v '):verts.append(list(map(float,l.split()[1:])))
 if l.startswith('o '):name=l[2:];g[name]=[]
 if l.startswith('f '):g[name].append([int(s)-1 for s in l.split()[1:]])
v=np.array(verts); N=500;K=12; A=v[:6000].reshape(N,K,3);A=np.r_[A,A[:1]]
pins=[0,100,104,105,250,350,354,355,500]
def error(a,b):
 k=np.arange(a,b+1)
 u=(k-a)/(b-a)
 B=(1-u[:,None,None])*A[a]+u[:,None,None]*A[b]
 d=np.linalg.norm(A[k]-B,axis=2).max()
 # Max bilinear-strip vs edge-diagonal interpolation error bounded by 1/4
 # mixed finite edge differences. Add both source and coarse triangulations.
 e0=np.roll(A[a:b+1],-1,axis=1)-A[a:b+1]
 source=.25*np.linalg.norm(np.diff(e0,axis=0),axis=2).max()
 coarse=.25*np.linalg.norm(e0[-1]-e0[0],axis=1).max()
 return float(d+source+coarse)
out=[0]
def split(a,b):
 if b-a<=1 or error(a,b)<.00060:out.append(b);return
 m=(a+b)//2;split(a,m);split(m,b)
for a,b in zip(pins,pins[1:]):split(a,b)
idx=out[:-1];num=len(idx); Q=A[idx].reshape(-1,3);fs=[]
for i in range(num):
 for j in range(K):
  a=i*K+j;b=i*K+(j+1)%K;c=(i+1)%num*K+(j+1)%K;d=(i+1)%num*K+j;fs.extend(((a,b,c),(a,c,d)))
fs=np.array(fs)
E=Q[fs]
if np.einsum('ij,ij->i',E[:,0],np.cross(E[:,1],E[:,2])).sum()<0:
 fs=fs[:,::-1];E=Q[fs]
c=Counter((i,j) for f in fs for i,j in zip(f,np.roll(f,-1)))
assert all(vv==1 and c[j,i]==1 for (i,j),vv in c.items())
check=pairs(E,E,True,fs,fs);assert check['pairs']==0,check
seat={k:v[np.array(a)] for k,a in g.items() if k!='weave'}
ret={}
for k,s in seat.items():
 F={frozenset(map(tuple,t)) for t in E}
 eq=[i for i,t in enumerate(s) if frozenset(map(tuple,t)) in F]
 assert len(eq)==2
 hit=pairs(E,s);assert hit['pairs']==0
 ret[k]=dict(retained_identical_support_triangles=len(eq),exclusion=hit)
d=np.load(NP)
U=d['position'];G=d['group']
protected=pairs(E,U[np.isin(G,['body','caps','rear_0','rear_1','rail_1'])]);assert protected['pairs']==0
rho=max(error(a,b) if b-a>1 else 0. for a,b in zip(out,out[1:]))
cap=float((9.94742-Q[:,2].max())*1000)
report=dict(original=12000,low=len(fs),ring_count=num,pinned_rings=pins,strict_self=check,
             max_continuous_correspondence_bound_mm=rho*1000,whole_anisotropy_independent_camera_error_px=rho*720/13,
             retained_radius_and_faceting=True,seats=ret,protected=protected,outward_margin_mm=cap)
print(json.dumps(report,indent=2))
def obj(q,f):
 return ['v '+' '.join(f'{x:.12f}' for x in a) for a in q]+['f '+' '.join(str(int(x)+1) for x in a) for a in f]
(R/'ReducedWeave_Study.obj').write_text('\n'.join(['# exact one-bay detached proof; supports in upstream OBJ']+obj(Q,fs))+'\n')
