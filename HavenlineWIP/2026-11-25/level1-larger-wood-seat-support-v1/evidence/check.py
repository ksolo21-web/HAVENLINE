import argparse,json,hashlib,runpy
from pathlib import Path
import numpy as np
from scipy.spatial import ConvexHull
from scipy.spatial.transform import Rotation
from scipy.optimize import root
from PIL import Image,ImageDraw
G=lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
def clip(poly, other):
 for u,v in zip(other,np.roll(other,-1,axis=0)):
  d=v-u;out=[]
  for a,b in zip(poly,np.roll(poly,-1,axis=0)):
   da=d[0]*(a[1]-u[1])-d[1]*(a[0]-u[0]);db=d[0]*(b[1]-u[1])-d[1]*(b[0]-u[0])
   if da>=-1e-12:out.append(a)
   if (da>=-1e-12)!=(db>=-1e-12):out.append(a+(b-a)*(da/(da-db)))
  if not out:return []
  poly=np.array(out)
 return poly
p=argparse.ArgumentParser();[p.add_argument(i,type=Path) for i in ['mesh','frames','stage']];a=p.parse_args()
assert G(a.mesh)=='31378ac3c6b21fbc0fdcfe597333794a7fe8b36c628a53956ad6bc0956fd1554'
assert G(a.frames)=='c3f34aa549171d9dde0ca6c3fdf7f7f4baf938429e2a91f368c184f9388e64aa'
assert G(a.stage)=='51e34077a346b0f60951d9ee18c43276c82e8a9787af8f82cdf14a1a7f84c31e'
png=a.stage.parent/'paint-inlay.png'
assert G(png)=='9301e61ba2530431c0f1e3821fd9cc87a92e27bf4db50c40a86a62027b920cb1'
s=json.loads(a.stage.read_bytes());fr=json.loads(a.frames.read_bytes())['frames'][-1]
tr,_=runpy.run_path('hvn-l1-transfer-crown-spacing-v1/audit.py')['decode'](a.mesh)
original=np.unique(tr.reshape(-1,3),axis=0).astype(float)
local_center=.5*(original.min(0)+original.max(0));v=original-local_center
hull=ConvexHull(v)
F=np.array(s['faces']);V=np.array(s['vertices_godot']);UV=np.array(s['uv_gltf'])
surf=V[F];XZ=surf[:,:,[0,2]]
rev=np.linalg.det(XZ[:,1:]-XZ[:,0:1])<0
surf[rev]=surf[rev][:,[0,2,1]]
XZ=surf[:,:,[0,2]];Lo=XZ.min(1);Hi=XZ.max(1)
A=XZ[:,1:]-XZ[:,0:1];good=np.linalg.det(A)>1e-12
slopes=np.zeros((len(XZ),2))
slopes[good]=np.linalg.solve(A[good],(surf[good,1:,1]-surf[good,0:1,1])[...,None]).squeeze(-1)
def candidates(X):
 return np.flatnonzero(good&np.all(Hi>=X.min(0)-1e-12,axis=1)&np.all(Lo<=X.max(0)+1e-12,axis=1))
def height(X):
 out=[]
 for q in X:
  i=candidates(q[None,:]);D=XZ[i,1:]-XZ[i,0:1]
  w=np.linalg.solve(np.swapaxes(D,1,2),(q-XZ[i,0])[...,None]).squeeze(-1)
  i=i[np.all(w>=-1e-9,axis=1)&(w.sum(1)<=1+1e-9)]
  assert len(i)
  out.append(surf[i[0],0,1]+(q-XZ[i[0],0])@slopes[i[0]])
 return np.array(out)
def min_gap(points, facets=None):
 out=[];tested=0
 for t in (points[hull.simplices] if facets is None else facets):
  x=t[:,[0,2]]
  d=x[1:]-x[0]
  if abs(np.linalg.det(d))<1e-13:continue
  m=np.linalg.solve(d,t[1:,1]-t[0,1])
  for i in candidates(x):
   z=clip(x,XZ[i])
   if not len(z):continue
   tested+=len(z)
   out.append(float(np.min(t[0,1]+(z-x[0])@m-surf[i,0,1]-(z-XZ[i,0])@slopes[i])))
 return min(out),tested
def xy(points):
 o,r,u,_=np.array(fr['camera']);b=(points-o)@np.c_[r,-u]*(720/13)
 return b+[640,360]
