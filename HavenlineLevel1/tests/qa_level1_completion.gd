extends SceneTree
## Bound to a unique marked /tmp profile by qa_level1_completion.py.
const Ledger = preload("res://field_inventory.gd")
const Rules = preload("res://field_progression.gd")
const Store = preload("res://field_save.gd")
const Session = preload("res://tests/lifecycle_test_profile.gd")
const ORDER := ["center_hearth", "expansion_1", "storage_wood", "storage_stone", "storage_meat", "expansion_2", "watchtower", "orbit_upgrade"]
var checks := {}
var failures: Array[String] = []
var observed := {}
var folder := ""
var game
var stage := ""

func _initialize() -> void:
	call_deferred("run")

func check(label: String, condition: bool) -> void:
	checks[label] = condition
	if not condition:
		failures.append(label)
		push_error(label)

func fresh_book():
	var ledger = Ledger.new()
	ledger.configure(Rules.offers({"wood":3}))
	return ledger

func legacy() -> void:
	var book = fresh_book()
	for id: String in ORDER:
		for kind: String in book.remaining(id):
			for i in int(book.remaining(id)[kind]):
				var token := "earned-%s-%s-%d" % [id, kind, i]
				check("prior purchase " + token, book.collect(token, kind) and book.payment(id, kind, false))
	book.collect("stored-legacy-meat","meat")
	book.deposit("meat")
	book.collect("carried-legacy-meat","meat")
	book.collect("second-carried-legacy-meat","meat")
	for kind in ["wood","stone"]:
		for i in 5:
			book.collect("legacy-spare-%s-%d"%[kind,i],kind)
	var state: Dictionary = book.snapshot()
	var store := Store.new()
	check("prior build committed genuine version-3 save through its own writer",store.configure(OS.get_cmdline_user_args()) and store.commit(book)==OK and read_disk().version==3 and not state.has("settlement"))
	check("prior eight purchases represented exactly once", state.build_order == ORDER and state.paid.size()==8)
	check("prior independent stocks preserved", state.stored.meat==1 and state.carried.meat==2)
	observed["schema"] = state.version

func ledger_edges() -> void:
	var book=fresh_book()
	var opened=fresh_book()
	var blank: Dictionary=opened.snapshot()
	var premature: Dictionary=blank.duplicate(true)
	premature["version"]=4
	premature["settlement"]=book.settlement.duplicate(true)
	premature.settlement.rescued=true
	check("survivor receipt cannot precede first hearth",not opened.restore(premature) and opened.snapshot()==blank)
	for n in 3:
		book.collect("first-hearth-%d" % n,"wood")
		book.payment("center_hearth","wood",false)
	book.settlement.rescued=true
	check("paid hearth alone cannot release the survivor", not opened.restore(book.snapshot()) and opened.snapshot()==blank)
	for i in 2:
		book.collect("trial-sponsor-%d"%i,"wood")
	book.carried.wood -= 2
	book.settlement.survivor_wood=2
	book.settlement.survivor_paid=true
	var early: Dictionary=book.snapshot()
	check("paid survivor at first hearth survives without a storage purchase",opened.restore(early) and opened.settlement.rescued and opened.stored.wood==0)
	for key in ["worker_carry_token","worker_deliveries","served","level","processed_stone","processed_wood"]:
		var bad: Dictionary=early.duplicate(true)
		if key=="worker_carry_token": bad.settlement[key]="wood-1"
		else: bad.settlement[key]=2
		check("ineligible " + key + " rejected on old hearth save",not opened.restore(bad) and opened.snapshot()==early)
	var evidence: Dictionary=opened.snapshot()
	evidence.settlement.worker_receipts.append("wood-123")
	check("uncommitted working receipt cannot alter previous checkpoint",opened.settlement.worker_receipts.is_empty() and book.settlement.worker_receipts.is_empty())
	var malformed: Dictionary=early.duplicate(true)
	malformed.settlement["level"]=1.5
	check("fractional level cannot be accepted",not opened.restore(malformed) and opened.snapshot()==early)

func finish() -> void:
	if is_instance_valid(game) and game.get("sound"):
		game.set_physics_process(false)
		await Session.drain_field_audio(self, game)
		game.queue_free()
		for i in 8:
			await process_frame
	print("SETTLEMENT_QA ",JSON.stringify({"phase":stage,"checks":checks,"failures":failures,"observed":observed}))
	quit(0 if failures.is_empty() else 1)

