extends SceneTree

const Session = preload("res://tests/lifecycle_test_profile.gd")
var world
var checks := {}
var speeds := {}
var movement := {}
var origin := Vector2(400, 400)

func _initialize() -> void:
	if not Session.isolated(self, "res://tests/qa_field_run_input.gd"):
		call_deferred("run")

func touch(pressed: bool) -> void:
	var event := InputEventScreenTouch.new()
	event.index = 5
	event.position = origin
	event.pressed = pressed
	world._input(event)

func measure(label: String, displacement: float) -> void:
	steer(Vector2(displacement, 0))
	for tick in 50: await physics_frame
	var speed: float = world.actor.velocity.length()
	var gait = world.character_kit.locomotion
	speeds[label] = speed
	if displacement <= 3.:
		checks[label] = speed < .01 and gait.current == "idle"
	else:
		checks[label] = absf(speed - 6.25) < .02 and gait.current == "run" and is_equal_approx(gait.gait_weight, 1.)

func local_joint(skeleton: Skeleton3D, joint: String) -> Vector3:
	var bone := skeleton.find_bone(joint)
	return world.actor.to_local(skeleton.to_global(skeleton.get_bone_global_pose(bone).origin))

# Align each measured gait cycle to the actual player's descending left boot.
# At 60 Hz a steady run spans ~33 frames, so each phase has finite precision.
func check_knee_sequence(clearances: Array[float], knee: Array[float], roll: Array[float]) -> void:
	var landings: Array[int] = []
	var raised := false
	for tick in clearances.size():
		if clearances[tick] > .05:
			raised = true
		elif raised and clearances[tick] < .008:
			raised = false
			landings.append(tick)
	var phases: Array = []
	var sequence_ok := landings.size() >= 2
	for step in range(1, landings.size()):
		var start := landings[step - 1]
		var ticks := landings[step] - start
		var load_window := knee.slice(start, start + roundi(.26 * ticks))
		var swing_window := knee.slice(start + roundi(.43 * ticks), start + roundi(.88 * ticks))
		var load_flex: float = load_window.max()
		var load_phase := float(load_window.find(load_flex)) / ticks
		var swing_flex: float = swing_window.max()
		var swing_phase := float(roundi(.43 * ticks) + swing_window.find(swing_flex)) / ticks
		var push: float = knee.slice(start + roundi(.24 * ticks), start + roundi(.38 * ticks)).min()
		var toe_roll: float = roll.slice(start + roundi(.16 * ticks), start + roundi(.33 * ticks)).max()
		var early_fold: float = knee[start + roundi(.40 * ticks)]
		var middle_fold: float = knee[start + roundi(.50 * ticks)]
		var trailing_fold: float = knee[start + roundi(.80 * ticks)]
		phases.append({"loaded_deg":load_flex, "loaded_cycle":load_phase, "push_deg":push,
			"recovery_deg":swing_flex, "recovery_cycle":swing_phase, "heel_above_toe_m":toe_roll,
			"knee_at_40_deg":early_fold, "knee_at_50_deg":middle_fold, "knee_at_80_deg":trailing_fold})
		sequence_ok = sequence_ok and load_flex > 30. and load_flex < 55. and load_phase >= .075 and load_phase <= .235
		sequence_ok = sequence_ok and push < 27. and push < load_flex - 12. and toe_roll > .012
		sequence_ok = sequence_ok and early_fold < 56. and middle_fold > early_fold + 12. and middle_fold < 91. and trailing_fold > 67.
		sequence_ok = sequence_ok and swing_flex > 95. and swing_flex < 135. and swing_phase >= .59 and swing_phase <= .79
	movement["measured_stride_phases"] = phases
	checks["knee yields under load, extends at toe-off, then folds during recovery"] = sequence_ok

