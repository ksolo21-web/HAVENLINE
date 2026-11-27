extends RefCounted

const PREVIEW_TOP_SPEED := 2.80
const MAX_SPEED := 6.25
const DEAD_ZONE := 0.035
const MOVING_TURN := 5.9
const PIVOT_TURN := 10.8

var top_speed := PREVIEW_TOP_SPEED
var acceleration := 8.0
var braking := 11.0
var redirect_rate := 4.45

# Track a sparse grid on both soles from the bound game mesh. The samples move
# with their original skin weights, so a heel strike can roll through to the toe.
var skeleton: Skeleton3D
var bind_transforms: Dictionary = {}
var samples: Array = []
var contact_world: Node3D
var floor_pending := false
var redirecting := false
var turn_beats := 4
var support_step_serial := 0
var procedural_steps_active: bool:
	get:
		return not special.is_empty() or bridge
var lifted: Array[bool] = [false, false]
var travel_speed := 0.0
var previous_command_speed := 0.0
var releasing := false
var leg_chains: Array = []

# A grounded redirection starts on one boot. The second boot returns the actor
# to the normal walk or neutral stance without dragging both soles together.
var special := ""
var beat := 0
var beat_time := 0.0
var beat_duration := 0.17
var support := 0
var neutral_ankles: Array[Transform3D] = []
var boot_from: Array[Transform3D] = []
var toe_from: Array[Transform3D] = []
var step_targets: Array[Transform3D] = []
var toe_targets: Array[Transform3D] = []
var final_heading := 0.0
var gait_tree: AnimationTree
var desired_touchdown := 0.05
var sampled_scales: Dictionary = {}
var pelvis_index := -1
var spine_index := -1
var neck_index := -1
var field_turn_lean := 0.0
var recoil_height_offset := 0.0
var tilting_for_hit := false
var neutral_toes: Array[Transform3D] = []
var leg_tracking := 0.0
var action_elapsed := 0.0
var bridge := false
var bridge_time := 0.0
var bridge_wait := 0.0
var planned_landing := Transform3D.IDENTITY
var landing_time := -.1
var bridge_grounded := false
var bridge_side := 0
var bridge_origin := Transform3D.IDENTITY
var bridge_toe := Transform3D.IDENTITY
var initial_hold := 0.0
var previous_request := false


func use_field_run() -> void:
	top_speed = MAX_SPEED
	acceleration = 23.0
	braking = 44.0
	redirect_rate = 8.1


func _boot_world(side: int) -> Transform3D:
	return skeleton.global_transform * skeleton.get_bone_global_pose(leg_chains[side][2])


func _toe_relative(side: int) -> Transform3D:
	return (
		skeleton.get_bone_global_pose(leg_chains[side][2]).affine_inverse()
		* skeleton.get_bone_global_pose(leg_chains[side][3])
	)


func _prepare_steps(mode: String, heading: float) -> void:
	action_elapsed = 0.0 if not procedural_steps_active else .08
	bridge = false
	releasing = false
	special = mode
	beat = 0
	beat_time = 0.0
	initial_hold = .035 if mode == "pivot" else 0.0
	final_heading = heading
	boot_from = [_boot_world(0), _boot_world(1)]
	toe_from = [_toe_relative(0), _toe_relative(1)]
	var forward := Vector3(sin(heading), 0, cos(heading))
	if mode in ["brake", "turn", "change_pace"]:
		if mode in ["turn", "change_pace"] and contact_world.actor.velocity.length() > .2:
			forward = contact_world.actor.velocity.normalized()
		support = int(forward.dot(boot_from[1].origin - boot_from[0].origin) > 0)
		var boot_heights := _heights()
		if absf(boot_heights.x - boot_heights.y) > .012:
			support = int(boot_heights.y < boot_heights.x)
		beat_duration = .155 if mode in ["brake", "change_pace"] else .175
		if mode in ["turn", "change_pace"]:
			var support_lead: float = (
				(boot_from[support].origin - contact_world.actor.global_position).dot(forward)
			)
			beat_duration = clampf(.12 + support_lead * .32, .075, .175)
	else:
		var rotation: float = angle_difference(contact_world.actor.rotation.y, heading)
		support = int(rotation > 0)
		beat_duration = .16
	if mode == "turn":
		turn_beats = clampi(
			ceili(absf(angle_difference(contact_world.actor.rotation.y, heading)) / deg_to_rad(50)),
			2,
			4
		)
	var landing_side := support if mode != "turn" or turn_beats % 2 == 0 else 1 - support
	desired_touchdown = .555 if landing_side == 1 else .055
	var heights := _heights()
	for side in 2:
		lifted[side] = heights[side] > contact_world.actor.global_position.y + .025
	_brief_targets()


