extends SceneTree
## Validate the exact visible character in the live field, then drive both
## actor roles through complete body clips using the same presentation API.
const Session = preload("res://tests/lifecycle_test_profile.gd")
const Motion = preload("res://field_character_motion.gd")
const Delta := 1. / 120.
var world
var checks := {}
var metrics := {}
var pose_times: Array[int] = []

func _initialize() -> void:
	if not Session.isolated(self, "res://tests/qa_t06_character_motion.gd"):
		call_deferred("run")

func drive(point: Vector2, strength: Vector2) -> void:
	var event := InputEventScreenDrag.new()
	event.index = 5
	event.position = point + strength * 82.
	world._input(event)

func start_motion() -> void:
	var origin := root.get_visible_rect().size * Vector2(.16, .72)
	world.actor.global_position = Vector3(30.,0.,26.)
	world.actor.rotation.y = atan2(world.camera.global_basis.x.x, world.camera.global_basis.x.z)
	world.previous_dry_position = world.actor.global_position
	for tick in 12: await physics_frame
	var press := InputEventScreenTouch.new()
	press.index = 5
	press.position = origin
	press.pressed = true
	world._input(press)
	var previous: PackedVector3Array = world.gait_motor._contacts()
	var largest_jump := 0.
	var takeoff := false
	var start: Vector3 = world.actor.global_position
	drive(origin, Vector2.RIGHT)
	for tick in 30:
		await physics_frame
		var points: PackedVector3Array = world.gait_motor._contacts()
		if tick < 5:
			for i in points.size():
				if points[i].y < .012 and previous[i].y < .012:
					largest_jump = maxf(largest_jump, points[i].distance_to(previous[i]))
		var soles: Vector2 = world.gait_motor._heights()
		if tick < 19 and absf(soles.x - soles.y) >= .032: takeoff = true
		previous = points
	checks.launch_with_takeoff = takeoff
	checks.launch_support_continuity = largest_jump < .036
	checks.launch_still_moves = start.distance_to(world.actor.global_position) >= .66
	metrics.launch_max_ground_point_m_per_tick = largest_jump
	metrics.launch_distance_m = start.distance_to(world.actor.global_position)
	drive(origin, Vector2.ZERO)
	for tick in 104: await physics_frame
	world.clear_touch()

