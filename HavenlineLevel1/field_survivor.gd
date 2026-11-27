extends Node3D

const Human = preload("res://field_human.gd")
const Crew = preload("res://field_crew.gd")
const Wildlife = preload("res://field_wildlife.gd")
const RESCUE := Vector3(-5.10,0,9.90)
const PINE := Vector2(-3.60,9.10)
# A three-quarter flank keeps both gloves and the contact side of the trunk visible.
const STANCE := Vector3(-4.34,0,9.04)
const PINE_APPROACH := Vector3(-3.17,0,10.24)
const READY := Vector3(-2.7,0,1.72)
# Workers have their own travel pace in world metres per second.
const EMPTY_SPEED := 3.6
const LADEN_SPEED := 2.8
const ACCELERATION := 7.2
const BRAKING := 10.0
const FOOT_RADIUS := .25
const SUPPLIES := ["wood","stone","meat"]
var world
var actor: Node3D
var tree
var phase := "waiting_rescue"
var contacts := 0
var contact_position := Vector3.INF
var step_cycle := .0
var travel_speed := 0.0
var restored_service := ""
var swing_time := .0
var swing_landed := false
var pickup_token := ""
var drop_floor := 0
var waiting := .0
var route: Array[Vector3] = []
var supply_model: Node3D
var pack: Node3D
var pack_view = preload("res://field_inventory.gd").new()
var assigned_bank: Node3D
var timber_approach: Array[Vector3] = []
var forage_token := ""
var bank_approach: Array[Vector3] = []
var bank_swing := 0.0
var bank_hit := false
var failed_swings := 0
var previous_tree := ""
var previous_bank := ""
var work_clock := 0.0
var deferred_sources := {}
const CAMP_DUTIES := ["serve","assist","feed","field"]
const FIELD_DUTIES := ["mining","wood","forage","hunt"]
var camp_cursor := 0
var priority_order_available := true
var field_cursor := 0
var assisted_plot := ""
var transfer_mesh: Node3D
var spend_kind := ""
var delivery_stream: Array[Dictionary] = []
var receipt_departure:=Vector3.ZERO
var launch_window:=.58
var unload_packets: Array[Dictionary] = []
var next_packet := 0
var dispatch_count := 0
var outdoor_route = preload("res://field_home_route.gd").new()
const WORK_RADIUS := 24.0
const PICKUP_REACH := 1.22
# In a busy camp the worker checks back after a bounded field circuit.
# A rich stand can fill one complete 500-unit stack first.
const FIELD_SHIFT_SECONDS := 38.
const WORK_WAIT_BUNDLES := 12
var shift_seconds := 0.0
var wildlife: Node3D
var hunt_contacted := false
var hunt_elapsed := 0.0
var hunt_retry := 0.0
var hunt_goal := Vector3.INF
var hunt_replans := 0
var defender: Node3D
var retaliation := {}
var defend_elapsed := 0.0
var defend_landed := false
var hit_flare := 0.0
var fallen_elapsed := .7
var health_label: Label3D
# Clear both open leaves before turning laterally on either side of the gate.
const GATE_LANDING := 2.55
const RAW_RULES = preload("res://field_settlement.gd")

func make_customer(id: String) -> Node3D:
	if id not in ["customer_male_01","customer_female_01"]: return null
	var person := Human.new()
	person.configure(id)
	return person

func setup(host: Node3D) -> void:
	world = host
	actor = Human.new()
	actor.name = "RescuedForester"
	actor.position = RESCUE
	actor.rotation.y = -.50
	actor.configure("survivor_male_01")
	actor.add_to_group("snow_track_survivors")
	add_child(actor)
	health_label = Label3D.new()
	health_label.name = "SurvivorHealth"
	health_label.position.y = 1.9
	health_label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	health_label.font_size = 29
	health_label.pixel_size = .007
	health_label.modulate = Color("#ffd49a")
	health_label.hide()
	actor.add_child(health_label)
	wildlife = Wildlife.new()
	add_child(wildlife)
	wildlife.setup(world)
	pack = preload("res://field_carry.gd").new()
	add_child(pack)
	# B at 8 s: the top of the carried food stands roughly 2.3 worker heights.
	# The full six balances stay in worker_load independent of representative meshes.
	pack.visual_top = 1.50*2.30/.80
	pack.fit_to_viewport = false
	pack.setup(pack_view,actor,world.FieldArt.make)
	pack.rack.scale = Vector3.ONE*.80
	_sync_pack()
	var journal: Dictionary = world.inventory.settlement
	camp_cursor = posmod(int(journal.served)+int(journal.processed_wood)+int(journal.processed_stone),CAMP_DUTIES.size())
	field_cursor = posmod(int(journal.worker_deliveries),FIELD_DUTIES.size())
	tree = world.add_resource_source("survivor-work-pine","wood",PINE,1)
	if journal.rescued and not Crew.survivor_alive(journal):
		phase = "fallen"
		actor.hide()
	elif _has_finished_goods():
		restored_service = "cooker_output"
		actor.position = _cooked_apron()
		_go_to_counter()
	elif not world.inventory.settlement.worker_supply.is_empty():
		restored_service = "store"
		actor.position = _shelf_apron()
		_begin_supply_run(world.inventory.settlement.worker_supply)
	elif not world.inventory.settlement.worker_carry_token.is_empty():
		actor.position = STANCE
		_begin_inbound(true)
	elif world.inventory.settlement.worker_load.values().any(func(n): return n > 0):
		actor.position = READY
		_begin_bin_delivery()
	elif world.inventory.settlement.rescued:
		actor.position = READY
		phase = "waiting_storage"

func at_rescue(at: Vector3) -> bool:
	return phase == "waiting_rescue" and world.inventory.settlement.get("survivor_paid",false) and at.distance_to(actor.global_position) <= 1.46

func can_claim(token: String) -> bool:
	if phase != "pickup" or token != pickup_token or not world.drops.has(token) or not is_instance_valid(tree): return false
	var item: Dictionary = world.drops[token]
	return item.kind == "wood" and item.at.distance_to(actor.global_position) <= .24 and item.from.distance_to(tree.global_position+Vector3.UP*.29) < .04 and item.age >= .41

func at_wood_receiver() -> bool:
	return phase == "unload" and actor.global_position.distance_to(_shelf_apron()) < .23

func _begin_inbound(carrying: bool) -> void:
	var portal: Vector3 = world.gates[0].position
	var approach := Vector3(0,0,portal.z+GATE_LANDING)
	route = _outdoor_path(actor.position,approach)
	route.append(Vector3(0,0,portal.z-GATE_LANDING))
	route.append(Vector3(-2.65,0,2.14))
	if carrying and world.inventory.storage_open("wood"): route.append(_shelf_apron())
	else: route.append(READY)
	phase = "carrying" if carrying else "first_walk"

func _sync_pack() -> void:
	var journal: Dictionary = world.inventory.settlement
	var display: Dictionary = journal.worker_load.duplicate()
	if journal.worker_carry_token != "": display.wood += 1
	if journal.worker_supply != "": display[journal.worker_supply] += 1
	pack_view.carried = display
	var market: Dictionary = journal.get("market",{})
	var products: Dictionary = market.get("worker_products",{})
	pack_view.settlement.hand_products = {"planks":int(products.get("planks",0)),"blocks":int(products.get("blocks",0))}
	pack_view.settlement.held_meal = int(journal.worker_meal)
	pack_view.settlement.pocket_cash = int(market.get("worker_cash",0))
	pack.sync()
	actor.bundle.hide()

