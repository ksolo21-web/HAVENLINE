extends "res://previews/r17_fence/r17_fence_view.gd"
## Opt-in only by explicit detached scene selection. No authority mutation.
const Mount = preload("res://previews/gate_pair_study/gate_pair_mount.gd")
const StockReview = preload("res://previews/gate_pair_study/gate_art_review.gd")
const REPAIRED_LEFT: Mesh = preload("res://previews/clearance_gate/assets/GateLeaf.obj")
const REPAIRED_RIGHT: Mesh = preload("res://previews/clearance_gate/assets/GateLeaf_Right.obj")
const IMPORT_CONFIG = preload("res://previews/clearance_gate/import_census.json")
const EXACT_TRIANGLES := {"beam":1036,"board":470,"board_soft":56,"board_warm":56,"brace_back":228,"metal":392,"rope":184,"rope_dark":184,"snow":620}
const GRAFT_IDS := ["gate-south", "gate-east"]
var clearance_outcome := "not-attempted"

func setup_camp() -> void:
	super.setup_camp()
	var reason := _graft_verified_four()
	if reason.is_empty():
		clearance_outcome = "mounted-four-clearance-authored"
		print("CLEARANCE_GATE_GRAFT ", clearance_outcome)
	else:
		clearance_outcome = "fallback:" + reason
		push_warning("CLEARANCE_GATE_FALLBACK: " + reason + "; original technical leaves retained")

func _graft_verified_four() -> String:
	# The exact earlier apply_all rejects a subclass by design. This distinct,
	# explicit scene validates its known composition instead of relaxing it.
	if scene_file_path != "res://previews/clearance_gate/clearance_gate_view.tscn":
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
			# The stock helper proves imported V4 donor and immutable side frame;
			# never present its donor here. The separately sealed repaired source
			# gets an independent envelope and material guard.
			var ticket := _exact_donor(REPAIRED_LEFT if side else REPAIRED_RIGHT,side)
			if not ticket:
				return "donor-materials-or-topology"
			var placeholder := row.placeholder as MeshInstance3D
			if not placeholder.visible:
				return "technical-fallback-not-intact"
			row.visual = REPAIRED_LEFT if side else REPAIRED_RIGHT
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

func _exact_donor(input: Mesh, left: bool) -> bool:
	var source := input as ArrayMesh
	if not source or source.get_surface_count() != 39:
		return false
	var contract: Dictionary = IMPORT_CONFIG.data.leaves["left" if left else "right"]
	if source.resource_path != String(contract.resource):
		return false
	var ordered: Array = contract.ordered_surfaces
	if ordered.size() != 39:
		return false
	var bounds := source.get_aabb()
	var low := Vector3(0 if left else -1.18,0,-.07)
	var high := Vector3(1.18 if left else 0,1.35,.07)
	if not bounds.position.is_finite() or not bounds.end.is_finite():
		return false
	for i in range(3):
		if bounds.position[i]<low[i]-.00001 or bounds.end[i]>high[i]+.00001:
			return false
		if absf(bounds.position[i]-float(contract.signed_aabb_m[0][i])) > .000001 or absf(bounds.end[i]-float(contract.signed_aabb_m[1][i])) > .000001:
			return false
	var totals := {}
	var triangles := 0
	for i in range(39):
		var mat := source.surface_get_material(i) as StandardMaterial3D
		var observed: Dictionary = ordered[i]
		if not mat or mat.albedo_texture != null or source.surface_get_primitive_type(i) != Mesh.PRIMITIVE_TRIANGLES:
			return false
		for prop in mat.get_property_list():
			if int(prop.type)==TYPE_OBJECT and mat.get(prop.name) is Texture:
				return false
		var key := mat.resource_name.to_lower()
		if int(observed.index)!=i or key!=String(observed.material) or mat.get_class()!=String(observed["class"]) or int(observed.primitive)!=int(source.surface_get_primitive_type(i)) or not EXACT_TRIANGLES.has(key):
			return false
		var indices := source.surface_get_array_index_len(i)
		var vertices := source.surface_get_array_len(i)
		var count := int((indices if indices > 0 else vertices) / 3.0)
		if count!=int(observed.triangles) or indices!=int(observed.indices) or vertices!=int(observed.vertices) or bool(observed.albedo_map):
			return false
		totals[key] = int(totals.get(key,0)) + count
		triangles += count
	if triangles != 3226 or totals.size()!=9:
		return false
	for label in EXACT_TRIANGLES:
		if int(totals.get(label,-1)) != int(EXACT_TRIANGLES[label]):
			return false
	return true

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
