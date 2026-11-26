shader_type spatial;
render_mode diffuse_burley, specular_schlick_ggx;

// Optional panel-local variant. No environmental fill, directional-light or
// camera changes. Palette vectors are sRGB source colors: assign by label.
uniform vec4 cream_pigment : source_color = vec4(0.96,0.79,0.55,1.0);
uniform vec4 amber_pigment : source_color = vec4(0.86,0.60,0.34,1.0);
uniform vec4 wood_shadow : source_color = vec4(0.57,0.27,0.13,1.0);
uniform vec4 wood_face : source_color = vec4(0.82,0.45,0.25,1.0);
uniform vec4 snow_lip : source_color = vec4(0.67,0.78,0.92,1.0);
uniform vec4 snow_crown : source_color = vec4(0.92,0.96,1.0,1.0);
uniform int style_role = 0; // 0 wood/1 snow/2 warm hemp/3 cream hemp
uniform float paint_strength : hint_range(0.0,1.0) = 1.0;
varying vec3 local_v;
varying vec3 local_n;
void vertex() {
	local_v = VERTEX;
	local_n = NORMAL;
}
void fragment() {
	vec3 n = normalize(local_n);
	float broad_face = smoothstep(0.22,0.78,abs(n.z));
	vec3 fiber_axis = normalize(vec3(-0.39,0.83,0.39));
	float fiber_turn = 0.5+0.5*dot(n,fiber_axis);
	vec3 pigment;
	float quiet_reflectance;
	float rough;
	if (style_role == 0) {
		float waviness = sin(local_v.y*5.6 + sin(local_v.x*19.0)*0.53);
		float woodgrain = 0.5+0.5*sin(local_v.x*47.0 + .92*waviness + local_v.z*13.0);
		pigment = mix(wood_shadow.rgb,wood_face.rgb,(0.47+0.39*broad_face)*(0.86+0.14*woodgrain));
		quiet_reflectance = 0.105;
		rough = 0.86;
	} else if (style_role == 1) {
		float edge = smoothstep(0.03,0.83,max(n.y,0.0));
		pigment = mix(snow_lip.rgb,snow_crown.rgb,edge);
		quiet_reflectance = 0.13;
		rough = 0.82;
	} else {
		// Broad unbroken gold/cream core survives the stock pixel footprint;
		// tiny fiber grain never drives pigment fully dark or breaks the run.
		float micro = 0.5+0.5*sin(local_v.x*91.0 + local_v.y*118.0);
		vec3 coat = style_role == 3 ? cream_pigment.rgb : amber_pigment.rgb;
		pigment = coat*(0.83+0.13*fiber_turn+0.04*micro);
		quiet_reflectance = style_role == 3 ? 0.33 : 0.31;
		rough = 0.79;
	}
	ALBEDO = pigment;
	EMISSION = pigment * quiet_reflectance * paint_strength;
	ROUGHNESS = rough;
	SPECULAR = 0.24;
	METALLIC = 0.0;
}
