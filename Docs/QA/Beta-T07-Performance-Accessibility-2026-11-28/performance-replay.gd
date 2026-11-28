extends "res://tests/qa_snow_truck.gd"

var native := OS.get_environment("T07_NATIVE")=="1"
var report := {}
var busy := OS.get_environment("T07_BUSY")=="1"
var target_preset:=int(OS.get_environment("T07_PRESET"))
var draw_samples:=maxi(4,int(OS.get_environment("T07_DRAW_SAMPLES")))

func stock_and_staff() -> void:
	var book=field.inventory
	for kind in ["wood","stone","meat"]:
		for i in 20:
			book.collect("c6-workshop-stock-%s-%d"%[kind,i],kind)
			book.deposit(kind)
	for i in book.survivor_cost:
		book.collect("c6-rescue-wood-%d"%i,"wood")
	book.carried.wood-=book.survivor_cost
	book.settlement.survivor_wood=book.survivor_cost
	book.settlement.survivor_paid=true
	field.actor.global_position=field.survivor.RESCUE
	field.survivor.advance(1./60.)
	_assert("one active worker completed the normal rescue",book.settlement.rescued and field.survivor.phase!="waiting_rescue")
	field._inventory_changed()
	field.player_invulnerability=120.
	field.encounters.remaining=900.

func seed_ambient_wave() -> void:
	for wolf in field.enemies.duplicate(): field.encounters._remove(wolf)
	for i in 4:
		var at:=Vector3(13.4+float(i%2)*2.,.008,2.+float(i/2)*2.)
		field.encounters.serial+=1
		field.encounters._add(at,i==3,field.encounters.serial,at)

func rss_mib() -> float:
	for line in FileAccess.get_file_as_string("/proc/self/status").split("\n"):
		if line.begins_with("VmRSS:"):
			return float(line.trim_prefix("VmRSS:").strip_edges().split(" ")[0])/1024.
	return -1.


func _initialize() -> void:
	run.call_deferred()

func p95(values: Array[float]) -> float:
	values.sort()
	return values[ceili(.95*values.size())-1]

func tree_counts() -> Dictionary:
	var materials := {}
	var rigs := 0
	var bodies := 0
	var npcs := 0
	for node: Node in field.find_children("*","Node3D",true,false):
		if node is Skeleton3D and node.is_visible_in_tree(): rigs+=1
		if node is PhysicsBody3D: bodies+=1
		if node is CharacterBody3D and node.is_visible_in_tree() and node!=field.actor: npcs+=1
		if not node.is_visible_in_tree(): continue
		var mesh: Mesh
		if node is MeshInstance3D: mesh=node.mesh
		if node is MultiMeshInstance3D and node.multimesh: mesh=node.multimesh.mesh
		if not mesh: continue
		for surface in mesh.get_surface_count():
			var material: Material=mesh.surface_get_material(surface)
			if node is MeshInstance3D: material=node.get_active_material(surface)
			if node.material_override: material=node.material_override
			if material: materials[material.get_instance_id()]=true
	return {"unoccluded_tree_material_upper_bound":materials.size(),"active_character_bodies_upper_bound":npcs,
		"visible_tree_rigs_upper_bound":rigs,"all_physics_bodies_upper_bound":bodies,
		"active_3d_physics_bodies":Performance.get_monitor(Performance.PHYSICS_3D_ACTIVE_OBJECTS)}

func run() -> void:
	field=load("res://field_opening.tscn").instantiate()
	root.add_child(field)
	camera=field.camera
	truck=field.snow_truck
	origin=Vector2(root.get_visible_rect().size)*Vector2(.28,.71)
	for _step in 12: await physics_frame
	field.graphics.set_preset(target_preset)
	for id in ["center_hearth","expansion_1","storage_wood","storage_stone","storage_meat","expansion_2","camp_cooker","saw_bench","quarry_drill","watchtower","orbit_upgrade","snow_garage","snow_truck"]:
		_assert("paid fixture "+id,_fund(id))
		for _step in 4: await physics_frame
	if busy: stock_and_staff()
	var states := {"south_approach":Vector3(0.,.008,5.90),"work_aisle":Vector3(1.72,.008,1.8),
		"east_patrol":Vector3(11.4,.008,.9)}
	for route: String in states:
		field.actor.global_position=states[route]
		field.previous_dry_position=states[route]
		if busy: seed_ambient_wave()
		for _i in 90: await physics_frame
		if native:
			for _i in 2:
				await process_frame
				RenderingServer.force_draw(false)
		var durations: Array[float]=[]
		var scene := {}
		if native:
			var draws: Array[float]=[]
			var primitives: Array[float]=[]
			var texture_memory: Array[float]=[]
			for tick in draw_samples:
				if tick==1: steer(_heading(Vector3.RIGHT))
				if tick==draw_samples-2: steer(Vector2.ZERO)
				await physics_frame
				await process_frame
				var start := Time.get_ticks_usec()
				RenderingServer.force_draw(false)
				durations.append((Time.get_ticks_usec()-start)*.001)
				draws.append(RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_DRAW_CALLS_IN_FRAME))
				primitives.append(RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_PRIMITIVES_IN_FRAME))
				texture_memory.append(RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TEXTURE_MEM_USED)/1048576.)
			scene={"software_render_submission_ms_p95":p95(durations),"peak_draw_calls":draws.max(),
				"peak_submitted_primitives":primitives.max(),"peak_renderer_texture_mb":texture_memory.max(),
				"active_draw_frames":draws.size()}
		else:
			var previous:= Time.get_ticks_usec()
			var previous_frame := Engine.get_physics_frames()
			var gaps := 0
			for tick in 360:
				if tick%120==0:
					var direction:= Vector3.FORWARD if tick==0 else Vector3.BACK
					steer(_heading(direction) if tick<240 else Vector2.ZERO)
				await physics_frame
				var next := Time.get_ticks_usec()
				var id := Engine.get_physics_frames()
				if id==previous_frame+1: durations.append((next-previous)*.001)
				else: gaps+=1
				previous=next
				previous_frame=id
			scene={"headless_tick_wall_ms_p95":p95(durations),"ticks":durations.size(),"gaps":gaps}
		steer(Vector2.ZERO)
		scene.merge(tree_counts())
		scene["position"]=pt(field.actor.global_position)
		scene["actors"]={"wolves":field.enemies.size(),"rescued_survivor":field.survivor.can_defend(),"survivor_phase":field.survivor.phase,
			"customers":field.counter.queue.size(),"owl":int(is_instance_valid(field.owl) and field.owl.is_visible_in_tree())}
		scene["resident_process_mb"]=rss_mib()
		report[route]=scene
		print("T07_PERFORMANCE_ROUTE ",route," ",JSON.stringify(scene))
	print("T07_PERFORMANCE ",JSON.stringify({"native":native,"busy":busy,"raster":[root.size.x,root.size.y],
		"renderer":RenderingServer.get_video_adapter_name(),"profile":field.graphics.preset_name(),
		"scale_3d":root.scaling_3d_scale,"msaa_enum":root.msaa_3d,"routes":report,"checks":checks,
		"static_engine_mb":Performance.get_monitor(Performance.MEMORY_STATIC)/1048576.,
		"source":{"field":FileAccess.get_sha256("res://field_opening.gd"),"selector":FileAccess.get_sha256("res://field_context_director.gd")}}))
	await _close_field()
	quit(int(checks.values().has(false)))
