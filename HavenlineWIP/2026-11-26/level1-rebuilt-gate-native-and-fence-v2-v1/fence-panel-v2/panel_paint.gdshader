shader_type spatial;
render_mode diffuse_burley, specular_schlick_ggx;
// Kept separate from the mesh/MTL A/B. Per local surface only, never global light.
uniform vec4 coat : source_color = vec4(0.79,0.43,0.225,1.0);
uniform int surface_role = 0; // wood=0, draped snow=1, hemp=2
uniform float local_fill = 0.0; // explicit opt-in supplemental trial only
varying vec3 local_vertex;

void vertex() { local_vertex = VERTEX; }
void fragment() {
	float warp = sin(local_vertex.y * 5.1 + sin(local_vertex.x * 17.0) * 0.55);
	float grain = sin(local_vertex.x * 106.0 + warp * 1.33 + local_vertex.z * 19.0);
	float grain_long = sin(local_vertex.x * 42.0 + local_vertex.y * 4.0 + 0.55 * warp);
	float tonal = 1.0;
	if (surface_role == 0) {
		tonal += 0.057 * grain_long + 0.028 * grain;
	}
	if (surface_role == 1) {
		tonal -= (1.0 - smoothstep(0.92,1.42,local_vertex.y)) * 0.10;
	}
	if (surface_role == 2) {
		tonal += 0.026 * sin(158.0 * local_vertex.x + 83.0 * local_vertex.y);
	}
	vec3 pigment = clamp(coat.rgb * tonal, vec3(0.0), vec3(1.0));
	ALBEDO = pigment;
	ROUGHNESS = surface_role == 1 ? 0.79 : 0.87;
	SPECULAR = 0.26;
	METALLIC = 0.0;
	EMISSION = pigment * clamp(local_fill,0.0,0.085);
}
