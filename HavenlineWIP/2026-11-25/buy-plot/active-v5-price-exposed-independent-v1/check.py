import hashlib,json,subprocess,sys,ctypes as C,struct
from pathlib import Path
import numpy as np
w,repo=map(Path,sys.argv[1:])
def sh(p):return hashlib.sha256(p.read_bytes()).hexdigest()
trial=Path('../hvn-l1-v5-price-exposed-fit-v1')
assert sh(trial/'SHA256SUMS')=='93475711ec9ede90409a5c2d52fb5912bcfcc2ce0bcd8ffae960ef82eab6afd6'
orig=Path('../hvn-l1-v5-ordinary-south-v1')
ref=Path('../hvn-l1-v5-price-independent-v1.7ynPB9')
assert sh(ref/'SHA256SUMS')=='d2e15b83e7ac9e0bea467bdf1f6c51ff0e925b08c1d24d11a1b52b0e7dd31dc9'
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
def label_box(l):
 t=np.array(l['triangles'])[:,[0,2]]
 return t.min(0),t.max(0)
build=json.loads((ref/'base-native.json').read_text())['label']['Action']
B0,B1=label_box(build); bmar=(B1[0]-B0[0])*14/build['string_metrics'][0];B0-=bmar; B1+=bmar
assert abs(in_roof(B0,B1)-1)<1e-7
rows={}
for mode in ('unfunded','funded'):
 A=w/'base'/mode; B=w/'candidate'/mode
 clean=lambda p:[json.loads(x[10:]) for x in p.read_text().splitlines() if x.startswith('PAD_ROUTE ')]
 a0,a1=clean(A/'log'),clean(B/'log'); assert len(a0)==len(a1)
 assert sh(A/'log')==sh(orig/(mode+'.log'))
 out=[]
 for x,y in zip(a0,a1):
  assert {k:v for k,v in x.items() if k!='quad'}=={k:v for k,v in y.items() if k!='quad'}
  k=x['tag']
  if k=='after':
   assert y['receipt']['typed_debit']=={'wood':3} and y['receipt']['revision']==1 and y['stock']==0 and y['camp'] and not y['visible'] and not y['pad_visible']
   out.append({'tag':k,'debit':y['receipt']['typed_debit'],'pad_hidden':True,'camp_visible':True})
   continue
  assert x['text']==y['text']=='3 WOOD'
  assert sh(A/(k+'.json'))==sh(B/(k+'.json'))
  t=np.concatenate([np.array(v['positions'])[np.array(v['triangles']).reshape(-1,3)] for v in json.loads((B/(k+'.json')).read_text())])
  assert len(t)==96001
  ray=np.array(y['camera_back']); ray/=np.linalg.norm(ray)
  ix=np.cross([0.,1.,0.],ray); ix/=np.linalg.norm(ix); screen=np.c_[ix,np.cross(ray,ix)]
  per={}
  for k0,rec in [('base',x),('candidate',y)]:
   sq=np.array(rec['quad']); lo=sq.min(0)[[0,2]];hi=sq.max(0)[[0,2]]
   h=sq[:,1].mean(); d=14*(hi[0]-lo[0])/122
   o=np.array(rec['anchor'])[[0,2]]
   assert abs(in_roof(lo-o-d,hi-o+d)-1)<1e-7
   if k0=='candidate':
    assert min(B0[1]-(hi-o+d)[1],.15)>.01
    if np.std(np.array(x['quad'])-sq,axis=0).max()>2e-6: raise AssertionError('not rigid label translation')
    assert abs(h-np.array(x['quad'])[:,1].mean())<1e-8
   cov=[frac(t,lo,hi,h),frac(t,lo-d,hi+d,h)]
   ray_ct=[positive_rays(t,lo,hi,h),positive_rays(t,lo-d,hi+d,h)]
   expect=k0=='base' and k!='far'
   assert max(abs(i-float(expect)) for i in cov)<1e-7 and ray_ct==[169*int(expect)]*2
   per[k0]={'coverage_quad_guard':cov,'positive_rays_quad_guard':ray_ct,'deck_roof_support_guard':True}
  out.append({'tag':k,'distance':y['distance'],'native0_vs_1':per,'actor_geometry_byte_identical':True})
 rows[mode]=out
print(json.dumps({'same_route_camera_actor_frames_and_ledger':True,'action_source_unchanged_guard_on_deck':True,'price_original_font_spacing_preserved':True,'samples':rows},indent=2,sort_keys=True))