func _brief_targets() -> void:
	var body: CharacterBody3D = contact_world.actor
	var endpoint := body.global_transform
	var speed := body.velocity.slide(Vector3.UP).length()
	var travel := (
		speed * speed / (2.0 * braking) if special == "brake" else minf(.11, speed * beat_duration)
	)
	var facing := Vector3(sin(final_heading), 0, cos(final_heading))
	endpoint.basis = Basis(Vector3.UP, final_heading)
	endpoint.origin += facing * travel
	if special == "change_pace":
		var forecast := speed
		endpoint.origin = body.global_position
		for tick in ceili(60 * (beat_duration + .155 * .45)):
			forecast = move_toward(
				forecast, travel_speed, (acceleration if travel_speed > forecast else braking) / 60.
			)
			endpoint.origin += facing * forecast / 60.
	if special == "pivot":
		var yaw := rotate_toward(body.rotation.y, final_heading, 6.2 * beat_duration * 1.35)
		endpoint.basis = Basis(Vector3.UP, yaw)
	if special == "turn":
		var yaw := body.rotation.y
		var predicted_speed := speed
		endpoint.origin = body.global_position
		for tick in ceili(60 * (beat_duration + .175 * .45)):
			var turn_speed := redirect_rate
			yaw = rotate_toward(yaw, final_heading, turn_speed / 60.)
			var direction := Vector3(sin(yaw), 0, cos(yaw))
			var desired := (
				travel_speed * lerpf(.38, 1.0, smoothstep(-.45, .85, direction.dot(facing)))
			)
			predicted_speed = move_toward(
				predicted_speed,
				desired,
				(acceleration if desired > predicted_speed else braking) / 60.
			)
			endpoint.origin += direction * predicted_speed / 60.
		endpoint.basis = Basis(Vector3.UP, yaw)
	step_targets.clear()
	toe_targets = neutral_toes.duplicate()
	for side in 2:
		step_targets.append(endpoint * neutral_ankles[side])


func _heights() -> Vector2:
	var h := Vector2(INF, INF)
	var points := _contacts()
	for i in points.size():
		var side := int(Vector3(samples[i][0]).x < 0)
		h[side] = minf(h[side], points[i].y)
	return h


func _place_boot(side: int, target: Transform3D, toe: Transform3D) -> void:
	var current := _boot_world(side)
	_adjust_leg(leg_chains[side], target.origin - current.origin, 0.0, target.basis * toe.origin)
	var boot := skeleton.get_bone_global_pose(leg_chains[side][2])
	boot.basis = skeleton.global_basis.inverse() * target.basis
	if top_speed == MAX_SPEED:
		# A planted winter boot can roll onto the heel or toe. Preserve the
		# FieldRun ankle envelope as the hips pass over it during a fast turn.
		var shin := skeleton.get_bone_global_pose(leg_chains[side][1])
		var relative := shin.basis.inverse() * boot.basis
		var angles := relative.orthonormalized().get_euler(EULER_ORDER_ZYX)
		angles.x = clampf(angles.x, deg_to_rad(-124.), deg_to_rad(-38.))
		angles.y = clampf(angles.y, deg_to_rad(-8.), deg_to_rad(8.))
		angles.z = clampf(angles.z, deg_to_rad(-10.), deg_to_rad(10.))
		boot.basis = shin.basis * Basis.from_euler(angles, EULER_ORDER_ZYX).scaled_local(relative.get_scale())
	skeleton.set_bone_global_pose(leg_chains[side][2], boot)
	skeleton.set_bone_global_pose(leg_chains[side][3], boot * toe)


