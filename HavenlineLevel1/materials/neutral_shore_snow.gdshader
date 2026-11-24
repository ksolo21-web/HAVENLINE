shader_type spatial;
render_mode diffuse_burley, specular_schlick_ggx;

uniform vec4 snow_color : source_color = vec4(0.88, 0.93, 0.98, 1.0);
uniform vec4 shore_color : source_color = vec4(0.68, 0.77, 0.86, 1.0);
uniform float snow_roughness : hint_range(0.85, 1.0) = 0.95;
uniform float shore_roughness : hint_range(0.85, 1.0) = 0.89;
varying vec2 world_xz;
varying float encoded_shore;

float lattice(vec2 h) {
	return fract(sin(dot(h, vec2(127.1, 311.7))) * 43758.5453);
}

float soft_noise(vec2 p) {
	vec2 cell = floor(p);
	vec2 f = fract(p);
	f = f * f * (3.0 - 2.0 * f);
	return mix(mix(lattice(cell), lattice(cell + vec2(1.0, 0.0)), f.x),
		mix(lattice(cell + vec2(0.0, 1.0)), lattice(cell + vec2(1.0)), f.x), f.y);
}

void vertex() {
	world_xz = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xz;
	encoded_shore = COLOR.r;
}

void fragment() {
	// Accepted Surface's encoded shore field is presentation input only.
	// Decode range [-4,4]; collision and dryness remain owned by the CPU.
	float shore = encoded_shore * 8.0 - 4.0;
	float snow_weight = smoothstep(0.30, 1.45, shore);
	float pixel_footprint = max(length(dFdx(world_xz)), length(dFdy(world_xz)));
	float grain_fade = 1.0 - smoothstep(0.025, 0.16, pixel_footprint);
	float broad = (soft_noise(world_xz * 0.42) - 0.5) * 0.055;
	float grain = (soft_noise(world_xz * 7.8) - 0.5) * 0.025 * grain_fade;
	vec3 sky_snow = mix(shore_color.rgb, snow_color.rgb, snow_weight);
	ALBEDO = clamp(sky_snow * (1.0 + broad + grain), vec3(0.0), vec3(1.0));
	ROUGHNESS = mix(shore_roughness, snow_roughness, snow_weight);
	SPECULAR = 0.20;
}
