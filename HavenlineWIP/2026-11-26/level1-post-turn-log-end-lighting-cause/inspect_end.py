"""Existing native raster and source geometry diagnosis, not a render or pose variant."""
from pathlib import Path
import contextlib,io
P0=Path(__file__).resolve().parent.parent
TURN=P0/'hvn-l1-carry-turn-crown-clearance-v1'
with contextlib.redirect_stdout(io.StringIO()):
 exec((TURN/'sweep.py').read_text().split('rows=[];prev=None')[0])
from PIL import Image
from scipy.ndimage import binary_erosion
S=P/'hvn-l1-crown-bark-only-appearance-stage-v1'
E=S/'graphics-evidence.8KFAMg9O'
pins={'bark-only-result.json':'8476f54fb16cd1c57f61ac5fa008108484da9d9e7c128b0dbf25c1bfc9c2be60',
'one_flag/passive.log':'b3ea6ce065ceb997924d169a747204e6461a0dd765c4c2ea6418168ad4bb9347',
'one_flag/palette.json':'d9f1a3ea48a0b9d39093891508a653438fde42d39f8eaa30f835ee73f400aa12',
'stock/passive.log':'893e9399ad78325c90cecdca9bbc17aaf185c76b52fe1188beb77b0f31eca124'}
assert all(sha(E/n)==h for n,h in pins.items())
assert (E/'one_flag/palette.json').read_bytes()==(D/'palette.json').read_bytes()
def rec(mode):
 l=(E/mode/'passive.log').read_text()
 assert 'CARRY_PASSIVE_REJECT' not in l
 o,=[json.loads(a) for a in re.findall(r'^CARRY_APPEARANCE (.+)$',l,re.M)]
 assert o['mode']=='virtual_crown'
 assert all(sha(E/mode/f"frame-{t}.png")==h for t,h in o['images'].items())
 return {a['tick']:a for a in o['frames']}
o=rec('stock'); v=rec('one_flag')
g=GLB(A); node=next(z for z in g.j['nodes'] if z['name']=='Pickup LOD - Crown log')
raw=[]
for pr in g.j['meshes'][node['mesh']]['primitives']:
 ix=g.read(pr['indices']).reshape(-1,3)
 xyz=g.read(pr['attributes']['POSITION']).astype(float)[ix]
 normal=g.read(pr['attributes']['NORMAL']).astype(float)[ix]
 raw.append((xyz,normal))
assert [len(p[0]) for p in raw]==[1087,213]
ends=[raw[1][0].mean(1)[:,0]<0,raw[1][0].mean(1)[:,0]>0]
assert sum(map(np.count_nonzero,ends))==213
shape=(720,1280)
Y,X=np.mgrid[:720,:1280]
def project(t,k,p):
 q=(t-p)@k
 q[:,:,:2]=q[:,:,:2]*[720/13,-720/13]+[640,360]
 return q
def depth(q):
 m=np.full(shape,-np.inf);px(np.ascontiguousarray(q),len(q),m,shape[1],shape[0]);return m
def detail(q,n,wp):
 d=np.full(shape,-np.inf); N=np.full((*shape,3),np.nan); p=np.full((*shape,3),np.nan)
 for f,fn,fw in zip(q,n,wp):
  low=np.maximum(0,np.floor(f[:,:2].min(0)).astype(int));hi=np.minimum([1279,719],np.ceil(f[:,:2].max(0)).astype(int))
  if np.any(hi<low):continue
  qx=X[low[1]:hi[1]+1,low[0]:hi[0]+1]+.5-f[0,0];qy=Y[low[1]:hi[1]+1,low[0]:hi[0]+1]+.5-f[0,1]
  a,b=f[1:]-f[0]; det=a[0]*b[1]-b[0]*a[1]
  if abs(det)<1e-10:continue
  u=(qx*b[1]-qy*b[0])/det;w=(a[0]*qy-a[1]*qx)/det
  z=f[0,2]+u*a[2]+w*b[2]
  s=np.s_[low[1]:hi[1]+1,low[0]:hi[0]+1]
  ok=(u>=-1e-10)&(w>=-1e-10)&(u+w<=1+1e-10)&(z>d[s])
  d[s][ok]=z[ok]
  N[s][ok]=fn[0]+u[ok,None]*(fn[1]-fn[0])+w[ok,None]*(fn[2]-fn[0])
  p[s][ok]=fw[0]+u[ok,None]*(fw[1]-fw[0])+w[ok,None]*(fw[2]-fw[0])
 return d,N,p
