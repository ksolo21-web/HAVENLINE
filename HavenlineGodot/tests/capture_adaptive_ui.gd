extends SceneTree
const Main = preload("res://scripts/main.gd")
func _initialize(): call_deferred("run")
func run():
	var destination := "user://adaptive-ui-captures"
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--output="): destination=argument.trim_prefix("--output=")
	DirAccess.make_dir_recursive_absolute(destination)
	var game := Main.new()
	game.qa_mode=true;game.render_review=true;game.capture_frames=100
	game.capture_directory=destination
	root.add_child(game)
	game.set_process(false);game.set_physics_process(false)
	game.scene_view.render_target_update_mode=SubViewport.UPDATE_DISABLED
	# Isolate actual menu nodes for layout evidence; not environment art evidence.
	game.paused=true;game.menu.visible=true
	game.qa_mode=false;game.rebuild_menu();game.qa_mode=true
	for fixture in [["phone-layout", Vector2i(640,360)],["tablet-layout",Vector2i(960,720)]]:
		root.content_scale_size=fixture[1]
		root.size=fixture[1]
		game.size=fixture[1]
		game.apply_hud_layout(Rect2(Vector2(12,12),Vector2(fixture[1])-Vector2(24,24)),1.0)
		for i in 6: await process_frame
		await RenderingServer.frame_post_draw
		root.get_texture().get_image().save_png(destination+"/"+fixture[0]+".png")
	game.outpost_audio.stop_all()
	await create_timer(.35).timeout
	game.free()
	await process_frame
	print("Actual UI-only layout captures; NOT physical Android or environment quality approval.")
	quit()
