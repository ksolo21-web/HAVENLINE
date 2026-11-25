import hashlib,json,re,subprocess,sys,ctypes as C,struct
from pathlib import Path
import numpy as np
raw,repo=map(lambda x:Path(x).resolve(),sys.argv[1:])
def sh(x):return hashlib.sha256(x.read_bytes()).hexdigest()
prior=Path('../hvn-l1-v5-paid-pine-combined-v1')
assert sh(prior/'SHA256SUMS')=='950d1a8b9992596a7b56ec64c7c98fbe1c9d34c04e698a78fb0dfbc50db4b031'
p=(raw/'project/pad_v5_view.gd')
assert subprocess.check_output(['git','hash-object',str(p)],text=True).strip()=='a39b99e1c7c060eed80b469132d21a251b0b6f83'
p0=subprocess.check_output(['git','-C',str(repo),'show','11c14a1c:HavenlineLevel1/pad_v5_view.gd'])
assert p.read_bytes()==p0.replace(b'_cost = _new_label("Cost", 0.18, 0.0032)',b'_cost = _new_label("Cost", -0.362559, 0.0032)\n\t_cost.position.x = 0.682963')
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
# Independent original deck fit based on indexed GLB data, not bounding box.
s=subprocess.check_output(['git','-C',str(repo),'show','11c14a1c:HavenlineLevel1/assets/studio/purchase_pad_v5.glb'])
assert hashlib.sha256(s).hexdigest()=='d938ed53778f135359d4a345603a84353a7d02daddc0ff6e389453101119b7cb'
n=struct.unpack_from('<I',s,12)[0];g=json.loads(s[20:20+n]);binary=memoryview(s)[28+n:]
def a(i):
 y=g['accessors'][i];v=g['bufferViews'][y['bufferView']];off=v['byteOffset']+y.get('byteOffset',0)
 fmt='fff' if y['componentType']==5126 else 'H' if y['componentType']==5123 else 'I'
 return np.asarray(list(struct.iter_unpack('<'+fmt,binary[off:off+struct.calcsize('<'+fmt)*y['count']])))
V={};IX={}
for item in g['nodes']:
 assert set(item)=={'mesh','name'}
 p=g['meshes'][item['mesh']]['primitives'][0]; name=item['name']; V[name]=a(p['attributes']['POSITION']); IX[name]=a(p['indices']).reshape(-1,3)
allv=np.vstack(list(V.values())); mn,mx=allv.min(0),allv.max(0)
fit=.80/max((mx-mn)[[0,2]])
deck=V['PurchaseDeck_Surface'][IX['PurchaseDeck_Surface']]; roof=deck[:,:,1].max()
q=((deck[deck[:,:,1].min(1)>=roof-1e-4/fit]-(mn+mx)/2)*fit)[:,:,[0,2]]
q=q[np.abs(cross2(q[:,1]-q[:,0],q[:,2]-q[:,0]))>1e-15]
assert len(q)==256
hardroof=uni(read(('MULTIPOLYGON('+','.join(map(disk,q))+')').encode()))
def rect(lo,hi):
 return read(('POLYGON '+disk(np.array([lo,[hi[0],lo[1]],hi,[lo[0],hi[1]]]))).encode())
def in_roof(lo,hi):
 t=rect(lo,hi)
 return ar(inter(t,hardroof))/ar(t)
logs={k:(raw/k/'log').read_text() for k in ('funded','cold')}
for s in logs.values(): assert not re.search(r'ERROR|WARNING|FAIL',s)
counts={k:sum(r.startswith('PASS ') for r in s.splitlines()) for k,s in logs.items()}
assert counts=={'funded':33,'cold':3} 
for lock in ('one +1 original pine occurrence','rooted at tick 300','East gate physical outward traversal','South gate physical return traversal'):
 assert lock in logs['funded']
assert 'imports one existing paid cut, not duplicated' in logs['cold']
records=[json.loads(r[10:]) for r in logs['funded'].splitlines() if r.startswith('PAD_ROUTE ')]
summ=[]
prior_row=next(json.loads(j[10:]) for j in (prior/'funded.log').read_text().splitlines() if j.startswith('PAD_ROUTE ') and '"tag":"moving"' in j)
guard0=None; paired_fail_control=False
for r in records:
 tag=r['tag']
 if tag=='after':
  assert r['receipt']=={'grant':'center-hearth','offer':'center-hearth','revision':1,'typed_debit':{'wood':3}} and r['stock']==0 and r['camp'] and not r['visible'] and not r['pad_visible']
  continue
 assert r['stock']==3 and r['receipt']=={} and not r['camp'] and r['visible'] and r['pad_visible'] and r['text']=='3 WOOD'
 assert .72<r['distance'] and abs(r['feet'][0]-r['anchor'][0])<.01 and r['camera_projection']==1 and r['camera_size']==13.
 ray=np.array(r['camera_back']); ray/=np.linalg.norm(ray)
 ix=np.cross([0.,1.,0.],ray);ix/=np.linalg.norm(ix);screen=np.c_[ix,np.cross(ray,ix)]
 sq=np.array(r['quad']); lo=sq.min(0)[[0,2]];hi=sq.max(0)[[0,2]]; y=sq[:,1].mean()
 o=np.array(r['anchor'])[[0,2]]; d=14*(hi[0]-lo[0])/122
 assert np.ptp(sq[:,1])<1e-7 and abs(in_roof(lo-o-d,hi-o+d)-1)<1e-8
 for k0,vs in V.items():
  if not k0.startswith('PurchaseCorner_'):continue
  vl=((vs-(mn+mx)/2)*fit)[:,[0,2]]
  ia=ar(inter(rect(lo-o-d,hi-o+d),rect(vl.min(0),vl.max(0))))
  assert ia<1e-10
 mesh=raw/'funded'/(tag+'.json')
 geo=np.concatenate([np.array(v['positions'])[np.array(v['triangles']).reshape(-1,3)] for v in json.loads(mesh.read_text())]);assert len(geo)==96001
 quad=frac(geo,lo,hi,y);guard=frac(geo,lo-d,hi+d,y)
 rays=[positive_rays(geo,lo,hi,y),positive_rays(geo,lo-d,hi+d,y)]
 if r['tick']==prior_row['tick']:
  assert all(prior_row[k]==r[k] for k in r if k not in ('quad','tag'))
  assert sh(mesh)=='eeda1086089dfc30e3d96cfc5c04eae35b4438d56a8871aaa7e108ada091a5c0'
  old=np.array(prior_row['quad']); old_lo=old.min(0)[[0,2]]; old_hi=old.max(0)[[0,2]]
  oc=frac(geo,old_lo,old_hi,y)
  assert abs(oc-.470472309)<1e-6
  paired_fail_control=True
 if tag.startswith('run-'): assert r['animation']=='l1_hero_preview/run'
 summ.append({'tag':tag,'motion':r['animation'],'phase_seconds':r['animation_t'],'distance_m':r['distance'],'native_and_guard_occlusion':[quad,guard],'native_and_guard_rays_of_169':rays,'cpu_pose_hash':sh(mesh)})
assert paired_fail_control
moving=[x for x in summ if x['tag'].startswith('run-')];assert len(moving)>=4
worst=max(moving,key=lambda x:max(x['native_and_guard_occlusion']))
print(json.dumps({'funded_cold_pass_counts':counts,'paired_same_run_previous_price_failure_confirmed':paired_fail_control,
 'motion_captures':len(moving),'worst_motion':worst,'samples':summ,'pin':'11c14a1c exact replacement+same paid pine'},sort_keys=True,indent=2))
