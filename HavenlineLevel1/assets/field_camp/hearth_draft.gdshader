shader_type spatial;
render_mode unshaded, cull_disabled, depth_draw_never, shadows_disabled;
void vertex() {
    vec3 size = vec3(length(MODEL_MATRIX[0].xyz),length(MODEL_MATRIX[1].xyz),1.0);
    MODELVIEW_MATRIX = VIEW_MATRIX*mat4(INV_VIEW_MATRIX[0]*size.x,INV_VIEW_MATRIX[1]*size.y,INV_VIEW_MATRIX[2],MODEL_MATRIX[3]);
}
float noise2(vec2 p) {
    vec2 cell = floor(p), f = fract(p);
    f = f*f*(3.0-2.0*f);
    vec4 n = sin(dot(cell,vec2(127.1,311.7)) + vec4(0.0,127.1,311.7,438.8))*4375.5453;
    n = fract(n);
    return mix(mix(n.x,n.y,f.x),mix(n.z,n.w,f.x),f.y);
}
void fragment() {
    float h = 1.0-UV.y;
    float t = TIME*0.72;
    float x = UV.x-0.43-h*0.20 - h*(0.09*sin(8.0*h-t*2.2)+0.04*sin(h*18.0-t*3.0));
    float spread = 0.095 + h*0.22;
    float vapor = noise2(vec2(x*15.0,h*6.0-t*2.2))*0.65 + noise2(vec2(x*24.0,h*12.0-t*3.5))*0.35;
    float cross_section = abs(x)/(spread*(0.45+vapor));
    float density = exp(-3.0*cross_section*cross_section) * smoothstep(0.0,0.12,h) * (1.0-smoothstep(0.38,0.98,h));
    vec3 color = mix(vec3(0.56,0.52,0.49), vec3(0.92,0.92,0.91), smoothstep(0.1,0.85,h)+0.1*vapor);
    ALBEDO = OUTPUT_IS_SRGB ? color : pow(color,vec3(2.2));
    ALPHA = density*(0.35+0.58*vapor);
}
