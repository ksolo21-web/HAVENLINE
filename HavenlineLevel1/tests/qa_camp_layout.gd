extends "res://tests/qa_storage_stream.gd"

const COOKER := "camp_cooker"
var layout
var log_entries: Array = []
var shot_dir := OS.get_environment("LAYOUT_PICTURES")
var film_dir := OS.get_environment("LAYOUT_MOVIE_FRAMES")
var recording := false
var film_tick := 0
var film_index := 0

func film() -> void:
	if not recording: return
	if film_tick%5==0:
		RenderingServer.force_draw(false)
		root.get_texture().get_image().save_jpg(film_dir.path_join("frame%03d.jpg"%film_index),.91)
		film_index+=1
	film_tick+=1

func hold(frames:int) -> void:
	if not recording: return
	for i in frames: await physics_frame

func tap(at:Vector2) -> void:
	touch(4,at,true)
	touch(4,at,false)
	await physics_frame

func click(at:Vector2) -> void:
	for down in [true,false]:
		var e:=InputEventMouseButton.new()
		e.button_index=MOUSE_BUTTON_LEFT
		e.position=at
		e.pressed=down
		root.push_input(e,true)
	await physics_frame

func open_layout(mouse:=false) -> void:
	var dock=field.opening_hud.camp_dock
	var menu_at:Vector2=dock.tabs.Camp.get_global_rect().get_center()
	if mouse:await click(menu_at)
	else:await tap(menu_at)
	for command in dock.commands:
		if command[1]!="move":continue
		var move_at:Vector2=command[0].get_global_rect().get_center()
		if mouse:await click(move_at)
		else:await tap(move_at)
		return

func photograph(label:String) -> void:
	if shot_dir.is_empty(): return
	await process_frame
	RenderingServer.force_draw()
	root.get_texture().get_image().save_jpg(shot_dir.path_join(label+".jpg"),.92)

func select_building(id:String,mouse:=false) -> void:
	var target:Vector3 = layout.on_ground(layout.center(id)) + Vector3.UP*float(layout.HEIGHT[id])*.48
	var at:Vector2=layout.map_camera.unproject_position(target)
	if mouse: await click(at)
	else: await tap(at)
	verify(id+" picked by tapping its actual artwork",layout.chosen==id)

func place_at(id:String, dest:Vector2, mouse:=false) -> void:
	var pixel:Vector2=layout.map_camera.unproject_position(layout.on_ground(dest))
	if mouse: await click(pixel)
	else: await tap(pixel)
	verify(id+" previews its physical destination",layout.preview_set and layout.candidate.distance_to(dest)<.01 and layout.candidate_reason.is_empty())
	if not layout.candidate_reason.is_empty(): print("REJECTED ",id," ",dest," ",layout.candidate_reason)
	if id==COOKER:
		await photograph("03-valid-cooker-footprint-and-service-aisle")
		await hold(55)
	if mouse: await click(layout.overlay.place.get_global_rect().get_center())
	else: await tap(layout.overlay.place.get_global_rect().get_center())
	verify(id+" committed by confirmation",layout.center(id).distance_to(dest)<.01 and layout.chosen.is_empty())

func outlet_markers(id:String) -> Array:
	match id:
		COOKER: return [field.lakeshore.cooker_input.global_position,field.lakeshore.cooker_output.global_position,field.lakeshore.apron_position(),field.lakeshore.output_apron_position(),field.lakeshore.guard.global_position]
		"storage_wood": return [field.depot.apron.global_position,field.depot.upgrade_mark.global_position,field.depot.bins.meat.global_position,field.depot.house.collision.global_position]
		"north_counter": return [field.counter.service_point.global_position,field.counter.customer_point.global_position,field.counter.payment_rest.global_position,field.counter.food_rest.global_position,field.counter.guard.global_position]
		_:
			var kind:String="wood" if id=="saw_bench" else "stone"
			return [field.processors.input_position(kind),field.processors.output_position(kind),field.processors.apron_position(kind),field.processors.guards[kind].global_position]

