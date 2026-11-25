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
 rot0=Rotation.from_rotvec([fit.x[0],0,fit.x[1]]).as_matrix()
 RR=rot0@rot@R
 trans=parked[0]-RR@V[0]
 assert np.allclose(V@RR.T+trans,parked,atol=1e-12)
 transforms.append({'R_source_to_source_world':RR.tolist(),'t_source_to_source_world':trans.tolist()})
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
import struct
stage_glb=Path(sys.argv[3]); out=Path(sys.argv[4]); assert not out.exists(); out.mkdir()
v3=packet('hvn-l1-wood-storage-footprint-comparison-v3','5e95756cbb5094963a904888d7fe1ec5a0b71c426b7c9c78a5721eeb7e2ab437')
assert sha(stage_glb)=='c89ee6e92e352f32586113c6d5e1d81b21bc7cfb84603ee70d16e0b0d426afc1'
packet('hvn-l1-wood-storage-visible-park-v1','bdd0038128cca869a4b14bef7bf0e358f22c4666eb5f44db80286a4ed133b02c')
b=stage_glb.read_bytes(); n=struct.unpack_from('<I',b,12)[0]; doc=json.loads(b[20:20+n])
def buf(i):
 v=doc['bufferViews'][i];return b[28+n+v['byteOffset']:28+n+v['byteOffset']+v['byteLength']]
def acc(i):
 q=doc['accessors'][i]
 return np.frombuffer(buf(q['bufferView']),dtype='<f4',count=q['count']*{'VEC3':3,'VEC2':2}[q['type']]).reshape(q['count'],-1)
pr=doc['meshes'][0]['primitives'][0]; body=doc['materials'][0]
texture=buf(doc['images'][0]['bufferView'])
assert hashlib.sha256(texture).hexdigest()=='9301e61ba2530431c0f1e3821fd9cc87a92e27bf4db50c40a86a62027b920cb1'
srcpts=acc(pr['attributes']['POSITION']); srcuv=acc(pr['attributes']['TEXCOORD_0'])
assert np.max(np.abs(srcpts[:,1]))==0
UV=np.linalg.lstsq(np.c_[srcpts[:,[0,2]],np.ones(len(srcpts))],srcuv,rcond=None)[0]
uv_res=np.abs(np.c_[srcpts[:,[0,2]],np.ones(len(srcpts))]@UV-srcuv).max()
assert uv_res<1e-7
srcxz=srcpts[:,[0,2]]; unique=np.unique(srcxz,axis=0); hull=ConvexHull(unique)
unzoom=unique[hull.vertices]
outline=(np.c_[unzoom[:,0],np.zeros(len(unzoom)),unzoom[:,1]]@rot.T)[:,[0,2]]+origin
assert len(outline)==52
g0=outline.min(0);g1=outline.max(0)
# Existing source mask rectangle, in unshifted game axes translated to real terrain.
world_lo=np.array([-8.25,1.8]); world_hi=np.array([1.75,9.8])
assert (g0>world_lo).all() and (g1<world_hi).all()
def cut(p,a,b,keep):
 e=b-a; pts=[]
 for x,y in zip(p,p[1:]+p[:1]):
  sx=np.cross(np.r_[e,0],np.r_[x-a,0])[2]*keep
  sy=np.cross(np.r_[e,0],np.r_[y-a,0])[2]*keep
  if sx>=-1e-12:pts.append(x)
  if (sx>=-1e-12)!=(sy>=-1e-12):pts.append(x+(y-x)*sx/(sx-sy))
 return pts
def area(q):
 a=np.array(q)
 if len(a)<3:return 0.
 return abs(np.sum(a[:,0]*np.roll(a[:,1],-1)-a[:,1]*np.roll(a[:,0],-1)))/2
vertices=[]; faces=[];uvrows=[];types=[]
def emit(q,kind):
 if area(q)<1e-12:return
 start=len(vertices)
 for x,z in q:
  vertices.append((x,t(x,z)+ground_lift,z))
  s=np.array([x-origin[0],0,z-origin[1]])@rot
  uvrows.append((np.r_[s[[0,2]],1.]@UV).tolist())
 for i in range(1,len(q)-1):
  if area([q[0],q[i],q[i+1]])<1e-13:continue
  faces.append([start,start+i+1,start+i]);types.append(kind)
