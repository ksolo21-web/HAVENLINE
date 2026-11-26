"""Read-only GLB intake. No rendering, edits to model, or extraction into its source folder."""
from hashlib import sha256
import io,json,struct
from pathlib import Path
import sys
import numpy as np
from PIL import Image
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree
p=Path(sys.argv[1]); raw=p.read_bytes()
assert sha256(raw).hexdigest()=="c5256ca7ac3956c91b19654076afa80b96fede20873be704136ab89edf4709b3"
assert struct.unpack_from('<4s2I',raw,0)==(b'glTF',2,len(raw))
n,t=struct.unpack_from('<2I',raw,12); assert t==0x4e4f534a
doc=json.loads(raw[20:20+n]); bn,bt=struct.unpack_from('<2I',raw,20+n); assert bt==0x004e4942
blob=memoryview(raw)[28+n:28+n+bn];assert doc['buffers']==[{'byteLength':bn}]
def view(i):
 q=doc['bufferViews'][i]; assert q['buffer']==0
 return blob[q.get('byteOffset',0):q.get('byteOffset',0)+q['byteLength']]
def decode(i):
 a=doc['accessors'][i]; n={'SCALAR':1,'VEC2':2,'VEC3':3}[a['type']]
 dt={5126:'<f4',5125:'<u4',5123:'<u2'}[a['componentType']]
 assert not a.get('sparse') and not a.get('normalized') and 'byteStride' not in doc['bufferViews'][a['bufferView']]
 return np.frombuffer(view(a['bufferView']),dtype=dt,count=a['count']*n,offset=a.get('byteOffset',0)).reshape(-1,n)
assert len(doc['scenes'])==len(doc['nodes'])==len(doc['meshes'])==1
assert doc['scenes'][0]['nodes']==[0] and doc['nodes'][0]['matrix']==np.eye(4).ravel().tolist()
assert len(doc['meshes'][0]['primitives'])==1
pr=doc['meshes'][0]['primitives'][0]; assert pr['mode']==4
V=decode(pr['attributes']['POSITION']).astype(float)
NV=decode(pr['attributes']['NORMAL']).astype(float)
UV=decode(pr['attributes']['TEXCOORD_0']).astype(float)
F=decode(pr['indices']).reshape(-1,3).astype(np.int64)
assert F.max()<len(V) and not np.any(~np.isfinite(V))
T=V[F]; mins,maxs=V.min(0),V.max(0); span=maxs-mins
area=.5*np.linalg.norm(np.cross(T[:,1]-T[:,0],T[:,2]-T[:,0]),axis=1)
normal_agree=np.einsum('ij,ij->i',np.cross(T[:,1]-T[:,0],T[:,2]-T[:,0]),NV[F].mean(1))
assert np.all(area>0)
def aabb(P):return [np.round(P.min(0),8).tolist(),np.round(P.max(0),8).tolist()]
def connectivity(V,F,near=None):
 k=len(V)
 ip=F.ravel()
 jp=np.roll(F,1,axis=1).ravel()
 if near is not None and len(near):
  ip=np.concatenate((ip,near[:,0]));jp=np.concatenate((jp,near[:,1]))
 G=csr_matrix((np.ones(len(ip),np.uint8),(ip,jp)),shape=(k,k))
 _, labels=connected_components(G,directed=False,return_labels=True)
 assert np.all((labels[F]==labels[F[:,:1]]))
 fl=labels[F[:,0]]; ct=np.bincount(fl)
 order=np.argsort(ct)[::-1]
 ans=[]
 for i in order[:30]:
  if not ct[i]:continue
  f=F[fl==i]; q=V[f]; bound=aabb(q.reshape(-1,3))
  ans.append(dict(triangles=int(ct[i]),positions=int(np.count_nonzero(labels==i)),bounds=bound,
      backs_or_front=str('both' if bound[0][2]<0<bound[1][2] else '+' if bound[0][2]>=0 else '-')))
 return {'components_with_triangles':int(np.count_nonzero(ct)),
         'components_with_100_plus_triangles':int(np.count_nonzero(ct>=100)),
         'unreferenced_vertices':int(len(V)-len(np.unique(F))),
         'total_triangles_outside_largest':int(len(F)-ct[order[0]]),'components':ans}, fl
