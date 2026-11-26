extends "res://tests/world_route.gd"

var braking := false
func move_to(p:Array,tol:float) -> bool:
	var pos:Vector3 = field.actor.position
	var delta := Vector3(p[0]-pos.x,0,p[1]-pos.z)
	var velocity:Vector3 = field.actor.velocity
	if delta.length() <= tol:
		braking = false
		steer(Vector2.ZERO)
		return true
	if delta.length() < 1.6 and velocity.length() > .55 and velocity.normalized().dot(delta.normalized()) < .75:
		braking = true
	if braking and velocity.length() > .15:
		steer(Vector2.ZERO)
		return false
	braking = false
	return super.move_to(p,tol)

func read_field() -> Dictionary:
	return {"at":pt(field.actor.position),"carried":field.inventory.carried.duplicate(),"paid":field.inventory.paid.duplicate(true),"order":field.inventory.build_order.duplicate(),"tokens":field.inventory.collected.size(),"wood_hud":field.opening_hud.numbers.wood.text,"hearth_floor":field.field_env.payment_costs.get_node("wood").text,"survivor_paid":field.inventory.settlement.survivor_paid,"stage":field.field_env.perimeter_stage}
	
func execute(row: Dictionary) -> void:
	if row.action == "sponsor":
		if field.inventory.settlement.survivor_paid: advance()
		elif tick-stage_tick > 1200: finished=true;quit(4)
		else: move_to([-5.5,10.9],.15)
	elif row.action == "buy_partial":
		var pos:Vector3 = field.carry.receivers[row.id].global_position
		if field.inventory.paid[row.id].wood>=9 and field.carry.flights.is_empty():
			advance()
		elif tick-stage_tick > 1800:
			finished=true
			quit(4)
		else:
			move_to([pos.x,pos.z],.18)
	else:
		super.execute(row)
