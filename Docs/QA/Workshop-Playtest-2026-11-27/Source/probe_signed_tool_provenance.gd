extends SceneTree

func _initialize() -> void:
	run.call_deferred()

func run() -> void:
	var world = load("res://field_opening.tscn").instantiate()
	root.add_child(world)
	for tick in 5: await physics_frame
	var human: Node3D = world.survivor.actor
	var paths := {
		"axe": String(human.tool.scene_file_path),
		"pickaxe": String(human.mining_tool.scene_file_path)
	}
	var passed:bool = not world.persist_blocked and paths.axe=="res://assets/tools/axe-field-grip.glb" and paths.pickaxe=="res://assets/tools/pickaxe-meshy.glb"
	print("WORKER_TOOL_ASSETS ",JSON.stringify({"passes":passed,"paths":paths}))
	world.set_physics_process(false)
	world.carry.set_physics_process(false)
	world.sound.stop_playback()
	for tick in 12:
		OS.delay_msec(20)
		await process_frame
	world.queue_free()
	for tick in 3: await process_frame
	quit(0 if passed else 1)