func test_action(motion: RefCounted, key: StringName) -> void:
	var bone_state: Array[Quaternion] = []
	for bone in motion.rig.get_bone_count():
		bone_state.append(motion.rig.get_bone_pose_rotation(bone))
	var spec: Array = Motion.CLIPS[key]
	var at: Vector3 = world.actor.global_position + world.actor.global_basis.z
	var source: Vector3 = world.actor.global_position
	var baseline: Dictionary = motion.sockets()
	var feet: PackedVector3Array = world.gait_motor._contacts()
	var cuffs := {}
	for joint: int in world.gait_motor.boot_cuffs: cuffs[joint] = motion.rig.get_bone_global_pose(joint)
	var sample_count := ceili(float(spec[0]) / Delta)
	var normalized := PackedFloat32Array([0., float(spec[1]), float(spec[2]), float(spec[3]), 1.])
	for tick in range(1, sample_count): normalized.append(float(tick) / sample_count)
	normalized.sort()
	var peak_reach := 0.
	var step_reach := 0.
	var foot_error := 0.
	var cuff_error := 0.
	var left_right_clearance := INF
	var role_ok := true
	var distances := {}
	var previous := baseline
	for phase in normalized:
		var lead := Motion.select(0., world.actor.rotation.y, world.actor.rotation.y, key, phase, Motion.LEAD)
		var companion := Motion.select(0., world.actor.rotation.y, world.actor.rotation.y, key, phase, Motion.COMPANION)
		role_ok = role_ok and lead == companion and lead.socket == spec[4] and lead.contact == spec[2]
		var started := Time.get_ticks_usec()
		motion.pose(lead, 1., at)
		pose_times.append(Time.get_ticks_usec() - started)
		var palms: Dictionary = motion.sockets()
		left_right_clearance = minf(left_right_clearance, (palms.left_hand as Vector3).distance_to(palms.right_hand))
		for side in ["left_hand", "right_hand"]:
			peak_reach = maxf(peak_reach, (palms[side] as Vector3).distance_to(baseline[side]))
			step_reach = maxf(step_reach, (palms[side] as Vector3).distance_to(previous[side]))
		if absf(phase - float(spec[2])) < .00001:
			var contact: Vector3 = world.actor.to_local(palms[spec[4]])
			distances = {"contact_local": [contact.x, contact.y, contact.z], "contact_phase": spec[2], "socket": spec[4]}
		var surface: PackedVector3Array = world.gait_motor._contacts()
		for i in surface.size(): foot_error = maxf(foot_error, surface[i].distance_to(feet[i]))
		for joint: int in cuffs:
			var original: Transform3D = cuffs[joint]
			var rendered: Transform3D = motion.rig.get_bone_global_pose(joint)
			cuff_error = maxf(cuff_error, original.origin.distance_to(rendered.origin))
		previous = palms
		motion.clear_pose()
	checks[String(key) + "_two_roles"] = role_ok
	checks[String(key) + "_readable_grounded_work"] = peak_reach > .11 and foot_error < .0001 and cuff_error < .0001 and left_right_clearance > .06 and world.actor.global_position == source
	var restored: Dictionary = motion.sockets()
	checks[String(key) + "_continuous_recovery"] = step_reach < .065 and (restored.left_hand as Vector3).is_equal_approx(baseline.left_hand) and (restored.right_hand as Vector3).is_equal_approx(baseline.right_hand)
	for bone in bone_state.size():
		checks[String(key) + "_continuous_recovery"] = checks[String(key) + "_continuous_recovery"] and bone_state[bone].is_equal_approx(motion.rig.get_bone_pose_rotation(bone))
	distances.merge({"max_hand_motion_m": peak_reach, "largest_per_tick_m": step_reach, "min_palm_gap_m": left_right_clearance, "max_boot_error_m": foot_error, "max_cuff_error_m": cuff_error})
	metrics[key] = distances

func test_grade(label: String, grade: Vector2, running: bool) -> void:
	var gait = world.character_kit.locomotion
	var motor = world.gait_motor
	gait.run_only = running
	motor.special = ""
	motor.bridge = false
	motor.previous_request = false
	motor.previous_command_speed = 0.
	motor.launch_remaining = 0.
	motor.ground_grade = grade
	# The gameplay snow is flat. Supply the fixture plane instead of bumping
	# into the level's flat physics when the downhill case goes below it.
	var collision_mask: int = world.actor.collision_mask
	world.actor.collision_mask = 0
	world.actor.global_position = Vector3(30., 0., 26.)
	world.actor.velocity = Vector3.ZERO
	world.previous_dry_position = world.actor.global_position
	world.actor.rotation.y = atan2(world.camera.global_basis.x.x, world.camera.global_basis.x.z)
	gait.observe(0., true, Delta)
	var plane_origin: Vector3 = world.actor.global_position
	var pace := 1. if running else .208
	var highs := Vector2.ZERO
	var lows := Vector2(INF, INF)
	var both_track := true
	var desired := "run" if running else "walk"
	var step_count := 0
	for tick in 310:
		await physics_frame
		world.previous_dry_position = world.actor.global_position
		var speed: float = motor.step(world, Vector2(pace, 0.), Delta, 0., grade)
		var delta: Vector3 = world.actor.global_position - plane_origin
		world.actor.position.y = grade.dot(Vector2(delta.x, delta.z))
		gait.observe(speed, true, Delta)
		if tick < 65: continue
		var clearance: Vector2 = motor._heights() - Vector2.ONE * world.actor.global_position.y
		lows = lows.min(clearance)
		highs = highs.max(clearance)
		both_track = both_track and gait.current == desired
		step_count += int(minf(clearance.x, clearance.y) < .009)
	checks[label] = both_track and minf(lows.x, lows.y) >= -.0025 and maxf(lows.x, lows.y) < .007 and minf(highs.x, highs.y) > .030 and step_count > 30
	metrics[label] = {"grade": [grade.x, grade.y], "min_m": [lows.x, lows.y], "swing_m": [highs.x, highs.y], "supported_samples": step_count}
	world.actor.collision_mask = collision_mask

