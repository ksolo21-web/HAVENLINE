import os
from pathlib import Path
import numpy as np,hashlib,json
P=Path(__file__).resolve().parent
old=Path(os.environ['C1_LAYERED_DATA'])
tri0=Path(os.environ['C1_VISIBLE_PANEL_DATA'])
assert hashlib.sha256((old/'exact-assembled-surface.npz').read_bytes()).hexdigest()=='fd8119c8fbc802ced409fea6aabc0414657e88983e95ffb0050c0e34ceda1631'
a=np.load(old/'exact-assembled-surface.npz');b=np.load(tri0/'manual-panel-surface.npz')
V=a['v'];T=a['tri']; trim=a['trim_v'];f=a['trim_f'];n=b['trim_planar_normal'];C=trim[:5].mean(0)
ex=trim[1]-trim[0];ex/=np.linalg.norm(ex);ey=np.cross(n,ex);ey/=np.linalg.norm(ey)
basis=np.stack((ex,ey,n),1)
def tr(points):return (points-C)@basis
X=tr(V); q=tr(trim);F=f[:3]
def cross(a,b):return a[0]*b[1]-a[1]*b[0]
def clip_vertices(A, B):
 B=B if cross(B[1]-B[0],B[2]-B[0])>=0 else B[::-1]
 p=A
 for u,v in zip(B,np.roll(B,-1,axis=0)):
  q=[]
  for j,a in enumerate(p):
   b=p[(j+1)%len(p)];w=cross(v-u,a[:2]-u);z=cross(v-u,b[:2]-u)
   if w>=-1e-15:q.append(a)
   if (w< -1e-15)!=(z< -1e-15):q.append(a+(w/(w-z))*(b-a))
  p=np.asarray(q)
  if len(p)==0:break
 return p
r=np.empty((3,2));proj=q[F,:2].reshape(-1,2);W=X[T]
near=((W[:,:,:2].max(1)>=proj.min(0)-1e-9)&(W[:,:,:2].min(1)<=proj.max(0)+1e-9)).all(1)&(W[:,:,2].max(1)>-.010)&(W[:,:,2].min(1)<.002)
fix=np.flatnonzero(near)
rows=[]
for i in fix:
 ss=[]
 for t in F:
  p=clip_vertices(W[i],q[t,:2])
  if len(p):ss.extend(p.tolist())
 if ss:
  z=np.asarray(ss);k=z[z[:,2].argmax()]
  rows.append({'id':int(i),'max_mm_relative_to_exact_cap':k[2]*1000,'point_mm':(k*1000).tolist(),'geometry_ids':T[i].tolist()})
rows=sorted(rows,key=lambda x:x['max_mm_relative_to_exact_cap'],reverse=True)
print('in footprint',len(rows),'nearest',rows[:12]);print('rim',X[b['repeated_rim_indices'],2]*1000, b['repeated_rim_indices'])
(P/'stack.json').write_text(json.dumps({'cap_origin_m':C.tolist(),'basis':basis.tolist(),'count':len(rows),'nearest':rows[:60]},indent=2))
