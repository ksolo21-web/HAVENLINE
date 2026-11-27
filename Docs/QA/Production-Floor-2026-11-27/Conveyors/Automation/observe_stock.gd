extends "res://tests/qa_unattended_lines.gd"
## Observe the production journal after each normal physics tick. Times use the
## same scene clock as the sale receipt and refer to the start of this launch.
var last := {}
var sample := 0
var began := 0.
var stages := {}
var first_counter := false

func run() -> void:
	physics_frame.connect(trace_frame)
	await super()

func trace_frame() -> void:
	if not field or not is_instance_valid(field) or not field.field_ready or not field.is_physics_processing():
		return
	var j:Dictionary=field.inventory.settlement
	var lanes:Dictionary=j.line_load
	var b=field.settlement_loop.conveyors
	if sample==0:
		began=field.simulation_time
	var now:float=snappedf(field.simulation_time-began,.001)
	for lane:String in lanes:
		if sample == 0 and not lanes[lane]:
			continue
		if sample > 0 and last.get(lane,0)==lanes[lane]:
			continue
		var action:="fixture cargo resumed" if sample==0 else ("dispatch" if lanes[lane] else "delivery")
		var pose:=Vector3.ZERO
		if b.paths.has(lane) and not b.paths[lane].is_empty():
			pose=b._sample(lane,float(j.line_progress[lane])) if lanes[lane] else b.paths[lane][-1]
		print("FREIGHT ", JSON.stringify({"t":now,"lane":lane,"action":action,"xyz":[snappedf(pose.x,.001),snappedf(pose.y,.001),snappedf(pose.z,.001)],"cold_shelf":j.product_store.meal,"counter":j.counter_stock,"people_waiting":field.counter.queue.size(),"receipts":j.served}))
	if j.counter_stock==2 and not first_counter:
		print("BUFFER_FULL ", JSON.stringify({"t":now,"counter":j.counter_stock,"cold_shelf":j.product_store.meal,"people_waiting":field.counter.queue.size(),"receipts":j.served}))
		first_counter=true
	last=lanes.duplicate()
	sample+=1
