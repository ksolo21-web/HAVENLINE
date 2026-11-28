shader_type spatial;
render_mode cull_disabled, diffuse_burley, specular_schlick_ggx;

// The owner's atlas contains many small UV islands. Preserve the kerchief and
// feather bands when the entire expedition owl occupies a few dozen pixels.
uniform sampler2D feather_color : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D packed_surface : hint_default_white, filter_linear_mipmap, repeat_enable;
uniform sampler2D feather_normals : hint_normal, filter_linear_mipmap, repeat_enable;
uniform float coverage : hint_range(0.0,1.0) = 1.0;
uniform bool folded = false;
uniform float lookout_yaw = 0.0;

void vertex() {
	if (folded && abs(lookout_yaw) > .001) {
		// Leave the bedroll and chest straps on the seated body. The high
		// front feather collar eases into the rotation at the original neck.
		float head = smoothstep(.416, .493, VERTEX.y) * smoothstep(.035, .145, VERTEX.z);
		float angle = lookout_yaw * head;
		float c = cos(angle);
		float s = sin(angle);
		mat2 twist = mat2(vec2(c, -s), vec2(s, c));
		vec2 neck = vec2(-.02, .173);
		VERTEX.xz = neck + twist * (VERTEX.xz - neck);
		NORMAL.xz = twist * NORMAL.xz;
		TANGENT.xz = twist * TANGENT.xz;
		BINORMAL.xz = twist * BINORMAL.xz;
	}
}

void fragment() {
	if (coverage < 1.0) {
		float dither = fract(52.9829189 * fract(dot(FRAGCOORD.xy, vec2(0.06711056, 0.00583715))));
		if ((folded ? 1.0-dither : dither) >= coverage) discard;
	}
	vec3 color = texture(feather_color, UV, -1.10).rgb;
	vec3 surface = texture(packed_surface, UV).rgb;
	ALBEDO = color;
	ROUGHNESS = max(0.20, surface.g);
	METALLIC = surface.b;
	NORMAL_MAP = texture(feather_normals, UV).rgb;
	float footprint = length(fwidth(UV) * vec2(textureSize(feather_color, 0)));
	NORMAL_MAP_DEPTH = mix(0.87, 0.54, smoothstep(6.0, 36.0, footprint));
	// Soft ambient reflection from the snow around the post and flight path.
	// It follows the actual painted albedo; direct lighting and shadows remain.
	EMISSION = color * vec3(0.14, 0.16, 0.18);
}
