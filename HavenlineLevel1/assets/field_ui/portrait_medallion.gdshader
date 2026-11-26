shader_type canvas_item;
render_mode unshaded;

void fragment() {
	vec2 point = (UV - vec2(0.5)) * 2.0;
	float distance_to_center = length(point);
	vec4 face = texture(TEXTURE, UV);
	vec3 backdrop = mix(vec3(0.10, 0.19, 0.28), vec3(0.27, 0.43, 0.52), 1.0 - UV.y);
	vec3 brass = mix(vec3(0.79, 0.48, 0.19), vec3(1.0, 0.86, 0.55), 1.0 - UV.y);
	vec3 portrait = mix(backdrop, face.rgb, face.a);
	vec3 color = mix(portrait, vec3(0.09, 0.16, 0.22), smoothstep(0.82, 0.86, distance_to_center));
	color = mix(color, brass, smoothstep(0.87, 0.90, distance_to_center));
	color = mix(color, vec3(0.12, 0.18, 0.22), smoothstep(0.94, 0.97, distance_to_center));
	float alpha = 1.0 - smoothstep(0.97, 1.0, distance_to_center);
	COLOR = vec4(color, alpha);
}
