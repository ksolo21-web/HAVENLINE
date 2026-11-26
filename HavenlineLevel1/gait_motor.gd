extends RefCounted

const MAX_SPEED := 2.80
const DEAD_ZONE := 0.035
const ACCELERATION := 8.0
const BRAKING := 11.0
const MOVING_TURN := 5.9
const PIVOT_TURN := 10.8

# Track a sparse grid on both soles from the bound game mesh. The samples move
# with their original skin weights, so a heel strike can roll through to the toe.
var skeleton: Skeleton3D
var bind_transforms: Dictionary = {}
var samples: Array = []
var previous_contacts := PackedVector3Array()
var contact_world: Node3D
var foot_offsets: Array[Vector3] = [Vector3.ZERO, Vector3.ZERO]
var foot_twists := Vector2.ZERO
var braking_or_turning := false
var redirecting := false
var stopping := false
var settling_idle := false
var settle_side := -1
var settle_amount := 0.0
var settle_from := Vector3.ZERO
var settle_twist := 0.0
var previous_headings := PackedVector3Array()
var leg_chains: Array = []


func _bind_soles(world: Node3D) -> void:
	var body: Node3D = world.actor
	for part: MeshInstance3D in body.find_children("*", "MeshInstance3D", true, false):
		if not part.skin:
			continue
		skeleton = part.get_node(part.skeleton)
		var arrays := part.mesh.surface_get_arrays(0)
		var vertices: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX]
		var weights: PackedFloat32Array = arrays[Mesh.ARRAY_WEIGHTS]
		var indices: PackedInt32Array = arrays[Mesh.ARRAY_BONES]
		var width := weights.size() / vertices.size()
		var lowest := {}
		for i in vertices.size():
			var v := vertices[i]
			if v.y > .027:
				continue
			var cell := Vector2i(floori(v.x / .065), floori(v.z / .065))
			if not lowest.has(cell) or vertices[lowest[cell]].y > v.y:
				lowest[cell] = i
		for index: int in lowest.values():
			var influences := {}
			for k in width:
				var at := index * width + k
				if weights[at] <= 0:
					continue
				var binding := indices[at]
				bind_transforms[binding] = [
					skeleton.find_bone(part.skin.get_bind_name(binding)),
					part.skin.get_bind_pose(binding)
				]
				influences[binding] = weights[at]
			samples.append([vertices[index], influences])
		break
	if skeleton:
		contact_world = world
		for side in [".L", ".R"]:
			leg_chains.append(
				[
					skeleton.find_bone("Thigh" + side),
					skeleton.find_bone("Shin" + side),
					skeleton.find_bone("Foot" + side),
					skeleton.find_bone("Toe" + side)
				]
			)
		world.character_kit.locomotion.tree.mixer_applied.connect(_settle_support)


func _contacts() -> PackedVector3Array:
	var transforms := {}
	for binding: int in bind_transforms:
		var bind: Array = bind_transforms[binding]
		transforms[binding] = (
			skeleton.global_transform * skeleton.get_bone_global_pose(bind[0]) * bind[1]
		)
	var result := PackedVector3Array()
	for sample: Array in samples:
		var point := Vector3.ZERO
		for binding: int in sample[1]:
			point += (transforms[binding] * Vector3(sample[0])) * float(sample[1][binding])
		result.append(point)
	return result


func _sole_headings() -> PackedVector3Array:
	var headings := PackedVector3Array()
	for leg: Array in leg_chains:
		var toe := skeleton.get_bone_global_pose(leg[3]).origin
		var ankle := skeleton.get_bone_global_pose(leg[2]).origin
		headings.append((skeleton.global_basis * (toe - ankle)).slide(Vector3.UP).normalized())
	return headings


