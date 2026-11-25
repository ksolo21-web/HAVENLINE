from pathlib import Path
import ctypes as C, hashlib, json, re, subprocess, sys, math
import numpy as np
import struct
from collections import deque
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
dif=bind('GEOSDifference',ptr,ptr,ptr)
cov=bind('GEOSCovers',C.c_byte,ptr,ptr)
destroy=bind('GEOSGeom_destroy',None,ptr)
def pg(poly):return read(('POLYGON('+loop(np.asarray(poly))+')').encode())
def cover_safe(X,l,h):
 e=pg(rect(l,h)); z=cov(X,e);destroy(e);assert z in (0,1);return bool(z)
def die_overlap(X,l,h):
 e=pg(rect(l,h)); z=inter(X,e); area0=garea(z);destroy(e);destroy(z); return area0
repo, workp = sys.argv[1:3]; work=Path(workp)
rev='11c14a1c41971067c7dc97db69375f720a408f68'
blob=subprocess.check_output(['git','-C',repo,'show',rev+':HavenlineLevel1/assets/studio/purchase_pad_v5.glb'])
assert hashlib.sha256(blob).hexdigest()=='d938ed53778f135359d4a345603a84353a7d02daddc0ff6e389453101119b7cb'
js=struct.unpack_from('<I',blob,12)[0]; gl=json.loads(blob[20:20+js]); buf=memoryview(blob)[28+js:]
def a(i):
 ac=gl['accessors'][i]; bv=gl['bufferViews'][ac['bufferView']]
 assert 'byteStride' not in bv and not ac.get('sparse')
 return np.frombuffer(buf,dtype={5126:'<f4',5123:'<u2',5125:'<u4'}[ac['componentType']],count=ac['count']*{'VEC3':3,'SCALAR':1}[ac['type']],offset=bv.get('byteOffset',0)+ac.get('byteOffset',0))
pr={n['name']:gl['meshes'][n['mesh']]['primitives'][0] for n in gl['nodes']}
vs={n:a(q['attributes']['POSITION']).reshape(-1,3) for n,q in pr.items()}
limit=np.concatenate(list(vs.values())); low,high=limit.min(0),limit.max(0);center=(low+high)/2
scale=float(.8/max((high-low)[[0,2]]))
sroof=vs['PurchaseDeck_Surface'][a(pr['PurchaseDeck_Surface']['indices']).reshape(-1,3)]
sroof=sroof[np.isclose(sroof[:,:,1],sroof[:,:,1].max(),atol=5e-8,rtol=0).all(1)]
assert len(sroof)==256
worldroof=(sroof[:,:,[0,2]]-center[[0,2]])*scale
deck=union(read(('MULTIPOLYGON('+','.join('('+loop(x)+')' for x in worldroof)+')').encode()))
lo0,hi0=worldroof.min((0,1)),worldroof.max((0,1))
G=deck
for k,v in vs.items():
 if not k.startswith('PurchaseCorner_'):continue
 box=(v[:,[0,2]]-center[[0,2]])*scale
 G=dif(G,pg(rect(box.min(0),box.max(0))))
# Existing BUILD label with guarded native footprint stays fixed.
npath=Path('../hvn-l1-v5-price-independent-v1.7ynPB9'); assert hashlib.sha256((npath/'SHA256SUMS').read_bytes()).hexdigest()=='d2e15b83e7ac9e0bea467bdf1f6c51ff0e925b08c1d24d11a1b52b0e7dd31dc9'
subprocess.run(['sha256sum','-c','--status','SHA256SUMS'],cwd=npath,check=True)
native=json.loads((npath/'base-native.json').read_text())
aa=native['label']['Action']; A=np.array(aa['triangles'])[:,[0,2]]; M=(A.max(0)[0]-A.min(0)[0])*14/aa['string_metrics'][0]
G=dif(G,pg(rect(A.min(0)-M,A.max(0)+M)))
limits={'deck':garea(deck),'after_existing_art_and_label_exclusions':garea(G)}
p=Path('../hvn-l1-v5-ordinary-south-v1')
assert hashlib.sha256((p/'SHA256SUMS').read_bytes()).hexdigest()=='7480ea02eba2e75c4a7a073e703470304d4e41f46bb9996285d7d4893146a38a'
subprocess.run(['sha256sum','-c','--status','SHA256SUMS'],cwd=p,check=True)
rows=json.loads((p/'result.json').read_text())
for entry in Path('source-surface-pins.txt').read_text().splitlines():
 sha,file=entry.split(); assert hashlib.sha256((work/file).read_bytes()).hexdigest()==sha
