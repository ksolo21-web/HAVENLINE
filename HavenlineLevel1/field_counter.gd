extends Node3D
## The north fence stays sealed. Customers take stocked goods from the outer face.
signal served(order: int)
signal exchange_event(event: String, at: Vector3)

const Market = preload("res://field_market.gd")
const Art = preload("res://field_art.gd")
const COUNTER = preload("res://assets/customer_counter/self_service_counter.glb")
const ORDER_PLATE = preload("res://assets/customer_counter/order_plate.svg")
const ORDER_ITEM = preload("res://assets/customer_counter/roast_order.png")
const CENTER_X := 2.8
const HALF_BAY := 1.825
const HALF_DEPTH := .955
const GUARD_HEIGHT := 2.4
const CUSTOMER_Z := -1.60
const CAPACITY := 3
const SPACING := 1.15
const APPROACH_SPEED := 1.65
const FOOD_TO_BOARD := .36
const EXCHANGE_TIME := .88

var world
var model: Node3D
var service_point := Marker3D.new()
var customer_point := Marker3D.new()
var food_rest := Marker3D.new()
var payment_rest := Marker3D.new()
var queue: Array[Dictionary] = []
var leaving: Array[Dictionary] = []
var active := false
var make_customer: Callable
var take_payment: Callable
var freeze_order: Callable
var next_order := 1
var arrival_clock := 0.0
var queue_clock := 0.0
var sale_order := 0
var sale_elapsed := 0.0
var sale_committed := false
var sale_goods: Array[Dictionary] = []
var paid_amount := 0
var meal: Node3D
var cash: Node3D
var cash_pile: Array[Node3D] = []
var public_piles := {}
var guard := StaticBody3D.new()

func setup(host, visitor_factory: Callable, sale_callback: Callable, order_callback := Callable()) -> void:
	world = host
	make_customer = visitor_factory
	take_payment = sale_callback
	freeze_order = order_callback
	model = COUNTER.instantiate()
	model.name = "NorthSelfServiceCounter"
	add_child(model)
	# These are the surviving fence's timber caps. They overlap the donor/fence joins.
	for x: float in [-1.7025, 1.71076]:
		var cap: MeshInstance3D = host.field_env.donor_mesh(host.field_env.POST)
		cap.position = Vector3(x,0,0)
		add_child(cap)
	_add_marker(service_point, "WorkerInside", Vector3(0,0,1.54))
	_add_marker(customer_point, "CustomerOutside", Vector3(0,0,CUSTOMER_Z))
	# Original worktop heights measured on the docked donor's board triangles.
	_add_marker(food_rest, "MealOnBoard", Vector3(0,1.080,0))
	_add_marker(payment_rest, "NotesOnBoard", Vector3(1.16,1.085,-.10))
	var shape := CollisionShape3D.new()
	var box := BoxShape3D.new()
	box.size = Vector3(HALF_BAY*2.,GUARD_HEIGHT,HALF_DEPTH*2.)
	shape.shape = box
	shape.position.y = GUARD_HEIGHT*.5
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
	for entry in sale_goods:
		if is_instance_valid(entry.item): entry.item.queue_free()
	sale_goods.clear()
	if is_instance_valid(cash): cash.queue_free()
	meal = null
	cash = null
	sale_order = 0
	sale_elapsed = 0.
	sale_committed = false
	paid_amount = 0

# Keep motion corrections and restored feet on their original side of the paid
# fence bay, including profiles that placed their actor on the tabletop.
func constrain_actor(from: Vector3, to: Vector3, radius: float) -> Vector3:
	if not active: return to
	var start := to_local(from)
	var finish := to_local(to)
	var span := HALF_BAY+radius
	var depth := HALF_DEPTH+radius
	var in_board := absf(finish.x)<span and absf(finish.z)<depth
	var crossed := false
	if start.z*finish.z < 0.:
		var crossing_x := lerpf(start.x,finish.x,-start.z/(finish.z-start.z))
		crossed = absf(crossing_x)<span
	if not in_board and not crossed: return to
	var side := -1. if start.z < -.001 else 1.
	finish.z = side * (depth+.006)
	finish.y = 0.
	return to_global(finish)

func at_service(at: Vector3) -> bool:
	if active and world.settlement_loop and world.settlement_loop.conveyors:
		var network=world.settlement_loop.conveyors.network
		if network and network.receiver and network.receiver.at_pickup(at):return true
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
	card.name = "OrderRequest"
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
	var label := Label3D.new()
	label.name = "OrderBasket"
	label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	label.outline_size = 9
	label.font_size = 39
	label.pixel_size = .009
	label.modulate = Color("#fff3d2")
	label.outline_modulate = Color("#173754")
	label.render_priority = 4
	label.position = Vector3(0,.44,0)
	card.add_child(label)
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
		for i in entry.food.size():
			var food: Node3D = entry.food[i]
			food.global_position = _guest_palm(entry,"right") + visitor.global_basis * Vector3(-.15,.01 + float(food.get_meta("buyer_stack", 0.)),.04)
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

