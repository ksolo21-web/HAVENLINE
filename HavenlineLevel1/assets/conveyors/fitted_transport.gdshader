shader_type spatial;
render_mode cull_disabled, diffuse_burley, specular_schlick_ggx;
uniform sampler2D pigment_map : source_color, filter_linear_mipmap_anisotropic,repeat_enable;
uniform vec4 tint : source_color=vec4(1.);
uniform float roughness:hint_range(0.,1.)=1.;
uniform float metalness:hint_range(0.,1.)=0.;
uniform bool foot_piece=false;
uniform bool end_supports=false;
uniform vec2 support_center=vec2(0.);
uniform bool rail_shell=false;
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
// module's exit turns toward +X. The original UV atlas stays on the fitted
// module. Keep every enlargement on the underside and inside its footprint.
vec3 fitted(vec3 p,vec4 equipment) {
	float begin=equipment.r*4.;
	float end=equipment.g*4.;
	float run=max(.01,equipment.b*4.);
	float width_scale=deck_width/source_width;
	if(foot_piece && curved) {
		p.xz=support_center+(p.xz-support_center)*1.25;
	} else if(foot_piece && end_supports) {
		vec2 center=vec2(sign(p.x)*source_width*.36,source_run*(p.z<source_run*.5?.145:.855));
		p.xz=center+(p.xz-center)*vec2(1.20,1.38);
	}
	float forward_progress;
	float lateral;
	vec2 projected;
	if(curved){
		vec2 radius=vec2(source_radius-p.x,p.z);
		float angle=atan(radius.y,radius.x);
		forward_progress=clamp(angle/1.5707963,0.,1.);
		float offset=(length(radius)-source_radius)*width_scale;
		projected=vec2(run,0.)+vec2(-cos(angle),sin(angle))*(run+offset);
		lateral=abs(offset);
	} else {
		forward_progress=clamp(p.z/source_run,0.,1.);
		projected=vec2(p.x*width_scale,p.z*run/source_run);
		lateral=abs(projected.x);
	}
	float original_surface=source_rise*clamp((forward_progress-transition.x)/(transition.y-transition.x),0.,1.);
	float surface=mix(begin,end,forward_progress);
	float depth=(p.y-original_surface)*width_scale;
	if(rail_shell) {
		float outside=smoothstep(.171,.204,lateral);
		float guard=smoothstep(-.24,-.165,depth);
		depth-=min(max(-depth,0.)*.39,.049)*outside*guard;
	}
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
	cut_foot=INSTANCE_CUSTOM.a>.5 && foot_piece?-1.:1.;
	VERTEX=p;
}
void fragment(){
	if(cut_foot<0.)discard;
	vec3 pigment=texture(pigment_map,UV).rgb*tint.rgb;
	float orange=smoothstep(.055,.34,pigment.r-pigment.g)
		*smoothstep(.018,.17,pigment.g-pigment.b);
	float cobalt=smoothstep(.012,.16,pigment.b-max(pigment.r,pigment.g)*1.10);
	float reflected=dot(pigment,vec3(.2126,.7152,.0722));
	vec3 enamel=vec3(.99,.36,.016)*mix(.68,1.05,smoothstep(.013,.50,reflected));
	vec3 paint=mix(pigment,enamel,.73);
	vec3 shades=mix(pigment,paint,orange);
	shades=mix(shades,min(vec3(1.),pigment*vec3(1.16,1.35,1.50)),cobalt);
	float feet=foot_piece?1.:0.;
	vec3 zinc=vec3(.48,.51,.55)*mix(.56,1.18,smoothstep(.018,.45,reflected));
	ALBEDO=mix(shades,mix(pigment,zinc,.75),feet);
	// Reflectance keeps readably painted hardware in camp shadow without
	// flattening the black deck, fasteners or colored details.
	EMISSION=paint*orange*.11+zinc*feet*.16;
	ROUGHNESS=mix(roughness,.47,max(orange,feet*.65));
	METALLIC=mix(mix(metalness,.06,orange),.18,feet);
}
