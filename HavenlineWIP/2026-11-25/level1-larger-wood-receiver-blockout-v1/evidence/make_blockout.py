"""Create one editable receiver blockout and validate exact linked log seats."""
import argparse,json,hashlib,math,runpy
from pathlib import Path
import numpy as np
from scipy.spatial import ConvexHull, distance
pa=argparse.ArgumentParser()
pa.add_argument('source',type=Path)
pa.add_argument('output',type=Path)
pa.add_argument('paint',type=Path)
opts=pa.parse_args()
source=opts.source
paint=opts.paint
paint_sha='9301e61ba2530431c0f1e3821fd9cc87a92e27bf4db50c40a86a62027b920cb1'
assert hashlib.sha256(paint.read_bytes()).hexdigest()==paint_sha
out=opts.output
assert hashlib.sha256(source.read_bytes()).hexdigest()=='31378ac3c6b21fbc0fdcfe597333794a7fe8b36c628a53956ad6bc0956fd1554'
decode=runpy.run_path('hvn-l1-transfer-crown-spacing-v1/audit.py')['decode']
tri,group_sizes=decode(source)
v=np.unique(tri.reshape(-1,3),axis=0)
assert len(v)==834 and sum(group_sizes)==1300
support=(625,633,215)
src_hull=ConvexHull(v)
supports=[i for i,face in enumerate(src_hull.simplices) if set(face)==set(support)]
assert len(supports)==1
fac=src_hull.equations[supports[0]]
up=-fac[:3]
axis=np.array([1.,0,0])
z=axis-(axis@up)*up;z/=np.linalg.norm(z)
x=np.cross(up,z)
M=np.array([x,up,z]);assert np.allclose(M@M.T,np.eye(3),atol=1e-12) and np.linalg.det(M)>0
k=3.5227541825679687
q=k*v@M.T
level=-q[:,1].min()
q[:,1]+=level
before=((q.max(0)+q.min(0))/2)
q[:,[0,2]]-=before[[0,2]]
m=float(np.ptp(q[:,2]))
assert m>.99
XMAX=1.122/m; ZMAX=1.43/m; RAD=.10/m; TRIM=.022/m
BODY_HEIGHT=0.0 # coplanar face only, no thick lip/deck geometry, no collider-authority effect
q/=m
qx=float(np.ptp(q[:,0])); margin=.025/m
pitch=qx+margin
receiving_center_z=.70/m # same art family, nominal front strip in detached coordinates
seats=[[-pitch/2,0,receiving_center_z],[pitch/2,0,receiving_center_z]]
def rounded(ax,az,rad):
 pts=[]
 for s,t,start in [(1,1,0),(-1,1,90),(-1,-1,180),(1,-1,270)]:
  for th in np.linspace(start,start+90,13,endpoint=True):
   pts.append([s*(ax-rad)+rad*math.cos(math.radians(th)),t*(az-rad)+rad*math.sin(math.radians(th))])
 return np.array(pts)
outer=rounded(XMAX,ZMAX,RAD)
inner=rounded(XMAX-TRIM,ZMAX-TRIM,RAD-TRIM)
poly=ConvexHull(outer).equations
inners=ConvexHull(inner).equations
contacts=[]
extents=[]
for loc in seats:
 moved=q+np.array(loc)
 assert np.min(moved[:,1])>=-1e-13
 cs=np.flatnonzero(np.abs(moved[:,1])<1e-11)
 assert set(cs)==set(support)
 region=ConvexHull(moved[cs][:,[0,2]]).equations
 # AABB center is a conservative authored geometry proxy, not physical mass.
 center=(moved.max(0)+moved.min(0))/2
 support_margin=float(np.min(-region[:,2]-region[:,:2]@center[[0,2]])*m)
 axes=moved[:,[0,2]]
 support_reserve=float(np.min([-row[2]-np.max(axes@row[:2]) for row in inners])*m)
 assert support_margin>.008 and support_reserve>.07
 contacts.append(dict(local_indices=list(map(int,cs)),support_triangle_bbox_proxy_margin_m=support_margin,receiving_surface_to_inner_trim_minimum_m=support_reserve,
  max_contact_gap_m=float(abs(moved[cs,1]).max()*m),minimum_all_actual_vertex_gap_m=float(moved[:,1].min()*m),
  strictly_positive_noncontact_vertex_gap_m=float(np.min(np.delete(moved[:,1],cs))*m)))
 extents.append(moved)
