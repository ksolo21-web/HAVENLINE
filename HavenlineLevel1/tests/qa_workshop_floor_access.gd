extends "res://tests/qa_paid_conveyors.gd"
## Run with a settled paid trial profile. Trace each full-body worker step and
## put a real raw bundle through the normal player's adjacent worksite transfer.

var observations := {}
var network

func common_floor() -> Vector3:
	var wood: Rect2 = field.processors._rect("wood",0.)
	var meat: Rect2 = field.lakeshore._footprint(0.)
	var overlap := wood.grow(field.Reach.NEAR).intersection(meat.grow(field.Reach.NEAR))
	if not overlap.has_area(): return Vector3.INF
	var centered: Vector2 = overlap.get_center()
	var nearest := INF
	var result := Vector3.INF
	for zi in ceili(overlap.size.y/.055):
		for xi in ceili(overlap.size.x/.055):
			var floor_point: Vector2 = overlap.position + Vector2(xi+.5,zi+.5)*.055
			var at := Vector3(floor_point.x,0,floor_point.y)
			if not field.lakeshore.at_cooker(at) or field.processors.at_station(at) != "wood": continue
			if not network.pedestrian_clear(at,at,field.layout.actor_radius): continue
			var distance := centered.distance_squared_to(floor_point)
			if distance < nearest:
				nearest=distance
				result=at
	return result

func verify_handoffs() -> void:
	var desk = field.settlement_loop.works
	var point := common_floor()
	check("real cook and saw have a shared standing area with physical body clearance",point.is_finite())
	if not point.is_finite(): return
	park(point)
	observations["standing_point"]=[point.x,point.z]
	for kind:String in ["wood","meat"]:
		var book=field.inventory
		check(kind+" pickup is owned",book.collect("qa-one-off-workshop-item-"+kind,kind))
		field.carry.sync(true)
		var before: int = book.settlement.hoppers[kind]
		var remaining: int = book.carried[kind]
		check(kind+" chooses its own inlet at the overlapping floor",desk._site()==kind)
		var arrived := await until(func(): return book.carried[kind]==remaining-1 and book.settlement.hoppers[kind]==before+1,80)
		check(kind+" physically arrives in its own paid inlet",arrived)
		observations[kind]={"selected_before_handoff":kind,"hopper_before":before,"hopper_after":book.settlement.hoppers[kind],"carried_after":book.carried[kind]}

func verify_walks() -> void:
	field.set_physics_process(false)
	var worker=field.survivor
	var shelf: Vector3=worker._shelf_apron()
	var stops := {"store to cooker": worker._supply_apron("meat"),"cooker to counter": worker._counter_apron(),"counter to store": shelf,"store to saw": worker._supply_apron("wood"),"saw to drill":worker._supply_apron("stone")}
	check("paid warehouse exposes an accessible material apron",shelf.is_finite())
	if not shelf.is_finite(): return
	worker.actor.global_position=shelf
	for label:String in stops:
		var goal:Vector3=stops[label]
		var reach := false
		var blocked_steps := 0
		var distance := 0.
		var trace:Array=[]
		if goal.is_finite():
			for tick in 1800:
				var previous:Vector3=worker.actor.global_position
				reach=worker._walk(goal,1./60.,true)
				var pos:Vector3=worker.actor.global_position
				if not network.pedestrian_clear(previous,pos,worker.FOOT_RADIUS):blocked_steps+=1
				distance+=previous.distance_to(pos)
				trace.append([snappedf(pos.x,.001),snappedf(pos.z,.001)])
				if reach: break
		check(label+" reaches the real service spot on foot",reach)
		check(label+" clears the installed machinery and rails",reach and blocked_steps==0)
		observations[label]={"goal":str(goal),"arrived":reach,"blocked_steps":blocked_steps,"travel_metres":distance,"travel_seconds":float(trace.size())/60.,"walk_xz":trace}

func run()->void:
	field=load("res://field_opening.tscn").instantiate()
	root.add_child(field)
	camera=field.camera
	park(Vector3(1.15,0,.9))
	field.settlement_loop.conveyors.refresh_paths()
	network=field.settlement_loop.conveyors.network
	var worker_mode:bool="--walk-forester" in OS.get_cmdline_user_args()
	if worker_mode: verify_walks()
	else: await verify_handoffs()
	print("FLOOR_ACCESS_QA ",JSON.stringify({"mode":"walk" if worker_mode else "handoff","checks":results,"observations":observations}))
	field.set_physics_process(false)
	await Session.drain_field_audio(self,field)
	field.queue_free()
	await process_frame
	quit(1 if false in results.values() else 0)
