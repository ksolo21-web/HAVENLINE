extends SceneTree
## Bound to a unique marked /tmp profile by qa_level1_completion.py.
const Ledger = preload("res://field_inventory.gd")
const Rules = preload("res://field_progression.gd")
const Store = preload("res://field_save.gd")
const Session = preload("res://tests/lifecycle_test_profile.gd")
const ORDER := ["center_hearth", "expansion_1", "storage_wood", "storage_stone", "storage_meat", "expansion_2", "watchtower", "orbit_upgrade"]
const EQUIPMENT := ["camp_cooker","saw_bench","quarry_drill"]
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
		for i in (11 if kind=="wood" else 5):
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
	premature.erase("legacy_prices")
	premature["version"]=5
	premature["settlement"]=book.settlement.duplicate(true)
	premature.settlement.rescued=true
	check("survivor receipt cannot precede first hearth",not opened.restore(premature) and opened.snapshot()==blank)
	for n in int(book.remaining("center_hearth").wood):
		book.collect("first-hearth-%d" % n,"wood")
		book.payment("center_hearth","wood",false)
	book.settlement.rescued=true
	check("paid hearth alone cannot release the survivor", not opened.restore(book.snapshot()) and opened.snapshot()==blank)
	for i in book.survivor_cost:
		book.collect("trial-sponsor-%d"%i,"wood")
	book.carried.wood -= book.survivor_cost
	book.settlement.survivor_wood=book.survivor_cost
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
		game.carry.set_physics_process(false)
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
	check("all original receipts and both raw stocks survived migration",ledger.build_order==ORDER + EQUIPMENT and ledger.stored.meat==1 and ledger.carried.meat==2)
	check("eight purchases alone cannot enter the next level",not game.enter_next_level())
	place(Vector3(1.72,0,1.8))
	check("rescue cannot be claimed remotely",not game.rescue_survivor())
	check("no remote or duplicate worker grants before a physical pickup",not game.receive_worker_wood() and not game.claim_worker_wood("missing-drop"))
	check("remote cook and remote sale rejected",not game.cook_meal() and not game.serve_meal(1))
	place(Vector3(-5.1,0,9.9))
	check("unpaid plot cannot recruit even alongside the survivor",not game.rescue_survivor())
	place(Vector3(-5.5,0,10.9))
	check("first wood arrives as a separate survivor-plot receipt",await wait_for(func():return ledger.settlement.survivor_wood==1,180))
	check("partial payment consumes one wood and keeps the survivor waiting",ledger.carried.wood==10 and not ledger.settlement.survivor_paid and not ledger.settlement.rescued)

func claim() -> void:
	var ledger=game.inventory
	check("partial survivor payment resumed before the second wood",ledger.settlement.survivor_wood==1 and ledger.carried.wood==10)
	place(Vector3(-5.5,0,10.9))
	check("remaining wood completes the single survivor purchase",await wait_for(func():return ledger.settlement.survivor_paid,300))
	check("purchase consumed exactly the displayed raw amount",ledger.carried.wood==3 and ledger.settlement.survivor_wood==ledger.survivor_cost)
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

# The survivor can reserve a shelf unit on the same tick as its first wood delivery.
func unprocessed_meat_outside_pack(ledger) -> int:
	return int(ledger.stored.meat) + int(ledger.settlement.worker_supply == "meat")