A,fl=connectivity(V,F)
U,inv=np.unique(V,return_inverse=True,axis=0); W=inv[F]
B,wl=connectivity(U,W)
eps=1e-6; near=cKDTree(U).query_pairs(eps,output_type='ndarray'); C,_=connectivity(U,W,near)
edges=np.sort(np.vstack([W[:,[0,1]],W[:,[1,2]],W[:,[2,0]]]),axis=1)
UE,cnt=np.unique(edges,axis=0,return_counts=True)
# Proven connections across center seam and post/leaf zones in coordinate space.
# Owner's front framing places jamb transition near 12% / 88% of full width.
def crosses(x):
 mask=(T[:,:,0].min(1)<x)&(T[:,:,0].max(1)>x)
 q=T[mask]
 return {'triangles':int(mask.sum()),'area_mesh_units_squared':float(area[mask].sum()),
    'mesh_bbox_of_triangles':aabb(q.reshape(-1,3)) if len(q) else None,
    'triangles_below_top_rail_and_above_floor':int(np.count_nonzero(mask&(T[:,:,1].mean(1)>mins[1]+.12*span[1])&(T[:,:,1].mean(1)<mins[1]+.73*span[1]))),
    'low_mid_high_height_bin_counts':np.histogram(q[:,:,1].mean(1),bins=np.linspace(mins[1],maxs[1],12))[0].tolist()}
sections={n:dict(x=float(x),**crosses(x)) for n,x in [('center_at_zero',0.),('bounds_mid',float((mins[0]+maxs[0])/2)),('likely_left_post_end_12pct',mins[0]+.12*span[0]),('likely_right_post_end_88pct',mins[0]+.88*span[0])]}
# Stronger: require no X partition through the central seam neighborhood,
# not merely a cut slightly off-center. Such a partition would have zero face bridges.
center_trials=[len(T[(T[:,:,0].min(1)<x)&(T[:,:,0].max(1)>x)]) for x in np.linspace(-.07,.07,141)]
# Normals/texture sample and morphology traits saved as non-visual hints, not a rendered art claim.
imgs=[]
for i in doc['images']:
 x=bytes(view(i['bufferView']))
 with Image.open(io.BytesIO(x)) as im:
  imgs.append({'mime':i['mimeType'],'bytes':len(x),'pixels':list(im.size),'sha256':sha256(x).hexdigest()})
res={'file':str(p.name),'sha256':sha256(raw).hexdigest(),'file_bytes':len(raw),'glTF_version':doc['asset']['version'],
 'world_position_identity':True,'node_mesh_primitive_material_counts':[len(doc[k]) for k in ('nodes','meshes')]+[len(doc['meshes'][0]['primitives']),len(doc['materials'])],
 'skin_animation_morph_target_count':[len(doc.get(k,[])) for k in ('skins','animations')]+[len(pr.get('targets',[]))],
 'positions':len(V),'exact_position_welded_positions':len(U),'triangles':len(F),
 'normal_geometric_direction_agrees_count':int(np.count_nonzero(normal_agree>0)),
 'bounds_world':aabb(V),'span_world':span.tolist(),'material_contract':doc['materials'][0],'embedded_images':imgs,
 'indexed_connectivity':A,'exact_coincident_position_connectivity':B,'within_1e_6_unit_connectivity':C,
 'near_position_pairs_excluding_exact_duplicates':len(near),
 'unique_exact_weld_edges':len(UE),'exact_weld_edge_incidence_histogram':dict(zip(*[v.tolist() for v in np.unique(cnt,return_counts=True)])),
 'cross_sections':sections,'bridge_triangles_min_max_for_141_center_cuts_minus_point07_plus_point07':[int(min(center_trials)),int(max(center_trials))]}

