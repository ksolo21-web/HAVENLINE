shader_type spatial;
render_mode unshaded, cull_disabled;

uniform vec4 pigment : source_color = vec4(1.0);

void fragment() {
	ALBEDO = pigment.rgb;
}