func _play_steps(dt: float) -> void:
	action_elapsed += dt
	leg_tracking = smoothstep(0.0, .075, action_elapsed)
	var swing := 1 - support
	var latest := _boot_world(swing)
	var latest_toe := _toe_relative(swing)
	var last_beat := releasing or beat >= (turn_beats - 1 if special == "turn" else 1)
	var t := clampf(beat_time / beat_duration, 0.0, 1.0)
	var u := smoothstep(0.0, 1.0, t)
	if special == "turn":
		# Accelerate into lift-off and brake into touchdown while maintaining
		# an even speed through the airborne middle of the step.
		var ramp := .14
		if t < ramp:
			u = t * t / (2.0 * ramp * (1.0 - ramp))
		elif t > 1.0 - ramp:
			u = 1.0 - (1.0 - t) * (1.0 - t) / (2.0 * ramp * (1.0 - ramp))
		else:
			u = (t - ramp * .5) / (1.0 - ramp)
	var from := boot_from[swing]
	var to := step_targets[swing]
	var pelvis := skeleton.get_bone_global_pose(pelvis_index)
	var pelvis_world := skeleton.to_global(pelvis.origin)
	var toward := (boot_from[support].origin - pelvis_world).slide(Vector3.UP).normalized()
	# Keep the planted ankle reachable as the hips turn over the support leg.
	var thigh_position := skeleton.to_global(
		skeleton.get_bone_global_pose(leg_chains[support][0]).origin
	)
	var knee_position := skeleton.to_global(
		skeleton.get_bone_global_pose(leg_chains[support][1]).origin
	)
	var ankle_position := _boot_world(support).origin
	var target := boot_from[support].origin
	var reach := (
		thigh_position.distance_to(knee_position) + knee_position.distance_to(ankle_position) - .006
	)
	var reach_gap := maxf(0, thigh_position.distance_to(target) - reach)
	pelvis.origin += (
		skeleton.global_basis.inverse()
		* (target - thigh_position).normalized()
		* minf(.17, reach_gap)
	)
	var transfer := sin(PI * t)
	pelvis.origin += (
		skeleton.global_basis.inverse() * (toward * .027 - Vector3.UP * .045) * transfer
	)
	skeleton.set_bone_global_pose(pelvis_index, pelvis)
	if last_beat:
		to = latest
	var moving := from.interpolate_with(to, u)
	moving.origin.y += .090 * sin(PI * t)
	var yaw: float = contact_world.actor.rotation.y
	var outward := Vector3(cos(yaw), 0, -sin(yaw)) * (1.0 if swing == 0 else -1.0)
	var spacing: float = (moving.origin - boot_from[support].origin).dot(outward)
	var step_weight := smoothstep(0.0, .30, t)
	if special == "turn" and last_beat and travel_speed <= 1.7:
		# Release the outward clearance offset as the authored foot lands.
		# Otherwise the first frame after the turn pulls the planted boot sideways.
		step_weight *= 1.0 - smoothstep(.63, 1.0, t)
	moving.origin += outward * maxf(0.0, .28 - spacing) * step_weight
	var support_knee := skeleton.to_global(
		skeleton.get_bone_global_pose(leg_chains[support][1]).origin
	)
	var body_center := skeleton.to_global(pelvis.origin)
	var around_hip: float = (moving.origin - body_center).dot(outward)
	moving.origin += outward * maxf(0.0, .115 - around_hip) * step_weight
	var knee_space: float = (moving.origin - support_knee).dot(outward)
	moving.origin += outward * maxf(0.0, .25 - knee_space) * step_weight
	_place_boot(support, boot_from[support], toe_from[support])
	_place_boot(
		swing,
		moving,
		toe_from[swing].interpolate_with(latest_toe if last_beat else toe_targets[swing], u)
	)
	var h := _heights()[support]
	var correction: float = clampf(contact_world.actor.global_position.y + .001 - h, -.05, .03)
	if absf(correction) > .0015:
		var held := _boot_world(support)
		held.origin.y += correction
		_place_boot(support, held, toe_from[support])
	# A newly braked swing can arrive below the floor before the first beat.
	if special == "brake":
		var clearance: float = _heights()[swing] - contact_world.actor.global_position.y
		if clearance < 0.0:
			var raised := _boot_world(swing)
			raised.origin.y += .0005 - clearance
			_place_boot(swing, raised, _toe_relative(swing))
	if t < 1.0:
		beat_time = minf(beat_duration, beat_time + dt)
		return
	if last_beat:
		bridge = true
		bridge_time = 0.0
		bridge_wait = 0.0
		landing_time = -.1
		bridge_grounded = false
		bridge_side = support
		bridge_origin = _boot_world(support)
		bridge_toe = _toe_relative(support)
		special = ""
		return
	boot_from = [_boot_world(0), _boot_world(1)]
	toe_from = [_toe_relative(0), _toe_relative(1)]
	support = swing
	beat += 1
	if special == "turn":
		beat_duration = .175
	if special == "change_pace":
		beat_duration = .155
	beat_time = 0.0
	_brief_targets()


