extends "/tmp/havenline-t01-framing/capture.gd"

var frames: Array[Dictionary] = []
var probes := {}
var video := false

func record_view(label: String) -> void:
	var witness := await frame_at(label)
	witness["capture_pixels"] = [root.size.x, root.size.y]
	witness["scale_3d"] = root.scaling_3d_scale
	var seasonal: Array[Dictionary] = []
	for tree: Node3D in field.field_env.seasonal_pines:
		seasonal.append({"source":tree.get_meta("field_source_id"),"root":pt(tree.global_position),"state":tree.phase})
	witness["seasonal_roots"] = seasonal
	witness["tool"] = field.character_kit.equipped
	witness["orbit_turn"] = field.character_kit.turn_id
	witness["orbit_seconds"] = field.character_kit.elapsed
	frames.append(witness)

func record_interactions() -> void:
	var kit = field.character_kit
	var initial_turn: int = kit.turn_id
	var orbit := []
	for tick in 160:
		if tick % 8 == 0:
			var file := "orbit-%03d" % tick
			await _view(file)
			orbit.append({"view":file,"simulation_tick":tick,"turn":kit.turn_id,"elapsed":kit.elapsed,"tool":kit.equipped,"tip":pt(kit.current_tip),"player":pt(field.actor.global_position)})
		await _step()
	_check(kit.turn_id > initial_turn, "complete actual orbit")
	probes["orbit"] = orbit
	var events := []
	for direction: Vector2 in [Vector2.LEFT,Vector2.RIGHT,Vector2(.72,.66)]:
		var before: Vector3 = field.actor.global_position
		steer(direction*.57)
		var first_motion := 0
		for tick in range(1,37):
			await _step()
			if first_motion == 0 and before.distance_to(field.actor.global_position) > .06:
				first_motion = tick
		var receipt := {"direction":[direction.x,direction.y],"touch":field.touch_id,"first_motion_tick":first_motion,"travel":before.distance_to(field.actor.global_position)}
		_check(field.touch_id >= 0 and receipt.travel > .06, "touch gesture owns input and travels")
		await _view("touch-%d" % events.size())
		await _coast(28)
		receipt["released"] = field.touch_id < 0
		_check(receipt.released, "stick released")
		events.append(receipt)
	probes["touch"] = events

func record_founding() -> void:
	var bundles: int = field.inventory.remaining("center_hearth").wood - 1
	for i in bundles:
		field.inventory.collect("isolated-founding-framing-%02d" % i,"wood")
	field.carry.sync()
	_check(await _walk(Vector3(0.,0.,2.4)), "reach hearth pad by touch")
	for i in 300:
		if field.inventory.remaining("center_hearth").wood == 1: break
		if video and i % 10 == 0: await _view("funding-%03d" % i)
		await _step()
	_check(field.inventory.remaining("center_hearth").wood == 1 and field.field_env.perimeter_stage == 0, "actual proximity transfer leaves green pad one bundle short")
	await record_view("founding-1x")
	if video:
		await _pinch()
		await record_view("founding-2x")
		field.set_zoom_ratio(1.0)
		field.inventory.collect("isolated-founding-framing-final", "wood")
		field.carry.sync()
		for i in 240:
			if field.field_env.perimeter_stage > 0 and field.reveal_countdown < 0.0: break
			if i % 10 == 0: await _view("reveal-%03d" % i)
			await _step()
		_check(field.field_env.perimeter_stage == 1, "actual purchase reveals first camp")
		await record_view("built-1x")

func record_performance() -> void:
	var metrics := []
	for i in 9:
		await physics_frame
		var start := Time.get_ticks_usec()
		RenderingServer.force_draw(false,1.0/60.0)
		var elapsed := Time.get_ticks_usec() - start
		metrics.append({"submit_draw_wall_usec":elapsed,"draw_calls":RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_DRAW_CALLS_IN_FRAME),"primitives":RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_PRIMITIVES_IN_FRAME),"video_memory_bytes":Performance.get_monitor(Performance.RENDER_VIDEO_MEM_USED),"texture_bytes":Performance.get_monitor(Performance.RENDER_TEXTURE_MEM_USED),"physics_active_objects":Performance.get_monitor(Performance.PHYSICS_3D_ACTIVE_OBJECTS),"process_static_bytes":Performance.get_monitor(Performance.MEMORY_STATIC)})
	var skeletons := 0
	for n: Node3D in field.find_children("*","Skeleton3D",true,false):
		if n.is_visible_in_tree(): skeletons+=1
	probes["performance"] = {"renderer":RenderingServer.get_video_adapter_name(),"method":RenderingServer.get_current_rendering_method(),"screen":[root.size.x,root.size.y],"scale_3d":root.scaling_3d_scale,"logical_canvas":[root.get_visible_rect().size.x,root.get_visible_rect().size.y],"visible_rigs":skeletons,"active_enemies":field.enemies.size(),"samples":metrics}

func run() -> void:
	capture=true
	video=OS.get_environment("T01_VIDEO")=="1"
	forest_out=OS.get_environment("T01_OUT")
	var dimensions := OS.get_environment("T01_SIZE").split("x")
	root.size=Vector2i(460,760) if dimensions.size()!=2 else Vector2i(dimensions[0].to_int(),dimensions[1].to_int())
	root.borderless = true
	if root.size.x >= 2000: root.position = Vector2i.ZERO
	field=load("res://field_opening.tscn").instantiate()
	root.add_child(field)
	current_scene=field
	camera=field.camera
	origin=Vector2(root.get_visible_rect().size)*Vector2(.22,.82)
	await _coast(18)
	if field.field_env.perimeter_stage == 0:
		await record_founding()
	else:
		for route_point: Array in CASES.west.slice(0,5):
			var ok := await _walk(Vector3(route_point[0],0,route_point[1]))
			_check(ok,"touch route reaches "+str(route_point))
		await record_view("west-1x")
		await _pinch()
		await record_view("west-2x")
		if video:
			await record_interactions()
	if OS.get_environment("T01_FAST_PROBE") != "1": await record_performance()
	var out := FileAccess.open(forest_out.path_join("projections.json"),FileAccess.WRITE)
	out.store_string(JSON.stringify({"frames":frames,"failures":failures,"probes":probes},"\t"))
	out.close()
	await SessionProof.drain_field_audio(self,field)
	field.queue_free()
	for i in 8: await process_frame
	quit(0 if failures.is_empty() else 1)
