shader_type spatial;
render_mode diffuse_burley, specular_schlick_ggx;
// Opaque bounded water avoids full-screen refraction and transparent depth sorting.
// Runtime simulation time (not shader TIME) freezes coherently with pause/resume.
uniform float sim_time=0.0;
uniform vec2 lake_center=vec2(-7.6,-13.85);
uniform vec2 lake_half=vec2(5.2,1.85);
varying vec2 world_xz;
void vertex(){world_xz=(MODEL_MATRIX*vec4(VERTEX,1.)).xz;}
void fragment(){
 vec2 p=world_xz;vec2 q=abs(p-lake_center)/lake_half;
 float sd=(pow(pow(q.x,4.)+pow(q.y,4.),.25)-1.)*lake_half.y;
 float depth=1.-smoothstep(-.8,-.04,sd);
 vec3 base=mix(vec3(.16,.70,.87),vec3(.015,.46,.77),depth);
 float a=sin(p.x*2.5+p.y*1.5+sim_time*.75);
 float b=sin(p.x*-1.7+p.y*3.3-sim_time*.42);
 float caustic=pow(clamp((a+b)*.25+.5,0.,1.),7.0);
 base+=vec3(.07,.12,.13)*caustic;
 float shoreline=exp(-pow((sd+.30)/.07,2.0));
 base=mix(base,vec3(.49,.87,.95),shoreline*.48);
 ALBEDO=pow(base,vec3(2.2));ROUGHNESS=.29;SPECULAR=.36;
 // Small analytic slopes keep calm, rounded ripples without displacing the bank.
 NORMAL_MAP=normalize(vec3(cos(p.x*2.5+p.y*1.5+sim_time*.75)*.035,cos(p.x*-1.7+p.y*3.3-sim_time*.42)*.045,1.0))*.5+.5;
 NORMAL_MAP_DEPTH=.4;
}
