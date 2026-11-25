"""Independent strict surface-crossing witness; not contact/apparel approval."""
import gzip,hashlib,json,pathlib,struct,sys
import numpy as np
repo=pathlib.Path(sys.argv[1])
trace=pathlib.Path(sys.argv[2])
assert hashlib.sha256(trace.read_bytes()).hexdigest()=='55b34b3e4d5041b4b8777e20d5f3f9b2f7a05aa6c239b02bad249218d1d4fe4f'
P={'hero':'9d11c756195ffaac649b7f4c01d80f29d50dfec1','axe':'9d7ab5e3cbb42f64b3ce0451e6e5171954dc172e','pickaxe':'f6e12004a1bcc261df842f3dc758fdabd4cd269f'}
def open_glb(p,key):
 b=(repo/p).read_bytes()
 assert hashlib.sha1(f'blob {len(b)}\0'.encode()+b).hexdigest()==P[key]
 n=struct.unpack_from('<I',b,12)[0]
 return json.loads(b[20:20+n]),b[28+n:]
def read(g,i):
 j,b=g; a=j['accessors'][i];v=j['bufferViews'][a['bufferView']]
 dt=np.dtype({5121:'u1',5123:'<u2',5125:'<u4',5126:'<f4'}[a['componentType']])
 count={'SCALAR':1,'VEC3':3,'VEC4':4,'MAT4':16}[a['type']]
 return np.ndarray((a['count'],count),dtype=dt,buffer=b,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',count*dt.itemsize),dt.itemsize)).copy()
def mat(o):
 m=np.eye(4)
 m[:3,:3]=np.stack([o[k] for k in 'xyz'],axis=1);m[:3,3]=o['origin']
 return m
def points(v,m):
 return v @ m[:3,:3].T + m[:3,3]
def hit(te,tf):
 # Möller–Trumbore on oriented segment, exclude grazing or coplanar contact.
 # Return paired-row boolean for strict edges crossing a strict triangle interior.
 a,b,c=np.transpose(tf,(1,0,2)); b=b-a;c=c-a
 flags=np.zeros(len(te),dtype=bool)
 for i in range(3):
  p=te[:,i]; d=te[:,(i+1)%3]-p;h=np.cross(d,c)
  dot=lambda x,y:np.einsum('ij,ij->i',x,y)
  den=dot(b,h); ok=np.abs(den)>1e-13
  s=p-a; q=np.cross(s,b)
  u=np.divide(dot(s,h),den,out=np.zeros_like(den),where=ok);v=np.divide(dot(d,q),den,out=np.zeros_like(den),where=ok);t=np.divide(dot(c,q),den,out=np.zeros_like(den),where=ok)
  tol=1e-7
  flags|=ok&(u>tol)&(v>tol)&(u+v<1-tol)&(t>tol)&(t<1-tol)
 return flags
def crossings(a,b):
 # AABB broadphase on memory-bounded sash; strict crossing in both directions.
 bmin,bmax=b.min(axis=1),b.max(axis=1); result=[]
 for start in range(0,len(a),256):
  av=a[start:start+256]
  la,lb=np.where(np.all((av.min(axis=1)[:,None,:]<=bmax)&(av.max(axis=1)[:,None,:]>=bmin),axis=2))
  x,y=av[la],b[lb]; h=hit(x,y)|hit(y,x)
  result.extend(zip((la[h]+start).tolist(),lb[h].tolist()))
 return result
a=np.array([[[-1.,-1,0],[1,-1,0],[0,1,0]]])
b=np.array([[[0.,-0.25,-1],[0,-0.25,1],[0,0.55,1]]])
assert crossings(a,b)==[(0,0)] and crossings(a,b+[10.,0,0])==[] and crossings(a,a)==[]
head=None; rows=[]; verdict=None
with gzip.open(trace,'rt') as f:
 for line in f:
  kind,payload=line.split(' ',1); d=json.loads(payload)
  if kind=='GRIP_HEADER':head=d
  if kind=='GRIP_SAMPLE':rows.append(d)
  if kind=='GRIP_VERDICT':verdict=d
assert head and verdict['samples']==len(rows)==36 and not verdict['failures']
hg=open_glb('assets/characters/Character1.glb','hero');doc=hg[0];skin=doc['skins'][0]
raw_bind=read(hg,skin['inverseBindMatrices']).reshape(-1,4,4).transpose(0,2,1)
native=head['hero_mesh_bindings'];assert len(native)==1
native=native[0]
bname=[doc['nodes'][i]['name'] for i in skin['joints']]
assert len(bname)==66 and bname==[r['bind_name'] for r in native['skin_binds']]
native_bind=np.array([mat(r['pose']) for r in native['skin_binds']])
assert np.max(np.abs(raw_bind-native_bind))<1e-6
bn_idx=np.array([head['bone_order'].index(n) for n in bname])
mesh=doc['meshes'][0]
assert [doc['materials'][p['material']]['name'] for p in mesh['primitives'][1:]]==['C1_leather','C1_cream','C1_boot','C1_sole']
attrs=mesh['primitives'][1]['attributes']; V=read(hg,attrs['POSITION']).astype(float)
J=read(hg,attrs['JOINTS_0']).astype(int); W=read(hg,attrs['WEIGHTS_0']).astype(float)
assert np.max(abs(W.sum(axis=1)-1))<1e-5
new_faces={}
for group,idx in [('glove',1),('wrist_cuff',2)]:
 F=read(hg,mesh['primitives'][idx]['indices']).reshape(-1,3)
 selected=[]
 for side in 'LR':
  # Explicit material and native named wrist/palm skin weights, excludes boot-top cuffs.
  permitted=[bname.index(side+'_Hand')] if group=='glove' else [bname.index(side+'_Hand'),bname.index(side+'_Forearm')]
  wt=np.sum(np.where(np.isin(J,permitted),W,0),axis=1)
  mask=np.min(wt[F],axis=1)>1-1e-6
  selected.append(mask)
  new_faces[group+'_'+side]=(F[mask],np.flatnonzero(mask))
 assert np.max(np.sum(selected,axis=0))==1
 if group=='glove':assert np.all(np.any(selected,axis=0))
tools={}
for id in ['axe','pickaxe']:
 g=open_glb(f'assets/tools/{id}.glb',id)
 assert len(g[0]['nodes'])==1 and set(g[0]['nodes'][0])=={'mesh','name'}
 p=g[0]['meshes'][0]['primitives'][0]
 vs=read(g,p['attributes']['POSITION']).astype(float)
 tf=read(g,p['indices']).reshape(-1,3)
 # Conservative lower/tool-region subsets constrained by original vertex coordinates.
 tools[id]=(vs[tf],(vs[tf][:,:,1].max(axis=1)<=-.029))
res=[]
for r in rows:
 if r['action'] not in ('carry','chop'): continue
 rig=mat(r['rig_world'])
 assert np.max(abs(rig-mat(r['hero_visuals'][0]['world'])))<1e-8
 pal=(np.array([mat(m) for m in r['rig_bone_poses']])[bn_idx]@native_bind)
 paired=np.einsum('vkij,vj->vki',pal[J,:,:],np.column_stack((V,np.ones(len(V)))))
 vs=points(np.sum(W[:,:,None]*paired,axis=1)[:,:3],rig)
 ts,is_low=tools[r['tool']]
 assert len(r['tool_visuals'])==1
 t=mat(r['tool_visuals'][0]['world'])
 left=np.array(r['anatomical_L']['origin']);right=np.array(r['anatomical_R']['origin'])
 axis=left-right;axis/=np.linalg.norm(axis)
 xx=np.cross(axis,[0,0,-1])
 if np.linalg.norm(xx)<.001:xx=np.cross(axis,[1,0,0])
 xx/=np.linalg.norm(xx)
 zz=np.cross(xx,axis);zz/=np.linalg.norm(zz)
 d=np.eye(4);d[:3,:3]=np.stack((xx,axis,zz),axis=1)
 assert abs(np.linalg.det(d[:3,:3])-1)<1e-8
 assert r['band_local_y']==[-.34,-.08]
 d[:3,3]=(left+right)/2-axis*np.mean(r['band_local_y'])+.08*xx
 mounted=points(ts.reshape(-1,3),t).reshape(-1,3,3)
 detached=points(ts.reshape(-1,3),d).reshape(-1,3,3)
 result={}
 for label,tw in [('native_baseline',mounted),('intrinsic_fixed_id',detached)]:
  result[label]={}
  for name,(faces,ids) in new_faces.items():
   cf=crossings(vs[faces],tw)
   if not res:assert not crossings(vs[faces],tw+[10.,0,0])
   counts={'strict_pairs_full_tool':len(cf),'strict_pairs_lower_haft_subset':sum(bool(is_low[j]) for i,j in cf)}
   if cf:counts['first_face_pairs']=[[int(ids[i]),j] for i,j in cf[:2]]
   result[label][name]=counts
 res.append({'action':r['action'],'phase':r['ratio'],'counterfactual_world':d.tolist(),'crossings':result})
summarized={}
for action in ['carry','chop']:
 summarized[action]={}
 for label in ['native_baseline','intrinsic_fixed_id']:
  summarized[action][label]={}
  for name in new_faces:
   summarized[action][label][name]={}
   for measure in ['strict_pairs_full_tool','strict_pairs_lower_haft_subset']:
    xs=[r['crossings'][label][name][measure] for r in res if r['action']==action]
    summarized[action][label][name][measure]={'phases_with_crossings':sum(x>0 for x in xs),'min_max_pairs':[min(xs),max(xs)]}
print(json.dumps({'source_pin':P,'bind_check':{'count':len(bname),'matrix_max_abs':float(np.max(np.abs(raw_bind-native_bind)))},'face_counts':{n:len(f) for n,(f,i) in new_faces.items()},'scope':'Read-only strict noncoplanar exact frozen carry/chop intersection counterfactual, unchanged source axe at intrinsic 1.0 instead of PR multiplier, fixed R-lower/L-upper, same midpoint translation/basis/80mm term, unchanged character. No penetration depth, pressure, enclosure, all-body sweep, or render approval.', 'results':summarized,'sample_rows':res},indent=2,sort_keys=True))