func load_cooker() -> void:
	purchase_equipment_fixture()
	var ledger=game.inventory
	var token: String=ledger.settlement.worker_carry_token
	var before_wood: int = int(ledger.stored.wood) + int(ledger.settlement.worker_supply=="wood")
	check("fresh process restored the in-progress wood delivery",not token.is_empty() and not game.drops.has(token) and not ledger.collected.has(token))
	check("worker delivers at the real storage shelf",await wait_for(func():return ledger.settlement.worker_deliveries==1,4000))
	check("one wood delivery credited exactly once, including any immediately reserved for a machine",int(ledger.stored.wood)+int(ledger.settlement.worker_supply=="wood")==before_wood+1 and ledger.collected.get(token)=="wood" and ledger.settlement.worker_receipts.count(token)==1 and ledger.settlement.worker_carry_token=="")
	check("finished token cannot pay a second time",not game.claim_worker_wood(token) and not game.receive_worker_wood())
	park_worker_for_player_supply_test()
	place(game.lakeshore.APRON)
	check("first raw portion can reserve a transfer", game.carry.deposit_storage("meat"))
	game.carry.advance(.17)
	check("all remaining raw meat can be reserved without cooking it", game.carry.deposit_storage("meat") and game.carry.available_to_station("meat")==0)
	for tick in 30: game.settlement_loop.works.advance(1./60.)
	check("reserved outgoing raw portions cannot enter the hopper", ledger.settlement.hoppers.meat==0 and ledger.carried.meat==2)
	game.carry.cancel_transfers()
	check("cancelled flights restored the two carried portions", ledger.carried.meat==2 and unprocessed_meat_outside_pack(ledger)==1)
	check("cooker accepts one raw portion through its loading apron",await wait_for(func():return ledger.settlement.hoppers.meat==1,100))
	place(Vector3(1.72,0,1.8))
	check("loading a real hopper debits exactly one carried raw meat",ledger.carried.meat==1 and unprocessed_meat_outside_pack(ledger)==1 and read_disk().settlement.hoppers.meat==1)
	check("cook advances after the player leaves", await wait_for(func():return game.settlement_loop.cooking>=.5,75))
	check("visible HUD displays the unattended production cycle",game.opening_hud.operation.is_visible_in_tree() and game.opening_hud.operation.value>0)
	game._checkpoint_lifecycle()
	check("partially finished cook is saved before shutdown",read_disk().settlement.work_seconds.meat>0 and read_disk().settlement.cooked==0)

func finish_cooker(interrupted: bool) -> void:
	var ledger=game.inventory
	place(Vector3(1.72,0,1.8))
	check("queued meat and its running clock survived a fresh launch",ledger.settlement.hoppers.meat==1 and ledger.settlement.work_seconds.meat>0 and ledger.carried.meat==1)
	var previous := FileAccess.get_file_as_bytes(folder.path_join(Store.PRIMARY))
	if interrupted: lock_save()
	check("unattended cooker reaches a durable transaction", await wait_for(func():return ledger.settlement.cooked==1 or game.persist_blocked,240))
	if interrupted:
		check("interrupted output commit returns its input to the hopper",game.persist_blocked and ledger.settlement.hoppers.meat==1 and ledger.settlement.cooked==0 and ledger.carried.meat==1)
		check("failed output left the previous envelope intact",FileAccess.get_file_as_bytes(folder.path_join(Store.PRIMARY))==previous)
		release_save()
		return
	check("unattended meat finishes once and becomes physical outfeed stock",ledger.settlement.cooked==1 and ledger.settlement.held_meal==0 and ledger.settlement.hoppers.meat==0 and not is_instance_valid(game.counter.meal))
	check("empty input and proximity to the counter produce no reward",ledger.settlement.served==0 and not game.serve_meal(1))
	place(game.counter.service_point.global_position)
	for tick in 225: await physics_frame
	check("counter cannot sell remotely buffered food",ledger.settlement.served==0 and ledger.settlement.held_meal==0 and ledger.settlement.cooked==1 and not is_instance_valid(game.counter.meal))
	check("stocked or carried raw meat never auto-debits at a distance",ledger.carried.meat==1 and unprocessed_meat_outside_pack(ledger)==1 and ledger.settlement.hoppers.meat==0)
	observed["raw_in_pack"]=ledger.carried.meat
	observed["raw_in_storage"]=ledger.stored.meat
	observed["raw_on_courier"]=ledger.settlement.worker_supply

# These phases measure the player's own feed and the machine's independent clock.
# Stop the optional surplus courier to keep a second legitimate input from
# racing the single-input conservation and injected write-failure cases.
func park_worker_for_player_supply_test() -> void:
	game.survivor.phase = "qa_stationary"

