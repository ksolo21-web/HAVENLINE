extends Node3D
## One independent, conservative double-leaf technical gate; never grants progress.
const HALF_SPAN := 1.20
const LEAF_LENGTH := 1.18
const LEAF_DEPTH := 0.14
const LEAF_HEIGHT := 1.35
const SWING_SPEED := 2.3
const INTERACTION_RANGE := 2.75
const SAFETY_MARGIN := 0.12
var gate_id := ""
var active := false
var target_open := false
var angle := 0.0
var holding_for_occupancy := false
var _leaf_bodies: Array[AnimatableBody3D] = []
var _pivots: Array[Node3D] = []

func build(id: String) -> void:
	gate_id = id
	name = id
	for side in [-1.0, 1.0]:
		var pivot := Node3D.new()
		pivot.name = "HingeLeft" if side < 0 else "HingeRight"
		add_child(pivot)
		pivot.position.x = side * HALF_SPAN
		_pivots.append(pivot)
		var body := AnimatableBody3D.new()
		body.sync_to_physics = false
		body.collision_layer = 0
		body.collision_mask = 0
		pivot.add_child(body)
		_leaf_bodies.append(body)
		body.position = Vector3(-side * LEAF_LENGTH * 0.5, LEAF_HEIGHT * 0.5, 0)
		var shape := CollisionShape3D.new()
		var box := BoxShape3D.new()
		box.size = Vector3(LEAF_LENGTH, LEAF_HEIGHT, LEAF_DEPTH)
		shape.shape = box
		body.add_child(shape)
		var mesh := MeshInstance3D.new()
		var panel := BoxMesh.new()
		panel.size = box.size
		var tint := StandardMaterial3D.new()
		tint.albedo_color = Color("#795b46")
		tint.roughness = 0.92
		mesh.material_override = tint
		mesh.mesh = panel
		body.add_child(mesh)
	visible = false

func set_earned(earned: bool) -> void:
	if active == earned:
		return
	active = earned
	target_open = false
	holding_for_occupancy = false
	angle = 0.0
	_update_hinges()
	visible = earned
	for body in _leaf_bodies:
		body.collision_layer = 1 if earned else 0

func interaction_in_range(feet: Vector3) -> bool:
	return active and global_position.distance_to(feet) <= INTERACTION_RANGE

func request_toggle(feet: Vector3) -> bool:
	if not interaction_in_range(feet):
		return false
	target_open = not target_open
	return true

func sweep_clear(feet: Vector3, capsule_radius: float) -> bool:
	# Full conservative pair sweep box, plus next-frame movement margin.
	# Freeze rather than pushing or teleporting any actor. This slice has only C1.
	var at := to_local(feet)
	var margin := capsule_radius + SAFETY_MARGIN + LEAF_DEPTH * 0.5
	return absf(at.x) > HALF_SPAN + margin or at.z < -LEAF_LENGTH - margin or at.z > margin

func advance(dt: float, feet: Vector3, capsule_radius: float) -> void:
	var wanted := PI * 0.5 if target_open else 0.0
	holding_for_occupancy = false
	if not active or is_equal_approx(angle, wanted):
		return
	if not sweep_clear(feet, capsule_radius):
		holding_for_occupancy = true
		return
	angle = move_toward(angle, wanted, clampf(dt, 0.0, .02) * SWING_SPEED)
	_update_hinges()

func _update_hinges() -> void:
	_pivots[0].rotation.y = angle
	_pivots[1].rotation.y = -angle