func _begin_outbound() -> bool:
	var portal: Vector3 = world.gates[0].position
	var staging := Vector3(portal.x,0,portal.z+GATE_LANDING)
	var outside := _in_work_area(actor.global_position)
	var start := actor.global_position if outside else staging
	if not _choose_tree(start): return false
	route.clear()
	if not outside:
		route.assign([Vector3(-2.65,0,2.14),Vector3(portal.x,0,portal.z-GATE_LANDING),staging])
	route.append_array(timber_approach)
	phase="to_tree"
	return true

func _paid_walkways():
	if not world or not world.settlement_loop or not world.settlement_loop.conveyors or not world.camp_layout:
		return null
	var purchases: Array = world.inventory.build_order
	if world.Progress.SUPPLY_LINE not in purchases and world.Progress.FOOD_LINE not in purchases:
		return null
	# Layout is restored after the survivor and conveyors are constructed.
	# Rebuild before the first reservation or stride after a purchase or move.
	var belts = world.settlement_loop.conveyors
	belts.refresh_paths()
	return belts.network

func _service_apron(kind: String, ordinary: Vector3) -> Vector3:
	var network = _paid_walkways()
	if network:
		return network.accessible_service(kind)
	return Vector3(ordinary.x,0,ordinary.z)

func _shelf_apron() -> Vector3:
	return _service_apron("store",world.depot.apron.global_position)

func _cooked_apron() -> Vector3:
	return _service_apron("cooker_output",world.lakeshore.output_apron_position())

func _counter_apron() -> Vector3:
	return _service_apron("counter",world.counter.service_point.global_position)

func _supply_apron(kind: String) -> Vector3:
	var ordinary: Vector3 = world.lakeshore.apron_position() if kind == "meat" else world.processors.apron_position(kind)
	# A worker can also carry building tender to a machine's unbuilt plot.
	if not world.inventory.is_machine_owned(kind): return ordinary
	return _service_apron(kind,ordinary)

func _available_surplus(kind: String) -> int:
	var stock: int = world.carry.available_on_shelf(kind)
	# Keep reserved player flights intact. A waiting cook/processor may take one
	# unit even while the next building still needs the same raw material.
	var remaining: Dictionary = world.inventory.remaining(world.next_project)
	return mini(stock,maxi(1,stock-int(remaining.get(kind,0))))

func _next_supply() -> String:
	if not world.inventory.complete(world.Progress.SECOND): return ""
	for offset in SUPPLIES.size():
		var kind: String = SUPPLIES[(dispatch_count+offset)%SUPPLIES.size()]
		if not world.settlement_loop.conveyors.line_live(kind) and world.settlement_loop.available_to_feeder(kind) and _available_surplus(kind)>0 and _supply_apron(kind).is_finite(): return kind
	return ""

func _begin_supply_run(kind: String) -> void:
	supply_model = world.FieldArt.make(kind,.43)
	actor.add_child(supply_model)
	supply_model.hide()
	_sync_pack()
	supply_model.position = Vector3(0,.58,.235)
	route.assign([_supply_apron(kind)])
	phase = "supply_out"

func _needs_customer_meat() -> bool:
	var belts=world.settlement_loop.conveyors
	if world.settlement_loop.worker_market_needs("meal")==0 or belts.line_live("meat"):
		return false
	var journal:Dictionary=world.inventory.settlement
	if journal.hoppers.meat>0 or RAW_RULES.waiting_meals(journal)>0:
		return false
	return (
		world.settlement_loop.available_to_feeder("meat")
		and _available_surplus("meat")>0
		and _supply_apron("meat").is_finite()
	)

func _leave_shelf() -> void:
	if _has_finished_goods():
		world.settlement_loop.worker_bank_unrequested_goods()
		_sync_pack()
	if _worker_cash()>0:
		world.settlement_loop.worker_bank_cash()
		_sync_pack()
	# Reserve one early service opportunity per field shift. A visible customer
	# can be served from stored meat before the porter sets out on a long haul.
	# Ordinary rotation still supplies the saw, quarry and construction plots.
	if priority_order_available and world.counter and world.counter.active:
		if _can_fetch_meal():
			priority_order_available=false
			_to_cooker()
			return
		if _needs_customer_meat():
			priority_order_available=false
			_load_hopper_stock("meat")
			return
	# Advance after each opportunity so a busy kitchen, full stockroom or a
	# stream of customers cannot starve an open contract or field gathering.
	for offset in CAMP_DUTIES.size():
		var duty: String = CAMP_DUTIES[camp_cursor]
		camp_cursor = (camp_cursor+1)%CAMP_DUTIES.size()
		match duty:
			"serve":
				if _can_deliver_counter():
					_go_to_counter()
					return
				if _can_fetch_meal():
					_to_cooker()
					return
			"assist":
				if _prepare_assistance(): return
			"feed":
				var kind := _next_supply()
				if not kind.is_empty():
					_load_hopper_stock(kind)
					return
			"field":
				_start_field_job()
				return

func _load_hopper_stock(kind: String) -> void:
	dispatch_count = (SUPPLIES.find(kind)+1)%SUPPLIES.size()
	var journal: Dictionary = world.inventory.settlement
	var space := RAW_RULES.HOPPER_CAPACITY-int(journal.hoppers[kind])-int(journal.line_load[kind])-int(world.carry.incoming(kind,kind))
	var amount := mini(_available_surplus(kind),mini(worker_space(kind),space))
	if amount <= 0: return
	world.inventory.stored[kind] -= amount
	journal.worker_supply = kind
	journal.worker_load[kind] += amount-1
	if world.settlement_loop.commit_receipt("worker_pickup",actor.global_position):
		_begin_supply_run(kind)

func _advance_supply(dt: float) -> void:
	var journal: Dictionary = world.inventory.settlement
	var kind: String = journal.worker_supply
	# A connection may be bought while the porter is already on the way,
	# or after this load was saved. Return that owned cargo to its own bay.
	if phase in ["supply_out","supply_unload"] and world.settlement_loop.conveyors.line_live(kind):
		supply_model.hide()
		_sync_pack()
		route.assign([_shelf_apron()])
		phase = "supply_return"
	match phase:
		"supply_out":
			var apron := _supply_apron(kind)
			if not apron.is_finite():
				route.assign([_shelf_apron()])
				phase = "supply_return"
				return
			route.assign([apron])
			var reached := _walk_route(dt,true)
			actor.bundle.hide()
			if reached:
				waiting = 0.0
				phase = "supply_unload"
		"supply_unload":
			var recognized: bool = world.lakeshore.at_cooker(actor.global_position) if kind == "meat" else world.processors.at_station(actor.global_position) == kind
			if not recognized or actor.global_position.distance_to(_supply_apron(kind)) > .42:
				supply_model.hide()
				_sync_pack()
				phase = "supply_out"
				return
			# The player may have filled this hopper during the trip. Carry the
			# unit back to its own shelf instead of discarding it or overfilling.
			if not world.settlement_loop.available_to_feeder(kind):
				supply_model.hide()
				_sync_pack()
				route.assign([_shelf_apron()])
				phase = "supply_return"
				return
			if not supply_model.visible:
				supply_model.show()
				pack_view.carried[kind] -= 1
				pack.sync()
			waiting += dt
			var t := clampf(waiting/.16,0.,1.)
			var target: Vector3 = world.lakeshore.cooker_input.global_position if kind=="meat" else world.processors.input_position(kind)
			supply_model.global_position = _rack_from(kind).lerp(target,t)+Vector3.UP*.22*sin(PI*t)
			if t >= 1.0:
				journal.hoppers[kind] += 1
				if journal.worker_load[kind] > 0:
					journal.worker_load[kind] -= 1
					if world.settlement_loop.commit_receipt("spend_"+kind,target):
						waiting = 0.
						supply_model.hide()
						_sync_pack()
					return
				journal.worker_supply = ""
				if world.settlement_loop.commit_receipt("spend_"+kind,target):
					supply_model.queue_free()
					_sync_pack()
					pack.rack.show()
					route.assign([_shelf_apron()])
					phase = "supply_back"
		"supply_return":
			var reached := _walk_route(dt,true)
			actor.bundle.hide()
			if reached:
				world.inventory.stored[kind] += 1+int(journal.worker_load[kind])
				journal.worker_load[kind] = 0
				journal.worker_supply = ""
				if world.settlement_loop.commit_receipt("deposit_"+kind,actor.global_position):
					supply_model.queue_free()
					_sync_pack()
					_start_field_job()
		"supply_back":
			if _walk_route(dt,false): _leave_shelf()

