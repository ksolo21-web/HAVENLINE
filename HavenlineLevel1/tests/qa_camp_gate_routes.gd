extends "res://tests/qa_worker_jobs.gd"

const TEST := "res://tests/qa_camp_gate_routes.gd"
const STEP := 1.0/60.0
const FAR := Vector3(42.,0.,22.)
var transits: Array[Dictionary] = []

func _initialize() -> void:
	if not Session.isolated(self,TEST): run.call_deferred()

func place_player(at: Vector3) -> void:
	game.actor.global_position = at
	game.previous_dry_position = at
	game.actor.velocity = Vector3.ZERO
	game.gait_motor.travel_speed = 0.0

func send_to(gate, target: Vector3) -> bool:
	worker.travel_speed = 0.0
	worker.route = worker._camp_route(worker.actor.global_position,target)
	var throat: Vector3 = gate.to_global(Vector3(0.,0.,-worker.GATE_LANDING))
	return throat in worker.route

func worker_cross(gate, departure: float, loaded: bool) -> void:
	var start: Vector3 = gate.to_global(Vector3(0.,0.,departure*3.02))
	var end: Vector3 = gate.to_global(Vector3(0.,0.,-departure*3.02))
	var label := "%s %s %s" % [gate.gate_id,"inbound" if departure > 0. else "outbound","loaded worker" if loaded else "empty worker"]
	worker.actor.global_position = start
	var selected := send_to(gate,end)
	var book: Dictionary = game.inventory.settlement.worker_load.duplicate()
	var ticks := 0
	for i in 450:
		game.step_technical_gates(STEP)
		ticks = i+1
		if worker._walk_route(STEP,false): break
	var depth: float = gate.to_local(worker.actor.global_position).z
	var reached: bool = selected and depth*departure < -2.80
	check(reached and game.inventory.settlement.worker_load == book,label)
	transits.append({"test":label,"routed_by_gate":selected,"reached":reached,"ticks":ticks,"gate_local_finish":str(gate.to_local(worker.actor.global_position)),"cargo":book})

func opposing_cross(gate, worker_side: float) -> void:
	var worker_start: Vector3 = gate.to_global(Vector3(0.,0.,worker_side*.88))
	var destination: Vector3 = gate.to_global(Vector3(0.,0.,-worker_side*2.82))
	worker.actor.global_position = worker_start
	worker.travel_speed = 0.0
	worker.route.assign([destination])
	var none: Array[Vector4] = []
	for i in 120: gate.advance_automatic(STEP,FAR,.31,Vector3.INF,none)
	place_player(gate.to_global(Vector3(0.,0.,-worker_side*.87)))
	var forward: Vector3 = gate.global_basis.z*worker_side
	var right: Vector3 = game.camera.global_basis.x
	var input := Vector2(forward.dot(right),forward.dot(right.cross(Vector3.UP))).normalized()
	game.actor.rotation.y = atan2(forward.x,forward.z)
	var min_separation := INF
	var yielded := false
	var player_clear := false
	var reached := false
	var conservation: Dictionary = game.inventory.settlement.worker_load.duplicate()
	var ticks := 0
	for i in 410:
		await physics_frame
		game.previous_dry_position = game.actor.global_position
		if not player_clear: game.move_actor(input,STEP)
		game.step_technical_gates(STEP)
		reached = worker._walk_route(STEP,false)
		var worker_local: Vector3 = gate.to_local(worker.actor.global_position)
		var player_local: Vector3 = gate.to_local(game.actor.global_position)
		yielded = yielded or worker_side*worker_local.z > 1.75
		if not player_clear:
			min_separation = minf(min_separation,game.actor.global_position.distance_to(worker.actor.global_position))
			if player_local.z*worker_side > 2.80:
				player_clear = true
				place_player(FAR)
		ticks = i+1
		if player_clear and reached: break
	var label := "%s opposing loaded worker from %s" % [gate.gate_id,"outside" if worker_side > 0. else "inside"]
	check(yielded and player_clear and reached and min_separation > .55 and conservation == game.inventory.settlement.worker_load,label)
	transits.append({"test":label,"player_clear":player_clear,"worker_clear":reached,"worker_yielded":yielded,"min_spacing_m":min_separation,"ticks":ticks,"cargo":conservation})

func load_worker() -> void:
	for material in ["wood","stone","meat"]:
		for i in 6: game.inventory.collect("gate-worker-%s-%d" % [material,i],material)
		game.inventory.carried[material] -= 6
		game.inventory.settlement.worker_load[material] = 6
	worker._sync_pack()

func reopen_wall_positions() -> void:
	var court: Vector4 = game.field_env.COURTS[2]
	var prior_clearance := .56
	var sides := [Vector3(-5.8,0,court.w),Vector3(court.z,0,-4.8),Vector3(court.x,0,-2.8),Vector3(-6.8,0,court.y)]
	var directions := [Vector3.BACK,Vector3.RIGHT,Vector3.LEFT,Vector3.FORWARD]
	for i in sides.size():
		for side in [-1.,1.]:
			var legacy: Vector3 = sides[i] + directions[i]*prior_clearance*side
			game.lifecycle._restore_actor({"x":legacy.x,"z":legacy.z,"hp":17})
			var restored: Vector3 = game.actor.global_position
			check(game.field_env.travel_clear(restored,restored,float(game.layout.actor_radius)) and game.field_env.is_inside_camp(restored) == (side < 0.) and game.player_hp == 17,
				"legacy save beside wall %d recovers to its own side %s" % [i,side])

func run() -> void:
	game = load("res://field_opening.tscn").instantiate()
	root.add_child(game)
	for i in 6: await physics_frame
	game.set_physics_process(false)
	game.carry.set_physics_process(false)
	worker = game.survivor
	setup_camp()
	for wolf in game.enemies.duplicate(): game.encounters._remove(wolf)
	place_player(FAR)
	for loaded in [false,true]:
		if loaded: load_worker()
		for gate in game.gates:
			for side in [1.,-1.]: await worker_cross(gate,side,loaded)
	for gate in game.gates:
		for side in [1.,-1.]: await opposing_cross(gate,side)
	reopen_wall_positions()
	var recovered = game.Inventory.new()
	check(recovered.configure(game.inventory.configured_costs) and recovered.restore(game.inventory.snapshot()),"congestion preserves the live mixed cargo ledger")
	print("CAMP_GATE_ROUTES ",JSON.stringify({"checks":checks,"errors":errors,"transits":transits}))
	await Session.drain_field_audio(self,game)
	game.queue_free()
	for i in 4: await process_frame
	quit(int(not errors.is_empty()))
