extends SceneTree

func _initialize() -> void:
	run.call_deferred()

func run() -> void:
	var field = load("res://field_opening.tscn").instantiate()
	root.add_child(field)
	for i in 5: await physics_frame
	var route_scene = load("res://field_home_route.gd")
	var reports := {}
	for stage in [0,1,2,3]:
		if stage == 1:
			for i in int(field.inventory.costs.center_hearth.wood):
				field.inventory.collect("t02-route-camp-"+str(i),"wood")
				field.inventory.payment("center_hearth","wood",false)
			field._finish_purchase("center_hearth")
			field._apply_hearth(true,false)
			field.reveal_countdown = -1.
		if stage > 0:
			field.field_env.set_perimeter(stage,false)
		for x in [-74.0,-27.0,8.0,56.0]:
			var guide = route_scene.new()
			var actor_radius: float = field.layout.actor_radius
			var edges: Vector2 = field.river.banks_at(x)
			var p := Vector2(x,edges.x-2.06)
			var length := 0.0
			var reached := false
			for tick in 950:
				if stage > 0 and field.field_env.is_inside_camp(Vector3(p.x,0,p.y)):
					reached = true
					break
				if not guide.update(field,p): break
				if stage == 0 and guide.distance < .26:
					reached = true
					break
				var next := p.move_toward(guide.direction_target,.235)
				if next.distance_squared_to(p) < .00001 or not field.river.travel_clear(p,next,actor_radius): break
				length += p.distance_to(next)
				p = next
			reports["stage-%s-x-%s" % [stage,x]] = {"reached":reached,"length_m":length,"finish":str(p)}
	print("T02_COMPLETE_ROUTES ",JSON.stringify(reports))
	var okay := true
	for record in reports.values():
		okay = okay and record.reached
	await load("res://tests/lifecycle_test_profile.gd").drain_field_audio(self,field)
	field.queue_free()
	for i in 6: await process_frame
	quit(0 if okay else 1)