func _travel_clear(start: Vector3, end: Vector3, radius: float) -> bool:
	return world.field_env.travel_clear(start,end,radius)

func _has_cargo() -> bool:
	var journal: Dictionary = world.inventory.settlement
	if _has_finished_goods() or _worker_cash()>0 or journal.worker_supply != "" or journal.worker_carry_token != "": return true
	return journal.worker_load.values().any(func(amount): return amount > 0)

func _has_finished_goods() -> bool:
	var journal: Dictionary = world.inventory.settlement
	return journal.worker_meal>0 or journal.get("market",{}).get("worker_products",{}).values().any(func(amount):return amount>0)

func _can_deliver_counter() -> bool:
	if not world.counter.active or not _counter_apron().is_finite(): return false
	if world.inventory.till_balance() > world.counter.cash_in_exchange(): return true
	var journal: Dictionary = world.inventory.settlement
	if int(journal.worker_meal)>0 and world.settlement_loop.counter_accepts("meal"): return true
	var products: Dictionary = journal.market.worker_products
	for kind: String in products:
		if int(products[kind])>0 and world.settlement_loop.counter_accepts(kind): return true
	return false

func _worker_cash() -> int:
	return int(world.inventory.settlement.get("market",{}).get("worker_cash",0))

func _walk(destination: Vector3, dt: float, carrying := false) -> bool:
	var before := actor.global_position
	if not destination.is_finite():
		travel_speed = 0.
		actor.pose("idle",step_cycle)
		return false
	destination.y = before.y
	var waypoint := destination
	var network = _paid_walkways()
	if world.camp_active and world.field_env.is_inside_camp(before) and world.field_env.is_inside_camp(destination) and world.camp_layout:
		if network:
			waypoint = network.walker_waypoint(before,destination)
			if not waypoint.is_finite(): waypoint = before
		else:
			waypoint = world.camp_layout.next_waypoint(before,destination,FOOT_RADIUS)
	var heading := before.direction_to(waypoint)
	var distance := before.distance_to(waypoint)
	if distance <= .01:
		travel_speed = 0.
		actor.pose("idle",step_cycle)
		return before.distance_to(destination) <= .025
	var desired_yaw := atan2(heading.x,heading.z)
	var turn := angle_difference(actor.rotation.y,desired_yaw)
	if actor.forester_gait.turn_towards(actor, desired_yaw, dt, travel_speed < .6):
		travel_speed = 0.
		actor.bundle.hide()
		return false
	actor.rotation.y += clampf(turn,-8.5*dt,8.5*dt)
	var loaded := carrying or _has_cargo()
	var cruise := LADEN_SPEED if loaded else EMPTY_SPEED
	var corner_limit := lerpf(cruise,cruise*.38,smoothstep(.3,1.9,absf(turn)))
	var speed_limit := minf(corner_limit,sqrt(2.*BRAKING*distance))
	travel_speed = move_toward(travel_speed,speed_limit,(ACCELERATION if speed_limit > travel_speed else BRAKING)*dt)
	var next := before.move_toward(waypoint,travel_speed*dt)
	var inside_step: bool = network != null and world.field_env.is_inside_camp(before) and world.field_env.is_inside_camp(next)
	if not _travel_clear(before,next,FOOT_RADIUS) or (inside_step and not network.pedestrian_clear(before,next,FOOT_RADIUS)):
		travel_speed = 0.
		actor.pose("idle",step_cycle)
		return false
	actor.global_position = next
	var meters := before.distance_to(next)
	var pace := meters/maxf(dt,.0001)
	step_cycle = fposmod(step_cycle+meters/actor.forester_gait.stride_for_speed(pace),1.)
	actor.travel_pose(step_cycle,pace,loaded)
	actor.bundle.hide()
	return next.distance_to(destination) <= .015

func _walk_route(dt: float, carrying: bool) -> bool:
	if not route.is_empty() and _walk(route[0],dt,carrying):
		route.pop_front()
	return route.is_empty()

func advance(dt: float) -> void:
	if not actor or world.persist_blocked or world.reset_time>0: return
	work_clock+=dt
	var hunter := actor.global_position if phase in ["hunt_approach","hunt_strike"] else Vector3.INF
	wildlife.advance(dt,hunter)
	var journal: Dictionary = world.inventory.settlement
	if journal.rescued and not Crew.survivor_alive(journal):
		_advance_fallen(dt)
		return
	if phase == "fallen":
		_return_replacement()
	hit_flare = maxf(0.0,hit_flare-dt)
	health_label.visible = hit_flare>0.0
	actor.forester_gait.pivot_frame = false
	if not _defend(dt): _advance_tasks(dt)
	if actor.mode=="travel" and not actor.forester_gait.pivot_frame:
		actor.forester_gait.settle_contact(dt,actor)
	else:
		actor.forester_gait.previous_points.clear()
		actor.forester_gait.marker.fill(-1)
		actor.forester_gait.correction.fill(Vector3.ZERO)

func can_defend() -> bool:
	return is_instance_valid(actor) and actor.is_visible_in_tree() and Crew.survivor_alive(world.inventory.settlement)

func provoked(attacker: Node3D) -> bool:
	return is_instance_valid(attacker) and float(retaliation.get(attacker.get_instance_id(),-1.0))>world.simulation_time

func apply_enemy_contact(attacker: Node3D, damage: int) -> bool:
	if damage<=0 or not can_defend() or not world.settlement_loop.can_transact(): return false
	if not is_instance_valid(attacker) or attacker not in world.enemies: return false
	var at := actor.global_position
	if at.distance_squared_to(attacker.global_position)>4.84 or not _travel_clear(attacker.global_position,at,.08):
		return false
	var journal: Dictionary = world.inventory.settlement
	var loss := mini(damage,int(journal.get("survivor_hp",Crew.SURVIVOR_HP)))
	journal.survivor_hp = int(journal.get("survivor_hp",Crew.SURVIVOR_HP))-loss
	if not world.settlement_loop.commit_receipt("survivor_hit",at,"hit"): return false
	health_label.text = "%d / %d" % [journal.survivor_hp,Crew.SURVIVOR_HP]
	hit_flare = 2.4
	world._combat_number(at+Vector3.UP*1.45,"−%d" % loss,Color("#ffc196"),actor)
	if journal.survivor_hp == 0:
		phase = "fallen"
		fallen_elapsed = 0.0
		defender = null
		if is_instance_valid(transfer_mesh): transfer_mesh.queue_free()
		if is_instance_valid(supply_model): supply_model.queue_free()
		for flight: Dictionary in delivery_stream:
			if is_instance_valid(flight.get("mesh")): flight.mesh.queue_free()
		delivery_stream.clear()
		pack.rack.hide()
		world._event("survivor_fallen",at,"defeat")
		return true
	if defender != attacker:
		defender = attacker
		defend_elapsed = -.15
		defend_landed = false
	return true

