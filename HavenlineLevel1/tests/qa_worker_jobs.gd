extends SceneTree
const Session = preload("res://tests/lifecycle_test_profile.gd")
const Save = preload("res://field_save.gd")
const SELF := "res://tests/qa_worker_jobs.gd"
var game
var worker
var errors := PackedStringArray()
var checks := PackedStringArray()
var scenes := {}
var phases := []
var observations := {}
var output := OS.get_environment("WORKER_PROOF")
var timelapsed := 0.
var recording := OS.get_environment("WORKER_VISUALS") == "1"
var render_next := 0.

func _initialize() -> void: call_deferred("run")

func check(ok: bool, label: String) -> void:
	checks.append(label)
	if not ok: errors.append(label)

func setup_camp(leave_tower := false) -> void:
	var book = game.inventory
	for id: String in ["center_hearth","expansion_1","storage_wood","storage_stone","storage_meat","expansion_2","camp_cooker","saw_bench","quarry_drill","watchtower","orbit_upgrade"]:
		if leave_tower and id == "watchtower": continue
		for kind: String in book.remaining(id):
			for i in int(book.remaining(id)[kind]):
				book.collect("buy-%s-%s-%d"%[id,kind,i],kind)
				book.payment(id,kind,false)
	game._apply_hearth(true,false)
	for i in book.survivor_cost: book.collect("rescue-wood-%d"%i,"wood")
	book.carried.wood -= book.survivor_cost
	book.settlement.survivor_wood = book.survivor_cost
	book.settlement.survivor_paid = true
	game.actor.position = worker.RESCUE
	worker.advance(1./60.)
	check(book.settlement.rescued,"paid helper physically rescued")
	game.actor.position=Vector3(4,0,1)
	game.camera.position=game.actor.position+game.camera_follow_offset
	for kind: String in ["stone","meat","wood"]:
		for i in 2:
			book.collect("ingredients-%s-%d"%[kind,i],kind)
			book.deposit(kind)
	game._inventory_changed()

func tick(dt: float) -> void:
	game.lifecycle.advance(dt)
	game.resource_rock.advance(dt)
	game.step_tree(dt)
	game.step_technical_gates(dt)
	game._step_drops(dt)
	game.settlement_loop.advance(dt)
	timelapsed += dt
	if phases.is_empty() or phases.back().phase != worker.phase:
		phases.append({"second":snappedf(timelapsed,.01),"phase":worker.phase,"x":worker.actor.position.x,"z":worker.actor.position.z})

func still(key: String) -> void:
	if not recording or output.is_empty() or scenes.has(key): return
	scenes[key] = true
	var game_camera: Camera3D = game.camera
	observations[key] = {"player_position":str(game.actor.position),"worker_position":str(worker.actor.position),"worker_rotation_y":worker.actor.rotation.y,"zoom":game.get_zoom_ratio(),"viewport":str(root.size),"player_at_counter":game.counter.at_service(game.actor.position),"worker_serving":game.counter.worker_serving,"served":game.inventory.settlement.served}
	if key.begins_with("500-of-each"):
		var top_y := INF
		for group: Array in worker.pack.pieces.values():
			for resource: Node3D in group:
				if not resource.is_visible_in_tree(): continue
				for mesh:MeshInstance3D in resource.find_children("*","MeshInstance3D",true,false):
					var box: AABB = mesh.get_aabb()
					for corner in 8:
						top_y = minf(top_y,game_camera.unproject_position(mesh.to_global(box.get_endpoint(corner))).y)
		var boot_y := game_camera.unproject_position(worker.actor.global_position).y
		var head_y := game_camera.unproject_position(worker.actor.global_position + Vector3.UP*1.50).y
		observations[key].projected_body_px=boot_y-head_y
		observations[key].projected_loaded_heights=(boot_y-top_y)/(boot_y-head_y)
		observations[key].display_counts=worker.pack.presented.duplicate()
	await process_frame
	RenderingServer.force_draw()
	root.get_texture().get_image().save_jpg(output.path_join(key+".jpg"),.9)

func film() -> void:
	if not recording or output.is_empty() or timelapsed < render_next: return
	render_next=timelapsed+.075
	await process_frame
	RenderingServer.force_draw()
	var folder := output.path_join("frames")
	DirAccess.make_dir_recursive_absolute(folder)
	root.get_texture().get_image().save_jpg(folder.path_join("f%06d.jpg"%roundi(timelapsed*60)),.84)

