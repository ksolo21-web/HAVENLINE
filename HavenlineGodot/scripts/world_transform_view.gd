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
const LABEL_CAMERA_OFFSET := Vector2(0.0, -190.0)
const LABEL_RENDER_PRIORITY := 100
const LABEL_OUTLINE_RENDER_PRIORITY := 99
const LABEL_MIN_CLEARANCE_PX := 12.0
const LABEL_SAFE_INSET_RATIO := 0.025
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
		"label_camera_offset": LABEL_CAMERA_OFFSET,
		"label_render_priority": LABEL_RENDER_PRIORITY,
		"label_outline_render_priority": LABEL_OUTLINE_RENDER_PRIORITY,
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
	# Label3D.offset is evaluated in the billboard camera plane. Keeping the
	# status lane above the maximum response envelope prevents the overhead
	# camera from collapsing world-Y separation into the ring/ghost silhouette.
	_beacon.offset = LABEL_CAMERA_OFFSET
	_beacon.render_priority = LABEL_RENDER_PRIORITY
	_beacon.outline_render_priority = LABEL_OUTLINE_RENDER_PRIORITY
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
	set_process(lifecycle != "locked")
	_last_visual_signature = _visual_signature()
	visual_apply_count += 1

func _process(delta: float) -> void:
	if not is_instance_valid(_beacon):
		return
	_update_camera_lane()
	if lifecycle != "committing":
		return
	_pulse_time = fmod(_pulse_time + delta, 10.0)
	var flow_scale := 1.0 + fmod(_pulse_time, 1.0) * 3.0
	_ring_material.uv1_scale = Vector3(2.0 * flow_scale, 2.0 * flow_scale, 1.0)
	_ring_material.uv1_offset = Vector3(0.5 - 0.5 * flow_scale, 0.5 - 1.5 * flow_scale, 0.0)
	var pulse := 1.0 + sin(_pulse_time * TAU * PULSE_HZ) * 0.18
	_ghost.scale = _target_form_scale() * pulse
	_ghost.position.y = 0.08 + 0.75 * _ghost.scale.y

func _projected_response_rect(active_camera: Camera3D) -> Rect2:
	var points: Array[Vector2] = []
	var radius := 1.58
	var top := 0.08 + 1.5 * _target_form_scale().y * 1.18
	for x in [-radius, radius]:
		for y in [0.0, top]:
			for z in [-radius, radius]:
				points.append(active_camera.unproject_position(_visual_root.to_global(Vector3(x, y, z))))
	var minimum := points[0]
	var maximum := points[0]
	for point in points:
		minimum = minimum.min(point)
		maximum = maximum.max(point)
	return Rect2(minimum, maximum - minimum)

func _label_projection(active_camera: Camera3D) -> Dictionary:
	var viewport_size := Vector2(get_viewport().get_visible_rect().size)
	var base := active_camera.unproject_position(_beacon.global_position)
	var camera_up := active_camera.global_transform.basis.y.normalized()
	var probe := active_camera.unproject_position(_beacon.global_position + camera_up * _beacon.pixel_size * 100.0)
	var pixels_per_label_unit := maxf(0.01, absf(probe.y - base.y) / 100.0)
	var measured := _beacon.font.get_multiline_string_size(_beacon.text, HORIZONTAL_ALIGNMENT_CENTER, _beacon.width, _beacon.font_size)
	var label_size := (measured + Vector2(_beacon.outline_size * 2.0, _beacon.outline_size * 2.0)) * pixels_per_label_unit
	var response := _projected_response_rect(active_camera)
	var gap := maxf(LABEL_MIN_CLEARANCE_PX, viewport_size.y * 0.015)
	var inset := maxf(LABEL_MIN_CLEARANCE_PX, minf(viewport_size.x, viewport_size.y) * LABEL_SAFE_INSET_RATIO)
	var desired := Vector2(response.get_center().x, response.position.y - gap - label_size.y * 0.5)
	if desired.y - label_size.y * 0.5 < inset:
		desired = Vector2(response.end.x + gap + label_size.x * 0.5, response.get_center().y)
	if desired.x + label_size.x * 0.5 > viewport_size.x - inset:
		desired.x = response.position.x - gap - label_size.x * 0.5
	var next_offset := (desired - base) / pixels_per_label_unit
	return {
		"viewport": viewport_size,
		"base": base,
		"pixels_per_label_unit": pixels_per_label_unit,
		"label_size": label_size,
		"response_rect": response,
		"desired_center": desired,
		"offset": next_offset,
		"gap": gap,
		"safe_inset": inset,
	}

