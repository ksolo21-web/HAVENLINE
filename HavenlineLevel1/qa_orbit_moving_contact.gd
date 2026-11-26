extends SceneTree
const Opening = preload("res://orbit_opening.tscn")
func _initialize() -> void:
	var hz := OS.get_environment("HAVENLINE_ORBIT_TEST_HZ").to_int()
	if hz in [30,60,120]: Engine.physics_ticks_per_second = hz
	call_deferred("run")

func run() -> void:
	var success := true
	for scenario: String in ["walk", "run"]:
		var world = Opening.instantiate()
		root.add_child(world)
		await physics_frame
		var target: Node3D = world.resource_tree if scenario == "walk" else world.resource_rock
		var radius := 2.61
		world.actor.global_position = target.global_position + Vector3.RIGHT * radius
		var origin := Vector2(62,610)
		var touch := InputEventScreenTouch.new()
		touch.index=0
		touch.position=origin
		touch.pressed=true
		world._input(touch)
		var matches := 0
		for i in range(Engine.physics_ticks_per_second * 12):
			var radial: Vector3 = world.actor.global_position-target.global_position
			radial.y=0
			var tangent := Vector3.UP.cross(radial.normalized())
			var correction := (radius-radial.length())*6.0
			var steer := (tangent*(1.38 if scenario=="walk" else 3.45) + radial.normalized()*correction).rotated(Vector3.UP,-atan2(7.,11.))
			var drag := InputEventScreenDrag.new()
			drag.index=0
			drag.position = origin + Vector2(steer.x,steer.z)*82./4.
			world._input(drag)
			await physics_frame
			if world.character_kit.locomotion.current==scenario and world.character_kit.active: matches+=1
			if target.strikes==3: break
		print(Engine.physics_ticks_per_second,"Hz ",scenario," moving contacts=",target.strikes," matching movement samples=",matches)
		success=success and target.strikes==3 and matches>10
		world.queue_free()
		await process_frame
	quit(0 if success else 1)
