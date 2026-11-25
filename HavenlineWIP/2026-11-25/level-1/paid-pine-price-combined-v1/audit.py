from pathlib import Path
import ctypes as C, hashlib, json, re, subprocess, sys, math
import numpy as np
ray=rayxz=None
lib=C.CDLL('libgeos_c.so.1'); ptr=C.c_void_p
def bind(n,ret,*a):
 f=getattr(lib,n); f.restype=ret; f.argtypes=a; return f
bind('initGEOS',None,ptr,ptr)(None,None)
read=bind('GEOSGeomFromWKT',ptr,C.c_char_p); union=bind('GEOSUnaryUnion',ptr,ptr)
inter=bind('GEOSIntersection',ptr,ptr,ptr); area=bind('GEOSArea',C.c_int,ptr,C.POINTER(C.c_double))
def garea(g):
 x=C.c_double();assert g and area(g,C.byref(x));return x.value
def loop(P):return '('+','.join(f'{a:.12f} {b:.12f}' for a,b in [*P,P[0]])+')'
def rect(l,h):return np.array([l,[h[0],l[1]],h,[l[0],h[1]]])
def clipfront(t,y):
 out=[]
 for a,b in zip(t,np.roll(t,-1,axis=0)):
  u,v=a[1]-y,b[1]-y
  if u>=0:out.append(a)
  if (u>=0)!=(v>=0):out.append(a+(b-a)*(u/(u-v)))
 return np.array(out)
def polys(t,y,lo,hi,sign=0):
 px=t[:,:,[0,2]]-(t[:,:,1:2]-y)*rayxz
 normals=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0])@ray
 ok=((px.max(1)>=lo)&(px.min(1)<=hi)).all(1)&(t[:,:,1].max(1)>y+1e-10)
 if sign:ok &= sign*normals>1e-14
 arr=[]
 for i in np.flatnonzero(ok):
  q=clipfront(t[i],y); X=q[:,[0,2]]-(q[:,1:2]-y)*rayxz
  if len(X)<3 or len(np.unique(X.round(12),axis=0))!=len(X):continue
  u,v=X[1]-X[0],X[2]-X[0]
  if abs(u[0]*v[1]-u[1]*v[0])<1e-13:continue
  arr.append('('+loop(X)+')')
 return (union(read(('MULTIPOLYGON('+','.join(arr)+')').encode())) if arr else None,len(arr))
root=Path(sys.argv[1])
data={}
for k in ('funded',):
 d=root/k
 rows=[json.loads(l[10:]) for l in (d/'log').read_text().splitlines() if l.startswith('PAD_ROUTE ')]
 assert [r['tag'] for r in rows]==['far','moving','near','before','after']
 for r in rows:
  if r['tag']=='after':
   assert r['stock']==0 and r['receipt']['typed_debit']=={'wood':3} and not r['visible'] and not r['pad_visible']
   continue
  assert r['visible'] and r['stock']==(3 if k=='funded' else 0) and len(r['quad'])==6 and r['camera_size']==13 and r['distance']>=.72
  assert np.allclose(np.array(r['camera_back'])/r['camera_back'][1],[7/11,1,1],atol=3e-6)
  ray=np.array(r['camera_back'])/r['camera_back'][1];rayxz=ray[[0,2]]
  M=np.asarray(r['quad'])
  w,lo,hi=M[:,1].mean(),M.min(0)[[0,2]],M.max(0)[[0,2]]
  assert np.ptp(M[:,1])<2e-6
  src=json.loads((d/(r['tag']+'.json')).read_text()); tri=np.concatenate([np.array(o['positions'])[np.array(o['triangles']).reshape(-1,3)] for o in src])
  assert len(tri)==96001
  targets={'native':(lo,hi),'modeled_guard_14px':(lo-(hi[0]-lo[0])*14/122,hi+(hi[0]-lo[0])*14/122)}
  r['occlusion']={}
  for label,(L,H) in targets.items():
   if label.startswith('modeled') and r['text']!='3 WOOD':continue
   target=read(('POLYGON('+loop(rect(L,H))+')').encode()); orig=garea(target)
   r['occlusion'][label]={}
   for sign in (0,1,-1):
    mask,cnt=polys(tri,w,L,H,sign)
    r['occlusion'][label][str(sign)]=dict(fraction=0 if mask is None else garea(inter(target,mask))/orig,triangles=cnt)
 data[k]=rows
print(json.dumps(data,indent=2,sort_keys=True))
