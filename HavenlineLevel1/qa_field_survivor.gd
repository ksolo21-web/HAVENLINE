extends SceneTree
## Authored axe/trunk contact and one indivisible autonomous worker receipt.
## Supply a disposable profile for the world and a recording folder for optional live frames.
var game
var camera: Camera3D
var errors: Array[String] = []
var samples: Array[Dictionary] = []
var out := ""
func _initialize() -> void:
	call_deferred("run")
func check(ok: bool,message: String) -> void:
	if not ok: errors.append(message)
func buy(id: String) -> void:
	for kind: String in game.inventory.remaining(id):
		for j in int(game.inventory.remaining(id)[kind]):
			check(game.inventory.collect("worker-test-%s-%s-%d" % [id,kind,j],kind),"fixture collect")
			check(game.inventory.payment(id,kind,false),"fixture purchase")
	game._finish_purchase(id)

func capture(label: String, aim: Vector3, zoom: float) -> void:
	if out.is_empty(): return
	camera.position=aim+Vector3(2.5,1.55,3.11)
	camera.size=zoom
	camera.look_at(aim)
	await process_frame
	RenderingServer.force_draw()
	root.get_texture().get_image().save_jpg(out.path_join(label+".jpg"),.95)

func run() -> void:
	var isolated := preload("res://opening_save.gd").new()
	if not isolated.configure(OS.get_cmdline_user_args()):
		push_error("Worker audit needs a marked disposable Level 1 profile.")
		quit(2)
		return
	out = OS.get_environment("HAVENLINE_WORKER_EVIDENCE")
	game=preload("res://field_opening.tscn").instantiate()
	root.add_child(game)
	for i in 3: await process_frame
	game.persist_requested=false
	game.set_physics_process(false)
	game.set_process(false)
	var worker = game.survivor
	check(not game.rescue_survivor(),"cannot rescue before camp and survivor purchase")
	for id in ["center_hearth","expansion_1","storage_wood"]: buy(id)
	game._apply_hearth(true,false)
	check(not game.rescue_survivor(),"cannot rescue at a distance")
	game.actor.position=game.settlement_loop.works.PLOT_AT
	for i in 2:
		check(game.inventory.collect("worker-rescue-payment-%d" % i,"wood"),"seed physical payment")
	game.carry.sync(true)
	for i in 60: game.settlement_loop.works.advance(1./60.)
	check(game.inventory.settlement.survivor_paid and game.inventory.settlement.survivor_wood==2,"both wood physically spent on rescue plot")
	game.actor.position=worker.RESCUE
	worker.advance(1./60.)
	check(game.inventory.settlement.rescued,"rescue at actual purchased spot")
	game.actor.position=Vector3(-6.4,0,10.3)
	game.opening_hud.hide()
	camera=Camera3D.new()
	game.add_child(camera)
	camera.current=true
	camera.projection=Camera3D.PROJECTION_ORTHOGONAL
	await capture("01-survivor",worker.actor.position+Vector3.UP*.74,2.38)
	var last_phase := ""
	var last_hits := 0
	var original: Array = []
	var physical_token := ""
	var observations := {}
	
	for frame in 3600:
		var dt := 1./60.
		game.lifecycle.advance(dt)
		game.step_tree(dt)
		for g in game.gates: g.advance(dt,game.actor.position,.28)
		for token: String in game.drops: game.drops[token].age+=dt
		worker.advance(dt)
		var phase: String = worker.phase
		if phase == "chopping" and worker.swing_time > .35 and not observations.has("raise"):
			observations.raise=true
			await capture("02-two-hand-windup",worker.actor.position+Vector3(0,.85,.33),2.42)
		if worker.contacts > last_hits:
			samples.append({"frame":frame,"phase":phase,"contact":str(worker.contact_position),"count":worker.contacts})
			if last_hits == 0: await capture("03-blade-contact",worker.actor.position+Vector3(0,.76,.36),2.42)
			last_hits=worker.contacts
		if phase!=last_phase:
			samples.append({"frame":frame,"phase":phase,"feet":str(worker.actor.position),"tree":str(worker.tree.phase)})
			last_phase=phase
		if phase=="pickup" and original.is_empty():
			for tok: String in game.drops:
				var row: Dictionary=game.drops[tok]
				if row.from.distance_to(worker.tree.position+Vector3.UP*.29)<.04: original.append(tok)
		if phase=="carrying" and physical_token.is_empty():
			physical_token=game.inventory.settlement.worker_carry_token
			var checkpoint = game.Inventory.new()
			check(checkpoint.configure(game.inventory.costs) and checkpoint.restore(game.inventory.snapshot()) and checkpoint.settlement.worker_carry_token==physical_token,"cargo receipt survives saved inventory")
			await capture("04-log-bundle",worker.actor.position+Vector3.UP*.71,2.70)
		if phase=="carrying" and absf(worker.actor.position.z-game.gates[0].position.z)<.30:
			check(game.gates[0].angle > 1.29,"worker crossed closed leaves")
		if not out.is_empty() and phase=="chopping" and worker.contacts==0 and worker.swing_time>.54 and not observations.has("game"):
			observations.game=true
			game.camera.current=true
			game.camera.position=game.actor.position+Vector3(7,11,11)
			game.camera.look_at(game.actor.position)
			game.opening_hud.show()
			for z in [1,2]:
				game.set_zoom_ratio(z)
				await process_frame
				RenderingServer.force_draw()
				root.get_texture().get_image().save_jpg(out.path_join("gameplay-%dx.jpg" % z),.96)
			game.opening_hud.hide()
			camera.current=true
		if game.inventory.settlement.worker_deliveries > 0:
			await capture("05-storehouse-delivery",worker.actor.position+Vector3.UP*.68,3.78)
			break
	check(last_hits==3,"three deliberate two-hand axe contacts")
	check(original.size()==3,"one real pine yielded three floor drops")
	check(physical_token in original,"the worker carried one of the physical new drops")
	check(game.inventory.settlement.worker_deliveries==1 and game.inventory.stored.wood==1,"one delivered to the wood shelf")
	check(game.inventory.settlement.worker_receipts==[physical_token] and not game.drops.has(physical_token),"no duplicated carried receipt")
	var remaining:=0
	for token in original:
		if game.drops.has(token): remaining+=1
	check(remaining==2,"other two bundles remain ordinary pickups")
	check(not game.receive_worker_wood(),"no second claim after unload")
	print(JSON.stringify({"errors":errors,"states":samples,"token":physical_token,"remaining":remaining}))
	if not out.is_empty():
		var file:=FileAccess.open(out.path_join("worker-audit.json"),FileAccess.WRITE)
		file.store_string(JSON.stringify({"errors":errors,"states":samples,"token":physical_token,"remaining":remaining},"  "))
	if errors.is_empty():
		game._close_field()
	else:
		game.sound.stop_playback()
		await create_timer(.28).timeout
		quit(1)
