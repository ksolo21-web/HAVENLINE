shader_type spatial;
render_mode diffuse_burley, specular_schlick_ggx;

global uniform vec3 field_player_feet;
global uniform vec3 field_player_eye;
uniform sampler2D paint : source_color, filter_linear_mipmap_anisotropic, hint_default_white;
uniform vec4 tint : source_color = vec4(1.0);
uniform vec4 glow : source_color = vec4(0.0);
uniform sampler2D glow_map : source_color, filter_linear_mipmap_anisotropic, hint_default_white;
uniform float glow_power;
uniform float roughness = 0.86;
uniform float metalness;
uniform float specular = 0.5;
varying vec3 world_point;

void vertex() {
	world_point = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	// Keep the tower of bundles solid above the head and behind the hero.
	// Eye-space distances are in metres, so the portrait survives either zoom.
	vec3 eye = field_player_eye;
	vec3 offset = world_point - field_player_feet - vec3(0.0, 1.46, 0.0);
	if (dot(eye, INV_VIEW_MATRIX[2].xyz) > 0.999 && dot(offset, eye) > 0.10) {
		vec2 portrait = vec2(dot(offset, INV_VIEW_MATRIX[0].xyz), dot(offset, INV_VIEW_MATRIX[1].xyz));
		float distance_to_head = length(portrait / vec2(0.255, 0.277));
		float cleared = 1.0 - smoothstep(0.78, 1.06, distance_to_head);
		float dither = fract(52.9829189 * fract(dot(floor(FRAGCOORD.xy), vec2(0.06711056, 0.00583715))));
		if (cleared > dither) {
			discard;
		}
	}
	ALBEDO = texture(paint, UV).rgb * tint.rgb;
	ROUGHNESS = roughness;
	METALLIC = metalness;
	SPECULAR = specular;
	EMISSION = glow.rgb * texture(glow_map, UV).rgb * glow_power;
}
