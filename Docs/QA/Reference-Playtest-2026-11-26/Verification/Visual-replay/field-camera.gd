extends SceneTree
var g
var dir:=OS.get_environment("PROBE_DIR")
var hz:=int(OS.get_environment("ACTION_HZ")) if OS.has_environment("ACTION_HZ") else 24
var film:=OS.get_environment("NATIVE_MOVIE")=="1"
var plates:=OS.get_environment("PORTRAIT_4K")=="1"
var dry:=not film and not plates
var starter:=OS.get_environment("STARTER_FOOD")=="1"
var chapter:=""
var photos:Array=[]
var frames:Array=[]
var logbook:Array=[]
var ingest_seen:=false
var routes:Array=[]
var start:=0.
func _initialize():call_deferred("run")
func uv(at:Vector3):
	if not is_instance_valid(g.camera) or dry:return []
	var pixel:Vector2=g.camera.unproject_position(at)/root.get_visible_rect().size
	return [pixel.x,pixel.y]
func pose():
	return {"elapsed":snappedf(g.simulation_time-start,.001),"actor":[g.actor.position.x,g.actor.position.z],"haul":g.inventory.carried.duplicate(),"stored":g.inventory.stored.duplicate(),"hoppers":g.inventory.settlement.hoppers.duplicate(),"worker_world":[g.survivor.actor.global_position.x,g.survivor.actor.global_position.z],"worker_mode":g.survivor.actor.mode,"worker_showing_bundle":g.survivor.actor.bundle.visible,"worker_swing":g.survivor.swing_time,"worker_contacts":g.survivor.contacts,"worker":g.survivor.phase,"owl":g.owl.state,"zoom":g.get_zoom_ratio(),"flights":g.carry.flights.size(),"in_storage":g.depot.at_loading_area(g.actor.position) if g.depot.has_method("at_loading_area") else g.depot.at_apron(g.actor.position),"build_order":g.inventory.build_order.duplicate(),"deposit_visit":g.depot.visit,"chapter":chapter}
func photo(name:String,z:float):
	g.set_zoom_ratio(z)
	var im:Image
	if not OS.has_environment("PLATES_SIM_ONLY"):
		RenderingServer.force_draw(false,0.)
		im=root.get_texture().get_image()
		im.save_jpg(dir.path_join(name+".jpg"),.95)
	var p=pose()
	p.merge({"id":name,"graphics_ultra":g.graphics.ultra,"size":[im.get_width(),im.get_height()] if im else [0,0],"native_render_scale":root.scaling_3d_scale,"native_camera":g.camera==root.get_camera_3d(),"food_shelf_uv":uv(g.carry.storage_anchors["meat"].global_position) if g.carry.storage_anchors.has("meat") else [],"hero_uv":uv(g.actor.global_position+Vector3.UP*.85),"worker_uv":uv(g.survivor.actor.global_position+Vector3.UP*.9),"owl_uv":uv(g.owl.global_position+Vector3.UP*.25)})
	photos.append(p)
func sample():
	if chapter.is_empty() or (OS.has_environment("WAREHOUSE_ONLY") and chapter!="Unload at the storage house"):return
	var si=pose()
	if plates and starter and not ingest_seen:
		var meats:Array=g.carry.flights.filter(func(f):return f.kind=="meat" and f.to=="storage")
		if meats.size()>=2 and meats.any(func(f):return f.t>.15):
			ingest_seen=true
			photo("Starter-food-in-flight-1x",1.)
			photo("Starter-food-in-flight-2x",2.)
			g.set_zoom_ratio(1.)
	if film:
		RenderingServer.force_draw(false,1./hz)
		root.get_texture().get_image().save_jpg(dir.path_join("frame-%04d.jpg"%frames.size()),.94)
	frames.append(si)
func touch(origin:Vector2,when:bool):
	var e:=InputEventScreenTouch.new();e.pressed=when;e.index=0;e.position=origin;root.push_input(e,true)
func move_to(dest:Vector2,limit:=110):
	var origin:Vector2=root.get_visible_rect().size*Vector2(.17,.71);touch(origin,true)
	var tstart:float=g.simulation_time
	for j in limit:
		var direction3:=Vector3(dest.x-g.actor.position.x,0,dest.y-g.actor.position.z)
		if direction3.length()<.13:break
		var right:Vector3=g.camera.global_basis.x
		var near:Vector3=right.cross(Vector3.UP)
		var axis:=Vector2(direction3.dot(right),direction3.dot(near)).normalized()
		var drag:=InputEventScreenDrag.new();drag.position=origin+axis*82.*clampf(direction3.length()*1.35,.3,.99);drag.index=0;root.push_input(drag,true)
		await physics_frame
	touch(origin,false)
	routes.append({"phase":chapter,"to":str(dest),"end":str(g.actor.position),"seconds":g.simulation_time-tstart})
