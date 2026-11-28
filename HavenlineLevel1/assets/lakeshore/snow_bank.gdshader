shader_type spatial;
render_mode cull_disabled,diffuse_burley,specular_schlick_ggx;
uniform float river_snow_fill : hint_range(0.0,1.0)=0.0;
uniform vec2 river_crossing = vec2(0.0);
varying vec3 bank_point;
void vertex(){bank_point=(MODEL_MATRIX*vec4(VERTEX,1.)).xyz;}
void fragment(){
 float grain=sin(bank_point.z*5.31+sin(bank_point.x*3.84))*sin(bank_point.x*8.31-bank_point.z*3.7);
 vec3 pigment=COLOR.rgb*(1.+grain*.018);
 float from_deck=abs(bank_point.x-river_crossing.x)-river_crossing.y;
 float deck_snow=(1.-smoothstep(.10,1.35,from_deck))*smoothstep(-.11,.0,bank_point.y);
 float dry_snow=smoothstep(-.13,.085,bank_point.y)*.90;
 float snow_join=max(deck_snow,dry_snow)*river_snow_fill;
 pigment=mix(pigment,vec3(1.002,1.060,1.092),snow_join);
 ALBEDO=OUTPUT_IS_SRGB?pigment:pow(pigment,vec3(2.2));
 EMISSION=mix(vec3(.034,.045,.051)*smoothstep(.56,.89,COLOR.r)*river_snow_fill,vec3(.052,.054,.058),snow_join);
 NORMAL=normalize(mix(NORMAL,normalize((VIEW_MATRIX*vec4(0.0,1.0,0.0,0.0)).xyz),snow_join));
 ROUGHNESS=mix(.58,.94,COLOR.r); SPECULAR=.16;
}
