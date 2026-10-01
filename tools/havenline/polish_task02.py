"""Repair observed T02 water-edge seam and refine the actual shoreline.
Writes only the four stated Task2 files, then verifies their exact locally tested hashes.
No score, tree replacement, camera change or later-task implementation.
"""
from pathlib import Path
import hashlib
r=Path('.')
expected={'HavenlineGodot/scripts/outpost_surface.gd':'6afb0c9f91b7db4fee322b20de43f5479fac2585a0f0c109eb3cddbf059abb4e','HavenlineGodot/shaders/outpost_snow.gdshader':'2c365d4db63a1a4a6c7564611118b2fc253f00e30fd5885a3c3e87ee0f1ba56a','HavenlineGodot/shaders/lakeshore_water.gdshader':'45fb599c9d693d308f617b1dc0a0684f188ab212c58d351f109a5b14966c94f9','HavenlineGodot/tests/test_task02_terrain.gd':'1dd4167c9b9aa0531a38d3afd3e372cb80b4dee7ef2117b5759b247ca86ad430'}
if all(hashlib.sha256(Path(n).read_bytes()).hexdigest()==h for n,h in expected.items()):raise SystemExit(0)
p=r/'HavenlineGodot/scripts/outpost_surface.gd';s=p.read_text();assert 'static func coast_shape' not in s
s=s.replace('static func lake_distance(p: Vector2) -> float:', 'static func coast_shape(q: Vector2) -> float:\n\tvar angle := atan2(q.y,q.x)\n\treturn 1.0+.035*sin(3.0*angle)+.018*cos(5.0*angle)\n\nstatic func lake_distance(p: Vector2) -> float:')
s=s.replace('var q := (p-LAKE_CENTER).abs()/LAKE_HALF\n\treturn (pow(pow(q.x,4.0)+pow(q.y,4.0),0.25)-1.0)*LAKE_HALF.y','var signed_q := (p-LAKE_CENTER)/LAKE_HALF\n\tvar q := signed_q.abs()\n\treturn (pow(pow(q.x,4.0)+pow(q.y,4.0),0.25)/coast_shape(signed_q)-1.0)*LAKE_HALF.y')
s=s.replace('q*((1.0+(margin+.00002)/LAKE_HALF.y)/norm)','q*((1.0+(margin+.00002)/LAKE_HALF.y)*coast_shape(q/LAKE_HALF)/norm)')
s=s.replace('# The rim reaches d=-.06; the ground itself occludes the inner shoreline.','# Extend beyond the actual ground/water intersection so the whole mesh edge\n\t# is buried under the snow bank, never an exposed floating water lip.')
s=s.replace('q*LAKE_HALF*(1.0-.06/LAKE_HALF.y)','q*LAKE_HALF*coast_shape(q)*(1.0+.20/LAKE_HALF.y)');p.write_text(s)
p=r/'HavenlineGodot/shaders/outpost_snow.gdshader';s=p.read_text().replace('vec2 q=abs(p-lake_center)/lake_half;\n return (pow(pow(q.x,4.)+pow(q.y,4.),.25)-1.)*lake_half.y;','vec2 signed_q=(p-lake_center)/lake_half;vec2 q=abs(signed_q);\n float angle=atan(signed_q.y,signed_q.x);float shape=1.+.035*sin(3.*angle)+.018*cos(5.*angle);\n return (pow(pow(q.x,4.)+pow(q.y,4.),.25)/shape-1.)*lake_half.y;')
s=s.replace('float ice=(1.-smoothstep(.12,.33,shore));','float ice=(1.-smoothstep(-.12,.035,shore));').replace('ice*.48','ice*.35');p.write_text(s)
p=r/'HavenlineGodot/shaders/lakeshore_water.gdshader';s=p.read_text().replace('vec2 p=world_xz;vec2 q=abs(p-lake_center)/lake_half;\n float sd=(pow(pow(q.x,4.)+pow(q.y,4.),.25)-1.)*lake_half.y;','vec2 p=world_xz;vec2 signed_q=(p-lake_center)/lake_half;vec2 q=abs(signed_q);\n float angle=atan(signed_q.y,signed_q.x);float shape=1.+.035*sin(3.*angle)+.018*cos(5.*angle);\n float sd=(pow(pow(q.x,4.)+pow(q.y,4.),.25)/shape-1.)*lake_half.y;')
s=s.replace('vec3(.16,.70,.87),vec3(.015,.46,.77)','vec3(.24,.76,.85),vec3(.03,.59,.76)').replace('base+=vec3(.07,.12,.13)*caustic;','base+=vec3(.018,.024,.023)*caustic;').replace('shoreline*.48','shoreline*.16').replace('ROUGHNESS=.29;SPECULAR=.36','ROUGHNESS=.45;SPECULAR=.18');p.write_text(s)
p=r/'HavenlineGodot/tests/test_task02_terrain.gd';s=p.read_text().replace('check("Lakebed below water",','var edge_buried:=true;var water_faces:=true\n\tvar wf:=water.get_faces()\n\tfor v in wf:\n\t\tvar q:=Vector2(v.x,v.z)\n\t\tif Surface.lake_distance(q)>.1 and Surface.height_at(q)<=Surface.WATER_Y+.10:edge_buried=false\n\tfor i in range(0,wf.size(),3):\n\t\tif (wf[i+1]-wf[i]).cross(wf[i+2]-wf[i]).y>=-.000001:water_faces=false\n\tcheck("Every water mesh rim is buried under the actual bank",edge_buried)\n\tcheck("Water has no reversed or degenerate faces",water_faces)\n\tcheck("Lakebed below water",');p.write_text(s)
for name,h in expected.items():assert hashlib.sha256(Path(name).read_bytes()).hexdigest()==h,'Unexpected patched bytes '+name
print('Task2 shore correction matches all four locally tested source files. No task approval.')