func place(p:Vector3,rotation_angle:float):
	g.clear_touch()
	g.actor.position=p;g.actor.rotation.y=rotation_angle;g.camera.position=p+g.camera_follow_offset
	for k in 3: await physics_frame
func pause(ticks:int):
	for k in ticks:await physics_frame
func run():
	g=load("res://field_opening.tscn").instantiate();root.add_child(g);current_scene=g
	await pause(15)
	if g.persist_blocked or (not starter and not g.inventory.settlement.survivor_paid):quit(2);return
	if plates and not starter:
		g.graphics.set_ultra(true)
		chapter="At the forester's work pine"
		# The forester follows the normal walk and tree-harvest states. Position the player
		# downstage from the tree so the actual camera includes all three living actors.
		await place(Vector3(-3.05,0,-1.18),PI)
		await pause(120)
		# Hold the wave clock for this isolated art inspection while the survivor and owl animate normally.
		for existing in g.enemies.duplicate():g.encounters._remove(existing)
		g.encounters.remaining=g.encounters.WAVE_SECONDS
		await place(g.survivor.STANCE+Vector3(-2.08,0,.89),.91)
		var initial_contacts:int=g.survivor.contacts
		var seen:=false
		var contact:=false
		var haul:=false
		var pickup_origin:=Vector3.INF
		for t in 2400:
			await physics_frame
			if not seen and g.survivor.phase=="chopping" and g.survivor.swing_time>=.35:
				seen=true
				photo("Ultra-field-1x",1.);photo("Ultra-field-2x",2.);g.set_zoom_ratio(1.)
			if seen and not contact and g.survivor.contacts>initial_contacts:
				contact=true
				photo("Ultra-contact-1x",1.);photo("Ultra-contact-2x",2.);g.set_zoom_ratio(1.)
			if contact and g.survivor.phase=="carrying" and pickup_origin==Vector3.INF:
				pickup_origin=g.survivor.actor.global_position
				await place(pickup_origin+Vector3(-.68,0,1.02),.91)
			if contact and g.survivor.phase=="carrying" and g.survivor.actor.mode=="carry" and g.survivor.actor.bundle.visible and pickup_origin.distance_to(g.survivor.actor.global_position)>=.45 and g.survivor.step_cycle>.17 and g.survivor.step_cycle<.45:
				haul=true
				photo("Ultra-haul-1x",1.);photo("Ultra-haul-2x",2.);g.set_zoom_ratio(1.)
				break
		logbook.append({"chop":seen,"blade_contact":contact,"haul":haul,"haul_displacement":pickup_origin.distance_to(g.survivor.actor.global_position) if haul else 0.,"phase":g.survivor.phase})

	elif OS.has_environment("GAIT_ONLY"):
		g.set_zoom_ratio(1.);process_frame.connect(sample)
		await place(Vector3(1.0,0,13.15),1.62)
		start=g.simulation_time
		chapter="Run across the snow"
		await move_to(Vector2(6.9,12.80),97);await pause(22)
		chapter=""
	elif starter:
		g.set_zoom_ratio(1.); process_frame.connect(sample)
		await place(Vector3(-3.05,0,.99),PI)
		start=g.simulation_time
		chapter="Enter the starter FOOD shelf"
		await move_to(Vector2(-3.05,-1.18),90);await pause(50)
		chapter=""
		logbook.append(pose())
		if plates:
			photo("Starter-food-stored-1x",1.)
			photo("Starter-food-stored-2x",2.)
	else:
		g.set_zoom_ratio(1.); process_frame.connect(sample)
		await place(Vector3(1.0,0,13.15),1.62)
		start=g.simulation_time
		chapter="Run across the snow"
		await move_to(Vector2(6.9,12.80),97);await pause(8)
		chapter=""
		await place(Vector3(1.35,0,-3.76),-2.9)
		chapter="Load the cooker"
		await move_to(Vector2(1.20,-5.67),75);await pause(26)
		chapter=""
		await place(Vector3(-3.05,0,.65),3.0)
		chapter="Unload at the storage house"
		await move_to(Vector2(-3.05,-1.18),85);await pause(92 if OS.has_environment("WAREHOUSE_ONLY") else 40)
		chapter=""
		logbook.append(pose())
		await place(Vector3(1.0,0,13.15),1.62)
		chapter="Run after unloading"
		await move_to(Vector2(6.75,12.80),91);await pause(5)
		chapter=""
	var f:=FileAccess.open(dir.path_join("live.json"),FileAccess.WRITE)
	f.store_string(JSON.stringify({"scene":g.scene_file_path,"actions":frames,"photos":photos,"observations":logbook,"events":g.events,"routes":routes,"camera_output":[root.size.x,root.size.y],"fps":hz,"start":start},"  "));f.close()
	g.queue_free();await pause(5);quit()
