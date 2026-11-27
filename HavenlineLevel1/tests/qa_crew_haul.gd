extends "res://tests/qa_worker_jobs.gd"
## Observe ordinary work across several regrowing nodes after the tutorial
## delivery. Nothing is inserted into the worker's pack or the loose-item list.
const HERE:="res://tests/qa_crew_haul.gd"
var route_rows:Array=[]
var maximum:=0
var mixed_max:=0
var first_delivery_tick:=-1
var freight_tick:=-1
var outside_seconds:=0.
var cameras:={}
var frames:=0
var recording_walk:=false

func units() -> Dictionary:
	var j:Dictionary=game.inventory.settlement
	var cargo:Dictionary=j.worker_load.duplicate()
	if j.worker_carry_token!="":cargo.wood+=1
	if j.worker_supply!="":cargo[j.worker_supply]+=1
	for kind:String in cargo:cargo[kind]=game.Progress.units(cargo[kind])
	return cargo

func record_frame() -> void:
	await process_frame
	RenderingServer.force_draw(false)
	root.get_texture().get_image().save_jpg(output.path_join("frames/s%04d.jpg"%frames),.90)
	frames+=1

func zooms(label:String) -> void:
	if not recording or cameras.has(label) or output.is_empty():return
	cameras[label]={"load":units(),"worker":str(worker.actor.global_position),"phase":worker.phase,"player":str(game.actor.global_position),"renderer":RenderingServer.get_video_adapter_name()}
	for zoom in [1.,2.]:
		game.set_zoom_ratio(zoom)
		var body_pixels:float=game.camera.unproject_position(worker.actor.global_position).y-game.camera.unproject_position(worker.actor.global_position+Vector3.UP*1.50).y
		var top_y:=INF
		for group:Array in worker.pack.pieces.values():
			for resource:Node3D in group:
				if not resource.is_visible_in_tree():continue
				for mesh:MeshInstance3D in resource.find_children("*","MeshInstance3D",true,false):
					var box:=mesh.get_aabb()
					for corner in 8:
						top_y=minf(top_y,game.camera.unproject_position(mesh.to_global(box.get_endpoint(corner))).y)
		var feet:Vector2=game.camera.unproject_position(worker.actor.global_position)
		cameras[label][str(int(zoom))+"x"]={"feet":str(feet),"top_y":top_y,"body_px":body_pixels,"loaded_body_heights":(feet.y-top_y)/body_pixels,"lanes":worker.pack.presented.duplicate()}
		await process_frame
		RenderingServer.force_draw(false)
		root.get_texture().get_image().save_jpg(output.path_join(label+"-"+str(int(zoom))+"x.jpg"),.95)
	game.set_zoom_ratio(1.)

