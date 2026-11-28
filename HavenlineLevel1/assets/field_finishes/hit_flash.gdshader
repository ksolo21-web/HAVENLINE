shader_type spatial;
render_mode blend_add, unshaded, depth_draw_never;

uniform vec4 pigment : source_color = vec4(1.0);

void fragment() {
	ALBEDO = pigment.rgb;
	ALPHA = pigment.a;
}
