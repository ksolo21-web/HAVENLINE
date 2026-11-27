shader_type canvas_item;
render_mode unshaded;

void fragment() {
	vec2 p = abs((UV - 0.5) * 2.0);
	// The field badge uses clipped corners to keep all of the glasses, hair and collar.
	float d = max(max(p.x,p.y), (p.x+p.y)/1.67);
	vec4 face = texture(TEXTURE, UV);
	vec3 sky = mix(vec3(.30,.52,.58),vec3(.09,.24,.34),UV.y);
	vec3 color = mix(sky,face.rgb,face.a);
	color = mix(color,mix(vec3(.97,.85,.63),vec3(.65,.46,.25),UV.y),smoothstep(.87,.91,d));
	color = mix(color,vec3(.08,.17,.23),smoothstep(.93,.96,d));
	COLOR=vec4(color,1.-smoothstep(.96,1.,d));
}
