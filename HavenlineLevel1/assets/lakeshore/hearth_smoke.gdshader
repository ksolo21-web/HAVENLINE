shader_type spatial;
render_mode unshaded,cull_disabled,depth_draw_never;
void vertex(){
 vec3 s=vec3(length(MODEL_MATRIX[0].xyz),length(MODEL_MATRIX[1].xyz),length(MODEL_MATRIX[2].xyz));
 MODELVIEW_MATRIX=VIEW_MATRIX*mat4(INV_VIEW_MATRIX[0]*s.x,INV_VIEW_MATRIX[1]*s.y,INV_VIEW_MATRIX[2]*s.z,MODEL_MATRIX[3]);
}
void fragment(){
 vec2 p=UV*2.-1.;
 float edge=1.-smoothstep(.18,1.,length(p)+.11*sin(p.x*8.+p.y*3.)+.10*sin(p.y*9.-p.x*2.));
 ALBEDO=mix(vec3(.38,.44,.49),vec3(.76,.80,.82),UV.y);
 ALPHA=edge*.32*COLOR.a;
}
