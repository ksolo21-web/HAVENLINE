shader_type spatial;
render_mode unshaded, cull_back, shadows_disabled, fog_disabled;

uniform vec3 depth_origin;
uniform vec3 depth_eye;
varying float cover_depth;

void vertex() {
	vec3 at = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	cover_depth = 0.5 + dot(at - depth_origin, depth_eye) * 0.0625;
}

void fragment() {
	float depth = clamp(cover_depth, 0.0, 1.0);
	ALBEDO = vec3(floor(depth * 255.0) / 255.0, fract(depth * 255.0), 0.0);
}
