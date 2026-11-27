extends Node3D

const Rules = preload("res://field_settlement.gd")
const Progress = preload("res://field_progression.gd")
const Shore = preload("res://field_lakeshore.gd")
const Counter = preload("res://field_counter.gd")
const Survivor = preload("res://field_survivor.gd")
const Transfers = preload("res://field_production_transfer.gd")
const COOK_SECONDS: float = Rules.CYCLE_SECONDS.meat
var world
var works
var transfers
var conveyors
var belt_audio_initialized := false
var belt_was_blocked := false
var cooking: float:
	get:
		return float(world.inventory.settlement.work_seconds.meat) if world else 0.0
var hot := false
var announced_finish := false
var finger := -1

func install(host: Node3D) -> void:
	world = host
	world.lakeshore = Shore.new()
	add_child(world.lakeshore)
	world.lakeshore.setup(world)
	world.processors = preload("res://field_processors.gd").new()
	add_child(world.processors)
	world.processors.setup(world)
	works = preload("res://field_worksites.gd").new()
	add_child(works)
	works.setup(world)
	world.owl = preload("res://field_owl.gd").new()
	add_child(world.owl)
	world.owl.setup(world)
	world.survivor = Survivor.new()
	add_child(world.survivor)
	world.survivor.setup(world)
	world.counter = Counter.new()
	add_child(world.counter)
	world.counter.setup(world,make_customer,serve)
	world.counter.served.connect(_meal_received)
	transfers = Transfers.new()
	add_child(transfers)
	transfers.setup(world)
	conveyors=preload("res://field_conveyors.gd").new()
	add_child(conveyors)
	conveyors.setup(world,self)
	world.counter.set_active(world.inventory.complete(Progress.SECOND), int(world.inventory.settlement.served))
	sync()
	announced_finish = ready()
	_present_production(0.)

func make_customer(choice: String) -> Node3D:
	return world.survivor.make_customer(choice)

func ready() -> bool:
	return Rules.ready_to_continue(world.inventory.settlement, world.inventory.build_order)

func can_transact() -> bool:
	return _simulation_active() and world.reset_time <= 0

func _simulation_active() -> bool:
	return world.field_ready and not world.persist_blocked and not world.closing

func sync() -> void:
	var journal: Dictionary = world.inventory.settlement
	world.opening_hud.level_continue.visible = ready() and journal.level == 1 and not world.persist_blocked
	world.opening_hud.settlement_status(journal,0)
	world.opening_hud.reflow()

func advance(dt: float) -> void:
	world.survivor.advance(dt)
	world.owl.advance(dt)
	# Existing jobs advance even when nobody is on an apron. A new handoff enters
	# the hopper after this step, so a late delivery cannot earn a head start.
	_advance_production(dt)
	if _simulation_active(): conveyors.advance(dt)
	_update_belt_mix()
	works.advance(dt)
	if can_transact(): collect_meal()
	var progress := _present_production(dt)
	world.counter.set_active(world.inventory.complete(Progress.SECOND),int(world.inventory.settlement.served))
	if world.inventory.complete(Progress.FOOD_LINE):
		world.counter.staff_food_line(Callable(conveyors,"buffer_position"))
	if can_transact(): world.counter.advance(dt)
	if ready() and not announced_finish:
		announced_finish = true
		world._event("level_complete",world.actor.global_position)
	sync_if_needed()
	if not works.active.is_empty():
		for flight in world.carry.flights:
			if flight.to == "work:"+works.active: progress = maxf(progress,flight.t)
	world.opening_hud.settlement_status(world.inventory.settlement,progress)

func sync_if_needed() -> void:
	var journal: Dictionary = world.inventory.settlement
	if world.opening_hud.level_continue.visible != (ready() and journal.level == 1 and not world.persist_blocked):
		sync()

