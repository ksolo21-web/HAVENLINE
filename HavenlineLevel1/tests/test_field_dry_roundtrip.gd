extends "res://tests/test_integrated_opening.gd"
## Private route witness only; no entity, designated spawn, fishing or progress changes.
const RiverSource = preload("res://river_geometry.gd")
const FieldDry = preload("res://previews/fixture_dry_shore_sweep.gd")
const INSIDE = [0.0, 2.0]
const APRON = [0.0, 6.0]
const TURN_A = [1.35, 8.15]
const FIELD = [3.00, 9.60]
const TURN_B = [0.70, 9.75]

var observed := 0
var observed_safe := 0
var supported := 0
var minimum_shore := INF
var maximum_height_error := 0.0
var gate_hits := 0
var log_frames := false
var south_gate: Node3D

func tick(n: int) -> void:
	for i in range(n):
		await super.tick(1)
		if not log_frames:
			continue
		var p: Vector3 = game.actor.position
		var at := Vector2(p.x, p.z)
		var sample := Terrain.sample(at)
		observed += 1
		if bool(sample.valid) and FieldDry.dry_footprint(at, float(game.layout.actor_radius), game.bank_side, FieldDry.SWEEP_PAD) and not bool(sample.crossing_reserved):
			observed_safe += 1
			minimum_shore = minf(minimum_shore, float(sample.shore_distance))
		if bool(sample.valid) and game.actor.is_on_floor():
			supported += 1
			maximum_height_error = maxf(maximum_height_error, absf(p.y - float(sample.height)))
		for j in range(game.actor.get_slide_collision_count()):
			var hit_node = game.actor.get_slide_collision(j).get_collider()
			if hit_node is Node and is_instance_valid(south_gate) and south_gate.is_ancestor_of(hit_node):
				gate_hits += 1

func camp_pay() -> void:
	check(await travel(game.wood_anchors["wood-b"]), "earn wood-b at its exact normal source")
	check(await travel(game.wood_anchors["wood-c"]), "earn wood-c at its exact normal source")
	check(await travel(game.point([-.35, 6.0])), "approach standing tree")
	check(await travel(game.point([-.85, 6.0])), "orient west to standing tree via ordinary movement")
	for i in range(3):
		press(KEY_F)
		await tick(21)
	check(game.resource_tree.phase == "falling" and game.resource_tree.blocked, "occupied fall remains held")
	check(await travel(game.point(APRON)), "clear fall zone via native movement")
	await tick(58)
	check(int(game.ledger.stock.wood) == 3 and game.ledger.receipt.is_empty(), "normal first tree plus two pickups")
	check(await travel(game.pad_anchor), "normal pad approach")
	await tick(5)
	check(game.camp_built.visible and int(game.ledger.stock.wood) == 0 and not game.ledger.receipt.is_empty(), "ordinary paid camp reveals both original gates")

func route_point(mark: Array, title: String, end_tolerance := .08) -> void:
	var goal: Vector3 = game.point(mark)
	check(goal.is_finite() and await travel(goal), title + " through actual ordinary routed movement")
	var p: Vector3 = game.actor.position
	check(p.distance_to(goal) < end_tolerance and game.actor.is_on_floor(), title + " measured same terrain endpoint")
	print("FIELD_POINT ", JSON.stringify({"id":title,"x":p.x,"y":p.y,"z":p.z,"gap_m":p.distance_to(goal)}))

