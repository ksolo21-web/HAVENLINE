shader_type spatial;
render_mode unshaded,cull_disabled,depth_draw_never;
uniform sampler2D track_mask : filter_linear_mipmap, repeat_disable;
varying vec4 stamp;
void vertex() { stamp = INSTANCE_CUSTOM; }
void fragment() {
	// Snow surface UV.y grows towards +Z; the atlas toes are at the top.
	vec2 uv = vec2(UV.x, 1.0-UV.y);
	if (stamp.z > .5) { uv.x = 1.0 - uv.x; }
	float toe = length(vec2((abs(uv.x - .5) - mix(.122,.178,uv.y)) * 7.45,(uv.y - .48) * 2.75));
	vec2 hoof = vec2(1.0 - smoothstep(.70,.91,toe),smoothstep(.70,.91,toe) * (1.0 - smoothstep(.92,1.10,toe)));
	vec2 texel;
	if (stamp.x > .5 && stamp.y > .5) {
		float across = abs(uv.x - .5);
		float strip = 1.0 - smoothstep(.32,.48,across);
		float tread = 1.0 - smoothstep(.20,.44,abs(fract(uv.y*5.0 + across*.67)-.5));
		float ends = smoothstep(0.,.09,uv.y) * (1. - smoothstep(.91,1.,uv.y));
		texel = vec2(strip*mix(.18,.49,tread), strip*tread*.18)*ends;
	} else {
		uv.x = (uv.x + stamp.y) * .5;
		texel = mix(texture(track_mask, uv).rg, hoof, stamp.x);
	}
	float fade = stamp.w;
	float recess = texel.r;
	float rim = texel.g;
	ALBEDO = mix(vec3(.16,.24,.35),vec3(.91,.96,1.0),rim / max(.001,recess+rim));
	ALPHA = clamp(recess*.66+rim*.50,0.0,1.0)*fade;
}
