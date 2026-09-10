shader_type spatial;
render_mode diffuse_burley, specular_schlick_ggx;
// T02 finish revision: softly packed snow/earth contact and restrained material
// variation. One continuous opaque surface, no decals, vertex displacement,
// added draw calls or time-dependent ground pattern. Approved trees untouched.
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
float material_hash(vec2 p){
 vec3 h=fract(vec3(p.xyx)*vec3(.1031,.1030,.0973));
 h+=dot(h,h.yzx+33.33);return fract((h.x+h.y)*h.z);
}
float material_noise(vec2 p){
 vec2 cell=floor(p), f=fract(p);f=f*f*(3.-2.*f);
 return mix(mix(material_hash(cell),material_hash(cell+vec2(1,0)),f.x),
            mix(material_hash(cell+vec2(0,1)),material_hash(cell+vec2(1,1)),f.x),f.y);
}
void vertex(){world_pos=(MODEL_MATRIX*vec4(VERTEX,1.)).xyz;}
void fragment(){
 vec2 p=world_pos.xz;
 float d=work_distance(p);float shore=shore_distance(p);
 // Bounded cool tone changes follow world space rather than the screen,
 // retaining the references' clean stylization rather than gritty realism.
 float broad=material_noise(p*.37)-.5;
 float fine=material_noise(p*7.8)-.5;
 float footprint=max(length(dFdx(p)),length(dFdy(p)));
 float detail_weight=1.-smoothstep(.025,.16,footprint);
 vec3 snow=vec3(.955,.976,1.0)+vec3(.042,.029,.016)*broad;
 snow+=vec3(.012,.010,.008)*fine*detail_weight;
 float rim=(1.-smoothstep(.04,.48,d))*smoothstep(-.16,.04,d);
 snow=mix(snow,vec3(.73,.82,.94),rim*.16);
 // A narrow packed-snow transition is softly feathered, not a muddy halo.
 // Screen derivatives add coverage without changing the physical bank.
 float aa=max(fwidth(d)*.75,.022);
 float edge_d=d+(material_noise(p*1.6)-.5)*.035;
 float cleared=1.-smoothstep(-.08-aa,.13+aa,edge_d);
 // Restrained peach/clay variation and wear, without checkerboard tiling.
 vec3 floor=vec3(.80,.48,.36)+vec3(.046,.032,.023)*broad;
 floor+=vec3(.010,.008,.006)*fine*detail_weight;
 float dist=length(p-furnace_center);
 float warmth=(1.-smoothstep(warmth_radius-.4,warmth_radius+.12,dist))*heat_strength;
 floor=mix(floor,floor+vec3(.025,.012,0.),warmth*.42);
 vec3 material=mix(snow,floor,cleared);
 // The submerged bank grades into a cool clean ice-blue face; not an extra plane.
 float ice=(1.-smoothstep(-.12,.035,shore));
 material=mix(material,vec3(.37,.67,.84),ice*.35);
 ALBEDO=pow(material,vec3(2.2));
 // Very small grain slopes soften highlights; they do not deform geometry.
 float sx=cos(p.x*8.1+p.y*3.7)*.006;
 float sz=cos(p.x*-4.6+p.y*9.3)*.006;
 NORMAL=normalize(NORMAL+(VIEW_MATRIX*vec4(-sx,0.,-sz,0.)).xyz*detail_weight);
 ROUGHNESS=clamp(mix(.92,.88,cleared)+fine*.028*detail_weight,.84,.95);
 SPECULAR=.18;
}
