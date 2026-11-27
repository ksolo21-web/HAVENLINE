extends "res://tests/field_route.gd"

func photograph(output: String, shot: String, zoom_ratio: float) -> void:
	field.set_zoom_ratio(zoom_ratio)
	await process_frame
	RenderingServer.force_draw(false)
	root.get_texture().get_image().save_jpg(output.path_join(shot + ".jpg"), .94)

func run() -> void:
	var output := OS.get_environment("BELT_FILM")
	field = load("res://field_opening.tscn").instantiate()
	root.add_child(field)
	current_scene = field
	camera = field.camera
	origin = root.get_visible_rect().size * Vector2(.30, .68)
	await physics_frame
	var belts = field.settlement_loop.conveyors
	var snapshots := {}
	var reached := true
	for destination: Vector2 in [Vector2(2, -.8), Vector2(.8, -4.9)]:
		var arrived := false
		for i in 100:
			arrived = move_to([destination.x, destination.y], .18)
			await physics_frame
			if arrived:
				break
		reached = reached and arrived
	var house := field.depot.house.global_position as Vector3
	if not reached:
		push_warning("A photo route did not reach every intended viewpoint.")
	field.set_physics_process(false)
	await photograph(output, "yard-1x", 1.0)
	await photograph(output, "yard-2x", 2.0)
	var recorder := FileAccess.open(output.path_join("witness.json"), FileAccess.WRITE)
	recorder.store_string(JSON.stringify({"actor": pt(field.actor.global_position), "house":pt(house),
		"modules":belts.network.art.fitted.counts, "width":root.size.x,"height":root.size.y,
		"renderer":RenderingServer.get_video_adapter_name(),"reached":reached, "field_scene":field.scene_file_path}, "\t"))
	recorder.close()
	await preload("res://tests/lifecycle_test_profile.gd").drain_field_audio(self,field)
	field.queue_free()
	for i in 4:await process_frame
	quit(0)
