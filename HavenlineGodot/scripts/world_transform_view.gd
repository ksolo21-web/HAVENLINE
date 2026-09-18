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
const RESOURCE_SYMBOLS = preload("res://assets/world_transform_v1/resource_symbols.tres")
const RESOURCE_GLYPHS := {"wood": "", "stone": "", "metal": "", "fuel": ""}

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
var _accepted_scale := Vector3(0.65, 0.12, 0.65)

var _visual_root: Node3D
var _ring: MeshInstance3D
var _ghost: MeshInstance3D
var _beacon: Label3D
var _ring_material: StandardMaterial3D
var _ghost_material: StandardMaterial3D
var displayed_costs: Dictionary = {}
var next_preview: Dictionary = {}
var _last_visual_signature: Array = []

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
		"world_response_shapes": ["perimeter_ring", "preview_volume", "status_label"],
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

func set_ready(preview: Dictionary = {}) -> void:
	if preview.is_empty() and lifecycle == "complete":
		source_state = target_state
		target_state = ""
		displayed_costs.clear()
		next_preview.clear()
	if not preview.is_empty() and String(preview.get("target_id", "")) == target_id:
		displayed_costs = preview.get("costs", {}).duplicate(true)
		source_state = String(preview.get("source_state", source_state))
		target_state = String(preview.get("target_state", target_state))
		presentation_key = String(preview.get("presentation_key", presentation_key))
		target_revision = int(preview.get("target_revision", 0)) + 1
	_clear_blocked()
	_set_lifecycle("ready")

func show_preview(preview: Dictionary) -> bool:
	if not bool(preview.get("passed", false)) or String(preview.get("target_id", "")) != target_id:
		return false
	displayed_costs = preview.get("costs", {}).duplicate(true)
	presentation_key = String(preview.get("presentation_key", ""))
	source_state = String(preview.get("source_state", ""))
	target_state = String(preview.get("target_state", ""))
	target_revision = int(preview.get("target_revision", 0)) + 1
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
	displayed_costs = preview.get("costs", {}).duplicate(true)
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
	displayed_costs = intent.get("debits", {}).duplicate(true)
	presentation_key = String(intent.get("presentation_key", ""))
	source_state = String(intent.get("source_state", ""))
	target_state = String(intent.get("target_state", ""))
	target_revision = int(intent.get("target_revision", 0))
	transaction_id = next_transaction_id
	_clear_blocked()
	_set_lifecycle("committing")
	return true

func mark_complete(receipt: Dictionary, next_offer: Dictionary = {}) -> bool:
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
	next_preview = next_offer.duplicate(true) if String(next_offer.get("target_id", "")) == target_id else {}
	_accepted_scale = _target_form_scale()
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
	# One tiny radial emission texture: pending activity, never transaction progress.
	var flow_gradient := Gradient.new()
	flow_gradient.offsets = PackedFloat32Array([0.0, 0.80, 0.88, 0.96, 1.0])
	flow_gradient.colors = PackedColorArray([Color.BLACK, Color.BLACK, Color.WHITE, Color.BLACK, Color.BLACK])
	var flow_texture := GradientTexture2D.new()
	flow_texture.width = 64
	flow_texture.height = 64
	flow_texture.gradient = flow_gradient
	flow_texture.fill = GradientTexture2D.FILL_RADIAL
	flow_texture.fill_from = Vector2(0.5, 0.5)
	flow_texture.fill_to = Vector2(1.0, 0.5)
	_ring_material.texture_repeat = false
	_ring_material.emission_texture = flow_texture
	_ring_material.emission = Color("b9edff")
	_ring_material.emission_energy_multiplier = 1.4
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

	_beacon = Label3D.new()
	_beacon.name = "StatusLabel"
	_beacon.position.y = 2.8
	var resource_font := ThemeDB.fallback_font.duplicate() as Font
	resource_font.fallbacks = [RESOURCE_SYMBOLS]
	_beacon.font = resource_font
	_beacon.font_size = 38
	_beacon.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_beacon.width = 1000.0
	_beacon.outline_size = 9
	_beacon.pixel_size = 0.006
	_beacon.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	_beacon.no_depth_test = true
	_visual_root.add_child(_beacon)

	_visual_root.scale = Vector3.ONE * readability_scale
	visual_build_count += 1

func _visual_signature() -> Array:
	return [lifecycle, presentation_key, source_state, target_state, target_revision, transaction_id, block_reasons.duplicate(), blocked_shortfalls.duplicate(true), displayed_costs.duplicate(true), next_preview.duplicate(true)]

func _set_lifecycle(next: String) -> void:
	if next not in LIFECYCLE: return
	if next != lifecycle:
		lifecycle = next
		update_count += 1
		_pulse_time = 0.0
	if _visual_signature() != _last_visual_signature:
		_apply_visuals()