func commit_receipt(cue: String, at: Vector3, audio_id := "") -> bool:
	world._inventory_changed()
	sync()
	if world.persist_blocked: return false
	world.carry.sync(true)
	if audio_id.is_empty():
		world._event(cue,at)
	else:
		world._event(cue,at,audio_id)
	return true

func rescue() -> bool:
	if not can_transact() or not world.inventory.settlement.survivor_paid or world.inventory.settlement.rescued: return false
	if not world.survivor.at_rescue(world.actor.global_position): return false
	world.inventory.settlement.rescued = true
	return commit_receipt("survivor_rescued",world.survivor.actor.global_position)

func claim_worker_wood(token: String) -> bool:
	if not can_transact() or not world.inventory.settlement.rescued or not world.inventory.storage_open("wood"): return false
	if not world.inventory.settlement.worker_carry_token.is_empty() or not world.inventory.settlement.worker_supply.is_empty() or world.inventory.collected.has(token): return false
	if not world.drops.has(token) or world.drops[token].kind != "wood" or not world.survivor.can_claim(token): return false
	var position_: Vector3 = world.drops[token].at
	world._remove_drop(token)
	world.inventory.settlement.worker_carry_token = token
	return commit_receipt("worker_pickup",position_)

func deliver_worker_wood() -> bool:
	if not can_transact() or not world.inventory.storage_open("wood") or not world.survivor.at_wood_receiver(): return false
	var journal: Dictionary = world.inventory.settlement
	var token: String = journal.worker_carry_token
	if token.is_empty() or world.inventory.collected.has(token):
		return false
	world.inventory.collected[token] = "wood"
	world.inventory.stored.wood += 1
	journal.worker_carry_token = ""
	journal.worker_receipts.append(token)
	journal.worker_deliveries += 1
	return commit_receipt("worker_delivery",world.depot.bins.wood.global_position)

func _meal_received(_order: int) -> void:
	world._event("meal_handoff", world.counter.customer_point.global_position)

func _update_belt_mix() -> void:
	var gain := 0.0
	var journal: Dictionary = world.inventory.settlement
	var blocked: bool = not conveyors.blocked_lane.is_empty() or journal.counter_stock >= Rules.COUNTER_RACK_CAPACITY
	if _simulation_active():
		for lane: String in conveyors.goods:
			if journal.line_load[lane] == 0: continue
			var cargo: Node3D = conveyors.goods[lane]
			if not cargo.visible: continue
			if float(journal.line_progress[lane]) >= 1.0:
				blocked = true
				continue
			var distance := cargo.global_position.distance_to(world.actor.global_position)
			gain = maxf(gain, clampf(1.0-distance/14.0, 0.0, 1.0))
	if belt_audio_initialized and blocked != belt_was_blocked and _simulation_active():
		world._event("conveyor_hold" if blocked else "conveyor_restart",world.depot.house.global_position)
	belt_audio_initialized = true
	belt_was_blocked = blocked
	world.sound.set_conveyor_proximity(gain)

func available_to_feeder(kind: String) -> bool:
	return _simulation_active() and kind in Rules.KINDS and world.inventory.is_machine_owned(kind) and int(world.inventory.settlement.hoppers[kind])+int(world.inventory.settlement.line_load[kind])+world.carry.incoming(kind,kind) < Rules.HOPPER_CAPACITY

func _running(kind: String) -> bool:
	var journal: Dictionary = world.inventory.settlement
	if not _simulation_active() or not world.inventory.is_machine_owned(kind) or journal.hoppers[kind] <= 0: return false
	return Rules.Logistics.rack(journal,kind)<Rules.Logistics.WORK_RACK

func advance_unattended(dt: float) -> void:
	if not _simulation_active(): return
	_advance_production(dt)
	conveyors.advance(dt)
	world.opening_hud.settlement_status(world.inventory.settlement,_present_production(dt))

func _can_cook() -> bool:
	return _running("meat")

