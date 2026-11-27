extends SceneTree

var folder := OS.get_environment("TOWER_OUTPUT")
var rows := {}
var capture := DisplayServer.get_name() != "headless"
func _initialize() -> void:call_deferred("go")
func picture(name_: String) -> void:
	if not capture:return
	RenderingServer.force_draw(false)
	root.get_texture().get_image().save_jpg(folder.path_join(name_+".jpg"),.95)
func go() -> void:
	var profile = preload("res://tests/lifecycle_test_profile.gd").Profile.new()
	if not profile.configure(OS.get_cmdline_user_args()):
		quit(2)
		return
	var world=load("res://field_opening.tscn").instantiate()
	root.add_child(world)
	current_scene=world
	for i in 8:await physics_frame
	var tower=world.defense_tower
	if not tower.active or world.persist_blocked:
		quit(2)
		return
	var aim_point:Vector3 = tower.global_position+Vector3(4.35,0.,.90)
	world.actor.global_position = tower.global_position+Vector3(1.28,0.,1.48)
	world.camera.position = world.actor.global_position+world.camera_follow_offset
	# A native joystick nudge at the gate, then the operator engages unassisted.
	var touch := InputEventScreenTouch.new()
	touch.index = 6
	touch.position = Vector2(300,640)
	touch.pressed = true
	world._input(touch)
	var drag := InputEventScreenDrag.new()
	drag.index = 6
	drag.position = touch.position+Vector2(8.,28.)
	world._input(drag)
	var movement_start:Vector3 = world.actor.position
	for i in 8:await physics_frame
	touch.pressed=false
	world._input(touch)
	rows["joystick_travel_m"] = movement_start.distance_to(world.actor.position)
	for w in world.enemies:w.active=false
	var wolf=world.encounters._add(aim_point,false,990,aim_point)
	tower.reload=.86
	for i in 7:await physics_frame
	for z in [1.,2.]:
		world.set_zoom_ratio(z)
		for i in 2:await physics_frame
		picture("Gameplay-%dx"%int(z))
		rows["station_projected_%dx"%int(z)] = str(world.camera.unproject_position(tower.art.swivel.global_position))
	# One uninterrupted normal-camera encounter. A live enemy moves on its own.
	world.set_zoom_ratio(1.)
	rows["paid"]=tower.active
	rows["footprint"]=str(tower.FOOTPRINT)
	rows["renderer"]=RenderingServer.get_video_adapter_name() if capture else "headless"
	rows["muzzle_origin"]=str(tower.art.muzzle_global_position())
	var h:int=wolf.hp
	var summary:={}
	var before:Vector3=tower.art.muzzle_global_position()
	var seen:=false
	var shot_steps:=[]
	var impact_steps:=[]
	var last_flight:=false
	var last_hp:int=wolf.hp
	for i in 216:
		await physics_frame
		if capture and i%4==0:
			picture("frames/shot-%03d"%int(i/4))
		var inflight: bool=not tower.flights.is_empty()
		if inflight and not last_flight:
			shot_steps.append(i)
			if not seen:
				seen=true
				for e in world.events:
					if e.event=="tower_fire":
						summary["release_xz_error_from_previous_loaded_tip_center_m"]=Vector2(e.x,e.z).distance_to(Vector2(before.x,before.z))
				summary["flight_distance_after_first_tick_m"]=before.distance_to(tower.flights[0].mesh.global_position)
				picture("Bolt-release-1x")
		last_flight=inflight
		before=tower.art.muzzle_global_position()
		if wolf.hp<last_hp:
			impact_steps.append(i)
			if last_hp==h:picture("Impact-1x")
			last_hp=wolf.hp
	rows["launch_physics_ticks"]=shot_steps
	rows["impact_physics_ticks"]=impact_steps
	rows["target_hp_before"]=h
	rows["target_hp_after"]=wolf.hp
	rows["flight"]=seen
	rows["launch"]=summary
	rows["visible_meshes"]=tower.art.find_children("*","MeshInstance3D",true,false).map(func(n):return str(n.name))
	var f:=FileAccess.open(folder.path_join("Scene.json"),FileAccess.WRITE)
	f.store_string(JSON.stringify(rows,"  ")+"\n")
	f.close()
	await preload("res://tests/lifecycle_test_profile.gd").drain_field_audio(self,world)
	world.queue_free()
	for i in 5:await process_frame
	quit(0)