func place(at: Vector3) -> void:
	game.actor.position = at
	game.actor.velocity = Vector3.ZERO
	game.camera.position = at + Vector3(7,11,11)

func eligible_for_claim() -> bool:
	return game.inventory.settlement.worker_carry_token != ""

func wait_for(witness: Callable, limit: int) -> bool:
	for tick in limit:
		if witness.call(): return true
		if game.persist_blocked: return false
		await physics_frame
	return witness.call()

func read_disk() -> Dictionary:
	var envelope = JSON.parse_string(FileAccess.get_file_as_string(folder.path_join(Store.PRIMARY)))
	var payload: String = envelope.payload
	assert(payload.sha256_text() == envelope.sha256)
	return JSON.parse_string(payload)

func reject_corrupt_progress() -> void:
	var book = fresh_book()
	var initial: Dictionary = game.inventory.snapshot()
	check("same build accepts the valid snapshot",book.restore(initial))
	for key in ["cooked","served","worker_deliveries","level"]:
		var corrupt: Dictionary = initial.duplicate(true)
		corrupt.settlement[key] = -1
		check("invalid " + key + " rejected atomically",not book.restore(corrupt) and book.snapshot()==initial)
	var unearned := initial.duplicate(true)
	unearned.settlement.level = 2
	check("unearned level 2 rejected atomically",not book.restore(unearned) and book.snapshot()==initial)
	var extra := initial.duplicate(true)
	extra.settlement.cooked += 1
	check("a cooked meal needs a matching consumed raw meat",not book.restore(extra) and book.snapshot()==initial)

func plot_partial() -> void:
	var ledger=game.inventory
	check("legacy v3 started in Level 1",ledger.settlement.level==1 and not ledger.settlement.rescued and ledger.settlement.worker_deliveries==0 and ledger.settlement.served==0)
	check("all original receipts and both raw stocks survived migration",ledger.build_order==ORDER and ledger.stored.meat==1 and ledger.carried.meat==2)
	check("eight purchases alone cannot enter the next level",not game.enter_next_level())
	place(Vector3(1.72,0,1.8))
	check("rescue cannot be claimed remotely",not game.rescue_survivor())
	check("no remote or duplicate worker grants before a physical pickup",not game.receive_worker_wood() and not game.claim_worker_wood("missing-drop"))
	check("remote cook and remote sale rejected",not game.cook_meal() and not game.serve_meal(1))
	place(Vector3(-5.1,0,9.9))
	check("unpaid plot cannot recruit even alongside the survivor",not game.rescue_survivor())
	place(Vector3(-5.5,0,10.9))
	check("first wood arrives as a separate survivor-plot receipt",await wait_for(func():return ledger.settlement.survivor_wood==1,180))
	check("partial payment consumes one wood and keeps the survivor waiting",ledger.carried.wood==4 and not ledger.settlement.survivor_paid and not ledger.settlement.rescued)

func claim() -> void:
	var ledger=game.inventory
	check("partial survivor payment resumed before the second wood",ledger.settlement.survivor_wood==1 and ledger.carried.wood==4)
	place(Vector3(-5.5,0,10.9))
	check("second wood completes the single survivor purchase",await wait_for(func():return ledger.settlement.survivor_paid,180))
	check("purchase consumed exactly two raw wood",ledger.carried.wood==3 and ledger.settlement.survivor_wood==2)
	place(Vector3(-5.1,0,9.9))
	check("rescue performed by reaching the survivor",await wait_for(func():return ledger.settlement.rescued,300))
	check("rescue is idempotent",not game.rescue_survivor())
	place(Vector3(1.72,0,1.8))
	check("worker claimed a real pine drop",await wait_for(eligible_for_claim,4000))
	game.set_physics_process(false)
	var token: String=ledger.settlement.worker_carry_token
	check("pending worker pickup left the ground and has no bank credit",not token.is_empty() and not game.drops.has(token) and not ledger.collected.has(token) and ledger.stored.wood==0)
	check("duplicate worker pickup rejected",not game.claim_worker_wood(token))
	observed["claimed_token"]=token
	if not token.is_empty():
		reject_corrupt_progress()