func _release_last_foot(dt: float) -> void:
	var live := _boot_world(bridge_side)
	var toe := _toe_relative(bridge_side)
	if not bridge_grounded:
		var h := _heights()[1 - bridge_side]
		if h <= contact_world.actor.global_position.y + .006 or bridge_wait >= .18:
			bridge_grounded = true
		else:
			bridge_wait += dt
			_place_boot(bridge_side, bridge_origin, bridge_toe)
			return
	if landing_time < 0.0:
		var body: CharacterBody3D = contact_world.actor
		var hz: float = contact_world.character_kit.locomotion.stride_hz
		var phase: float = (
			float(gait_tree.get("parameters/walk/current_position"))
			/ contact_world.character_kit.locomotion.walk_length
		)
		var future_phase := .51 if bridge_side == 1 else .01
		var remaining := fposmod(future_phase - phase, 1.0)
		landing_time = clampf(remaining / maxf(.75, hz), .20, .35)
		var endpoint := body.global_transform
		var forward := body.velocity.slide(Vector3.UP)
		var shoe_lead := minf(.29, forward.length() * .135)
		endpoint.origin += forward * landing_time + forward.normalized() * shoe_lead
		planned_landing = endpoint * neutral_ankles[bridge_side]
	var t := clampf(bridge_time / landing_time, 0, 1)
	leg_tracking = 1.0 - smoothstep(.55, 1.0, t)
	var weight := smoothstep(0, 1, t)
	var dest := bridge_origin.interpolate_with(planned_landing, weight)
	dest = dest.interpolate_with(live, smoothstep(.55, 1.0, t))
	dest.origin.y += .08 * sin(PI * t)
	_place_boot(bridge_side, dest, bridge_toe.interpolate_with(toe, weight))
	if t >= 1.0:
		bridge = false
	bridge_time += dt


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
		neutral_ankles = [
			body.global_transform.affine_inverse() * _boot_world(0),
			body.global_transform.affine_inverse() * _boot_world(1)
		]
		neutral_toes = [_toe_relative(0), _toe_relative(1)]
		pelvis_index = skeleton.find_bone("Pelvis")
		spine_index = skeleton.find_bone("Spine")
		neck_index = skeleton.find_bone("Neck")
		gait_tree = world.character_kit.locomotion.tree
		var graph: AnimationNodeBlendTree = gait_tree.tree_root
		graph.disconnect_node("output", 0)
		graph.add_node("transfer_speed", AnimationNodeTimeScale.new())
		graph.connect_node("transfer_speed", 0, "movement")
		graph.connect_node("output", 0, "transfer_speed")
		gait_tree.mixer_applied.connect(_settle_support)


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


# Gameplay recoil rotates the full figure after locomotion has solved both legs.
# Restore the original model frame before solving the next step, then tilt about
# the contacting outsole or its current airborne height.
func clear_hit_pose(visual: Node3D) -> void:
	if not tilting_for_hit:
		return
	visual.position.y -= recoil_height_offset
	visual.rotation.x = 0.0
	visual.rotation.z = 0.0
	recoil_height_offset = 0.0
	tilting_for_hit = false


