extends Node3D
## The north fence stays sealed. The cashier and the outside FIFO meet across its worktop.
signal served(order: int)
signal exchange_event(event: String, at: Vector3)

const COUNTER = preload("res://assets/customer_counter/canonical_counter.glb")
const ORDER_PLATE = preload("res://assets/customer_counter/order_plate.svg")
const ORDER_ITEM = preload("res://assets/customer_counter/roast_order.png")
const MEAL = preload("res://assets/customer_counter/cooked_game_meat.glb")
const MONEY = preload("res://assets/customer_counter/banded_notes.glb")
const CENTER_X := 2.8
const HALF_BAY := 1.825
const CUSTOMER_Z := -1.60
const CAPACITY := 3
const SPACING := 1.15
const APPROACH_SPEED := 1.65
const FOOD_TO_BOARD := .36
const EXCHANGE_TIME := .88

var world
var service_point := Marker3D.new()
var customer_point := Marker3D.new()
var food_rest := Marker3D.new()
var payment_rest := Marker3D.new()
var queue: Array[Dictionary] = []
var leaving: Array[Dictionary] = []
var active := false
var make_customer: Callable
var take_meal_payment: Callable
var next_order := 1
var arrival_clock := 0.0
var queue_clock := 0.0
var sale_order := 0
var sale_elapsed := 0.0
var sale_committed := false
var worker_serving := false
var belt_serving := false
var worker_palm: BoneAttachment3D
var worker_roast: Node3D
var worker_origin := Vector3.ZERO
var worker_transfer := 1.0
var parked_player_meal: Node3D
var meal: Node3D
var cash: Node3D
var collect_time := 1.0
var meal_origin := Vector3.ZERO
var exchange_origin := Vector3.ZERO
var guard := StaticBody3D.new()
var player_palm: BoneAttachment3D

static func make_meal() -> Node3D:
	return MEAL.instantiate()

func setup(host, visitor_factory: Callable, sale_callback: Callable) -> void:
	world = host
	make_customer = visitor_factory
	take_meal_payment = sale_callback
	player_palm = _attach_to_palm(host.actor, "Hand.R")
	var donor := COUNTER.instantiate()
	donor.name = "AlfredNorthCounter"
	add_child(donor)
	# These are the surviving fence's timber caps. They overlap the donor/fence joins.
	for x: float in [-1.7025, 1.71076]:
		var cap: MeshInstance3D = host.field_env.donor_mesh(host.field_env.POST)
		cap.position = Vector3(x,0,0)
		add_child(cap)
	_add_marker(service_point, "WorkerInside", Vector3(0,0,1.54))
	_add_marker(customer_point, "CustomerOutside", Vector3(0,0,CUSTOMER_Z))
	# Original worktop heights measured on the docked donor's board triangles.
	_add_marker(food_rest, "MealOnBoard", Vector3(0,1.080,0))
	_add_marker(payment_rest, "NotesOnBoard", Vector3(1.25,1.085,0))
	var shape := CollisionShape3D.new()
	var box := BoxShape3D.new()
	box.size = Vector3(3.40,.95,1.91)
	shape.shape = box
	shape.position.y = .475
	guard.name = "SolidCounterBody"
	guard.add_child(shape)
	guard.collision_layer = 0
	guard.collision_mask = 0
	add_child(guard)
	hide()

func _attach_to_palm(body: Node3D, bone: String) -> BoneAttachment3D:
	for rig: Skeleton3D in body.find_children("*","Skeleton3D",true,false):
		if rig.find_bone(bone) >= 0:
			var hand := BoneAttachment3D.new()
			hand.bone_name = bone
			rig.add_child(hand)
			return hand
	return null

func _add_marker(marker: Marker3D, label: String, point: Vector3) -> void:
	marker.name = label
	marker.position = point
	add_child(marker)

func set_active(enabled: bool, last_served: int) -> void:
	if enabled == active:
		return
	active = enabled
	if not enabled and is_instance_valid(worker_roast):
		worker_roast.queue_free()
		worker_roast = null
	visible = enabled
	guard.collision_layer = 1 if enabled else 0
	if enabled:
		position = Vector3(world.field_env.counter_center_x,0,world.field_env.COURTS.back().y)
		next_order = last_served + 1
		arrival_clock = 0.0
		return
	for group: Array in [queue, leaving]:
		for visitor: Dictionary in group:
			visitor.body.queue_free()
		group.clear()
	_clear_presentations()

