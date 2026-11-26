extends Node3D
## One independent, conservative double-leaf technical gate; never grants progress.
signal hinge_moved(radians: float)

const HALF_SPAN := 1.20
const LEAF_LENGTH := 1.18
const LEAF_DEPTH := 0.14
const LEAF_HEIGHT := 1.35
const SWING_SPEED := 2.3
const INTERACTION_RANGE := 2.75
const SAFETY_MARGIN := 0.12
const APPROACH_DEPTH := 3.15
const CLEAR_DELAY := .80
var swing_direction := 1.
var clear_time := 0.
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
	clear_time = 0.
	swing_direction = 1.
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

func _near_aperture(at:Vector3) -> bool:
	return absf(at.x)<=HALF_SPAN+.08 and absf(at.z)<=APPROACH_DEPTH

func _leaf_clearance(at:Vector2,side:float,radians:float) -> float:
	var hinge := Vector2(side*HALF_SPAN,0.)
	var tip := hinge + Vector2(-side*cos(radians),-swing_direction*sin(radians))*LEAF_LENGTH
	return at.distance_to(Geometry2D.get_closest_point_to_segment(at,hinge,tip))

func _safe_step(at:Vector3,radius:float,next_angle:float) -> bool:
	if absf(at.x)>HALF_SPAN+radius+.24 or absf(at.z)>LEAF_LENGTH+radius+.24:
		return true
	var feet := Vector2(at.x,at.z)
	var limit := radius + SAFETY_MARGIN + LEAF_DEPTH*.5
	for side:float in [-1.,1.]:
		var old := _leaf_clearance(feet,side,angle)
		var next := _leaf_clearance(feet,side,next_angle)
		# Sample the swept arc as well as its endpoint. If somebody already
		# touches a closed leaf, it may move away from them to release them.
		var mid := _leaf_clearance(feet,side,(angle+next_angle)*.5)
		if minf(mid,next) < limit and (next<=old+.000001 or mid<old-.000001):
			return false
	return true

func advance_automatic(dt:float,player:Vector3,radius:float,helper:Vector3,bystanders:Array[Vector4]) -> void:
	if not active: return
	var local_player := to_local(player)
	var local_helper := to_local(helper) if helper.is_finite() else Vector3.INF
	var player_near := _near_aperture(local_player)
	var helper_near := _near_aperture(local_helper)
	if player_near or helper_near:
		if is_zero_approx(angle):
			# Each pair opens away from its first arriving traveler.
			var first := local_player if player_near else local_helper
			swing_direction = -1. if first.z < 0. else 1.
		target_open = true
		clear_time = 0.
	else:
		clear_time += dt
		if clear_time >= CLEAR_DELAY:
			target_open = false
	var next := move_toward(angle,PI*.5 if target_open else 0.,minf(dt,.02)*SWING_SPEED)
	holding_for_occupancy = false
	if is_equal_approx(next,angle): return
	holding_for_occupancy = not _safe_step(local_player,radius,next) or (local_helper.is_finite() and not _safe_step(local_helper,.38,next))
	if not holding_for_occupancy:
		for visitor:Vector4 in bystanders:
			if not _safe_step(to_local(Vector3(visitor.x,visitor.y,visitor.z)),visitor.w,next):
				holding_for_occupancy = true
				break
	if not holding_for_occupancy:
		angle = next
		_update_hinges()

func _update_hinges() -> void:
	_pivots[0].rotation.y = swing_direction * angle
	_pivots[1].rotation.y = -swing_direction * angle
	hinge_moved.emit(angle)
