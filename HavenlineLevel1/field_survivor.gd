extends Node3D

const Human = preload("res://field_human.gd")
const RESCUE := Vector3(-5.10,0,9.90)
const PINE := Vector2(-3.60,9.10)
const STANCE := Vector3(-2.69,0,9.37)
const READY := Vector3(-2.7,0,1.72)
const SPEED := 1.80
const SUPPLIES := ["wood","stone","meat"]
# Follow the open aisle between the storehouse's east wall and the hearth.
const SHELF_TURN := Vector3(-.82,0,-1.18)
const NORTH_TURN := Vector3(-.82,0,-5.46)
var world
var actor: Node3D
var tree
var phase := "waiting_rescue"
var contacts := 0
var contact_position := Vector3.INF
var step_cycle := .0
var swing_time := .0
var swing_landed := false
var pickup_token := ""
var drop_floor := 0
var waiting := .0
var route: Array[Vector3] = []
var supply_model: Node3D

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
	tree = world.add_resource_source("survivor-work-pine","wood",PINE,1)
	if not world.inventory.settlement.worker_supply.is_empty():
		actor.position = world.depot.APRON
		_begin_supply_run(world.inventory.settlement.worker_supply)
	elif not world.inventory.settlement.worker_carry_token.is_empty():
		actor.position = STANCE
		_begin_inbound(true)
	elif world.inventory.settlement.rescued:
		actor.position = READY
		phase = "waiting_storage"

func at_rescue(at: Vector3) -> bool:
	return phase == "waiting_rescue" and world.inventory.settlement.get("survivor_paid",false) and at.distance_to(actor.global_position) <= 1.46

func can_claim(token: String) -> bool:
	if phase != "pickup" or token != pickup_token or not world.drops.has(token): return false
	var item: Dictionary = world.drops[token]
	return item.kind == "wood" and item.at.distance_to(actor.global_position) <= .24 and item.from.distance_to(tree.global_position+Vector3.UP*.29) < .04 and item.age >= .41

func at_wood_receiver() -> bool:
	return phase == "unload" and actor.global_position.distance_to(world.depot.APRON) < .23

func _begin_inbound(carrying: bool) -> void:
	var portal: Vector3 = world.gates[0].position
	route.assign([Vector3(0,0,portal.z+1.5),Vector3(0,0,portal.z-1.45),Vector3(-2.65,0,2.14)])
	if carrying: route.append(world.depot.APRON)
	else: route.append(READY)
	phase = "carrying" if carrying else "first_walk"

func _begin_outbound() -> void:
	var portal: Vector3 = world.gates[0].position
	route.assign([Vector3(-2.65,0,2.14),Vector3(0,0,portal.z-1.45),Vector3(0,0,portal.z+1.50),STANCE])
	phase = "to_tree"

func _supply_apron(kind: String) -> Vector3:
	return world.lakeshore.APRON if kind == "meat" else world.processors.APRONS[kind]

func _next_supply() -> String:
	if not world.inventory.complete(world.Progress.SECOND): return ""
	var journal: Dictionary = world.inventory.settlement
	for offset in SUPPLIES.size():
		var kind: String = SUPPLIES[(int(journal.worker_deliveries)+offset)%SUPPLIES.size()]
		if not world.settlement_loop.available_to_feeder(kind): continue
		var reserve := 0
		for id: String in world.inventory.costs:
			reserve += int(world.inventory.remaining(id).get(kind,0))
		if world.carry.available_on_shelf(kind) > reserve: return kind
	return ""

func _begin_supply_run(kind: String) -> void:
	supply_model = world.FieldArt.make(kind,.43)
	actor.add_child(supply_model)
	supply_model.position = Vector3(0,.58,.235)
	route.assign([SHELF_TURN,NORTH_TURN,_supply_apron(kind)])
	phase = "supply_out"

func _leave_shelf() -> void:
	var kind := _next_supply()
	if kind.is_empty():
		_begin_outbound()
		return
	world.inventory.stored[kind] -= 1
	world.inventory.settlement.worker_supply = kind
	if world.settlement_loop.commit_receipt("worker_pickup",actor.global_position):
		_begin_supply_run(kind)

func _advance_supply(dt: float) -> void:
	var journal: Dictionary = world.inventory.settlement
	var kind: String = journal.worker_supply
	match phase:
		"supply_out":
			var reached := _walk_route(dt,true)
			actor.bundle.hide()
			if reached:
				waiting = 0.0
				phase = "supply_unload"
		"supply_unload":
			# The player may have filled this hopper during the trip. Carry the
			# unit back to its own shelf instead of discarding it or overfilling.
			if not world.settlement_loop.available_to_feeder(kind):
				supply_model.position = Vector3(0,.58,.235)
				route.assign([NORTH_TURN,SHELF_TURN,world.depot.APRON])
				phase = "supply_return"
				return
			waiting += dt
			var t := clampf(waiting/.36,0.,1.)
			var target: Vector3 = world.lakeshore.cooker_input.global_position if kind=="meat" else world.processors.input_position(kind)
			supply_model.global_position = actor.to_global(Vector3(0,.58,.235)).lerp(target,t)+Vector3.UP*.22*sin(PI*t)
			if t >= 1.0:
				journal.hoppers[kind] += 1
				journal.worker_supply = ""
				if world.settlement_loop.commit_receipt("spend_"+kind,target):
					supply_model.queue_free()
					route.assign([NORTH_TURN,SHELF_TURN,world.depot.APRON])
					phase = "supply_back"
		"supply_return":
			var reached := _walk_route(dt,true)
			actor.bundle.hide()
			if reached:
				world.inventory.stored[kind] += 1
				journal.worker_supply = ""
				if world.settlement_loop.commit_receipt("deposit_"+kind,actor.global_position):
					supply_model.queue_free()
					_begin_outbound()
		"supply_back":
			if _walk_route(dt,false): _begin_outbound()

