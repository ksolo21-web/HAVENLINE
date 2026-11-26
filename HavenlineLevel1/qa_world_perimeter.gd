extends SceneTree
## Exercise the live wall and leaf physics in every authored expansion size.
var failures: Array[String] = []
var rows := []

func check(ok: bool, label: String) -> void:
	if not ok: failures.append(label)

func _initialize() -> void:
	call_deferred("run")

func pay_fixture(game: Node, id: String) -> void:
	for kind: String in game.inventory.remaining(id):
		for n in int(game.inventory.remaining(id)[kind]):
			game.inventory.collect("perimeter-%s-%s-%s" % [id,kind,n],kind)
			check(game.inventory.payment(id,kind,false),"fixture transaction "+id)
	game._finish_purchase(id)

func save_frame(folder: String, label: String) -> void:
	RenderingServer.force_draw()
	root.get_texture().get_image().save_jpg(folder.path_join(label+".jpg"),.94)

func detail_views(game, folder: String) -> void:
	game.set_zoom_ratio(2.)
	for i in 3: await physics_frame
	save_frame(folder,"stage-1-gameplay-2x")
	game.set_zoom_ratio(1.)
	# These reverse-side construction views inspect the actual earned gate.
	# Gameplay captures keep using the original camera.
	var original_feet: Vector3 = game.actor.position
	game.actor.position = Vector3(-4.,0,8.)
	for i in 12: await physics_frame
	game.opening_hud.hide()
	var eye := Camera3D.new()
	game.add_child(eye)
	eye.projection = Camera3D.PROJECTION_ORTHOGONAL
	eye.size = 2.35
	eye.current = true
	var gate: Vector3 = game.gates[0].global_position
	for view in [{"name":"gate-front","z":1.84},{"name":"gate-rear","z":-1.84}]:
		eye.global_position = gate+Vector3(.19,1.49,view.z)
		eye.look_at(gate+Vector3(0,.79,0))
		await process_frame
		save_frame(folder,view.name)
	for view in [{"name":"wall-front","z":1.84},{"name":"wall-rear","z":-1.84}]:
		var at := gate+Vector3(3.25,0,0)
		eye.global_position = at+Vector3(.28,1.2,view.z)
		eye.look_at(at+Vector3(0,.64,0))
		await process_frame
		save_frame(folder,view.name)
	eye.global_position = gate+Vector3(.33,1.64,2.05)
	eye.look_at(gate+Vector3(0,.79,0))
	var mechanism = game.gates[0]
	var outside := gate+Vector3(0,0,1.95)
	mechanism.request_toggle(outside)
	for i in 15: mechanism.advance(1./60.,outside,.31)
	await process_frame
	save_frame(folder,"gate-unlatching")
	for i in 60: mechanism.advance(1./60.,outside,.31)
	await process_frame
	save_frame(folder,"gate-open")
	mechanism.request_toggle(outside)
	for i in 70: mechanism.advance(1./60.,outside,.31)
	game.actor.position = original_feet
	game.opening_hud.show()
	game.camera.current = true
	eye.queue_free()

func run() -> void:
	var game = preload("res://field_opening.tscn").instantiate()
	root.add_child(game)
	for i in 8: await physics_frame
	var env = game.field_env
	check(not env.is_inside_camp(Vector3.ZERO),"unpaid center must be outdoors")
	check(game.gates.all(func(g): return not g.active),"unpaid gate must be inactive")
	pay_fixture(game,"center_hearth")
	game._apply_hearth(true,false)
	for stage in [1,2,3,1]:
		if stage == 2:
			pay_fixture(game,"expansion_1")
		elif stage == 3:
			for id in ["storage_wood","storage_stone","storage_meat","expansion_2"]: pay_fixture(game,id)
		env.set_perimeter(stage,false)
		for i in 3: await physics_frame
		var rect: Vector4 = env.COURTS[stage-1]
		check(env.is_inside_camp(Vector3.ZERO),"center")
		check(env.is_inside_camp(Vector3(rect.z,0,0)),"east threshold")
		check(not env.is_inside_camp(Vector3(rect.z+.01,0,0)),"outside east threshold")
		var record := {"stage":stage,"rect":game.layout.camp_rect_xz.duplicate(),"panel_modules":env.palisades.multimesh.instance_count,"gates":[]}
		for wall in game.layout.walls_xz:
			var at := Vector3(wall[0],.5,wall[1])
			var query := PhysicsPointQueryParameters3D.new()
			query.position = at
			query.collision_mask = 1
			check(not game.get_world_3d().direct_space_state.intersect_point(query).is_empty(),"wall collider %s" % at)
		for gate in game.gates:
			var normal: Vector3 = gate.global_basis.z
			var start: Vector3 = gate.position+Vector3.UP*.55+normal*1.8
			var end: Vector3 = gate.position+Vector3.UP*.55-normal*1.8
			var query := PhysicsRayQueryParameters3D.create(start,end,1)
			# Probe the gate and fence. A mobile wolf may occupy the exterior
			# approach while the leaves are open.
			var actors: Array[RID] = [game.actor.get_rid()]
			for wolf in game.enemies:
				for body in wolf.find_children("*", "CollisionObject3D", true, false):
					actors.append(body.get_rid())
			query.exclude = actors
			# Offset from the narrow gap between both opposing leaf tips.
			var offset: Vector3 = gate.global_basis.x*.20
			query.from += offset
			query.to += offset
			if gate.angle > 0:
				gate.request_toggle(start)
				for i in 65: gate.advance(1./60.,start,.31)
			for i in 2: await physics_frame
			check(not game.get_world_3d().direct_space_state.intersect_ray(query).is_empty(),gate.name+" closed")
			check(gate.request_toggle(start),gate.name+" reachable controls")
			for i in 65: gate.advance(1./60.,start,.31)
			for i in 2: await physics_frame
			var blockage: Dictionary = game.get_world_3d().direct_space_state.intersect_ray(query)
			check(blockage.is_empty(),"%s stage %d open (%s)" % [gate.name,stage,blockage.collider.get_path() if not blockage.is_empty() else "clear"])
			query.from=end+offset
			query.to=start+offset
			check(game.get_world_3d().direct_space_state.intersect_ray(query).is_empty(),gate.name+" inbound open")
			record.gates.append({"id":gate.gate_id,"center":str(gate.position)})
			gate.request_toggle(start)
			for i in 65: gate.advance(1./60.,start,.31)
		rows.append(record)
		if OS.get_environment("CAMP_STAGE_STILLS") != "" and rows.size() <= 3:
			game.actor.position = Vector3(1.7,0,rect.w+1.45)
			for i in 65: await physics_frame
			var folder := OS.get_environment("CAMP_STAGE_STILLS")
			save_frame(folder,"stage-%d"%stage)
			if stage == 1: await detail_views(game,folder)
	print(JSON.stringify({"perimeter":rows,"failures":failures}))
	await preload("res://tests/lifecycle_test_profile.gd").drain_field_audio(self, game)
	game.queue_free()
	for tick in 5: await process_frame
	quit(1 if not failures.is_empty() else 0)
