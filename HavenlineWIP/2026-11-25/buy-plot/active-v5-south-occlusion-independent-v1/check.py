import hashlib,json,sys,subprocess,ctypes as C
from pathlib import Path
import numpy as np
from scipy.optimize import brentq
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def seal(p,h):
 assert digest(p/'SHA256SUMS')==h
 for ln in (p/'SHA256SUMS').read_text().splitlines():
  sh,n=ln.split();assert digest(p/n)==sh
root=Path('..')
prod=root/'hvn-l1-v5-south-occlusion-v1'
seal(prod,'595cf64fea1851df5a46369b682a944c781b9b0085ec7654d08b1e603ab6d887')
expected=json.loads((prod/'result.json').read_text())
native=root/'hvn-l1-v5-price-independent-v1.7ynPB9'
seal(native,'d2e15b83e7ac9e0bea467bdf1f6c51ff0e925b08c1d24d11a1b52b0e7dd31dc9')
m={k:json.loads((native/(k+'-native.json')).read_text()) for k in ['base','trial']}
rh=root/'havenline-pad-v6-south-read-window/replay.WCCavq'
assert digest(rh/'EVIDENCE_SHA256')=='74273477aaada021bffbba0d2a77673698689a86e0c0e779e579c975662556d3'
assert [r.split()[0] for r in (rh/'EVIDENCE_SHA256').read_text().splitlines() if r.endswith('render.log')]==[digest(rh/'render.log')]
route={j['name']:j for x in (rh/'render.log').read_text().splitlines() if x.startswith('APPROACH ') for j in [json.loads(x[9:])]}
repo,hero=sys.argv[1:];hero=Path(hero)
assert digest(hero)=='1085971466b96a34b79eb96e00dd4f01d95f8498a37b638292ec112b57a73089'
origin=next(json.loads(x[12:]) for x in (root/'hvn-counter-cpu-surface-audit/route.log').read_text().splitlines() if x.startswith('CPU_SURFACE ') and 'center-inboard-hard-stop' in x)
assert origin==expected['borrowed_pose']
sr=subprocess.check_output(['git','-C',repo,'show','11c14a1c41971067c7dc97db69375f720a408f68:HavenlineLevel1/previews/integrated_opening.gd']).decode()
assert 'camera.position = actor.position + Vector3(7, 11, 11)' in sr and '_within_logical_reach(pad_anchor, .72)' in sr
ray=np.array([7.,11.,11.]); ray/=np.linalg.norm(ray)
ix=np.cross([0.,1.,0.],ray);ix/=np.linalg.norm(ix); iy=np.cross(ray,ix)
screen=np.c_[ix,iy]
T=[]
for q in json.loads(hero.read_text()):
 assert q['matrixes']==66
 T.extend((np.array(q['positions'])-origin['foot'])[np.array(q['triangles']).reshape(-1,3)])
T=np.array(T); assert len(T)==96001
def pv(a,k):return np.array([float(v) for v in a[k].strip('()').split(',')])
near=route['05-south-090cm']; nxt=route['04-south-110cm']
pad=pv(near,'pad_global'); l0=pv(near,'actor_global')-pad; l1=pv(nxt,'actor_global')-pad
coef=(l1[1]-l0[1])/(l1[2]-l0[2]); foot=lambda z:np.array([l0[0],l0[1]+coef*(z-l0[2]),z])
z=brentq(lambda z: np.linalg.norm(foot(z))-.72,.60,.80,xtol=1e-15)
samples={k:(pv(route[k],'actor_global')-pad,route[k]['actor_yaw_rad']) for k in ['02-south-160cm','05-south-090cm']}
samples['synthetic-south-072cm']=(foot(z),near['actor_yaw_rad'])
# World-space triangle clipping to screen-side of horizontal label plane;
# independently accumulate in orthonormal image coordinates, not projected XZ.
lib=C.CDLL('libgeos_c.so.1'); ptr=C.c_void_p
def bind(n,out,*a):
 f=getattr(lib,n);f.restype=out; f.argtypes=a;return f
bind('initGEOS',None,ptr,ptr)(None,None)
read=bind('GEOSGeomFromWKT',ptr,C.c_char_p)
uni=bind('GEOSUnaryUnion',ptr,ptr)
inter=bind('GEOSIntersection',ptr,ptr)
area=bind('GEOSArea',C.c_int,ptr,C.POINTER(C.c_double))
def ar(k):
 v=C.c_double(); assert k and area(k,C.byref(v))==1
 return v.value
def disk(x):return '(('+','.join('%.13f %.13f'%tuple(u) for u in np.r_[x,x[:1]])+'))'
def cross2(a,b):return a[...,0]*b[...,1]-a[...,1]*b[...,0]
def clips(t,y):
 # Case split by count above; enumerate edge-plane intersections, then order convex hull
 v=t[t[:,1]>=y].tolist()
 if not v:return np.empty((0,2))
 a,b,c=t; h=t[:,1]-y
 for i,j in [(0,1),(0,2),(1,2)]:
  if h[i]*h[j]<0:v.append(((h[i]*t[j]-h[j]*t[i])/(h[i]-h[j])).tolist())
 q=np.array(v)@screen
 if len(q)<3:return q
 d=q-q.mean(0)
 return q[np.argsort(np.arctan2(d[:,1],d[:,0]))]
def frac(t,lo,hi,y):
 target=np.array([[lo[0],y,lo[1]],[hi[0],y,lo[1]],[hi[0],y,hi[1]],[lo[0],y,hi[1]]])@screen
 tp=t@screen
 ok=(tp.max(1)>=target.min(0)).all(1)&(tp.min(1)<=target.max(0)).all(1)&(t[:,:,1].max(1)>y+1e-10)
 q=[]
 for a in t[ok]:
  p=clips(a,y)
  if len(p)>=3 and abs(cross2(p,np.roll(p,-1,axis=0)).sum())>1e-15:q.append(p)
 if not q:return 0.
 t=read(('POLYGON '+disk(target)).encode())
 u=uni(read(('MULTIPOLYGON('+','.join(map(disk,q))+')').encode()))
 return ar(inter(t,u))/ar(t)
res={}
for name,(v,yaw) in samples.items():
 h=yaw-origin['yaw']; c=np.cos(h);s=np.sin(h)
 Q=np.array([[c,0,s],[0,1,0],[-s,0,c]])
 g=T@Q.T+v
 rows={}
 for kind in m:
  for k,l in m[kind]['label'].items():
   native_q=np.array(l['triangles']); assert len(native_q)==6
   lo=native_q.min(0)[[0,2]];hi=native_q.max(0)[[0,2]]
   y=native_q[0,1]; assert np.ptp(native_q[:,1])<1e-9
   margin=(hi[0]-lo[0])*14/l['string_metrics'][0]
   raw,guard=frac(g,lo,hi,y),frac(g,lo-margin,hi+margin,y)
   orig=expected['results'][name]['labels'][kind+'/'+k]['occlusion']
   assert max(abs(raw-orig['native_line_quad']['0']['fraction']),abs(guard-orig['14font_px_guard']['0']['fraction']))<2e-7
   rows[kind+'/'+k]=[raw,guard]
 res[name]={'borrowed_distance_m':float(np.linalg.norm(v)),'fractions_native_and_guard':rows}
print(json.dumps({'threshold_height_interpolated_not_observation':True,'threshold_actual_3d_dist_m':float(np.linalg.norm(foot(z))),
 'exact_borrowed_animation':origin.get('animation','see original route'), 'verified_results':res},indent=2,sort_keys=True))
