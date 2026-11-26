extends RefCounted
const SHADER = preload("res://previews/clearance_gate/owner_33035.gdshader")
const LABELS := {"wood_even":0,"wood_amber":0,"wood_soft":0,"frame":1,"snow":2,"rope":3,"rope_soft":3,"iron":4,"iron_soft":4}

# Build a complete strict set before writing any instance state.
static func plan(mesh: Mesh, rows: Array) -> Array[ShaderMaterial]:
	var result: Array[ShaderMaterial] = []
	if not mesh or mesh.get_surface_count()!=rows.size():
		return []
	for i in range(rows.size()):
		var label: String = rows[i].label
		var base := mesh.surface_get_material(i) as StandardMaterial3D
		if not LABELS.has(label) or not base or rows[i].index!=i:
			return []
		var material := ShaderMaterial.new()
		material.shader=SHADER
		material.set_shader_parameter("family",LABELS[label])
		material.set_shader_parameter("base_tint",base.albedo_color)
		material.set_shader_parameter("stock_roughness",base.roughness)
		var group: String = rows[i].source_group
		if group in ["front_handle_rosette","front_handle_owned_bar","front_receiver_keeper"]:
			if LABELS[label]!=4:
				return []
			material.set_shader_parameter("front_latch_role",2 if group=="front_handle_owned_bar" else 1)
		result.append(material)
	return result

static func apply_to(node: MeshInstance3D, materials: Array[ShaderMaterial]) -> void:
	for i in range(materials.size()):
		node.set_surface_override_material(i,materials[i])
