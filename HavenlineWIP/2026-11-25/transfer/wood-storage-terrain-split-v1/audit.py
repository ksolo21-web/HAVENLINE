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
ground_lift=.012  # fixed visual camp shader overlay, not a physics support plane
summ=[]
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
for c in r['clearance_result']:
 local=V@R.T+np.array(c['source_to_plate_t'])
 contacts=np.flatnonzero(abs(local[:,1])<1e-9); assert len(contacts)==3
 world=local@rot.T+np.array([origin[0],0.,origin[1]])
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
 co=(np.array(r['source_center_proxy_xyz_m'])@R.T+np.array(c['source_to_plate_t']))@rot.T+np.array([origin[0],0,origin[1]])
 newcom=corrected(co.reshape(1,3),fit.x)[0]
 cp=moved[contacts]; hc=ConvexHull(cp[:,[0,2]])
 margin=float((-hc.equations[:,:2]@newcom[[0,2]]-hc.equations[:,2]).min())
 summ.append({'stock_rest_exact_contact_heights_m':h.tolist(),'spread_m':float(np.ptp(h)),'axis_fixed_Yonly_hull_shift_m':-absolute_min,'axis_fixed_contact_gaps_m':fixed_contact_gap.tolist(),
 'triangle_intersections_tested_fixed':n0,'triangle_intersections_tested_tilted':n1,
 'exact_log_footprint_world_bounds_xz_m':np.stack([world[:,[0,2]].min(0),world[:,[0,2]].max(0)]).tolist(),
 'source_three_point_terrain_plane_slopes_xz':plane[:2].tolist(),
 'corrective_roll_pitch_deg_diagnostic_only':np.degrees(fit.x[:2]).tolist(),'tilted_residual_contact_m':residual.tolist(),
 'corrected_hull_min_minus_terrain_m':min1, 'visible_floor_occlusion_lower_bound_m':ground_lift-min1,'original_mesh_vertices_below_existing_visible_floor':int(np.count_nonzero(visible_lowest < -1.e-8)),'proxy_com_margin_tilted_m':margin,
 'posttilt_world_X_interval_m':[float(moved[:,0].min()),float(moved[:,0].max())]})
# Local indexed terrain patch covering both actual projected boxes, not the
# oversized art marker or the entire west family.
l=np.min(limits,axis=0); h=np.max(limits,axis=0)
Q=[]
for vec in region_vertices(l,h):
 for i in range(2):
  vec=clip_poly(vec,i,l[i],True);vec=clip_poly(vec,i,h[i],False)
 Q.extend(vec)
Q=np.array(sorted(set(Q))); hq=np.array([t(*q) for q in Q]); B=np.c_[Q-Q.mean(0),np.ones(len(Q))]
E=np.c_[np.concatenate((B,-B)),np.full(2*len(Q),-1)]
pl=linprog([0,0,0,1],A_ub=E,b_ub=np.r_[hq,-hq],bounds=[(None,None)]*3+[(0,None)],method='highs'); assert pl.success
print(json.dumps({'local_pair_patch_indexed_aabb_bounds_xz_m':[l.tolist(),h.tolist()],'local_paired_floor_fit':{'clipped_vertices':len(Q),'horizontal_relief_m':float(np.ptp(hq)),'best_plane_residual_sup_error_m':float(pl.fun),'best_plane_slope_xz':pl.x[:2].tolist()},'terrain_following_paint_definable_on_existing_same_surface':True,'visible_ground_cannot_be_matched_by_raising_physics_rest':True,'scope' :'one actual source patch, offline, optic apron unbuilt; no adopted pose/site','existing_camp_visual_layer_over_terrain_m':ground_lift,
 'fixed_crown_orientation_exact_three_point_possible':all(x['spread_m']<1e-9 for x in summ),'terrain_tilt_without_terrain_edit_diagnostic':summ,
 'tilted_pair_positive_interval_gap_m':max(summ[0]['posttilt_world_X_interval_m'][0]-summ[1]['posttilt_world_X_interval_m'][1],summ[1]['posttilt_world_X_interval_m'][0]-summ[0]['posttilt_world_X_interval_m'][1])},indent=2,sort_keys=True))
