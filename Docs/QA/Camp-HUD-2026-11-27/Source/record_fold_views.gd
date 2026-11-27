extends SceneTree
## Capture the same paid camp before and after a desktop window geometry change.
## The framebuffer size models the handset displays; this does not profile its GPU.
var folder := OS.get_environment("HAVENLINE_DISPLAY_OUT")

func _initialize() -> void:
	call_deferred("capture")

func capture() -> void:
	var world = load("res://field_opening.tscn").instantiate()
	root.add_child(world)
	current_scene = world
	for i in 6:
		await physics_frame
	if not world.camp_active or world.persist_blocked:
		quit(2)
		return
	world.actor.position = Vector3(.4, 0, -3.65)
	world.camera.position = world.actor.position + world.camera_follow_offset
	world.graphics.set_ultra(true)
	var views := {"Cover":Vector2i(1080,2520), "Inner":Vector2i(1968,2184), "Cover-reopened":Vector2i(1080,2520)}
	var rows := {}
	var successful := true
	for view in views:
		root.size=views[view]
		for frame in 12:
			await process_frame
		world.set_zoom_ratio(1.)
		for frame in 5:
			await physics_frame
		RenderingServer.force_draw(false, 1./60.)
		var photo := root.get_texture().get_image()
		photo.save_jpg(folder.path_join(view+".jpg"), .93)
		var world_rect := root.get_visible_rect()
		var projected: Vector2 = world.camera.unproject_position(world.actor.global_position)
		var full_frame: bool = photo.get_size()==views[view] and world_rect.has_point(projected)
		successful = successful and full_frame and world.graphics.ultra and is_equal_approx(root.scaling_3d_scale,1.)
		rows[view]={"width":photo.get_width(),"height":photo.get_height(),"camera_size":world.camera.size,"game_view":str(world_rect),"player_projection":str(projected),"player_in_frame":world_rect.has_point(projected),"render_scale":root.scaling_3d_scale,"device":"Desktop Godot with simulated Fold7 display dimensions","adapter":RenderingServer.get_video_adapter_name()}
	var receipt := FileAccess.open(folder.path_join("Geometry.json"),FileAccess.WRITE)
	receipt.store_string(JSON.stringify(rows,"  ")+"\n")
	receipt.close()
	await preload("res://tests/lifecycle_test_profile.gd").drain_field_audio(self,world)
	world.queue_free()
	for frame in 4:
		await process_frame
	quit(0 if successful else 3)