# Keep visitors on their feet while the service bay changes. The queue walks
# to its new north-wall slot through the ordinary arrival and serving loop.
func move_to_bay(x:float) -> void:
	var shift := Vector3(x-global_position.x,0,0)
	global_position += shift
	for group: Array in [queue,leaving]:
		for visitor: Dictionary in group:
			visitor.body.global_position -= shift
	world.field_env.counter_center_x = x
	world.field_env.set_perimeter(world.field_env.perimeter_stage,false,true)

func _clear_presentations() -> void:
	if is_instance_valid(meal): meal.queue_free()
	if is_instance_valid(cash): cash.queue_free()
	meal = null
	cash = null
	sale_order = 0
	sale_committed = false

func at_service(at: Vector3) -> bool:
	if not active:
		return false
	var local := to_local(at)
	# Use the whole inside edge of the worktop, including its two corners.
	var along := clampf(local.x,-HALF_BAY+.16,HALF_BAY-.16)
	return local.z >= .82 and Vector2(local.x-along,local.z-1.12).length() <= 1.30 and absf(local.y) < .65

func front_ready(order: int) -> bool:
	if not active or queue.is_empty() or int(queue[0].order) != order:
		return false
	return (queue[0].body as Node3D).position.distance_to(customer_point.position) < .035

func awaiting_payment(order: int) -> bool:
	return order == sale_order and not sale_committed and sale_elapsed >= FOOD_TO_BOARD and front_ready(order)

func _slot(i: int) -> Vector3:
	return customer_point.position + Vector3(0,0,-i*SPACING)

func _order_request(visitor: Node3D) -> Node3D:
	var card := Node3D.new()
	card.name = "RequestedMeal"
	visitor.add_child(card)
	card.position.y = 1.90
	for layer in [ORDER_PLATE,ORDER_ITEM]:
		var art := Sprite3D.new()
		art.texture = layer
		art.billboard = BaseMaterial3D.BILLBOARD_ENABLED
		art.pixel_size = .0065
		art.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		if layer == ORDER_ITEM:
			art.offset = Vector2(0,9)
			art.render_priority = 2
		else: art.render_priority = 1
		card.add_child(art)
	return card

func _admit() -> void:
	# Admit from beyond the last waiting visitor, then walk all the way onto a slot.
	if queue.size() >= CAPACITY:
		return
	var entrance := _slot(CAPACITY-1) + Vector3(0,0,-1.72)
	for other: Dictionary in queue:
		if (other.body as Node3D).position.distance_to(entrance) < SPACING:
			return
	var asset := "customer_male_01" if next_order % 2 == 1 else "customer_female_01"
	var visitor: Node3D = make_customer.call(asset)
	if not visitor:
		return
	visitor.name = "Customer%d" % next_order
	visitor.add_to_group("snow_track_survivors")
	visitor.position = entrance
	add_child(visitor)
	queue.append({"order":next_order,"body":visitor,"phase":0.0,"request":_order_request(visitor),
		"right":_attach_to_palm(visitor,"Palm.R"),"left":_attach_to_palm(visitor,"Palm.L")})
	next_order += 1

func _step_visitor(entry: Dictionary, target: Vector3, dt: float) -> bool:
	var visitor: Node3D = entry.body
	var old := visitor.position
	var next := old.move_toward(target,APPROACH_SPEED*dt)
	if world.field_env.travel_clear(to_global(old),to_global(next),.21):
		visitor.position = next
	var step := visitor.position - old
	var moving := step.length_squared() > .000001
	if moving:
		visitor.rotation.y = lerp_angle(visitor.rotation.y,atan2(step.x,step.z),clampf(dt*13.,0,1))
		entry.phase = fposmod(float(entry.phase) + step.length()/1.40,1.0)
	else:
		visitor.rotation.y = lerp_angle(visitor.rotation.y,0.0,clampf(dt*9.,0,1))
	if visitor.has_method("pose"):
		if not moving and int(entry.order) == sale_order:
			visitor.pose("receive", clampf(sale_elapsed/(FOOD_TO_BOARD+EXCHANGE_TIME),0,1))
		else:
			visitor.pose("walk" if moving else "idle",entry.phase if moving else fposmod(queue_clock*.55+.17*int(entry.order),1.0))
	if entry.has("food"):
		entry.food.global_position = _guest_palm(entry,"right") + visitor.global_basis * Vector3(-.15,.01,.04)
	return visitor.position.is_equal_approx(target)

