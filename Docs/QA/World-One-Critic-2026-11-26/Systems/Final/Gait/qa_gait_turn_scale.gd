extends SceneTree
## Repeated redirects may expose scale drift from world-space leg IK.
const TICKS := 5600
const SCALE_TOLERANCE := .001

func _initialize() -> void:
	call_deferred("run")

func run() -> void:
	var profile_guard = preload("res://field_save.gd").new()
	var arguments := OS.get_cmdline_user_args()
	if not profile_guard.requested(arguments) or not profile_guard.configure(arguments):
		printerr("The gait test requires a marked disposable profile.")
		quit(2)
		return
	var world = load("res://field_opening.tscn").instantiate()
	root.add_child(world)
	while not world.gait_motor.skeleton:
		await physics_frame
	world.actor.position = Vector3(55, 0, 55)
	var touch := InputEventScreenTouch.new()
	touch.index = 5
	touch.position = Vector2(80, 620)
	touch.pressed = true
	world._input(touch)
	var rng := RandomNumberGenerator.new()
	rng.seed = 146835
	var next_steer := 0
	var skeleton: Skeleton3D = world.gait_motor.skeleton
	var min_scale := 1.0
	var max_scale := 1.0
	var failed_tick := -1
	var failed_bone := ""
	for tick in TICKS:
		if tick == next_steer:
			var drag := InputEventScreenDrag.new()
			drag.index = touch.index
			var heading := rng.randf_range(-PI, PI)
			drag.position = touch.position + Vector2.RIGHT.rotated(heading) * rng.randf_range(32, 82)
			world._input(drag)
			next_steer += rng.randi_range(10, 48)
		await physics_frame
		for leg in world.gait_motor.leg_chains:
			for index: int in leg:
				var scale := skeleton.get_bone_pose_scale(index)
				min_scale = minf(min_scale, minf(scale.x, minf(scale.y, scale.z)))
				max_scale = maxf(max_scale, maxf(scale.x, maxf(scale.y, scale.z)))
				if failed_tick < 0 and (not scale.is_finite() or min_scale < 1.0-SCALE_TOLERANCE or max_scale > 1.0+SCALE_TOLERANCE):
					failed_tick = tick
					failed_bone = skeleton.get_bone_name(index)
	var passed := failed_tick < 0
	print(JSON.stringify({"passed":passed, "physics_ticks":TICKS, "min_scale":min_scale, "max_scale":max_scale, "first_bad_tick":failed_tick, "first_bad_bone":failed_bone}))
	world.sound.stop_playback()
	world.queue_free()
	for i in 8:
		await process_frame
	quit(0 if passed else 1)
