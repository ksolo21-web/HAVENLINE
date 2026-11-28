extends "res://tests/qa_worker_jobs.gd"

const HERE := "res://tests/qa_offsite_camp.gd"
const FIELD_POINT := Vector3(32.,0.,26.)
const STEP := 1.0/60.0

func stock(kind: String, count: int, tag: String) -> void:
	for i in count:
		game.inventory.collect("offsite-%s-%s-%d" % [tag,kind,i],kind)
		game.inventory.deposit(kind)

func run() -> void:
	var profile := Save.Profile.new()
	if not profile.configure(OS.get_cmdline_user_args()):
		var private_dir := Session.make_directory()
		var code := Session.child(HERE,private_dir,"offsite")
		Session.remove_owned(private_dir)
		quit(code)
		return
	game = load("res://field_opening.tscn").instantiate()
	root.add_child(game)
	game.set_physics_process(false)
	game.set_process(false)
	for i in 3: await process_frame
	worker = game.survivor
	setup_camp()
	var book = game.inventory
	var journal: Dictionary = book.settlement
	var raid = game.encounters.raids.clock
	var line_id: String = game.Progress.FOOD_LINE
	for kind in ["wood","stone","meat"]:
		stock(kind,18,"manual")
	book.collect("offsite-player-sentinel","metal")
	raid.condition["gate-east"] = raid.hp("gate-east") - 6
	var bill: Dictionary = raid.repair_bill("gate-east")
	game.actor.position = FIELD_POINT
	game.previous_dry_position = FIELD_POINT
	game._inventory_changed()
	check(game.encounters.raids._camp_unattended(),"player actually outside the raid's unattended radius")
	check(not worker._plot_authorized(line_id),"conveyor starts unselected")
	var seen := {}
	for i in 60*220:
		tick(STEP)
		seen[worker.phase] = true
		if game.persist_blocked or (raid.repair_bill("gate-east").is_empty() and journal.house_cash>0 and journal.product_store.planks>0 and journal.product_store.blocks>0):
			break
	check(not game.persist_blocked,"offsite transactions remained save-valid")
	check("repair_site" in seen and raid.repair_bill("gate-east").is_empty() and raid.spend.wood==bill.wood and raid.spend.stone==bill.stone,"survivor repaired the paid gate with one exact bill")
	check("supply_out" in seen and "collect_output" in seen and journal.product_store.planks>0 and journal.product_store.blocks>0,"survivor fed and cleared both unconnected workshops")
	check(journal.cooked>0 and journal.served>0 and journal.house_cash>0 and journal.pocket_cash==0,"survivor stocked counter and banked customer cash through real receipts")
	check(not book.complete(line_id) and book.paid[line_id].values().all(func(amount):return amount==0),"unselected conveyor spent nothing")
	check(game.actor.position.is_equal_approx(FIELD_POINT) and book.carried.metal==1 and book.carried.wood==0 and book.carried.stone==0 and book.carried.meat==0,"player stayed away and their backpack remained intact")

	stock("wood",12,"chosen-line")
	stock("stone",8,"chosen-line")
	game.opening_hud.camp_dock.choose(line_id)
	# Let the worker reach the store and take a reservation for the offer.
	for i in 60*160:
		tick(STEP)
		if worker.assisted_plot==line_id or game.persist_blocked: break
	check(worker.assisted_plot==line_id,"survivor undertook the selected conveyor project")
	if worker.assisted_plot==line_id:
		game.settlement_loop.conveyors.menu.select(line_id)
		tick(STEP)
		check(worker.assisted_plot.is_empty() and not book.complete(line_id) and book.paid[line_id].values().all(func(amount):return amount==0),"revoking permission stops tender before any debit")
		game.settlement_loop.conveyors.menu.select(line_id)
	for i in 60*180:
		tick(STEP)
		if book.complete(line_id) or game.persist_blocked: break
	check(book.complete(line_id) and book.build_order.count(line_id)==1,"selected conveyor built by survivor once without the player returning")
	var copy = game.Inventory.new()
	check(not game.persist_blocked and copy.configure(book.configured_costs) and copy.restore(book.snapshot()),"worker, stock, sales, repairs and plots conserve the saved balance")
	print("OFFSITE_CAMP ",JSON.stringify({
		"checks":checks,"failures":errors,"elapsed":timelapsed,"worker_phase":worker.phase,
		"observed_phases":seen.keys(),"house_cash":journal.house_cash,"sales":journal.served,
		"product_stock":journal.product_store,"workshop_output":[journal.processed_wood,journal.processed_stone],"hoppers":journal.hoppers,"repair_spend":raid.spend,
		"build_order":book.build_order,"player_position":str(game.actor.position),
		"save_error":game.persist_error}))
	await Session.drain_field_audio(self,game)
	game.queue_free()
	await process_frame
	quit(0 if errors.is_empty() else 1)
