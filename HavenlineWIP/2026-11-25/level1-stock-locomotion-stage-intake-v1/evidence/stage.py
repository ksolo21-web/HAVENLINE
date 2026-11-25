from pathlib import Path
import numpy as np,json,sys,hashlib,subprocess,os,math
work,repo,output=map(Path,sys.argv[1:]); output.mkdir(mode=0o700)
CAP=work/'stock.private.ndjson'; root=work/'HavenlineLevel1'
assert hashlib.sha256(CAP.read_bytes()).hexdigest()=='5d74b695b85eaf088efe4800643cee2bcd750eef91a904ff45b002c21c75a77a'
commit='11c14a1c41971067c7dc97db69375f720a408f68'
for f in ('accepted_t02_surface.gd','river_geometry.gd','terrain_source.gd','previews/integrated_opening.gd','previews/integrated_opening.tscn','previews/terrain_water_preview.tscn','previews/terrain_contact_preview.gd','previews/terrain_contact_preview.tscn','materials/neutral_shore_snow.tres','materials/neutral_shore_snow.gdshader'):
 assert (root/f).read_bytes()==subprocess.check_output(['git','-C',str(repo),'show',commit+':HavenlineLevel1/'+f])
os.environ['HVN_EXACT_STOCK_ROOT']=str(root.resolve())
from source_math import vertex,shore,height
rows=[json.loads(l.split(' ',1)[1]) for l in CAP.read_text().splitlines() if l.startswith('STOCK_PRIVATE_FRAME ')]
assert len(rows)==90 and all(x['camera_size']==13 and x['viewport']==[1280,720] for x in rows)
assert [r['tick'] for r in rows]==list(range(26,205,2))
# Geometry in Y extents can be bounded conservatively from the exact authored formula;
# include the whole native quarter-meter grid touched by any viewport ray.
q=[]
for r in rows:
 o,x,y,b=np.array(r['camera']); assert np.max(abs(np.stack([x,y,b])@np.stack([x,y,b]).T-np.eye(3)))<1e-5
 for u in (-13*1280/720/2,13*1280/720/2):
  for v in (-6.5,6.5):
   p=o+x*u+y*v
   for terrain_y in (-1.5,2.):
    q.append((p-b*((p[1]-terrain_y)/b[1]))[[0,2]])
lo=np.maximum(-31.,np.floor((np.min(q,0)-.5)*4)/4);hi=np.minimum(31.,np.ceil((np.max(q,0)+.5)*4)/4)
xv=np.arange(lo[0],hi[0]+.25,.25);zv=np.arange(lo[1],hi[1]+.25,.25)
P=np.asarray([(x,vertex(x,z),z) for z in zv for x in xv],'<f4')
W=len(xv); ix=[]
# Native Godot winding flipped naturally for a right-handed Blender scene.
for j in range(len(zv)-1):
 for i in range(W-1):
  a=j*W+i; ix.extend(((a,a+W,a+1),(a+1,a+W,a+W+1)))
shore_v=np.array([shore(float(x),float(z)) for x,_,z in P],'<f4')
actor=[r['actor'][0] for r in rows]
delta=np.array([y+.035-height(x,z) for x,y,z in actor])
assert np.max(abs(delta))<.003 # actor physics has its own visible/contact tolerances
np.savez_compressed(output/'terrain-LOCAL.npz',points=P,faces=np.asarray(ix,dtype='<i4'),shore=shore_v)
ages=[dict(r,age_tick=r['tick']-rows[0]['tick']) for r in rows[::2]]
# Exact normally timed 45 facial/torso pose samples from the four actual locomotion phases.
assert len(ages)==45 and ages[0]['age_tick']==0 and ages[-1]['age_tick']==176
(output/'poses-LOCAL.json').write_text(json.dumps(ages,separators=(',',':')))
projected_shore=[]
tri=np.asarray(ix)
for frame in rows:
 o,r,u,b=np.array(frame['camera']); screen=(P-o)@np.asarray([r,u]).T*(720/13)*[1,-1]+[640,360]
 points=screen[tri]
 used=(points.min(1)<[1280,720]).all(1)&(points.max(1)>0).all(1)
 projected_shore.append(float(shore_v[tri[used]].min()))
assert min(projected_shore)>1.45
report=dict(stock_camera_samples_total=90,proposed_captured_samples_15_fps=len(ages),nominal_seconds=3,
 authored_quarter_meter_segment=True,terrain_points_count=len(P),terrain_native_source_equivalence='indexed source formula replay; numerical, not native mesh bytes',
 original_grid_domain=[-31,31],visible_conformance_y_ground_max_abs_from_native_capsule_plane_m=float(max(abs(delta))),
 planned_terrain_sha256=hashlib.sha256((output/'terrain-LOCAL.npz').read_bytes()).hexdigest(),
 environment_geometry='ground only; no water, trees, props or camera changes; source shader and luminance not reproduced',
 observed_action_phases=[a for a in dict.fromkeys(r['phase'] for r in ages)],
 actual_raster=False, stage_shader_not_native=True,min_conservatively_visible_shore_m=min(projected_shore), clipped_xz_grid=[lo.tolist(),hi.tolist()],min_region_shore_distance_m=float(shore_v.min()))
print(json.dumps(report,indent=2))
