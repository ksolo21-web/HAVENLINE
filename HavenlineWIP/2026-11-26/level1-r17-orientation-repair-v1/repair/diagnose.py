"""Read-only source donor geometry and exact desktop frame diagnosis."""
from pathlib import Path
from collections import defaultdict,Counter
from io import BytesIO
import hashlib,struct,json
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from PIL import Image
D=Path('../hvn-level1-r17-fence-view-v1').resolve()
E=Path('../hvn-level1-r17-admission-v1/graphics-evidence.GvhVsTIb').resolve()
REF=Path('../havenline-ref-audit/t03-old/18595.png').resolve()
H=lambda b:hashlib.sha256(b).hexdigest()
for row in (D/'SHA256SUMS').read_text().splitlines():
 h,n=row.split();assert H((D/n).read_bytes())==h
G=json.loads((E/'frame-evidence.json').read_text()); R=(E/'paid-first-frame.png').read_bytes()
assert H(R)==G['frames']['paid-first-frame']['png_sha256']
def parse(name):
 lines=(D/'assets'/name).read_text().splitlines()
 v=[];n=[];f=[];norm=[];m=[];sel=None
 for l in lines:
  a=l.split()
  if not a:continue
  if a[0]=='v':v.append(tuple(map(float,a[1:])))
  if a[0]=='vn':n.append(tuple(map(float,a[1:])))
  if a[0]=='usemtl':sel=a[1]
  if a[0]=='f':
   ff,nn=zip(*[(int(x.split('/')[0])-1,int(x.split('/')[-1])-1) for x in a[1:]])
   assert len(ff)==3
   f.append(ff);norm.append(nn);m.append(sel)
 return list(map(np.asarray,(v,n,f,norm,m)))
def face_audit(V,N,F,T,mat):
 X=V[F]; cn=np.cross(X[:,1]-X[:,0],X[:,2]-X[:,0]); ln=np.linalg.norm(cn,axis=1);assert np.min(ln)>1e-12
 norm=cn/ln[:,None]
 actual=N[T]; dots=np.einsum('ni,nji->nj',norm,actual)
 stored=actual.mean(1)
 prism={}
 for key in np.unique(mat):
  rows=np.flatnonzero(mat==key)
  prism[key]=dict(total=len(rows),normal_vs_raw_obj_corner_dot_min=float(dots[rows].min()),
        vertex_y_bounds=[float(X[rows,:,1].min()),float(X[rows,:,1].max())],
        unique_direction_vectors=len(np.unique(actual[rows].reshape(-1,3),axis=0)))
 return X,norm,stored,prism
def comps(V,F):
 unique,inv=np.unique(V,axis=0,return_inverse=True);t=inv[F]
 edges=np.concatenate([t[:,[0,1]],t[:,[1,2]],t[:,[2,0]]])
 g=coo_matrix((np.ones(len(edges),dtype='b'),(edges[:,0],edges[:,1])),shape=(len(unique),len(unique))).tocsr()
 k,L=connected_components(g,directed=False)
 return inv,t,L[t[:,0]]
def jnorm(pitch,yaw):
 # Godot's YXZ Euler with no roll. DirectionalLight emits along local
 # -Z, hence source-to-sun shading direction is world basis +Z.
 i,j=np.deg2rad([pitch,yaw])
 return np.array([np.sin(j)*np.cos(i),-np.sin(i),np.cos(j)*np.cos(i)])
sun=jnorm(-48,-28)
cam=np.array([7.,11.,11.]);cam/=np.linalg.norm(cam)
result={}
for n in ('fence_panel.obj','gate_post.obj'):
 V,N,F,T,mat=parse(n);X,norm,stored,by=face_audit(V,N,F,T,mat)
 weld,tf,L=comps(V,F)
 cc=[]
 for k in np.unique(L):
  ids=np.flatnonzero(L==k)
  q=X[ids]
  b0=q.reshape(-1,3).min(0);b1=q.reshape(-1,3).max(0);center=(b0+b1)*.5
  # Raw OBJ wind conventions geometry, irrespective of importer face
  # swap for Godot CW. Signed closed-component volume distinguishes
  # interior surfaces, whereas flat/overlapping groups need qualification.
  faces=[tuple(x) for x in tf[ids]]
  ec=Counter(tuple(sorted((int(a),int(b)))) for t in faces for a,b in zip(t,np.roll(t,-1)))
  sign_vol=np.einsum('ni,ni->n',q[:,0]-center,np.cross(q[:,1]-center,q[:,2]-center)).sum()/6.
  dot=(stored[ids]*(q.mean(1)-center)).sum(1)
  cc.append(dict(face_count=len(ids),surface_counts=dict(Counter(mat[ids].tolist())),non_two_sided_edges=int(sum(v!=2 for v in ec.values())),signed_raw_obj_volume=float(sign_vol),
      approximate_convex_face_outward_dot_counts={'positive':int((dot>1e-7).sum()),'negative':int((dot < -1e-7).sum())},
      x_range_m=[float(b0[0]),float(b1[0])],y_range_m=[float(b0[1]),float(b1[1])],
      z_range_m=[float(b0[2]),float(b1[2])]))
 def directional(d):
  axis=np.array(d); cr=np.cross(axis,[0,1.,0])
  bases=np.stack([axis*[1.,1.,1.], [0,1.,0], cr*(1.95 if n.startswith('fence') else 1.)],axis=1)
  assert np.linalg.det(bases)>0
  Nw=stored@np.linalg.inv(bases);Nw/=np.linalg.norm(Nw,axis=1)[:,None]
  hit=Nw@sun;fv=Nw@cam
  records={}
  for k in np.unique(mat):
   ok=(mat==k)&(fv>1e-7);records[k]={'if_normals_point_outward_camera_facing':int(ok.sum()),
     'if_normals_point_inward_visible_far_side':int(ok.sum()),
     'facing_normal_has_no_direct_sun':int((ok&(hit<=0)).sum()),
     'if_corrected_normal_unlit':int(((mat==k)&(fv<0)&(hit>=0)).sum())}
  return records
 result[n]=dict(sha256=H((D/'assets'/n).read_bytes()),source_materials=by,component_count=len(cc),
   ccw_volume_components=cc,source_direct_sun_and_cam_dot_for_x_z_wall=dict(WorldX=directional([1.,0,0]),WorldZ=directional([0,0,1.])))
pic=np.array(Image.open(BytesIO(R)).convert('RGB'));assert pic.shape==(720,1280,3)
# Fixed known bands visibly across top timber/shadow area, distinct from gate
# panel and HUD. Pixel tuple readout only, not a zone-normalization or render.
rois={}
for name,(x,y,w,h) in {'south_warm_strip':(430,238,83,64),'east_near_wall':(1000,205,96,87),'back_northeast_wall':(736,49,126,100),'flat_snow_context':(835,530,90,60)}.items():
 z=pic[y:y+h,x:x+w].reshape(-1,3);W=z.astype(float)
 rois[name]={'pixels':len(z),'exact_black_rgb':sum(int((v==0).all()) for v in z),
  'mid_timber_rgb_range_count':int(((W[:,0]>W[:,1]+8)&(W[:,1]>W[:,2]+4)&(W[:,0]>=35)).sum()),
  'minimum_srgb_component':int(z.min())}
print(json.dumps(dict(snapshot_sha256=H(R),reference_18595_sha256=H(REF.read_bytes()),
 rights_and_source_both_read_only=True,objects=result,direct_sun_world=sun.tolist(),normal_camera_direction=cam.tolist(),read_only_pixel_checks=rois,
 planned_no_runtime_or_candidate_update=True),indent=2))
