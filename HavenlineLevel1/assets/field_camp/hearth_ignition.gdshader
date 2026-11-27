shader_type spatial;
render_mode unshaded, blend_add, shadows_disabled, depth_draw_never;

uniform float heat : hint_range(0.0, 1.0) = 0.0;
uniform vec4 ember : source_color = vec4(1.0, 0.64, 0.09, 1.0);

void fragment() {
	float rim = pow(1.0 - clamp(dot(normalize(NORMAL), normalize(VIEW)), 0.0, 1.0), 1.5);
	ALBEDO = ember.rgb * (0.70 + 0.30 * rim);
	ALPHA = heat;
}