# Keep both authored link lengths and the original knee bend plane when the
# sole stays planted during redirection or braking. The collision body is never
# displaced by the animation.
func _adjust_leg(chain: Array, delta: Vector3, turn: float) -> void:
	var thigh := skeleton.get_bone_global_pose(chain[0])
	var shin := skeleton.get_bone_global_pose(chain[1])
	var boot := skeleton.get_bone_global_pose(chain[2])
	var target := boot.origin + skeleton.global_basis.inverse() * delta
	var axis := (target - thigh.origin).normalized()
	var upper := thigh.origin.distance_to(shin.origin)
	var lower := shin.origin.distance_to(boot.origin)
	var distance := clampf(
		target.distance_to(thigh.origin), absf(upper - lower) + .001, upper + lower - .001
	)
	var along := (distance * distance + upper * upper - lower * lower) / (2.0 * distance)
	var bend := (shin.origin - thigh.origin).slide(axis).normalized()
	var knee := thigh.origin + axis * along + bend * sqrt(maxf(0.0, upper * upper - along * along))
	target = thigh.origin + axis * distance
	var first := Quaternion(
		(shin.origin - thigh.origin).normalized(), (knee - thigh.origin).normalized()
	)
	thigh.basis = Basis(first) * thigh.basis
	skeleton.set_bone_global_pose(chain[0], thigh)
	var second := Quaternion((boot.origin - shin.origin).normalized(), (target - knee).normalized())
	shin.basis = Basis(second) * shin.basis
	shin.origin = knee
	skeleton.set_bone_global_pose(chain[1], shin)
	boot.basis = (
		Basis((skeleton.global_basis.inverse() * Vector3.UP).normalized(), -turn) * boot.basis
	)
	boot.origin = target
	skeleton.set_bone_global_pose(chain[2], boot)


func _settle_support() -> void:
	if previous_contacts.is_empty():
		return
	var after := _contacts()
	var offsets: Array[Vector3] = [Vector3.ZERO, Vector3.ZERO]
	var centers: Array[Vector3] = [Vector3.ZERO, Vector3.ZERO]
	var counts := Vector2i.ZERO
	var sole_height := Vector2(INF, INF)
	var ground: float = contact_world.actor.global_position.y
	for i in after.size():
		var side := int(Vector3(samples[i][0]).x < 0.0)
		sole_height[side] = minf(sole_height[side], after[i].y - ground)
		if previous_contacts[i].y > ground + .005 or after[i].y > ground + .006:
			continue
		offsets[side] += (previous_contacts[i] - after[i]).slide(Vector3.UP)
		centers[side] += after[i]
		counts[side] += 1
	previous_contacts.clear()
	var headings := _sole_headings()
	var dt := 1.0 / Engine.physics_ticks_per_second
	# Finish a brake by lifting each displaced boot back to its authored idle
	# pose, one at a time, with the opposite boot supporting the body.
	if settling_idle:
		if settle_side < 0:
			settle_side = int(foot_offsets[1].length_squared() > foot_offsets[0].length_squared())
			settle_from = foot_offsets[settle_side]
			settle_twist = foot_twists[settle_side]
			if settle_from.length() < .012 and absf(settle_twist) < .04:
				settling_idle = false
				settle_side = -1
			else:
				settle_amount = 0.0
		if settling_idle:
			settle_amount = minf(1.0, settle_amount + dt / .16)
			var weight := smoothstep(0.0, 1.0, settle_amount)
			foot_offsets[settle_side] = settle_from * (1.0 - weight)
			foot_twists[settle_side] = settle_twist * (1.0 - weight)
			for side in 2:
				var delta: Vector3 = skeleton.global_basis * foot_offsets[side]
				if side == settle_side:
					delta.y += .055 * sin(PI * settle_amount)
				_adjust_leg(leg_chains[side], delta, foot_twists[side])
			if settle_amount >= 1.0:
				settle_side = -1
			return
	for side in 2:
		var offset := Vector3.ZERO
		var twist := 0.0
		if braking_or_turning and counts[side] >= 2:
			var ankle: Vector3 = skeleton.to_global(
				skeleton.get_bone_global_pose(leg_chains[side][2]).origin
			)
			var lever: Vector3 = (centers[side] / float(counts[side]) - ankle).slide(Vector3.UP)
			twist = clampf(
				previous_headings[side].signed_angle_to(headings[side], Vector3.UP), -.90, .90
			)
			offset = offsets[side] / float(counts[side]) + lever - lever.rotated(Vector3.UP, -twist)
		var target: Vector3 = (skeleton.global_basis.inverse() * offset).limit_length(.17)
		var max_step: float = 2.4 * dt
		foot_offsets[side] = foot_offsets[side].move_toward(target, max_step)
		foot_twists[side] = move_toward(foot_twists[side], twist, 9.0 * dt)
		var lift := maxf(0.0, -sole_height[side] + .0002)
		if (
			foot_offsets[side].length_squared() > .000001
			or absf(foot_twists[side]) > .001
			or lift > .001
		):
			_adjust_leg(
				leg_chains[side],
				skeleton.global_basis * foot_offsets[side] + Vector3.UP * lift,
				foot_twists[side]
			)


