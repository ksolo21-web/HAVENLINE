class_name HavenlineCampConstructionView
extends Node3D

## T11 presentation/placement adapter over the approved T10 transaction authority.
## This node never owns resource counts, transaction acceptance, or progression state.

const AUTHORITY_ID := "T11-camp-construction-view-v1"
const CATALOG_PATH := "res://data/camp_construction_recipes.json"
const TRANSACTION_AUTHORITY := "T10-world-transform-v1"
const MAX_AUTHORED_MESHES := 24
const PREVIEW_ALPHA := 0.46
const COMMIT_PULSE_HZ := 1.25
const COMMIT_PULSE_AMPLITUDE := 0.035

var target_id := ""
var construction_id := ""
var lifecycle := "ready"
var transaction_id := ""
var placement_origin := Vector3.ZERO
var occupied_footprints: Array = []
var placement_blocked := false
var scene_swap_count := 0
var catalog: Dictionary = {}
var _spec: Dictionary = {}
var _authored_root: Node3D
var _pulse_time := 0.0

static func contract() -> Dictionary:
	return {
		"authority_id": AUTHORITY_ID,
		"transaction_authority": TRANSACTION_AUTHORITY,
		"presentation_only": true,
		"mutates_resources": false,
		"advances_transform_state": false,
		"placement_validation_pure": true,
		"placement_validation_changes_t10_authority": false,
		"completion_requires_t10_accepted_receipt": true,
		"manual_action_button_required": false,
		"max_authored_meshes": MAX_AUTHORED_MESHES,
	}

static func placement_is_clear(origin: Vector3, occupied: Array, clearance_radius: float) -> bool:
	if not is_finite(clearance_radius) or clearance_radius <= 0.0:
		return false
	if not is_finite(origin.x) or not is_finite(origin.z):
		return false
	for blocker: Variant in occupied:
		if not (blocker is Dictionary):
			return false
		var position_value: Variant = blocker.get("position")
		var radius_value: Variant = blocker.get("radius")
		if not (position_value is Vector3) or not (radius_value is int or radius_value is float):
			return false
		var radius := float(radius_value)
		var position: Vector3 = position_value
		if not is_finite(radius) or radius < 0.0 or not is_finite(position.x) or not is_finite(position.z):
			return false
		var delta := Vector2(origin.x - position.x, origin.z - position.z)
		var distance := delta.length()
		var contact_limit := clearance_radius + radius
		if distance < contact_limit and not is_equal_approx(distance, contact_limit):
			return false
	return true

func _load_catalog() -> bool:
	if not FileAccess.file_exists(CATALOG_PATH):
		return false
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(CATALOG_PATH))
	if not (parsed is Dictionary):
		return false
	if parsed.get("authority_id") != "T11-camp-construction-content-v1":
		return false
	if parsed.get("transaction_authority") != TRANSACTION_AUTHORITY:
		return false
	if parsed.get("presentation_only") != true or parsed.get("shadow_resource_authority") != false:
		return false
	var rows: Variant = parsed.get("builds")
	if not (rows is Array) or rows.is_empty():
		return false
	var next := {}
	for row: Variant in rows:
		if not (row is Dictionary):
			return false
		for forbidden in ["costs", "prerequisites", "progression_tags"]:
			if row.has(forbidden):
				return false
		for required in ["construction_id", "world_transform_recipe_id", "presentation_key", "source_state", "target_state", "before_scene", "after_scene", "footprint_radius", "clearance_radius"]:
			if not row.has(required):
				return false
		var cid := String(row.construction_id)
		if cid.is_empty() or cid in next:
			return false
		if not FileAccess.file_exists(String(row.before_scene)) or not FileAccess.file_exists(String(row.after_scene)):
			return false
		if float(row.footprint_radius) <= 0.0 or float(row.clearance_radius) < float(row.footprint_radius):
			return false
		next[cid] = row.duplicate(true)
	catalog = next
	return true

func configure(next_target_id: String, next_construction_id: String) -> bool:
	if next_target_id.is_empty():
		return false
	if catalog.is_empty() and not _load_catalog():
		return false
	if next_construction_id not in catalog:
		return false
	target_id = next_target_id
	construction_id = next_construction_id
	_spec = catalog[next_construction_id].duplicate(true)
	transaction_id = ""
	lifecycle = "ready"
	placement_blocked = false
	_pulse_time = 0.0
	return _show_scene(String(_spec.before_scene), 0.0)

func set_placement_context(origin: Vector3, occupied: Array) -> bool:
	placement_origin = origin
	occupied_footprints = occupied.duplicate(true)
	placement_blocked = not placement_is_clear(origin, occupied_footprints, float(_spec.get("clearance_radius", 0.0)))
	return not placement_blocked