for mode in ('unfunded','funded'):
 for q in rows[mode]:
  tag=q['tag']
  if tag=='after':continue
  anc=np.array(q['anchor']); Y=np.array(q['quad'])[:,1].mean()-anc[1]
  ray=np.array(q['camera_back'])/q['camera_back'][1];rayxz=ray[[0,2]]
  dat=json.loads((work/mode/(tag+'.json')).read_text())
  t=np.concatenate([(np.array(r['positions'])-anc)[np.asarray(r['triangles']).reshape(-1,3)] for r in dat]); assert len(t)==96001
  occult,n=polys(t,Y,lo0,hi0,0)
  if n:G=dif(G,occult)
  limits[mode+'_'+tag]=garea(G)
# Branch-and-bound over continuous centers. A whole cell cannot work if the
# common intersection rectangle of all labels centered in it is itself blocked.
# Direct Covers finds exact geometric witness. Do not claim impossibility if
# any cells persist to the resolution limit.
cost=native['label']['Cost']; P=np.array(cost['triangles'])[:,[0,2]]; w=(P.max(0)-P.min(0)); up=float(np.linalg.norm(cost['px_axis_y_for_30'])/30*cost['glyph_texture_metrics'][0]['size'][1])
out={}
for key,factor in [('unchanged',1.),('price_trial_scale_with_3mm_clearance',.0050/.0032)]:
 half=(w+2*14*w[0]/122)*factor/2
 guard=.003 if key.startswith('price_trial') else 0.
 half+=guard
 recommended=(P.min(0)+P.max(0))/2
 Q=deque([(lo0+half,hi0-half)]); left=0; reject=0; witness=None
 while Q:
  l,h=Q.popleft();mid=(l+h)/2; delta=h-l
  if (delta<0).any():reject+=1;continue
  if (l+half>h-half).all() and not cover_safe(G,h-half,l+half):
   reject+=1;continue
  if cover_safe(G,mid-half,mid+half):witness=mid;break
  k=int(np.argmax(delta))
  if delta[k]<.0001:left+=1;continue
  u,v=l.copy(),h.copy(); u[k]=v[k]=mid[k]
  choices=[(l,v),(u,h)]
  choices.sort(key=lambda q:np.linalg.norm((q[0]+q[1])/2-recommended))
  Q.extendleft(reversed(choices))
 offsets=None
 if witness is not None and guard:
  # Preserve deck Y, orientation and move only the original Cost label.
  origin=recommended
  offsets=np.around((witness-origin)/scale+np.array([0.,.18]),6)
  checked=origin+(offsets-np.array([0.,.18]))*scale
  assert cover_safe(G,checked-half,checked+half)
 out[key]=dict(rounded_source_offsets=None if offsets is None else offsets.tolist(),additional_mm=1000*guard,full_support_size_m=(2*half).tolist(),witness=None if witness is None else witness.tolist(),unresolved_tiny_cells=left,rejected_cells=reject,first_glyph_atlas_height_px=up*factor)
print(json.dumps(dict(regions_m2=limits,search=out,deck_global_bounds_relative=[lo0.tolist(),hi0.tolist()],source_model_to_world=scale,raw_model_center=center.tolist(),original_price_center=((P.min(0)+P.max(0))/2).tolist()),indent=2))
