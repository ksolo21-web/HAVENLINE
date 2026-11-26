shader_type spatial;
render_mode cull_disabled,diffuse_burley,specular_schlick_ggx;
varying vec3 bank_point;
void vertex(){bank_point=(MODEL_MATRIX*vec4(VERTEX,1.)).xyz;}
void fragment(){
 float grain=sin(bank_point.z*5.31+sin(bank_point.x*3.84))*sin(bank_point.x*8.31-bank_point.z*3.7);
 vec3 pigment=COLOR.rgb*(1.+grain*.018);
 ALBEDO=OUTPUT_IS_SRGB?pigment:pow(pigment,vec3(2.2));
 ROUGHNESS=mix(.58,.94,COLOR.r); SPECULAR=.16;
}
