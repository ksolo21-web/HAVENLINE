extends SceneTree
const Session=preload("res://tests/lifecycle_test_profile.gd")
var out:=OS.get_environment("CAMP_OUT")
var world
var tower
var draw:=DisplayServer.get_name()!="headless"
var motion:Array=[]
var serial:=0
func _initialize()->void:call_deferred("run")
func at(p:Vector3,z:float)->void:
	world.actor.global_position=p
	world.previous_dry_position=p
	world.actor.velocity=Vector3.ZERO
	world.gait_motor.travel_speed=0.
	world.actor.reset_physics_interpolation()
	world.set_zoom_ratio(z)
	world.camera.global_position=p+world.camera_follow_offset
	world.camera.reset_physics_interpolation()
func snap(key:String)->void:
	if not draw:return
	await process_frame
	RenderingServer.force_draw(false)
	var photo=root.get_texture().get_image()
	photo.save_jpg(out.path_join(key+".jpg"),.94)
func run()->void:
	var profile=Session.Profile.new()
	if not profile.configure(OS.get_cmdline_user_args()):quit(2);return
	world=load("res://field_opening.tscn").instantiate()
	root.add_child(world);current_scene=world
	for tick in 5:await physics_frame
	tower=world.defense_tower
	if world.persist_blocked or not tower.active or not world.counter.active:
		printerr("Guarded earned camp could not load. ",world.persist_error)
		quit(2);return
	var base:Vector3=tower.global_position
	for zoom in [1.,2.]:
		at(base+Vector3(-1.58,0.,-1.12),zoom)
		var touch:=InputEventScreenTouch.new()
		touch.index=7;touch.position=Vector2(282,634);touch.pressed=true
		world._input(touch)
		var drag:=InputEventScreenDrag.new()
		drag.index=7;drag.position=touch.position+Vector2(-23.,28.)
		world._input(drag)
		for i in 5:await physics_frame
		touch.pressed=false;world._input(touch)
		world.set_zoom_ratio(zoom)
		world.camera.global_position=world.actor.global_position+world.camera_follow_offset
		world.camera.reset_physics_interpolation()
		for i in 4:await physics_frame
		await snap("Approach-%dx"%int(zoom))
	world.set_physics_process(false)
	for side in [1.,-1.]:
		var c=world.counter
		var start:Vector3=c.to_global(Vector3(.32,0,side*2.))
		at(start,1.)
		world.actor.move_and_collide(c.global_position-start)
		world.previous_dry_position=start;world.constrain_private_snow_travel()
		for i in 2:await physics_frame
		await snap("Counter-inside-1x" if side>0 else "Counter-outside-1x")
		world.set_zoom_ratio(2.)
		world.camera.global_position=world.actor.global_position+world.camera_follow_offset
		for i in 2:await physics_frame
		await snap("Counter-inside-2x" if side>0 else "Counter-outside-2x")
	# Reopen a legacy saved position that fell inside the worktop footprint.
	var embedded:Vector3=world.counter.to_global(Vector3(.42,0.,-.37))
	world.lifecycle._restore_actor({"x":embedded.x,"z":embedded.z,"yaw":0.,"hp":world.MAX_HP})
	var recovered=world.counter.to_local(world.actor.global_position)
	at(world.actor.global_position,2.)
	for i in 2:await physics_frame
	await snap("Counter-restored-2x")
	# Drive the real yaw and elevation relative to the fixed tower at the authored camera.
	# Combat only acquires exterior hostiles; the complete-circle sweep also covers turn boundaries.
	var art=tower.art
	for zoom in [1.,2.]:
		at(base+Vector3(-1.95,0.,-.57),zoom)
		for i in 2:await physics_frame
		for step in 72:
			var a:=TAU*step/72.
			var hit:=base+Vector3(5.5*sin(a),.72+.60*sin(2.*a),5.5*cos(a))
			if step==0:
				for tick in 85:art.aim_at_world(hit,1./60.);art.animate(1./60.)
			for tick in 3:
				art.aim_at_world(hit,1./60.)
				art.animate(1./60.)
			if step%24==11:art.fire(hit)
			art.update_sightline(world.actor.global_position,world.camera)
			if step%3==0:
				motion.append([zoom,step*5,art.swivel.rotation.y,art.bow.rotation.x])
				if draw:
					await physics_frame
					await snap("frames/"+str(int(zoom))+"x-%03d"%int(step/3))
			if step in [9,27,45,63]:
				await snap("Turn-%03d-%dx"%[step*5,int(zoom)])
	# True obstruction from an ordinary legal standing point.
	for zoom in [1.,2.]:
		var eye:Vector3=world.camera.global_basis.z
		var horizontal:=Vector3(eye.x,0,eye.z).normalized()
		at(base-horizontal*2.04,zoom)
		art.update_sightline(world.actor.global_position,world.camera)
		for i in 3:await physics_frame
		await snap("Behind-%dx"%int(zoom))
	var combat:={}
	if not out.contains("Build12"):
		world.set_physics_process(true)
		at(base+Vector3(1.28,0.,1.48),1.)
		for enemy in world.enemies:enemy.active=false
		var where:=base+Vector3(4.35,0.,.90)
		var wolf=world.encounters._add(where,false,993,where)
		var start_hp:int=wolf.hp
		tower.reload=.40
		var released:=-1
		var impact:=-1
		var fire_id:=0
		var xz:Array=[]
		for tick in 115:
			await physics_frame
			if tick%8==0:xz.append([tick,wolf.position.x,wolf.position.z,art.swivel.rotation.y])
			var airborne:bool=not tower.flights.is_empty()
			if tick==12:await snap("Field-Aim")
			if airborne and released<0:
				released=tick
				await snap("Field-Release")
			elif released>=0 and tick==released+5:await snap("Field-Flight")
			if wolf.hp<start_hp and impact<0:
				impact=tick
				await snap("Field-Hit")
			if impact>=0 and tick==impact+12:await snap("Field-Reload")
		combat={"starting_hp":start_hp,"ending_hp":wolf.hp,"release_tick":released,"hit_tick":impact,"tracked_enemy_xz_and_tower_yaw":xz}
	var f=FileAccess.open(out.path_join("Native.json"),FileAccess.WRITE)
	f.store_string(JSON.stringify({"scene":"res://field_opening.tscn","motion":motion,"combat":combat,"restored_local_counter":str(recovered),"window":str(root.size),"reference_qa":"paid camp fixture and native touch approach; forced track sweep separately","renderer":RenderingServer.get_video_adapter_name() if draw else "headless"}," "));f.close()
	await Session.drain_field_audio(self,world);world.queue_free()
	for i in 3:await process_frame
	quit()