func pickup_roast() -> void:
	var ledger=game.inventory
	check("output survived restart without teleporting to the player",ledger.settlement.held_meal==0 and ledger.settlement.cooked==1 and not is_instance_valid(game.counter.meal))
	place(game.lakeshore.OUTPUT_APRON)
	check("collecting at the distinct output apron equips one cooked meal",await wait_for(func():return ledger.settlement.held_meal==1 and is_instance_valid(game.counter.meal),240))
	place(Vector3(1.72,0,1.8))
	check("pickup produces no payment or second input debit",read_disk().settlement.held_meal==1 and ledger.settlement.served==0 and ledger.carried.meat==1)

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
	check("ready-to-serve meal persisted independently of the raw stock",ledger.settlement.cooked==1 and ledger.settlement.served==0 and ledger.settlement.held_meal==1 and ledger.carried.meat==1 and unprocessed_meat_outside_pack(ledger)==1)
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
	var batch := ["wood","stone"]
	for kind: String in batch:
		var before: int=ledger.carried[kind]
		check("remote "+kind+" cannot grant an input receipt",not game.settlement_loop.works.receive(kind,kind,1))
		place(game.processors.APRONS[kind])
		check(kind+" loading apron is accessible inside the paid camp",game.field_env.is_inside_camp(game.actor.global_position) and game.processors.at_station(game.actor.global_position)==kind)
		check(kind+" raw input transferred to its own hopper",await wait_for(func():return ledger.settlement.hoppers[kind]==1,90))
		check(kind+" loading withdraws once from the player's pack",ledger.carried[kind]==before-1 and ledger.settlement["processed_"+kind]==0)
		place(Vector3(1.72,0,1.8))
	check("stocked saw and stone mill operate concurrently",ledger.settlement.hoppers.wood==1 and ledger.settlement.hoppers.stone==1 and await wait_for(func():return ledger.settlement.work_seconds.wood>0 and ledger.settlement.work_seconds.stone>0,12))
	check("both machines finish while the player is away",await wait_for(func():return ledger.settlement.processed_wood==1 and ledger.settlement.processed_stone==1,180))
	check("each completion consumes its own hopper input and saves its own product",ledger.settlement.hoppers.wood==0 and ledger.settlement.hoppers.stone==0 and read_disk().settlement.processed_wood==1 and read_disk().settlement.processed_stone==1)
	for tick in 150: await physics_frame
	check("empty hoppers cannot make a second batch",ledger.settlement.processed_wood==1 and ledger.settlement.processed_stone==1 and ledger.settlement.hoppers.wood==0 and ledger.settlement.hoppers.stone==0)
	# Take the encounter away from the paid tower. Keep the enemies, serials, and
	# life-cycle settings from the ordinary wave producer.
	place(Vector3(55,0,12))
	await wait_for(func():return game.owl.global_position.distance_to(game.actor.global_position)<4.,900)
	# A defeated wolf stays in the scene until its fall animation ends.
	# Select a live target even if the previous wave is still fading out.
	if not game.enemies.any(func(wolf): return wolf.active and wolf.hp > 0):
		game.encounters.rng.seed=8173
		game.encounters.launch()
	var spawned: bool = await wait_for(func(): return game.enemies.any(func(wolf): return wolf.active and wolf.hp > 0),1800)
	check("physical wolf spawned for owl contact",spawned)
	if not spawned: return
	var foe = game.enemies.filter(func(wolf): return wolf.active and wolf.hp > 0).front()
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
		for id: String in ORDER + EQUIPMENT:
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
	check("eight prior purchases and the banked delivery survived",ledger.build_order==ORDER + EQUIPMENT and ledger.settlement.worker_receipts.size()>=1)
	check("served receipt unchanged on cold launch",ledger.settlement.served==1 and ledger.settlement.cooked==1)
	check("both processed balances and companion contact persisted",ledger.settlement.processed_wood==1 and ledger.settlement.processed_stone==1 and ledger.settlement.owl_hits>0 and ledger.settlement.survivor_paid)
	check("already-claimed completion avoided a second transition",not game.opening_hud.level_continue.is_visible_in_tree() and not game.enter_next_level())
	var labels := []
	for label:Label in game.opening_hud.find_children("*","Label",true,false):
		if label.is_visible_in_tree(): labels.append(label.text)
	var hud = game.opening_hud
	check("Level 2 arrives in the normal visible gameplay chapter",hud.chapter_detail.is_visible_in_tree() and hud.chapter_detail.text=="Camp  ·  Level 2")
	check("the resumed field shows all Level 1 plots finished and camp open",labels.has("Level 2 preview · All Level 1 plots complete. The camp is open."))
	check("cash label reflects the one confirmed wallet payment",hud.outputs.cash.is_visible_in_tree() and hud.outputs.cash.text=="1" and hud.display_goods.cash.art.texture!=null)
	check("both finished-material counters match persistent balances",hud.outputs.planks.is_visible_in_tree() and hud.outputs.planks.text=="1" and hud.outputs.blocks.is_visible_in_tree() and hud.outputs.blocks.text=="1" and hud.display_goods.planks.art.texture.region!=hud.display_goods.blocks.art.texture.region)
	check("visible health reading matches the live player",hud.health_bar.is_visible_in_tree() and int(hud.health_bar.value)==game.player_hp and int(hud.health_bar.max_value)==game.MAX_HP)
	observed["visible_labels"]=labels

