from pathlib import Path
import subprocess,sys,json,hashlib,runpy,io,contextlib,math
import numpy as np
from scipy.spatial import ConvexHull
from scipy.spatial.transform import Rotation
from scipy.optimize import root,linprog
base=Path('..'); repo=Path(sys.argv[1]); source=Path(sys.argv[2])
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def packet(name,d):
 p=base/name; assert sha(p/'SHA256SUMS')==d
 subprocess.run(['sha256sum','-c','--status','SHA256SUMS'],cwd=p,check=True)
 return p
packet('hvn-l1-wood-storage-terrain-split-v1','c58613cf9cfabe8177d0f25bf75db5762608070abb212a3deafdd10205039cd4')
packet('hvn-l1-wood-storage-occupied-reference-v1','867beed12a916f12365b56c9c8b5321efe8dad13ebf83490a11cfc665fe62ccb')
p=packet('hvn-l1-wood-storage-camp-fit-v1','af1d5e7ed9f9043b6b1becb008bdff5a1e6196e1ed5b779b5d9d6ef039ee2548')
packet('hvn-l1-storage-reference-scale-independent-v1.4QShW9','f923c2f9ed3ec29089e04a355e6cf80b1307b46e73e797513b545ccfc52f550d')
rest=packet('hvn-l1-wood-storage-rest-facet-v1','76d3a59cc9dd3bda83c1abe187bc3d9ab81705bf162ba0b3edbd1f8f1af893e2')
r=json.loads((rest/'result.json').read_text())
with contextlib.redirect_stdout(io.StringIO()):
 m=runpy.run_path(str(base/'havenline-buy-plot-footprint-study-v8/project.py'))
t=m['height']; pin='11c14a1c41971067c7dc97db69375f720a408f68'
for k in ('accepted_t02_surface.gd','river_geometry.gd','terrain_source.gd'):
 assert (m['pin']/k).read_bytes()==subprocess.check_output(['git','-C',repo,'show',pin+':HavenlineLevel1/'+k])
R=np.array(r['exact_source_basis_matrix_row_major'])
tri,_=runpy.run_path(str(base/'hvn-l1-transfer-crown-spacing-v1/audit.py'))['decode'](source)
V=np.unique(tri.reshape(-1,3),axis=0)
H=ConvexHull(V)
rot=Rotation.from_euler('y',90,degrees=True).as_matrix()
g=json.loads((p/'result.json').read_text()); assert g['rotation_range_deg']==[89,91]
origin=np.mean(g['center_envelope_pre_shift_xz_m'],axis=0)+np.array([-3.25,5.80])
active=subprocess.check_output(['git','-C',repo,'show',pin+':HavenlineLevel1/previews/integrated_opening.gd']).decode()
assert 'floor.mesh = Terrain.terrain_mesh()' in active
import re
ground_lift=float(re.search(r'floor.position.y = ([.0-9]+)',active)[1]); assert ground_lift==.012
assert 'terrain_xz = VERTEX.xz' in subprocess.check_output(['git','-C',repo,'show',pin+':HavenlineLevel1/previews/integrated_camp_floor.gdshader']).decode()
summ=[]
worlds=[]
transforms=[]
limits=[]
def heights(q):return np.array([t(*v) for v in q[:,[0,2]]])
def clip_poly(poly, axis, bound, keep):
 return m['clip'](poly,axis,bound,keep)
def region_vertices(lo,hi):
 for i in range(math.floor(lo[0]*4),math.ceil(hi[0]*4)):
  for j in range(math.floor(lo[1]*4),math.ceil(hi[1]*4)):
   a,b,c,d=[(i/4+x,j/4+y) for x,y in [(0.,0.),(.25,0.),(0.,.25),(.25,.25)]]
   for q in ([a,b,c],[b,d,c]):yield q
def intersect(q,other):
 # other triangles always XZ counterclockwise; clipping keeps the left side.
 q=list(q)
 for u,v in zip(other,other[1:]+other[:1]):
  u,v=np.array(u),np.array(v);vec=v-u
  ans=[]
  for a,b in zip(q,q[1:]+q[:1]):
   da=vec[0]*(a[1]-u[1])-vec[1]*(a[0]-u[0]); db=vec[0]*(b[1]-u[1])-vec[1]*(b[0]-u[0])
   if da>=-1e-13:ans.append(a)
   if (da>=-1e-13)!=(db>=-1e-13):ans.append(a+(b-a)*(da/(da-db)))
  q=ans
  if not q:break
 return q
def valid_min(surface):
 # Scan lower supporting hull facets against terrain triangles; all affine
 # separations attain extrema at vertices of these polygon intersections.
 out=[]; count=0
 for face in H.simplices:
  T=surface[face]; X=T[:,[0,2]]; dif=(X[1:]-X[0])
  if abs(np.linalg.det(dif))<1e-13:continue
  yplane=np.linalg.solve(dif,T[1:,1]-T[0,1])
  for t0 in region_vertices(X.min(0),X.max(0)):
   P=intersect(X,t0)
   if not P:continue
   ll=np.array(P); h=np.array([t(*q) for q in ll])
   delta=T[0,1]+(ll-X[0])@yplane-h
   out.append(delta.min());count+=len(P)
 return float(min(out)),count
