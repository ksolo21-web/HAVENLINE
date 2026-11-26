// A world-space capsule stays the same size as the character on either display
// and at either pinch setting. Only foreground fragments inside it are removed.
global uniform vec3 field_player_feet;
global uniform vec3 field_player_eye;

bool covers_field_player(vec3 point, vec2 pixel, vec3 pass_direction) {
	vec3 eye = field_player_eye;
	// Keep the original light-space shadow silhouette.
	if (dot(eye, pass_direction) < 0.999) {
		return false;
	}
	vec3 relative = point - (field_player_feet + vec3(0.0, 0.16, 0.0));
	float depth = dot(relative, eye);
	if (depth <= 0.0 || depth > 9.0) {
		return false;
	}
	vec3 body = vec3(0.0, 1.48, 0.0);
	vec3 projected_body = body - eye * dot(body, eye);
	vec3 projected = relative - eye * depth;
	float along = clamp(dot(projected, projected_body) / max(dot(projected_body, projected_body), 0.001), 0.0, 1.0);
	if (dot(relative - along * body, eye) <= 0.0) {
		return false;
	}
	vec3 offset = projected - along * projected_body;
	float radius_squared = dot(offset, offset);
	if (radius_squared >= 0.58 * 0.58) {
		return false;
	}
	float rim = smoothstep(0.39 * 0.39, 0.58 * 0.58, radius_squared);
	float dither = fract(52.9829189 * fract(dot(floor(pixel), vec2(0.06711056, 0.00583715))));
	return dither >= rim;
}
