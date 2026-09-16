class_name HavenlineCampConstructionView
extends Node3D

## T11 presentation-only authored camp stage switcher. This node owns no
## inventory, economy, progression, transform authority or gameplay controls.
## Lifecycle feedback is an in-world pad-adjacent presentation layer only.

const MANIFEST_PATH := "res://assets/camp_upgrades_v1/manifest.json"
const AUTHORITY_ID := "T11-camp-construction-view-v1"
const LIFECYCLES := ["blocked", "ready", "preview", "committing", "complete", "error"]
const STATUS_RING_INNER_RADIUS := 0.74
const STATUS_RING_OUTER_RADIUS := 1.12
const STATUS_SPIRE_HEIGHT := 0.90
const STATUS_BEACON_OFFSET := Vector3(0.92, 0.0, 0.0)
const STATUS_ORB_RADIUS := 0.22

var manifest: Dictionary = {}
var current_stage_id := ""
var current_lifecycle := "blocked"
var stage_root: Node3D = null
var status_root: Node3D = null
var status_ring: MeshInstance3D = null
var status_spire: MeshInstance3D = null
var status_orb: MeshInstance3D = null
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

static func lifecycle_color(lifecycle: String) -> Color:
	match lifecycle:
		"blocked":
			return Color("68788f")
		"ready":
			return Color("f0bd32")
		"preview":
			return Color("36b8e3")
		"committing":
			return Color("f17c2f")
		"complete":
			return Color("4fbd72")
		"error":
			return Color("dd454f")
		_:
			return Color.WHITE

static func lifecycle_scale(lifecycle: String) -> float:
	match lifecycle:
		"blocked":
			return 0.80
		"ready":
			return 1.0
		"preview":
			return 1.08
		"committing":
			return 1.17
		"complete":
			return 0.72
		"error":
			return 1.02
		_:
			return 1.0

static func lifecycle_spire_scale(lifecycle: String) -> float:
	match lifecycle:
		"blocked":
			return 0.55
		"ready":
			return 0.90
		"preview":
			return 1.20
		"committing":
			return 1.80
		"complete":
			return 0.42
		"error":
			return 1.45
		_:
			return 1.0

static func lifecycle_emission(lifecycle: String) -> float:
	return 0.95 if lifecycle in ["ready", "preview", "committing", "error"] else 0.55

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

func _make_status_material(color: Color, emission_energy: float) -> StandardMaterial3D:
	var material := StandardMaterial3D.new()
	material.albedo_color = color
	material.roughness = 0.36
	material.metallic = 0.04
	material.emission_enabled = true
	material.emission = color
	material.emission_energy_multiplier = emission_energy
	return material

func _ensure_status_visual() -> void:
	if is_instance_valid(status_root):
		return
	status_root = Node3D.new()
	status_root.name = "LifecycleStatus"
	status_root.set_meta("t11_presentation_only", true)
	status_root.set_meta("t11_status_contract", "in_world_pad_adjacent")
	add_child(status_root)

	status_ring = MeshInstance3D.new()
	status_ring.name = "LifecycleRing"
	var ring := TorusMesh.new()
	ring.inner_radius = STATUS_RING_INNER_RADIUS
	ring.outer_radius = STATUS_RING_OUTER_RADIUS
	ring.rings = 36
	ring.ring_segments = 14
	status_ring.mesh = ring
	status_ring.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	status_root.add_child(status_ring)

	status_spire = MeshInstance3D.new()
	status_spire.name = "LifecycleSpire"
	var spire := CylinderMesh.new()
	spire.top_radius = 0.11
	spire.bottom_radius = 0.18
	spire.height = STATUS_SPIRE_HEIGHT
	spire.radial_segments = 16
	status_spire.mesh = spire
	status_spire.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	status_root.add_child(status_spire)

	status_orb = MeshInstance3D.new()
	status_orb.name = "LifecycleOrb"
	var orb := SphereMesh.new()
	orb.radius = STATUS_ORB_RADIUS
	orb.height = STATUS_ORB_RADIUS * 2.0
	orb.radial_segments = 20
	orb.rings = 10
	status_orb.mesh = orb
	status_orb.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	status_root.add_child(status_orb)

func _update_status_visual() -> void:
	_ensure_status_visual()
	if current_stage_id.is_empty() or manifest.is_empty() or current_stage_id not in manifest.get("stages", {}):
		status_root.visible = false
		return
	status_root.visible = true
	status_root.position = interaction_anchor() + Vector3(0.0, 0.045, 0.0)
	var color := lifecycle_color(current_lifecycle)
	var material := _make_status_material(color, lifecycle_emission(current_lifecycle))
	status_ring.material_override = material
	status_spire.material_override = material
	status_orb.material_override = material
	var ring_scale := lifecycle_scale(current_lifecycle)
	var spire_scale := lifecycle_spire_scale(current_lifecycle)
	status_ring.scale = Vector3.ONE * ring_scale
	status_spire.scale = Vector3(1.0, spire_scale, 1.0)
	status_spire.position = STATUS_BEACON_OFFSET + Vector3(0.0, STATUS_SPIRE_HEIGHT * spire_scale * 0.5, 0.0)
	status_orb.position = STATUS_BEACON_OFFSET + Vector3(0.0, STATUS_SPIRE_HEIGHT * spire_scale + STATUS_ORB_RADIUS * 1.15, 0.0)
	status_root.set_meta("t11_lifecycle", current_lifecycle)
	status_root.set_meta("t11_lifecycle_color", color.to_html(false))
	status_root.set_meta("t11_lifecycle_scale", ring_scale)
	status_root.set_meta("t11_lifecycle_spire_scale", spire_scale)

func set_lifecycle(lifecycle: String) -> bool:
	if lifecycle not in LIFECYCLES:
		return false
	if current_lifecycle != lifecycle:
		lifecycle_changes += 1
	current_lifecycle = lifecycle
	set_meta("t11_lifecycle", lifecycle)
	_update_status_visual()
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
		_update_status_visual()
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
	_update_status_visual()
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

func status_descriptor() -> Dictionary:
	return {
		"visible": is_instance_valid(status_root) and status_root.visible,
		"lifecycle": current_lifecycle,
		"anchor": status_root.position if is_instance_valid(status_root) else Vector3.ZERO,
		"color": lifecycle_color(current_lifecycle).to_html(false),
		"scale": lifecycle_scale(current_lifecycle),
		"spire_scale": lifecycle_spire_scale(current_lifecycle),
		"beacon_offset": STATUS_BEACON_OFFSET,
		"orb_radius": STATUS_ORB_RADIUS,
		"presentation_only": true,
	}

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
		"lifecycle_visual": status_descriptor(),
		"owns_resources": false,
		"owns_progression": false,
		"owns_economy": false,
		"build_pending_dependency": true,
	}