func cook() -> void:
	var ledger=game.inventory
	var token: String=ledger.settlement.worker_carry_token
	check("fresh process restored the in-progress wood delivery",not token.is_empty() and not game.drops.has(token) and not ledger.collected.has(token))
	check("worker delivers at the real storage shelf",await wait_for(func():return ledger.settlement.worker_deliveries==1,4000))
	check("only one stored wood and receipt",ledger.stored.wood==1 and ledger.collected.get(token)=="wood" and ledger.settlement.worker_carry_token=="")
	check("finished token cannot pay a second time",not game.claim_worker_wood(token) and not game.receive_worker_wood())
	place(Vector3(-19.65,0,16.65))
	check("first raw portion can reserve a transfer", game.carry.deposit_storage("meat"))
	game.carry.advance(.17)
	check("all remaining raw meat can be reserved without cooking it", game.carry.deposit_storage("meat") and game.carry.available_to_station("meat")==0)
	check("reserved outgoing raw portions cannot start a cooking cycle", not game.settlement_loop._can_cook())
	game.carry.cancel_transfers()
	check("cancelled flights restored the two carried portions", ledger.carried.meat==2 and ledger.stored.meat==1)
	check("cooker begins its normal timed process",await wait_for(func():return game.settlement_loop.cooking>=.50,90))
	check("the HUD exposes the active timed cook", game.opening_hud.operation.is_visible_in_tree() and game.opening_hud.operation.value > 0)
	place(Vector3(1.72,0,1.8))
	await physics_frame
	await physics_frame
	check("leaving the cooker interrupts a partial cycle without debiting meat",game.settlement_loop.cooking==0 and ledger.settlement.cooked==0 and ledger.carried.meat==2)
	place(Vector3(-19.65,0,16.65))
	check("ordinary cooking interval debits one carried meat",await wait_for(func():return ledger.settlement.cooked==1,700))
	check("stored meat intact and one prepared meal unpaid",ledger.stored.meat==1 and ledger.carried.meat==1 and ledger.settlement.served==0)
	check("cannot prepare a second unserved meal",not game.cook_meal())
	check("cooker refuses remote or skipped customer order",not game.serve_meal(1) and not game.serve_meal(2))
	observed["raw_in_pack"]=ledger.carried.meat
	observed["raw_in_storage"]=ledger.stored.meat

func lock_save() -> void:
	var dir := DirAccess.open(folder)
	check("fixture acquires a live save lock", dir.make_dir(Store.LOCK)==OK)
	var marker := FileAccess.open(folder.path_join(Store.LOCK).path_join("owner-" + str(OS.get_process_id())),FileAccess.WRITE)
	marker.close()

func release_save() -> void:
	var dir := DirAccess.open(folder)
	dir.remove(Store.LOCK + "/owner-" + str(OS.get_process_id()))
	dir.remove(Store.LOCK)

func interrupt_delivery() -> void:
	game.set_physics_process(false)
	var ledger=game.inventory
	var token: String=ledger.settlement.worker_carry_token
	check("worker returned with the same single pending token",not token.is_empty() and ledger.settlement.worker_deliveries==0)
	var previous := FileAccess.get_file_as_bytes(folder.path_join(Store.PRIMARY))
	lock_save()
	for tick in 3000:
		game.step_technical_gates(1./60.)
		game.survivor.advance(1./60.)
		if game.persist_blocked: break
	check("interrupted shelf credit paused new grants",game.persist_blocked)
	check("bank credit and receipt rolled back together",ledger.settlement.worker_carry_token==token and ledger.settlement.worker_deliveries==0 and ledger.stored.wood==0 and not ledger.collected.has(token))
	check("failed shelf receipt left the durable bytes intact",FileAccess.get_file_as_bytes(folder.path_join(Store.PRIMARY))==previous)
	release_save()
	observed["retained_token"]=token