func _advance_production(dt: float) -> void:
	for kind: String in Rules.KINDS:
		if not _running(kind): continue
		var seconds: float = Rules.CYCLE_SECONDS[kind]
		var elapsed: Dictionary = world.inventory.settlement.work_seconds
		if elapsed[kind] == 0:
			var cue := "cooker_start" if kind == "meat" else "process_"+kind
			var at: Vector3 = world.lakeshore.cooker_input.global_position if kind == "meat" else world.processors.input_position(kind)
			world._event(cue,at)
		elapsed[kind] = minf(seconds, float(elapsed[kind]) + dt)
		if elapsed[kind] >= seconds and not _finish_cycle(kind):
			return

func _finish_cycle(kind: String) -> bool:
	var journal: Dictionary = world.inventory.settlement
	if not _running(kind) or journal.work_seconds[kind] < Rules.CYCLE_SECONDS[kind]: return false
	journal.work_seconds[kind] = 0.0
	journal.hoppers[kind] -= 1
	if kind == "meat":
		journal.cooked += 1
		return commit_receipt("meal_ready",world.lakeshore.cooker_output.global_position)
	journal["processed_"+kind] += 1
	return commit_receipt("process_done",world.processors.output_position(kind), "plank_out" if kind == "wood" else "block_out")

func _present_production(dt: float) -> float:
	transfers.set_meal_stock(Rules.waiting_meals(world.inventory.settlement))
	var progress := 0.0
	for kind: String in Rules.KINDS:
		var running := _running(kind)
		var fraction := -1.0
		if running:
			fraction = float(world.inventory.settlement.work_seconds[kind]) / float(Rules.CYCLE_SECONDS[kind])
			progress = maxf(progress, fraction)
		transfers.show_cycle(kind,fraction)
		if kind == "meat":
			hot = running
			world.lakeshore.update_activity(hot)
		else:
			world.processors.set_running(kind,running)
	world.processors.tick(dt)
	world.lakeshore.tick(dt)
	return progress

func cook() -> bool:
	return _finish_cycle("meat")

func _meal_pickup(at:Vector3)->Vector3:
	var j:Dictionary=world.inventory.settlement
	# A paid outfeed owns every new serving until it reaches its destination.
	# Personal and worker-held servings from older saves can still be sold.
	if world.inventory.complete(Progress.FOOD_LINE):return Vector3.INF
	if not conveyors.line_live("meal_to_store") and Rules.waiting_meals(j)>0 and world.lakeshore.at_output(at):
		return world.lakeshore.cooker_output.global_position
	if j.product_store.meal>0 and conveyors.unclaimed_orders()>0 and world.depot.at_loading_area(at):
		j.product_store.meal-=1
		return conveyors.shelf_position("meal")
	return Vector3.INF

func collect_meal() -> bool:
	var journal: Dictionary = world.inventory.settlement
	if not can_transact() or not world.inventory.is_machine_owned("meat") or journal.held_meal>0 or world.counter.sale_order!=0:return false
	var at:=_meal_pickup(world.actor.global_position)
	if not at.is_finite():return false
	journal.held_meal=1
	if not commit_receipt("pickup_partial",at):return false
	world.counter.collect_meal(at)
	return true

func collect_worker_meal() -> bool:
	var journal:Dictionary=world.inventory.settlement
	if not can_transact() or not journal.rescued or not world.inventory.is_machine_owned("meat") or journal.worker_meal>0 or conveyors.unclaimed_orders()==0:return false
	var at:=_meal_pickup(world.survivor.actor.global_position)
	if not at.is_finite():return false
	journal.worker_meal=1
	if not commit_receipt("pickup_partial",at):return false
	world.counter.collect_worker_meal(at)
	return true

