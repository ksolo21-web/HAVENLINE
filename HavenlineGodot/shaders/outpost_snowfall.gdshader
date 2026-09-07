shader_type spatial;
render_mode unshaded, cull_disabled, blend_mix, depth_draw_never;
uniform float sim_time = 0.0;
uniform float snow_amount = 0.1;
uniform float wind = 0.15;
uniform vec3 follow_center = vec3(0.0);
varying float particle_alpha;
void vertex() {
 float seed=INSTANCE_CUSTOM.r;
 float speed=.72+INSTANCE_CUSTOM.g*.95;
 vec3 p=MODEL_MATRIX[3].xyz;
 p.y=mod(p.y-sim_time*speed,13.0)-.6;
 p.x=mod(p.x+sim_time*(.18+wind*1.65)+.3*sin(sim_time*.6+seed*50.),24.0)-12.0;
 p.z=mod(p.z+sim_time*.13,24.0)-12.0;
 p+=follow_center;
 vec3 right=INV_VIEW_MATRIX[0].xyz; vec3 up=INV_VIEW_MATRIX[1].xyz;
 float scale=.019+INSTANCE_CUSTOM.b*.035;
 vec3 wp=p+(right*VERTEX.x+up*VERTEX.y)*scale;
 VERTEX=(inverse(MODELVIEW_MATRIX)*VIEW_MATRIX*vec4(wp,1.0)).xyz;
 particle_alpha=smoothstep(seed-.08,seed+.02,snow_amount)*.62;
}
void fragment() {
 float d=length(UV-vec2(.5))*2.0;
 ALBEDO=vec3(.91,.96,1.0);
 ALPHA=(1.0-smoothstep(.1,1.0,d))*particle_alpha;
}
