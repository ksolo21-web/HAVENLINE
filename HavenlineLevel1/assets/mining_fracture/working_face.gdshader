shader_type spatial;
render_mode unshaded, shadows_disabled, depth_draw_never;

uniform vec3 bank_center;
uniform float bank_size = 1.0;
uniform float contacts = 1.0;
varying vec3 position_in_bank;

void vertex() {
	position_in_bank = (VERTEX - bank_center) / bank_size;
	VERTEX += NORMAL * (.0015 * bank_size);
}

void fragment() {
	vec3 p = position_in_bank;
	float a = dot(p,vec3(1.0,.24,.19)) - .065;
	float b = dot(p,vec3(-.34,-.14,1.0)) + .035;
	float grain = .007*sin(31.0*p.z+24.0*p.y) + .004*sin(56.0*p.x-42.0*p.y);
	float seam = abs(a + grain);
	if (contacts > 1.5) seam = min(seam, abs(b - grain));
	float width = .012 + .009*contacts;
	if (seam > width) discard;
	float lip = smoothstep(.38*width,.80*width,seam);
	ALBEDO = mix(vec3(.045,.038,.035),vec3(.34,.31,.28),lip);
	ALPHA = mix(.93,.58,lip);
}