func _advance_fallen(dt: float) -> void:
	fallen_elapsed += dt
	if fallen_elapsed<.55:
		actor.pose("idle",step_cycle)
		actor.rotation.z = 1.41*smoothstep(0.0,.45,fallen_elapsed)
	else:
		actor.hide()

func _return_replacement() -> void:
	actor.global_position = READY
	actor.rotation = Vector3(0,-.5,0)
	actor.show()
	pack.rack.show()
	retaliation.clear()
	_sync_pack()
	var journal: Dictionary = world.inventory.settlement
	if _has_finished_goods():
		_go_to_counter()
	elif not journal.worker_supply.is_empty():
		_begin_supply_run(journal.worker_supply)
	elif not journal.worker_carry_token.is_empty():
		phase = "carrying"
		route.assign([_shelf_apron()])
	elif journal.worker_load.values().any(func(amount): return amount > 0):
		_begin_bin_delivery()
	else:
		_return_to_shelf()

func _defend(dt: float) -> bool:
	if not is_instance_valid(defender): return false
	if not defender.can_receive_swirl() or defender.global_position.distance_squared_to(actor.global_position)>3.85:
		defender = null
		actor.work_strike_point=Vector3.INF
		return false
	if not _travel_clear(actor.global_position,defender.global_position,.045):
		defender = null
		actor.work_strike_point=Vector3.INF
		return false
	travel_speed = 0.0
	actor.bundle.hide()
	var axis := actor.global_position.direction_to(defender.global_position)
	actor.rotation.y = rotate_toward(actor.rotation.y,atan2(axis.x,axis.z),dt*9.0)
	actor.work_strike_point=_defense_face()
	var previous: PackedVector3Array = actor.blade_points()
	defend_elapsed += dt
	actor.pose("chop",maxf(0.0,defend_elapsed)/Human.CHOP_SECONDS)
	if not defend_landed and defend_elapsed>=.48 and defend_elapsed<=1.14:
		var next: PackedVector3Array = actor.blade_points()
		for i in mini(previous.size(),next.size()):
			if not defender.contact_segment(previous[i],next[i]): continue
			if not _travel_clear(actor.global_position,next[i],.055): continue
			defend_landed = defender.receive_hit(1,next[i])
			if defend_landed:
				retaliation[defender.get_instance_id()] = world.simulation_time+8.0
				world._event("survivor_defends",next[i],"impact_wood")
				break
	if defend_elapsed>=Human.CHOP_SECONDS:
		defend_elapsed = 0.0
		defend_landed = false
	return true

func _defense_face() -> Vector3:
	var surface: MeshInstance3D=defender.surface
	var skin: TriangleMesh=defender.hit_surface
	if not surface or not skin: return Vector3.INF
	var feet := actor.global_position
	var body := defender.global_position
	var axis := feet.direction_to(body).slide(Vector3.UP).normalized()
	for base: float in [.84,.70,.96,.59]:
		var height := base*float(defender.size_factor())
		var start := Vector3(feet.x,height,feet.z)
		var end := Vector3(body.x,height,body.z)+axis*.42
		var hit := skin.intersect_segment(surface.to_local(start),surface.to_local(end))
		if not hit.is_empty(): return surface.to_global(hit.position)+axis*.058
	return Vector3.INF

func _begin_hunt(origin: Vector3) -> bool:
	if not wildlife.is_huntable() or worker_space("meat")<=0 or not world.inventory.storage_open("meat"):
		return false
	if not _in_work_area(wildlife.global_position): return false
	hunt_goal = wildlife.approach_from(origin)
	var approach := _outdoor_path(origin,hunt_goal)
	if approach.is_empty(): return false
	route.append_array(approach)
	hunt_replans = 0
	hunt_retry = 0.0
	phase = "hunt_approach"
	return true

func _advance_hunt(dt: float) -> void:
	if shift_seconds>=FIELD_SHIFT_SECONDS:
		_go_home_bulk()
		return
	if phase == "hunt_pickup":
		hunt_elapsed += dt
		_walk(wildlife.global_position,dt)
		_sweep_drops()
		if hunt_elapsed>=.82:
			_begin_inbound(true)
			phase = "bulk_return"
		return
	if not wildlife.is_huntable():
		_go_home_bulk()
		return
	if phase == "hunt_approach":
		actor.work_strike_point=Vector3.INF
		hunt_retry = maxf(0.0,hunt_retry-dt)
		if hunt_goal.distance_to(wildlife.global_position)>1.12 and hunt_retry==0.0 and _in_work_area(actor.global_position):
			hunt_retry = .38
			hunt_goal = wildlife.approach_from(actor.global_position)
			route = _outdoor_path(actor.global_position,hunt_goal)
			hunt_replans += 1
			if route.is_empty() or hunt_replans>8:
				_go_home_bulk()
				return
		if _walk_route(dt,false):
			hunt_contacted = false
			hunt_elapsed = 0.0
			phase = "hunt_strike"
		return
	var axis := actor.global_position.direction_to(wildlife.global_position)
	actor.rotation.y = rotate_toward(actor.rotation.y,atan2(axis.x,axis.z),dt*8.0)
	var hunt_level := Vector3.UP*.87
	var near: Vector3=wildlife.intersect_blade(actor.global_position+hunt_level,wildlife.global_position+hunt_level)
	actor.work_strike_point=near+axis*.07 if near.is_finite() else Vector3.INF
	var previous: PackedVector3Array = actor.blade_points()
	hunt_elapsed += dt
	actor.pose("chop",hunt_elapsed/Human.CHOP_SECONDS)
	if not hunt_contacted and hunt_elapsed>=.48 and hunt_elapsed<=1.14:
		var next: PackedVector3Array = actor.blade_points()
		for i in mini(previous.size(),next.size()):
			var contact: Vector3 = wildlife.intersect_blade(previous[i],next[i])
			if not contact.is_finite(): continue
			if not wildlife.receive_hunting_contact(contact,actor.global_position): continue
			hunt_contacted = true
			world._record_field_event("survivor_hunt_hit",contact)
			if wildlife.hp<=0:
				hunt_elapsed = 0.0
				phase = "hunt_pickup"
			break
	if phase=="hunt_pickup" or hunt_elapsed<Human.CHOP_SECONDS: return
	if not hunt_contacted:
		hunt_goal = wildlife.approach_from(actor.global_position)
		route = _outdoor_path(actor.global_position,hunt_goal)
		hunt_replans += 1
		if route.is_empty() or hunt_replans>8:
			_go_home_bulk()
		else:
			phase = "hunt_approach"
	else:
		hunt_contacted = false
		hunt_elapsed = 0.0

