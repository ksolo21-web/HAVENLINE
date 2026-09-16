class_name HavenlineWorldTransformView
extends Node3D

## T10 presentation-only world response. It owns no resources, progression, or
## transform authority. The geometry is deliberately neutral framework feedback
## so T11 can attach final camp/build content without changing T10 semantics.

const AUTHORITY_ID := "T10-world-transform-view-v1"
const CORE_LIFECYCLE := ["locked", "ready", "preview", "committing", "complete"]
const LIFECYCLE := ["locked", "ready", "preview", "committing", "complete", "blocked"]
const VISUAL_NODE_BUDGET := 4
const READABILITY_MIN := 0.85
const READABILITY_MAX := 1.35
const PULSE_HZ := 1.4

const STATE_COLORS := {
	"locked": Color("4a5159"),
	"ready": Color("63879a"),
	"preview": Color("e7a64a"),
	"committing": Color("5fa8d3"),
	"complete": Color("66b86a"),
	"blocked": Color("d86a5f"),
}

var target_id := ""
var lifecycle := "locked"
var presentation_key := ""
var source_state := ""
var target_state := ""
var target_revision := 0
var transaction_id := ""
var block_reasons: Array[String] = []
var blocked_shortfalls: Dictionary = {}
var update_count := 0
var visual_apply_count := 0
var visual_build_count := 0
var readability_scale := 1.0
var _pulse_time := 0.0

var _visual_root: Node3D
var _ring: MeshInstance3D
var _ghost: MeshInstance3D
var _beacon: MeshInstance3D
var _ring_material: StandardMaterial3D
var _ghost_material: StandardMaterial3D
var _beacon_material: StandardMaterial3D

static func contract() -> Dictionary:
	return {
		"authority_id": AUTHORITY_ID,
		"lifecycle": CORE_LIFECYCLE.duplicate(),
		"blocked_lifecycle": "blocked",
		"presentation_only": true,
		"mutates_resources": false,
		"advances_progression": false,
		"complete_requires_simulation_receipt": true,
		"complete_requires_world_transform_acceptance": true,
		"t11_owns_final_camp_content": true,
		"neutral_framework_visuals_only": true,
		"world_response_shapes": ["perimeter_ring", "preview_volume", "status_beacon"],
		"shape_and_color_redundancy": true,
		"visual_node_budget": VISUAL_NODE_BUDGET,
		"readability_scale_range": [READABILITY_MIN, READABILITY_MAX],
		"committing_pulse_hz": PULSE_HZ,
	}

func _ready() -> void:
	_ensure_visuals()
	_apply_visuals()

func configure(next_target_id: String) -> bool:
	if next_target_id.is_empty():
		return false
	target_id = next_target_id
	return true

func configure_readability(next_scale: float) -> bool:
	if not is_finite(next_scale) or next_scale < READABILITY_MIN or next_scale > READABILITY_MAX:
		return false
	if is_equal_approx(next_scale, readability_scale):
		return true
	readability_scale = next_scale
	_ensure_visuals()
	_visual_root.scale = Vector3.ONE * readability_scale
	visual_apply_count += 1
	return true

func set_locked() -> void:
	_clear_blocked()
	_set_lifecycle("locked")

func set_ready() -> void:
	_clear_blocked()
	_set_lifecycle("ready")

func show_preview(preview: Dictionary) -> bool:
	if not bool(preview.get("passed", false)) or String(preview.get("target_id", "")) != target_id:
		return false
	presentation_key = String(preview.get("presentation_key", ""))
	source_state = String(preview.get("source_state", ""))
	target_state = String(preview.get("target_state", ""))
	target_revision = int(preview.get("target_revision", 0))
	transaction_id = ""
	_clear_blocked()
	_set_lifecycle("preview")
	return true

func show_blocked(preview: Dictionary) -> bool:
	if bool(preview.get("passed", true)) or String(preview.get("target_id", "")) != target_id:
		return false
	var errors: Variant = preview.get("errors", [])
	if not (errors is Array) or errors.is_empty():
		return false
	block_reasons.clear()
	for error in errors:
		block_reasons.append(String(error))
	var shortfalls: Variant = preview.get("shortfalls", {})
	blocked_shortfalls = shortfalls.duplicate(true) if shortfalls is Dictionary else {}
	presentation_key = String(preview.get("presentation_key", presentation_key))
	source_state = String(preview.get("source_state", source_state))
	target_state = String(preview.get("target_state", target_state))
	target_revision = int(preview.get("target_revision", target_revision))
	transaction_id = ""
	_set_lifecycle("blocked")
	return true

func show_commit(intent: Dictionary) -> bool:
	if not bool(intent.get("passed", false)) or String(intent.get("target_id", "")) != target_id:
		return false
	if bool(intent.get("replayed", false)) or bool(intent.get("authoritative_applied", false)):
		return false
	var next_transaction_id := String(intent.get("transaction_id", ""))
	if next_transaction_id.is_empty() or not bool(intent.get("submit_debit_transaction", false)):
		return false
	presentation_key = String(intent.get("presentation_key", ""))
	source_state = String(intent.get("source_state", ""))
	target_state = String(intent.get("target_state", ""))
	target_revision = int(intent.get("target_revision", 0))
	transaction_id = next_transaction_id
	_clear_blocked()
	_set_lifecycle("committing")
	return true

