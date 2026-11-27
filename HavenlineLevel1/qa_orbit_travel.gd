extends SceneTree
const Opening = preload("res://orbit_opening.tscn")
const Orbit = preload("res://weapon_orbit.gd")
var world
var output := OS.get_environment("HAVENLINE_ORBIT_TRAVEL")
var frame := 0
var measurements := {}
var max_delta := 0.0
var last_tip := Vector3.ZERO
var failures: Array[String] = []

func _initialize() -> void: call_deferred("run")

func move_input(stick: Vector2) -> void:
	var drag := InputEventScreenDrag.new()
	drag.index = 0
	drag.position = Vector2(82,620) + stick * 82.0
	world._input(drag)

func take_segment(state: String, stick: Vector2, ticks: int) -> void:
	move_input(stick)
	var start: Vector3 = world.actor.global_position
	var matched := 0
	var settled_mismatches := 0
	var expected_gait := "idle" if state=="upgraded" else state
	var angles := []
	for i in ticks:
		await process_frame
		if DisplayServer.get_name() != "headless":
			await RenderingServer.frame_post_draw
		var kit = world.character_kit
		var correct: bool = kit.locomotion.current == expected_gait and kit.active and kit.count==(10 if state=="upgraded" else 1)
		if correct: matched += 1
		if i >= 32 and not correct: settled_mismatches += 1
		var tip: Vector3 = kit.current_tip
		var local_tip: Vector3 = tip - world.actor.global_position
		angles.append(atan2(local_tip.x,local_tip.z))
		if frame > 0:
			var delta := tip.distance_to(last_tip)
			max_delta = maxf(max_delta,delta)
			# Preserve the old allowance and add only the arc travel due to
			# the higher rotation rate at the same 60 Hz sampling interval.
			var extra_speed := maxf(0.0,1.0 / kit.duration - 1.0 / Orbit.PERIOD)
			var allowed := .48 + float(kit.maximum_radius()) * TAU * extra_speed / 60.0
			if delta > allowed and "discontinuous tool path" not in failures:
				failures.append("discontinuous tool path")
		last_tip = tip
		if DisplayServer.get_name() != "headless":
			root.get_texture().get_image().save_jpg(output.path_join("%04d.jpg"%frame),.94)
		frame += 1
	var total := 0.0
	for i in range(1,angles.size()):
		total += wrapf(angles[i]-angles[i-1],-PI,PI)
	var dist: float = world.actor.global_position.distance_to(start)
	measurements[state] = {"frames":ticks,"mismatches_after_allowed_turn_and_brake":settled_mismatches,"matching_state_and_visible_orbit":matched,"travel_m":dist,"degrees":rad_to_deg(total)}
	if settled_mismatches != 0 or total <= TAU: failures.append(state)
	if state in ["walk","run"] and dist < .75: failures.append(state+" distance")

func run() -> void:
	DirAccess.make_dir_recursive_absolute(output)
	world = Opening.instantiate()
	root.add_child(world)
	await process_frame
	world.actor.global_position = Vector3(8,0,4)
	world.camera.global_position=world.actor.global_position+Vector3(7,11,11)
	var press := InputEventScreenTouch.new()
	press.index=0
	press.position=Vector2(82,620)
	press.pressed=true
	world._input(press)
	await take_segment("idle",Vector2.ZERO,73)
	await take_segment("walk",Vector2(.42,0),75)
	await take_segment("run",Vector2(-.90,.14),85)
	world.character_kit.set_upgraded(true)
	await take_segment("upgraded",Vector2.ZERO,100)
	var out := FileAccess.open(output.path_join("travel.json"),FileAccess.WRITE)
	out.store_string(JSON.stringify({"states":measurements,"maximum_interframe_tip_displacement_m":max_delta,"failures":failures},"  "))
	out.close()
	print("Orbit travel ",measurements," failures ",failures)
	quit(0 if failures.is_empty() else 1)
