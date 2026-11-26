extends SceneTree

const Session = preload("res://tests/lifecycle_test_profile.gd")
var world
var checks := {}
var speeds := {}
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
	var drag := InputEventScreenDrag.new()
	drag.index = 5
	drag.position = origin + Vector2(displacement, 0)
	world._input(drag)
	for tick in 50: await physics_frame
	var speed: float = world.actor.velocity.length()
	var gait = world.character_kit.locomotion
	speeds[label] = speed
	if displacement <= 3.:
		checks[label] = speed < .01 and gait.current == "idle"
	else:
		checks[label] = absf(speed - world.gait_motor.MAX_SPEED) < .02 and gait.current == "run" and is_equal_approx(gait.gait_weight, 1.)

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
	touch(false)
	for tick in 65: await physics_frame
	checks["release comes to rest"] = world.actor.velocity.length() < .01 and world.character_kit.locomotion.current == "idle"
	print("FIELD_RUN ", JSON.stringify({"checks":checks, "speeds_m_s":speeds}))
	await Session.drain_field_audio(self,world)
	world.queue_free()
	for tick in 3: await process_frame
	quit(int(checks.values().has(false)))