# Axis-aligned orthographic XY depth probes: sample geometry only, no rendered image.
# Partition by projected bounding boxes so all candidate triangles are tested.
# Quantify both face profiles with no assumptions about which sign Meshy selected as front.
N=85; M=53
xs=np.linspace(-.73,.73,N); ys=np.linspace(-.48,.20,M)
q0=T[:,:,:2].min(1);q1=T[:,:,:2].max(1)
x_a=np.clip(np.searchsorted(xs,q0[:,0]),0,N)
x_b=np.clip(np.searchsorted(xs,q1[:,0],side="right"),0,N)
y_a=np.clip(np.searchsorted(ys,q0[:,1]),0,M)
y_b=np.clip(np.searchsorted(ys,q1[:,1],side="right"),0,M)
cells=[[] for _ in range(N*M)]
for j in np.flatnonzero((x_a<x_b)&(y_a<y_b)):
 for iy in range(y_a[j],y_b[j]):
  for ix in range(x_a[j],x_b[j]): cells[iy*N+ix].append(j)
png=doc['images'][doc['textures'][doc['materials'][0]['pbrMetallicRoughness']['baseColorTexture']['index']]['source']]
with Image.open(io.BytesIO(bytes(view(png['bufferView'])))) as im: tex=np.asarray(im.convert("RGB"))
def uv_color(val):
 return tex[min(int(val[1]*tex.shape[0]),tex.shape[0]-1),min(int(val[0]*tex.shape[1]),tex.shape[1]-1)]
data=[]
for iy,y in enumerate(ys):
 for ix,x in enumerate(xs):
  ids=np.asarray(cells[iy*N+ix],np.int64)
  if not len(ids):continue
  S=T[ids];u=S[:,1,:2]-S[:,0,:2];v=S[:,2,:2]-S[:,0,:2];w=[x,y]-S[:,0,:2]
  den=u[:,0]*v[:,1]-u[:,1]*v[:,0]; non=abs(den)>1e-12
  ids=ids[non];S=S[non];u=u[non];v=v[non];w=w[non];den=den[non]
  a=(w[:,0]*v[:,1]-w[:,1]*v[:,0])/den;b=(u[:,0]*w[:,1]-u[:,1]*w[:,0])/den
  hit=(a>=-1e-7)&(b>=-1e-7)&(a+b<=1+1e-7)
  if not hit.any():continue
  a,b,S,ids=a[hit],b[hit],S[hit],ids[hit]
  z=S[:,0,2]+a*(S[:,1,2]-S[:,0,2])+b*(S[:,2,2]-S[:,0,2])
  ans=[x,y]
  for j in (np.argmax(z),np.argmin(z)):
   i=ids[j];t=UV[F[i]];uv=t[0]+a[j]*(t[1]-t[0])+b[j]*(t[2]-t[0])
   rgb=uv_color(uv)
   ans.extend([z[j],*rgb])
  data.append(ans)
D=np.asarray(data)
def profile(is_right):
 # Model at local extents of interior leaf, not a claim of semantically segmented boards.
 x,y=D[:,:2].T
 u=(x-.04)/.65 if is_right else (-x-.04)/.65
 v=(y+.40)/.52
 inside=(u>.12)&(u<.87)&(v>.13)&(v<.88)
 dist=np.minimum(abs(u-v),abs(u+v-1))
 diag=inside&(dist<.11); other=inside&(dist>.19)
 def stats(mask,s):
  col,zidx=(2,2) if s=='positive' else (6,6)
  z=D[mask,zidx]*(1 if s=='positive' else -1)
  color=D[mask,col+1:col+4]
  return {'samples':int(mask.sum()),'depth_median':float(np.median(z)),
   'depth_p10_p90':np.percentile(z,[10,90]).tolist(),'atlas_median_encoded_RGB':np.median(color,axis=0).tolist()}
 return {s:{'diagonal_band':stats(diag,s),'outside_diagonal_band':stats(other,s)} for s in ('positive','negative')}
res['normal_axis_depth_probe_non_visual']={'grid':{'x_samples':N,'y_samples':M,'bounds':[[-.73,-.48],[.73,.20]]},
  'covered_points':len(D),'left_interior':profile(False),'right_interior':profile(True),
  'limitations':'nominal diagonal coordinate bands; not segmentation, not a rendered result or owner acceptance. Texture RGB nearest on the raw atlas.'}
print(json.dumps(res,indent=2,sort_keys=True))
