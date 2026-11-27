shader_type spatial;
render_mode unshaded, cull_disabled, depth_draw_never, shadows_disabled;

uniform float phase = 0.0;

// Keep the fire vertical in the mouth when viewed down into the camp.
void vertex() {
    vec3 up = vec3(0.0, 1.0, 0.0);
    vec3 right = normalize(cross(up, INV_VIEW_MATRIX[3].xyz - MODEL_MATRIX[3].xyz));
    vec3 depth = cross(right, up);
    MODELVIEW_MATRIX = VIEW_MATRIX * mat4(vec4(right * length(MODEL_MATRIX[0].xyz), 0.0),
        vec4(up * length(MODEL_MATRIX[1].xyz), 0.0), vec4(depth, 0.0), MODEL_MATRIX[3]);
}

float tongue(vec2 p, float bend, float height, float width, float t) {
    float v = p.y / height;
    float x = p.x - bend * v * v - sin(t + v * 4.5) * v * 0.09;
    float radius = width * pow(clamp(1.0 - v, 0.0, 1.0), 0.73);
    return (radius - abs(x)) / width - max(0.0, v - 1.0) * 14.0;
}
void fragment() {
    vec2 p = vec2(UV.x * 2.0 - 1.0, 1.0 - UV.y);
    float t = TIME * 4.8 + phase;
    float outer = tongue(p, 0.14 * sin(t * 0.79), 0.79 + 0.13 * sin(t), 0.53, t);
    outer = max(outer, tongue(p - vec2(0.42, -0.01), -0.15, 0.48 + 0.14 * sin(t * 1.21), 0.39, t + 2.2));
    outer = max(outer, tongue(p + vec2(0.39, 0.0), 0.21, 0.57 + 0.15 * sin(t * 0.86 + 1.7), 0.38, t + 3.1));
    float hot = smoothstep(0.17, 0.76, outer) * (1.0 - smoothstep(0.18, 0.82, p.y));
    vec3 color = mix(vec3(1.0, 0.26, 0.025), vec3(1.0, 0.71, 0.11), smoothstep(-0.08, 0.53, outer));
    color = mix(color, vec3(1.0, 0.94, 0.54), hot);
    ALBEDO = OUTPUT_IS_SRGB ? color : pow(color, vec3(2.2));
    ALPHA = smoothstep(-0.085, 0.12, outer) * smoothstep(0.0, 0.07, p.y);
}