func _advance_tasks(dt: float) -> void:
	if not restored_service.is_empty():
		var network = _paid_walkways()
		if network:
			var floor_point: Vector3 = network.accessible_service(restored_service)
			if floor_point.is_finite(): actor.global_position = floor_point
		restored_service = ""
	var journal: Dictionary = world.inventory.settlement
	if phase in ["to_tree","work_ready","chopping","falling","pickup","foraging","mining_approach","mining","hunt_approach","hunt_strike","hunt_pickup"]:
		shift_seconds+=dt
		if shift_seconds>=FIELD_SHIFT_SECONDS and phase in ["to_tree","work_ready","pickup","foraging","mining_approach"]:
			_go_home_bulk()
			return
	if phase in ["carrying","bulk_return","supply_pickup","supply_return","supply_back","bin_delivery"] and world.inventory.storage_open("wood"):
		var door := _shelf_apron()
		if not route.is_empty(): route[-1] = door
		elif actor.global_position.distance_to(door) > .20: route.assign([door])
	match phase:
		"waiting_rescue":
			step_cycle=fposmod(step_cycle+dt*.45,1)
			actor.pose("idle",step_cycle)
			if at_rescue(world.actor.global_position) and world.rescue_survivor():
				_begin_outbound()
				if phase=="waiting_rescue": phase="waiting_storage"
		"first_walk":
			if _walk_route(dt,false): phase = "waiting_storage"
		"waiting_storage":
			waiting=maxf(0.0,waiting-dt)
			step_cycle = fposmod(step_cycle+dt*.45,1)
			actor.pose("idle",step_cycle)
			if journal.rescued and waiting<=0.0:
				if _can_fetch_meal():
					_to_cooker()
				elif not world.inventory.storage_open("wood"):
					_start_field_job()
				else:
					route.assign([_shelf_apron()])
					phase = "supply_pickup"
		"meal_collect":
			if not _can_fetch_meal():
				_return_to_shelf()
				return
			route.assign([_meal_pickup_apron()])
			if _walk_route(dt,false):
				if world.settlement_loop.collect_worker_meal(): _go_to_counter()
				else: _return_to_shelf()
				_sync_pack()
		"meal_serve":
			if not _can_deliver_counter():
				_return_to_shelf()
				return
			route.assign([_counter_apron()])
			if _walk_route(dt,false):
				actor.rotation.y = PI
				actor.pose("receive",.48 if world.counter.sale_order != 0 else .22)
				world.settlement_loop.worker_stock_counter()
				_sync_pack()
				_return_to_shelf()
		"hunt_approach","hunt_strike","hunt_pickup":
			_advance_hunt(dt)
		"foraging","mining_approach","mining","bulk_return","bin_delivery":
			_work_field(dt)
		"assist_plot":
			_deliver_to_plot(dt)
		"supply_pickup":
			if _walk_route(dt,false): _leave_shelf()
		"supply_out","supply_unload","supply_return","supply_back":
			_advance_supply(dt)
		"to_tree":
			if not _working_tree():
				_go_home_bulk()
			elif _walk_route(dt,false):
				phase = "work_ready"
		"work_ready":
			actor.pose("idle",step_cycle)
			if not _working_tree():
				_go_home_bulk()
			elif tree.cooldown <= 0.:
				drop_floor = world.drop_id
				_begin_swing()
		"chopping":
			_step_swing(dt)
		"falling":
			actor.pose("idle",step_cycle)
			waiting+=dt
			if not is_instance_valid(tree) or waiting>2.4:
				if is_instance_valid(tree): _defer_source(tree)
				_go_home_bulk()
			elif tree.phase == "credited":
				pickup_token = _nearest_new_bundle()
				if pickup_token.is_empty(): _go_home_bulk()
				else: phase = "pickup"
			elif tree.phase == "rooted":
				_go_home_bulk()
		"pickup":
			if not is_instance_valid(tree):
				_go_home_bulk()
				return
			if not world.drops.has(pickup_token):
				pickup_token = _nearest_new_bundle()
				if pickup_token.is_empty(): _go_home_bulk()
			if phase == "pickup":
				_walk(world.drops[pickup_token].at,dt)
				if can_claim(pickup_token):
					if worker_space("wood")==0:
						_go_home_bulk()
						return
					if world.inventory.storage_open("wood") and journal.worker_carry_token.is_empty() and journal.worker_deliveries==0:
						if not world.claim_worker_wood(pickup_token):return
						_sync_pack()
					_sweep_drops()
					pickup_token=""
					if journal.worker_deliveries==0 and journal.worker_carry_token!="": _begin_inbound(true)
					else: _go_home_bulk()

		"carrying":
			if _walk_route(dt,true):
				phase = "unload"
				waiting = 0.
		"unload":
			if not at_wood_receiver():
				phase = "carrying"
				actor.bundle.hide()
				_sync_pack()
				route.assign([_shelf_apron()])
				return
			waiting += dt
			var u := clampf(waiting/.28,0,1)
			var target: Vector3 = world.depot.landing_position("wood",int(world.inventory.stored.wood))
			if not actor.bundle.visible:
				receipt_departure=_rack_from("wood")
				actor.bundle.show()
				pack_view.carried.wood=maxi(0,int(pack_view.carried.wood)-1)
				pack.sync(true)
			actor.bundle.global_position = receipt_departure.lerp(target,u)+Vector3.UP*.28*sin(u*PI)
			if u >= 1. and world.receive_worker_wood():
				actor.bundle.hide()
				pack.rack.show()
				_sync_pack()
				if journal.worker_load.values().any(func(n): return n > 0): _begin_bin_delivery(true)
				else: _leave_shelf()

func _begin_swing() -> void:
	var aim := _work_face(tree,actor.global_position,false)
	if not aim.is_finite():
		_defer_source(tree)
		_go_home_bulk()
		return
	_face_site(tree)
	actor.rotation.y-=.14
	actor.work_strike_point=aim
	swing_time = 0.
	swing_landed = false
	actor.pose("chop",0)
	phase = "chopping"

func _step_swing(dt: float) -> void:
	if not is_instance_valid(tree) or not world.surfaces.has(tree):
		_go_home_bulk()
		return
	if tree.phase != "rooted" and not swing_landed:
		waiting=0.0
		phase = "falling"
		return
	if tree.phase=="rooted" and not actor.work_strike_point.is_finite():
		_begin_swing()
		return
	var before: PackedVector3Array = actor.blade_points()
	swing_time += dt
	actor.pose("chop",swing_time/Human.CHOP_SECONDS)
	if not swing_landed and swing_time>=.53 and swing_time<=1.14:
		var after: PackedVector3Array = actor.blade_points()
		var contact := _swept_contact(tree,before,after)
		if not contact.is_empty():
			var hit: Vector3 = contact.position
			world.tree_input_sequence=maxi(world.tree_input_sequence,tree.last_sequence)+1
			swing_landed = tree.strike(tree.TREE_ID,world.tree_input_sequence,actor.global_position,actor.global_basis.z,contact.direction,hit,true)
			if swing_landed:
				contacts+=1
				contact_position=hit
				world.lifecycle.record_strike(tree)
				world._event("impact_wood",hit)
				world._record_field_event("survivor_chop_contact",hit)
	if swing_time >= Human.CHOP_SECONDS:
		actor.work_strike_point=Vector3.INF
		failed_swings=0 if swing_landed else failed_swings+1
		if failed_swings>=2:
			_defer_source(tree)
			_go_home_bulk()
			return
		if tree.phase=="rooted":
			_begin_swing()
		else:
			previous_tree=String(tree.get_meta("field_source_id"))
			waiting=0.0
			phase="falling"

func _nearest_new_bundle() -> String:
	var selected := ""
	var nearest := INF
	for id: String in world.drops:
		var item: Dictionary = world.drops[id]
		if item.kind != "wood" or id.get_slice("-",1).to_int() <= drop_floor: continue
		if item.from.distance_to(tree.global_position+Vector3.UP*.29) > .04: continue
		var dist := actor.global_position.distance_to(item.at)
		if dist < nearest:
			nearest = dist
			selected = id
	return selected

func _can_fetch_meal() -> bool:
	if not world.counter or not world.counter.active or _has_finished_goods(): return false
	return _counter_apron().is_finite() and _meal_pickup_apron().is_finite()

func _meal_pickup_apron() -> Vector3:
	var source: Vector3 = world.settlement_loop.market_worker_product_source()
	if not source.is_finite(): return source
	if source.is_equal_approx(world.depot.apron.global_position): return _shelf_apron()
	return _cooked_apron()

func _to_cooker() -> void:
	route.assign([_meal_pickup_apron()])
	phase = "meal_collect"