func step(world: Node3D, input: Vector2, dt: float) -> float:
	var body: CharacterBody3D = world.actor
	var start := body.global_position
	var previous_speed := body.velocity.slide(Vector3.UP).length()
	if not skeleton:
		_bind_soles(world)
	var next_heading := body.rotation.y
	var requested := remap(clampf(input.length(), DEAD_ZONE, 1.0), DEAD_ZONE, 1.0, 0.0, MAX_SPEED)
	var forward := Vector3(sin(body.rotation.y), 0.0, cos(body.rotation.y))
	var speed := previous_speed
	if requested > 0.0:
		var view_right: Vector3 = world.camera.global_basis.x
		var view_near: Vector3 = view_right.cross(Vector3.UP)
		var wish: Vector3 = (view_right * input.x + view_near * input.y).normalized()
		if speed >= 2.0 and forward.dot(wish) < 0.05:
			redirecting = true
		var turn_speed := lerpf(PIVOT_TURN, MOVING_TURN, clampf(speed / MAX_SPEED, 0.0, 1.0))
		next_heading = rotate_toward(body.rotation.y, atan2(wish.x, wish.z), turn_speed * dt)
		forward = Vector3(sin(next_heading), 0.0, cos(next_heading))
		# Preserve running cadence through the turn. At a standing start the
		# body still pivots before carrying momentum into its first stride.
		if redirecting and forward.dot(wish) > .995:
			redirecting = false
		var turn_floor := 0.88 * smoothstep(1.15, 2.0, speed)
		requested *= lerpf(turn_floor, 1.0, smoothstep(-0.45, 0.85, forward.dot(wish)))
	speed = move_toward(speed, requested, (ACCELERATION if requested > speed else BRAKING) * dt)
	if requested <= 0.001:
		redirecting = false
		if previous_speed > 1.1:
			stopping = true
	if stopping and previous_speed <= .001:
		stopping = false
		settling_idle = true
	if requested > .001:
		stopping = false
		settling_idle = false
		settle_side = -1
	braking_or_turning = redirecting or stopping
	var changing_speed := absf(previous_speed - speed) > .005
	if (
		skeleton
		and (
			changing_speed
			or braking_or_turning
			or settling_idle
			or not foot_offsets[0].is_zero_approx()
			or not foot_offsets[1].is_zero_approx()
			or not foot_twists.is_zero_approx()
		)
	):
		previous_contacts = _contacts()
		previous_headings = _sole_headings()
	body.rotation.y = next_heading
	body.velocity = forward * speed
	body.move_and_slide()
	world.constrain_private_snow_travel()
	var traveled := (body.global_position - start).slide(Vector3.UP)
	# A wall or the edge of the map can shorten a stride. Drive the gait from that result.
	return traveled.length() / maxf(dt, 0.00001)
