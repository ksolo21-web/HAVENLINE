shader_type spatial;
render_mode unshaded, blend_mix, depth_draw_never, depth_test_disabled, cull_back, shadows_disabled, fog_disabled;

uniform sampler2D tower_depth : repeat_disable, filter_nearest;
uniform sampler2D scene_depth : hint_depth_texture, repeat_disable, filter_nearest;
uniform vec3 depth_origin;
uniform vec3 depth_eye;
uniform vec4 outline : source_color = vec4(0.43, 0.81, 0.94, 0.52);
varying float guard_depth;

void vertex() {
	vec3 at = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	guard_depth = 0.5 + dot(at - depth_origin, depth_eye) * 0.0625;
}

void fragment() {
	vec4 cover = texture(tower_depth, SCREEN_UV);
	float depth = cover.r + cover.g / 255.0;
	if (cover.a < 0.5 || depth - guard_depth <= 0.00375) {
		discard;
	}
	float measured = texture(scene_depth, SCREEN_UV).r;
	vec3 ndc = vec3(SCREEN_UV * 2.0 - 1.0, measured);
#if CURRENT_RENDERER == RENDERER_COMPATIBILITY
	ndc.z = measured * 2.0 - 1.0;
#endif
	vec4 point = INV_PROJECTION_MATRIX * vec4(ndc, 1.0);
	vec3 foreground = (INV_VIEW_MATRIX * vec4(point.xyz / point.w, 1.0)).xyz;
	float foreground_depth = 0.5 + dot(foreground - depth_origin, depth_eye) * 0.0625;
	// The reduced-resolution tower mask must agree with the exact visible
	// surface. This excludes the guard's exposed glove or boot at an edge.
	if (abs(foreground_depth - depth) > 0.0022) {
		discard;
	}
	float edge = 1.0 - clamp(dot(normalize(NORMAL), normalize(VIEW)), 0.0, 1.0);
	ALBEDO = outline.rgb;
	ALPHA = outline.a * mix(0.35, 1.0, edge * edge);
}
