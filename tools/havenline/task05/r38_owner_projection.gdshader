shader_type spatial;
render_mode unshaded, cull_disabled, depth_draw_opaque;
// The source renders contain baked illumination. This is an isolated
// view-dependent photo-projection TEST, not a final physically-lit material.
uniform sampler2D front_tex : source_color, filter_linear_mipmap;
uniform sampler2D right_tex : source_color, filter_linear_mipmap;
uniform sampler2D rear_tex : source_color, filter_linear_mipmap;
uniform vec3 front_direction=vec3(0.482963,0.258819,0.836516);
uniform vec3 right_direction=vec3(0.992546,0.121869,0.0);
uniform vec3 rear_direction=vec3(0.0,0.121869,-0.992546);
uniform vec3 front_right=vec3(0.866025,0.0,-0.5);
uniform vec3 front_up=vec3(-0.129410,0.965926,-0.224144);
uniform vec3 right_right=vec3(0.,0.,-1.);
uniform vec3 right_up=vec3(-0.121869,0.992546,0.);
uniform vec3 rear_right=vec3(-1.,0.,0.);
uniform vec3 rear_up=vec3(0.,0.992546,0.121869);
uniform vec2 front_center=vec2(773.5,764.5);
uniform vec2 right_center=vec2(803.,632.);
uniform vec2 rear_center=vec2(770.5,467.);
uniform vec2 front_scale=vec2(353.9024,386.5574);
uniform vec2 right_scale=vec2(244.6667,309.5082);
uniform vec2 rear_scale=vec2(323.1707,216.3934);
uniform vec2 front_dims=vec2(1536.,1536.);
uniform vec2 right_dims=vec2(1536.,1147.);
uniform vec2 rear_dims=vec2(1536.,903.);
varying vec3 world_vertex;
void vertex(){
    world_vertex=(MODEL_MATRIX*vec4(VERTEX,1.)).xyz;
}
vec2 photo_uv(vec3 pos,vec3 r,vec3 up,vec2 ctr,vec2 scl,vec2 dims){
    vec3 v=pos-vec3(0.,1.55,0.);
    vec2 px=vec2(ctr.x+dot(v,r)*scl.x,ctr.y-dot(v,up)*scl.y);
    // Godot shader sampler uses top-origin UV; glTF/Trimesh UV convention differs.
    return clamp(vec2(px.x/(dims.x-1.),px.y/(dims.y-1.)),vec2(0.),vec2(1.));
}
void fragment(){
    vec3 toward_cam=normalize(CAMERA_POSITION_WORLD-world_vertex);
    float f=pow(max(dot(toward_cam,normalize(front_direction)),0.001),14.);
    float r=pow(max(dot(toward_cam,normalize(right_direction)),0.001),14.);
    float b=pow(max(dot(toward_cam,normalize(rear_direction)),0.001),14.);
    vec3 front=texture(front_tex,photo_uv(world_vertex,front_right,front_up,front_center,front_scale,front_dims)).rgb;
    vec3 right=texture(right_tex,photo_uv(world_vertex,right_right,right_up,right_center,right_scale,right_dims)).rgb;
    vec3 rear=texture(rear_tex,photo_uv(world_vertex,rear_right,rear_up,rear_center,rear_scale,rear_dims)).rgb;
    float total=f+r+b;
    // Never create a misleading black hole at the unobserved left side.
    // This fallback is expressly NOT validated source geometry.
    if (total < 0.00000001) {
        ALBEDO=front;
    } else {
        ALBEDO=(front*f+right*r+rear*b)/total;
    }
    ROUGHNESS=1.;
}
