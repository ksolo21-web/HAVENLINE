shader_type spatial;
// The shell uses a single painted atlas. Open only the bay actually connected
// to a paid guide, while retaining the shell's original paint and emissive fill.
uniform sampler2D painted_timber : source_color, filter_linear_mipmap, repeat_enable;
uniform bool utility_receiving;
uniform bool utility_dispatch;
uniform bool food_receiving;
uniform bool food_dispatch;
uniform bool cold_dispatch;
varying vec3 house_point;
void vertex() {
	house_point = VERTEX;
}
void fragment() {
	vec3 p = house_point;
	if (p.x < -1.16 && p.y > 0.41 && p.y < 0.85) {
		if ((utility_receiving && abs(p.z - 0.06) < 0.21) || (utility_dispatch && abs(p.z + 0.67) < 0.21)) { discard; }
	}
	if (p.x > 1.16 && cold_dispatch && abs(p.z - 0.28) < 0.21 && p.y > 0.31 && p.y < 0.63) { discard; }
	if (p.z < -0.82 && p.y > 0.94 && p.y < 1.39) {
		if ((food_receiving && abs(p.x - 0.55) < 0.21) || (food_dispatch && abs(p.x + 0.50) < 0.21)) { discard; }
	}
	vec3 paint = texture(painted_timber, UV).rgb;
	ALBEDO = paint;
	ROUGHNESS = 0.87;
	EMISSION = paint * 0.22;
}
