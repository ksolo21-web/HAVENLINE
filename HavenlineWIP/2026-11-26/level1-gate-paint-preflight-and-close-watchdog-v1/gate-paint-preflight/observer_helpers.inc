func _effective_gate_paint(art: MeshInstance3D, source_rows: Array[Dictionary]) -> Array[Dictionary]:
	var rows: Array[Dictionary] = []
	if art.material_override != null or art.material_overlay != null or source_rows.size() != 39:
		return rows
	if art.get_surface_override_material_count() != 39:
		return rows
	for i in range(39):
		var label := String(source_rows[i].material)
		if not EXPECTED_PAINT.has(label):
			return []
		var instance_mat := art.get_surface_override_material(i) as ShaderMaterial
		if instance_mat == null or art.get_active_material(i) != instance_mat or instance_mat.shader != ADMITTED_PAINT:
			return []
		var expected: Array = EXPECTED_PAINT[label]
		var family: Variant = instance_mat.get_shader_parameter("family")
		var tone: Variant = instance_mat.get_shader_parameter("tone")
		if typeof(family) != TYPE_INT or typeof(tone) != TYPE_FLOAT:
			return []
		if family != int(expected[0]) or not is_equal_approx(float(tone),float(expected[1])):
			return []
		if instance_mat.resource_name != "gate_18591_"+label:
			return []
		rows.append({"surface":i,"label":label,"family":family,"tone":tone,"shader":instance_mat.shader.resource_path,
			"effective":true,"whole_instance_override_or_overlay":false})
	return rows

func _paint_census(evidence: Dictionary) -> Dictionary:
	var out := {}
	for gate in evidence.gates:
		var sides := {}
		for row in evidence.gates[gate].mounts:
			sides[String(row.owner_pivot)] = row.paint_overrides
		out[gate] = sides
	return out
