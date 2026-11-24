extends "res://tests/test_integrated_opening.gd"
## Manual-fishing accessibility only. No fishing interaction, stock, recipe,
## new anchor in gameplay, movement change, default boot or persistence.
const AcceptedRiver = preload("res://river_geometry.gd")
const Sweep = preload("res://previews/fixture_dry_shore_sweep.gd")
# Accepted-terrain frame coordinates from the prior provisional screening.
const BANK_ANCHOR := Vector2(4.8, -2.9553380834572076)
const BANK_CORRIDOR_TURN := Vector2(4.8, 5.8)
const OUTSIDE_EAST := Vector2(3.55, 5.8)
const INSIDE_EAST := Vector2(-.45, 5.8)
const SAMPLE_CONTACT_EPS := .10
var route_ticks := 0
var route_floor_ticks := 0
var route_dry_ticks := 0
var max_support_error := 0.0
var minimum_shore_distance := INF

func floor_point(xz: Vector2) -> Vector3:
	var sample := Terrain.sample(xz)
	if not sample.get("valid", false):
		return Vector3(INF, INF, INF)
	return Vector3(xz.x, float(sample.height), xz.y)

func observe_route_step() -> void:
	var foot: Vector3 = game.actor.position
	var xz := Vector2(foot.x, foot.z)
	var sampled := Terrain.sample(xz)
	route_ticks += 1
	if not sampled.get("valid", false):
		return
	minimum_shore_distance = minf(minimum_shore_distance, float(sampled.shore_distance))
	if game.actor.is_on_floor():
		route_floor_ticks += 1
		max_support_error = maxf(max_support_error, absf(foot.y - float(sampled.height)))
	if Sweep.dry_footprint(xz, float(game.layout.actor_radius), game.bank_side) and not bool(sampled.crossing_reserved):
		route_dry_ticks += 1

func reach_segment(target: Vector2, title: String, limit := 210) -> bool:
	gesture += 1
	send_touch(true)
	var advance_moves := 0
	for i in range(limit):
		var previous: Vector3 = game.actor.position
		var delta := target - Vector2(previous.x, previous.z)
		if delta.length() < .025 or not game.bound:
			break
		var locally := Vector3(delta.x, 0, delta.y).rotated(Vector3.UP, -atan2(7.0, 11.0))
		var ev := InputEventScreenDrag.new()
		ev.index = gesture
		ev.position = CENTER + (Vector2(locally.x, locally.z) * 15.0).limit_length() * 82.0
		game._input(ev)
		await tick(1)
		observe_route_step()
		if game.actor.position.distance_to(previous) > .005:
			advance_moves += 1
	send_touch(false)
	await tick(3)
	var observed: Vector3 = game.actor.position
	var remaining := target.distance_to(Vector2(observed.x, observed.z))
	print("shore_route ", JSON.stringify({"label":title,"requested_x":target.x,"requested_z":target.y,"observed_x":observed.x,"observed_y":observed.y,"observed_z":observed.z,"remaining_m":remaining,"actual_movement_frames":advance_moves}))
	return game.bound and advance_moves >= 3 and remaining < .05

func earn_camp() -> void:
	check(await travel(game.wood_anchors["wood-b"]), "first wood normal pickup approach")
	check(await travel(game.wood_anchors["wood-c"]), "second wood normal pickup approach")
	check(await travel(game.point([-.35, 6.0])), "normal tree approach")
	check(await travel(game.point([-.85, 6.0])), "orient to tree through normal input")
	for i in range(3):
		press(KEY_F)
		await tick(21)
	check(game.resource_tree.phase == "falling" and game.resource_tree.blocked, "tree waits for occupied sweep")
	check(await travel(game.point([0.0, 6.0])), "leave tree sweep normally")
	await tick(58)
	check(game.ledger.stock.wood == 3 and game.ledger.receipt.is_empty(), "normal input earns the exact three starter wood")
	check(await travel(game.pad_anchor), "normal input reaches real purchase pad")
	await tick(4)
	check(game.camp_built.visible and game.ledger.stock.wood == 0 and not game.ledger.receipt.is_empty(), "camp paid once before East route")