# Sample traversable ground against the shipped collision bodies at the normal
# avatar height. Cardinal neighbours prevent cutting diagonally through corners.
func check_saw_sightline() -> void:
	var house=game.depot.house
	for zoom in [1,2]:
		game.set_zoom_ratio(zoom)
		place(game.processors.APRONS.wood)
		for frame in 3: await physics_frame
		check("west saw stays visible at %dx zoom" % zoom,not house.parts.Roof.visible and is_equal_approx(house.parts.BackWall.scale.y,.39))
		check("rear cutaway keeps the physical storehouse closed at %dx zoom" % zoom,not house.doors_open and house.collision.collision_layer==1 and not house.is_interior_visible())
		place(Vector3(1.72,0,1.8))
		for frame in 3: await physics_frame
		check("leaving the saw restores its full roof and rear wall at %dx zoom" % zoom,house.parts.Roof.visible and is_equal_approx(house.parts.BackWall.scale.y,1.0))
	game.set_zoom_ratio(1)

func purchase_equipment_fixture() -> void:
	var book = game.inventory
	for id: String in EQUIPMENT:
		if book.complete(id): continue
		var due: Dictionary = book.remaining(id)
		for kind: String in due:
			for i in int(due[kind]): book.collect("setup-%s-%s-%d" % [id,kind,i],kind)
			check("separately paid " + id + kind,book.payment(id,kind,false,int(due[kind])))
		game._finish_purchase(id)
	game._persist_world()

