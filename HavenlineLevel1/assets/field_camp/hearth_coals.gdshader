shader_type spatial;
render_mode unshaded, cull_disabled, depth_draw_opaque, shadows_disabled;
vec2 seed(vec2 cell) {
    return fract(sin(vec2(dot(cell,vec2(127.1,311.7)),dot(cell,vec2(269.5,183.3))))*4375.5453);
}
void fragment() {
    vec2 uv = UV * 2.0 - 1.0;
    if (length(uv) > 0.995) { discard; }
    vec2 p = uv * 3.3 + vec2(0.19*sin(uv.y*8.7+uv.x*2.1),0.12*sin(uv.x*10.1));
    vec2 cell = floor(p);
    float nearest = 4.0, second = 4.0;
    float heat_seed = 0.0;
    for (int y=-1; y<=1; y++) {
        for (int x=-1; x<=1; x++) {
            vec2 c = cell + vec2(float(x),float(y));
            vec2 r = seed(c);
            vec2 delta = c + 0.22 + 0.56*r - p;
            float d = dot(delta,delta);
            if (d < nearest) {
                second = nearest; nearest = d; heat_seed = r.y;
            } else {
                second = min(second, d);
            }
        }
    }
    float pulse = 0.5 + 0.5*sin(TIME*2.4 + heat_seed*6.0 + p.y*0.3);
    float fissure = 1.0 - smoothstep(0.008,0.37,second-nearest);
    float core = smoothstep(0.24,0.9,heat_seed) * (0.62+0.38*pulse);
    vec3 body = mix(vec3(0.65,0.135,0.025), vec3(1.0,0.52,0.08), core);
    vec3 color = mix(body, vec3(1.0,0.77,0.20),fissure*(0.73+0.27*pulse));
    // The high draft concentrates the brightest heat in the centre of the vent.
    // Coarse charcoal at the rim remains legible at pinch zoom.
    float draft = (1.0-smoothstep(0.40,1.04,length(uv))) * (0.88+0.06*pulse);
    color = mix(color, mix(vec3(1.0,0.69,0.12),vec3(1.0,0.86,0.34),0.45*core+0.55*fissure),draft);
    ALBEDO = OUTPUT_IS_SRGB ? color : pow(color,vec3(2.2));
}
