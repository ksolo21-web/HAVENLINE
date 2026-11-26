shader_type spatial;

// The frame has one painted atlas. Preserve its timber, slate and lighting on
// every fragment outside the part that projects directly onto the character.
uniform sampler2D atlas : source_color, filter_linear_mipmap, repeat_enable;
uniform vec4 emission_tint : source_color;
uniform float roughness : hint_range(0.0,1.0) = 0.87;
uniform vec3 player_feet;
uniform vec3 toward_camera;
varying vec3 world_position;

void vertex() {
	world_position = (MODEL_MATRIX * vec4(VERTEX,1.0)).xyz;
}

void fragment() {
	vec3 relative = world_position - player_feet;
	vec3 body = vec3(0.0,2.15,0.0);
	vec3 projected_body = body - toward_camera*dot(body,toward_camera);
	vec3 projected = relative - toward_camera*dot(relative,toward_camera);
	float along = clamp(dot(projected,projected_body)/max(dot(projected_body,projected_body),0.001),0.0,1.0);
	float depth = dot(relative-along*body,toward_camera);
	if (depth>0.0) {
		float distance_to_body = length(projected-along*projected_body);
		float coverage = smoothstep(0.42,0.59,distance_to_body);
		float screen_dither = fract(52.9829189*fract(dot(floor(FRAGCOORD.xy),vec2(0.06711056,0.00583715))));
		if (coverage < 1.0 && screen_dither >= coverage) {
			discard;
		}
	}
	vec3 paint = texture(atlas,UV).rgb;
	ALBEDO = paint;
	ROUGHNESS = roughness;
	EMISSION = paint*emission_tint.rgb;
}