func serve(order: int) -> bool:
	if not can_transact() or not world.counter.awaiting_payment(order): return false
	var journal: Dictionary = world.inventory.settlement
	if world.counter.belt_serving:
		if not world.inventory.complete(Progress.FOOD_LINE) or journal.counter_stock < 1 or journal.served+1!=order: return false
		journal.counter_stock-=1
		journal.served+=1
		return commit_receipt("meal_served",world.counter.payment_rest.global_position)
	var worker: bool = world.counter.worker_serving
	var at: Vector3 = world.survivor.actor.global_position if worker else world.actor.global_position
	if not world.counter.at_service(at): return false
	if not world.inventory.complete(Progress.SECOND) or journal.served + 1 != order or int(journal.worker_meal if worker else journal.held_meal) != 1: return false
	if worker: journal.worker_meal = 0
	else: journal.held_meal = 0
	journal.served += 1
	return commit_receipt("meal_served",at)

func enter_next_level() -> bool:
	if not can_transact() or not ready() or world.inventory.settlement.level != 1: return false
	world.inventory.settlement.level = 2
	return commit_receipt("next_level",world.actor.global_position)

func handle_input(event: InputEvent) -> bool:
	if conveyors and conveyors.menu.handle(event):return true
	var button: Button = world.opening_hud.level_continue
	if event is InputEventScreenDrag and finger != -1 and event.index == finger: return true
	if event is InputEventScreenTouch and finger != -1 and event.index == finger:
		if not event.pressed: finger = -1
		return true
	if not button.visible: return false
	if event is InputEventKey and event.pressed and not event.echo and event.physical_keycode == KEY_ENTER:
		enter_next_level()
		return true
	if event is InputEventScreenTouch and event.pressed and not event.canceled and button.get_global_rect().has_point(event.position):
		finger = event.index
		enter_next_level()
		return true
	if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT and button.get_global_rect().has_point(event.position):
		enter_next_level()
		return true
	return false

const BLOCKED_BELT := {
	"wood":"Move the saw or storehouse to reconnect the wood belt.",
	"planks":"Move the saw or storehouse to reconnect the plank belt.",
	"stone":"Move the drill or storehouse to reconnect the stone belt.",
	"blocks":"Move the drill or storehouse to reconnect the block belt.",
	"meat":"Move the cooker or storehouse to reconnect the meat belt.",
	"meal_to_store":"Move the cooker or storehouse to reconnect the roast belt.",
	"meal":"Move the cooker or counter to reconnect meal service.",
	"stored_meal":"Move the storehouse or counter to reconnect meal service."
}