func delivery_position(slot: int = 0) -> Vector3:
	return stock_position("meal", slot)

func _has_serving_belt() -> bool:
	if not world.settlement_loop: return false
	var conveyors=world.settlement_loop.conveyors
	return conveyors and conveyors.network and ("meal" in conveyors.network.routes or "stored_meal" in conveyors.network.routes)

func stock_position(kind: String, slot: int = 0) -> Vector3:
	if kind == "meal" and _has_serving_belt():
		var network=world.settlement_loop.conveyors.network
		if network.receiver:
			return network.counter_buffer_position(network.receiver.position_in_queue(slot,world.inventory.settlement.market.sold.meal))
		var slot_at:Vector3=network.counter_buffer_position(slot%2)
		return slot_at + Vector3.UP*.24*floori(slot/2.)
	return _board_stock(kind,slot)

func _board_stock(kind: String, slot: int) -> Vector3:
	var x := -1.16
	if kind == "planks": x = -.52
	elif kind == "blocks": x = .14
	var size := Art.unit_extents(kind)
	return to_global(Vector3(x, 1.088 + size.y * slot, .075))

func _guest_palm(entry: Dictionary, side: String) -> Vector3:
	var palm := entry[side] as BoneAttachment3D
	if palm:
		return palm.global_position
	return (entry.body as Node3D).to_global(Vector3(-.25 if side == "right" else .25,.86,.24))

static func _arc(a: Vector3, b: Vector3, t: float, lift: float) -> Vector3:
	var u := clampf(t,0,1)
	return a.lerp(b,smoothstep(0,1,u)) + Vector3.UP * (4.*u*(1.-u)*lift)

func _show_order(card: Node3D, order: Dictionary) -> void:
	if order.is_empty():
		card.hide()
		return
	card.show()
	var single_meal: bool = order.goods.size() == 1 and order.goods.get("meal",0) == 1
	for i in 2:
		card.get_child(i).visible = single_meal
	var label := card.get_node("OrderBasket") as Label3D
	label.visible = not single_meal
	if single_meal: return
	var groups := PackedStringArray()
	for kind: String in Market.PRODUCTS:
		var count := int(order.goods.get(kind,0))
		if count == 0: continue
		var word := "Meal" if kind == "meal" and count == 1 else ("Meals" if kind == "meal" else kind.capitalize())
		groups.append("%d %s" % [count,word])
	label.text = "  +  ".join(groups)

func _prepare_sale(order: Dictionary) -> void:
	sale_order = int(order.id)
	sale_elapsed = 0.
	paid_amount = int(order.price)
	var stack_height := 0.
	for kind: String in Market.PRODUCTS:
		for slot in int(order.goods.get(kind, 0)):
			var from_belt:=kind=="meal" and _has_serving_belt()
			var source_slot:=slot
			if from_belt and not world.settlement_loop.conveyors.network.receiver:
				# Take from the tail first so an unsold leading portion stays
				# on its rollers throughout a mixed or partial basket sale.
				var available:=clampi(Market.available(world.inventory.settlement,kind),1,4)
				source_slot=maxi(0,available-1-slot)
			var item := Art.make(kind)
			item.set_meta("buyer_stack", stack_height)
			stack_height += Art.unit_extents(kind).y
			item.hide()
			add_child(item)
			item.global_position = stock_position(kind,source_slot)
			var receiver_meal:bool=from_belt and world.settlement_loop.conveyors.network.receiver!=null
			if receiver_meal:item.rotation.y=-PI*.5
			sale_goods.append({"kind":kind,"slot":source_slot,"source":item.global_position,"item":item,"receiver_meal":receiver_meal})
			if kind == "meal" and meal == null: meal = item

# The wider table sits several metres inside the sales bay. Start the
# normal automatic presentation when the order is accepted, then pass the
# portion across the counter lip directly into the customer's actual mitt.
func _present_from_receiver(visual:Dictionary,buyer:Dictionary,index:int) -> void:
	var piece:Node3D=visual.item
	var front:Vector3=food_rest.global_position+Vector3(.12*index,.04+.10*index,-.39)
	var body:Node3D=buyer.body
	var hand:=_guest_palm(buyer,"right")+body.global_basis*Vector3(-.15,.01 + float(piece.get_meta("buyer_stack", 0.)),.04)
	var elapsed:=maxf(0.,sale_elapsed-index*.04)
	var on_board:=FOOD_TO_BOARD+EXCHANGE_TIME*.36
	if elapsed<on_board:
		var ratio:=elapsed/on_board
		piece.global_position=_arc(visual.source,front,ratio,.32)
	else:
		piece.global_position=_arc(front,hand,(elapsed-on_board)/(.38*EXCHANGE_TIME),.17)
	piece.show()

