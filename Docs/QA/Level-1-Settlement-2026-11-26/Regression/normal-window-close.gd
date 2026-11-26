extends SceneTree
func _initialize():
	call_deferred("run")
func run():
	change_scene_to_file(ProjectSettings.get_setting("application/run/main_scene"))
	await scene_changed
	for i in 140: await physics_frame
	var world=current_scene
	var guard=preload("res://opening_save.gd").new()
	if not guard.configure(OS.get_cmdline_user_args()) or world.field_save.directory!=guard._dir:
		printerr("bad guarded profile")
		quit(1)
		return
	print("Normal window close on live ", world.scene_file_path, " after 140 physics frames")
	root.close_requested.emit()
