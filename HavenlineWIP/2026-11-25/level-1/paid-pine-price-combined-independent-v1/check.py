import hashlib,json,re,subprocess,sys,ctypes as C,tempfile
from pathlib import Path
import numpy as np
raw,repo=map(lambda x:Path(x).resolve(),sys.argv[1:])
q=Path('../hvn-l1-v5-paid-pine-combined-v1').resolve()
f=Path('../hvn-l1-v5-price-exposed-fit-v1').resolve()
p=Path('../hvn-l1-paid-pine-renewal-v1').resolve()
def sh(x):return hashlib.sha256(x.read_bytes()).hexdigest()
for k,h in [(q,'950d1a8b9992596a7b56ec64c7c98fbe1c9d34c04e698a78fb0dfbc50db4b031'),(f,'93475711ec9ede90409a5c2d52fb5912bcfcc2ce0bcd8ffae960ef82eab6afd6'),(p,'2939ea7d5a82461840888791619fd4ecc0eb41d6f6371cfc4170554de94d5a2f')]:
 assert sh(k/'SHA256SUMS')==h
 for row in (k/'SHA256SUMS').read_text().splitlines():
  h,n=row.split(); assert sh(k/n)==h
blobs=dict((b,a) for a,b in (r.split() for r in (q/'combined-blobs.txt').read_text().splitlines()))
pin='11c14a1c41971067c7dc97db69375f720a408f68'
def raw_pin(name):return subprocess.check_output(['git','-C',str(repo),'show',pin+':HavenlineLevel1/'+name])
with tempfile.TemporaryDirectory() as d:
 for n in blobs:
  x=Path(d,n); x.parent.mkdir(parents=True,exist_ok=True);x.write_bytes(raw_pin(n))
 Path(d,'tests').mkdir(exist_ok=True)
 for k,n in [(f,'cost-location-only.patch'),(p,'renewal.patch')]:
  subprocess.run(['patch','--quiet','--fuzz=0','-p2','-i',str(k/n)],cwd=d,check=True)
 for n,b in blobs.items():
  assert Path(d,n).read_bytes()==(raw/'project'/n).read_bytes()
  assert subprocess.check_output(['git','hash-object',str(Path(d,n))],text=True).strip()==b
for n in ['opening.gd','opening_save.gd','resource_tree.gd','purchase_pad_visual.gd','previews/integrated_opening.tscn','previews/hero_locomotion.gd','assets/characters/Character1.glb','tests/test_integrated_opening.gd','project.godot']:
 assert raw_pin(n)==(raw/'project'/n).read_bytes()
assert sh(raw/'project/assets/studio/purchase_pad_v5.glb')=='d938ed53778f135359d4a345603a84353a7d02daddc0ff6e389453101119b7cb'
assert sh(raw/'project/assets/studio/hearth_trial_02.glb')=='35d5529066168834ed87c09e0db6f98bf058f5a75b0175c57e0e78bbc2a70f5a'
lib=C.CDLL('libgeos_c.so.1'); ptr=C.c_void_p
def bind(n,out,*a):
 f=getattr(lib,n);f.restype=out; f.argtypes=a;return f
bind('initGEOS',None,ptr,ptr)(None,None)
read=bind('GEOSGeomFromWKT',ptr,C.c_char_p)
uni=bind('GEOSUnaryUnion',ptr,ptr)
inter=bind('GEOSIntersection',ptr,ptr,ptr)
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
# Second independent positive-projection oracle: start rays in actual target
# plane and trace physical triangle intersections, no projected-polygon union.
def positive_rays(t,lo,hi,y,n=13):
 z=np.linspace(.025,.975,n); points=np.array([[lo[0]+(hi[0]-lo[0])*a,y,lo[1]+(hi[1]-lo[1])*b] for a in z for b in z])
 # Preselect with independent image-bound containment and camera-side depth.
 px=points@screen; tx=t@screen
 mask=(tx.min(1)<=px.max(0)).all(1)&(tx.max(1)>=px.min(0)).all(1)&(t[:,:,1].max(1)>y)
 t=t[mask]
 if not len(t):return 0
 A=t[:,0]; B=t[:,1]-A; D=t[:,2]-A
 H=np.cross(ray,D); p=(B*H).sum(1); good=abs(p)>1e-14; safe=np.where(good,p,1.)
 off=points[:,None]-A; Q=np.cross(off,B)
 u=(off*H).sum(2)/safe; v=Q@ray/safe; distance=(D*Q).sum(2)/safe
 return int(np.any(good & (u>=-1e-10)&(v>=-1e-10)&(u+v<=1+1e-10)&(distance>1e-8),axis=1).sum())
