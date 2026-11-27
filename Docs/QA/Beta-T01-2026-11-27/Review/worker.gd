extends "res://tests/qa_worker_jobs.gd"

var cases := {}
var report := {}
var profile_fixture := ""
var local_checks := PackedStringArray()

func verify(ok: bool, name_: String) -> void:
	cases[name_]=ok
	if not ok: push_error(name_)

func _wait(frames: int) -> void:
	for i in frames: await physics_frame

func _event_contacts(limit: int, tree: Node3D) -> Array:
	var events: Array=[]
	for tick_id in limit:
		await physics_frame
		var loc: Vector3=tree.global_position if is_instance_valid(tree) else Vector3.INF
		for e: Dictionary in game.events:
			if e.event=="survivor_chop_contact" and Vector2(e.x,e.z).distance_to(Vector2(loc.x,loc.z))<.8 and not events.has(e):
				events.append(e.duplicate())
		if events.size()>=3:break
	return events

func _scene() -> void:
	game=load("res://field_opening.tscn").instantiate()
	root.add_child(game)
	current_scene=game
	for i in 4: await physics_frame
	worker=game.survivor
	setup_camp()

func _loss_branch() -> void:
	var original: Node3D=game.lifecycle.loaded.get("survivor-work-pine")
	verify(is_instance_valid(original),"preferred tree is initially present in the fixture")
	if not is_instance_valid(original):return
	var local: Array=[]
	for pine:Node3D in game.trees:
		var id:String=pine.get_meta("field_source_id","")
		if not id.begins_with("grove@") and pine.global_position.length()<24.:
			# The preferred tree genuinely depletes. Temporarily deferring the
			# other close legacy pines isolates the active grove selection.
			if pine==original:game.lifecycle.deplete(pine)
			worker.deferred_sources[id]=worker.work_clock+30.
			local.append(id)
	var grove: Dictionary={}
	for row: Dictionary in game.forest.records:
		if row.index<0 or row.get("occupied",false):continue
		if grove.is_empty() or (row.transform.origin as Vector3).distance_to(Vector3(-14.4,0,11.2)) < (grove.transform.origin as Vector3).distance_to(Vector3(-14.4,0,11.2)):
			grove=row
	var seed: Vector3=grove.transform.origin
	var idle:bool=OS.get_environment("T01_ROUTE")=="worker-idle"
	if not idle: worker.actor.global_position=seed+Vector3(-2.4,0,1.7)
	worker.route.clear()
	worker.phase="waiting_storage"
	worker.waiting=20.
	game.actor.position=Vector3(-3.6,0,-3.8)
	await _wait(30)
	var already_live:int=0
	for pine:Node3D in game.trees:
		if String(pine.get_meta("field_source_id","")).begins_with("grove@"):
			already_live+=1
	if idle: verify(already_live==0,"no eligible grove is live before idle fallback")
	else: verify(is_instance_valid(game.lifecycle.loaded.get(grove.id)),"alternate grove streams around worker while player remains in camp")
	var ready:bool=worker._begin_outbound()
	var selected:Node3D=worker.tree
	var id:String=selected.get_meta("field_source_id","") if is_instance_valid(selected) else ""
	verify(ready and id.begins_with("grove@") and worker.phase=="to_tree","a normal fallback job selects a formerly excluded groved source")
	var contacts:=await _event_contacts(1060,selected)
	verify(contacts.size()==3,"normal survivor animation physically delivers three alternate chops")
	var stock0: int=game.inventory.stored.wood
	for i in 1100:
		await physics_frame
		if int(game.inventory.stored.wood)>stock0:break
	verify(int(game.inventory.stored.wood)>stock0,"alternate-source wood reaches storage while player stays in camp")
	report.loss={"worker_seed_staged":not idle,"existing_grove_nodes_before_choose":already_live,"isolated_worker_seed":str(seed) if not idle else "","depleted":"survivor-work-pine","temporarily_deferred":local,"chosen":id,"contact_events":contacts,"warehouse_before":stock0,"warehouse_after":game.inventory.stored.wood}

