extends SceneTree

const Scene = preload("res://field_opening.tscn")
const Rules = preload("res://field_progression.gd")
var game
var checks := {}
var launched := 0
var clock := 0

func _initialize() -> void: call_deferred("run")

func check(id: String, value: bool) -> void:
	checks[id] = value
	if not value: push_error(id)

func approach(id: String, n: int, offset := Vector3.ZERO) -> void:
	game.actor.global_position = game.carry.receivers[id].global_position + offset
	for i in n:
		game._step_receivers()
		if game.carry.flights.size()>0: launched+=1
		game.carry.advance(1./60.)
		clock+=1

func exercise_partial_restart() -> void:
	var is_read := "--house-partial-read" in OS.get_cmdline_user_args()
	if not is_read:
		for kind in ["wood","stone"]:
			for i in (7 if kind=="wood" else 1):
				game.inventory.collect("limited-%s-%s"%[kind,i],kind)
		game.carry.sync()
		approach(Rules.HEARTH,120)
		game.reveal_countdown=-1.
		game._apply_hearth(true,false)
		approach(Rules.FIRST,120)
		approach("storage_wood",120,Vector3(.55,0,0))
	check("Partial starter balance survives without free construction",game.inventory.paid.storage_wood.wood==1 and game.inventory.remaining("storage_wood").wood==1 and game.depot.house.tier==0 and game.depot.offer=="storage_wood")
	if is_read:
		check("Reopening on apron waits for new visit",game.depot.visit=="done")
		game.inventory.collect("last-starter-timber","wood")
		approach("storage_wood",120,Vector3(.55,0,0))
		check("Reload cannot spend without departure",game.inventory.paid.storage_wood.wood==1)
		game.actor.position=Vector3.ZERO
		game._step_receivers()
		approach("storage_wood",120,Vector3(.55,0,0))
		check("Existing partial consumed exactly once after re-entry",game.depot.house.tier==1 and game.inventory.paid.storage_wood.wood==2 and game.inventory.carried.wood==0 and game.depot.offer=="storage_stone")
	print(JSON.stringify({"partial_restart":checks}))
	game.sound.stop_playback()
	game.queue_free()
	for i in 4: await process_frame
	quit(1 if checks.values().has(false) else 0)

