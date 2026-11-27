extends SceneTree
var game
var out:=OS.get_environment("MOTION_QUICK")
var records:=[]
var start:=Vector2(135,495)
func _initialize()->void:call_deferred("run")
func stick(active:bool,dr:=Vector2(90,-20))->void:
	var e:=InputEventScreenTouch.new();e.pressed=active;e.position=start;e.index=2;game._input(e)
	if active:
		var d:=InputEventScreenDrag.new();d.index=2;d.position=start+dr;game._input(d)
func run()->void:
	game=load("res://field_opening.tscn").instantiate();root.add_child(game);current_scene=game
	for i in 5:await physics_frame
	if game.persist_blocked or not game.field_ready:quit(2);return
	for zoom in [1,2]:
		if zoom==2:
			for k in ["wood","stone"]:
				for j in 6:game.inventory.collect("film-q-"+k+str(j),k)
			game.carry.sync(true)
		game.set_zoom_ratio(zoom)
		for choice in OS.get_environment("MOTION_BATCH").split(","):
			var n:=int(choice)
			if not game.set_player_character(n):quit(4);return
			stick(false);game.clear_touch();game.actor.velocity=Vector3.ZERO
			game.actor.position=Vector3(22,0,19);game.camera.position=game.actor.position+game.camera_follow_offset
			for i in 7:await physics_frame
			stick(true)
			for t in 64:
				if t==48:stick(true,Vector2(40,-80))
				await physics_frame
				if t%3==0:
					RenderingServer.force_draw(false,0.)
					var img:=root.get_texture().get_image()
					img.save_jpg(out.path_join("c%d-z%d-%03d.jpg"%[n,zoom,t]),.88)
					records.append({"tick":t,"role":game.player_character(),"zoom":zoom,"measured_speed":game.actor.velocity.length(),"pos":[game.actor.position.x,game.actor.position.y,game.actor.position.z],"visible_rig":str(game.player_wardrobe.target.get_path()),"bones":game.player_wardrobe.target.get_bone_count()})
			stick(false)
	var f:=FileAccess.open(out.path_join("camera-receipt.json"),FileAccess.WRITE);f.store_string(JSON.stringify(records));f.close()
	game.set_physics_process(false)
	await preload("res://tests/lifecycle_test_profile.gd").drain_field_audio(self,game)
	game.queue_free()
	for i in 4:await process_frame
	quit()
