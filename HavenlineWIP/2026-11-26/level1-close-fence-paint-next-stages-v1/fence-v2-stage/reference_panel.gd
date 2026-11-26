extends "res://previews/r17_fence/r17_fence_view.gd"
## Exact technical gates, physical wall, pads, camera and shader remain inherited.
const DETAIL: Mesh = preload("res://previews/reference_panel/assets/Fence18595V2.obj")
const DETAIL_NODE := &"SouthwestOuterReferencePanel"
const CUT_INDEX := 0
const MATERIAL_ORDER := ["amber_timber","draped_snow","warm_hemp","cream_hemp"]
const MATERIAL_TRIANGLES := [1800,1920,2560,2560]
const EXPECTED_BASE := [Color(.79,.43,.225,1),Color(.88,.935,.995,1),Color(.77,.55,.32,1),Color(.91,.72,.45,1)]
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
	if DETAIL.get_surface_count() != MATERIAL_ORDER.size() or not DETAIL.get_aabb().is_equal_approx(stock.mesh.get_aabb()):
		return "detail-import-or-envelope"
	var first: Transform3D = stock.get_instance_transform(CUT_INDEX)
	var row: Array = layout.walls_xz[0]
	if not Vector4(float(row[0]),float(row[1]),float(row[2]),float(row[3])).is_equal_approx(Vector4(-3.15,4,3.9,.30)) or not first.basis.x.normalized().is_equal_approx(Vector3.RIGHT):
		return "not-the-pinned-southwest-run"
	var south_x := float(camp_colliders[0].position.x)
	if not is_equal_approx(first.origin.x,south_x - .972) or not is_equal_approx(first.origin.z,camp_colliders[0].position.z + .00975):
		return "not-the-pinned-outside-west-half"
	var detail := DETAIL as ArrayMesh
	if not detail:
		return "detail-not-a-triangle-array-mesh"
	var census := []
	for i in range(detail.get_surface_count()):
		var mat := detail.surface_get_material(i) as StandardMaterial3D
		if not mat or mat.emission_enabled or detail.surface_get_primitive_type(i) != Mesh.PRIMITIVE_TRIANGLES:
			return "unexpected-imported-surface-type"
		for prop in mat.get_property_list():
			if int(prop.type)==TYPE_OBJECT and mat.get(prop.name) is Texture:
				return "unexpected-imported-texture"
		var key := mat.resource_name.to_lower()
		if key != MATERIAL_ORDER[i]:
			return "material-sequence-mismatch"
		var ni := detail.surface_get_array_index_len(i)
		var nv := detail.surface_get_array_len(i)
		var tris := int((ni if ni > 0 else nv) / 3.0)
		if tris != MATERIAL_TRIANGLES[i]:
			return "material-triangle-budget"
		if not mat.albedo_color.is_equal_approx(EXPECTED_BASE[i]):
			return "draft-material-albedo"
		census.append({"label":key,"tris":tris,"vertices":nv,"indices":ni,"class":mat.get_class(),"roughness":mat.roughness})
	# Geometry + sourced local MTL is tested alone. Explicitly bind no shader
	# override, no V1 timber/snow material conversion and no emission/light fill.
	print("REFERENCE_PANEL_V2_MATERIALS ",JSON.stringify(census))
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
