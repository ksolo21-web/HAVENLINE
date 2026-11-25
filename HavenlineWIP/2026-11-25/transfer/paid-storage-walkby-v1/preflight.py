import json,hashlib,sys,subprocess
import numpy as np
from pathlib import Path
r=Path(sys.argv[1]); p=Path(sys.argv[2])
d=json.loads(p.read_text())
assert hashlib.sha256(p.read_bytes()).hexdigest()=='51e34077a346b0f60951d9ee18c43276c82e8a9787af8f82cdf14a1a7f84c31e'
commit='11c14a1c41971067c7dc97db69375f720a408f68'
lay=json.loads(subprocess.check_output(['git','-C',r,'show',commit+':HavenlineLevel1/layout.json']))
shift=np.array([-3.25,5.80])
v=np.asarray(d['vertices_godot'])[:,[0,2]]
tri=v[np.asarray(d['faces'])[np.asarray(d['material_ids'])==1]]
path=np.asarray([[0.,2.],[-1.6,2.25],[-2.875,1.15],[-3.30,.20],[-1.60,2.25],[0.,2.]])
def on_marker(q):
 t=tri-q
 cross=lambda a,b:a[:,0]*b[:,1]-a[:,1]*b[:,0]
 s=np.column_stack([cross(t[:,i],t[:,(i+1)%3]) for i in range(3)])
 return int(np.sum((s>=-1e-9).all(1)|(s<=1e-9).all(1)))
def segdist(a,b,c):
 d=b-a
 return float(np.linalg.norm(a+np.clip(d@(c-a)/(d@d),0,1)*d-c))
f=np.asarray(lay['furnace_xz'])
m=[segdist(a,b,f)-lay['actor_radius']-.85 for a,b in zip(path[:-1],path[1:])]
assert min(m)>.25 and on_marker(path[2]+shift)>0
assert not on_marker(path[1]+shift) and not on_marker(path[0]+shift)
print(json.dumps(dict(source_pin=commit,route_local_xz=path.tolist(),route_world_xz=(path+shift).tolist(),near_diagnostic_goal_intersects_polygon_in_source=bool(on_marker(path[2]+shift)),source_collider_plan_actor_margin_to_hearth_each_leg_m=m,notes='Goal is within the diagnostic conformed marker polygon when used as read-only reference; marker and receiver not instantiated. Native arrival and actual body path untested.'),indent=2))
