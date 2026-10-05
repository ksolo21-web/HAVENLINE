#!/usr/bin/env python3
"""Apply the tested rendering-precision correction without changing lake geometry.
The real same-view comparison showed material debanding removes the wide bands.
Restore the original lit water shader and automatic ambient handling; preserve
fog, shadows, ripple normals, saved-time animation and all previous failure logs.
"""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
p=ROOT/'HavenlineGodot/scripts/outpost_view.gd'
assert sha(p)=='7788b97862a13436289b354942a7345084b4cf528127cad9bec66c0d5b331750','Concurrent view edit'
s=p.read_text().replace('var heat_light: OmniLight3D','var heat_light: OmniLight3D\nvar material_debanding_enabled := false')
needle='\tenvironment=env; sunlight=sun; furnace_node=furnace; heat_light=light';assert s.count(needle)==1
s=s.replace(needle,needle+'\n\t# Mobile precision dithering prevents visible bands in low-contrast water fog.\n\t# Keep normal material lighting; no extra fullscreen blur or unlit fallback.\n\tRenderingServer.material_set_use_debanding(true)\n\tmaterial_debanding_enabled=true')
for needle in ['\tlake_material.set_shader_parameter("stable_ambient_color",environment.ambient_light_color)\n','\tlake_material.set_shader_parameter("stable_ambient_energy",environment.ambient_light_energy)\n']:
 assert s.count(needle)==1;s=s.replace(needle,'')
needle='"east_west_end_to_end":true,"shared_actor_surface":true,';assert s.count(needle)==1
s=s.replace(needle,'"material_debanding_enabled":material_debanding_enabled,"east_west_end_to_end":true,"shared_actor_surface":true,')
p.write_text(s)
assert sha(p)=='c9971ef7711b6f58ee1484d51e43b9c2d439eb1d80fd504f4c9cd2ba475ca337','View differs from tested local source'
p=ROOT/'HavenlineGodot/shaders/lakeshore_water.gdshader'
assert sha(p)=='d553e45292653b141bfbab3e6e0e77be22bd18f77961a77e4fa28daeff11a86c','Concurrent shader edit'
p.write_text('''shader_type spatial;
render_mode diffuse_burley, specular_schlick_ggx;
// Opaque bounded water avoids full-screen refraction and transparent depth sorting.
// Runtime simulation time (not shader TIME) freezes coherently with pause/resume.
uniform float sim_time=0.0;
uniform vec2 lake_center=vec2(0.0,-13.85);
uniform vec2 lake_half=vec2(15.2,1.85);
varying vec2 world_xz;
void vertex(){world_xz=(MODEL_MATRIX*vec4(VERTEX,1.)).xz;}
void fragment(){
 vec2 p=world_xz;vec2 q=abs(p-lake_center);
 float sd=length(vec2(max(q.x-(lake_half.x-lake_half.y),0.),q.y))-lake_half.y;
 float depth=1.-smoothstep(-.29,-.02,sd);
 vec3 base=mix(vec3(.05,.63,.86),vec3(.002,.40,.77),depth);
 float a=sin(p.x*2.5+p.y*1.5+sim_time*.75);
 float b=sin(p.x*-1.7+p.y*3.3-sim_time*.42);
 float caustic=pow(clamp((a+b)*.25+.5,0.,1.),7.0);
 // Broad, quiet current strokes, not foamy noise or a glossy pool rim.
 float stroke=pow(.5+.5*sin(p.x*1.9+p.y*.51+sin(p.y*2.1)*.16+sim_time*.32),12.);
 base+=vec3(.006,.022,.028)*caustic+vec3(.003,.012,.021)*stroke;
 float shoreline=exp(-pow((sd+.115)/.035,2.0));
 base=mix(base,vec3(.49,.87,.95),shoreline*.055);
 ALBEDO=pow(base,vec3(2.2));ROUGHNESS=.54;SPECULAR=.12;
 // Small analytic slopes keep calm, rounded ripples without displacing the bank.
 NORMAL_MAP=normalize(vec3(cos(p.x*2.5+p.y*1.5+sim_time*.75)*.035,cos(p.x*-1.7+p.y*3.3-sim_time*.42)*.045,1.0))*.5+.5;
 NORMAL_MAP_DEPTH=.4;
}
''')
assert sha(p)=='ffa9ee60e87cafda8fee89d356ef88008a8de658c2997843bfcb00e8c45898e5','Original lit shader not restored exactly'
paths=['scripts/outpost_surface.gd','scripts/outpost_view.gd','scripts/outpost_simulation.gd','scripts/main.gd','shaders/outpost_snow.gdshader','shaders/lakeshore_water.gdshader','tests/test_task02_terrain.gd','tests/test_lake_east_west.gd','tests/capture_lake_east_west.gd']
runtime={'HavenlineGodot/'+name:sha(ROOT/'HavenlineGodot'/name) for name in paths}
print(json.dumps({'correction':'T02-extended-lake-material-precision','tested_runtime_hashes':runtime,'lake_extent_x':[-15.2,15.2],'playable_extent_x':[-14.2,14.2],'material_debanding_enabled':True,'diagnostic_run':34542759625,'original_lit_shader_restored':True,'ambient_workaround_removed':True,'old_failures_preserved':True,'task_approved':False}))
