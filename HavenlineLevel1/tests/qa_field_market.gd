extends "res://tests/field_route.gd"
## The ordinary scene opens a returning camp, then walks through typed counter and survival states.
const Store = preload("res://field_save.gd")
const Market = preload("res://field_market.gd")
const Profile = preload("res://tests/lifecycle_test_profile.gd")
@warning_ignore("unused_private_class_variable")
const PROJECT = preload("res://field_opening.tscn")
var checks := {}
var ledger
var journal: Dictionary
var loop
var counter
var captures := OS.get_environment("MARKET_CAPTURE")

func check(label: String, outcome: bool) -> void:
	checks[label] = outcome
	if not outcome: push_error(label)

func park(at: Vector3) -> void:
	steer(Vector2.ZERO)
	field.actor.global_position = at
	field.previous_dry_position = at
	field.actor.velocity = Vector3.ZERO

func wait_until(condition: Callable, limit: int) -> bool:
	for tick in limit:
		await physics_frame
		if condition.call(): return true
	return false

func photo(label: String) -> void:
	if captures.is_empty(): return
	field.set_physics_process(false)
	var following: Vector3 = camera.global_position
	camera.global_position = counter.to_global(Vector3(0,.52,-.15)) + field.camera_follow_offset
	camera.force_update_transform()
	await process_frame
	RenderingServer.force_draw(false)
	root.get_texture().get_image().save_jpg(captures.path_join(label+".jpg"),.95)
	camera.global_position = following
	field.set_physics_process(true)

func find_case() -> void:
	await check_everything()
	print("FIELD_MARKET ",JSON.stringify({"checks":checks,"money":ledger.till_balance(),"served":journal.served,"paid_goods":journal.market.sold}))
	field.set_physics_process(false)
	await Profile.drain_field_audio(self,field)
	field.queue_free()
	await process_frame
	quit(1 if false in checks.values() else 0)

func run() -> void:
	var guard := Store.Profile.new()
	if not guard.configure(OS.get_cmdline_user_args()): quit(2); return
	field = PROJECT.instantiate()
	root.add_child(field)
	camera = field.camera
	origin = root.get_visible_rect().size*Vector2(.30,.72)
	ledger = field.inventory
	journal = ledger.settlement
	loop = field.settlement_loop
	counter = field.counter
	await find_case()

func check_everything() -> void:
	var home: Vector3 = counter.to_global(Vector3(3.1,0,3.5))
	park(home)
	counter.arrival_clock = 200.
	check("old paid workshop profile opens in the new schema",not field.persist_blocked and ledger.complete("quarry_drill") and ledger.snapshot().version==13)
	# These are legitimate raw credits matched against each synthesized historic sale and prepared input.
	for n in 12: ledger.collect("market-meat-%s" % n,"meat")
	for n in ledger.survivor_cost+3: ledger.collect("market-wood-%s" % n,"wood")
	ledger.carried.meat -= 12
	ledger.carried.wood -= ledger.survivor_cost+3
	journal.cooked += 12
	journal.held_meal += 2
	journal.product_store.meal += 2
	journal.served = 8
	journal.market.sold.meal = 8
	journal.market.earned = 8
	journal.market.counter_cash = 8
	journal.processed_wood += 3
	journal.product_store.planks += 1
	journal.hand_products.planks += 1
	journal.market.counter_products.planks += 1
	journal.survivor_paid = true
	journal.survivor_wood = ledger.survivor_cost
	journal.rescued = true
	field.survivor.actor.global_position = home + Vector3(1,0,0)
	field._inventory_changed()
	check("paid fixture and new typed accounting agree",not field.persist_blocked)
	counter.set_active(false,8)
	counter.set_active(true,8)
	counter.arrival_clock = 0.
	check("first displayed developed order asks for two meals",await wait_until(func():return journal.market.order.get("goods",{})=={"meal":2},360))
	check("held goods do not make a customer pay",journal.served==8 and ledger.till_balance()==8)
	park(counter.service_point.global_position)
	await physics_frame
	await physics_frame
	check("one visit stocks both meals and collects the old cash",journal.held_meal==0 and journal.counter_stock==2 and journal.pocket_cash==8 and ledger.till_balance()==0)
	check("counter leaves the player's planks in the pack",journal.hand_products.planks==1 and journal.market.counter_products.planks==1 and not loop.counter_accepts("planks"))
	park(home)
	check("customer self-serves a two-item order without anyone at counter",await wait_until(func():return journal.served==9,780))
	await photo("01-first-unstaffed-order")
	if not captures.is_empty():
		field.set_zoom_ratio(2.)
		await wait_until(func():return counter.cash_in_exchange()==0,50)
		await photo("02-counter-cash")
		field.set_zoom_ratio(1.)
	check("next developed order requests only a meal",await wait_until(func():return journal.market.order.get("goods",{})=={"meal":1},540))
	check("stored planks cannot substitute for a meal",journal.counter_stock==0 and journal.market.counter_cash==2)
	var readback = field.Inventory.new()
	readback.configure(ledger.configured_costs)
	check("reopening preserves the quoted whole basket",field.field_save.load_into(readback)==OK and readback.settlement.market.order==journal.market.order)
	# Take the old payment and the full available meal stock via the survivor's station APIs.
	field.survivor.actor.global_position = field.depot.apron.global_position
	var worked: bool = loop.collect_worker_meal()
	check("owned worker loads both meals and leaves warehouse planks",worked and journal.worker_meal==2 and journal.product_store.planks==1 and journal.market.worker_products.planks==0)
	field.survivor.actor.global_position = counter.service_point.global_position
	worked = loop.worker_stock_counter()
	check("owned worker drops both meals and picks up all posted cash",worked and journal.worker_meal==0 and journal.counter_stock==2 and journal.market.worker_cash==2 and ledger.till_balance()==0)
	check("a concurrent second pickup cannot claim the same money",not loop.exchange.visit_counter(false,counter.service_point.global_position))
	field.survivor.actor.global_position = field.depot.apron.global_position
	worked = loop.worker_bank_cash()
	check("owned worker banks its payment once",worked and journal.market.worker_cash==0 and journal.house_cash==2)
	field.survivor.actor.global_position = home + Vector3(1,0,0)
	check("customer buys one meal and leaves the rest of the stock",await wait_until(func():return journal.served==10,780) and ledger.till_balance()==1 and journal.market.sold.planks==0 and journal.counter_stock==1 and journal.market.counter_products.planks==1)
	if not captures.is_empty():
		field.set_zoom_ratio(2.)
		for tick in 9: await physics_frame
		await photo("03-meal-only-order")
	check("physical sale contains only the meal",counter.sale_goods.size()==1 and counter.sale_goods[0].kind=="meal")
	check("cash and legacy stock pass exact save validation",not field.persist_blocked and readback.restore(ledger.snapshot()))
