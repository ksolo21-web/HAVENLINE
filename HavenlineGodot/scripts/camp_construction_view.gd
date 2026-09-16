class_name HavenlineCampConstructionView
extends Node3D

## T11 presentation-only authored camp stage switcher. This node owns no
## inventory, economy, progression, transform authority or gameplay controls.

const MANIFEST_PATH := "res://assets/camp_upgrades_v1/manifest.json"
const AUTHORITY_ID := "T11-camp-construction-view-v1"
const LIFECYCLES := ["blocked", "ready", "preview", "committing", "complete", "error"]

var manifest: Dictionary = {}
var current_stage_id := ""
var current_lifecycle := "blocked"
var stage_root: Node3D = null
var rebuild_count := 0
var lifecycle_changes := 0

static func read_manifest(path := MANIFEST_PATH) -> Dictionary:
	if not FileAccess.file_exists(path):
		return {}
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(path))
	return parsed if parsed is Dictionary else {}

static func validate_manifest(value: Dictionary) -> bool:
	var stages: Variant = value.get("stages")
	if not (stages is Dictionary) or stages.is_empty():
		return false
	for stage_id: Variant in stages:
		if not (stage_id is String or stage_id is StringName) or String(stage_id).is_empty():
			return false
		var row: Variant = stages[stage_id]
		if not (row is Dictionary):
			return false
		var scene_path := String(row.get("scene", ""))
		if scene_path.is_empty() or not ResourceLoader.exists(scene_path):
			return false
		if not (row.get("interaction_anchor_xz") is Array) or row.interaction_anchor_xz.size() != 2:
			return false
	return true

func configure(value: Dictionary) -> bool:
	if not validate_manifest(value):
		return false
	manifest = value.duplicate(true)
	return true

func configure_from_file(path := MANIFEST_PATH) -> bool:
	return configure(read_manifest(path))

func _clear_stage() -> void:
	if is_instance_valid(stage_root):
		stage_root.free()
	stage_root = null

func set_lifecycle(lifecycle: String) -> bool:
	if lifecycle not in LIFECYCLES:
		return false
	if current_lifecycle != lifecycle:
		lifecycle_changes += 1
	current_lifecycle = lifecycle
	set_meta("t11_lifecycle", lifecycle)
	return true

func apply_stage(camp_state_id: String, lifecycle := "complete") -> Dictionary:
	if manifest.is_empty() and not configure_from_file():
		return {"passed": false, "errors": ["manifest_unavailable"], "rebuilt": false}
	if lifecycle not in LIFECYCLES:
		return {"passed": false, "errors": ["invalid_lifecycle"], "rebuilt": false}
	var stages: Dictionary = manifest.stages
	if camp_state_id not in stages:
		return {"passed": false, "errors": ["unknown_camp_state"], "rebuilt": false}
	set_lifecycle(lifecycle)
	if current_stage_id == camp_state_id and is_instance_valid(stage_root):
		return {"passed": true, "camp_state_id": current_stage_id, "lifecycle": current_lifecycle, "rebuilt": false, "rebuild_count": rebuild_count}
	var row: Dictionary = stages[camp_state_id]
	var packed := load(String(row.scene)) as PackedScene
	if packed == null:
		return {"passed": false, "errors": ["stage_scene_unavailable"], "rebuilt": false}
	var next := packed.instantiate() as Node3D
	if next == null:
		return {"passed": false, "errors": ["stage_scene_not_node3d"], "rebuilt": false}
	_clear_stage()
	stage_root = next
	stage_root.name = "ActiveCampStage"
	stage_root.set_meta("t11_camp_state_id", camp_state_id)
	stage_root.set_meta("t11_presentation_key", String(row.get("presentation_key", "")))
	add_child(stage_root)
	current_stage_id = camp_state_id
	rebuild_count += 1
	return {"passed": true, "camp_state_id": current_stage_id, "lifecycle": current_lifecycle, "rebuilt": true, "rebuild_count": rebuild_count}

func interaction_anchor() -> Vector3:
	if manifest.is_empty() or current_stage_id.is_empty() or current_stage_id not in manifest.get("stages", {}):
		return Vector3.ZERO
	var values: Array = manifest.stages[current_stage_id].interaction_anchor_xz
	return Vector3(float(values[0]), 0.0, float(values[1]))

func stage_node_count() -> int:
	if not is_instance_valid(stage_root):
		return 0
	return _count_nodes(stage_root)

func _count_nodes(node: Node) -> int:
	var total := 1
	for child in node.get_children():
		total += _count_nodes(child)
	return total

func descriptor() -> Dictionary:
	return {
		"authority_id": AUTHORITY_ID,
		"camp_state_id": current_stage_id,
		"lifecycle": current_lifecycle,
		"rebuild_count": rebuild_count,
		"lifecycle_changes": lifecycle_changes,
		"stage_node_count": stage_node_count(),
		"required_controls": [],
		"interaction_mode": "movement_proximity_context",
		"owns_resources": false,
		"owns_progression": false,
		"owns_economy": false,
		"build_pending_dependency": true,
	}
