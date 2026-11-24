shader_type spatial;

uniform vec4 bounds;
varying vec2 terrain_xz;

void vertex() {
	terrain_xz = VERTEX.xz;
}

void fragment() {
	if (terrain_xz.x < bounds.x || terrain_xz.y < bounds.y || terrain_xz.x > bounds.z || terrain_xz.y > bounds.w) {
		discard;
	}
	ALBEDO = vec3(0.51, 0.57, 0.60);
	ROUGHNESS = 0.94;
}
