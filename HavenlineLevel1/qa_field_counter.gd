extends SceneTree
## Exercise the live presentation across a real north perimeter, with isolated sale receipts.
const Counter = preload("res://field_counter.gd")
const Human = preload("res://field_human.gd")
const FieldEnvironment = preload("res://field_environment.gd")

const Market = preload("res://field_market.gd")

class TestHost extends Node3D:
	var field_env = FieldEnvironment.new()
	var actor := Node3D.new()
	var inventory := {"settlement":{"cooked":0,"served":0,"held_meal":0,"counter_stock":0,"market":Market.EMPTY.duplicate(true)}}
	var calls := []
	var presentation_guard: Callable

	func quote(id: int) -> Dictionary:
		var j: Dictionary = inventory.settlement
		if id != int(j.served) + 1: return {}
		if j.market.order.is_empty():
			j.market.order = Market.new_order(id,true,true,true,id>2)
		return j.market.order

	func sale(order: int) -> bool:
		if not presentation_guard.call(order) or not Market.sell(inventory.settlement,order): return false
		calls.append(order)
		return true

var failures := []
var successes := {}
var counter = Counter.new()
var host := TestHost.new()

func check(label: String, condition: bool) -> void:
	successes[label] = condition
	if not condition:
		failures.append(label)
		push_error(label)

func simulate(seconds: float) -> void:
	for i in ceili(seconds*60.):
		counter.advance(1./60.)

func visitor_model(identity: String) -> Node3D:
	var visitor := Human.new()
	visitor.configure(identity)
	return visitor

func sighted(order: int) -> bool:
	return not counter.queue.is_empty() and counter.queue[0].order == order and counter.front_ready(order)

func check_paid_counter_barrier() -> void:
	var probe := CharacterBody3D.new()
	var shape := CollisionShape3D.new()
	var capsule := CapsuleShape3D.new()
	capsule.radius = .31
	capsule.height = 1.68
	shape.shape = capsule
	shape.position.y = capsule.height*.5
	probe.add_child(shape)
	host.add_child(probe)
	await physics_frame
	var physical := true
	var constrained := true
	var restored := true
	for side:float in [-1.,1.]:
		for lateral:float in [-1.72,0.,1.72]:
			for rise:float in [0.,1.10]:
				var start:Vector3 = counter.to_global(Vector3(lateral,rise,side*2.))
				var end:Vector3 = counter.to_global(Vector3(lateral,rise,-side*2.))
				probe.global_position = start
				var collision := probe.move_and_collide(end-start,true)
				physical = physical and collision != null and collision.get_collider()==counter.guard
				var resolved:Vector3 = counter.to_local(counter.constrain_actor(start,end,capsule.radius))
				constrained = constrained and resolved.z*side>Counter.HALF_DEPTH and is_zero_approx(resolved.y)
			var embedded:Vector3 = counter.to_global(Vector3(lateral,1.1,side*.3))
			var clear:Vector3 = counter.to_local(counter.constrain_actor(embedded,embedded,capsule.radius))
			restored = restored and clear.z*side>Counter.HALF_DEPTH+capsule.radius and is_zero_approx(clear.y)
	check("player collides with both counter facades up to worktop height",physical)
	check("post-movement corrections preserve each side of the paid counter",constrained)
	check("embedded positions recover on ground and on their original side",restored)
	probe.queue_free()

func _initialize() -> void:
	call_deferred("run")

func run() -> void:
	root.add_child(host)
	host.add_child(host.field_env)
	host.field_env.add_child(host.field_env.buy_anchor)
	host.field_env.add_child(host.field_env.upgrade_anchor)
	# This counter-only fixture skips building the hearth and must own its unused fire node.
	host.field_env.add_child(host.field_env.hearth_fire)
	host.field_env.hearth_fire.set_physics_process(false)
	host.add_child(host.actor)
	host.add_child(counter)
	host.presentation_guard = counter.awaiting_payment
	counter.setup(host, visitor_model, host.sale, host.quote)
	check("counter hidden and harmless before expansion",not counter.visible and counter.guard.collision_layer==0)
	counter.set_active(true,0)
	var north: float = FieldEnvironment.COURTS[-1].y
	check("north plane and both stances",is_equal_approx(counter.position.z,north) and counter.service_point.global_position.z > north and counter.customer_point.global_position.z < north)
	await check_paid_counter_barrier()
	for i in 4: counter.set_active(true,0)
	simulate(7.)
	check("three physical waiting bodies",counter.queue.size()==3 and sighted(1))
	check("authored visitors have both actual palms",counter.queue[0].right != null and counter.queue[0].left != null and counter.queue[0].body.identity != counter.queue[1].body.identity)
	check("waiting guest alone cannot collect a payment",not counter.awaiting_payment(1))
	var outside := true
	for i in range(counter.queue.size()):
		var body: Node3D = counter.queue[i].body
		outside = outside and body.global_position.z < north-1. and body.is_inside_tree()
		if i: outside=outside and body.position.distance_to(counter.queue[i-1].body.position)>=Counter.SPACING-.005
	check("outside FIFO with physical spacing",outside)
	var journal: Dictionary = host.inventory.settlement
	journal.cooked = 1
	journal.held_meal = 1
	host.actor.global_position = counter.to_global(Vector3(0,0,4))
	simulate(1.)
	check("a private meal cannot grant a remote sale",host.calls.is_empty() and not is_instance_valid(counter.meal))
	journal.held_meal = 0
	journal.counter_stock = 1
	simulate(.45)
	check("unstaffed worktop settles physical goods and payment once",host.calls==[1] and counter.sale_committed and is_instance_valid(counter.cash))
	simulate(1.)
	check("self-service retires first guest with the purchased food",counter.queue[0].order==2 and not counter.leaving.is_empty() and counter.leaving[0].food.size()==1)
	simulate(7.)
	check("no duplicate payment or diner",host.calls==[1] and counter.leaving.is_empty() and sighted(2))
	counter.set_active(false,1)
	check("visual and queue cleanup",counter.queue.is_empty() and counter.leaving.is_empty() and not counter.visible and counter.guard.collision_layer==0)
	counter.set_active(true,1)
	journal.counter_stock = 1
	simulate(7.)
	check("second ticket commits once after reopening",host.calls==[1,2])
	simulate(5.)
	check("next basket asks for two meals",journal.market.order.goods=={"meal":2})
	journal.counter_stock = 1
	simulate(1.)
	check("buyer waits for the entire displayed basket",host.calls==[1,2])
	journal.counter_stock = 2
	simulate(4.)
	check("complete multi-unit order debits both goods",host.calls==[1,2,3] and journal.counter_stock==0)
	simulate(5.)
	check("developed buyer asks for meal and planks",journal.market.order.goods=={"meal":1,"planks":1})
	journal.counter_stock = 1
	journal.market.counter_products.planks = 1
	simulate(4.)
	check("mixed basket pays its whole price once without a clerk",host.calls==[1,2,3,4] and journal.market.counter_cash==7 and journal.market.sold=={"meal":5,"planks":1,"blocks":0})
	check("different product piles are visibly separate",counter.stock_position("meal").distance_to(counter.stock_position("planks"))>.50 and counter.stock_position("blocks").distance_to(counter.payment_rest.global_position)>.65)
	host.queue_free()
	for i in 3: await process_frame
	print(JSON.stringify({"checks":successes,"failures":failures}))
	quit(0 if failures.is_empty() else 1)