func test_capacity() -> void:
	var book = game.inventory
	worker.actor.position=game.depot.APRON+Vector3(0,0,.9)
	game.actor.position=worker.actor.position+Vector3(2.7,0,.8)
	game.camera.position=game.actor.position+game.camera_follow_offset
	var at:Vector3=worker.actor.position
	for kind: String in book.KINDS:
		for i in 49: book.collect("worker-stock-%s-%d"%[kind,i],kind)
		book.carried[kind] -= 49
		book.settlement.worker_load[kind] = 49
		game._make_drops(kind,at,2)
	for d: Dictionary in game.drops.values(): d.age=.5
	worker._sweep_drops()
	for kind: String in book.KINDS:
		check(book.settlement.worker_load[kind]==50 and worker.worker_space(kind)==0,"500 raw "+kind+" cap")
		var units: Array=worker.pack.pieces[worker.pack.HAND+"/"+kind]
		check(not units.is_empty() and units[0].visible and units[0].get_meta("field_material") == kind,"own visible rack lane "+kind)
	await still("500-of-each-gameplay")
	if recording:
		var packed_lanes: Dictionary = worker.pack.presented.duplicate()
		var away: Vector3 = -game.camera.global_basis.z
		worker.actor.rotation.y=atan2(away.x,away.z)
		worker.pack.sync()
		await still("500-of-each-rear")
		game.actor.position = worker.actor.position + Vector3(-1.05,0,-1.40)
		game.camera.position = game.actor.position + game.camera_follow_offset
		game.set_zoom_ratio(2.0)
		worker.pack.sync()
		await still("500-of-each-pinch")
		game.set_zoom_ratio(1.0)
		# Walk a short flank approach with the real forester gait and pack attachment.
		var side := worker.actor.global_basis.x as Vector3
		var end:Vector3 = worker.actor.position+side*.68
		for frame in 18: worker._walk(end,1./60.,true)
		await still("500-of-each-flank-moving")
		for pose in ["500-of-each-rear","500-of-each-pinch","500-of-each-flank-moving"]:
			check(observations[pose].display_counts == packed_lanes,"all material rows retained across "+pose)
	check(game.drops.size()==6,"one excess pickup of every family stays on snow")
	var copy=game.Inventory.new()
	check(copy.configure(book.configured_costs) and copy.restore(book.snapshot()),"all six independent full loads conserve receipts")
	var bad=book.snapshot()
	bad.settlement.worker_load.meat+=1
	bad.collected["invalid-overflow"]="meat"
	check(not copy.restore(bad),"501+ units cannot restore as a valid load")
	worker._begin_bin_delivery()
	worker.actor.position=game.depot.APRON
	var before: Dictionary=book.stored.duplicate()
	for frame in 75: tick(1./60.)
	for kind: String in book.KINDS:
		var outbound := 1+int(book.settlement.worker_load[kind]) if book.settlement.worker_supply == kind else 0
		check(book.stored[kind]+outbound == before[kind]+50 and (book.settlement.worker_load[kind]==0 or outbound>0),"bulk shelf delivery "+kind)
	check(copy.restore(book.snapshot()),"bulk transfer balanced after landing")

func test_assistance() -> void:
	var book = game.inventory
	worker.actor.position = game.depot.APRON
	check(not worker._prepare_assistance(),"worker cannot start an unpurchased project")
	var tower = game.Progress.TOWER
	for kind: String in book.remaining(tower):
		for i in book.remaining(tower)[kind]:
			book.collect("assistance-%s-%d"%[kind,i],kind)
		if kind == "wood": book.payment(tower,kind,false,1)
		var remaining := int(book.remaining(tower)[kind])
		book.deposit(kind,remaining)
	check(worker._prepare_assistance(),"worker takes an already-open commission at the storehouse")
	var before: Dictionary = book.settlement.worker_load.duplicate()
	check(before.wood > 0 and before.stone > 0 and before.meat == 0,"takes only the outstanding timber and stone from stock")
	for i in 1500:
		tick(1./60.)
		if book.complete(tower): break
	check(book.complete(tower),"worker physically finishes the owner's partially funded tower")
	check(book.build_order.count(tower)==1 and book.settlement.worker_load.wood == 0,"one tower receipt and materials consumed once")
	var copy=game.Inventory.new()
	check(copy.configure(book.configured_costs) and copy.restore(book.snapshot()),"assisted purchase round-trips without fictitious resource income")

func watch_counter() -> void:
	# Move to the interior aisle with the same virtual stick used on Android.
	# Deliberately stop outside the wider cashier interaction band.
	var target := Vector3(3.2,0,-4.75)
	var origin := Vector2(root.size.x*.28,root.size.y*.76)
	var touch := InputEventScreenTouch.new()
	touch.index = 0
	touch.position = origin
	touch.pressed = true
	root.push_input(touch,true)
	game.set_physics_process(true)
	for tick_index in 155:
		var delta: Vector3 = target-game.actor.position
		if delta.length() < .36: break
		var right: Vector3 = game.camera.global_basis.x
		var near := right.cross(Vector3.UP)
		var heading := Vector2(delta.dot(right),delta.dot(near)).normalized()
		var drag := InputEventScreenDrag.new()
		drag.index = 0
		drag.position = origin+heading*75.0
		drag.relative = heading*10.
		drag.screen_relative = drag.relative
		root.push_input(drag,true)
		await physics_frame
	touch.pressed = false
	root.push_input(touch,true)
	for i in 28: await physics_frame
	game.set_physics_process(false)
	check(game.actor.position.distance_to(target)<.75 and not game.counter.at_service(game.actor.position),"normal phone stick reached viewing aisle outside cashier zone")

