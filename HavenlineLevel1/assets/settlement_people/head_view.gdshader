shader_type spatial;
render_mode cull_disabled;
uniform sampler2D studio: source_color, filter_linear_mipmap_anisotropic, repeat_disable;
uniform vec4 projection[8];
varying vec3 bind_position;
varying float azimuth;
void vertex(){
	bind_position = vec3(UV2.x, COLOR.r*1.50, UV2.y);
	vec3 local_view = (inverse(MODEL_MATRIX)*vec4(INV_VIEW_MATRIX[2].xyz,0.)).xyz;
	azimuth = atan(local_view.x,local_view.z)*4./PI;
}
vec2 studio_uv(int cell){
	float theta = float(cell)*PI*.25;
	vec4 p = projection[cell];
	float x = p.x+p.y*(bind_position.x*cos(theta)-bind_position.z*sin(theta));
	float y = p.z-p.y*bind_position.y;
	vec2 uv = clamp(vec2((x+.5)/368.,(y+.5)/p.w),vec2(.002),vec2(.998));
	return (vec2(float(cell%4),float(cell/4))+uv)/vec2(4.,2.);
}
void fragment(){
	float view = mod(azimuth,8.);
	int left = int(floor(view));
	int right = (left+1)%8;
	float transition = smoothstep(.37,.63,fract(view));
	ALBEDO=mix(texture(studio,studio_uv(left)).rgb,texture(studio,studio_uv(right)).rgb,transition);
	ROUGHNESS=.91;
}