for r0 in region_vertices(world_lo,world_hi):
 poly=r0[:]
 for axis in range(2):
  poly=clip_poly(poly,axis,world_lo[axis],True); poly=clip_poly(poly,axis,world_hi[axis],False)
 if area(poly)<1e-12:continue
 poly=[np.array(v) for v in poly]
 q=np.array(poly)
 if (q.min(0)>g1).any() or (q.max(0)<g0).any():
  emit(poly,0);continue
 for a,b in zip(outline,np.roll(outline,-1,axis=0)):
  if len(poly)<3:break
  emit(cut(poly,a,b,-1),0)
  poly=cut(poly,a,b,1)
 if len(poly)>=3:emit(poly,1)
Vv=np.array(vertices); FT=np.array(faces); K=np.array(types);UVs=np.array(uvrows)
areas=np.abs(np.cross(Vv[FT][:,1]-Vv[FT][:,0],Vv[FT][:,2]-Vv[FT][:,0])[:,1])/2
assert abs(areas.sum()-80)<1e-8 and abs(areas[K==1].sum()-area(outline))<1e-8
marker=np.unique(FT[K==1]); assert UVs[marker].min()>0 and UVs[marker].max()<1
floor_depth=max(abs(v[1]-t(v[0],v[2])-ground_lift) for v in vertices)
assert floor_depth<1e-11
combined=packet('hvn-l1-v5-paid-pine-combined-v1','950d1a8b9992596a7b56ec64c7c98fbe1c9d34c04e698a78fb0dfbc50db4b031')
cam=next(x for x in json.loads((combined/'result.json').read_text())['funded'] if x['tag']=='after')
assert cam['camp'] and cam['camera_projection']==1 and cam['camera_size']==13
back=np.array(cam['camera_back']); pos=np.array(cam['cam_position'])
right=np.cross([0,1,0],back);right/=np.linalg.norm(right); up=np.cross(back,right)
world_points=Vv[marker]-pos
project=np.c_[640+(world_points@right)*720/13,360-(world_points@up)*720/13]
assert (project.min(0)>0).all() and (project.max(0)<[1280,720]).all()
path=out/'paint-inlay.png';path.write_bytes(texture)
# LOCAL stage source projection and recipe only; no source geometry/bytes
# for crown trees. Review renderer must reopen exact original asset.
payload={'vertices_godot':vertices,'faces':faces,'material_ids':types,'uv_gltf':uvrows,
 'per_log_pose_godot':transforms,'pinned_crown_glb_sha256':sha(source),
 'camera':{'size':13,'position':cam['cam_position'],'back':cam['camera_back'],'right':right.tolist(),'up':up.tolist(),'render_resolution':[1280,720]},
 'floor':{'roughness':.94,'linear_base_color':[.51,.57,.60],'existing_y_offset_m':.012,'no_support_collider':True},
 'marker':{'roughness':body['pbrMetallicRoughness']['roughnessFactor'],'png_file':path.name,'is_coplanar_in_material_partition':True}}
(out/'stage.LOCAL.json').write_text(json.dumps(payload,separators=(',',':')))
print(json.dumps({'source_crown_sha256':sha(source),'footprint_art_glb_sha256':sha(stage_glb),
 'paint_sha256':sha(path),'outline_vertices':len(outline),'render_fixture_has_no_overlay_height_delta':True,
 'stage_vertices':len(vertices),'stage_faces':len(faces),'marker_faces':int((K==1).sum()),'floor_area_m2':float(areas.sum()),
 'marked_area_m2':float(areas[K==1].sum()),'paint_uv_axial_affine_residual':float(uv_res),'floor_y_relative_source_error':float(floor_depth),
 'camera_bounds_diagnostic_logical_px':np.stack([project.min(0),project.max(0)]).tolist(),'camera_metadata':payload['camera'],
 'wood_contact_from_exact_source':summ,'two_log_plan_gap_m':gap,'marker_rest_stage_output_sha':sha(out/'stage.LOCAL.json')},indent=2,sort_keys=True))
