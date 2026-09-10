shader_type spatial;
render_mode diffuse_burley, specular_schlick_ggx;
// T02: clean painted-snow material. No stock checker, gravel noise or black mud.
uniform vec2 furnace_center = vec2(0.0,0.2);
uniform float warmth_radius = 4.5;
uniform float heat_strength = 1.0;
uniform float snow_amount = 0.03;
uniform vec2 lake_center = vec2(-7.6,-13.85);
uniform vec2 lake_half = vec2(5.2,1.85);
varying vec3 world_pos;
float rounded_rect(vec2 p,vec2 c,vec2 h,float r) {
 vec2 q=abs(p-c)-h+vec2(r);return length(max(q,vec2(0)))+min(max(q.x,q.y),0.0)-r;
}
float work_distance(vec2 p) {
 float a=rounded_rect(p,vec2(0,.3),vec2(9.75,6.7),.72);
 float b=rounded_rect(p,vec2(-6.5,-9.4),vec2(6.6,1.95),.65);
 return min(a,min(b,rounded_rect(p,vec2(-4.3,-6.8),vec2(4.45,1.25),.5)));
}
float shore_distance(vec2 p) {
 vec2 signed_q=(p-lake_center)/lake_half;vec2 q=abs(signed_q);
 float angle=length(signed_q)>.00001?atan(signed_q.y,signed_q.x):0.0;float shape=1.+.035*sin(3.*angle)+.018*cos(5.*angle);
 return (pow(pow(q.x,4.)+pow(q.y,4.),.25)/shape-1.)*lake_half.y;
}
void vertex(){world_pos=(MODEL_MATRIX*vec4(VERTEX,1.)).xyz;}
void fragment(){
 vec2 p=world_pos.xz;
 float d=work_distance(p);float shore=shore_distance(p);
 // Clean blue-white reference snow; shape and lighting supply the shading.
 vec3 snow=vec3(.97,.987,1.0);
 // A continuous blue shadow under the rounded, genuinely elevated snow lip.
 float rim=(1.-smoothstep(.02,.26,d))*smoothstep(-.08,.02,d);
 snow=mix(snow,vec3(.69,.79,.94),rim*.23);
 // Screen-derivative coverage keeps the painted boundary stable at every view.
 float aa=max(fwidth(d)*.75,.022);
 float cleared=1.-smoothstep(-aa,aa,d);
 // Uniform reference workfloor, without procedural mottling or edge dirt.
 vec3 floor=vec3(.815,.435,.29);
 float dist=length(p-furnace_center);
 float warmth=(1.-smoothstep(warmth_radius-.4,warmth_radius+.12,dist))*heat_strength;
 floor=mix(floor,floor+vec3(.025,.012,0.),warmth*.42);
 vec3 material=mix(snow,floor,cleared);
 // The submerged bank grades into a cool clean ice-blue face; not an extra plane.
 float ice=(1.-smoothstep(-.12,.035,shore));
 material=mix(material,vec3(.37,.67,.84),ice*.35);
 ALBEDO=pow(material,vec3(2.2));
 ROUGHNESS=mix(.91,.87,cleared);SPECULAR=.20;
}
