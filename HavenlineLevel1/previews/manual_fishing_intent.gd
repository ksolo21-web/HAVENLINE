extends RefCounted
## Detached opt-in intent only: neither a scene hook nor the fishing authority.
## The eventual caller is responsible for admitting a spot and actual input.
const Terrain = preload("res://terrain_source.gd")
const River = preload("res://river_geometry.gd")
const DrySweep = preload("res://previews/fixture_dry_shore_sweep.gd")
const KEYS := ["admitted", "spot_id", "bank_xz", "aim_xz", "bank_side", "foot_radius",
	"stand_tolerance", "height_tolerance", "cast_range", "min_facing_dot", "keycode"]
var _binding: Dictionary = {}
var _last_seen_sequence := 0
var _held := false

static func _finite_number(value: Variant) -> bool:
	return (typeof(value) == TYPE_FLOAT or typeof(value) == TYPE_INT) and is_finite(float(value))

func bind(config: Dictionary) -> bool:
	# One-time bind; a subsequent call cannot reset input history or swap the aim.
	if not _binding.is_empty() or config.size() != KEYS.size():
		return false
	for key in KEYS:
		if not config.has(key):
			return false
	for key: Variant in config:
		if typeof(key) != TYPE_STRING:
			return false
	if typeof(config.admitted) != TYPE_BOOL or not config.admitted:
		return false
	if typeof(config.spot_id) != TYPE_STRING or config.spot_id.is_empty() or config.spot_id != config.spot_id.strip_edges():
		return false
	if typeof(config.bank_xz) != TYPE_VECTOR2 or typeof(config.aim_xz) != TYPE_VECTOR2:
		return false
	if not config.bank_xz.is_finite() or not config.aim_xz.is_finite():
		return false
	for key in ["bank_side", "foot_radius", "stand_tolerance", "height_tolerance", "cast_range", "min_facing_dot"]:
		if not _finite_number(config[key]):
			return false
	if float(config.bank_side) != -1.0 and float(config.bank_side) != 1.0:
		return false
	if float(config.stand_tolerance) <= 0.0 or float(config.height_tolerance) <= 0.0 or float(config.cast_range) <= 0.0:
		return false
	if float(config.min_facing_dot) < 0.0 or float(config.min_facing_dot) > 1.0:
		return false
	if typeof(config.keycode) != TYPE_INT or int(config.keycode) <= 0:
		return false
	var bank := Terrain.sample(config.bank_xz)
	var aim := Terrain.sample(config.aim_xz)
	if not bank.get("valid", false) or not aim.get("valid", false):
		return false
	if bank.crossing_reserved or aim.crossing_reserved or float(aim.shore_distance) >= 0.0:
		return false
	if not DrySweep.dry_footprint(config.bank_xz, float(config.foot_radius), float(config.bank_side), DrySweep.SWEEP_PAD):
		return false
	var aim_on_water := Vector3(config.aim_xz.x, River.WATER_Y, config.aim_xz.y)
	var bank_on_ground := Vector3(config.bank_xz.x, float(bank.height), config.bank_xz.y)
	if bank_on_ground.distance_to(aim_on_water) > float(config.cast_range):
		return false
	# All validated values are copied scalars; no caller callbacks or scene refs.
	_binding = config.duplicate()
	return true

func eligibility(frame: Node3D, actor: CharacterBody3D, camera: Camera3D) -> String:
	if _binding.is_empty():
		return "unadmitted"
	if not is_instance_valid(frame) or not is_instance_valid(actor) or not is_instance_valid(camera):
		return "unavailable"
	if not frame.is_inside_tree() or not actor.is_inside_tree() or not camera.is_inside_tree():
		return "unavailable"
	if not frame.is_ancestor_of(actor) or not frame.is_ancestor_of(camera) or camera.get_viewport() != actor.get_viewport() or not camera.is_current():
		return "wrong_view"
	if not actor.is_on_floor():
		return "airborne"
	var foot := frame.to_local(actor.global_position)
	var xz := Vector2(foot.x, foot.z)
	if not foot.is_finite():
		return "invalid_foot"
	var sample := Terrain.sample(xz)
	if not sample.get("valid", false):
		return "invalid_foot"
	if sample.crossing_reserved or not DrySweep.dry_footprint(xz, float(_binding.foot_radius), float(_binding.bank_side), DrySweep.SWEEP_PAD):
		return "unsafe_foot"
	if absf(foot.y - float(sample.height)) > float(_binding.height_tolerance):
		return "unsupported_foot"
	var bank_xz: Vector2 = _binding.bank_xz
	if xz.distance_to(bank_xz) > float(_binding.stand_tolerance):
		return "away_from_anchor"
	var aim_xz: Vector2 = _binding.aim_xz
	var to_target := aim_xz - xz
	var aim := Vector3(aim_xz.x, River.WATER_Y, aim_xz.y)
	if to_target.is_zero_approx() or foot.distance_to(aim) > float(_binding.cast_range):
		return "aim_out_of_range"
	var forward := frame.global_basis.inverse() * actor.global_basis.z
	var facing := Vector2(forward.x, forward.z)
	if not facing.is_finite() or facing.is_zero_approx() or facing.normalized().dot(to_target.normalized()) < float(_binding.min_facing_dot):
		return "wrong_facing"
	var world_aim := frame.to_global(aim)
	if not camera.is_position_in_frustum(world_aim) or not camera.is_position_in_frustum(actor.global_position):
		return "outside_view"
	return "eligible"

func capture(event: InputEvent, sequence: int, frame: Node3D, actor: CharacterBody3D, camera: Camera3D) -> Dictionary:
	if _binding.is_empty():
		return {"status":"unadmitted"}
	if not event is InputEventKey or event.physical_keycode != int(_binding.keycode):
		return {"status":"wrong_input"}
	if sequence <= _last_seen_sequence:
		return {"status":"duplicate_or_stale"}
	_last_seen_sequence = sequence
	if event.echo:
		return {"status":"echo"}
	if not event.pressed:
		_held = false
		return {"status":"released"}
	if _held:
		return {"status":"held"}
	_held = true
	var result := eligibility(frame, actor, camera)
	if result != "eligible":
		return {"status":result}
	var aim_xz: Vector2 = _binding.aim_xz
	return {"status":"intent", "spot_id":_binding.spot_id, "sequence":sequence,
		"aim_world":frame.to_global(Vector3(aim_xz.x, River.WATER_Y, aim_xz.y))}