func run() -> void:
	game=Scene.instantiate()
	root.add_child(game)
	game.set_physics_process(false)
	game.carry.set_physics_process(false)
	if "--house-partial-read" in OS.get_cmdline_user_args() or "--house-partial-write" in OS.get_cmdline_user_args():
		await exercise_partial_restart()
		return
	if "--native-resume-final" in OS.get_cmdline_user_args() or "--native-resume-legacy" in OS.get_cmdline_user_args():
		var sequence: Array = ["storage_meat","storage_stone","storage_wood"] if "--native-resume-legacy" in OS.get_cmdline_user_args() else Rules.STORAGE
		var expected_order := [Rules.HEARTH,Rules.FIRST]+sequence+[Rules.SECOND,Rules.TOWER,Rules.AXES]
		check("Independent native app slot reopened",game.field_save.native_profile and not game.persist_blocked)
		check("All eight purchases restored in original order",game.inventory.build_order==expected_order)
		check("Restored court has one advanced storehouse and all paid bays",game.field_env.perimeter_stage==3 and game.depot.house.tier==3 and game.depot.bins.values().all(func(a):return a.visible) and game.offer_floors.values().all(func(f):return not f.visible))
		print(JSON.stringify({"native_restart":checks}))
		game.sound.stop_playback()
		game.queue_free()
		for i in 4: await process_frame
		quit(1 if checks.values().has(false) else 0)
		return
	check("Actual game fresh save",not game.persist_blocked and game.inventory.build_order.is_empty())
	for kind in ["wood","stone","meat"]:
		for i in 30: game.inventory.collect(kind+str(i),kind)
	game.carry.sync()
	check("Only the central hearth payment is initially visible",game.field_env.buy_anchor.visible and game.offer_floors.values().all(func(f):return not f.is_visible_in_tree()))
	approach(Rules.HEARTH,100)
	check("Payment commits before hearth reveal",game.inventory.complete(Rules.HEARTH) and game.reveal_countdown>0.)
	game.reveal_countdown=-1.
	game._apply_hearth(true,true)
	check("Hearth reveals only first expansion and no storage",game.offer_floors[Rules.FIRST].is_visible_in_tree() and not game.depot.apron.is_visible_in_tree() and not game.depot.house.visible and not game.field_env.upgrade_anchor.is_visible_in_tree() and not game.offer_floors[Rules.AXES].is_visible_in_tree())
	approach(Rules.FIRST,130)
	check("Single starter offer after first expansion",game.depot.offer=="storage_wood" and game.depot.apron.visible and not game.depot.house.visible and not game.offer_floors[Rules.SECOND].is_visible_in_tree())
	for kind: String in ["wood","stone","meat"]:
		var id := "storage_"+kind
		game.actor.position=Vector3.ZERO
		game._step_receivers()
		var before_store: Dictionary=game.inventory.stored.duplicate()
		approach(id,120,Vector3(.55,0,0))
		check(id+" purchased without chaining next tier",game.inventory.complete(id) and game.depot.bins[kind].visible and game.depot.visit=="done")
		check(id+" keeps only the authored apron visible",game.depot.apron.get_children().all(func(part):return not part.visible))
		var order: Array = game.inventory.build_order.duplicate()
		var paid_stock: Dictionary = game.inventory.stored.duplicate()
		approach(id,160,Vector3(-.55,0,0))
		check(id+" crossing the apron still requires leaving",game.inventory.build_order==order and game.depot.visit=="done" and game.inventory.stored==paid_stock)
		game.actor.position=Vector3.ZERO
		game._step_receivers()
		approach(id,420,Vector3(-.55,0,0))
		check(id+" left-side re-entry deposits through the shared apron",game.inventory.stored[kind]>before_store[kind] and game.depot.visit=="load")
	game.inventory.collect("probe-retired-corners","wood")
	var receipts_before: Dictionary=game.inventory.paid.duplicate(true)
	var stored_before: Dictionary=game.inventory.stored.duplicate()
	for empty_corner in [Vector3(-3.6,0,-3.5),Vector3(5.5,0,-3.5),Vector3(-3.6,0,3.2)]:
		game.actor.position=empty_corner
		for step in 60:
			game._step_receivers()
			game.carry.advance(1./60.)
	check("Visits to retired corner positions cause no debit or deposit",game.inventory.paid==receipts_before and game.inventory.stored==stored_before and game.carry.flights.is_empty())
	check("Original corner pads cannot accept payments or stock",game.find_children("*StoragePlot","",true,false).is_empty() and Rules.STORAGE.all(func(id):return game.carry.receivers[id]==game.depot.apron))
	check("Second expansion is the next build",game.offer_floors[Rules.SECOND].is_visible_in_tree() and not game.offer_floors[Rules.TOWER].is_visible_in_tree())
	approach(Rules.SECOND,160)
	check("East tower and extra axe pads unlock together",game.offer_floors[Rules.TOWER].is_visible_in_tree() and game.offer_floors[Rules.AXES].is_visible_in_tree())
	approach(Rules.TOWER,160)
	approach(Rules.AXES,120)
	check("All construction is paid and offerings retire",game.inventory.build_order==[Rules.HEARTH,Rules.FIRST,"storage_wood","storage_stone","storage_meat",Rules.SECOND,Rules.TOWER,Rules.AXES] and game.offer_floors.values().all(func(f):return not f.visible))
	check("Existing unit flights and authored purchase cues executed",launched>0 and game.events.any(func(e):return e.event=="spend_meat") and game.events.filter(func(e):return e.event=="purchase").size()==8)
	var loader=game.FieldSave.new()
	var restored=game.Inventory.new()
	restored.configure(Rules.offers({"wood":3}))
	var configured:bool=loader.configure(OS.get_cmdline_user_args())
	var read_error:int=loader.load_into(restored)
	var before:Dictionary=game.inventory.snapshot()
	var after:Dictionary=restored.snapshot()
	check("Disk contains this order, typed balances and lifecycle",configured and read_error==OK and before.build_order==after.build_order and before.carried==after.carried and before.stored==after.stored and before.paid==after.paid and restored.world_state.has("pack"))
	if read_error != OK: print("Save read failure: ",read_error, " ",game.persist_error)
	print(JSON.stringify({"scene_checks":checks,"route_physics_ticks":clock}))
	game.sound.stop_playback()
	game.queue_free()
	for i in 4: await process_frame
	quit(1 if checks.values().has(false) else 0)
