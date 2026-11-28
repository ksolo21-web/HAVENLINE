extends "forest_route_support.gd"

var accessible := OS.get_environment("T01_ACCESSIBLE")=="1"
var fit_states := {}
var canvas_nominal := Vector2i.ZERO

func tap(at: Vector2) -> void:
	touch(5,at,true)
	await process_frame
	touch(5,at,false)
	for i in 4: await process_frame

func command(dock: Control, id: String) -> void:
	for page in 8:
		var next: Control
		for button in dock.commands:
			if button[1]==id:
				await tap(button[0].get_global_rect().get_center())
				return
			if button[1]=="list_next": next=button[0]
		if not next: break
		await tap(next.get_global_rect().get_center())
	_check(false,"Can reach "+id+" by touch")

func choose_accessibility() -> void:
	var hud:Control=field.opening_hud
	var dock: Control=hud.camp_dock
	await tap(dock.tabs.Camp.get_global_rect().get_center())
	await command(dock,"accessibility")
	_check(dock.tab=="Accessibility","Can open accessibility during live field play")
	for option in ["large_ui","right_stick","reduced_motion","captions"]:
		await command(dock,"access:"+option)
		_check(field.access.values[option],"Selected from visible accessibility menu "+option)
	await tap(dock.close.get_global_rect().get_center())
	_check(dock.tab.is_empty() and root.content_scale_factor>1.0,"Large HUD applies to actual gameplay canvas")
	recenter_stick()

func recenter_stick() -> void:
	var hud:Control=field.opening_hud
	var control: Control=hud.get_node("MovementThumbstick")
	if field.access.values.right_stick:
		origin=control.position
		_check(origin.x>hud._safe_rect().get_center().x and hud._safe_rect().has_point(origin),"Right stick remains on reachable snow-play surface")
	else:
		origin=Vector2(root.get_visible_rect().size)*Vector2(.22,.77)

func player_clear_of_hud(key: String) -> void:
	var hud:Control=field.opening_hud
	var feet:Vector3=field.actor.global_position
	var hat:=camera.unproject_position(feet+Vector3.UP*1.55)
	var boot:=camera.unproject_position(feet)
	var blocked:=false
	for control:Control in [hud.objective,hud.camp_dock.build,hud.camp_dock.nav,hud.camp_dock.pack_button]:
		if control.is_visible_in_tree() and (control.get_global_rect().has_point(hat) or control.get_global_rect().has_point(boot)):
			blocked=true
	var in_view: bool=hud._safe_rect().has_point(hat) and hud._safe_rect().has_point(boot)
	fit_states[key]={"heads_and_boots_in_safe_canvas":in_view,"hud_covering_character":blocked,"zoom":field.get_zoom_ratio(),
		"stick":[origin.x,origin.y],"raster":[root.size.x,root.size.y]}
	_check(in_view and not blocked,"Character stays clear of HUD "+key)

func run() -> void:
	route_name=OS.get_environment("T01_ROUTE")
	capture=OS.get_environment("T01_IMAGES")=="1"
	forest_out=OS.get_environment("T01_OUT")
	var dims:=OS.get_environment("T01_SIZE").split("x")
	canvas_nominal=Vector2i(dims[0].to_int(),dims[1].to_int())
	root.size=canvas_nominal
	field=load("res://field_opening.tscn").instantiate()
	root.add_child(field)
	current_scene=field
	camera=field.camera
	await _coast(18)
	recenter_stick()
	report.camera_basis=camera.global_basis
	_check(field.field_ready and not field.persist_blocked,"Normal main scene opens with a writable isolated profile")
	_check(field.graphics.preset_name()=="Ultra","Default Ultra mode at the live scene")
	report.start=pt(field.actor.global_position)
	report.camp_stage_at_start=field.field_env.perimeter_stage
	if accessible: await choose_accessibility()
	report.accessibility=field.access.values.duplicate()
	forest_started=true
	player_clear_of_hud("entry")
	await _view("00-entry")
	var points: Array=CASES[route_name].duplicate(true)
	if field.field_env.perimeter_stage==0 and route_name=="south":
		points[0]=[1.2,7.2]
	for i in points.size():
		var target:=Vector3(points[i][0],0,points[i][1])
		var success:=await _walk(target)
		_record("waypoint " + str(i+1),target,success)
		_check(success and field.touch_id<0,"Touch reaches and releases at waypoint "+str(i+1))
		_check(camera==root.get_camera_3d() and camera.global_basis.is_equal_approx(report.camera_basis),"One stable camera at waypoint "+str(i+1))
		if i==4:
			await _coast(8)
			player_clear_of_hud("forest-edge")
			await _view("01-forest-edge")
			await _pinch()
			var factor:float=field.get_zoom_ratio()
			report.pinch_factor=factor
			_check(factor>1.8 and field.touch_id<0,"Two touch pinch preserves control and reaches 2×")
			player_clear_of_hud("forest-edge-pinch")
			await _view("02-forest-edge-pinch")
			field.set_zoom_ratio(1.0)
			recenter_stick()
	if OS.get_environment("T01_REGROW")=="1": await _regrowth_trial()
	if accessible and OS.get_environment("T01_FOLD")=="1":
		await _coast(6)
		recenter_stick()
		steer(Vector2.RIGHT)
		await _step()
		root.size=Vector2i(840,942) if canvas_nominal.y>canvas_nominal.x*2 else Vector2i(540,1260)
		for i in 8: await process_frame
		_check(field.touch_id<0 and field.trial_camera.fingers.is_empty(),"Resize releases the old forest gesture")
		steer(Vector2.ZERO)
		recenter_stick()
		player_clear_of_hud("after-fold")
		var before:Vector3=field.actor.global_position
		steer(Vector2.LEFT)
		for i in 22:await _step()
		await _coast(7)
		_check(before.distance_to(field.actor.global_position)>.45 and field.touch_id<0,"Fresh right-stick input works after fold")
		await _view("03-after-fold")
	report.erase("camera_basis")
	report.route=route_name
	report.failures=failures
	report.checkpoints=witness
	report.hud_layout=fit_states
	report.harvested_records=timings
	report.total_local_records=field.forest.records.size()
	report.high_open=high_open
	report.window=[root.size.x,root.size.y]
	report.persistence=not field.persist_blocked
	var out:=FileAccess.open(forest_out.path_join("witness.json"),FileAccess.WRITE)
	out.store_string(JSON.stringify(report,"\t"))
	out.close()
	print("FOREST_ROUTE ",JSON.stringify({"route":route_name,"waypoints":witness.size(),"failures":failures,"regrowth":report.get("regrowth",{}),"cutaway":high_open,"pinch":report.pinch_factor}))
	await SessionProof.drain_field_audio(self,field)
	field.queue_free()
	for i in 8: await process_frame
	quit(1 if not failures.is_empty() else 0)
