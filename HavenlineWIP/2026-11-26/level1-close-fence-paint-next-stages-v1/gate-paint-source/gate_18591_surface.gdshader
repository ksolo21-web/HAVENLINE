shader_type spatial;
render_mode cull_back, diffuse_burley, specular_schlick_ggx;

uniform vec4 wood_honey : source_color = vec4(0.68, 0.34, 0.19, 1.0);
uniform vec4 wood_low : source_color = vec4(0.46, 0.21, 0.11, 1.0);
uniform vec4 frame_honey : source_color = vec4(0.78, 0.50, 0.30, 1.0);
uniform vec4 frame_low : source_color = vec4(0.63, 0.35, 0.21, 1.0);
uniform vec4 rope_oat : source_color = vec4(0.74, 0.59, 0.38, 1.0);
uniform vec4 metal_edge : source_color = vec4(0.54, 0.60, 0.69, 1.0);
uniform vec4 snow_shade : source_color = vec4(0.52, 0.68, 0.85, 1.0);
uniform int family = 0; // 0 board, 1 frame, 2 snow, 3 iron, 4 rope
uniform float tone = 0.5;

varying vec3 leaf_p;
varying vec3 leaf_n;

void vertex() {
    leaf_p = VERTEX;
    leaf_n = NORMAL;
}

void fragment() {
    vec3 p = vec3(abs(leaf_p.x), leaf_p.yz);
    vec3 n = normalize(leaf_n);
    float sky = smoothstep(-0.25, 0.85, n.y);
    float floor_fill = 0.38;
    vec3 pigment = wood_honey.rgb;
    ROUGHNESS = 0.82;
    METALLIC = 0.0;
    SPECULAR = 0.21;
    if (family <= 1) {
        // Millimeter details subpixel at gameplay distance are omitted intentionally.
        // The 45–80mm warm grain reads as broad hand-painted longitudinal strokes.
        float phase = 89.0 * p.x + 0.75 * sin(p.y * 8.0 + p.x * 14.0);
        float grain = 0.5 + 0.5 * sin(phase + 0.24 * sin(p.y * 16.0));
        float longitudinal = 0.5 + 0.5 * sin(p.x * 49.0 + sin(p.y * 5.0));
        float warm_face = clamp(0.28 + 0.34 * tone + 0.30 * grain + 0.14 * longitudinal, 0.0, 1.0);
        pigment = mix(wood_low.rgb, wood_honey.rgb, warm_face);
        if (family == 1) {
            float bevel_catch = max(sky, 0.57 * (1.0 - abs(n.z)));
            pigment = mix(frame_low.rgb, frame_honey.rgb, 0.23 + 0.43 * warm_face + 0.34 * bevel_catch);
            pigment *= 1.13 + 0.19 * bevel_catch;
            floor_fill = 0.42;
        } else {
            pigment *= 0.92 + 0.12 * sky;
        }
    } else if (family == 2) {
        // A soft underside on the existing snow silhouette, not an added lip or mesh.
        float drape = smoothstep(1.22, 1.335, p.y);
        float soft_roll = 0.5 + 0.5 * sin(23.0 * p.x + 0.5 * sin(46.0 * p.x));
        float sunward = clamp(0.13 + 0.49 * sky + 0.32 * drape + 0.06 * soft_roll, 0.0, 1.0);
        pigment = mix(snow_shade.rgb, vec3(0.91, 0.95, 0.99), sunward);
        floor_fill = 0.29;
        ROUGHNESS = 0.9;
    } else if (family == 3) {
        // Cool lit fasteners remain distinct from warm boards in the dark approach.
        float catch_edge = clamp(0.25 + 0.56 * sky + 0.30 * (1.0 - abs(n.z)), 0.0, 1.0);
        pigment = mix(vec3(0.075, 0.101, 0.151), metal_edge.rgb, catch_edge);
        floor_fill = 0.50;
        ROUGHNESS = 0.63;
        METALLIC = 0.18;
    } else {
        pigment = mix(frame_low.rgb, rope_oat.rgb, clamp(0.24 + 0.49 * tone + 0.25 * sky, 0.0, 1.0));
        floor_fill = 0.35;
        ROUGHNESS = 0.93;
    }
    // Non-HDR, object-local diffuse readability floor; ordinary sun still lights this surface.
    ALBEDO = clamp(pigment, vec3(0.0), vec3(0.95));
    EMISSION = min(ALBEDO * floor_fill, vec3(0.24));
}