func _update_camera_lane() -> void:
	var active_camera := get_viewport().get_camera_3d()
	if active_camera == null or lifecycle == "locked":
		return
	var projection := _label_projection(active_camera)
	_beacon.offset = projection.offset

func projected_readability(active_camera: Camera3D) -> Dictionary:
	if active_camera == null or not is_instance_valid(_beacon):
		return {"passed": false, "error": "missing_camera_or_label"}
	_update_camera_lane()
	var projection := _label_projection(active_camera)
	var label_rect := Rect2(projection.desired_center - projection.label_size * 0.5, projection.label_size)
	var response_rect: Rect2 = projection.response_rect
	var frame := Rect2(Vector2(projection.safe_inset, projection.safe_inset), projection.viewport - Vector2.ONE * projection.safe_inset * 2.0)
	var horizontal_gap := maxf(maxf(response_rect.position.x - label_rect.end.x, label_rect.position.x - response_rect.end.x), 0.0)
	var vertical_gap := maxf(maxf(response_rect.position.y - label_rect.end.y, label_rect.position.y - response_rect.end.y), 0.0)
	var clearance := maxf(horizontal_gap, vertical_gap)
	var overlap := label_rect.intersects(response_rect)
	var in_frame := frame.encloses(label_rect)
	var priority_ok := _beacon.render_priority == LABEL_RENDER_PRIORITY and _beacon.outline_render_priority == LABEL_OUTLINE_RENDER_PRIORITY
	return {
		"label_rect": [label_rect.position.x, label_rect.position.y, label_rect.size.x, label_rect.size.y],
		"response_rect": [response_rect.position.x, response_rect.position.y, response_rect.size.x, response_rect.size.y],
		"frame_rect": [frame.position.x, frame.position.y, frame.size.x, frame.size.y],
		"clearance_px": clearance,
		"required_clearance_px": projection.gap,
		"overlap": overlap,
		"fully_in_frame": in_frame,
		"priority_ok": priority_ok,
		"label_offset": [_beacon.offset.x, _beacon.offset.y],
		"passed": not overlap and in_frame and clearance + 0.01 >= float(projection.gap) and priority_ok,
	}

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
	var cost_cues := _resource_cues(displayed_costs)
	if lifecycle == "complete":
		var text := "COMPLETE — %s" % destination
		if not next_preview.is_empty():
			var next_destination := String(next_preview.get("target_state", "")).capitalize()
			var next_shortfalls: Dictionary = next_preview.get("shortfalls", {})
			var next_reason := _readable_reasons(next_preview.get("errors", []), next_shortfalls)
			if next_preview.get("passed", false):
				text = "NEXT — approach %s" % next_destination
			elif not next_shortfalls.is_empty():
				text = "NEXT — deliver missing resources\n" + _resource_cues(next_shortfalls)
			elif not next_reason.is_empty():
				text = "NEXT — " + next_reason
			if not next_shortfalls.is_empty() and not next_reason.is_empty():
				text += "\n" + next_reason
		text += "\n✓ %s complete\nPaid: %s" % [destination, _resource_cues(displayed_costs)]
		return text
	if lifecycle == "blocked":
		var reason := _readable_reasons(block_reasons, blocked_shortfalls)
		if not blocked_shortfalls.is_empty():
			var text := "BLOCKED — deliver missing resources\n" + _resource_cues(blocked_shortfalls)
			if not reason.is_empty(): text += "\n" + reason
			if not displayed_costs.is_empty(): text += "\n%s cost: %s" % [destination, cost_cues]
			return text
		return "BLOCKED — " + reason + ("\n%s cost: %s" % [destination, cost_cues] if not displayed_costs.is_empty() else "")
	if lifecycle == "committing":
		return "APPLYING → " + destination + "\nDelivered resources: " + cost_cues + "\nAwaiting confirmation"
	if lifecycle == "preview":
		return "PREVIEW — stay near " + destination + "\nCost from delivered stock:\n" + cost_cues
	return "READY — approach " + destination + ("\nCost from delivered stock:\n" + cost_cues if not displayed_costs.is_empty() else "")

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
		"label_camera_offset": [_beacon.offset.x, _beacon.offset.y] if is_instance_valid(_beacon) else [],
		"label_render_priority": _beacon.render_priority if is_instance_valid(_beacon) else -1,
		"label_outline_render_priority": _beacon.outline_render_priority if is_instance_valid(_beacon) else -1,
		"presentation_only": true,
		"mutates_resources": false,
		"advances_progression": false,
		"neutral_framework_visuals_only": true,
	}