func _go_to_counter() -> void:
	# The counter may still be installing when a saved order resumes.
	route.clear()
	phase = "meal_serve"

func _return_to_shelf() -> void:
	route.assign([_shelf_apron() if world.inventory.storage_open("wood") else READY])
	phase = "supply_pickup"

func _rack_from(kind: String) -> Vector3:
	return pack._place(pack.HAND,kind,maxi(0,int(pack_view.carried[kind])-1))

func _start_field_job() -> void:
	priority_order_available=true
	shift_seconds=0.
	if world.inventory.settlement.worker_deliveries == 0 and world.inventory.storage_open("wood") and _begin_outbound(): return
	# Dispatch through the south gate. Restrict the worker's range to its camp
	# work area so the actor and assignments survive player-centred streaming.
	var portal: Vector3 = world.gates[0].position
	var outside := _in_work_area(actor.global_position)
	var staging := actor.global_position if outside else Vector3(portal.x,0,portal.z+GATE_LANDING)
	var target := _closest_drop(staging)
	assigned_bank = _choose_bank(staging)
	route.clear()
	if not outside: route.assign([Vector3(-2.65,0,2.14),Vector3(portal.x,0,portal.z-GATE_LANDING),staging])
	for offset in FIELD_DUTIES.size():
		var duty: String = FIELD_DUTIES[field_cursor]
		field_cursor = (field_cursor+1)%FIELD_DUTIES.size()
		match duty:
			"forage":
				if target.is_empty(): continue
				forage_token = target
				route.append_array(_outdoor_path(staging,world.drops[target].at))
				phase = "foraging"
			"hunt":
				if not _begin_hunt(staging): continue
			"mining":
				if not is_instance_valid(assigned_bank): continue
				route.append_array(bank_approach)
				phase = "mining_approach"
			"wood":
				if not _begin_outbound(): continue
		return
	if outside: _begin_inbound(_has_cargo())
	else:
		waiting=.65
		phase="waiting_storage"

func _in_work_area(point: Vector3) -> bool:
	return not world.field_env.is_inside_camp(point) and point.distance_squared_to(Vector3.ZERO) <= WORK_RADIUS*WORK_RADIUS

func _clear_outdoor_leg(a: Vector2,b: Vector2) -> bool:
	if not _travel_clear(Vector3(a.x,0,a.y),Vector3(b.x,0,b.y),FOOT_RADIUS+.015): return false
	if outdoor_route.bank.is_empty(): return true
	var span := Rect2(a,Vector2.ZERO).expand(b).grow(.01)
	return not span.intersects(outdoor_route.lake_bounds) or not outdoor_route._crosses(a,b,outdoor_route.bank)

func _outdoor_path(from: Vector3, to: Vector3) -> Array[Vector3]:
	var path: Array[Vector3] = []
	var a := Vector2(from.x,from.z)
	var b := Vector2(to.x,to.z)
	outdoor_route.update(world,a)
	if not _clear_outdoor_leg(a,b):
		var corners: PackedVector2Array = outdoor_route.points.duplicate()
		# The swinging leaves occupy either side of the gate, even fully open.
		var mouth: Vector3 = world.gates[0].position
		corners.append(Vector2(mouth.x,mouth.z+GATE_LANDING))
		corners.append(Vector2(mouth.x-2.,mouth.z+GATE_LANDING))
		corners.append(Vector2(mouth.x+2.,mouth.z+GATE_LANDING))
		corners.append(a)
		corners.append(b)
		var graph := AStar2D.new()
		for i in corners.size(): graph.add_point(i,corners[i])
		for i in corners.size():
			for j in range(i):
				if _clear_outdoor_leg(corners[i],corners[j]): graph.connect_points(i,j)
		var detour := graph.get_point_path(corners.size()-2,corners.size()-1)
		if detour.is_empty(): return path
		for i in range(1,detour.size()-1): path.append(Vector3(detour[i].x,0,detour[i].y))
	path.append(to)
	return path

func _closest_drop(origin: Vector3, material := "", source := Vector3.INF) -> String:
	var selected := ""
	var best := INF
	for token: String in world.drops:
		var item: Dictionary = world.drops[token]
		if not material.is_empty() and item.kind!=material: continue
		if source.is_finite() and source.distance_squared_to(item.from)>1.0: continue
		if not _in_work_area(item.at): continue
		if worker_space(item.kind) <= 0 or item.age < .30: continue
		var score := origin.distance_squared_to(item.at)
		if item.kind == "meat": score *= .12
		if score < best and not _outdoor_path(origin,item.at).is_empty():
			best = score
			selected = token
	return selected

func _working_tree() -> bool:
	return is_instance_valid(tree) and world.surfaces.has(tree) and tree.phase=="rooted"

func _defer_source(site: Node3D) -> void:
	deferred_sources[String(site.get_meta("field_source_id"))]=work_clock+8.0

func _source_available(site: Node3D, expected_phase: String) -> bool:
	if not is_instance_valid(site) or site.phase!=expected_phase or not _in_work_area(site.global_position): return false
	return world.surfaces.has(site) and float(deferred_sources.get(site.get_meta("field_source_id"),0.0))<=work_clock

func _face_site(site: Node3D) -> void:
	var toward: Vector3 = site.global_position-actor.global_position
	actor.rotation.y=atan2(toward.x,toward.z)

func _work_face(site: Node3D, feet: Vector3, mining: bool) -> Vector3:
	if not is_instance_valid(site) or not world.surfaces.has(site): return Vector3.INF
	var geometry: MeshInstance3D=world.surfaces[site][0]
	var surfaces: TriangleMesh=world.surfaces[site][1]
	var toward := feet.direction_to(site.global_position).slide(Vector3.UP).normalized()
	var levels := [.59,.49,.40,.30,.77] if mining else [.83,.75,.67,.96,.58]
	for height: float in levels:
		var start := Vector3(feet.x,height,feet.z)
		var end := Vector3(site.global_position.x,height,site.global_position.z)+toward*.20
		var result := surfaces.intersect_segment(geometry.to_local(start),geometry.to_local(end))
		if result.is_empty(): continue
		var face := geometry.to_global(result.position)
		var depth := feet.distance_to(Vector3(face.x,feet.y,face.z))
		if depth<.25 or depth>(.79 if mining else .87): continue
		if not _travel_clear(feet,face,.035): continue
		return face+toward*(.13 if mining else .052)
	return Vector3.INF

func _swept_contact(site: Node3D, before: PackedVector3Array, after: PackedVector3Array) -> Dictionary:
	var surface: MeshInstance3D=world.surfaces[site][0]
	var faces: TriangleMesh=world.surfaces[site][1]
	for i in mini(before.size(),after.size()):
		var impact := faces.intersect_segment(surface.to_local(before[i]),surface.to_local(after[i]))
		if impact.is_empty(): continue
		var hit := surface.to_global(impact.position)
		if _travel_clear(actor.global_position,hit,.035): return {"position":hit,"direction":after[i]-before[i]}
	return {}