func process_counter(interrupted: bool) -> void:
	var ledger=game.inventory
	check("ready-to-serve meal persisted independently of the raw stock",ledger.settlement.cooked==1 and ledger.settlement.served==0 and ledger.carried.meat==1 and ledger.stored.meat==1)
	check("service cannot claim a future customer",not game.serve_meal(2))
	game.set_physics_process(false)
	place(Vector3(1.72,0,1.8))
	for tick in 500:
		game.counter.advance(1./60.)
		if game.counter.front_ready(1): break
	check("actual first customer reached the outside marker",game.counter.front_ready(1))
	place(game.counter.customer_point.global_position)
	check("waiting customer cannot be served from the wrong side",not game.serve_meal(1) and ledger.settlement.served==0)
	place(game.counter.service_point.global_position)
	var previous := FileAccess.get_file_as_bytes(folder.path_join(Store.PRIMARY))
	if interrupted:
		lock_save()
	for tick in 2700:
		game.counter.advance(1./60.)
		if game.persist_blocked or int(ledger.settlement.served)>0: break
	if interrupted:
		check("failed customer payment paused new grants",game.persist_blocked)
		check("failed checkout left hot meal and currency unchanged",ledger.settlement.served==0 and ledger.settlement.cooked==1)
		check("failed checkout left the durable envelope byte-identical",FileAccess.get_file_as_bytes(folder.path_join(Store.PRIMARY))==previous)
		release_save()
	else:
		check("exactly one customer paid for one actual meal",not game.persist_blocked and ledger.settlement.served==1 and ledger.settlement.cooked==1)
		check("same customer cannot pay twice",not game.serve_meal(1))
		check("receipt and currency survive repeated counter ticks",read_disk().settlement.served==1)
		for tick in 160: game.counter.advance(1./60.)
		check("no second reward without another meal",ledger.settlement.served==1)
		check("finishing the sale waits for the player's Continue action",ledger.settlement.level==1)
	observed["served"]=ledger.settlement.served

func machines_and_owl() -> void:
	var ledger=game.inventory
	check("a sale alone leaves the new production objectives open",not game.enter_next_level() and not game.opening_hud.level_continue.is_visible_in_tree())
	for kind: String in ["wood","stone"]:
		var key="processed_"+kind
		var before: int=ledger.carried[kind]
		var stored: int=ledger.stored[kind]
		check("remote "+kind+" processor cannot grant output",not game.settlement_loop.works.finish(kind))
		var position_ = Vector3(-15.4,0,21.2) if kind=="wood" else Vector3(-18.7,0,25.55)
		place(position_)
		check("player is at the physical "+kind+" machine",game.processors.at_station(game.actor.global_position)==kind)
		check("one finished "+kind+" processing cycle",await wait_for(func():return ledger.settlement[key]>=1,360))
		check("one "+kind+" input consumed and one output saved",ledger.carried[kind]==before-1 and ledger.stored[kind]==stored and ledger.settlement[key]==1 and read_disk().settlement[key]==1)
		place(Vector3(1.72,0,1.8))
		await physics_frame
		await physics_frame
	# Take the encounter away from the paid tower. Keep the enemies, serials, and
	# life-cycle settings from the ordinary wave producer.
	place(Vector3(55,0,12))
	await wait_for(func():return game.owl.global_position.distance_to(game.actor.global_position)<4.,900)
	if game.enemies.is_empty():
		game.encounters.rng.seed=8173
		game.encounters.launch()
	var foe=game.enemies.front() if not game.enemies.is_empty() else null
	check("physical wolf spawned for owl contact",foe!=null and foe.hp>0)
	if not foe: return
	var start_hits: int=ledger.settlement.owl_hits
	place(foe.global_position + Vector3(0,0,5.0))
	check("remote owl callback cannot manufacture a hit",not game.owl_contact(foe,game.actor.global_position+Vector3(35,0,0)))
	check("live hovering companion earns an actual contact receipt",await wait_for(func():return ledger.settlement.owl_hits>start_hits,1800))
	check("owl hit saved with both production outputs",read_disk().settlement.owl_hits>start_hits and read_disk().settlement.processed_wood==1 and read_disk().settlement.processed_stone==1)
	observed["owl_hits_before"]=start_hits
	observed["owl_hits_after"]=ledger.settlement.owl_hits
	observed["last_owl_contact"]=game.events.filter(func(e):return e.event=="owl_hit").back() if ledger.settlement.owl_hits>start_hits else {}

