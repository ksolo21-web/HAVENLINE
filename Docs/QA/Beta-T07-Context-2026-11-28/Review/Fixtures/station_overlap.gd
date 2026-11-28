extends "res://tests/qa_snow_truck.gd"

var results := []

func _initialize()->void:
	run.call_deferred()

func choose_point(stone: Rect2, wood: Rect2) -> Vector2:
	var r: float = float(field.layout.actor_radius)+.025
	var around: Rect2 = wood.grow(field.Reach.NEAR)
	for x in range(ceili(around.position.x*20.),floori(around.end.x*20.)+1):
		for z in range(ceili(around.position.y*20.),floori(around.end.y*20.)+1):
			var p := Vector2(x*.05,z*.05)
			var at := Vector3(p.x,0,p.y)
			if not field.field_env.is_inside_camp(at) or field.depot.at_loading_area(at) or field.counter.at_service(at):continue
			var a: float = field.Reach.distance_to_rect(p,wood)
			var b: float = field.Reach.distance_to_rect(p,stone)
			if a>=r and b<=field.Reach.NEAR and b>a+.024:
				return p
	return Vector2.INF

func stage() -> Vector3:
	var house = field.camp_layout
	var stone: Rect2 = field.processors._rect("stone",0.)
	var around := Vector2(-7.0,-1.55)
	var footprint: Rect2 = field.processors.FOOTPRINT.wood
	for row in [Vector2(-.5,-3.25),Vector2(0,-3.25),Vector2(.5,-3.25),Vector2(3.75,0),
		Vector2(4.,0),Vector2(3.75,.5),Vector2(0,3.5),Vector2(0,3.75),Vector2(.5,3.5)]:
		var target: Vector2 = house._snap("saw_bench",around+row)
		if not house.reason("saw_bench",target).is_empty():
			continue
		var wood := Rect2(footprint.position+target,footprint.size)
		var spot := choose_point(stone,wood)
		if not spot.is_finite():continue
		if house.relocate("saw_bench",target):
			print("LEGAL STATION OVERLAP ",str(target)," ",str(spot))
			return Vector3(spot.x,0,spot.y)
	return Vector3.INF

func run()->void:
	field = load("res://field_opening.tscn").instantiate()
	root.add_child(field)
	camera=field.camera
	truck=field.snow_truck
	for n in 7:await physics_frame
	for name in ["center_hearth","expansion_1","storage_wood","storage_stone","storage_meat","expansion_2","camp_cooker","saw_bench","quarry_drill"]:
		if not _fund(name):
			print("FAILED TO FUND ",name)
			await _close_field()
			quit(2)
			return
		if name=="center_hearth":
			for n in 14:await physics_frame
	for wolf in field.enemies.duplicate():field.encounters._remove(wolf)
	field.encounters.remaining=900.
	var location := stage()
	if not location.is_finite():
		print("NO LEGAL OVERLAP")
		await _close_field()
		quit(3)
		return
	field.inventory.collected["t07-output-overlap-ore"]="stone"
	field.inventory.settlement.processed_stone+=1
	field._inventory_changed()
	field.actor.global_position=location
	field.previous_dry_position=location
	for n in 45:
		await physics_frame
		var work = field.settlement_loop.works
		var ex = field.settlement_loop.exchange
		if n in [0,4,8,20,44]:
			results.append({"n":n,"selected":field.context.descriptor.get("id",""),"nearest":ex._machine_at(location),
				"valid_drill":work.can_operate("stone"),"rack":ex.Logistics.rack(field.inventory.settlement,"stone"),
				"w":work.machine_distance("wood",location),"s":work.machine_distance("stone",location),
				"held":field.inventory.settlement.hand_products.blocks,
				"persist_blocked":field.persist_blocked})
	print("OVERLAP_RESULT ",JSON.stringify(results))
	await _close_field()
	quit()