func mark_complete(receipt: Dictionary) -> bool:
	if lifecycle != "committing":
		return false
	if not bool(receipt.get("authority_applied", false)) or String(receipt.get("authority_source", "")) != "simulation":
		return false
	if not bool(receipt.get("accepted_by_world_transform", false)):
		return false
	if String(receipt.get("transaction_id", "")) != transaction_id:
		return false
	if String(receipt.get("target_id", "")) != target_id or int(receipt.get("target_revision", -1)) != target_revision:
		return false
	_clear_blocked()
	_set_lifecycle("complete")
	return true

func _clear_blocked() -> void:
	block_reasons.clear()
	blocked_shortfalls.clear()

func _material(color: Color, alpha := 1.0) -> StandardMaterial3D:
	var material := StandardMaterial3D.new()
	var actual := color
	actual.a = alpha
	material.albedo_color = actual
	material.roughness = 0.55
	if alpha < 1.0:
		material.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	return material

func _ensure_visuals() -> void:
	if is_instance_valid(_visual_root):
		return
	_visual_root = Node3D.new()
	_visual_root.name = "T10WorldResponse"
	add_child(_visual_root)

	_ring = MeshInstance3D.new()
	_ring.name = "StateRing"
	var ring_mesh := CylinderMesh.new()
	ring_mesh.top_radius = 1.58
	ring_mesh.bottom_radius = 1.58
	ring_mesh.height = 0.08
	ring_mesh.radial_segments = 32
	_ring.mesh = ring_mesh
	_ring.position.y = 0.04
	_ring_material = _material(STATE_COLORS.locked, 0.78)
	_ring.material_override = _ring_material
	_visual_root.add_child(_ring)

	_ghost = MeshInstance3D.new()
	_ghost.name = "PreviewVolume"
	var ghost_mesh := BoxMesh.new()
	ghost_mesh.size = Vector3(2.58, 1.5, 2.58)
	_ghost.mesh = ghost_mesh
	_ghost.position.y = 0.78
	_ghost_material = _material(STATE_COLORS.preview, 0.17)
	_ghost.material_override = _ghost_material
	_visual_root.add_child(_ghost)

	_beacon = MeshInstance3D.new()
	_beacon.name = "StatusBeacon"
	var beacon_mesh := SphereMesh.new()
	beacon_mesh.radius = 0.24
	beacon_mesh.height = 0.48
	_beacon.mesh = beacon_mesh
	_beacon.position.y = 1.85
	_beacon_material = _material(STATE_COLORS.ready)
	_beacon.material_override = _beacon_material
	_visual_root.add_child(_beacon)

	_visual_root.scale = Vector3.ONE * readability_scale
	visual_build_count += 1

func _set_lifecycle(next: String) -> void:
	if next not in LIFECYCLE or next == lifecycle:
		return
	lifecycle = next
	update_count += 1
	_pulse_time = 0.0
	_apply_visuals()

func _apply_visuals() -> void:
	_ensure_visuals()
	var color: Color = STATE_COLORS.get(lifecycle, STATE_COLORS.locked)
	var ring_color := color
	ring_color.a = 0.78 if lifecycle != "complete" else 0.92
	_ring_material.albedo_color = ring_color
	_beacon_material.albedo_color = color
	var ghost_color := color
	ghost_color.a = 0.17 if lifecycle == "preview" else 0.11
	_ghost_material.albedo_color = ghost_color

	_ring.visible = lifecycle != "locked"
	_ghost.visible = lifecycle in ["preview", "committing"]
	_beacon.visible = lifecycle in ["ready", "committing", "complete", "blocked"]
	_beacon.scale = Vector3.ONE
	if lifecycle == "blocked":
		_beacon.scale = Vector3(1.35, 0.55, 1.35)
	elif lifecycle == "complete":
		_beacon.scale = Vector3.ONE * 1.25
	set_process(lifecycle == "committing")
	visual_apply_count += 1

func _process(delta: float) -> void:
	if lifecycle != "committing" or not is_instance_valid(_beacon):
		return
	_pulse_time = fmod(_pulse_time + delta, 10.0)
	var pulse := 1.0 + sin(_pulse_time * TAU * PULSE_HZ) * 0.18
	_beacon.scale = Vector3.ONE * pulse

func descriptor() -> Dictionary:
	return {
		"authority_id": AUTHORITY_ID,
		"target_id": target_id,
		"lifecycle": lifecycle,
		"presentation_key": presentation_key,
		"source_state": source_state,
		"target_state": target_state,
		"target_revision": target_revision,
		"transaction_id": transaction_id,
		"block_reasons": block_reasons.duplicate(),
		"blocked_shortfalls": blocked_shortfalls.duplicate(true),
		"update_count": update_count,
		"visual_apply_count": visual_apply_count,
		"visual_build_count": visual_build_count,
		"visual_node_count": _visual_root.get_child_count() + 1 if is_instance_valid(_visual_root) else 0,
		"readability_scale": readability_scale,
		"presentation_only": true,
		"mutates_resources": false,
		"advances_progression": false,
		"neutral_framework_visuals_only": true,
	}