row_offsets=[np.array([.715,0,.05]),np.array([.875,0,.05])]
for ordinal,c in enumerate(r['clearance_result']):
 local=V@R.T+np.array(c['source_to_plate_t'])
 contacts=np.flatnonzero(abs(local[:,1])<1e-9); assert len(contacts)==3
 world=local@rot.T+np.array([origin[0],0.,origin[1]]) + row_offsets[ordinal]
 picked=world[contacts]; h=heights(picked)
 plane=np.linalg.solve(np.c_[picked[:,[0,2]]-origin,np.ones(3)],h)
 absolute_min,n0=valid_min(world)
 # Existing exact orientation plus one independent Y translation, just enough
 # to avoid all conservative hull penetration. Test actual remaining contacts.
 fixed_contact_gap=-absolute_min-h
 assert fixed_contact_gap.min()>-1e-8
 # Diagnostic only: smallest local pitch/roll restoring original three contact vertices
 # without translating in XZ. No new source transform proposed for shipping.
 p0=world[:,[0,2]].mean(0)
 center=np.array([p0[0],0.,p0[1]])
 def corrected(q,k):
  rot0=Rotation.from_rotvec([k[0],0,k[1]]).as_matrix()
  return (q-center)@rot0.T+center+[0,k[2],0]
 def eq(k):
  q=corrected(picked,k)
  return q[:,1]-heights(q)
 fit=root(eq,[plane[1],-plane[0],h.mean()],tol=1e-11)
 moved=corrected(world,fit.x); residual=eq(fit.x)
 assert max(abs(residual))<1.e-8
 min1,n1=valid_min(moved)
 ls=moved[:,[0,2]]; limits.extend([ls.min(0),ls.max(0)])
 visible_lowest=(moved[:,1]-heights(moved))-ground_lift
 co=(np.array(r['source_center_proxy_xyz_m'])@R.T+np.array(c['source_to_plate_t']))@rot.T+np.array([origin[0],0,origin[1]])+row_offsets[ordinal]
 newcom=corrected(co.reshape(1,3),fit.x)[0]
 cp=moved[contacts]; hc=ConvexHull(cp[:,[0,2]])
 margin=float((-hc.equations[:,:2]@newcom[[0,2]]-hc.equations[:,2]).min())
  # Use same source triangles and only translate vertically. Compute exact
 # separation to both the collision copy (top = terrain) and visually shifted copy.
 parked=moved+[0,ground_lift,0]
 support=parked[contacts]
 rr=Rotation.from_rotvec([fit.x[0],0,fit.x[1]]).as_matrix()@rot@R
 tt=parked[0]-rr@V[0]
 assert np.linalg.det(rr)>0.999999 and np.allclose(V@rr.T+tt,parked,atol=1.e-12)
 worlds.append(parked)
 transforms.append({'R_source_to_source_world':rr.tolist(),'t_source_to_source_world':tt.tolist()})
 physical_min,nP=valid_min(parked)
 def visible_min(y):
  h,n=valid_min(parked+[0,y,0])
  return h-ground_lift,n
 min2=physical_min-ground_lift
 allV=parked[:,1]-heights(parked)-ground_lift
 remainder=np.ones(len(parked),bool); remainder[contacts]=False
 zeros=support[:,1]-heights(support)-ground_lift
 assert max(abs(zeros))<1.e-9 and abs(min2)<1.e-9
 assert abs(physical_min-ground_lift)<1.e-9 and min(allV[remainder])>=-1.e-9
 assert np.array_equal(parked[:,[0,2]],moved[:,[0,2]])
 undershoot,_=visible_min(-.001); overshoot,_=visible_min(.001)
 assert abs(undershoot+.001)<1.e-9 and abs(overshoot-.001)<1.e-9
 summ.append({'visible_seat_min_full_convex_envelope_m':min2,
   'collision_clearance_full_envelope_m':physical_min,'three_original_contact_vertices_visible_gap_m':zeros.tolist(),
   'minimum_noncontact_vertex_to_visible_floor_m':float(min(allV[remainder])),
   'vertices_tested_each_physical_park':len(parked),'terrain_hull_clipped_vertices_each':nP,
   'whole_mesh_intersection_control_minus_1mm':undershoot,'whole_mesh_gap_control_plus_1mm':overshoot,
   'clearance_intervals_x_m':[float(parked[:,0].min()),float(parked[:,0].max())],
   'clearance_oriented_rectangle_xz_m':np.stack([parked[:,[0,2]].min(0),parked[:,[0,2]].max(0)]).tolist()})
