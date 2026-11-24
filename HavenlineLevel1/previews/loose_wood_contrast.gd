extends RefCounted
## Local opt-in imported paint repair; not an asset, physics or lighting change.
const REVIEW_FLAG := "--l1-review-wood-contrast"
const EXPECTED := {"Bark | painted ridges":3, "End grain | amber":3, "Rope | twisted flax":3}
const REPAIRED := ["Bark | painted ridges", "Rope | twisted flax"]

static func apply(piece: Node3D) -> bool:
	if not is_instance_valid(piece) or not piece.is_inside_tree():
		return false
	var mesh_children := piece.find_children("*", "MeshInstance3D", true, false)
	if mesh_children.size() != 6:
		return false
	var tallies := {}
	var pending: Array[Dictionary] = []
	for item in mesh_children:
		var instance := item as MeshInstance3D
		if not instance.mesh is ArrayMesh or instance.material_override != null:
			return false
		for i: int in range(instance.mesh.get_surface_count()):
			var material := instance.mesh.surface_get_material(i) as StandardMaterial3D
			if material == null or instance.get_surface_override_material(i) != null:
				return false
			var role: String = material.resource_name
			if not EXPECTED.has(role) or (instance.mesh.surface_get_format(i) & Mesh.ARRAY_FORMAT_COLOR) == 0:
				return false
			tallies[role] = int(tallies.get(role, 0)) + 1
			if role in REPAIRED and not material.vertex_color_use_as_albedo:
				var local := material.duplicate() as StandardMaterial3D
				if local == null:
					return false
				local.vertex_color_use_as_albedo = true
				pending.append({"instance":instance, "index":i, "material":local})
			elif role not in REPAIRED and not material.vertex_color_use_as_albedo:
				# The independently imported end-grain comparator must stay intact.
				return false
	if tallies != EXPECTED:
		return false
	for change in pending:
		change.instance.set_surface_override_material(change.index, change.material)
	return true