func _serve(dt: float) -> void:
	sale_elapsed += dt
	if not sale_committed:
		if not front_ready(sale_order):
			_clear_presentations()
			return
		if sale_elapsed < FOOD_TO_BOARD:
			for i in sale_goods.size():
				if sale_goods[i].receiver_meal:_present_from_receiver(sale_goods[i],queue[0],i)
			return
		if not take_payment.call(sale_order):
			_clear_presentations()
			return
		sale_committed = true
		cash = Art.make("money")
		add_child(cash)
		exchange_event.emit("counter_trade",food_rest.global_position)
	var t := clampf((sale_elapsed-FOOD_TO_BOARD)/EXCHANGE_TIME,0,1)
	var buyer: Dictionary = queue[0]
	var body: Node3D = buyer.body
	for i in sale_goods.size():
		var visual: Dictionary = sale_goods[i]
		var piece: Node3D = visual.item
		piece.show()
		var destination := _guest_palm(buyer,"right") + body.global_basis * Vector3(-.15,.01 + float(piece.get_meta("buyer_stack", 0.)),.04)
		var stock:Vector3=visual.source
		var reach := (t-.12-i*.065)/.49
		if visual.receiver_meal:
			_present_from_receiver(visual,buyer,i)
		elif visual.kind == "meal" and to_local(stock).z>HALF_DEPTH:
			# The automatic counter presents the queued portion at the customer
			# edge before the buyer takes it, keeping the goods above the board.
			var board:Vector3=food_rest.global_position+Vector3(0,.02,-.58)
			piece.global_position=_arc(stock,board,reach/.54,.41) if reach<.54 else _arc(board,destination,(reach-.54)/.46,.17)
		else:
			piece.global_position=_arc(stock,destination,reach,.23)
		piece.global_rotation.y = lerp_angle(piece.global_rotation.y,body.global_rotation.y,clampf(10.*dt,0,1))
	cash.global_position = _arc(_guest_palm(buyer,"left"),payment_rest.global_position,t/.48,.27)
	cash.visible = t < .48
	if t < 1.: return
	var receipt := sale_order
	queue.pop_front()
	buyer.request.hide()
	buyer.leg = 0
	buyer.food = []
	for visual in sale_goods:
		var piece: Node3D = visual.item
		piece.reparent(body)
		buyer.food.append(piece)
	sale_goods.clear()
	leaving.append(buyer)
	_clear_presentations()
	served.emit(receipt)

func cash_in_exchange() -> int:
	if sale_order == 0 or not sale_committed: return 0
	return paid_amount if (sale_elapsed-FOOD_TO_BOARD)/EXCHANGE_TIME<.48 else 0

func show_cash(balance: int) -> void:
	var visible_count := clampi(balance-cash_in_exchange(),0,2) if active else 0
	while cash_pile.size() < visible_count:
		var note := Art.make("money")
		note.name = "CounterCash"
		add_child(note)
		cash_pile.append(note)
	for i in cash_pile.size():
		var note: Node3D = cash_pile[i]
		note.visible = i < visible_count
		if note.visible:
			var size := Art.unit_extents("money")
			note.position = payment_rest.position + Vector3(0., size.y * i, 0.)

func show_goods(journal: Dictionary) -> void:
	var serving:=_has_serving_belt()
	var station=world.settlement_loop.conveyors.network.receiver if serving else null
	for kind: String in Market.PRODUCTS:
		var wide:bool=kind=="meal" and station!=null
		var capacity:int=station.CAPACITY if wide else 4
		var count := clampi(Market.available(journal,kind),0,capacity) if active else 0
		var pile: Array = public_piles.get_or_add(kind,[])
		# Index actual pieces by sale sequence. A customer removes exactly its
		# piece; the stock behind it advances one row in that column.
		var needed:int=capacity if wide and count>0 else count
		while pile.size()<needed:
			var resource := Art.make(kind)
			resource.name="Counter"+kind.capitalize()
			resource.hide()
			add_child(resource)
			pile.append(resource)
		for index in pile.size():
			var piece:Node3D=pile[index]
			var rank:=posmod(index-int(journal.market.sold.meal),capacity) if wide else index
			var visible_piece:=rank<count and index<capacity
			if wide and sale_order>int(journal.served):
				for receipt:Dictionary in sale_goods:
					if receipt.receiver_meal and receipt.slot==rank:
						visible_piece=false
						break
			if visible_piece:
				var target:=stock_position(kind,rank)
				if wide and piece.visible and piece.global_position.distance_to(target)<station.ROW_PITCH+.035:
					piece.global_position=piece.global_position.move_toward(target,get_physics_process_delta_time()*3.5)
				else:
					piece.global_position=target
				piece.rotation.y=-PI*.5 if wide else 0.
			piece.visible=visible_piece

func advance(dt: float) -> void:
	if not active:
		return
	_walk_queue(dt)
	if sale_order != 0:
		_serve(dt)
		return
	if queue.is_empty() or not freeze_order.is_valid(): return
	var id := int(queue[0].order)
	var order: Dictionary = freeze_order.call(id)
	_show_order(queue[0].request,order)
	if front_ready(id) and Market.can_fill(world.inventory.settlement,order):
		_prepare_sale(order)
