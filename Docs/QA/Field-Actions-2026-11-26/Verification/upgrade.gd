extends SceneTree

var world
var checks := {}
var fixture := OS.get_environment("ACTIONS_UPGRADE_CASE")
var operation := OS.get_environment("ACTIONS_UPGRADE_OP")

func _initialize() -> void:
	run.call_deferred()

func expect(key: String, good: bool) -> void:
	checks[key] = good

func old_unit(offer: String, kind: String, serial: int) -> void:
	var token := "%s-preupdate-%s-%s-%d" % [fixture,offer,kind,serial]
	expect(token,world.inventory.collect(token,kind) and world.inventory.payment(offer,kind,false))

func run() -> void:
	world = load(ProjectSettings.get_setting("application/run/main_scene")).instantiate()
	root.add_child(world)
	for i in 3: await process_frame
	world.set_physics_process(false)
	var book = world.inventory
	expect("loaded isolated profile",world.field_ready and not world.persist_blocked and not world.field_save.native_profile)
	expect("tested compiled game",FileAccess.file_exists("res://field_opening.gdc"))
	if operation == "write-v2":
		expect("previous three wood hearth",book.costs.center_hearth.wood==3)
		for id: String in ["center_hearth","expansion_1","storage_wood","storage_stone","storage_meat","expansion_2","watchtower","orbit_upgrade"]:
			var partial := id=="expansion_1" and fixture=="partial"
			if partial:
				old_unit(id,"wood",0)
				break
			for kind: String in book.costs[id]:
				for serial in int(book.costs[id][kind]):
					old_unit(id,kind,serial)
			expect("old owned "+id,book.complete(id))
		for kind: String in ["wood","stone","meat","metal"]:
			for serial in 2: expect("stock "+kind+str(serial),book.collect("retained-"+kind+str(serial),kind))
		book.collect("rescue-part-one","wood")
		book.carried.wood-=1
		book.settlement.survivor_wood=1
		if fixture=="owned":
			book.collect("rescue-part-two","wood")
			book.carried.wood-=1
			book.settlement.survivor_wood=2
			book.settlement.survivor_paid=true
		world.player_hp=23
		world._inventory_changed()
		expect("commit old app receipt",not world.persist_blocked)
	else:
		expect("built camp still owned",book.complete("center_hearth") and world.camp_active)
		expect("health preserved",world.player_hp==23)
		for kind: String in ["wood","stone","meat","metal"]:
			expect("stock count preserved "+kind,book.carried[kind]==2 and book.collected.has("retained-"+kind+"0"))
		if fixture=="partial":
			expect("one old contribution retained",book.paid.expansion_1.wood==1 and not book.complete("expansion_1"))
			expect("unstarted plot uses revised price",int(book.costs.storage_wood.wood)>2)
			expect("partial survivor kept",book.settlement.survivor_wood==1 and not book.settlement.survivor_paid)
		else:
			expect("all old plots still owned",book.build_order.size()==8 and book.build_order.all(func(id): return book.complete(id)))
			expect("earned owl still owned",book.settlement.survivor_paid)
		world._inventory_changed()
		expect("new app accepts save and rewrites",not world.persist_blocked)
	var receipt={"operation":operation,"case":fixture,"checks":checks,"hp":world.player_hp,"remaining":book.remaining("expansion_1"),"owned":book.build_order.duplicate(),"survivor":book.settlement.survivor_wood,"stock":book.carried.duplicate(),"passed":not checks.values().has(false)}
	print("UPGRADE_SMOKE ",JSON.stringify(receipt))
	world.sound.stop_playback()
	for i in 14:
		OS.delay_msec(19)
		await process_frame
	world.queue_free()
	for i in 5: await process_frame
	quit(int(not receipt.passed))