func _choose_tree(origin: Vector3) -> bool:
	if worker_space("wood")==0: return false
	var selected: Node3D
	var best := INF
	var first: bool = world.inventory.settlement.worker_deliveries==0
	for pine in world.trees:
		if not _source_available(pine,"rooted"): continue
		var id: String = pine.get_meta("field_source_id","")
		if not (id in ["survivor-work-pine","starter-wood"] or id.begins_with("pine@")): continue
		var score := origin.distance_squared_to(pine.global_position)
		if first and id=="survivor-work-pine": score-=220.0
		elif id==previous_tree: score+=65.0
		if score>=best: continue
		var proposed: Array[Vector3]=[]
		var outward: Vector3=pine.global_position.direction_to(origin)
		if id=="survivor-work-pine" and _work_face(pine,STANCE,false).is_finite():
			proposed=_outdoor_path(origin,STANCE)
			if first and not proposed.is_empty() and _clear_outdoor_leg(Vector2(PINE_APPROACH.x,PINE_APPROACH.z),Vector2(STANCE.x,STANCE.z)):
				var visible_path := _outdoor_path(origin,PINE_APPROACH)
				if not visible_path.is_empty():
					proposed=visible_path
					proposed.append(STANCE)
		if proposed.is_empty():
			for octant:int in [0,1,-1,2,-2,3,-3,4]:
				var stance: Vector3=pine.global_position+outward.rotated(Vector3.UP,octant*PI/4.0)*.72
				if not _in_work_area(stance) or not _work_face(pine,stance,false).is_finite(): continue
				proposed=_outdoor_path(origin,stance)
				if not proposed.is_empty(): break
		if proposed.is_empty(): continue
		selected=pine
		best=score
		timber_approach=proposed
	if not is_instance_valid(selected): return false
	if tree!=selected: failed_swings=0
	tree=selected
	return true

func _choose_bank(origin: Vector3) -> Node3D:
	var best := INF
	var selected: Node3D
	for bank in world.rocks:
		if not _source_available(bank,"seated"): continue
		var kind: String = bank.get_meta("resource_kind")
		if worker_space(kind) <= 0: continue
		var score := origin.distance_squared_to(bank.position)+mini(100,int(world.inventory.stored[kind]))*5.
		if kind!="stone": score+=80.0
		if bank.get_meta("field_source_id")==previous_bank: score+=32.0
		if score>=best: continue
		var from_bank: Vector3 = bank.position.direction_to(origin)
		var viable: Array[Vector3] = []
		for radius: float in [1.39,1.33,1.26,1.14,.97]:
			for octant: int in [0,1,-1,2,-2,3,-3,4]:
				var stance: Vector3 = bank.position+from_bank.rotated(Vector3.UP,octant*PI/4)*radius
				if not _in_work_area(stance) or not _work_face(bank,stance,true).is_finite(): continue
				outdoor_route.update(world,Vector2(origin.x,origin.z))
				if outdoor_route.fence.grow(-outdoor_route.CLEARANCE+.39).has_point(Vector2(stance.x,stance.z)): continue
				viable = _outdoor_path(origin,stance)
				if not viable.is_empty(): break
			if not viable.is_empty(): break
		if viable.is_empty(): continue
		best=score
		selected=bank
		bank_approach=viable
	return selected

func worker_space(kind: String) -> int:
	if kind not in RAW_RULES.WORKER_LOAD: return 0
	var journal: Dictionary = world.inventory.settlement
	var occupied := int(journal.worker_load[kind])
	if kind == "wood" and journal.worker_carry_token != "": occupied += 1
	if kind == journal.worker_supply: occupied += 1
	return maxi(0,RAW_RULES.WORKER_LIMIT-occupied)

func _sweep_drops() -> void:
	var changed := false
	for token: String in world.drops.keys():
		var drop: Dictionary = world.drops[token]
		if drop.age < .30 or actor.position.distance_squared_to(drop.at) > PICKUP_REACH*PICKUP_REACH: continue
		var kind: String = drop.kind
		if worker_space(kind) == 0: continue
		if not _travel_clear(actor.position,drop.at,.035): continue
		if world.inventory.collected.has(token): continue
		world.inventory.collected[token] = kind
		world.inventory.settlement.worker_load[kind] += 1
		world._remove_drop(token)
		changed = true
	if changed:
		_sync_pack()
		world.settlement_loop.commit_receipt("worker_pickup",actor.position)

func _continue_field_shift() -> bool:
	var journal:Dictionary=world.inventory.settlement
	if journal.worker_deliveries==0 or shift_seconds>=FIELD_SHIFT_SECONDS:return false
	var packed:=0
	for kind:String in RAW_RULES.WORKER_LOAD:
		if worker_space(kind)==0:return false
		packed+=RAW_RULES.WORKER_LIMIT-worker_space(kind)
	if packed>=WORK_WAIT_BUNDLES and _can_fetch_meal():return false
	if journal.worker_load.wood>0 and journal.worker_load.stone>0 and packed>=5: return false
	var loose:=_closest_drop(actor.position)
	if not loose.is_empty():
		forage_token=loose
		route=_outdoor_path(actor.position,world.drops[loose].at)
		phase="foraging"
		return true
	# Alternate productive sites without a return to the storehouse in between.
	# A second kind goes in its own rack slot.
	var bank:=_choose_bank(actor.position)
	var can_chop:=_choose_tree(actor.position)
	if can_chop and (not bank or int(journal.worker_load.wood)<=int(journal.worker_load[bank.get_meta("resource_kind")])):
		route=timber_approach.duplicate()
		phase="to_tree"
		return true
	if bank:
		assigned_bank=bank
		route=bank_approach.duplicate()
		phase="mining_approach"
		return true
	return false

func _go_home_bulk() -> void:
	actor.work_strike_point=Vector3.INF
	if _continue_field_shift():return
	var carrying:=_has_cargo()
	_begin_inbound(carrying)
	if carrying and world.inventory.settlement.worker_carry_token.is_empty():phase="bulk_return"

func _begin_bin_delivery(after_wood_receipt:=false) -> void:
	# Keep a two-part timber receipt and the rest of its pack inside the same
	# landing beat as a regular mixed unload.
	launch_window=.32 if after_wood_receipt else .58
	var carried: Dictionary = world.inventory.settlement.worker_load
	for kind: String in carried:
		if carried[kind] > 0 and not world.inventory.storage_open(kind):
			# Use gathered goods directly, including early stone before its bay exists.
			if _prepare_assistance(false): return
			break
	unload_packets.clear()
	next_packet = 0
	var remaining: Dictionary = world.inventory.settlement.worker_load.duplicate()
	for course in 8:
		for kind: String in RAW_RULES.WORKER_LOAD:
			if not world.inventory.storage_open(kind): continue
			var total := int(world.inventory.settlement.worker_load[kind])
			var amount := mini(int(remaining[kind]),ceili(total/8.0))
			if amount == 0: continue
			unload_packets.append({"kind":kind,"amount":amount})
			remaining[kind] -= amount
	if unload_packets.is_empty():
		_start_field_job()
		return
	route.assign([_shelf_apron()])
	phase = "bin_delivery"
	waiting = 0.0

func _work_field(dt: float) -> void:
	match phase:
		"foraging":
			if not _walk_route(dt,false): return
			if world.drops.has(forage_token):
				_walk(world.drops[forage_token].at,dt)
				_sweep_drops()
			if not world.drops.has(forage_token) or worker_space(world.drops[forage_token].kind) == 0:
				var other := _closest_drop(actor.position)
				if other != "" and actor.position.distance_to(world.drops[other].at) < 4.5:
					forage_token = other
					route = _outdoor_path(actor.position,world.drops[other].at)
				else: _go_home_bulk()
		"mining_approach":
			if not _source_available(assigned_bank,"seated"):
				_go_home_bulk()
			elif _walk_route(dt,false):
				failed_swings=0
				_begin_mining()
		"mining":
			_step_mining(dt)
		"bulk_return":
			_sweep_drops()
			if _walk_route(dt,true): _begin_bin_delivery()
		"bin_delivery":
			if not _walk_route(dt,false): return
			_unload_stream(dt)