func inspect_stride() -> void:
	var skeleton: Skeleton3D = world.gait_motor.skeleton
	var slips: Array[float] = []
	var min_foot := INF
	var max_foot := -INF
	var max_clearance := 0.0
	var min_surface := INF
	var flight_ticks := 0
	var flight_apex := 0.0
	var supported_ticks := 0
	var print_count := 0
	var highest_print_contact := 0.0
	var left_heights: Array[float] = []
	var left_knee: Array[float] = []
	var heel_toe_roll: Array[float] = []
	var sample_started: float = world.tracks.clock
	var foot_spreads: Array[float] = []
	var previous_depths := Vector2.ZERO
	var longest_still := 0
	var still_ticks := 0
	var lean_sum := 0.0
	var min_elbow_flex := INF
	var prev := PackedVector3Array()
	var rear := INF
	var forward := -INF
	var gait = world.character_kit.locomotion
	for tick in 90:
		await physics_frame
		var feet: PackedVector3Array = world.gait_motor._contacts()
		var lowest := INF
		var lifted_left := INF
		var heel := INF
		var toe := INF
		for i in feet.size():
			var height: float = feet[i].y - world.actor.global_position.y
			lowest = minf(lowest, height)
			if Vector3(world.gait_motor.samples[i][0]).x > 0:
				lifted_left = minf(lifted_left, height)
				var rest: Vector3 = world.gait_motor.samples[i][0]
				if rest.z < -.045: heel = minf(heel, height)
				if rest.z > .095: toe = minf(toe, height)
			if not prev.is_empty() and height < .008 and prev[i].y - world.actor.global_position.y < .008:
				slips.append((feet[i] - prev[i]).slide(Vector3.UP).length() * 60.)
		# Check only newly stamped player treads, while their skinned vertices
		# are still in this same physics pose. NPCs use paw impressions here.
		for chunk in world.tracks.chunks.values():
			for mark in chunk.marks:
				if mark.wolf or mark.time <= sample_started:
					continue
				var near_height := INF
				for point in feet:
					if (point - Vector3(mark.p)).slide(Vector3.UP).length() < .14:
						near_height = minf(near_height, point.y - world.actor.position.y)
				highest_print_contact = maxf(highest_print_contact,near_height)
				print_count += 1
		sample_started = world.tracks.clock
		min_surface = minf(min_surface,lowest)
		if lowest > .012: flight_ticks += 1
		if lowest < .008: supported_ticks += 1
		flight_apex = maxf(flight_apex,lowest)
		max_clearance = maxf(max_clearance, lifted_left)
		prev = feet
		var foot_z := local_joint(skeleton,"Foot.L").z
		var depths := Vector2(foot_z, local_joint(skeleton,"Foot.R").z)
		foot_spreads.append(absf(depths.x - depths.y))
		if tick > 0:
			var delta := (depths - previous_depths).abs() * Engine.physics_ticks_per_second
			still_ticks = still_ticks + 1 if maxf(delta.x, delta.y) < .45 else 0
			longest_still = maxi(longest_still, still_ticks)
		previous_depths = depths
		min_foot = minf(min_foot,foot_z)
		max_foot = maxf(max_foot,foot_z)
		var thigh := local_joint(skeleton,"Thigh.L")
		var shin := local_joint(skeleton,"Shin.L")
		var ankle := local_joint(skeleton,"Foot.L")
		left_knee.append(180.0-rad_to_deg((thigh-shin).angle_to(ankle-shin)))
		left_heights.append(lifted_left)
		heel_toe_roll.append(heel-toe)
		var hand := local_joint(skeleton,"Hand.L")
		var elbow := local_joint(skeleton,"Forearm.L")
		var shoulder := local_joint(skeleton,"UpperArm.L")
		min_elbow_flex = minf(min_elbow_flex, 180.0-rad_to_deg((shoulder-elbow).angle_to(hand-elbow)))
		var hand_z := hand.z
		rear = minf(rear,hand_z)
		forward = maxf(forward,hand_z)
		var trunk := local_joint(skeleton,"Neck")-local_joint(skeleton,"Pelvis")
		lean_sum += rad_to_deg(atan2(trunk.z,trunk.y))
	slips.sort()
	var median := INF if slips.is_empty() else slips[slips.size()/2]
	movement = {"world_speed":world.actor.velocity.length(),"steps_per_minute":gait.stride_hz*120,
		"boot_front_back_m":max_foot-min_foot,"swing_sole_clearance_m":max_clearance,
		"actual_print_count":print_count,"highest_print_contact_m":highest_print_contact,"simultaneous_flight_apex_m":flight_apex,"supported_ticks":supported_ticks,"minimum_sole_y_m":min_surface,"airborne_ticks":flight_ticks,"stance_median_slip_m_s":median,
		"hand_front_back_m":forward-rear,"min_elbow_flex_deg":min_elbow_flex,"forward_trunk_lean_deg":lean_sum/90.}
	var widest: float = foot_spreads.max()
	var split_ticks := 0
	var longest_split := 0
	for spread in foot_spreads:
		split_ticks = split_ticks + 1 if spread >= .85 * widest else 0
		longest_split = maxi(longest_split, split_ticks)
	check_knee_sequence(left_heights,left_knee,heel_toe_roll)
	movement["longest_broad_split_s"] = float(longest_split) / Engine.physics_ticks_per_second
	movement["longest_two_boot_hold_s"] = float(longest_still) / Engine.physics_ticks_per_second
	checks["boots keep moving through the airborne exchange"] = movement.longest_broad_split_s < .12 and longest_still <= 1
	checks["run has visible stride, recovery and flight"] = max_foot-min_foot>.70 and max_clearance>.075 and flight_ticks>=3
	checks["hands pump as body leans into run"] = min_elbow_flex>55. and forward-rear>.34 and lean_sum/90.>10.
	checks["each snow impression begins under a contacting boot"] = print_count >= 4 and highest_print_contact < .006
	checks["run loads the snow through both steps"] = supported_ticks >= 42 and flight_apex < .055 and flight_ticks <= 43
	checks["travel keeps the supported sole planted"] = min_surface>-.0025 and median<.15 and gait.stride_hz*120.>188. and gait.stride_hz*120.<229.

