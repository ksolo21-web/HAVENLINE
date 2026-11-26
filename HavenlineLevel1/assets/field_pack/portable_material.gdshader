shader_type spatial;
render_mode diffuse_burley, specular_schlick_ggx;

// The GLBs hold the authored albedo palette in COLOR_0. Keep its sRGB
// interpretation consistent between the mobile and compatibility renderers.
uniform int surface_kind : hint_enum("Timber", "Slate", "Steel", "Fuel can", "Tool") = 0;
varying vec3 surface_position;
varying vec3 surface_normal;

void vertex() {
	surface_position = VERTEX;
	surface_normal = NORMAL;
}

vec3 linear_palette(vec3 color) {
	return mix(color / 12.92, pow((color + 0.055) / 1.055, vec3(2.4)),
		step(vec3(0.04045), color));
}

// Fade grain smaller than one screen pixel; distant cargo retains its silhouette.
float band(float phase) {
	return sin(phase) * (1.0 - smoothstep(0.65, 2.7, fwidth(phase)));
}

float lattice(vec2 corner) {
	vec3 seed = fract(vec3(corner.xyx) * vec3(0.1031, 0.1030, 0.0973));
	seed += dot(seed, seed.yzx + 33.33);
	return fract((seed.x + seed.y) * seed.z);
}

float mottling(vec2 point) {
	vec2 cell = floor(point);
	vec2 blend = smoothstep(vec2(0.0), vec2(1.0), fract(point));
	float coarse = mix(mix(lattice(cell), lattice(cell + vec2(1, 0)), blend.x),
		mix(lattice(cell + vec2(0, 1)), lattice(cell + vec2(1, 1)), blend.x), blend.y);
	return (coarse - 0.5) * (1.0 - smoothstep(0.5, 1.3, length(fwidth(point))));
}

void fragment() {
	vec3 p = surface_position;
	vec3 color = COLOR.rgb;
	float roughness = 0.9;
	float metallic = 0.0;
	float variation = 0.0;
	if (surface_kind == 0) {
		float ring = length(p.yz - vec2(0.442, 0.012));
		float cross_grain = p.z * 33.0 + p.y * 17.0;
		float bark = mottling(vec2(p.x * 4.0, cross_grain + sin(p.x * 3.7)));
		float end = band(ring * 81.0 + 2.1 * mottling(p.yz * 9.0));
		variation = mix(0.34 * bark, 0.065 * end, abs(surface_normal.x));
		roughness = 0.89 + variation * 0.35;
	} else if (surface_kind == 1) {
		vec2 mineral = vec2(p.x + 0.6 * p.z, p.y);
		float fracture = mottling(mineral * vec2(8.0, 29.0));
		variation = 0.21 * fracture + 0.035 * band(p.y * 74.0 + fracture * 5.3);
		roughness = 0.78 + 0.06 * band((p.x + p.z) * 9.0);
	} else if (surface_kind == 2) {
		variation = 0.12 * mottling(vec2(p.x * 2.5, p.y * 69.0 + p.z * 71.0));
		roughness = 0.43 + variation;
		metallic = 0.52;
	} else if (surface_kind == 3) {
		variation = 0.065 * mottling(vec2(p.x + p.z, p.y) * 36.0);
		roughness = 0.55 + variation;
		metallic = 0.08;
	} else {
		// Desaturated steel blades and collars share this draw with the stained
		// wooden handle and colored wraps. Palette hue separates their finish.
		float chroma = max(color.r, max(color.g, color.b)) - min(color.r, min(color.g, color.b));
		float steel = 1.0 - smoothstep(0.09, 0.27, chroma);
		metallic = mix(0.04, 0.52, steel);
		roughness = mix(0.76, 0.39, steel);
		variation = 0.05 * band(p.x * 47.0 + p.z * 29.0 + sin(p.y * 4.0));
	}
	ALBEDO = (OUTPUT_IS_SRGB ? color : linear_palette(color)) * (1.0 + variation);
	ROUGHNESS = roughness;
	METALLIC = metallic;
}