func run() -> void:
	game = GAME.instantiate()
	# Use exact scene default world transform, not an actor placement shortcut.
	root.add_child(game)
	if not game.bound:
		check(false, "existing accepted project failed to bind")
		quit(1)
		return
	await tick(10)
	check(not game.persist_requested and game.ledger.receipt.is_empty(), "fresh session, no persistence")
	await camp_pay()
	if failures > 0:
		quit(1)
		return
	var stable := var_to_bytes(game.ledger.snapshot())
	var gate = game.gates[0]
	south_gate = gate
	var east = game.gates[1]
	check(gate.gate_id=="gate-south" and gate.active and not gate.target_open and absf(gate.angle)<.002 and not east.target_open, "South settled closed; East closed")
	await route_point(INSIDE, "inside South staging")
	var inside: Vector3 = gate.to_local(game.actor.global_position)
	check(absf(inside.z)>1.7 and absf(inside.x)<.10, "inside true gate plane before controls")
	log_frames = true
	var reached_closed := await travel(game.point(APRON), 90)
	var obstructed: Vector3 = gate.to_local(game.actor.global_position)
	check(not reached_closed and obstructed.z * inside.z > 0.0 and gate_hits>0, "closed gate physically stopped native movement on inside")
	await route_point(INSIDE, "return away from closed sweep")
	check(game.nearest_gate == gate, "existing gate interaction selected normally")
	press(KEY_E)
	await tick(70)
	check(gate.target_open and absf(gate.angle-PI*.5)<.002 and not east.target_open, "South fully settled open following ordinary E")
	var contacts_before_open := gate_hits
	await route_point(APRON, "South outside apron")
	var outside: Vector3 = gate.to_local(game.actor.global_position)
	check(outside.z*inside.z<0.0 and absf(outside.z)>1.7 and absf(outside.x)<.10, "crossed South plane")
	await route_point(TURN_A, "off-shore outward diagonal")
	await route_point(FIELD, "new dry field turn")
	var before_dwell: Vector3 = game.actor.position
	await tick(26)
	check(game.actor.position.distance_to(before_dwell)<.02 and game.actor.is_on_floor(), "grounded break with no travel command")
	var first_direction: Vector3 = game.tree_facing()
	await route_point(TURN_B, "cross-field turn toward return leg")
	var second_direction: Vector3 = game.tree_facing()
	check(first_direction.dot(second_direction) < .50, "ordinary turn changed heading")
	await route_point(APRON, "return via same South apron")
	await route_point(INSIDE, "physically return via South opening")
	var returned: Vector3 = gate.to_local(game.actor.global_position)
	check(returned.z*inside.z>0.0 and absf(returned.z)>1.7 and gate_hits==contacts_before_open and not east.target_open, "open roundtrip really returned without any additional South leaf hit, East never used")
	press(KEY_E)
	await tick(70)
	check(not gate.target_open and absf(gate.angle)<.002, "same gate settles closed on return")
	log_frames = false

	var center_water := RiverSource.center_at_x(4.0)
	check(not FieldDry.dry_footprint(center_water,float(game.layout.actor_radius),game.bank_side,FieldDry.SWEEP_PAD), "existing dry predicate rejects actual channel center offline, never moves player there")
	var q := RiverSource.query(center_water)
	var side := float(game.bank_side)
	var edge_center: Vector2 = Vector2(q.center) + Vector2(q.north_normal) * side * (float(q.half_width) + RiverSource.DEFAULT_DRY_MARGIN + .045)
	var edge_sample := Terrain.sample(edge_center)
	check(bool(edge_sample.valid) and bool(edge_sample.dry) and not FieldDry.dry_footprint(edge_center,float(game.layout.actor_radius),side,FieldDry.SWEEP_PAD), "edge center is nominally dry but full actor footprint correctly rejected")
	check(observed >= 180 and observed_safe==observed and supported >= int(float(observed)*.95) and maximum_height_error<=.10, "every observed route sample dry off reservation and strong terrain support")
	check(stable == var_to_bytes(game.ledger.snapshot()), "no entity/loot/receipt/inventory side effect on field roundtrip")
	print("FIELD_RESULT ",JSON.stringify({"checks":checks,"failed":failures,"observed":observed,"safe":observed_safe,"grounded":supported,"min_shore":minimum_shore,"max_height_error":maximum_height_error,"intentional_closed_gate_hits":contacts_before_open}))
	quit(1 if failures else 0)