func _walk_queue(dt: float) -> void:
	arrival_clock -= dt
	if arrival_clock <= 0:
		_admit()
		arrival_clock = 1.40
	queue_clock += dt
	for i in queue.size():
		queue[i].request.visible = i == 0 and not sale_committed
		var target := _slot(i)
		if i > 0:
			# A waiting customer may only advance into space cleared by its predecessor.
			target.z = minf(target.z, (queue[i-1].body as Node3D).position.z-SPACING)
		elif not leaving.is_empty():
			var previous: Node3D = leaving.back().body
			if absf(previous.position.x) < SPACING:
				# Never step through the customer turning out of the queue.
				target.z = minf(target.z, CUSTOMER_Z-SPACING+absf(previous.position.x))
		_step_visitor(queue[i],target,dt)
	for i in range(leaving.size()-1,-1,-1):
		var entry: Dictionary = leaving[i]
		var target := Vector3(2.44,0,CUSTOMER_Z-.31) if entry.leg == 0 else Vector3(2.44,0,-7.1)
		if _step_visitor(entry,target,dt):
			if entry.leg == 0:
				entry.leg = 1
			else:
				entry.body.queue_free()
				leaving.remove_at(i)

func _carried_meal_point() -> Vector3:
	if player_palm:
		return player_palm.global_position + world.actor.global_basis * Vector3(-.15,.02,.03)
	return world.actor.to_global(Vector3(-.39,.88,.12))

func _worker_meal_point() -> Vector3:
	var body: Node3D = world.survivor.actor
	if not worker_palm: worker_palm = _attach_to_palm(body,"Palm.R")
	return worker_palm.global_position if worker_palm else body.to_global(Vector3(-.25,.82,.21))

func collect_worker_meal(origin: Vector3) -> void:
	if is_instance_valid(worker_roast): return
	worker_roast = make_meal()
	add_child(worker_roast)
	worker_roast.global_position = origin
	worker_origin = origin
	worker_transfer = 0.0

func _show_worker_meal(dt: float) -> void:
	if world.inventory.settlement.get("worker_meal",0) == 0:
		if is_instance_valid(worker_roast):
			worker_roast.queue_free()
			worker_roast = null
		return
	if not is_instance_valid(worker_roast):
		collect_worker_meal(_worker_meal_point())
		worker_transfer = 1.0
	worker_transfer = minf(1.0,worker_transfer+dt/.25)
	worker_roast.global_position = _arc(worker_origin,_worker_meal_point(),worker_transfer,.18)

func delivery_position(slot:int=0) -> Vector3:
	return to_global(Vector3(-.75,1.09,.20+.34*slot))

func _server_position() -> Vector3:
	if belt_serving:return service_point.global_position
	return world.survivor.actor.global_position if worker_serving else world.actor.global_position

func _server_hand() -> Vector3:
	if belt_serving:return payment_rest.global_position+global_basis*Vector3(-.26,.08,.30)
	return _worker_meal_point() if worker_serving else _carried_meal_point()

func _guest_palm(entry: Dictionary, side: String) -> Vector3:
	var palm := entry[side] as BoneAttachment3D
	if palm:
		return palm.global_position
	return (entry.body as Node3D).to_global(Vector3(-.25 if side == "right" else .25,.86,.24))

func collect_meal(origin: Vector3) -> void:
	if not active or sale_order != 0 or is_instance_valid(meal):
		return
	meal = make_meal()
	add_child(meal)
	meal.global_position = origin
	meal_origin = origin
	collect_time = 0.0

static func _arc(a: Vector3, b: Vector3, t: float, lift: float) -> Vector3:
	var u := clampf(t,0,1)
	return a.lerp(b,smoothstep(0,1,u)) + Vector3.UP * (4.*u*(1.-u)*lift)