func live() -> void:
	# Seed only predecessors and gathered inputs. Buy the subject cooker through the game's
	# normal approach, visible spending, receipt, and completion sequence.
	for id in ["center_hearth","expansion_1","storage_wood","storage_stone","storage_meat","expansion_2"]:
		open_site(id)
	field.camp_layout.overlay.sync()
	field.actor.global_position=Vector3(.65,0,-3.20)
	camera=field.camera
	supply("wood",12)
	supply("stone",8)
	field.carry.sync()
	field._persist_world()
	await photograph("00-cooker-unpaid")
	verify("Unowned cooker cannot be placed",not layout.relocate(COOKER,Vector2(4.75,2.75)))
	var target=field.offer_floors[COOKER].global_position+Vector3(0,0,1.36)
	await walk_to(target)
	steer(Vector2.ZERO)
	for i in 128: await physics_frame
	verify("Cooker paid normally with the exact 120 wood and 80 stone",field.inventory.complete(COOKER) and field.inventory.build_order.count(COOKER)==1 and field.lakeshore.available)
	if not field.inventory.complete(COOKER): print("MISSING RECEIPT ",field.actor.position," ",field.inventory.paid[COOKER])
	await photograph("01-cooker-paid-gameplay")
	recording=not film_dir.is_empty()
	if recording: physics_frame.connect(film)
	await hold(35)
	await open_layout()
	verify("Touch opens layout and liberates joystick",layout.active and field.touch_id<0)
	await hold(32)
	await select_building(COOKER)
	await hold(26)
	var before:=outlet_markers(COOKER)
	var home:Vector2=layout.center(COOKER)
	var bad:=Vector2(0,0)
	await tap(layout.map_camera.unproject_position(layout.on_ground(bad)))
	verify("Overlap rejected before it can persist",not layout.candidate_reason.is_empty() and layout.overlay.place.disabled and layout.center(COOKER)==home)
	await photograph("02-blocked-by-furnace")
	await hold(55)
	await tap(layout.overlay.place.get_global_rect().get_center())
	verify("Invalid destination leaves all equipment untouched",layout.snapshot().is_empty() and layout.center(COOKER)==home)
	var dest:=Vector2(4.75,2.75)
	await place_at(COOKER,dest)
	await hold(45)
	var after:=outlet_markers(COOKER)
	var translated:=true
	for i in before.size(): translated=translated and (after[i]-before[i]).distance_to(layout.on_ground(dest-home))<.001
	verify("Model, guard, hopper, outfeed and both worker aprons move as a unit",translated)
	await tap(layout.overlay.done.get_global_rect().get_center())
	await hold(30)
	recording=false
	verify("Exit returns player's gameplay camera and controls",not layout.active and field.camera.current and field.opening_hud.is_visible_in_tree())
	# Walk to the new rear side carrying real meat, and wait for the unattended cooker.
	field.actor.global_position=Vector3(5.0,0,-.45)
	supply("meat",2)
	field.carry.sync()
	await walk_to(Vector3(4.75,0,1.52))
	for i in 260: await physics_frame
	verify("Meat handed off at relocated cooker produces a real meal",int(field.inventory.settlement.cooked)>0)
	await photograph("04-serving-relocated-cooker")
	# Real touchscreen pinch in the ordinary character camera.
	var viewport_center:=root.get_visible_rect().get_center()
	touch(0,viewport_center-Vector2(47,0),true)
	touch(1,viewport_center+Vector2(47,0),true)
	var drag:=InputEventScreenDrag.new()
	drag.index=1
	drag.position=viewport_center+Vector2(165,0)
	drag.relative=Vector2(118,0)
	drag.screen_relative=drag.relative
	root.push_input(drag,true)
	touch(0,viewport_center-Vector2(47,0),false)
	touch(1,drag.position,false)
	verify("Gameplay pinch still works after moving",field.get_zoom_ratio()>1.5)
	await photograph("04b-cooker-at-gameplay-pinch")
	field.set_zoom_ratio(1.)

	field.actor.global_position=Vector3(1.72,0,1.8)
	# Machine checkout does not turn these into free permanent unlocks. Seed their own recipes separately.
	for id in ["saw_bench","quarry_drill","watchtower","orbit_upgrade"]:open_site(id)
	for i in 55:await physics_frame
	await open_layout(true)
	verify("Mouse opens identical layout controls",layout.active)
	for row in [["saw_bench",Vector2(-3.5,2.5)],["quarry_drill",Vector2(7.75,-6.25)],["north_counter",Vector2(4.,-9.)],["storage_wood",Vector2(4.50,-2.50)]]:
		var id:String=row[0]
		var old:Vector2=layout.center(id)
		before=outlet_markers(id)
		await select_building(id,true)
		await place_at(id,row[1],true)
		after=outlet_markers(id)
		translated=true
		for i in before.size(): translated=translated and (after[i]-before[i]).distance_to(layout.on_ground(row[1]-old))<.001
		verify(id+" inputs, outputs and guard follow",translated)
	for row in [["center_hearth",Vector2(-2.75,-2.5)],["watchtower",Vector2(8.,3.5)]]:
		await select_building(row[0])
		await place_at(row[0],row[1])
	verify("Relocated furnace light, art and solid footing stay together",layout.xz(field.field_env.hearth_footprint.global_position)==Vector2(-2.75,-2.5) and field.field_env.coal_glow.global_position.distance_to(field.field_env.hearth_footprint.global_position)<1.1)
	verify("Tower's paid physical footings stay on the moved defense side",layout.xz(field.defense_tower.guard.global_position)==Vector2(8,3.5) and field.defense_tower.guard.collision_layer==1)
	await photograph("05-paid-equipment-and-counter-rearranged")
	await click(layout.overlay.done.get_global_rect().get_center())
	verify("Service point and queue meet across the relocated north fence bay",field.counter.at_service(field.counter.service_point.global_position) and field.counter.customer_point.global_position.z<field.field_env.COURTS.back().y and field.field_env.counter_center_x==4.)
	verify("Storehouse at new position accepts side loading",field.depot.at_loading_area(field.depot.apron.global_position))
	# Use the relocated doors, and serve an actual waiting customer at the new north-wall slot.
	var load_start:Vector3=field.depot.apron.global_position
	field.actor.global_position=load_start+Vector3(0,0,1.67)
	supply("meat",2)
	field.carry.sync()
	var stock_before:=int(field.inventory.stored.meat)
	await walk_to(load_start)
	for i in 100: await physics_frame
	verify("Moving up to the relocated house stocks its real FOOD shelf",int(field.inventory.stored.meat)>=stock_before+2)
	var counter_tip:Vector3=field.counter.service_point.global_position
	field.actor.global_position=counter_tip+Vector3(0,0,2.)
	var served_before:=int(field.inventory.settlement.served)
	await walk_to(counter_tip)
	for i in 250: await physics_frame
	verify("A customer pays for the real roast across the relocated fence",int(field.inventory.settlement.served)>served_before)
	await photograph("05b-service-at-relocated-north-counter")
	verify("Spawn, defense side and gate are protected",not layout.reason("center_hearth",Vector2(1.72,1.8)).is_empty() and not layout.reason("watchtower",Vector2(-3,1)).is_empty() and not layout.reason("center_hearth",Vector2(0,4)).is_empty())
	var durable:Dictionary=layout.snapshot()
	var start:=Vector3(-4.33,0,-2.50)
	var goal:=Vector3(-1.1,0,-2.50)
	var next: Vector3=layout.next_waypoint(start,goal,.26)
	verify("Worker detours around the moved furnace without crossing its body",next.distance_to(goal)>.15 and next.distance_to(start)>.2 and absf(next.z+2.5)>.8)
	verify("Malformed layout restore rejected without partial mutation",not layout.restore({"camp_cooker":[10,"bad"]}) and layout.snapshot()==durable)
	field._persist_world()
	log_entries.append(durable)