func apply_hit_pose(visual: Node3D, pitch: float, roll: float) -> void:
	if is_zero_approx(pitch) and is_zero_approx(roll):
		return
	tilting_for_hit = true
	var before := _heights() if skeleton else Vector2.ZERO
	visual.rotation.x = pitch
	visual.rotation.z = roll
	if skeleton:
		var after := _heights()
		var gap := minf(before.x, before.y) - minf(after.x, after.y)
		var up := (visual.get_parent_node_3d().global_basis.inverse() * Vector3.UP).y
		recoil_height_offset = gap * up
		visual.position.y += recoil_height_offset


# Return the centre of each boot's supporting patch. The tread first lands
# on a heel and rolls forward. Snow impressions stay under that actual patch.
func snow_contact_points() -> PackedVector3Array:
	var points := _contacts()
	if points.is_empty():
		return PackedVector3Array()
	var lows := Vector2(INF, INF)
	for i in points.size():
		var side := int(Vector3(samples[i][0]).x < 0)
		lows[side] = minf(lows[side], points[i].y)
	var centers := PackedVector3Array([Vector3.ZERO, Vector3.ZERO])
	var counts := Vector2i.ZERO
	for i in points.size():
		var side := int(Vector3(samples[i][0]).x < 0)
		if points[i].y <= lows[side] + .004:
			centers[side] += points[i]
			counts[side] += 1
	for side in 2:
		centers[side] /= maxi(1, counts[side])
		centers[side].y = lows[side]
	return centers


