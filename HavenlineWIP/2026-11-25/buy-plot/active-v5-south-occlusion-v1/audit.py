from pathlib import Path
import ctypes as C, hashlib, json, re, subprocess, sys, math
import numpy as np
root=Path('..')
def hash_(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def verify(p,m,h):
 assert hash_(p/m)==h
 for r in (p/m).read_text().splitlines():
  sha,f=r.split(maxsplit=1);assert hash_(p/f.lstrip('*'))==sha
p=root/'hvn-l1-v5-price-independent-v1.7ynPB9'
verify(p,'SHA256SUMS','d2e15b83e7ac9e0bea467bdf1f6c51ff0e925b08c1d24d11a1b52b0e7dd31dc9')
variants={k:json.loads((p/(k+'-native.json')).read_text()) for k in ('base','trial')}
p=root/'havenline-pad-v6-south-read-window/replay.WCCavq'
assert hash_(p/'EVIDENCE_SHA256')=='74273477aaada021bffbba0d2a77673698689a86e0c0e779e579c975662556d3'
assert next(r.split()[0] for r in (p/'EVIDENCE_SHA256').read_text().splitlines() if r.endswith('render.log')) == hash_(p/'render.log')
route={q['name']:q for a in (p/'render.log').read_text().splitlines() if a.startswith('APPROACH ') for q in [json.loads(a[9:])]}
repo, hero = sys.argv[1],Path(sys.argv[2])
sha='1085971466b96a34b79eb96e00dd4f01d95f8498a37b638292ec112b57a73089'
assert hash_(hero)==sha
padlog=(root/'hvn-counter-cpu-surface-audit/route.log').read_text()
origin=next(json.loads(r[12:]) for r in padlog.splitlines() if r.startswith('CPU_SURFACE ') and 'center-inboard-hard-stop' in r)
tri=[]
for row in json.loads(hero.read_text()):
 assert row['matrixes']==66 and row['vertices_with_pose_delta']>100
 tri.extend((np.asarray(row['positions'])-origin['foot'])[np.array(row['triangles']).reshape(-1,3)])
tri=np.array(tri)
s=subprocess.check_output(['git','-C',repo,'show','11c14a1c41971067c7dc97db69375f720a408f68:HavenlineLevel1/previews/integrated_opening.gd']).decode()
assert 'camera.position = actor.position + Vector3(7, 11, 11)' in s and 'camera.look_at(actor.position)' in s
ray=np.array([7/11,1.,1.]); rayxz=ray[[0,2]]
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
def pv(q,k):return np.array([float(x) for x in q[k].strip('()').split(',')])
samples={k:route[k] for k in ('02-south-160cm','05-south-090cm')}
p90=pv(samples['05-south-090cm'],'actor_global'); pad=pv(samples['05-south-090cm'],'pad_global')
p110=pv(route['04-south-110cm'],'actor_global')
slope=(p110[1]-p90[1])/(p110[2]-p90[2])
z=.720
for _ in range(5):z=math.sqrt(.72**2-(p90[1]-pad[1]+slope*(pad[2]+z-p90[2]))**2)
near=np.array([p90[0],p90[1]+slope*(pad[2]+z-p90[2]),pad[2]+z])
stations={k:(pv(q,'actor_global')-pad,q['actor_yaw_rad']) for k,q in samples.items()}
stations['synthetic-south-072cm']=(near-pad,samples['05-south-090cm']['actor_yaw_rad'])
assert abs(np.linalg.norm(near-pad)-.72)<1e-6
results={}
for stance,(feet,yaw) in stations.items():
 c,s=math.cos(yaw-origin['yaw']),math.sin(yaw-origin['yaw'])
 yawmat=np.array([[c,0,s],[0,1,0],[-s,0,c]])
 t=tri@yawmat.T+feet
 out={}
 for mode,m in variants.items():
  for line,l in m['label'].items():
   T=np.array(l['triangles']); lo=T.min(0)[[0,2]]; hi=T.max(0)[[0,2]]; y=T[0,1]
   assert np.ptp(T[:,1])<1e-9
   unit_m=(hi[0]-lo[0])/l['string_metrics'][0]; margin=14*unit_m
   output={}
   for mask,(L,H) in [('native_line_quad',(lo,hi)),('14font_px_guard',(lo-margin,hi+margin))]:
    tar=read(('POLYGON('+loop(rect(L,H))+')').encode())
    total=garea(tar); cov={}
    for sign in (0,1,-1):
     mesh,n=polys(t,y,L,H,sign); pct=0. if mesh is None else garea(inter(tar,mesh))/total
     cov[str(sign)]={'fraction':pct,'near_occluder_triangles':n}
    output[mask]=cov
   out[mode+'/'+line]={'whole_line_adv_px':float(np.linalg.norm(l['px_axis_x_for_30'])/30*l['string_metrics'][0]),'first_glyph_height_px':float(np.linalg.norm(l['px_axis_y_for_30'])/30*l['glyph_texture_metrics'][0]['size'][1]),'occlusion':output}
 results[stance]={'distance_m':float(np.linalg.norm(feet)),'actor_yaw':yaw,'labels':out}
assert all(y['occlusion']['14font_px_guard']['0']['fraction']<1e-10 for y in results['02-south-160cm']['labels'].values())
print(json.dumps({'cpu_pose_sha256':sha,'borrowed_pose':origin,'triangles':len(tri),'above_label_positive_depth_only':True,'results':results},indent=2))