func handoff(interrupted: bool) -> void:
	var ledger=game.inventory
	check("first-reward receipt survived in a new process",ledger.settlement.served==1 and ledger.settlement.level==1)
	var button: Button=game.opening_hud.level_continue
	check("earned handoff button visible and enabled",button.is_visible_in_tree() and not button.disabled)
	if not interrupted:
		var gates = load("res://field_settlement.gd")
		for key: String in ["rescued","worker_deliveries","served","processed_wood","processed_stone","owl_hits"]:
			var missing: Dictionary = ledger.settlement.duplicate(true)
			missing[key] = false if key == "rescued" else 0
			check("continuation requires " + key, not gates.ready_to_continue(missing,ledger.build_order))
		for id: String in ORDER:
			var shorter: Array = ledger.build_order.duplicate()
			shorter.erase(id)
			check("continuation requires camp purchase " + id, not gates.ready_to_continue(ledger.settlement,shorter))
	if interrupted: lock_save()
	var touch := InputEventScreenTouch.new()
	touch.index = 7
	touch.position = button.get_global_rect().get_center()
	touch.pressed = true
	game._input(touch)
	touch.pressed = false
	game._input(touch)
	if interrupted:
		check("failed level write preserves the Level 1 completion and cash",game.persist_blocked and ledger.settlement.level==1 and ledger.settlement.served==1 and read_disk().settlement.level==1)
		release_save()
	else:
		check("touching the displayed Continue button commits Level 2 once",ledger.settlement.level==2 and read_disk().settlement.level==2)
		check("handoff cannot be applied twice",not game.enter_next_level())

func second_launch() -> void:
	var ledger=game.inventory
	check("cold launch restored Level 2",ledger.settlement.level==2 and not game.persist_blocked)
	check("eight prior purchases and the banked delivery survived",ledger.build_order==ORDER and ledger.stored.wood>=1)
	check("served receipt unchanged on cold launch",ledger.settlement.served==1 and ledger.settlement.cooked==1)
	check("both processed balances and companion contact persisted",ledger.settlement.processed_wood==1 and ledger.settlement.processed_stone==1 and ledger.settlement.owl_hits>0 and ledger.settlement.survivor_paid)
	check("already-claimed completion avoided a second transition",not game.opening_hud.level_continue.is_visible_in_tree() and not game.enter_next_level())
	var labels := []
	for label:Label in game.opening_hud.find_children("*","Label",true,false):
		if label.is_visible_in_tree(): labels.append(label.text)
	var hud = game.opening_hud
	check("Level 2 arrives in the normal visible gameplay chapter",hud.chapter.is_visible_in_tree() and hud.chapter.text=="Level 2  ·  Preview")
	check("the resumed field provides a playable objective",labels.has("Stay in the snowfield or serve another meal."))
	check("cash label reflects the one confirmed wallet payment",hud.purse.is_visible_in_tree() and hud.purse.text.strip_edges()=="Cash  1")
	check("both finished-material counters match persistent balances",hud.workshop_stock.is_visible_in_tree() and hud.workshop_stock.text.contains("Planks 1") and hud.workshop_stock.text.contains("Blocks 1"))
	check("visible health reading matches the live player",hud.health_bar.is_visible_in_tree() and int(hud.health_bar.value)==game.player_hp and int(hud.health_bar.max_value)==game.MAX_HP)
	observed["visible_labels"]=labels

func run() -> void:
	var args=OS.get_cmdline_user_args()
	var guard=Session.Profile.new()
	if not guard.configure(args):
		printerr("Use qa_level1_completion.py to create a disposable test profile.")
		quit(2)
		return
	folder=guard._dir
	for arg in args:
		if arg.begins_with("--settlement-qa="): stage=arg.trim_prefix("--settlement-qa=")
	if stage=="legacy":
		legacy()
		await finish()
		return
	if stage=="ledger-edges":
		ledger_edges()
		await finish()
		return
	var main_scene: String=ProjectSettings.get_setting("application/run/main_scene")
	if change_scene_to_file(main_scene)!=OK:
		quit(2)
		return
	await scene_changed
	game=current_scene
	await physics_frame
	check("shipping main scene loaded from disposable profile",game!=null and not game.persist_blocked and game.field_save.directory==folder)
	if failures.is_empty():
		match stage:
			"plot-partial": await plot_partial()
			"claim": await claim()
			"delivery-interrupted": interrupt_delivery()
			"cook": await cook()
			"interrupted": process_counter(true)
			"serve": process_counter(false)
			"machines-and-owl": await machines_and_owl()
			"handoff-interrupted": handoff(true)
			"handoff": handoff(false)
			"second-launch": second_launch()
			_: check("known fixture phase",false)
	await finish()