logs={}
for mode,num in [('funded',34),('cold',3)]:
 x=raw/mode/'log'
 assert sh(x)==sh(q/(mode+'.log')); text=x.read_text()
 assert not re.search(r'ERROR|WARNING|FAIL',text)
 logs[mode]=text.splitlines()
 assert len([r for r in logs[mode] if r.startswith('PASS ')])==num
paid=[r for r in logs['funded'] if r.startswith('PASS ')]
need=['East gate physical outward traversal','East gate physical return traversal','South gate physical outward traversal','South gate physical return traversal',
'one +1 original pine occurrence, unchanged hearth receipt','still hidden at tick 299, no passive new wood','rooted at tick 300, still one wood']
assert all(sum(s in p for p in paid)==1 for s in need)
assert all(any(s in r for r in logs['cold']) for s in ('imports one existing paid cut, not duplicated','keeps camp and hides relocated pad','regrows without a new payout'))
rows=[json.loads(r[10:]) for r in logs['funded'] if r.startswith('PAD_ROUTE ')]
assert [r['tag'] for r in rows]==['far','moving','near','before','after']
summary={}
new=[]
for rec in rows:
 tag=rec['tag']; delta=np.array(rec['feet'])-rec['anchor']
 assert abs(np.linalg.norm(delta)-rec['distance'])<2e-6
 if tag=='after':
  assert rec['receipt']=={'grant':'center-hearth','offer':'center-hearth','revision':1,'typed_debit':{'wood':3}}
  assert not rec['visible'] and not rec['pad_visible'] and rec['camp'] and rec['quad']==[] and rec['stock']==0
  continue
 assert rec['receipt']=={} and rec['stock']==3 and rec['visible'] and rec['pad_visible'] and not rec['camp'] and rec['text']=='3 WOOD'
 assert abs(delta[0])<.01 and delta[2]>.72
 assert rec['camera_projection']==1 and rec['camera_size']==13
 ray=np.array(rec['camera_back']);ray/=np.linalg.norm(ray); v=np.cross([0.,1.,0.],ray);v/=np.linalg.norm(v); screen=np.c_[v,np.cross(ray,v)]
 x=np.array(rec['quad']);lo,hi=x.min(0)[[0,2]],x.max(0)[[0,2]];y=x[0,1]
 assert len(np.unique(x,axis=0))==4 and np.ptp(x[:,1])<1e-7
 m=14*(hi[0]-lo[0])/122
 mesh=raw/'funded'/(tag+'.json')
 t=np.concatenate([np.array(v['positions'])[np.array(v['triangles']).reshape(-1,3)] for v in json.loads(mesh.read_text())])
 assert len(t)==96001
 c=[frac(t,lo,hi,y),frac(t,lo-m,hi+m,y)]
 r=[positive_rays(t,lo,hi,y,13),positive_rays(t,lo-m,hi+m,y,13)]
 if tag=='moving':
  assert rec['animation']=='l1_hero_preview/run' and rec['animation_t']==.15 and abs(rec['distance']-.95285302400589)<1e-10
  assert abs(c[0]-.47047)<.0001 and abs(c[1]-.47195)<.0001 and all(30<a<140 for a in r)
 else:
  assert max(c)<1e-7 and r==[0,0]
 summary[tag]={'distance_m':rec['distance'],'animation':rec['animation'],'t':rec['animation_t'],'quad_guard_fractions':c,'quad_guard_out_of_169_camera_rays':r,'mesh_hash':sh(mesh)}
print(json.dumps({'production_changed_blobs_reunited':blobs,'headless_author_log_counts':[34,3],'debit_revision_1_wood':3,'disposable_cold_gates_and_new_pine_verified' : True,'camera_positive_occlusion':summary},sort_keys=True,indent=2))
