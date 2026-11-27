shader_type spatial;
render_mode diffuse_burley, specular_schlick_ggx;
#include "res://assets/field_world/character_sightline.gdshaderinc"

uniform sampler2D paint : source_color, filter_linear_mipmap, repeat_enable;
uniform sampler2D paint_ultra : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D relief : hint_normal, filter_linear_mipmap, repeat_enable;
uniform sampler2D relief_ultra : hint_normal, filter_linear_mipmap_anisotropic, repeat_enable;
uniform vec4 tint : source_color = vec4(1.0);
uniform vec4 emission : source_color;
uniform float emission_energy;
uniform float roughness = 1.0;
uniform float metalness;
uniform float specular = 0.5;
uniform float relief_depth = 1.0;
uniform bool has_relief;
uniform bool vertex_paint;
uniform bool ultra_filter;
uniform bool worker_window;
uniform bool worker_in_view;
uniform vec3 worker_origin;
varying vec3 world_position;

void vertex() {
	world_position = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	vec3 eye = INV_VIEW_MATRIX[2].xyz;
	vec3 offset = world_position - worker_origin - vec3(0.0, 1.0, 0.0);
	float depth = dot(offset, eye);
	vec3 projected = offset - eye * depth;
	float footprint = dot(projected, projected);
	float speckle = fract(dot(floor(FRAGCOORD.xy), vec2(0.7548777, 0.5698403)));
	float window = smoothstep(0.20, 0.54, footprint);
	bool cover_worker = worker_window && worker_in_view && dot(eye, field_player_eye) > 0.999 && depth > 0.06 && depth < 3.8 && speckle >= window;
	if (cover_worker || covers_field_player(world_position, FRAGCOORD.xy, eye)) {
		discard;
	}
	vec3 albedo = ultra_filter ? texture(paint_ultra, UV).rgb : texture(paint, UV).rgb;
	ALBEDO = albedo * tint.rgb * (vertex_paint ? COLOR.rgb : vec3(1.0));
	ROUGHNESS = roughness;
	METALLIC = metalness;
	SPECULAR = specular;
	EMISSION = emission.rgb * emission_energy;
	if (has_relief) {
		NORMAL_MAP = ultra_filter ? texture(relief_ultra, UV).rgb : texture(relief, UV).rgb;
		NORMAL_MAP_DEPTH = relief_depth;
	}
}