func run() -> void:
	game = GAME.instantiate()
	game.position = Vector3(2, 1.1, -3)
	root.add_child(game)
	if not game.bound:
		check(false, "exact accepted world binds")
		quit(1)
		return
	await tick(10)
	check(not game.persist_requested, "ordinary opt-in scene never saves")
	var anchor := floor_point(BANK_ANCHOR)
	var shore := Terrain.sample(BANK_ANCHOR)
	check(anchor.is_finite() and shore.valid and shore.dry and not shore.crossing_reserved and float(shore.bank_side) == game.bank_side, "provisional anchor uses accepted same-bank indexed height; outside crossing reservation")
	check(Sweep.dry_footprint(BANK_ANCHOR, float(game.layout.actor_radius), game.bank_side, Sweep.SWEEP_PAD) and float(shore.shore_distance) >= AcceptedRiver.DEFAULT_DRY_MARGIN, "standing footprint satisfies the existing swept dry authority")
	await earn_camp()
	if failures > 0:
		quit(1)
		return
	var stable_ledger := var_to_bytes(game.ledger.snapshot())
	var east = game.gates[1]
	check(east.gate_id == "gate-east" and east.active and not east.target_open and not game.gates[0].target_open, "use existing earned East, no South-route alias")
	check(await travel(game.point([2.0, 1.9])), "inside staging route avoids existing hearth")
	check(await reach_segment(INSIDE_EAST, "inside-east"), "go to actual inside gate staging point")
	var inside := east.to_local(game.actor.global_position) as Vector3
	check(game.nearest_gate == east and east.interaction_in_range(game.actor.global_position) and inside.z < -1.70, "inside aligned to actual gate frame, not floating anchor")
	press(KEY_E)
	await tick(70)
	check(east.target_open and absf(east.angle - PI * .5) < .002 and not game.gates[0].target_open, "normal East open, South remains closed")
	check(await reach_segment(OUTSIDE_EAST, "east-outward"), "physically cross existing East aperture outward")
	var outside := east.to_local(game.actor.global_position) as Vector3
	check(outside.z > 1.70 and absf(outside.x) < .10, "observed outside of actual East plane on centerline")
	check(await reach_segment(BANK_CORRIDOR_TURN, "out-to-turn"), "traverse vetted East corridor bend")
	check(await reach_segment(BANK_ANCHOR, "out-to-provisional-bank"), "normal grounded movement reaches provisional bank")
	await tick(12)
	var at_bank: Vector3 = game.actor.position
	check(game.actor.is_on_floor() and at_bank.distance_to(anchor) < .12, "provisional bank feet stay grounded on exact conformed anchor")
	check(await reach_segment(BANK_CORRIDOR_TURN, "back-to-turn"), "return through exact same-bank corridor")
	check(await reach_segment(OUTSIDE_EAST, "back-to-east-outside"), "arrive at same physical outside East apron")
	check(await reach_segment(INSIDE_EAST, "east-inward"), "physically return via existing East aperture")
	var inside_again := east.to_local(game.actor.global_position) as Vector3
	check(inside_again.z < -1.70 and absf(inside_again.x) < .10 and east.target_open and not game.gates[0].target_open, "returned to actual inside; South never used")
	check(route_ticks > 180 and route_floor_ticks >= int(float(route_ticks) * .95) and max_support_error <= SAMPLE_CONTACT_EPS, "actual route stays physically grounded on accepted terrain")
	check(route_ticks == route_dry_ticks and minimum_shore_distance >= AcceptedRiver.DEFAULT_DRY_MARGIN, "every observed sample same-bank dry; no crossing reservation")
	check(var_to_bytes(game.ledger.snapshot()) == stable_ledger, "out-and-back access grants no fishing stock or other second receipt")
	print("manual shore route checks=", checks, " failures=", failures, " ticks=", route_ticks, " grounded=", route_floor_ticks, " dry=", route_dry_ticks, " support_error=", max_support_error, " minimum_shore=", minimum_shore_distance)
	quit(1 if failures else 0)
