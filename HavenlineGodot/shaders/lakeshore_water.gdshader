shader_type spatial;
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
