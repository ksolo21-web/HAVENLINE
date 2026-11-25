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
  # Use same source triangles and only translate vertically. Compute exact
 # separation to both the collision copy (top = terrain) and visually shifted copy.
 parked=moved+[0,ground_lift,0]
 support=parked[contacts]
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
print(json.dumps({'physical_collision_below_visual_m':ground_lift,'exact_same_mesh_floor_copy_source':True,
   'numerical_geometric_visual_contact_only':True,'rigid_support':False,'log_pair_envelope_gap_m':gap,'log_audits':summ},indent=2,sort_keys=True))
