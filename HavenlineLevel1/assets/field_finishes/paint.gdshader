shader_type spatial;
render_mode cull_disabled, diffuse_burley, specular_schlick_ggx;

uniform vec4 pigment : source_color = vec4(1.0);
uniform float roughness : hint_range(0.0, 1.0) = 0.8;
uniform float metalness : hint_range(0.0, 1.0) = 0.0;
uniform bool vertex_paint = false;

void fragment() {
	vec3 vertex_color = OUTPUT_IS_SRGB ? COLOR.rgb : pow(COLOR.rgb, vec3(2.2));
	ALBEDO = pigment.rgb * (vertex_paint ? vertex_color : vec3(1.0));
	ROUGHNESS = roughness;
	METALLIC = metalness;
	SPECULAR = 0.5;
}