# Solve the original hip–knee–ankle chain in its authored bend plane.
# Steering stays on the collision body; the foot targets affect only the rig.
func _adjust_leg(chain: Array, delta: Vector3, turn: float, target_toe := Vector3.ZERO) -> void:
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
	var radius := sqrt(maxf(0.0, upper * upper - along * along))
	# When the ankle crosses its native rest line, follow the toe with the
	# kneecap. The admissible arc preserves both skeletal link lengths.
	if procedural_steps_active and radius > .0001:
		var world_axis := skeleton.global_basis * (target - thigh.origin)
		var side: float = 1.0 if chain[0] == leg_chains[0][0] else -1.0
		var body_front: Vector3 = contact_world.actor.global_basis.z.slide(Vector3.UP).normalized()
		var toe_front := (
			target_toe.slide(Vector3.UP).normalized()
			if target_toe.length_squared() > .000001
			else body_front
		)
		var sagittal: Vector3 = body_front.slerp(toe_front, .58).normalized()
		var lateral: Vector3 = Vector3.UP.cross(sagittal).normalized() * side
		var frontal := lateral - Vector3.UP * world_axis.dot(lateral) / minf(-.001, world_axis.y)
		var plane: Vector3 = (skeleton.global_basis.transposed() * frontal).slide(axis)
		var sensitivity := radius * plane.length()
		if sensitivity > .01:
			plane = plane.normalized()
			var toe := skeleton.get_bone_global_pose(chain[3]).origin
			var toe_forward: Vector3 = (
				(skeleton.global_basis * (toe - boot.origin)).slide(Vector3.UP).normalized()
			)
			var wanted := .004
			var component := bend.dot(plane)
			var corrected := clampf(
				component, (wanted - .010) / sensitivity, (wanted + .023) / sensitivity
			)
			var value := lerpf(component, clampf(corrected, -.97, .97), leg_tracking)
			var other := bend.slide(plane).normalized()
			bend = (plane * value + other * sqrt(maxf(0, 1.0 - value * value))).normalized()
	# A moving brake target can cross the projected knee, reversing the old
	# estimate while the hips still face forward. Select the anatomical side
	# of the sagittal plane during the stop, its handoff, and floor correction.
	if top_speed == MAX_SPEED:
		var facing: Vector3 = contact_world.actor.global_basis.z.slide(Vector3.UP).normalized()
		var world_axis := skeleton.global_basis * axis
		var sagittal_normal := facing + Vector3.UP * world_axis.dot(facing) / maxf(.001, -world_axis.y)
		var anterior := (skeleton.global_basis.transposed() * sagittal_normal).normalized()
		var projection := bend.dot(anterior)
		if projection < .25:
			var lateral_deflection := bend.slide(anterior).normalized()
			var front_component := clampf(absf(projection), .25, 1.0)
			bend = (anterior * front_component + lateral_deflection * sqrt(maxf(0., 1. - front_component * front_component))).normalized()
	var knee := thigh.origin + axis * along + bend * radius
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
	# Bank the torso into a field turn while the boots follow their grounded
	# track. The neck absorbs part of the roll so the gaze remains level.
	if absf(field_turn_lean) > .0001:
		var forward: Vector3 = (skeleton.global_basis.inverse() * contact_world.actor.global_basis.z).normalized()
		var spine := skeleton.get_bone_global_pose(spine_index)
		spine.basis = Basis(forward, -field_turn_lean) * spine.basis
		skeleton.set_bone_global_pose(spine_index, spine)
		var neck := skeleton.get_bone_global_pose(neck_index)
		neck.basis = Basis(forward, field_turn_lean * .50) * neck.basis
		skeleton.set_bone_global_pose(neck_index, neck)
	if special.is_empty() and not bridge and not floor_pending:
		return
	# IK repositions and rotates the legs. Preserve the sampled local scales:
	# repeatedly decomposing a world-space boot or toe transform can introduce
	# shear that the animation mixer treats as the next frame's static scale.
	sampled_scales[pelvis_index] = skeleton.get_bone_pose_scale(pelvis_index)
	for chain: Array in leg_chains:
		for bone: int in chain:
			sampled_scales[bone] = skeleton.get_bone_pose_scale(bone)
	var dt := 1.0 / Engine.physics_ticks_per_second
	var protected_step := procedural_steps_active
	if not special.is_empty():
		_play_steps(dt)
	elif bridge:
		_release_last_foot(dt)
	else:
		var heights := _heights()
		for side in 2:
			var lift: float = contact_world.actor.global_position.y - heights[side] + .0002
			if lift > .001:
				_adjust_leg(leg_chains[side], Vector3.UP * lift, 0.0)

	for bone: int in sampled_scales:
		skeleton.set_bone_pose_scale(bone, sampled_scales[bone])

	if protected_step:
		var heights := _heights()
		var ground: float = contact_world.actor.global_position.y
		var floor_gap := ground - minf(heights.x, heights.y)
		if top_speed == MAX_SPEED and floor_gap > .001:
			# At the exchange of support the ankle can reach its cuff limit
			# before the whole outsole clears the snow. Raise the hips with
			# both legs together, preserving the constrained boot rotations.
			var pelvis := skeleton.get_bone_global_pose(pelvis_index)
			pelvis.origin += skeleton.global_basis.inverse() * Vector3.UP * floor_gap
			skeleton.set_bone_global_pose(pelvis_index, pelvis)
			heights += Vector2.ONE * floor_gap
		for side in 2:
			if heights[side] > ground + .025:
				lifted[side] = true
			elif lifted[side] and heights[side] <= ground + .008:
				lifted[side] = false
				support_step_serial += 1