func _remote_branch() -> void:
	var land:Node3D=game.get_node("WorldOneLandscape")
	var staging_key:=Vector2i(1,0)
	var best:Dictionary={}
	var desired:=Vector3(37.,0,15.)
	for row:Dictionary in land.describe_chunk(staging_key):
		var at:Vector3=row.position
		if row.kind!="wood" or at.x<36. or at.x>57. or at.z<6. or at.z>28.:continue
		if best.is_empty() or at.distance_to(desired)<(best.position as Vector3).distance_to(desired):best=row
	verify(not best.is_empty(),"seeded eastern chunk has a remote pine")
	if best.is_empty():return
	var expected:Vector3=best.position
	# Place independent actors in the separation fixture once. Production
	# streaming, source selection, routing and harvest then drive the result.
	game.actor.position=expected+Vector3(-3.4,0,1.2)
	worker.actor.global_position=expected+Vector3(-1.5,0,1.2)
	worker.route.clear()
	worker.phase="waiting_storage"
	worker.waiting=20.
	await _wait(20)
	var available_before: Node3D=game.lifecycle.loaded.get(best.id)
	verify(is_instance_valid(available_before) and expected.length()>24.0,"remote pine streams as a real source outside the former radius")
	var chosen: bool=worker._begin_outbound()
	var selected:Node3D=worker.tree
	var id:String=selected.get_meta("field_source_id","") if is_instance_valid(selected) else ""
	verify(chosen and id.begins_with("world1/") and selected.global_position.length()>24.,"worker chooses a live outer World One source")
	if not chosen or not is_instance_valid(selected):return
	var identity:=selected.get_instance_id()
	var selected_at:Vector3=selected.global_position
	var target_key: Vector2i=land.chunk_for(selected_at)
	game.actor.position=Vector3(-71.,0,25.)
	game.previous_dry_position=game.actor.position
	await _wait(34)
	var player_key:Vector2i=land.center_chunk
	var actual:Node3D=game.lifecycle.loaded.get(id)
	verify(abs(player_key.x-target_key.x)>1 and land.chunks.has(target_key) and is_instance_valid(actual) and actual.get_instance_id()==identity,"active target remains same node after player crosses multiple chunks")
	var contacts:=await _event_contacts(850,selected)
	verify(contacts.size()==3,"remote tree receives three physical survivor contacts after player departure")
	report.remote={"seed_candidate":best.id,"assigned":id,"distance_m":selected_at.length(),"from_player_m":selected_at.distance_to(game.actor.position),"worker_chunk":str(target_key),"player_chunk":str(player_key),"same_live_identity":is_instance_valid(actual) and actual.get_instance_id()==identity,"contact_events":contacts,"loaded_chunks":land.chunks.size()}

func _visual_branch() -> void:
	var chosen_grove: Dictionary={}
	for row: Dictionary in game.forest.records:
		if row.index<0 or row.get("occupied",false):continue
		if chosen_grove.is_empty() or (row.transform.origin as Vector3).distance_to(Vector3(-14.4,0,11.2))< (chosen_grove.transform.origin as Vector3).distance_to(Vector3(-14.4,0,11.2)):
			chosen_grove=row
	var stage: Vector3=chosen_grove.transform.origin
	game.actor.position=stage+Vector3(-1.8,0,3.7)
	game.previous_dry_position=game.actor.position
	worker.actor.global_position=stage+Vector3(-2.4,0,1.7)
	worker.phase="waiting_storage"
	worker.route.clear()
	worker.waiting=30.
	for pine:Node3D in game.trees:
		var name_:String=pine.get_meta("field_source_id","")
		if not name_.begins_with("grove@"): worker.deferred_sources[name_]=worker.work_clock+30.
	await _wait(28)
	verify(worker._begin_outbound(),"visual fixture dispatches normal grove approach")
	var renderer: String=RenderingServer.get_video_adapter_name()
	var result := {"renderer":renderer,"scene":"field_opening.tscn","player_camera":game.camera==root.get_camera_3d(),"staged_actor_positions":true,"views":[]}
	var wanted:Array=["to_tree","chopping"]
	for _i in 320:
		await physics_frame
		if wanted.is_empty():break
		if not wanted.has(worker.phase):continue
		var sight = game.field_env.resource_sightline
		var run_phase: String=worker.phase
		var feet:Vector3=worker.actor.global_position
		var eye:Vector3=game.camera.global_basis.z.normalized()
		var crowns := 0
		for source:Node3D in game.surfaces:
			if source.get_meta("resource_kind","")!="wood":continue
			var part:MeshInstance3D=game.surfaces[source][0]
			if sight.opened.has(part) and sight._near_sightline(part,feet,eye):crowns+=1
		if crowns==0 or not sight.worker_feet.is_finite():continue
		wanted.erase(run_phase)
		var row := {"worker_phase":run_phase,"worker":str(feet),"player":str(game.actor.global_position),"crown_parts_cleared":crowns}
		for zoom:float in [1.,2.]:
			game.set_zoom_ratio(zoom)
			await process_frame
			RenderingServer.force_draw(false,1.0/60.0)
			var capture_path:=OS.get_environment("T01_OUT").path_join("worker-%s-%dx.jpg"%[run_phase,int(zoom)])
			root.get_texture().get_image().save_jpg(capture_path,.91)
		result.views.append(row)
		game.set_zoom_ratio(1.)
	report.visual=result
	verify(not wanted.has("to_tree"),"moving worker receives camera-near canopy cutaway in actual scene")
	verify(not wanted.has("chopping"),"chopping worker retains camera-near canopy cutaway")

func run() -> void:
	await _scene()
	verify(not game.persist_blocked and game.inventory.settlement.rescued,"valid rescue fixture is loaded")
	if OS.get_environment("T01_ROUTE")=="worker-visual":
		await _visual_branch()
	elif OS.get_environment("T01_ROUTE")=="worker-remote":
		await _remote_branch()
	else:
		await _loss_branch()
	report.checks=cases
	report.viewport=str(root.size)
	report.persistence=not game.persist_blocked
	var path:=OS.get_environment("T01_OUT").path_join("witness.json")
	var f:=FileAccess.open(path,FileAccess.WRITE)
	f.store_string(JSON.stringify(report,"\t"))
	f.close()
	print("WORKER_UNRESTRICTED ",JSON.stringify(report))
	await Session.drain_field_audio(self,game)
	game.queue_free()
	for i in 5: await process_frame
	quit(int(cases.values().has(false)))