func run()->void:
	if not Save.Profile.new().configure(OS.get_cmdline_user_args()):
		var path:=Session.make_directory()
		var status:=Session.child(HERE,path,"--observe-haul")
		Session.remove_owned(path);quit(status);return
	game=load("res://field_opening.tscn").instantiate()
	root.add_child(game)
	current_scene=game
	for i in 3:await process_frame
	game.set_physics_process(false)
	game.set_process(false)
	worker=game.survivor
	setup_camp()
	var inv=game.inventory
	# Owned conveyors free the survivor for forest/mineral runs. All costs are
	# paid from named, independent setup receipts.
	for id:String in game.Progress.LINES:
		for kind:String in inv.remaining(id):
			for n in int(inv.remaining(id)[kind]):
				inv.collect("hauling-infrastructure-%s-%s-%d"%[id,kind,n],kind)
				inv.payment(id,kind,false)
		game._finish_purchase(id)
	# Finish any deferred floor egress for these newly paid buildings before
	# placing the stationary QA observer on an unobstructed public cell.
	await process_frame
	var initial:Dictionary=inv.carried.duplicate()
	var j:Dictionary=inv.settlement
	var return_load:=0
	var landed_tick:=-1
	var unload_tick:=-1
	var discharged:=false
	var old_phase:=""
	# The observer stands beside the paid storehouse apron; the normal
	# gameplay camera and HUD use this fixed player for the entire route.
	game.actor.position=Vector3(-2.37,0,-1.88)
	game.camera.global_position=game.actor.global_position+game.camera_follow_offset
	if recording:DirAccess.make_dir_recursive_absolute(output.path_join("frames"))
	for frame in 60*280:
		tick(1./60.)
		if j.worker_deliveries>0 and first_delivery_tick<0:first_delivery_tick=frame
		var balances:=units()
		var total:=0
		var families:=0
		for kind:String in balances:
			total+=int(balances[kind])
			if balances[kind]>0:families+=1
		maximum=maxi(maximum,total)
		if families>=2:mixed_max=maxi(mixed_max,total)
		if old_phase!=worker.phase:
			route_rows.append({"tick":frame,"phase":worker.phase,"units":balances,"x":snappedf(worker.actor.position.x,.01),"z":snappedf(worker.actor.position.z,.01)})
			old_phase=worker.phase
		if frame>first_delivery_tick and first_delivery_tick>=0 and worker.phase in ["bulk_return","carrying"] and total>=120:
			if freight_tick<0:freight_tick=frame
			return_load=maxi(return_load,total)
			var seen:bool=game.camera.is_position_in_frustum(worker.actor.global_position+Vector3.UP)
			if recording and seen and worker.actor.position.distance_to(game.actor.position)<1.65:
				recording_walk=true
				await zooms("Loaded-return")
		if recording and freight_tick>=0 and worker.phase=="bin_delivery" and not worker.delivery_stream.is_empty():await zooms("Shelf-transfer")
		if recording and recording_walk and frames<34 and frame%5==0:await record_frame()
		if freight_tick>=0 and worker.phase in ["unload","bin_delivery"] and unload_tick<0:unload_tick=frame
		if freight_tick>=0 and total==0 and worker.phase not in ["bin_delivery","unload"]:
			if landed_tick<0:landed_tick=frame
			discharged=true
		if discharged and (not recording or frames>=34):break
		if game.persist_blocked:break
	check(first_delivery_tick>=0,"first wood delivery retained")
	check(freight_tick>first_delivery_tick and return_load>=120,"a routine trip returns with at least 120 displayed units")
	check(mixed_max>=120,"mixed resources stay aboard across productive stops")
	check(discharged,"larger pack discharges through the ordinary storage or purchase path")
	check(unload_tick>=0 and float(landed_tick-unload_tick)/60.<=.92,"complete mixed unload fits the reference transfer beat")
	if recording:check(cameras.has_all(["Loaded-return","Shelf-transfer"]) and frames>=34,"both camera scales observe a full return and its visible discharge")
	check(inv.carried==initial,"helper leaves player stock alone")
	var restored=game.Inventory.new()
	check(not game.persist_blocked and restored.configure(inv.configured_costs) and restored.restore(inv.snapshot()),"earned load and final deliveries restore from balanced receipts")
	var doc:={"checks":checks,"failures":errors,"first_delivery_tick":first_delivery_tick,"large_return_tick":freight_tick,"largest_observed_units":maximum,"largest_mixed_units":mixed_max,"returned_units":return_load,"unload_start_tick":unload_tick,"unload_end_tick":landed_tick,"unload_seconds":float(landed_tick-unload_tick)/60.,"route":route_rows,"photos":cameras,"captured_frames":frames,"last_phase":worker.phase,"feet":str(worker.actor.position),"last_route":str(worker.route),"stored":inv.stored.duplicate(),"initial_player":initial,"final_player":inv.carried.duplicate()}
	if not output.is_empty():
		var f:=FileAccess.open(output.path_join("Natural-haul.json"),FileAccess.WRITE)
		f.store_string(JSON.stringify(doc," "));f.close()
	print("CREW_HAUL ",JSON.stringify({"checks":checks,"errors":errors,"peak":maximum,"mixed":mixed_max,"returned":return_load,"end":worker.phase}))
	await Session.drain_field_audio(self,game);game.queue_free()
	for i in 4:await process_frame
	quit(int(not errors.is_empty()))
