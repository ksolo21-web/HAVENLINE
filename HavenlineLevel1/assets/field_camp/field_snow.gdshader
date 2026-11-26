shader_type spatial;
render_mode diffuse_burley, specular_schlick_ggx;

uniform float reveal : hint_range(0.,1.) = 0.;
uniform vec2 half_court = vec2(5.,4.);
uniform vec2 court_center = vec2(0.);
varying vec2 field_xz;
float hash(vec2 p) {
	vec3 q = fract(vec3(p.xyx)*vec3(.1031,.103,.0973));
	q += dot(q,q.yzx+33.33);
	return fract((q.x+q.y)*q.z);
}
float snow_noise(vec2 p) {
	vec2 i=floor(p), t=fract(p); t=t*t*(3.-2.*t);
	return mix(mix(hash(i),hash(i+vec2(1.,0.)),t.x),mix(hash(i+vec2(0.,1.)),hash(i+vec2(1.)),t.x),t.y);
}
void vertex() { field_xz=(MODEL_MATRIX*vec4(VERTEX,1.)).xz; }
void fragment(){
	vec2 p=field_xz;
	float broad=snow_noise(p*.42)-.5;
	float fine=snow_noise(p*7.8)-.5;
	vec2 q=abs(p-court_center)-half_court+vec2(.32);
	float edge=length(max(q,vec2(0.)))+min(max(q.x,q.y),0.)-.32;
	float boundary=edge+.045*broad;
	float court=(1.-smoothstep(-.13,.02,boundary))*smoothstep(min(length(p)*.12,.79),min(length(p)*.12,.79)+.18,reveal);
	vec3 snow=vec3(1.002,1.060,1.092)+broad*vec3(.032,.023,.012)+fine*.01;
	vec3 packed=vec3(.95,.705,.57)+broad*vec3(.047,.038,.021)+fine*.016;
	float amber=(1.-smoothstep(.04,.19,abs(reveal-min(length(p)*.12,.79)-.08)))*smoothstep(0.,.12,reveal)*(1.-smoothstep(.80,1.,reveal));
	vec3 color=mix(snow,packed,court);
	color=mix(color,vec3(.98,.69,.34),amber*court*.67);
	ALBEDO=OUTPUT_IS_SRGB?color:pow(color,vec3(2.2));
	EMISSION=mix(vec3(.052,.054,.058),vec3(.040,.026,.020),court);
	ROUGHNESS=.94;
	SPECULAR=.15;
}
