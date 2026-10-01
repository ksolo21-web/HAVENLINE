shader_type spatial;
render_mode unshaded, blend_add, cull_disabled, depth_draw_never, depth_test_disabled;

uniform vec4 tint : source_color = vec4(0.36, 0.92, 1.0, 0.92);
uniform float role = 0.0;
uniform float emission_strength = 2.7;

varying vec3 authored_local_position;

void vertex() {
	authored_local_position = VERTEX;
}

void fragment() {
	float axial = clamp((authored_local_position.y + 0.32) / 0.64, 0.0, 1.0);
	float radial = clamp(length(authored_local_position.xz) * 3.2, 0.0, 1.0);
	float shimmer = 0.86 + 0.14 * sin(TIME * 5.4 + axial * 8.0 + role * 1.9);
	float rim = pow(1.0 - clamp(dot(normalize(NORMAL), normalize(VIEW)), 0.0, 1.0), 2.0);
	float burst = role > 1.5 ? (1.05 + 0.18 * sin(TIME * 7.0 + radial * 4.0)) : 1.0;
	vec3 glow = tint.rgb * (0.82 + 0.34 * shimmer + 0.46 * rim) * burst;
	ALBEDO = tint.rgb * 0.34;
	EMISSION = glow * emission_strength;
	ALPHA = tint.a * (0.70 + 0.22 * shimmer);
}
