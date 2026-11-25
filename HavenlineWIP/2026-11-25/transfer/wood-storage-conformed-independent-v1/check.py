import contextlib, io, json, runpy, subprocess, sys, re, hashlib
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
B=Path(__file__).resolve().parent.parent
s=Path(sys.argv[1]); crown=Path(sys.argv[2]); repo=Path(sys.argv[3]); st=json.loads(s.read_bytes()); cam=st['camera']
V=np.array(st['vertices_godot']); F=np.array(st['faces']); mids=np.array(st['material_ids']); uv=np.array(st['uv_gltf'])
p='11c14a1c41971067c7dc97db69375f720a408f68:HavenlineLevel1/'
def git(f):return subprocess.check_output(['git','-C',str(repo),'show',p+f])
shader=git('previews/integrated_camp_floor.gdshader').decode()
assert 'ALBEDO = vec3(0.51, 0.57, 0.60);' in shader and 'ROUGHNESS = 0.94;' in shader
script=git('previews/integrated_opening.gd').decode(); assert 'floor.position.y = .012' in script
with contextlib.redirect_stdout(io.StringIO()): m=runpy.run_path(str(B/'havenline-buy-plot-footprint-study-v8/project.py'))
for f in ('river_geometry.gd','accepted_t02_surface.gd','terrain_source.gd'):assert git(f)==(m['pin']/f).read_bytes()
offset=max(abs(y-m['height'](x,z)-.012) for x,y,z in V)
assert offset<1e-10
area=np.abs(np.cross(V[F[:,1]]-V[F[:,0]],V[F[:,2]]-V[F[:,0]])[:,1])*.5
tag=next(x for x in json.loads((B/'hvn-l1-v5-paid-pine-combined-v1/result.json').read_bytes())['funded'] if x['tag']=='after')
assert tag['camp'] and tag['camera_projection']==1 and tag['camera_size']==cam['size']==13
assert tag['cam_position']==cam['position'] and tag['camera_back']==cam['back']
R=np.array([cam['right'],cam['up'],cam['back']]); c=np.array(cam['position']); assert np.max(abs(R@R.T-np.eye(3)))<2e-6
marker=np.unique(F[mids==1])
tri,groups=runpy.run_path(str(B/'hvn-l1-transfer-crown-spacing-v1/audit.py'))['decode'](crown)
assert np.sum(groups)==1300
tri=tri.reshape(-1,3,3)
def project(v):return np.array([640,360])+((v-c)@R[:2].T)*np.array([1,-1])*720/13
def bbox(v):return [v.min(axis=0).tolist(),v.max(axis=0).tolist()]
def mask(P):
 im=Image.new('1',(1280*3,720*3)); dr=ImageDraw.Draw(im)
 for t in P:dr.polygon([tuple(x*3) for x in t],fill=1)
 return np.array(im)
details=[]; ms=[]; intervals=[]
for d in st['per_log_pose_godot']:
 rot=np.array(d['R_source_to_source_world']); t=np.array(d['t_source_to_source_world'])
 assert np.max(abs(rot.T@rot-np.eye(3)))<1e-10 and abs(np.linalg.det(rot)-1)<1e-10
 shape=tri@rot.T+t; C=np.unique(shape.reshape(-1,3),axis=0); assert len(C)==834
 ys=np.array([y-m['height'](x,z) for x,y,z in C])
 assert abs(min(ys)-.012)<1e-10 and np.count_nonzero(abs(ys-.012)<1e-9)==3
 P=project(shape); M=mask(P); ms.append(M); intervals.append((C[:,0].min(),C[:,0].max()))
 details.append(dict(screen_bbox_px=bbox(P.reshape(-1,2)),projected_area_px2=float(M.sum()/9),source_terrain_min_vertex_clearance_m=float(ys.min()),source_visible_contact_count=3))
assert len(ms)==2
g=sorted(intervals)[1][0]-sorted(intervals)[0][1]; assert g>.000999
j=Path('stocked-conformed-stage-1280x720.jpg')
assert Image.open(j).size==(1280,720)
print(json.dumps(dict(floor_vis_y_error_m=offset,existing_source_albedo_linear=[.51,.57,.60],whole_detached_floor_area_m2=float(sum(area)),paint_area_m2=float(sum(area[mids==1])),marker_screen_bbox_px=bbox(project(V[marker])),marker_V3_linear_uv_range=bbox(uv[marker]),camera=cam,pose=details,log_ground_plane_interval_gap_m=g,projected_silhouette_overlap_px2=float((ms[0]&ms[1]).sum()/9),stocked_frame_sha256=hashlib.sha256(j.read_bytes()).hexdigest(),stocked_frame_bytes=j.stat().st_size),indent=2,sort_keys=True))
