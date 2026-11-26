extends "res://previews/r17_fence/r17_fence_view.gd"
## Exact technical gates, physical wall, pads, camera and shader remain inherited.
const DETAIL: Mesh = preload("res://previews/reference_panel/assets/fence_reference_detail.obj")
const DETAIL_NODE := &"SouthwestOuterReferencePanel"
const CUT_INDEX := 0
var reference_panel_mounted := false
var reference_stock_transform := Transform3D.IDENTITY

func setup_camp() -> void:
	super.setup_camp()
	var reason := _replace_panel()
	if not reason.is_empty():
		push_warning("REFERENCE_PANEL_FALLBACK: " + reason)
	else:
		reference_panel_mounted = true
		print("REFERENCE_PANEL_MOUNT one authored panel replaces one stock transform")

func _replace_panel() -> String:
	if scene_file_path != "res://previews/reference_panel/reference_panel.tscn":
		return "unexpected-scene"
	var shell := camp_built.get_node_or_null("R17FenceViewOnly") as Node3D
	if not shell or shell.get_child_count() != 2 or not shell.transform.is_equal_approx(Transform3D.IDENTITY):
		return "missing-existing-r17-shell"
	var batch := shell.get_node_or_null("R17WallPanels") as MultiMeshInstance3D
	if not batch or not batch.multimesh or batch.multimesh.instance_count != 12:
		return "unexpected-inherited-batch"
	var stock := batch.multimesh
	if DETAIL.get_surface_count() != 3 or not DETAIL.get_aabb().is_equal_approx(stock.mesh.get_aabb()):
		return "detail-import-or-envelope"
	var first: Transform3D = stock.get_instance_transform(CUT_INDEX)
	var row: Array = layout.walls_xz[0]
	if not Vector4(float(row[0]),float(row[1]),float(row[2]),float(row[3])).is_equal_approx(Vector4(-3.15,4,3.9,.30)) or not first.basis.x.normalized().is_equal_approx(Vector3.RIGHT):
		return "not-the-pinned-southwest-run"
	var south_x := float(camp_colliders[0].position.x)
	if not is_equal_approx(first.origin.x,south_x - .972) or not is_equal_approx(first.origin.z,camp_colliders[0].position.z + .00975):
		return "not-the-pinned-outside-west-half"
	var detail := DETAIL.duplicate() as ArrayMesh
	if not detail:
		return "detail-not-a-triangle-array-mesh"
	var counts := {"timber":1800,"snow":1440,"rope":4800}
	var proved: Array[String] = []
	for i in range(detail.get_surface_count()):
		var mat := detail.surface_get_material(i) as StandardMaterial3D
		if not mat or mat.albedo_texture != null or detail.surface_get_primitive_type(i) != Mesh.PRIMITIVE_TRIANGLES:
			return "unexpected-imported-surface-type"
		var key := mat.resource_name.to_lower()
		if not counts.has(key) or key in proved:
			return "missing-or-duplicate-material-label"
		var ni := detail.surface_get_array_index_len(i)
		var nv := detail.surface_get_array_len(i)
		if int((ni if ni > 0 else nv) / 3.0) != counts[key]:
			return "material-triangle-budget"
		proved.append(key)
		if key == "rope":
			# Exact portable author palette; no changes to weather, light,
			# stock shader or any other material. Native artistic review pending.
			if not mat.albedo_color.is_equal_approx(Color(.63,.455,.284,1)):
				return "draft-rope-palette"
		else:
			if not _r17_materials.has(key):
				return "missing-exact-protected-timber-or-snow-material"
			detail.surface_set_material(i,_r17_materials[key])
	var remainder := MultiMesh.new()
	remainder.transform_format = MultiMesh.TRANSFORM_3D
	remainder.mesh = stock.mesh
	remainder.instance_count = 11
	for i in range(11):
		remainder.set_instance_transform(i,stock.get_instance_transform(i+1))
	var view := MeshInstance3D.new()
	view.name = DETAIL_NODE
	view.mesh = detail
	view.transform = first
	# All guards above. No old geometry left behind at the replaced transform.
	batch.multimesh = remainder
	shell.add_child(view)
	reference_stock_transform = first
	return ""