func _apply_visuals() -> void:
	_ensure_visuals()
	var color: Color = STATE_COLORS.get(lifecycle, STATE_COLORS.locked)
	var ring_color := color
	ring_color.a = 0.78 if lifecycle != "complete" else 0.92
	_ring_material.albedo_color = ring_color
	_ring_material.emission_enabled = lifecycle == "committing"
	# CylinderMesh top-cap UV center is (.25, .75), with radius .25.
	# Normalize that atlas quarter to the full clamped radial texture.
	_ring_material.uv1_scale = Vector3(2.0, 2.0, 1.0) if lifecycle == "committing" else Vector3.ONE
	_ring_material.uv1_offset = Vector3(0.0, -1.0, 0.0) if lifecycle == "committing" else Vector3.ZERO
	var ghost_color := color
	ghost_color.a = 0.30 if lifecycle in ["preview", "committing"] else 1.0
	_ghost_material.albedo_color = ghost_color
	_ghost_material.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA if ghost_color.a < 1.0 else BaseMaterial3D.TRANSPARENCY_DISABLED
	_ring.visible = lifecycle != "locked"
	_ghost.visible = lifecycle != "locked"
	var target_form := lifecycle in ["preview", "committing", "complete"]
	_ghost.scale = _target_form_scale() if target_form else _accepted_scale
	_ghost.position.y = 0.08 + 0.75 * _ghost.scale.y
	_beacon.visible = lifecycle != "locked"
	_beacon.text = feedback_text()
	set_process(lifecycle == "committing")
	_last_visual_signature = _visual_signature()
	visual_apply_count += 1

func _process(delta: float) -> void:
	if lifecycle != "committing" or not is_instance_valid(_beacon):
		return
	_pulse_time = fmod(_pulse_time + delta, 10.0)
	var flow_scale := 1.0 + fmod(_pulse_time, 1.0) * 3.0
	_ring_material.uv1_scale = Vector3(2.0 * flow_scale, 2.0 * flow_scale, 1.0)
	_ring_material.uv1_offset = Vector3(0.5 - 0.5 * flow_scale, 0.5 - 1.5 * flow_scale, 0.0)
	var pulse := 1.0 + sin(_pulse_time * TAU * PULSE_HZ) * 0.18
	_ghost.scale = _target_form_scale() * pulse
	_ghost.position.y = 0.08 + 0.75 * _ghost.scale.y

func _target_form_scale() -> Vector3:
	return Vector3(1.0, minf(1.35, 1.0 + 0.25 * maxi(0, target_revision - 1)), 1.0)

func _quantities(values: Dictionary) -> String:
	var parts: Array[String] = []
	for kind in ["wood", "stone", "metal", "fuel"]:
		if values.has(kind): parts.append("%d %s" % [int(values[kind]), kind])
	return " + ".join(parts)

func _resource_cues(values: Dictionary, marker := "") -> String:
	var parts: Array[String] = []
	for kind in ["wood", "stone", "metal", "fuel"]:
		if values.has(kind):
			parts.append("%s%s %d %s" % [marker, RESOURCE_GLYPHS[kind], int(values[kind]), kind])
	return "   ".join(parts)

func _readable_reasons(reasons: Array, shortfalls: Dictionary = {}) -> String:
	var readable: Array[String] = []
	for reason in reasons:
		var text := String(reason)
		if text == "insufficient_resources" and not shortfalls.is_empty():
			continue # The exact delivery action already explains this reason.
		var friendly := text.replace("missing_prerequisite:", "Requires ").replace("_", " ")
		readable.append(friendly.left(1).to_upper() + friendly.substr(1))
	return " / ".join(readable)

func feedback_text() -> String:
	var destination := target_state.capitalize() if not target_state.is_empty() else "Transformation"
	var cost_context := destination + " · Cost: " + _quantities(displayed_costs) if not displayed_costs.is_empty() else destination
	if lifecycle == "complete":
		var text := destination + " complete\n\nPaid: " + _resource_cues(displayed_costs, "✓ ")
		if not next_preview.is_empty():
			text += "\nNext: " + String(next_preview.get("target_state", "")).capitalize()
			var next_shortfalls: Dictionary = next_preview.get("shortfalls", {})
			var next_action := "ready to preview" if next_preview.get("passed", false) else _readable_reasons(next_preview.get("errors", []), next_shortfalls)
			if not next_shortfalls.is_empty():
				next_action = "Deliver " + _quantities(next_shortfalls) + (" · " + next_action if not next_action.is_empty() else "")
			text += " · " + next_action
		return text
	if lifecycle == "blocked":
		var reason := _readable_reasons(block_reasons, blocked_shortfalls)
		if not blocked_shortfalls.is_empty():
			return "Deliver " + _quantities(blocked_shortfalls) + "\n\nMissing: " + _resource_cues(blocked_shortfalls, "□ ") + "\n" + cost_context + ("\n" + reason if not reason.is_empty() else "")
		return reason + "\n\n" + cost_context
	if lifecycle == "committing":
		return "Applying delivered resources\n\n" + _resource_cues(displayed_costs) + " → " + destination + "\nAwaiting confirmation"
	if lifecycle == "preview":
		return "Stay near the target\n\nDelivered stock: " + _resource_cues(displayed_costs) + " → " + destination
	return "Approach the target\n\nDelivered stock: " + _resource_cues(displayed_costs) + "\n" + cost_context

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
		"displayed_costs": displayed_costs.duplicate(true),
		"feedback_text": feedback_text(),
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