results=[]; polys=[]; triangles=[]
for k,T in enumerate(fr['crowns']):
 center,*R=np.array(T);R=np.array(R); old=original@R+center
 old_gaps=old[:,1]-height(old[:,[0,2]])
 pick=np.argsort(np.abs(old_gaps))[:3]
 bc=center+[-.065 if k==0 else .065,0,0]
 Q=(3.5227541825679687*v@R)
 def restore(d,P=Q):
  return P@Rotation.from_rotvec([d[0],0,d[1]]).as_matrix().T+bc+[0,d[2],0]
 def zero(d):
  x=restore(d,Q[pick]);return x[:,1]-height(x[:,[0,2]])
 fit=root(zero,[0,0,.1],tol=1e-10); assert max(abs(zero(fit.x)))<1e-8
 w=restore(fit.x); mingap,n=min_gap(w)
 faces_3d=restore(fit.x,(3.5227541825679687*(tr-local_center)@R).reshape(-1,3)).reshape(-1,3,3)
 triangles.append(faces_3d)
 actual_gap,n_actual=min_gap(w,faces_3d)
 sample=xy(w);polys.append(sample[ConvexHull(sample).vertices])
 old_min,_=min_gap(old)
 results.append({'age':266,'old_rest_center_m':center.tolist(),'old_min_full_hull_gap_m':old_min,
  'original_3_contacts_error_m':old_gaps[pick].tolist(),'draft_contact_fit_residual_m':zero(fit.x).tolist(),
  'convex_hull_full_visible_gap_m':mingap,'convex_hull_overlay_vertices_tested':n,
  'actual_mesh_visible_gap_m':actual_gap,'actual_mesh_overlay_vertices_tested':n_actual,
  'collision_base_clearance_m':mingap+.012,
  'draft_support_contact_vertices':pick.tolist(),'draft_rotvec_pitch_roll_deg':np.degrees(fit.x[:2]).tolist(),
  'draft_additional_y_m':float(fit.x[2]),'draft_x_bounds_m':[w[:,0].min(),w[:,0].max()],
  'screen_hero_same_camera':True,'draft_screen_log_major_diameter_px':float(np.sqrt(np.max(np.sum((polys[-1][:,None]-polys[-1][None,:])**2,axis=2)))),
  'draft_screen_bounds_px':[sample.min(0).tolist(),sample.max(0).tolist()]})
# Map actual icon texture pixels to the log marker surface. UV polygon is
# inset away from border; segment high/low intensity from base brown in
# a central crop (unique component can be visually reconfirmed).
vp=np.unique(F[np.array(s['material_ids'])==1]); a2=np.linalg.lstsq(np.c_[UV[vp],np.ones(len(vp))],V[vp][:,[0,2]],rcond=None)[0]
assert np.max(np.abs(np.c_[UV[vp],np.ones(len(vp))]@a2-V[vp][:,[0,2]]))<1e-7
tex=np.array(Image.open(png).convert('RGB')); selector=np.zeros(tex.shape[:2],bool)
selector[300:740,475:845]=True
# Dark outline max R<=65 and fill R>=105; brown background R between 65 and 105.
selector&=(tex[:,:,0]<=65)|(tex[:,:,0]>=105)
yy,xx=np.nonzero(selector);q=np.c_[(xx+.5)/tex.shape[1],(yy+.5)/tex.shape[0],np.ones(len(xx))]@a2
# Piecewise-linear surface evaluation without per-pixel loops.
H=np.full(len(q),np.nan)
for i in candidates(q):
 sel=np.flatnonzero(np.isnan(H)&np.all(q>=Lo[i]-1e-12,axis=1)&np.all(q<=Hi[i]+1e-12,axis=1))
 if not len(sel):continue
 D=XZ[i,1:]-XZ[i,0:1]
 w=(q[sel]-XZ[i,0])@np.linalg.inv(D)
 sel=sel[np.all(w>=-1e-9,axis=1)&(w.sum(1)<=1+1e-9)]
 H[sel]=surf[i,0,1]+(q[sel]-XZ[i,0])@slopes[i]
assert np.isfinite(H).all()
icon_world=np.c_[q[:,0],H,q[:,1]]
icon=xy(icon_world)
back=np.array(fr['camera'])[3]
icon_depth=icon_world@back
def occlusion(t, p):
 proj=xy(t.reshape(-1,3)).reshape(-1,3,2);z=t@back
 out=np.zeros(len(p),bool)
 for T,D in zip(proj,z):
  E=T[1:]-T[0]
  if abs(np.linalg.det(E))<=1e-12:continue
  choose=np.flatnonzero((~out)&np.all(p>=T.min(0),axis=1)&np.all(p<=T.max(0),axis=1))
  if not len(choose):continue
  w=(p[choose]-T[0])@np.linalg.inv(E)
  d=(D[0]+w@(D[1:]-D[0]))-icon_depth[choose]
  hit=np.all(w>=-1e-9,axis=1)&(w.sum(1)<=1+1e-9)&(d>1e-7)
  out[choose[hit]]=True
 return out
over=[]
for poly,t in zip(polys,triangles):
 e=ConvexHull(poly).equations
 inside=(icon@e[:,:2].T+e[:,2]<=1e-9).all(1)
 over.append({'projected_icon_samples_in_conservative_log_silhouette':int(inside.sum()),
              'share_of_sampled_icon':float(inside.mean())})
 true=occlusion(t,icon)
 over[-1]['actual_opaque_log_depth_interference_samples']=int(true.sum())
 over[-1]['known_icon_sample_share_behind_actual_log_triangles']=float(true.mean())
sep=results[1]['draft_x_bounds_m'][0]-results[0]['draft_x_bounds_m'][1]
print(json.dumps({'draft_reference_scale_b':3.5227541825679687,'single_fixed_adjusted_spread_each_m':.065,
 'terrain':results,'x_axis_pair_gap_m':sep,'existing_icon_samples':len(icon),
 'icon_projection_bounds_px':[icon.min(0).tolist(),icon.max(0).tolist()], 'icon_conservative_occlusion':over,
 'admit':all(i['convex_hull_full_visible_gap_m']>=-1e-8 for i in results) and sep>=.02 and not any(i['actual_opaque_log_depth_interference_samples'] for i in over)},indent=2))