func steer(displacement: Vector2) -> void:
	var drag := InputEventScreenDrag.new()
	drag.index = 5
	drag.position = origin + displacement
	world._input(drag)

func ankle_pitch_range() -> Vector2:
	var rig: Skeleton3D = world.gait_motor.skeleton
	var span := Vector2(INF, -INF)
	for leg: Array in world.gait_motor.leg_chains:
		var lower_leg := rig.get_bone_global_pose(leg[1])
		var boot := rig.get_bone_global_pose(leg[2])
		var relative := (lower_leg.basis.inverse() * boot.basis).orthonormalized()
		var pitch := rad_to_deg(relative.get_euler(EULER_ORDER_ZYX).x)
		span.x = minf(span.x, pitch)
		span.y = maxf(span.y, pitch)
	return span

func inspect_turn_and_brake() -> void:
	Engine.physics_ticks_per_second = 120
	var turns_clear := true
	var stops_clear := true
	var lowest_sole := INF
	var min_turn_speed := INF
	var peak_bank := 0.0
	# Release on different phases of the stride, including both boot handoffs.
	for approach_ticks in [75, 84, 102, 138]:
		world.actor.global_position = Vector3(12., 0., 25.)
		world.actor.rotation.y = atan2(world.camera.global_basis.x.x, world.camera.global_basis.x.z)
		var approach_heading: float = world.actor.rotation.y
		touch(true)
		steer(Vector2(80., 0.))
		for tick in approach_ticks: await physics_frame
		steer(Vector2(0., 65.))
		for tick in 58:
			await physics_frame
			var pitch := ankle_pitch_range()
			turns_clear = turns_clear and pitch.x > -134. and pitch.y < -32.
			min_turn_speed = minf(min_turn_speed, world.actor.velocity.length())
			peak_bank = maxf(peak_bank, absf(world.gait_motor.field_turn_lean))
		turns_clear = turns_clear and absf(angle_difference(world.actor.rotation.y, approach_heading)) > deg_to_rad(85.)
		var released_at: Vector3 = world.actor.global_position
		touch(false)
		for tick in 100:
			await physics_frame
			var pitch := ankle_pitch_range()
			stops_clear = stops_clear and pitch.x > -134. and pitch.y < -32.
			var soles: Vector2 = world.gait_motor._heights()
			lowest_sole = minf(lowest_sole, minf(soles.x, soles.y) - world.actor.position.y)
		stops_clear = stops_clear and released_at.distance_to(world.actor.position) < .48
	movement["turn_and_brake_minimum_sole_m"] = lowest_sole
	movement["minimum_quarter_turn_speed_m_s"] = min_turn_speed
	movement["maximum_quarter_turn_lean_deg"] = rad_to_deg(peak_bank)
	checks["body leans into a moving turn and retains running speed"] = min_turn_speed > 4. and peak_bank > deg_to_rad(2.) and peak_bank < deg_to_rad(7.)
	checks["both boots stay within their measured pitch through quarter turns"] = turns_clear
	checks["both boots settle above the snow at multiple release phases"] = stops_clear and lowest_sole > -.0025

func run() -> void:
	world = load("res://field_opening.tscn").instantiate()
	root.add_child(world)
	await physics_frame
	# A clear stretch of the snowfield keeps obstacles and NPCs out of this input regression.
	world.actor.global_position = Vector3(30., 0., 26.)
	world.actor.rotation.y = atan2(world.camera.global_basis.x.x, world.camera.global_basis.x.z)
	touch(true)
	await measure("touch jitter stays idle", 3.)
	await measure("short drag runs", 12.)
	await measure("full drag runs", 82.)
	# Measure a complete steady cycle along the second clear centerline.
	world.actor.global_position = Vector3(26.,0.,24.)
	await inspect_stride()
	var released_at: Vector3 = world.actor.position
	touch(false)
	for tick in 65: await physics_frame
	movement["braking_distance_m"] = released_at.distance_to(world.actor.position)
	checks["release stops within half a metre"] = movement.braking_distance_m < .48
	checks["release comes to rest"] = world.actor.velocity.length() < .01 and world.character_kit.locomotion.current == "idle"
	await inspect_turn_and_brake()
	print("FIELD_RUN ", JSON.stringify({"checks":checks, "speeds_m_s":speeds,"motion":movement}))
	await Session.drain_field_audio(self,world)
	world.queue_free()
	for tick in 3: await process_frame
	quit(int(checks.values().has(false)))
