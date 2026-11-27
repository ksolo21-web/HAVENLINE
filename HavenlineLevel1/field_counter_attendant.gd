extends RefCounted
## A paid food line restocks a finite staff buffer. The attendant has to lift
## its first portion, walk to the board and present it before a sale can close.

enum Step { WAITING, APPROACH, LIFT, CARRY, AT_BOARD }
const BOARD_STANCE := Vector3(-1.25,0.,1.26)
const WALK_SPEED := 1.85
const LIFT_TIME := .27

var body: Node3D
var palm: BoneAttachment3D
var step := Step.WAITING
var phase := 0.
var lift_clock := 0.

func install(counter: Node3D, factory: Callable) -> void:
	body = factory.call("customer_female_01")
	body.name = "CounterAttendant"
	counter.add_child(body)
	body.position = BOARD_STANCE
	body.rotation.y = PI
	palm = counter._attach_to_palm(body,"Palm.R")

func hand() -> Vector3:
	return palm.global_position if palm else body.to_global(Vector3(-.21,.86,.23))

func begin() -> void:
	step = Step.APPROACH
	lift_clock = 0.

func idle(dt: float) -> void:
	step = Step.WAITING
	if _walk(BOARD_STANCE,dt,false):
		_face(Vector3.FORWARD,dt)
		phase = fposmod(phase+dt*.45,1.)
		body.pose("idle",phase)

func _face(direction: Vector3, dt: float) -> void:
	body.rotation.y = rotate_toward(body.rotation.y,atan2(direction.x,direction.z),dt*10.)

func _walk(goal: Vector3, dt: float, loaded: bool) -> bool:
	var offset := goal-body.position
	if offset.length_squared() < .000001: return true
	var before := body.position
	body.position = before.move_toward(goal,WALK_SPEED*dt)
	_face(offset,dt)
	phase = fposmod(phase+body.position.distance_to(before)/1.35,1.)
	body.pose("carry" if loaded else "walk",phase)
	return body.position.is_equal_approx(goal)

func bring_to_board(dt: float, meal: Node3D, slot: Vector3) -> bool:
	var counter := body.get_parent_node_3d()
	var pickup := counter.to_local(slot)
	if step == Step.APPROACH:
		meal.global_position = slot
		if _walk(Vector3(pickup.x-.58,0.,pickup.z+.46),dt,false):
			step = Step.LIFT
	elif step == Step.LIFT:
		lift_clock = minf(lift_clock+dt,LIFT_TIME)
		_face(Vector3(pickup.x-body.position.x,0.,pickup.z-body.position.z),dt)
		var reach := lift_clock/LIFT_TIME
		body.pose("receive",.5*reach)
		meal.global_position = slot.lerp(hand(),smoothstep(.27,1.,reach))
		if lift_clock >= LIFT_TIME: step = Step.CARRY
	elif step == Step.CARRY:
		var arrived := _walk(BOARD_STANCE,dt,true)
		meal.global_position = hand()
		if arrived:
			step = Step.AT_BOARD
	return step == Step.AT_BOARD

func present(dt: float, elapsed: float, until_board: float, exchange: float) -> void:
	_face(Vector3.FORWARD,dt)
	var reach := clampf(elapsed/until_board,0.,1.)
	if elapsed > until_board:
		reach = 1.-clampf((elapsed-until_board)/exchange,0.,1.)
	body.pose("receive",.5*reach)