func step(world: Node3D, input: Vector2, dt: float) -> float:
	var body: CharacterBody3D = world.actor
	var start := body.global_position
	var previous_speed := body.velocity.slide(Vector3.UP).length()
	if not skeleton:
		_bind_soles(world)
	var next_heading := body.rotation.y
	var requested := remap(clampf(input.length(), DEAD_ZONE, 1.0), DEAD_ZONE, 1.0, 0.0, top_speed)
	var forward := Vector3(sin(body.rotation.y), 0.0, cos(body.rotation.y))
	var speed := previous_speed
	travel_speed = requested
	if requested > 0.0:
		var view_right: Vector3 = world.camera.global_basis.x
		var view_near: Vector3 = view_right.cross(Vector3.UP)
		var wish: Vector3 = (view_right * input.x + view_near * input.y).normalized()
		var heading := atan2(wish.x, wish.z)
		if (
			skeleton
			and special.is_empty()
			and not redirecting
			and speed < .14
			and forward.dot(wish) < .72
		):
			_prepare_steps("pivot", heading)
		var crossing_to_run := previous_command_speed < 1.7 and requested >= 1.7 and speed < 1.45
		var crossing_to_walk := previous_command_speed > 1.7 and requested <= 1.7 and speed > 1.85
		if (
			skeleton
			and special.is_empty()
			and previous_request
			and forward.dot(wish) > .60
			and (crossing_to_run or crossing_to_walk)
		):
			_prepare_steps("change_pace", heading)
		if special == "brake":
			releasing = true
		if special == "turn" and absf(angle_difference(final_heading, heading)) > .8:
			final_heading = heading
		if speed >= .08 and forward.dot(wish) < .91:
			# The fast field run steers through its stride. The short, planted
			# redirection belongs to the slower walk/run locomotion set.
			if not redirecting and special == "" and skeleton and top_speed != MAX_SPEED:
				_prepare_steps("turn", heading)
			redirecting = true
		var turn_speed := lerpf(PIVOT_TURN, MOVING_TURN, clampf(speed / top_speed, 0.0, 1.0))
		var running_turn := redirecting and top_speed == MAX_SPEED
		if special == "turn" or running_turn:
			turn_speed = redirect_rate
		if special == "pivot":
			turn_speed = 6.2
		if initial_hold > 0.0:
			initial_hold -= dt
		else:
			next_heading = rotate_toward(body.rotation.y, atan2(wish.x, wish.z), turn_speed * dt)
		forward = Vector3(sin(next_heading), 0.0, cos(next_heading))
		# Preserve running cadence through the turn. At a standing start the
		# body still pivots before carrying momentum into its first stride.
		if redirecting and forward.dot(wish) > .995:
			redirecting = false
		var turn_floor := 0.88 * smoothstep(1.15, 2.0, speed)
		if running_turn:
			turn_floor = .60
		elif special == "turn":
			turn_floor = .38
		requested *= lerpf(turn_floor, 1.0, smoothstep(-0.45, 0.85, forward.dot(wish)))
	if input.length() <= DEAD_ZONE and previous_request and previous_speed > .30 and skeleton:
		_prepare_steps("brake", body.rotation.y)
	previous_request = input.length() > DEAD_ZONE
	previous_command_speed = travel_speed
	speed = move_toward(speed, requested, (acceleration if requested > speed else braking) * dt)
	if requested <= .001:
		redirecting = false
	floor_pending = absf(previous_speed - speed) > .005
	if gait_tree:
		var scale_rate := 1.0
		if special in ["turn", "change_pace"]:
			var gait = world.character_kit.locomotion
			var hz: float = gait.stride_hz
			if hz > .12:
				var phase: float = (
					float(gait_tree.get("parameters/walk/current_position")) / gait.walk_length
				)
				var beats_left: int = (turn_beats if special == "turn" else 2) - 1 - beat
				var future_duration := .175 if special == "turn" else beat_duration
				var remaining := maxf(
					dt,
					(
						(ceilf(future_duration / dt) + 1.0) * dt * beats_left
						+ beat_duration
						- beat_time
					)
				)
				var err := wrapf(desired_touchdown - (phase + hz * remaining), -.5, .5)
				scale_rate = clampf(1.0 + err / maxf(.045, hz * remaining), .05, 2.55)
		gait_tree.set("parameters/transfer_speed/scale", scale_rate)
	if top_speed == MAX_SPEED:
		var steer_rate := angle_difference(body.rotation.y, next_heading) / maxf(dt, .00001)
		var lean_target := deg_to_rad(5.) * clampf(steer_rate / redirect_rate, -1., 1.) * smoothstep(1.4, 5., speed)
		field_turn_lean = lerpf(field_turn_lean, lean_target, 1. - exp(-15. * dt))
	body.rotation.y = next_heading
	body.velocity = forward * speed
	body.move_and_slide()
	world.constrain_private_snow_travel()
	var traveled := (body.global_position - start).slide(Vector3.UP)
	# A wall or the edge of the map can shorten a stride. Drive the gait from that result.
	return traveled.length() / maxf(dt, 0.00001)
