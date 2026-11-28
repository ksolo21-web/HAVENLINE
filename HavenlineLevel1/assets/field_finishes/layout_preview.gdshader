shader_type spatial;
render_mode cull_disabled, depth_prepass_alpha, diffuse_burley, specular_schlick_ggx;

uniform vec4 pigment : source_color = vec4(1.0);

void fragment() {
	ALBEDO = pigment.rgb;
	ALPHA = pigment.a;
	ROUGHNESS = 0.77;
	SPECULAR = 0.5;
}
