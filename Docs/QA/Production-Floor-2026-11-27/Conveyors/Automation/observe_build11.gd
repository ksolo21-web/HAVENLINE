extends "res://tests/qa_paid_conveyors.gd"

func run()->void:
	field=load("res://field_opening.tscn").instantiate()
	root.add_child(field)
	var j:Dictionary=field.inventory.settlement
	var belts=field.settlement_loop.conveyors
	park(Vector3(1.15,0.,.9))
	# The counter exists; no customer is allowed to arrive in this interval.
	field.counter.arrival_clock=120.
	var report:Dictionary={"start":snapshot_values()}
	var stayed_away:=true
	for i in 1800:
		stayed_away=stayed_away and field.counter.queue.is_empty() and j.held_meal==0 and j.worker_meal==0 and field.settlement_loop.works.active==""
		await physics_frame
	report["final"]=snapshot_values()
	report["no_manual_work"]=stayed_away
	report["input_connected"]=belts.line_live("meat")
	report["output_connected"]=belts.line_live("meal_to_store")
	report["standing_player"]=str(field.actor.global_position)
	report["worker_rescued"]=j.rescued
	report["buffered_before_customer"]=j.counter_stock
	print("UNATTENDED ",JSON.stringify(report))
	field.set_physics_process(false)
	await Session.drain_field_audio(self,field)
	field.queue_free()
	await process_frame
	quit()
