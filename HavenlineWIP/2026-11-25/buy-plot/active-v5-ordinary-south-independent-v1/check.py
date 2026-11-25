import hashlib,json,sys,subprocess,ctypes as C,re
from pathlib import Path
import numpy as np
P=Path('../hvn-l1-v5-ordinary-south-v1')
def sh(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert sh(P/'SHA256SUMS')=='7480ea02eba2e75c4a7a073e703470304d4e41f46bb9996285d7d4893146a38a'
for line in (P/'SHA256SUMS').read_text().splitlines():
 h,n=line.split(); assert sh(P/n)==h
repo,raw=Path(sys.argv[1]),Path(sys.argv[2]); assert raw.is_dir()
gitrev='11c14a1c41971067c7dc97db69375f720a408f68'
keys=['opening.gd','pad_v5_view.gd','purchase_pad_visual.gd','previews/integrated_opening.gd','previews/integrated_opening.tscn','previews/hero_locomotion.gd','assets/characters/Character1.glb','tests/test_integrated_opening.gd']
for f in keys:
 s=subprocess.check_output(['git','-C',str(repo),'show',gitrev+':HavenlineLevel1/'+f])
 assert hashlib.sha256(s).hexdigest()==sh(raw/'project'/f)
assert sh(raw/'project/assets/studio/purchase_pad_v5.glb')=='d938ed53778f135359d4a345603a84353a7d02daddc0ff6e389453101119b7cb'
s=(raw/'project/previews/integrated_opening.gd').read_text()
assert '_within_logical_reach(pad_anchor, .72)' in s and 'ledger.receipt.is_empty()' in s
assert 'next.pay_center_hearth()' in s and 'return _commit_opening_progress(next)' in s
expect=json.loads((P/'result.json').read_text())
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
report={}
for k in ('unfunded','funded'):
 l0=raw/k/'log'
 assert sh(l0)==sh(P/(k+'.log'))
 log=l0.read_text(); assert not re.search(r'ERROR|WARNING|FAIL',log)
 rows=[json.loads(l[10:]) for l in log.splitlines() if l.startswith('PAD_ROUTE ')]
 assert [z['tag'] for z in rows]==(['far','near'] if k=='unfunded' else ['far','near','before','after'])
 assert all(a['tick']<b['tick'] for a,b in zip(rows,rows[1:]))
 got=[]
 for row,ref in zip(rows,expect[k]):
  assert row=={key:ref[key] for key in row}
  dist=np.array(row['feet'])-row['anchor']; assert abs(np.linalg.norm(dist)-row['distance'])<2e-6
  if row['tag']=='after':
   assert not row['visible'] and not row['pad_visible'] and row['quad']==[] and row['camp'] and row['stock']==0 and row['receipt']=={'grant':'center-hearth','offer':'center-hearth','revision':1,'typed_debit':{'wood':3}} and np.linalg.norm(dist)<.72
   got.append({'tag':row['tag'],'receipt':row['receipt'],'pad_and_label_hidden':True,'camp_visible':True})
   continue
  assert row['stock']==(3 if k=='funded' else 0) and not row['camp'] and row['pad_visible'] and row['visible'] and not row['receipt']
  assert .72<dist[2] and abs(dist[0])<.01 and row['text']=='3 WOOD'
  assert row['camera_projection']==1 and row['camera_size']==13.
  ray=np.array(row['camera_back']); ray/=np.linalg.norm(ray)
  ix=np.cross([0.,1.,0.],ray);ix/=np.linalg.norm(ix);screen=np.c_[ix,np.cross(ray,ix)]
  raw_file=raw/k/(row['tag']+'.json')
  src=json.loads(raw_file.read_text()); t=np.concatenate([np.array(v['positions'])[np.array(v['triangles']).reshape(-1,3)] for v in src])
  assert len(t)==96001
  sq=np.array(row['quad']); lo=sq.min(0)[[0,2]];hi=sq.max(0)[[0,2]];y=sq[:,1].mean(); assert np.ptp(sq[:,1])<1e-7 and len(np.unique(sq,axis=0))==4
  delta=14*(hi[0]-lo[0])/122
  cov=[frac(t,lo,hi,y),frac(t,lo-delta,hi+delta,y)]
  ray_count=[positive_rays(t,lo,hi,y),positive_rays(t,lo-delta,hi+delta,y)]
  truth=0 if row['tag']=='far' else 1
  assert max(abs(x-truth) for x in cov)<1e-7 and ray_count==[169*truth,169*truth]
  got.append({'tag':row['tag'],'xyz_distance_m':row['distance'],'animation':row['animation'],'t_seconds':row['animation_t'],
   'native_and_guard_orthonormal_coverage':cov,'native_and_guard_169_ray_counts':ray_count,'cpu_array_sha256':sh(raw_file)})
 report[k]=got
print(json.dumps({'assets_and_routes_verified':True,'actual_66_joint_surface_control':report},indent=2,sort_keys=True))
