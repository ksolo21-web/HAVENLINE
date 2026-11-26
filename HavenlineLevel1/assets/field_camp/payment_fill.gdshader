shader_type spatial;
render_mode unshaded, cull_disabled;
uniform float paid : hint_range(0.,1.) = 0.;
uniform vec4 grounded : source_color = vec4(.20,.23,.18,1.);
uniform vec4 funded : source_color = vec4(.24,.77,.12,1.);
varying float z_on_plot;
void vertex(){z_on_plot=VERTEX.z;}
void fragment(){
	float t=clamp((z_on_plot+1.06)/2.12,0.,1.);
	float green=1.-smoothstep(paid-.012,paid+.012,t);
	ALBEDO=mix(grounded.rgb,funded.rgb,green);
}