func _walk(destination: Vector3, dt: float, carrying := false) -> bool:
	var gate = world.gates[0]
	var before := actor.global_position
	var delta := destination-before
	var walking := true
	if gate.active and gate.position.distance_to(before)<2.45 and absf(before.x)<.90 and absf(delta.z)>.02:
		if gate.angle < 1.29 and absf(before.z-gate.position.z)<1.67: walking = false
	if delta.length_squared() > .00003:
		actor.rotation.y = lerp_angle(actor.rotation.y,atan2(delta.x,delta.z),clampf(dt*11,0,1))
		if walking:
			actor.global_position = before.move_toward(destination,SPEED*dt)
			step_cycle = fposmod(step_cycle+before.distance_to(actor.global_position)/1.32,1)
	actor.pose("carry" if carrying else ("walk" if walking else "idle"),step_cycle)
	return actor.global_position.distance_squared_to(destination) <= .0001

func _walk_route(dt: float, carrying: bool) -> bool:
	if not route.is_empty() and _walk(route[0],dt,carrying):
		route.pop_front()
	return route.is_empty()

func advance(dt: float) -> void:
	if not actor or world.persist_blocked or world.reset_time>0: return
	var journal: Dictionary = world.inventory.settlement
	match phase:
		"waiting_rescue":
			step_cycle=fposmod(step_cycle+dt*.45,1)
			actor.pose("idle",step_cycle)
			if at_rescue(world.actor.global_position) and world.rescue_survivor():
				if world.inventory.storage_open("wood"):
					route.assign([STANCE])
					phase="to_tree"
				else:
					_begin_inbound(false)
		"first_walk":
			if _walk_route(dt,false): phase = "waiting_storage"
		"waiting_storage":
			step_cycle = fposmod(step_cycle+dt*.45,1)
			actor.pose("idle",step_cycle)
			if journal.rescued and world.inventory.storage_open("wood"):
				if _next_supply().is_empty():
					_begin_outbound()
				else:
					route.assign([world.depot.APRON])
					phase = "supply_pickup"
		"supply_pickup":
			if _walk_route(dt,false): _leave_shelf()
		"supply_out","supply_unload","supply_return","supply_back":
			_advance_supply(dt)
		"to_tree":
			if _walk_route(dt,false):
				actor.rotation.y = atan2(PINE.x-STANCE.x,PINE.y-STANCE.z)
				phase = "work_ready"
		"work_ready":
			actor.pose("idle",step_cycle)
			if tree.phase == "rooted" and tree.cooldown <= 0.:
				drop_floor = world.drop_id
				_begin_swing()
		"chopping":
			_step_swing(dt)
		"falling":
			actor.pose("idle",step_cycle)
			if tree.phase == "credited":
				pickup_token = _nearest_new_bundle()
				phase = "pickup" if not pickup_token.is_empty() else "work_ready"
			elif tree.phase == "rooted":
				phase = "work_ready"
		"pickup":
			if not world.drops.has(pickup_token):
				pickup_token = _nearest_new_bundle()
				if pickup_token.is_empty(): phase = "work_ready"
			if phase == "pickup":
				_walk(world.drops[pickup_token].at,dt)
				if can_claim(pickup_token) and world.claim_worker_wood(pickup_token):
					pickup_token = ""
					_begin_inbound(true)
		"carrying":
			if _walk_route(dt,true):
				phase = "unload"
				waiting = 0.
		"unload":
			waiting += dt
			var u := clampf(waiting/.42,0,1)
			actor.pose("carry",step_cycle)
			var target: Vector3 = world.depot.landing_position("wood",int(world.inventory.stored.wood))
			actor.bundle.global_position = actor.to_global(Vector3(0,.58,.235)).lerp(target,u)+Vector3.UP*.28*sin(u*PI)
			if u >= 1. and world.receive_worker_wood():
				actor.bundle.position = Vector3(0,.58,.235)
				_leave_shelf()

func _begin_swing() -> void:
	actor.rotation.y = atan2(PINE.x-STANCE.x,PINE.y-STANCE.z)
	swing_time = 0.
	swing_landed = false
	actor.pose("chop",0)
	phase = "chopping"

func _step_swing(dt: float) -> void:
	if tree.phase != "rooted" and not swing_landed:
		phase = "falling"
		return
	var before: PackedVector3Array = actor.blade_points()
	swing_time += dt
	actor.pose("chop",swing_time/Human.CHOP_SECONDS)
	if not swing_landed and swing_time>=.48 and swing_time<=.94:
		var geometry: MeshInstance3D = world.surfaces[tree][0]
		var trunk: TriangleMesh = world.surfaces[tree][1]
		var after: PackedVector3Array = actor.blade_points()
		for i in before.size():
			var cross_section := trunk.intersect_segment(geometry.to_local(before[i]),geometry.to_local(after[i]))
			if cross_section.is_empty(): continue
			var hit := geometry.to_global(cross_section.position)
			world.tree_input_sequence += 1
			swing_landed = tree.strike(tree.TREE_ID,world.tree_input_sequence,actor.global_position,actor.global_basis.z,after[i]-before[i],hit)
			if swing_landed:
				contacts += 1
				contact_position = hit
				world.lifecycle.record_strike(tree)
				world._event("impact_wood",hit)
				break
	if swing_time >= Human.CHOP_SECONDS:
		phase = "work_ready" if tree.phase == "rooted" else "falling"

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
