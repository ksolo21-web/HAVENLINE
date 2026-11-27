extends SceneTree
## Exercise the live presentation across a real north perimeter, with isolated sale receipts.
const Counter = preload("res://field_counter.gd")
const Human = preload("res://field_human.gd")
const FieldEnvironment = preload("res://field_environment.gd")

class TestHost extends Node3D:
	var field_env = FieldEnvironment.new()
	var actor := Node3D.new()
	var player_hp := 100
	var inventory := {"settlement":{"cooked":0,"served":0,"held_meal":0}}
	var calls := []
	var presentation_guard: Callable
	var service
	func sale(order: int) -> bool:
		calls.append(order)
		if not presentation_guard.call(order) or order != inventory.settlement.served+1 or inventory.settlement.cooked <= inventory.settlement.served:
			return false
		inventory.settlement.served = order
		if service.belt_serving: inventory.settlement.counter_stock -= 1
		else: inventory.settlement.held_meal = 0
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

func _initialize() -> void:
	call_deferred("run")

func run() -> void:
	root.add_child(host)
	host.add_child(host.field_env)
	host.field_env.add_child(host.field_env.buy_anchor)
	host.field_env.add_child(host.field_env.upgrade_anchor)
	host.add_child(host.actor)
	host.add_child(counter)
	host.presentation_guard = counter.awaiting_payment
	host.service = counter
	counter.setup(host, visitor_model, host.sale)
	check("counter hidden and harmless before expansion",not counter.visible and counter.guard.collision_layer==0)
	counter.set_active(true,0)
	var north: float = FieldEnvironment.COURTS[-1].y
	check("north plane and both stances",is_equal_approx(counter.position.z,north) and counter.service_point.global_position.z > north and counter.customer_point.global_position.z < north)
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
	host.inventory.settlement.cooked=1
	host.actor.global_position=counter.service_point.global_position
	simulate(.6)
	check("a meal on the cooker rack cannot initiate a remote sale",host.calls.is_empty() and not is_instance_valid(counter.meal))
	host.inventory.settlement.held_meal=1
	host.actor.global_position=counter.customer_point.global_position
	simulate(1.)
	check("outside cannot initiate meal service",host.calls.is_empty() and is_instance_valid(counter.meal))
	host.actor.global_position=counter.service_point.global_position
	simulate(.20)
	host.actor.global_position+=Vector3.RIGHT*3.
	simulate(.50)
	check("withdrawn delivery remains with actor",host.calls.is_empty() and counter.sale_order==0 and is_instance_valid(counter.meal))
	host.actor.global_position=counter.service_point.global_position
	host.player_hp=0
	simulate(.55)
	check("unconscious player cannot serve",host.calls.is_empty())
	host.player_hp=100
	simulate(.45)
	check("worktop commit once with payment prop",host.calls==[1] and counter.sale_committed and is_instance_valid(counter.cash))
	simulate(1.)
	check("ordered handover retires first guest",counter.queue[0].order==2 and counter.leaving.size()==1 and counter.leaving[0].body.get_child_count()>0)
	simulate(7.)
	check("no duplicate payment or diner",host.calls==[1] and counter.leaving.is_empty() and sighted(2))
	counter.set_active(false,1)
	counter.set_active(true,1)
	host.inventory.settlement.cooked=2
	host.inventory.settlement.held_meal=1
	host.actor.global_position=Vector3.ZERO
	simulate(7.)
	check("saved meal restored with next order",sighted(2) and is_instance_valid(counter.meal) and host.calls==[1])
	host.actor.global_position=counter.service_point.global_position
	simulate(2.)
	check("second ticket commits exactly once",host.calls==[1,2])
	counter.set_active(false,2)
	check("visual and queue cleanup",counter.queue.is_empty() and counter.leaving.is_empty() and not counter.visible and counter.guard.collision_layer==0)
	counter.set_active(true,2)
	host.actor.global_position = Vector3(0,0,30)
	simulate(6.)
	host.inventory.settlement.cooked = 3
	host.inventory.settlement.counter_stock = 1
	simulate(.6)
	check("stock alone cannot grant a remote sale",host.calls==[1,2])
	var pickup := func(_slot:int)->Vector3: return counter.to_global(Vector3(-.64,.85,1.45))
	counter.staff_food_line(pickup)
	var start_point:Vector3=counter.attendant.body.global_position
	simulate(.22)
	check("cashier walks empty handed to buffer before payment",counter.belt_serving and counter.attendant.body.global_position.distance_to(start_point)>.12 and counter.meal.global_position.distance_to(pickup.call(0))<.015 and not counter.awaiting_payment(3))
	var saw_lift:=false
	var saw_carry:=false
	var cash_on_register:=false
	var min_staff_clearance:=INF
	for tick in 270:
		counter.advance(1./60.)
		var feet:Vector3=counter.attendant.body.position
		var closest:=Vector2(clampf(feet.x,-.64,.53),1.45)
		min_staff_clearance=minf(min_staff_clearance,Vector2(feet.x,feet.z).distance_to(closest))
		if counter.belt_serving and counter.attendant.step==counter.attendant.Step.LIFT: saw_lift=true
		if counter.belt_serving and counter.attendant.step==counter.attendant.Step.CARRY and counter.meal.global_position.distance_to(counter.attendant.hand())<.075: saw_carry=true
		if counter.sale_committed and counter.sale_elapsed>Counter.FOOD_TO_BOARD+Counter.EXCHANGE_TIME*.70:
			cash_on_register=counter.cash.global_position.distance_to(counter.payment_rest.global_position)<.015
	check("cashier clears the rounded end and standby roller lane on foot",min_staff_clearance>.52)
	check("cashier lifts the stock and visibly carries it with an actual palm",saw_lift and saw_carry and counter.attendant.palm!=null)
	check("one handed-off portion cleared the buffer and paid at the register",host.calls==[1,2,3] and host.inventory.settlement.counter_stock==0 and cash_on_register)
	host.queue_free()
	for i in 3: await process_frame
	print(JSON.stringify({"checks":successes,"failures":failures}))
	quit(0 if failures.is_empty() else 1)