func _begin_mining() -> void:
	var aim:=_work_face(assigned_bank,actor.global_position,true)
	if not aim.is_finite():
		_defer_source(assigned_bank)
		_go_home_bulk()
		return
	_face_site(assigned_bank)
	# A slight working flank lets the full pick travel beside his head while
	# both boots stay planted and the cutting point still reaches the bank.
	actor.rotation.y-=.35
	actor.work_strike_point=aim
	bank_swing=0.0
	bank_hit=false
	actor.pose("mine",0)
	phase="mining"

func _step_mining(dt: float) -> void:
	if not is_instance_valid(assigned_bank) or not world.surfaces.has(assigned_bank):
		_go_home_bulk()
		return
	if assigned_bank.phase=="seated" and not actor.work_strike_point.is_finite():
		_begin_mining()
		return
	var before: PackedVector3Array=actor.blade_points()
	bank_swing+=dt
	actor.pose("mine",bank_swing/Human.CHOP_SECONDS)
	if not bank_hit and bank_swing>=.53 and bank_swing<=1.14 and assigned_bank.phase=="seated":
		var contact:=_swept_contact(assigned_bank,before,actor.blade_points())
		if not contact.is_empty():
			world.rock_input_sequence=maxi(world.rock_input_sequence,assigned_bank.last_sequence)+1
			bank_hit=assigned_bank.strike(assigned_bank.ROCK_ID,world.rock_input_sequence,actor.global_position,actor.global_basis.z,true)
			if bank_hit:
				var kind: String=assigned_bank.get_meta("resource_kind")
				world.lifecycle.record_strike(assigned_bank)
				world._event("impact_"+kind,contact.position)
				world._record_field_event("survivor_mine_contact",contact.position)
				if assigned_bank.phase=="mined":
					previous_bank=String(assigned_bank.get_meta("field_source_id"))
					world._event("deplete_"+kind,assigned_bank.global_position)
					world._make_drops(kind,assigned_bank.global_position,3)
					world.lifecycle.deplete(assigned_bank)
					world._checkpoint_lifecycle()
	if bank_swing<Human.CHOP_SECONDS: return
	actor.work_strike_point=Vector3.INF
	if assigned_bank.phase!="seated":
		var kind:String=assigned_bank.get_meta("resource_kind")
		forage_token=_closest_drop(actor.global_position,kind,assigned_bank.global_position)
		if forage_token.is_empty(): _go_home_bulk()
		else:
			route=_outdoor_path(actor.global_position,world.drops[forage_token].at)
			phase="foraging"
		return
	failed_swings=0 if bank_hit else failed_swings+1
	if failed_swings>=2:
		_defer_source(assigned_bank)
		_go_home_bulk()
	else: _begin_mining()

func _unload_stream(dt: float) -> void:
	waiting += dt
	var interval := minf(.055,launch_window/maxi(1,unload_packets.size()-1))
	while next_packet < unload_packets.size() and waiting >= next_packet*interval:
		var packet := unload_packets[next_packet]
		next_packet += 1
		var kind: String = packet.kind
		var item: Node3D = world.FieldArt.make(kind,.37)
		add_child(item)
		item.global_position = _rack_from(kind)
		delivery_stream.append({"kind":kind,"amount":packet.amount,"mesh":item,"from":item.global_position,"age":0.0})
	for transfer in delivery_stream.duplicate():
		transfer.age += dt
		var t := clampf(transfer.age/.245,0,1)
		var kind: String = transfer.kind
		var target: Vector3 = world.depot.landing_position(kind,int(world.inventory.stored[kind]))
		transfer.mesh.global_position = transfer.from.lerp(target,t)+Vector3.UP*.3*sin(PI*t)
		if t < 1: continue
		var amount := mini(int(transfer.amount),int(world.inventory.settlement.worker_load[kind]))
		world.inventory.settlement.worker_load[kind] -= amount
		world.inventory.stored[kind] += amount
		transfer.mesh.queue_free()
		delivery_stream.erase(transfer)
		_sync_pack()
		if not world.settlement_loop.commit_receipt("deposit_"+kind,target): return
	if next_packet == unload_packets.size() and delivery_stream.is_empty(): _leave_shelf()

func _still_due(id: String, kind: String) -> int:
	return maxi(0,int(world.inventory.remaining(id).get(kind,0))-world.carry._outstanding(kind,id,false))

func _prepare_assistance(use_shelf := true) -> bool:
	var book = world.inventory
	if not book.settlement.rescued: return false
	# Prefer the published next offer, including partially funded contracts.
	# Other visible projects may progress when the next one needs unavailable stock.
	var candidates := [world.Progress.next_build(book)]
	for id: String in book.paid:
		if id != candidates[0]: candidates.append(id)
	for id: String in candidates:
		if not book.offer_open(id): continue
		if id in world.Progress.LINES: continue # Conveyors are player-selected enhancements.
		if id in ["snow_garage","snow_truck"]: continue # Vehicle purchase is an explicit player project.
		var pad: Node3D = world.carry.receivers.get(id)
		if not pad or not pad.is_visible_in_tree(): continue
		var loaded := false
		for kind: String in book.remaining(id):
			var due := _still_due(id,kind)
			var carried := int(book.settlement.worker_load[kind])
			var amount := 0
			if use_shelf and book.storage_open(kind):
				amount = mini(maxi(0,due-carried),mini(worker_space(kind),world.carry.available_on_shelf(kind)))
			book.stored[kind] -= amount
			book.settlement.worker_load[kind] += amount
			loaded = loaded or (due > 0 and amount+carried > 0)
		if not loaded: continue
		assisted_plot = id
		_sync_pack()
		if not world.settlement_loop.commit_receipt("worker_pickup",actor.position): return true
		route.assign([pad.global_position])
		phase = "assist_plot"
		waiting = 0.
		return true
	return false

func _deliver_to_plot(dt: float) -> void:
	var book = world.inventory
	if not book.offer_open(assisted_plot):
		_stop_plot_work()
		return
	var pad: Node3D = world.carry.receivers[assisted_plot]
	var stance: Vector3 = pad.global_position
	if assisted_plot in world.Progress.MACHINES.values():
		stance = _supply_apron(world.Progress.MACHINES.find_key(assisted_plot))
	route.assign([stance])
	if not _walk_route(dt,true): return
	if not _travel_clear(actor.position,pad.global_position,.035): return
	if not is_instance_valid(transfer_mesh):
		var due: Dictionary = book.remaining(assisted_plot)
		for kind: String in due:
			if _still_due(assisted_plot,kind) > 0 and book.settlement.worker_load[kind] > 0:
				spend_kind = kind
				break
		if spend_kind.is_empty():
			_stop_plot_work()
			return
		transfer_mesh = world.FieldArt.make(spend_kind,.38)
		add_child(transfer_mesh)
		waiting = 0.
	waiting += dt
	var t := clampf(waiting/.25,0,1)
	transfer_mesh.global_position = _rack_from(spend_kind).lerp(pad.global_position+Vector3.UP*.12,t)+Vector3.UP*.32*sin(PI*t)
	if t < 1: return
	var amount := mini(_still_due(assisted_plot,spend_kind),int(book.settlement.worker_load[spend_kind]))
	if amount > 0 and book.worker_payment(assisted_plot,spend_kind,amount):
		_sync_pack()
		if not world.settlement_loop.commit_receipt("spend_"+spend_kind,pad.global_position): return
		if book.complete(assisted_plot): world._finish_purchase(assisted_plot)
	transfer_mesh.queue_free()
	transfer_mesh = null
	spend_kind = ""

func _stop_plot_work() -> void:
	if is_instance_valid(transfer_mesh): transfer_mesh.queue_free()
	transfer_mesh = null
	spend_kind = ""
	assisted_plot = ""
	if world.inventory.settlement.worker_load.values().any(func(n): return n > 0):
		_begin_bin_delivery()
	else:
		_return_to_shelf()