func upgrade() -> void:
	for id in ["center_hearth","expansion_1","storage_wood"]: open_site(id)
	for i in 60: await physics_frame
	field.actor.global_position=Vector3(1.72,0,1.8)
	var old_mark:Vector3=field.depot.upgrade_mark.global_position
	await open_layout()
	await select_building("storage_wood")
	await place_at("storage_wood",Vector2(-3.50,-3.0))
	await tap(layout.overlay.done.get_global_rect().get_center())
	var new_mark:Vector3=field.depot.upgrade_mark.global_position
	supply("wood",8)
	supply("stone",6)
	field.carry.sync()
	camera=field.camera
	field.actor.global_position=new_mark+Vector3(-.12,0,2.43)
	await walk_to(new_mark)
	for i in 90: await physics_frame
	verify("Storehouse tier grows at the moved site through the moved upgrade plot",field.inventory.complete("storage_stone") and field.depot.house.tier==2 and layout.center("storage_wood")==Vector2(-3.50,-3.0) and new_mark.distance_to(old_mark)>.6)
	log_entries.append(layout.snapshot())

func cold() -> void:
	verify("Cold process recovers relocated cooker, counter and storehouse",layout.center(COOKER)==Vector2(4.75,2.75) and layout.center("north_counter")==Vector2(4,-9) and layout.center("storage_wood")==Vector2(4.5,-2.5))
	verify("Cold process recovers saw and drill collision",layout.center("saw_bench")==Vector2(-3.5,2.5) and layout.center("quarry_drill")==Vector2(7.75,-6.25))
	verify("Cold process recovers moved furnace and defending tower",layout.center("center_hearth")==Vector2(-2.75,-2.5) and layout.center("watchtower")==Vector2(8.,3.5))
	verify("Reloaded receipts and cooked meal survive relocation",int(field.inventory.settlement.cooked)>0 and field.inventory.complete(COOKER) and not field.persist_blocked)
	await photograph("06-cold-reload")
	log_entries.append(layout.snapshot())

func run() -> void:
	field=Scene.instantiate()
	root.add_child(field)
	current_scene=field
	camera=field.camera
	layout=field.camp_layout
	await physics_frame
	if "--layout-cold" in OS.get_cmdline_user_args(): await cold()
	elif "--layout-tier" in OS.get_cmdline_user_args(): await upgrade()
	else: await live()
	field.set_physics_process(false)
	field.carry.set_physics_process(false)
	await Session.drain_field_audio(self,field)
	field.queue_free()
	for i in 4: await process_frame
	print("CAMP_LAYOUT ",JSON.stringify({"checks":checks,"placements":log_entries}))
	quit(1 if checks.values().has(false) or log_entries.is_empty() else 0)
