shader_type spatial;
render_mode cull_disabled, diffuse_burley, specular_schlick_ggx;
uniform sampler2D pigment_map : source_color, filter_linear_mipmap_anisotropic,repeat_enable;
uniform vec4 tint : source_color=vec4(1.);
uniform float roughness:hint_range(0.,1.)=1.;
uniform float metalness:hint_range(0.,1.)=0.;
uniform bool foot_piece=false;
uniform vec2 transition=vec2(0.,1.);
uniform float source_width=.48;
uniform float source_run=1.;
uniform float source_rise=0.;
uniform float source_foot=-.38;
uniform bool curved=false;
uniform bool left_handed=false;
uniform float source_radius=.45;
uniform float deck_width=.484;
varying float cut_foot;

// Local frame: the input point is at (0,0,0), forward is +Z. A curved
// module's exit turns toward +X. The Meshy UVs and photographed paint are
// unmodified. Adjust only the radius, sleeve/roll spacing and underside.
vec3 fitted(vec3 p,vec4 equipment) {
	float begin=equipment.r*4.;
	float end=equipment.g*4.;
	float run=max(.01,equipment.b*4.);
	float width_scale=deck_width/source_width;
	float forward_progress;
	vec2 projected;
	if(curved){
		vec2 radius=vec2(source_radius-p.x,p.z);
		float angle=atan(radius.y,radius.x);
		forward_progress=clamp(angle/1.5707963,0.,1.);
		float offset=(length(radius)-source_radius)*width_scale;
		projected=vec2(run,0.)+vec2(-cos(angle),sin(angle))*(run+offset);
	} else {
		forward_progress=clamp(p.z/source_run,0.,1.);
		projected=vec2(p.x*width_scale,p.z*run/source_run);
	}
	float original_surface=source_rise*clamp((forward_progress-transition.x)/(transition.y-transition.x),0.,1.);
	float surface=mix(begin,end,forward_progress);
	float depth=(p.y-original_surface)*width_scale;
	float original_floor=(source_foot-original_surface)*width_scale;
	float sleeve=foot_piece?clamp((-depth-.135)/max(.035,-original_floor-.135),0.,1.):0.;
	float floor_height=equipment.a>.5?max(.025,surface-.19):.015;
	float y=surface+depth+(floor_height-(surface+original_floor))*sleeve;
	return vec3(projected.x*(left_handed?-1.:1.),y,projected.y);
}
void vertex() {
	vec3 original=VERTEX;
	vec3 p=fitted(original,INSTANCE_CUSTOM);
	// Evaluate the fitted source tangent frame, retaining the soft cast
	// edges of the original textured geometry through the height adapter.
	const float e=.0008;
	mat3 j=mat3((fitted(original+vec3(e,0.,0.),INSTANCE_CUSTOM)-p)/e,(fitted(original+vec3(0.,e,0.),INSTANCE_CUSTOM)-p)/e,(fitted(original+vec3(0.,0.,e),INSTANCE_CUSTOM)-p)/e);
	if(abs(determinant(j))>.0002){NORMAL=normalize(transpose(inverse(j))*NORMAL);}
	float progress=curved?0.:clamp(original.z/source_run,0.,1.);
	cut_foot=INSTANCE_CUSTOM.a>.5 && foot_piece?-1.:1.;
	VERTEX=p;
}
void fragment(){
	if(cut_foot<0.)discard;
	vec3 pigment=texture(pigment_map,UV).rgb*tint.rgb;
	float enamel=smoothstep(.012,.16,pigment.b-max(pigment.r,pigment.g)*1.10);
	ALBEDO=mix(pigment,min(vec3(1.),pigment*vec3(1.10,1.35,1.50)),enamel);
	ROUGHNESS=roughness;
	METALLIC=metalness;
}