gap=(extents[1][:,0].min()-extents[0][:,0].max())*m
assert gap>=.025-1e-10
# Camera screen projection: direction/extent only. Origin remains nominal; no map coupling.
camera=np.array([[.8436614871,0,-.5368754864],[-.3461942077,.7643247843,-.5440194607]]).T
pp=q@camera;draw=float(distance.pdist(pp[ConvexHull(pp).vertices,:]).max()*m*(720/13))
# Exact prior plate affine normalized into detached coordinates, measured
# previously on authored glTF marker (texture image origin top-left).
su,sv=.344352627,.437062941
from PIL import Image
tex=np.array(Image.open(paint).convert('RGB'))
yy,xx=np.indices(tex.shape[:2]);r,g,b=(tex[:,:,j] for j in range(3))
sel=(xx>=525)&(xx<=798)&(yy>=537)&(yy<=695)&(r>=180)&(g>=143)&(b>=68)
U=(xx[sel]+.5)/tex.shape[1];W=(yy[sel]+.5)/tex.shape[0]
icon=np.c_[(W-.5)/sv,np.zeros(len(U)),(.5-U)/su]/m
P=icon@camera
ncam=np.cross(camera[:,0],camera[:,1])
depth=icon@ncam
occ=np.zeros(len(icon),bool)
for shift in seats:
 t=(k/m*tri@M.T)+(np.array([-before[0],level,-before[2]])/m)+np.array(shift)
 projected=t@camera
 D=t@ncam
 for ar,dp in zip(projected,D):
  E=ar[1:]-ar[0]
  if abs(np.linalg.det(E))<1e-12:continue
  pick=np.flatnonzero(~occ&np.all(P>=ar.min(0),axis=1)&np.all(P<=ar.max(0),axis=1))
  if len(pick)==0:continue
  w=(P[pick]-ar[0])@np.linalg.inv(E)
  near=dp[0]+w@(dp[1:]-dp[0])>depth[pick]+1e-9
  inside=np.all(w>=-1e-9,axis=1)&(w.sum(1)<=1+1e-9)
  occ[pick[near&inside]]=True
# Editable local x/z shape. UVs tied to plate dimensions; actual stamped texture
# remains separate and is neither modified nor copied here.
assert out.is_dir()
obj=['# Non-production editable receiver; local x/z in nominal log-length units.','mtllib ReceiverBlockout.mtl','o RearWoodStoragePlate']
for p in np.r_[outer,inner,[[0.,0.]]]:
 obj+=['v %.12f %.12f %.12f'%(p[0],BODY_HEIGHT,p[1])]
for p in np.r_[outer,inner,[[0.,0.]]]:
 obj+=['vt %.12f %.12f'%(0.5-su*p[1]*m,0.5-sv*p[0]*m)]
obj+=['vn 0.0 1.0 0.0']
n=len(outer)
fmt=lambda *ix:'f '+' '.join(f'{i}/{i}/1' for i in ix)
obj+=['usemtl Low_Warm_Outline']
for u in range(n):
 j=(u+1)%n
 obj.append(fmt(u+1,n+u+1,n+j+1,j+1))
obj+=['usemtl Flat_Dark_Plate_Paint']
for u in range(n):
 j=(u+1)%n
 obj.append(fmt(2*n+1,n+j+1,n+u+1))
(out/'ReceiverBlockout.obj').write_text('\n'.join(obj)+'\n')
(out/'ReceiverBlockout.mtl').write_text('''# Directional blockout colors only; not coating or palette approval.
newmtl Low_Warm_Outline
Kd 0.49 0.38 0.27
Ks 0.025 0.022 0.018
Ns 8

newmtl Flat_Dark_Plate_Paint
Kd 0.115 0.093 0.076
Ks 0.020 0.017 0.015
Ns 7
''')
trans=k*np.array([0.,0.,0.])@M.T+[-before[0],level,-before[2]]
mdata={
  'status':'DETACHED_EDITABLE_LOCAL_ART_BLOCKOUT_NOT_SITE_OR_RELEASE_ADMISSION',
  'axes':'X along adjacent seats, Y up, Z along long axes toward camera-facing near plate edge',
  'local_units_to_m':m,
  'plate_local_center':[0,0,0],
  'plate_m_footprint_nominal':[2.244,2.860],
  'plate_primary_material_paint':{'uv_link':'Use the unchanged authored dark/stamp paint as visual direction; not embedded; no replacement stroke or recolor.',
    'existing_paint_sha256':'9301e61ba2530431c0f1e3821fd9cc87a92e27bf4db50c40a86a62027b920cb1'},
  'linked_exact_source_log':{'sha256':'31378ac3c6b21fbc0fdcfe597333794a7fe8b36c628a53956ad6bc0956fd1554',
      'group_triangle_counts':group_sizes,'verified_vertex_count':len(v),'normalized_linear_source_to_deck':(k/m*M).tolist(),
      'normalized_source_offset_before_inserting_seat':(trans/m).tolist(),
      'projected_long_axis_px_mid_1280x720_same_basis':draw},
  'one_near_row_two_anchor_offsets_local':seats,
  'exact_mesh_normalized_seat_bounds_local':[[sub.min(0).tolist(),sub.max(0).tolist()] for sub in extents],
  'working_space_X_pair_m':float((extents[1][:,0].max()-extents[0][:,0].min())*m),
  'clearance_m':float(gap),
  'stable_geometrical_contacts_not_runtime_physics':contacts,
  'local_default_basis_two_log_icon_cut_end_projection_only':{'sampled_original_core_points':len(occ),'obscured_by_actual_linked_triangles':int(occ.sum()),'percent_obscured':float(100*occ.mean()),'claimed_visual_pass':False},
  'visual_roles':{'empty':'No display logs; unchanged painted identity visible.',
    'partly_loaded':'Insert only known visual log instances at actual supported positions; retain recognizable real bark/pale ends and some recognizable mark if naturally visible.',
    'loaded':'Coherent parallel full-size logs may cover stamp naturally; visible outer silhouette; no declared geometry capacity, animation, inventory, physical stacking or row counts.'}
}
(out/'ReceiverBlockout.json').write_text(json.dumps(mdata,indent=2)+'\n')