func run() -> void:
	Engine.physics_ticks_per_second = 120
	world = load("res://field_opening.tscn").instantiate()
	root.add_child(world)
	current_scene = world
	await physics_frame
	for foe in world.enemies.duplicate(): world.encounters._remove(foe)
	world.encounters.remaining = 120.
	await start_motion()
	world.set_physics_process(false)
	var motion: RefCounted = world.character_motion
	motion.cancel()
	checks.frozen_character_source = FileAccess.get_sha256("res://assets/characters/Character1Fresh.glb") == Motion.MODEL_SHA256
	checks.bilateral_sockets = motion.sockets().size() == 6
	checks.idle_walk_run_api = Motion.select(0., 0., 0., &"", 0., Motion.LEAD).action == &"idle" and Motion.select(1.12, 0., 0., &"", 0., Motion.COMPANION).action == &"walk" and Motion.select(6.25, 0., 0., &"", 0., Motion.LEAD).action == &"run"
	for angle in [-179, -90, -30, 30, 90, 179]:
		var state := Motion.select(2., deg_to_rad(10.), deg_to_rad(10. + angle), &"", 0., Motion.LEAD)
		checks["turn_" + str(angle)] = absf(state.turn - absf(angle)) <= 1. and state.side == signf(angle)
	for key: StringName in Motion.CLIPS:
		test_action(motion, key)
	var state: Dictionary = world.inventory.snapshot()
	var receipts: int = world.events.size()
	var at: Vector3 = world.actor.global_position + world.actor.global_basis.z
	world.present_character_contact(&"chop", at)
	var aligned := is_equal_approx(motion.seconds, float(Motion.CLIPS.chop[0]) * float(Motion.CLIPS.chop[2]))
	var advances := true
	for tick in 180:
		motion.clear_pose()
		var elapsed: float = motion.seconds
		if tick == 2: world.present_character_contact(&"chop", at)
		motion.advance(Delta, 0., false)
		advances = advances and motion.seconds >= elapsed
	checks.one_shot_matches_receipt_and_recovers = aligned and advances and motion.action == &"" and motion.original_rotations.is_empty()
	motion.contact(&"deposit", at)
	for tick in 14:
		motion.clear_pose()
		motion.advance(Delta, 0., false)
	var before: Vector3 = motion.sockets().right_hand
	motion.clear_pose()
	motion.contact(&"build", at)
	var biggest := 0.
	for tick in 20:
		motion.clear_pose()
		motion.advance(Delta, 0., false)
		var hand: Vector3 = motion.sockets().right_hand
		biggest = maxf(biggest, hand.distance_to(before))
		before = hand
	checks.deposit_to_build_blends = biggest < .080 and motion.previous_action.is_empty()
	metrics.deposit_to_build_max_hand_delta_m = biggest
	motion.cancel()
	checks.motion_cannot_award_or_save = state == world.inventory.snapshot() and receipts == world.events.size()
	pose_times.sort()
	metrics.pose_samples = pose_times.size()
	metrics.pose_cpu_p95_us = pose_times[floori(.95 * (pose_times.size() - 1))]
	await test_grade("walk_level", Vector2.ZERO, false)
	await test_grade("walk_grade", Vector2(.10,.04), false)
	await test_grade("run_grade", Vector2(-.10,-.04), true)
	print(JSON.stringify({"checks": checks, "metrics": metrics}))
	await Session.drain_field_audio(self,world)
	world.queue_free()
	await process_frame
	quit(0 if not checks.values().has(false) else 1)
