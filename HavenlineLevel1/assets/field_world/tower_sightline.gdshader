shader_type spatial;
render_mode unshaded, cull_back, depth_draw_never, depth_test_disabled;

uniform sampler2D scene_depth : hint_depth_texture, repeat_disable, filter_nearest;

void fragment() {
	float depth = texture(scene_depth, SCREEN_UV).r;
	float ndc = mix(CLIP_SPACE_FAR, 1.0, depth);
	vec4 front = INV_PROJECTION_MATRIX * vec4(SCREEN_UV * 2.0 - 1.0, ndc, 1.0);
	if (VERTEX.z >= front.z / front.w - 0.06) {
		discard;
	}
	float rim = pow(1.0 - abs(dot(normalize(NORMAL), normalize(VIEW))), 1.8);
	ALBEDO = vec3(0.82, 0.90, 0.94);
	ALPHA = 0.08 + 0.69 * rim;
}
