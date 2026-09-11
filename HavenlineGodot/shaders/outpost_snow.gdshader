shader_type spatial;
render_mode diffuse_burley, specular_schlick_ggx;
// T02 river revision. Vertex COLOR.r carries encoded river shore distance and
// COLOR.g carries workfloor distance, both authored by outpost_surface.gd.
uniform vec2 furnace_center = vec2(0.0,0.2);
uniform float warmth_radius = 4.5;
uniform float heat_strength = 1.0;
uniform float snow_amount = 0.03;
uniform float daylight_fill = 1.0;
varying vec3 world_pos;
varying vec2 authored_distance;
float material_hash(vec2 p){
 vec3 h=fract(vec3(p.xyx)*vec3(.1031,.1030,.0973));
 h+=dot(h,h.yzx+33.33);return fract((h.x+h.y)*h.z);
}
float material_noise(vec2 p){
 vec2 cell=floor(p), f=fract(p);f=f*f*(3.-2.*f);
 return mix(mix(material_hash(cell),material_hash(cell+vec2(1,0)),f.x),
            mix(material_hash(cell+vec2(0,1)),material_hash(cell+vec2(1,1)),f.x),f.y);
}
void vertex(){
 world_pos=(MODEL_MATRIX*vec4(VERTEX,1.)).xyz;
 authored_distance=COLOR.rg*8.-4.;
}
void fragment(){
 vec2 p=world_pos.xz;
 float shore=authored_distance.x;
 float d=authored_distance.y;
 float broad=material_noise(p*.37)-.5;
 float fine=material_noise(p*7.8)-.5;
 float footprint=max(length(dFdx(p)),length(dFdy(p)));
 float detail_weight=1.-smoothstep(.025,.16,footprint);
 vec3 snow=vec3(.98,.994,1.0)+vec3(.042,.029,.016)*broad;
 snow+=vec3(.012,.010,.008)*fine*detail_weight;
 float rim=(1.-smoothstep(.04,.48,d))*smoothstep(-.16,.04,d);
 snow=mix(snow,vec3(.73,.82,.94),rim*.16);
 float aa=max(fwidth(d)*.75,.022);
 float edge_d=d+(material_noise(p*1.6)-.5)*.035;
 float cleared=1.-smoothstep(-.08-aa,.13+aa,edge_d);
 vec3 floor=vec3(.80,.48,.36)+vec3(.09,.058,.043)*broad;
 floor+=vec3(.022,.015,.011)*fine*detail_weight;
 float dist=length(p-furnace_center);
 float warmth=(1.-smoothstep(warmth_radius-.4,warmth_radius+.12,dist))*heat_strength;
 floor=mix(floor,floor+vec3(.025,.012,0.),warmth*.42);
 vec3 material=mix(snow,floor,cleared);
 // Same encoded river distance as the sculpted terrain, so the cool wet face
 // cannot diverge from collision or save recovery.
 float ice=1.-smoothstep(-.12,.035,shore);
 material=mix(material,vec3(.37,.67,.84),ice*.35);
 ALBEDO=pow(clamp(material,vec3(0.),vec3(1.)),vec3(2.2));
 EMISSION=vec3(.030,.034,.040)*(1.-cleared)*clamp(daylight_fill,0.,1.);
 float sx=cos(p.x*8.1+p.y*3.7)*.006;
 float sz=cos(p.x*-4.6+p.y*9.3)*.006;
 NORMAL=normalize(NORMAL+(VIEW_MATRIX*vec4(-sx,0.,-sz,0.)).xyz*detail_weight);
 ROUGHNESS=clamp(mix(.92,.88,cleared)+fine*.028*detail_weight,.84,.95);
 SPECULAR=.18;
}
