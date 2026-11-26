extends "res://previews/r17_fence/r17_fence_view.gd"
## Opt-in only by explicit detached scene selection. No authority mutation.
const Mount = preload("res://previews/gate_pair_study/gate_pair_mount.gd")
const StockReview = preload("res://previews/gate_pair_study/gate_art_review.gd")
const GRAFT_IDS := ["gate-south", "gate-east"]
var timber_outcome := "not-attempted"

func setup_camp() -> void:
	super.setup_camp()
	var reason := _graft_verified_four()
	if reason.is_empty():
		timber_outcome = "mounted-four-authored-v4"
		print("TIMBER_GATE_GRAFT ", timber_outcome)
	else:
		timber_outcome = "fallback:" + reason
		push_warning("TIMBER_GATE_FALLBACK: " + reason + "; original technical leaves retained")

func _graft_verified_four() -> String:
	# The exact earlier apply_all rejects a subclass by design. This distinct,
	# explicit scene validates its known composition instead of relaxing it.
	if scene_file_path != "res://previews/timber_gate/timber_gate_view.tscn":
		return "unexpected-scene"
	if OS.get_cmdline_user_args().has(StockReview.REVIEW_FLAG):
		return "conflicting-stock-review-flag"
	if not StockReview._translation_only(transform) or not StockReview._translation_only(global_transform):
		return "unexpected-scene-frame"
	if not camp_built or camp_built.get_parent() != self or camp_built.top_level or not Mount._frame_matches(camp_built.transform,Transform3D.IDENTITY):
		return "unexpected-camp"
	var shell := camp_built.get_node_or_null("R17FenceViewOnly") as Node3D
	if not shell or shell.get_child_count() != 2:
		return "no-admitted-r17-shell"
	if not _terrain_custody():
		return "terrain-custody"
	if gates.size() != 2:
		return "wrong-gate-count"
	var staged: Array[Dictionary] = []
	for index in range(2):
		var gate := gates[index]
		if gate.get_parent() != camp_built or gate.top_level or gate.gate_id != GRAFT_IDS[index] or not Mount._gate_frame_valid(gate):
			return "unexpected-gate-frame"
		var seats := StockReview._seats_for(gate)
		if seats.is_empty():
			return "terrain-seats"
		var offsets: Vector2 = seats.offsets
		for side: bool in [true,false]:
			var row := Mount._prepare_side(gate,side,offsets.x if side else offsets.y)
			if row.is_empty():
				return "incompatible-hinge-or-leaf"
			var ticket := _exact_donor(row.visual)
			if not ticket:
				return "donor-materials-or-topology"
			var placeholder := row.placeholder as MeshInstance3D
			if not placeholder.visible:
				return "technical-fallback-not-intact"
			staged.append(row)
	# All four poses and meshes verified before first mount. No transforms,
	# nodes, globals or server interfaces on the gate authority are modified.
	for row in staged:
		var art := MeshInstance3D.new()
		art.name = Mount.NAME
		art.mesh = row.visual
		row.pivot.add_child(art)
	for row in staged:
		row.placeholder.hide()
	return ""

func _exact_donor(input: Mesh) -> bool:
	var source := input as ArrayMesh
	if not source or source.get_surface_count() != 9:
		return false
	var seen: Array[String] = []
	var triangles := 0
	for i in range(9):
		var mat := source.surface_get_material(i) as StandardMaterial3D
		if not mat or mat.albedo_texture != null or source.surface_get_primitive_type(i) != Mesh.PRIMITIVE_TRIANGLES:
			return false
		var key := mat.resource_name.to_lower()
		if key in seen or key not in ["board","board_warm","board_soft","beam","brace_back","snow","metal","rope","rope_dark"]:
			return false
		seen.append(key)
		var indices := source.surface_get_array_index_len(i)
		triangles += int((indices if indices > 0 else source.surface_get_array_len(i)) / 3.0)
	return triangles == 1360

func _terrain_custody() -> bool:
	if not ground or not ground.is_inside_tree():
		return false
	var ground_root := ground.get_parent() as Node3D
	var surface := ground_root.get_parent() as Node3D if ground_root else null
	if not surface or surface.get_parent() != self or ground_root.name != &"AcceptedGround":
		return false
	if surface.scene_file_path != "res://previews/terrain_water_preview.tscn" or surface.get_node_or_null("AcceptedGround/GroundBody") != ground:
		return false
	if surface.get("water_bound") != true or ground_root.get("bound") != true:
		return false
	var col := ground.get_node_or_null("GroundTriangles") as CollisionShape3D
	var vis := ground_root.get_node_or_null("GroundVisual") as MeshInstance3D
	if not col or not vis or col.disabled or col.get_parent() != ground or vis.get_parent() != ground_root:
		return false
	for item: Node3D in [camp_built,surface,ground_root,ground,col,vis]:
		if item.top_level or not Mount._frame_matches(item.transform,Transform3D.IDENTITY) or not Mount._frame_matches(item.global_transform,global_transform):
			return false
	return StockReview._exact_terrain_contact(ground,col,vis)