func _update_carried(dt: float, ready: bool) -> void:
	if not ready:
		if is_instance_valid(meal):
			meal.queue_free()
			meal = null
		return
	if not is_instance_valid(meal):
		# A resumed receipt materializes at its current carrier.
		collect_meal(_carried_meal_point())
		collect_time = 1.
	collect_time = minf(1.,collect_time+dt/.32)
	meal.global_position = _arc(meal_origin,_carried_meal_point(),collect_time,.15)
	meal.global_rotation.y = world.actor.global_rotation.y + .25

func _finish_worker_presentation(cancelled: bool) -> void:
	if belt_serving:
		if cancelled and is_instance_valid(meal):meal.queue_free()
		meal=parked_player_meal
		parked_player_meal=null
		belt_serving=false
		return
	if not worker_serving: return
	if cancelled:
		worker_roast = meal
		worker_origin = meal.global_position
		worker_transfer = 0.0
	meal = parked_player_meal
	parked_player_meal = null
	worker_serving = false

func _serve(dt: float) -> void:
	sale_elapsed += dt
	if not sale_committed:
		if not at_service(_server_position()) or (not worker_serving and not belt_serving and world.player_hp <= 0) or not front_ready(sale_order):
			sale_order = 0
			meal_origin = meal.global_position
			collect_time = 0.
			_finish_worker_presentation(true)
			return
		meal.global_position = _arc(exchange_origin,food_rest.global_position,sale_elapsed/FOOD_TO_BOARD,.30)
		if sale_elapsed < FOOD_TO_BOARD:
			return
		if not take_meal_payment.call(sale_order):
			sale_order = 0
			meal_origin = meal.global_position
			collect_time = 0.
			_finish_worker_presentation(true)
			return
		sale_committed = true
		cash = MONEY.instantiate()
		add_child(cash)
		exchange_event.emit("counter_trade", food_rest.global_position)
	var t := clampf((sale_elapsed-FOOD_TO_BOARD)/EXCHANGE_TIME,0,1)
	var buyer_body: Node3D = queue[0].body
	var receiving_point := _guest_palm(queue[0],"right") + buyer_body.global_basis * Vector3(-.15,.01,.04)
	meal.global_position = _arc(food_rest.global_position,receiving_point,(t-.12)/.49,.24)
	meal.global_rotation.y = lerp_angle(meal.global_rotation.y,buyer_body.global_rotation.y,clampf(10.*dt,0,1))
	if t < .48:
		cash.global_position = _arc(_guest_palm(queue[0],"left"),payment_rest.global_position,t/.48,.30)
	else:
		cash.global_position = _arc(payment_rest.global_position, _server_hand(),(t-.60)/.40,.29)
	if t >= 1.:
		var receipt := sale_order
		var buyer: Dictionary = queue.pop_front()
		buyer.request.hide()
		buyer["leg"] = 0
		# The diner retains the actual served roast while walking away.
		meal.reparent(buyer.body)
		buyer["food"] = meal
		meal = null
		leaving.append(buyer)
		_clear_presentations()
		_finish_worker_presentation(false)
		served.emit(receipt)

func advance(dt: float) -> void:
	if not active:
		return
	_walk_queue(dt)
	if sale_order != 0:
		if (worker_serving or belt_serving) and is_instance_valid(parked_player_meal): parked_player_meal.global_position = _carried_meal_point()
		if not worker_serving: _show_worker_meal(dt)
		_serve(dt)
		return
	var ledger: Dictionary = world.inventory.settlement
	var ready: bool = int(ledger.held_meal) == 1
	_update_carried(dt,ready)
	_show_worker_meal(dt)
	var order := int(ledger.served)+1
	if not front_ready(order): return
	var player_ready: bool = ready and collect_time >= 1. and world.player_hp > 0 and at_service(world.actor.global_position)
	if not player_ready:
		var worker_ready:bool=ledger.get("worker_meal",0)==1 and worker_transfer>=1. and at_service(world.survivor.actor.global_position)
		if not worker_ready and ledger.get("counter_stock",0)==0:return
		parked_player_meal=meal
		if worker_ready:
			worker_serving=true
			meal=worker_roast
			worker_roast=null
		else:
			belt_serving=true
			meal=make_meal()
			add_child(meal)
			meal.global_position=delivery_position()
	sale_order = order
	sale_elapsed = 0.0
	exchange_origin = meal.global_position