func hint(previous: String, danger: bool) -> String:
	if conveyors and not conveyors.menu.selected.is_empty() and world.inventory.offer_open(conveyors.menu.selected):return world.build_hint(conveyors.menu.selected)
	if conveyors and not conveyors.blocked_lane.is_empty() and world.field_env.is_inside_camp(world.actor.global_position):
		return BLOCKED_BELT[conveyors.blocked_lane]
	var journal: Dictionary = world.inventory.settlement
	if journal.level == 2 and world.next_project.is_empty():
		return "Level 2 preview · All Level 1 plots complete. The camp is open."
	if ready(): return "Level 1 complete · Continue to Level 2."
	if works.plot.visible and world.actor.position.distance_to(works.PLOT_AT) < 2.0:
		return "Rescue survivor  ·  %d wood left" % Progress.units(world.inventory.survivor_cost - int(journal.survivor_wood))
	if world.depot.apron.visible and (world.depot.at_apron(world.actor.position) or world.depot.at_loading_area(world.actor.position) or (world.depot.upgrade_mark.visible and world.depot.on_upgrade_side(world.actor.position))): return previous
	if works.active in Rules.KINDS:
		return {"wood":"Loading saw…","stone":"Loading drill…","meat":"Loading cooker…"}[works.active]
	if journal.survivor_paid and not journal.rescued and world.survivor.at_rescue(world.actor.global_position): return "Approach the survivor."
	if not world.next_project.is_empty(): return previous
	if not world.inventory.complete(Progress.SECOND): return previous
	var hint_: String
	var target := Vector3.INF
	if journal.held_meal > 0:
		hint_ = "Deliver the meal inside the north counter."
		target = world.counter.service_point.global_position
	elif journal.worker_meal > 0 or world.counter.worker_serving:
		hint_ = "Survivor serving the north counter."
		target = world.counter.service_point.global_position
	elif conveyors.line_live("stored_meal") and (hot or conveyors.unclaimed_orders()>0 or journal.counter_stock>0 or Rules.waiting_meals(journal)>0):
		hint_ = "Cooker feeds the counter automatically." if world.carry.available_on_shelf("meat")>0 or hot or journal.counter_stock>0 or journal.line_load.values().has(1) or journal.product_store.meal>0 else "Bring meat to the storehouse to supply the cooker."
		if world.inventory.carried.meat>0:target=world.depot.apron.global_position
	elif conveyors.line_live("meal_to_store") and journal.product_store.meal>0 and conveyors.unclaimed_orders()>0:
		hint_ = "Collect a roast at the storehouse for the north counter."
		target = world.depot.apron.global_position
	elif not conveyors.line_live("meal_to_store") and Rules.waiting_meals(journal) > 0:
		hint_ = "Collect a roast from the cooker outfeed."
		target = world.lakeshore.output_apron_position()
	elif hot:
		hint_ = "Cooking  ·  Sending roast to storage." if conveyors.line_live("meal_to_store") else "Cooking  ·  The roast will wait at the outfeed."
	elif not journal.rescued:
		hint_ = "Rescue survivor · %d wood at the southwest plot" % Progress.units(world.inventory.survivor_cost-int(journal.survivor_wood)) if not journal.survivor_paid else "Approach the survivor by the south grove."
		target = works.PLOT_AT if not journal.survivor_paid else world.survivor.RESCUE
	elif journal.served == 0:
		if conveyors.line_live("meat"):
			hint_ = "Deliver meat to the storehouse for the cooker."
			if world.inventory.carried.meat>0:target=world.depot.apron.global_position
		else:
			hint_ = "Take meat to the camp cooker inlet." if world.inventory.carried.meat > 0 else "Hunt for meat to load the camp cooker."
			if world.inventory.carried.meat > 0: target = world.lakeshore.apron_position()
	elif not world.inventory.complete(Progress.TOWER) or not world.inventory.complete(Progress.AXES):
		return previous
	elif journal.processed_wood == 0:
		var automatic:bool = conveyors.line_live("wood")
		hint_ = "Deliver wood to the storehouse for the saw." if automatic else "Take wood to the saw inside the north fence."
		if world.inventory.carried.wood > 0: target = world.depot.apron.global_position if automatic else world.processors.APRONS.wood
	elif journal.processed_stone == 0:
		var automatic:bool = conveyors.line_live("stone")
		hint_ = "Deliver stone to the storehouse for the drill." if automatic else "Take stone to the drill inside the north fence."
		if world.inventory.carried.stone > 0: target = world.depot.apron.global_position if automatic else world.processors.APRONS.stone
	elif journal.owl_hits == 0:
		hint_ = "Meet a wolf outside camp with your owl."
	elif journal.worker_deliveries == 0:
		hint_ = "Let the survivor deliver wood to the storehouse."
	else:
		return previous
	if target.is_finite() and world.actor.global_position.distance_to(target) > 2.5:
		var heading: Vector2 = world.camera.unproject_position(target) - world.camera.unproject_position(world.actor.global_position)
		var octant := posmod(roundi(heading.angle()/(PI/4.0)),8)
		var arrows := ["→","↘","↓","↙","←","↖","↑","↗"]
		hint_ += "  %s %d m" % [arrows[octant],roundi(world.actor.global_position.distance_to(target))]
	return ("Wolves nearby  ·  " if danger else "") + hint_


func cancel_cooking() -> void:
	# A fallen carrier drops the in-flight presentation. Paid hopper stock and
	# machine work remain in the settlement ledger for the next simulation tick.
	works.cancel()
