extends SceneTree
var folder := OS.get_environment("TOWER_OUTPUT")
func _initialize()->void: call_deferred("go")
func go()->void:
	var profile = preload("res://tests/lifecycle_test_profile.gd").Profile.new()
	if not profile.configure(OS.get_cmdline_user_args()):
		quit(2)
		return
	var game=load("res://field_opening.tscn").instantiate()
	root.add_child(game)
	current_scene=game
	for i in 8:await physics_frame
	var tower=game.defense_tower
	if not tower.active or game.persist_blocked:
		quit(2)
		return
	for w in game.enemies:w.active=false
	var outside:Vector3=tower.position+Vector3(4.35,0,.90)
	game.encounters._add(outside,false,990,outside)
	game.actor.global_position=tower.position+Vector3(-1.60,0.,-.97)
	game.camera.position=game.actor.global_position+game.camera_follow_offset
	var start:Vector3=game.actor.position
	var touch:=InputEventScreenTouch.new()
	touch.index=6
	touch.position=Vector2(300,640)
	touch.pressed=true
	game._input(touch)
	var drag:=InputEventScreenDrag.new()
	drag.index=6
	drag.position=touch.position+Vector2(-18.,26.)
	game._input(drag)
	for i in 8:await physics_frame
	touch.pressed=false
	game._input(touch)
	game.set_zoom_ratio(2.)
	for i in 4:await physics_frame
	RenderingServer.force_draw(false)
	var result:=root.get_texture().get_image()
	result.save_jpg(folder.path_join("Gameplay-2x-interior.jpg"),.97)
	var f:=FileAccess.open(folder.path_join("Pinch.json"),FileAccess.WRITE)
	f.store_string(JSON.stringify({"global_pos":str(game.actor.global_position),"input_distance_m":game.actor.global_position.distance_to(start),"station_screen":str(game.camera.unproject_position(tower.art.swivel.global_position)),"viewport":str(root.get_visible_rect()),"size":str(result.get_size())},"  ")+"\n")
	f.close()
	await preload("res://tests/lifecycle_test_profile.gd").drain_field_audio(self,game)
	game.queue_free()
	for i in 5:await process_frame
	quit()