def blocked(point,t,L):
 # To-light exact triangle ray, excluding same-surface +1mm wall guard.
 ux=np.cross(L,[0.,1.,0.]);ux/=np.linalg.norm(ux)
 uy=np.cross(L,ux)
 B=np.stack([ux,uy,L],axis=1)
 tab=t@B;ps=point@B
 lo,hi=tab.min(1),tab.max(1);E=tab[:,1]-tab[:,0];F=tab[:,2]-tab[:,0]
 det=E[:,0]*F[:,1]-F[:,0]*E[:,1]
 out=[]
 for p in ps:
  ix=np.flatnonzero((lo[:,0]<=p[0])&(hi[:,0]>=p[0])&(lo[:,1]<=p[1])&(hi[:,1]>=p[1])&(hi[:,2]>p[2]+.001)&(abs(det)>1e-10))
  A=tab[ix,0];dx,dy=(p-A)[:,:2].T
  w=(dx*F[ix,1]-dy*F[ix,0])/det[ix]
  e=(E[ix,0]*dy-E[ix,1]*dx)/det[ix]
  z=A[:,2]+w*E[ix,2]+e*F[ix,2]
  good=(w>=-1e-10)&(e>=-1e-10)&(e+w<=1+1e-10)&(z>p[2]+.001)
  out.append(float(min(z[good])-p[2]) if np.any(good) else None)
 return out
rows=[]
for r in data['rows']:
 t=r['tick']
 if t not in (128,129,142):continue
 common=v[t]; assert all(common[k]==o[t][k] for k in common if k not in {'scenario','rid','source_mesh_rid'})
 mb,mp=tr(r['mesh']); cb,cp=tr(common['prop_submitted_transform']);kb,kp=tr(common['camera'])
 L=-np.array(common['sun_direction']); L/=np.linalg.norm(L)
 bsh=sh[0]; src,ix,J,wt=bsh
 pal=np.array([M(s[1]) for s in r['pose_and_product_by_slot']])
 body=(np.einsum('nwij,nj,nw->ni',pal[J],src,wt)[:,:3]@mb.T+mp)[ix]
 h=depth(project(body,kb,kp))
 idx=np.linalg.inv(cb).T
 bark=raw[0][0]@cb.T+cp;barkd=depth(project(bark,kb,kp))
 worlds=raw[1][0]@cb.T+cp;normals=raw[1][1]@idx.T
 ends_only=[];cases=[]
 for mask in ends:
  w=worlds[mask];n=normals[mask]
  d,N,points=detail(project(w,kb,kp),n,w)
  ends_only.append((d,N,points))
 Aimg=np.array(Image.open(E/'stock'/f'frame-{t}.png').convert('RGB'),dtype=np.int16)
 Bimg=np.array(Image.open(E/'one_flag'/f'frame-{t}.png').convert('RGB'),dtype=np.int16)
 for i,(d,N,points) in enumerate(ends_only):
  other=ends_only[1-i][0]
  finite=np.isfinite(d)
  capture=finite&(np.maximum(other,barkd)+.001<d)
  body_visible=capture&(h+.001<d)
  interior=binary_erosion(body_visible,iterations=1)
  Ns=N[body_visible]; n=Ns/np.linalg.norm(Ns,axis=1)[:,None]
  dots=n@L;cam=n@kb[:,2]
  b=d[body_visible]
  self_occluders=np.concatenate([bark,worlds])
  to_body=blocked(points[body_visible],body,L); to_self=blocked(points[body_visible],self_occluders,L)
  A0=Aimg[interior];B0=Bimg[interior]
  cases.append(dict(source_end='x-negative' if i==0 else 'x-positive',
   actual_end_median_normal_world=np.median(n,axis=0).tolist() if len(n) else [],
   cap_source_triangle_count=int(ends[i].sum()),unoccluded_end_projection_px=int(finite.sum()),
   after_other_crown_surfaces_px=int(capture.sum()),stock_body_front_blocks_yx_px=int((capture&~body_visible).sum()),
   native_proxy_visible_face_px=int(body_visible.sum()),native_proxy_interior_safe_pixels=int(interior.sum()),
   camera_normal_dot_minmax=[float(cam.min()),float(cam.max())] if len(cam) else None,
   sun_normal_dot_minmax=[float(dots.min()),float(dots.max())] if len(dots) else None,
   to_sun_body_blocks=int(sum(p is not None for p in to_body)),to_sun_crown_self_geometric_blocks_cast_off=int(sum(p is not None for p in to_self)),
   native_bark_override_case_end_rgb_median=np.median(B0,axis=0).tolist() if len(B0) else None,
   native_end_same_in_stock_and_bark_only_max_rgb_delta=int(np.max(abs(B0-A0))) if len(A0) else None))
 rows.append(dict(tick=t,cases=cases,sun_toward_light_world=L.tolist(),camera_back_world=kb[:,2].tolist()))
print(json.dumps(dict(scope='offline exact native capture pixels with source modeled geometric pixel/depth/light rays; not GPU stencil or shadow proof',
 fixed_origin_unmodified=True,original_source_end_material_unchanged=True,zero_engine=True,rows=rows),indent=2))
