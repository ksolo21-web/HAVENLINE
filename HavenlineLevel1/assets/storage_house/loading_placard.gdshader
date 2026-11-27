shader_type spatial;
render_mode cull_disabled;
// The generated raised placard is a separate island above the loading crown.
uniform sampler2D original_paint : source_color, filter_linear_mipmap, repeat_enable;
uniform vec4 enamel : source_color = vec4(0.97, 0.86, 0.65, 1.0);
varying float height_on_frame;
void vertex() {
	height_on_frame = VERTEX.y;
}
void fragment() {
	if (height_on_frame > 0.525) {
		ALBEDO = enamel.rgb * 0.42;
		EMISSION = enamel.rgb * 0.71;
		METALLIC = 0.0;
		ROUGHNESS = 0.83;
	} else {
		vec3 paint = texture(original_paint, UV).rgb;
		ALBEDO = paint;
		EMISSION = paint * 0.21;
		METALLIC = 0.08;
		ROUGHNESS = 0.78;
	}
}