gap=max(summ[0]['clearance_intervals_x_m'][0]-summ[1]['clearance_intervals_x_m'][1],summ[1]['clearance_intervals_x_m'][0]-summ[0]['clearance_intervals_x_m'][1])
assert gap>.000999
stage=Path(sys.argv[3]).resolve(); raw=stage.read_bytes()
packet('hvn-l1-wood-storage-conformed-stage-v1','58b419fc76129adc3f7089fa78acba63ac96c22532756fecd5eafd1f9e2636ad')
assert hashlib.sha256(raw).hexdigest()=='4b6b27b2bb2098de6f58a2af8fc6f634a4f54351e85c6158c76ecf0620812122'
base_stage=json.loads(raw); assert base_stage['pinned_crown_glb_sha256']==sha(source)
paint=stage.parent/base_stage['marker']['png_file']
assert sha(paint)=='9301e61ba2530431c0f1e3821fd9cc87a92e27bf4db50c40a86a62027b920cb1'
idx=np.array(base_stage['faces'])[np.asarray(base_stage['material_ids'])==1]
ii=np.unique(idx)
vs=np.asarray(base_stage['vertices_godot']);P=vs[ii][:,[0,2]]
material_outline=ConvexHull(P)
pad_edge_dist=[float((-material_outline.equations[:,:2]@w[:,[0,2]].T-material_outline.equations[:,2,None]).min()) for w in worlds]
assert min(pad_edge_dist)>.1
U=np.asarray(base_stage['uv_gltf']); UVtoXZ=np.linalg.lstsq(np.c_[U[ii],np.ones(len(ii))],P,rcond=None)[0]
err=float(abs(np.c_[U[ii],np.ones(len(ii))]@UVtoXZ-P).max());assert err<1e-8
# Glyph support is a conservative rectangle: closed source SVG path
# coordinate bounds mapped through the documented 2.1x group transform + paint strokes.
glyph=np.array([[466,284],[857,284],[857,755],[466,755]],float)/[1320,1040]
glyphXZ=np.c_[glyph,np.ones(4)]@UVtoXZ
if np.linalg.det(np.stack([glyphXZ[1]-glyphXZ[0],glyphXZ[2]-glyphXZ[0]]))<0:
 glyphXZ=glyphXZ[::-1]
G=[]
for q in region_vertices(glyphXZ.min(0),glyphXZ.max(0)):
 Q=intersect(glyphXZ,list(map(np.array,q)))
 for u in Q:G.append([u[0],t(*u)+ground_lift,u[1]])
C=base_stage['camera'];left=np.array(C['right']);up=np.array(C['up']); pos=np.array(C['position'])
def project(x):
 return (np.asarray(x)-pos)@np.stack([left,-up]).T*(720/13)+[640,360]
L=[project(x) for x in worlds]; gp=project(G)
def max_separating_margin(px,py):
 a,b=ConvexHull(px),ConvexHull(py); n=np.vstack([a.equations,b.equations])[:,:2]
 v,w=px@n.T,py@n.T
 return float(np.maximum(v.min(0)-w.max(0),w.min(0)-v.max(0)).max())
s_sep=max_separating_margin(*L)
g_sep=[max_separating_margin(x,gp) for x in L]
old_world=[V@np.array(f['R_source_to_source_world']).T+np.array(f['t_source_to_source_world']) for f in base_stage['per_log_pose_godot']]
old_pro=[project(x) for x in old_world]
old_pair=max_separating_margin(*old_pro)
old_glyph=[max_separating_margin(x,gp) for x in old_pro]
assert old_pair<0 and min(old_glyph)<0
assert s_sep>=2.0 and min(g_sep)>=2.0
# Keep floor and camera byte-stable as model JSON values; update only the 2 display transforms.
new=dict(base_stage,per_log_pose_godot=transforms)
assert [k for k in new if new[k]!=base_stage[k]]==['per_log_pose_godot']
out=Path(sys.argv[4]);out.mkdir(exist_ok=False)
path=out/'stage.LOG_DISPLAY_CANDIDATE.LOCAL.json';path.write_text(json.dumps(new,separators=(',',':')))
(out/paint.name).write_bytes(paint.read_bytes())
print(json.dumps({'scope':'new detached occupied-only display pose pair, no gameplay placement or render',
  'old_stage_SHA256':hashlib.sha256(raw).hexdigest(),'new_stage_SHA256':sha(path),'same_keys_except_exact_log_transforms':True,'old_center_pose_negative_separating_margins_px':[old_pair,*old_glyph], 'frozen_relative_row_offset_source_world_m':[x.tolist() for x in row_offsets],
  'terrain_support_and_full_mesh':summ,'pair_x_axis_clearance_m':gap,'finite_marker_top_outline_reserve_m':pad_edge_dist,
  'old_stage_camera_exact':C,'projected_conservative_pair_separating_margin_px':s_sep,'projected_each_log_to_conservative_glyph_px':g_sep,
  'projected_each_log_bounds_px':[np.stack([x.min(0),x.max(0)]).tolist() for x in L],
  'glyph_superset_projection_bounds_px':np.stack([gp.min(0),gp.max(0)]).tolist(),'visible_contact_is_not_collision_support':True,
  'detached_log_transforms':transforms},indent=2,sort_keys=True))
