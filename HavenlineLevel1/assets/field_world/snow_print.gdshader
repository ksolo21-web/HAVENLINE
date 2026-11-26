shader_type spatial;
render_mode unshaded,cull_disabled,depth_draw_never;
uniform sampler2D track_mask : filter_linear_mipmap, repeat_disable;
varying vec4 stamp;
void vertex() { stamp = INSTANCE_CUSTOM; }
void fragment() {
	// PlaneMesh UV.y grows towards +Z; the atlas toes are at the top.
	vec2 uv = vec2(UV.x, 1.0-UV.y);
	if (stamp.z > .5) { uv.x = 1.0 - uv.x; }
	uv.x = (uv.x + stamp.y) * .5;
	vec2 texel = texture(track_mask, uv).rg;
	float fade = stamp.w;
	float recess = texel.r;
	float rim = texel.g;
	ALBEDO = mix(vec3(.16,.24,.35),vec3(.91,.96,1.0),rim / max(.001,recess+rim));
	ALPHA = clamp(recess*.66+rim*.50,0.0,1.0)*fade;
}