func simulate(stop: String) -> void:
	var journal: Dictionary = game.inventory.settlement
	var parked:Vector3=game.actor.position
	for i in 60*260:
		tick(1./60.)
		if recording and worker.phase in ["supply_out","meal_collect","meal_serve"]:
			await film()
		if worker.phase=="supply_out" and not journal.worker_supply.is_empty(): await still("01-deliver-"+journal.worker_supply)
		if journal.worker_meal==1 and not game.counter.worker_serving:
			await still("02-worker-meal")
			if stop == "interrupt":
				check(journal.served==0,"before counter payment no cash granted")
				game._persist_world()
				if not output.is_empty():
					DirAccess.copy_absolute(game.field_save.directory.path_join(Save.PRIMARY),output.path_join("Earned-worker-meal.save.json"))
				break
		if game.counter.worker_serving: await still("03-worker-counter")
		if journal.served > 0:
			await still("04-paid-order")
			if stop == "service" and not game.counter.leaving.is_empty(): break
		if stop == "jobs" and journal.processed_wood>0 and journal.processed_stone>0 and journal.served>0 and journal.worker_deliveries>0 and phases.any(func(x): return x.phase=="mining") and phases.any(func(x): return x.phase=="bulk_return"): break
	check(game.actor.position.is_equal_approx(parked),"player stayed clear during survivor work")
	check(not game.persist_blocked,"worker jobs maintained valid save")
	if stop == "interrupt":
		check(journal.worker_meal==1,"survivor independently collected the cooked order")
	elif stop=="service":
		check(journal.served==1 and journal.worker_meal==0 and not game.counter.leaving.is_empty(),"resumed helper served one physical guest and collected cash once")
	else:
		check(journal.worker_deliveries>=1,"standing tree harvested and physically delivered")
		check(journal.processed_wood>0 and journal.processed_stone>0,"worker supplied independently purchased saw and drill")
		check(journal.cooked>0 and journal.served>0,"worker supplied paid cooker and served the waiting customer")
		check(phases.any(func(x): return x.phase=="mining"),"worker visibly mined a real bank")
		check(phases.any(func(x): return x.phase=="bulk_return"),"worker returning with physically collected resource drops")
		var final_book=game.Inventory.new()
		check(final_book.configure(game.inventory.configured_costs) and final_book.restore(game.inventory.snapshot()),"gather, production and customer payments conserved")

func run() -> void:
	var args:=OS.get_cmdline_user_args()
	var mode: String = args[-1] if not args.is_empty() else ""
	if not mode in ["jobs","capacity","interrupt","service","assist"]:
		var status:=0
		for group in [["jobs"],["capacity"],["assist"],["interrupt","service"]]:
			var directory:=Session.make_directory()
			for step: String in group:
				if status==0: status=Session.child(SELF,directory,step)
			Session.remove_owned(directory)
		quit(status)
		return
	if not Save.Profile.new().configure(args):
		quit(2)
		return
	game=load("res://field_opening.tscn").instantiate()
	root.add_child(game)
	game.set_physics_process(false)
	game.set_process(false)
	for i in 3: await process_frame
	worker=game.survivor
	if mode != "service": setup_camp(mode == "assist")
	if mode == "assist":
		test_assistance()
	elif mode == "capacity":
		await test_capacity()
	else:
		if mode=="service":
			check(game.inventory.settlement.worker_meal==1 and worker.phase=="meal_serve","cold load retains cooked order in worker hands")
			if recording: await watch_counter()
		await simulate(mode)
	if checks.size() < 4: errors.append("scenario did not exercise the required transactions")
	var result={"mode":mode,"checks":checks,"errors":errors,"elapsed":timelapsed,"phases":phases,"observations":observations,"ledger":game.inventory.settlement}
	print("Worker jobs ",mode," ",checks.size()," checks; failures ",errors)
	if not output.is_empty():
		var f:=FileAccess.open(output.path_join(mode+".json"),FileAccess.WRITE)
		f.store_string(JSON.stringify(result,"\t")+"\n")
	await Session.drain_field_audio(self,game)
	game.queue_free()
	for i in 3: await process_frame
	quit(0 if errors.is_empty() else 1)
