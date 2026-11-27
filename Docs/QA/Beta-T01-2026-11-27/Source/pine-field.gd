extends SceneTree
var out := OS.get_environment("T01_MESHY_OUT")
var game: Node3D
func _initialize() -> void:
	run.call_deferred()
func capture(name_: String, ratio: float) -> void:
	game.set_zoom_ratio(ratio)
	await process_frame
	await process_frame
	RenderingServer.force_draw(false,1.0/60.0)
	root.get_texture().get_image().save_jpg(out.path_join(name_+"-%dx.jpg"%int(ratio)),.92)
func run() -> void:
	root.size = Vector2i(460,760)
	game = load("res://field_opening.tscn").instantiate()
	root.add_child(game)
	current_scene=game
	for i in 5: await process_frame
	game.set_physics_process(false)
	game.set_process(false)
	game.actor.global_position = Vector3(-13.2,0,13.5)
	game.camera.global_position = game.actor.position + game.camera_follow_offset
	game.forest.advance(.25)
	var at := Vector3(-14.4,0,11.2)
	var original: Node3D
	for tree: Node3D in game.trees:
		if tree.global_position.distance_to(at)<.05:
			original=tree
			break
	if not original:quit(2);return
	for ratio in [1.,2.]: await capture("In-field-authored",ratio)
	var importer := GLTFDocument.new()
	var state := GLTFState.new()
	if importer.append_from_file(out.path_join("Forest-pine.glb"),state)!=OK:
		quit(3)
		return
	var model := importer.generate_scene(state) as Node3D
	game.add_child(model)
	var bounds := AABB()
	for part: MeshInstance3D in model.find_children("*","MeshInstance3D",true,false):
		var box := part.global_transform * part.get_aabb()
		if bounds.has_volume(): bounds=bounds.merge(box)
		else: bounds=box
	var scale_:float=original.crown_size.y*original.TREE_SCALE*original.scale.y / bounds.size.y
	model.scale=Vector3.ONE*scale_
	var center := bounds.get_center()*scale_
	model.global_position=at-Vector3(center.x,bounds.position.y*scale_,center.z)
	original.hide()
	for ratio in [1.,2.]: await capture("In-field-Meshy",ratio)
	game.sound.stop_playback()
	quit()
