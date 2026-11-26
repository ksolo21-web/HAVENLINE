"""Neutral, source-preserving cuff section witness; outputs counts and distances only."""
import hashlib,sys,struct,json
from pathlib import Path
from collections import defaultdict
import numpy as np
a,p,n,j = [Path(x) for x in sys.argv[1:]]
hashf=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for f,h in [(a,'95e4fed3a2778656cdf8b73affd2eb3feda8a32f82f4a0c3f76d90c82633c099'),(p,'c5aeeb13c75ec0b44b9b9cf42cd1e1b7e2e09836cde23888450e7778b5d163a7')]:assert hashf(f)==h
assert hashf(j)=='57c7bc4f70de42e9fd6f212d5c58e2bb7d65e0f84b971bcf76dc79d818b5d05e'
J=json.loads(j.read_text()); assert hashf(n)==J['payload_sha256'][n.name]
b=a.read_bytes(); l=struct.unpack_from('<I',b,12)[0];d=json.loads(b[20:20+l]);b=memoryview(b)[28+l:]
def read(i,k):
 q=d['accessors'][i];v=d['bufferViews'][q['bufferView']]
 assert not v.get('byteStride')
 return np.frombuffer(b,{5126:'<f4',5125:'<u4',5123:'<u2'}[q['componentType']],count=q['count']*k,offset=v.get('byteOffset',0)+q.get('byteOffset',0)).reshape(-1,k)
pr=d['meshes'][0]['primitives'][0]; V=read(pr['attributes']['POSITION'],3).astype(float); T=read(pr['indices'],1).reshape(-1,3)
C,*B=np.array(json.loads(p.read_text())[0]['camera']); S,*D=np.array(json.loads(p.read_text())[0]['character']['mesh_world'])
def proj(r):return ((r@D+S-C)@np.array(B[:2]).T)*(720/13.)
def cross(a,b):return a[...,0]*b[...,1]-a[...,1]*b[...,0]
def area(r):return abs(cross(r,np.roll(r,-1,axis=0)).sum())/2
def simple(r):
 for i,a in enumerate(r):
  b=r[(i+1)%len(r)]
  for j in range(i+2,len(r)-(i==0)):
   c,e=r[j],r[(j+1)%len(r)];ab=b-a;ce=e-c;d=cross(ab,ce)
   if abs(d)>1e-17:
    t=cross(c-a,ce)/d;u=cross(c-a,ab)/d
    if -1e-10<=t<=1+1e-10 and -1e-10<=u<=1+1e-10:return False
   elif abs(cross(c-a,ab))<1e-16:
    ts=sorted([(c-a)@ab/(ab@ab),(e-a)@ab/(ab@ab)])
    if ts[1]>=0 and ts[0]<=1:return False
 return True
def exact(y):
 h=V[T,1]; A=defaultdict(list); coords={}
 for face in np.flatnonzero((h.min(1)<y)&(h.max(1)>y)):
  ids=T[face]; edge=[]
  for i,k in zip(ids,np.roll(ids,1)):
   x,z=V[sorted((i,k))]
   if (x[1]-y)*(z[1]-y)<0:
    w=(y-x[1])/(z[1]-x[1]); r=x*(1-w)+z*w
    key=tuple(np.round(r,7));coords.setdefault(key,r)
    assert np.max(np.abs(coords[key]-r))<1e-7
    edge.append(key)
  assert len(edge)==2 and edge[0]!=edge[1]; m,n=edge;A[m].append(n);A[n].append(m)
 assert all(len(set(q))==2 for q in A.values())
 P=[]
 while A:
  start=min(A); loop=[]; prev=None; k=start
  while not loop or k!=start:
   loop.append(k); m=min(set(A.pop(k))-{prev});prev,k=k,m
  P.append(np.array([coords[k] for k in loop]))
 P=[r for r in P if r[:,0].mean()>0];return max(P,key=lambda r:area(r[:,[0,2]]))
def err(A,B):
 P=np.roll(B,-1,axis=0)-B; D=A[:,None]-B
 t=np.clip(np.einsum('mni,ni->mn',D,P)/np.maximum((P*P).sum(1),1e-18),0,1)
 return float(np.linalg.norm(D-t[:,:,None]*P,axis=2).min(1).max())
def pair(A,B):return max(err(A,B),err(B,A))
M=J['modules'][0]; N=np.load(n,allow_pickle=False)['v'][:M['count']].reshape(-1,M['ring_sizes'],3)
rows=[]
for i,y in enumerate(M['stations']):
 r=exact(y); proj_r=proj(r); old=pair(proj_r,proj(N[i]))
 xy=r[:,[0,2]]; theta=np.unwrap(np.angle((xy-xy.mean(0))@np.array([1,1j])))
 turn=np.diff(np.r_[theta,theta[-1]+np.angle(np.exp(1j*(theta[0]-theta[-1])))])
 s=simple(xy)
 assert s and len(r)>2
 rows.append(dict(art_height_m=y,source_polygon_corners=len(r),polyline_simple=s,angle_reverse_edges=int(min((turn<0).sum(),(turn>0).sum())),previous_px=old,exact_fixed_boundary_px=pair(proj_r,proj_r.copy())))
bad=max(rows,key=lambda q:q['previous_px']);assert abs(bad['previous_px']-M['max_profile_disagreement_stock_view_px'])<.0001 and bad['art_height_m']==.0861
print(json.dumps(dict(section_rows=rows,hard_section_exact_boundary_met=bad['exact_fixed_boundary_px']<=1,previous_current_unchanged_gate_prefers_only_exact_bad_ring_replacement_max_px=max(q['previous_px'] for q in rows if q is not bad),rig_and_splice_measured=False),indent=2))
