shader_type spatial;
render_mode diffuse_burley, specular_schlick_ggx, depth_prepass_alpha;
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
uniform bool canopy;
uniform bool pine_bark;
uniform bool worker_in_view;
uniform vec3 worker_origin;
varying vec3 world_position;

void vertex() {
	world_position = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

float boot_support_opacity(vec3 feet, vec3 eye, vec2 radii, float snow_floor) {
	vec3 offset = world_position - feet;
	float depth = dot(offset, eye);
	vec3 projected = offset - eye * depth;
	float opening = smoothstep(radii.x, radii.y, length(projected));
	float in_front = smoothstep(0.0, 0.10, depth) * (1.0 - smoothstep(4.15, 4.4, depth));
	float above_snow = smoothstep(snow_floor, snow_floor + 0.18, offset.y);
	return mix(1.0, opening, in_front * above_snow);
}

void fragment() {
	vec3 eye = INV_VIEW_MATRIX[2].xyz;
	bool main_view = dot(eye, field_player_eye) > 0.999;
	float opacity = 1.0;
	if (main_view) {
		if (canopy) {
			float player_distance = sqrt(field_player_sightline_offset_sq(world_position, eye));
			opacity = min(smoothstep(0.35, 0.63, player_distance), boot_support_opacity(field_player_feet, eye, vec2(0.43, 0.70), 0.06));
			if (worker_in_view) {
				vec3 offset = world_position - worker_origin - vec3(0.0, 1.0, 0.0);
				float depth = dot(offset, eye);
				vec3 projected = offset - eye * depth;
				float behind_crown = smoothstep(0.0, 0.14, depth) * (1.0 - smoothstep(3.55, 3.80, depth));
				float worker_opacity = mix(1.0, smoothstep(0.36, 0.74, length(projected)), behind_crown);
				opacity = min(opacity, min(worker_opacity, boot_support_opacity(worker_origin, eye, vec2(0.43, 0.70), 0.06)));
			}
		} else if (pine_bark) {
			float player_distance = sqrt(field_player_sightline_offset_sq(world_position, eye));
			// Match the canopy opening at the silhouette and the support snow.
			// Outside that local opening the bark stays fully visible.
			float body = smoothstep(0.40, 0.77, player_distance);
			float boots = boot_support_opacity(field_player_feet, eye, vec2(0.55, 0.88), 0.0);
			opacity = mix(0.055, 1.0, min(body, boots));
		} else if (covers_field_player(world_position, FRAGCOORD.xy, eye)) {
			discard;
		}
	}
	// The prepass retains ordinary depth and shadows where the crown is intact.
	// Partial coverage around the cutout blends instead of stippling the skirt.
	ALPHA = opacity;
	if (opacity < 0.004) {
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