func _matches_t10(row: Dictionary) -> bool:
	return (
		String(row.get("target_id", "")) == target_id
		and String(row.get("recipe_id", "")) == String(_spec.get("world_transform_recipe_id", ""))
		and String(row.get("presentation_key", "")) == String(_spec.get("presentation_key", ""))
		and String(row.get("source_state", "")) == String(_spec.get("source_state", ""))
		and String(row.get("target_state", "")) == String(_spec.get("target_state", ""))
	)

func show_ready() -> bool:
	transaction_id = ""
	lifecycle = "blocked" if placement_blocked else "ready"
	return _show_scene(String(_spec.before_scene), 0.0)

func show_preview(preview: Dictionary) -> bool:
	if placement_blocked or not bool(preview.get("passed", false)) or not _matches_t10(preview):
		return false
	transaction_id = ""
	lifecycle = "preview"
	return _show_scene(String(_spec.after_scene), PREVIEW_ALPHA)

func show_blocked(preview: Dictionary) -> bool:
	if bool(preview.get("passed", true)) or String(preview.get("target_id", "")) != target_id:
		return false
	transaction_id = ""
	lifecycle = "blocked"
	return _show_scene(String(_spec.before_scene), 0.0)

func show_commit(intent: Dictionary) -> bool:
	if placement_blocked or not bool(intent.get("passed", false)) or bool(intent.get("replayed", false)):
		return false
	if not bool(intent.get("submit_debit_transaction", false)) or not _matches_t10(intent):
		return false
	var next_transaction := String(intent.get("transaction_id", ""))
	if next_transaction.is_empty():
		return false
	transaction_id = next_transaction
	lifecycle = "committing"
	_pulse_time = 0.0
	return _show_scene(String(_spec.after_scene), PREVIEW_ALPHA)

func mark_complete(receipt: Dictionary) -> bool:
	if lifecycle != "committing" or transaction_id.is_empty():
		return false
	if String(receipt.get("transaction_id", "")) != transaction_id:
		return false
	if not bool(receipt.get("authority_applied", false)) or not bool(receipt.get("accepted_by_world_transform", false)):
		return false
	if not _matches_t10(receipt):
		return false
	lifecycle = "complete"
	transaction_id = ""
	_pulse_time = 0.0
	return _show_scene(String(_spec.after_scene), 0.0)

func _show_scene(path: String, alpha: float) -> bool:
	var packed := load(path) as PackedScene
	if packed == null:
		return false
	var node := packed.instantiate()
	var root := node as Node3D
	if root == null:
		node.free()
		return false
	var mesh_count := _count_meshes(root)
	if mesh_count <= 0 or mesh_count > MAX_AUTHORED_MESHES:
		root.free()
		return false
	_set_mesh_alpha(root, alpha)
	if _authored_root != null and is_instance_valid(_authored_root):
		_authored_root.free()
	_authored_root = root
	add_child(_authored_root)
	scene_swap_count += 1
	return true

static func _count_meshes(root: Node) -> int:
	var count := 0
	var stack: Array[Node] = [root]
	while not stack.is_empty():
		var node: Node = stack.pop_back()
		if node is MeshInstance3D:
			count += 1
		for child in node.get_children():
			stack.append(child)
	return count

static func _set_mesh_alpha(root: Node, alpha: float) -> void:
	var stack: Array[Node] = [root]
	while not stack.is_empty():
		var node: Node = stack.pop_back()
		if node is MeshInstance3D:
			var mesh_instance := node as MeshInstance3D
			mesh_instance.transparency = alpha
		for child in node.get_children():
			stack.append(child)

func _process(delta: float) -> void:
	if lifecycle != "committing" or _authored_root == null:
		return
	_pulse_time += delta
	var pulse := 1.0 + sin(_pulse_time * TAU * COMMIT_PULSE_HZ) * COMMIT_PULSE_AMPLITUDE
	_authored_root.scale = Vector3.ONE * pulse

func descriptor() -> Dictionary:
	return {
		"authority_id": AUTHORITY_ID,
		"target_id": target_id,
		"construction_id": construction_id,
		"lifecycle": lifecycle,
		"transaction_id": transaction_id,
		"placement_blocked": placement_blocked,
		"current_scene": String(_spec.get("after_scene" if lifecycle in ["preview", "committing", "complete"] else "before_scene", "")),
		"mesh_count": _count_meshes(_authored_root) if _authored_root != null else 0,
		"scene_swap_count": scene_swap_count,
		"presentation_only": true,
		"mutates_resources": false,
		"advances_transform_state": false,
	}
