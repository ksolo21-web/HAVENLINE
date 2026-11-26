shader_type spatial;
render_mode cull_back, diffuse_burley, specular_schlick_ggx;

uniform vec4 base_tint : source_color;
uniform int family = 0; // board, frame, snow, rope, iron
uniform int front_latch_role = 0;
uniform float stock_roughness = 0.83;
varying vec3 p_local;
varying vec3 n_local;
varying vec3 n_world;

void vertex() {
	p_local = VERTEX;
	n_local = NORMAL;
	n_world = MODEL_NORMAL_MATRIX * NORMAL;
}
void fragment() {
	vec3 n = normalize(n_local);
	// Unchanged opening sun; rotates with real gate faces, not camera or gate ID.
	const vec3 SUN = vec3(-0.3141377915, 0.7431448255, 0.5908072582);
	float facing = smoothstep(0.13, 0.54, dot(normalize(n_world), SUN));
	float up = smoothstep(-0.35, 0.90, n.y);
	float roll = 1.0 - abs(n.z);
	vec3 p = vec3(abs(p_local.x), p_local.yz);
	vec3 pigment = base_tint.rgb;
	float fill = 0.07;
	ROUGHNESS = stock_roughness;
	METALLIC = 0.0;
	SPECULAR = 0.19;
	if (family <= 1) {
		float grain = 0.5 + 0.5 * sin(77.0 * p.x + 0.62 * sin(7.0 * p.y + 3.0 * p.x));
		float surface_detail = 0.83 + 0.10 * grain + 0.07 * up;
		float bevel = family == 1 ? (0.86 + 0.14 * roll) : 0.92;
		vec3 lit_limit = mix(vec3(1.0), vec3(0.66, 0.82, 0.90), facing);
		pigment *= surface_detail * bevel * lit_limit;
		// Separate exterior and rear from the actual surface normals. Neither blackens.
		float face = 0.90 + 0.10 * smoothstep(-0.92, 0.74, n.z);
		fill = (family == 1 ? 0.43 : 0.40) * face * mix(1.0, 0.055, facing);
	} else if (family == 2) {
		// Rolls remain cool under a lip and white over its crown, not a uniformly white strip.
		pigment *= mix(vec3(0.61, 0.72, 0.89), vec3(0.93, 0.96, 0.98), up);
		fill = mix(0.36, 0.49, up) * mix(1.0, 0.68, facing);
		SPECULAR = 0.14;
	} else if (family == 3) {
		pigment *= mix(vec3(0.65, 0.65, 0.69), vec3(0.89, 0.91, 0.93), up);
		fill = mix(0.35, 0.44, up) * mix(1.0, 0.18, facing);
		SPECULAR = 0.10;
	} else {
		// Iron stays dark steel; silver-gray raised edges are distinct from the timber.
		float edge = clamp(0.64 * roll + 0.36 * up, 0.0, 1.0);
		pigment *= 0.72 + 0.44 * edge;
		fill = mix(0.35, 0.78, edge) * mix(1.0, 0.43, facing);
		METALLIC = 0.15;
		// Owner sheet 33040: a charcoal keeper/rosette, with a broader satin
		// face on the movable dark lever. No cosmetic bar spans the gate seam.
		if (front_latch_role > 0) {
			float bevel = smoothstep(0.15, 0.81, roll);
			float satin = 0.63 + 0.25 * up + 0.12 * bevel;
			vec3 graphite = vec3(0.044, 0.060, 0.084);
			vec3 satin_steel = vec3(0.23, 0.28, 0.34);
			float face_scale = front_latch_role == 2 ? 1.0 : 0.49;
			pigment = mix(graphite, satin_steel, face_scale * satin);
			fill = mix(0.61, 0.76, up) * mix(1.0, 0.38, facing);
			METALLIC = 0.18;
			SPECULAR = 0.25;
		}
	}
	ALBEDO = clamp(pigment, vec3(0.0), vec3(0.97));
	EMISSION = min(ALBEDO * fill, family == 2 ? vec3(0.40) : vec3(0.24));
}