func inspect_service_aisles() -> void:
	purchase_equipment_fixture()
	game.set_physics_process(false)
	await check_saw_sightline()
	var court: Vector4 = game.field_env.COURTS.back()
	var goals := {
		"saw feed": game.processors.APRONS.wood, "stone feed": game.processors.APRONS.stone,
		"kitchen feed": game.lakeshore.APRON, "roast pickup": game.lakeshore.OUTPUT_APRON,
		"counter service": game.counter.service_point.global_position, "storehouse": game.depot.APRON,
		"south gate": game.gates[0].position + Vector3.FORWARD*1.6,
		"east gate": game.gates[1].position + Vector3.LEFT*1.6,
	}
	for key: String in goals:
		check(key+" is inside the safe camp",game.field_env.is_inside_camp(goals[key]) and not game.orbit_permitted_at(goals[key]))
	check("the customer queue stays on the opposite side of the north fence",not game.field_env.is_inside_camp(game.counter.customer_point.global_position))
	check("the retired shore sites have no loading actions",not game.lakeshore.at_cooker(Vector3(-19.65,0,16.65)) and game.processors.at_station(Vector3(-15.19,0,21.2)).is_empty() and game.processors.at_station(Vector3(-18.57,0,25.55)).is_empty())
	var space:PhysicsDirectSpaceState3D=game.actor.get_world_3d().direct_space_state
	var query:=PhysicsShapeQueryParameters3D.new()
	var capsule:CapsuleShape3D=game.actor.find_children("*","CollisionShape3D",false,false)[0].shape.duplicate()
	capsule.radius=maxf(.48,capsule.radius)
	query.shape=capsule
	query.exclude=[game.actor.get_rid()]
	query.collision_mask=game.actor.collision_mask
	var grid:Dictionary={}
	var step:=.26
	for ix in range(1,ceili((court.z-court.x)/step)):
		for iz in range(1,ceili((court.w-court.y)/step)):
			var point:=Vector3(court.x+ix*step,0,court.y+iz*step)
			query.transform=Transform3D(Basis(),point+Vector3.UP*(capsule.height*.5+.06))
			if space.intersect_shape(query,1).is_empty():
				grid[Vector2i(ix,iz)]=point
	var anchor:=Vector3(1.72,0,1.8)
	var seed:=Vector2i(roundi((anchor.x-court.x)/step),roundi((anchor.z-court.y)/step))
	var seen: Dictionary={}
	var visit:Array[Vector2i]=[]
	if grid.has(seed):
		visit.append(seed)
		seen[seed]=true
	var index:=0
	while index<visit.size():
		var current:=visit[index]
		index+=1
		for direction:Vector2i in [Vector2i.LEFT,Vector2i.RIGHT,Vector2i.UP,Vector2i.DOWN]:
			var next:=current+direction
			if grid.has(next) and not seen.has(next):
				seen[next]=true
				visit.append(next)
	for key:String in goals:
		var goal:Vector3=goals[key]
		var nearest:=INF
		for cell:Vector2i in visit:
			nearest=minf(nearest,Vector2(goal.x,goal.z).distance_to(Vector2(grid[cell].x,grid[cell].z)))
		check(key+" connects to the same 0.96 m clear aisle",nearest<=.32)
		observed[key+"_sampling_error_m"]=snappedf(nearest,.001)
	observed["aisle_probe_diameter_m"]=2*capsule.radius
	observed["reachable_samples"]=seen.size()
	observed["grid_pitch_m"]=step
	for gate in game.gates:
		var inward:=Vector3.FORWARD if gate.gate_id=="gate-south" else Vector3.LEFT
		var exit:Vector3=gate.global_position-inward*1.8
		var entry:Vector3=gate.global_position+inward*1.8
		place(exit)
		for tick in 90: game.step_technical_gates(1./60.)
		await physics_frame
		check(gate.gate_id+" automatically opens from the exterior",is_equal_approx(gate.angle,PI/2) and not game.gate_button.visible)
		for endpoint:Vector3 in [entry,exit]:
			var previous:Vector3=game.actor.global_position
			game.actor.move_and_collide(endpoint-previous)
			game.previous_dry_position=previous
			game.constrain_private_snow_travel()
			var crossed:bool=game.actor.global_position.distance_to(endpoint)<.04
			check(gate.gate_id+(" traverses inward" if endpoint==entry else " traverses outward"),crossed)

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
	if stage in ["cook-interrupted","cook","pickup-roast","interrupted","serve","machines-and-owl","handoff-interrupted","handoff","second-launch","layout"]:
		park_worker_for_player_supply_test()
	await physics_frame
	check("shipping main scene loaded from disposable profile",game!=null and not game.persist_blocked and game.field_save.directory==folder)
	if failures.is_empty():
		match stage:
			"layout": await inspect_service_aisles()
			"plot-partial": await plot_partial()
			"claim": await claim()
			"delivery-interrupted": interrupt_delivery()
			"load-cooker": await load_cooker()
			"cook-interrupted": await finish_cooker(true)
			"cook": await finish_cooker(false)
			"pickup-roast": await pickup_roast()
			"interrupted": process_counter(true)
			"serve": process_counter(false)
			"machines-and-owl": await machines_and_owl()
			"handoff-interrupted": handoff(true)
			"handoff": handoff(false)
			"second-launch": second_launch()
			_: check("known fixture phase",false)
	await finish()
