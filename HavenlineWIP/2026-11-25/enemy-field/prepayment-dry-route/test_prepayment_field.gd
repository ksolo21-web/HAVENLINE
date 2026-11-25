extends "res://tests/test_integrated_opening.gd"
## Only pre-payment locomotion on the unmodified integrated preview, no encounter.
const FieldDry = preload("res://previews/fixture_dry_shore_sweep.gd")
const START := [0.0, 6.0]
const TURN_A := [1.35, 8.15]
const FIELD := [3.00, 9.60]
const TURN_B := [0.70, 9.75]

var measure := false
var observed := 0
var grounded_dry := 0
var unchanged := 0
var inactive := 0
var min_wood_c := INF
var min_shore := INF
var initial_ledger: PackedByteArray

func still_unpaid() -> bool:
	if game.camp_built.visible or game.gates.size() != 2:
		return false
	for gate in game.gates:
		if gate.active or gate.target_open or absf(gate.angle) > .002:
			return false
	return game.ledger.receipt.is_empty() and not game.persist_requested

func tick(n: int) -> void:
	for i in range(n):
		await super.tick(1)
		if not measure:
			continue
		var pos: Vector3 = game.actor.position
		var at := Vector2(pos.x, pos.z)
		var sample := Terrain.sample(at)
		observed += 1
		if bool(sample.valid) and not bool(sample.crossing_reserved) and game.actor.is_on_floor() and FieldDry.dry_footprint(at, float(game.layout.actor_radius), game.bank_side, FieldDry.SWEEP_PAD):
			grounded_dry += 1
			min_shore = minf(min_shore, float(sample.shore_distance))
		if var_to_bytes(game.ledger.snapshot()) == initial_ledger and game.wood_visuals["wood-b"].is_visible_in_tree() and game.wood_visuals["wood-c"].is_visible_in_tree():
			unchanged += 1
		if still_unpaid():
			inactive += 1
		var wood_c: Vector3 = game.wood_anchors["wood-c"]
		min_wood_c = minf(min_wood_c, pos.distance_to(wood_c))

func route_point(mark: Array, label: String) -> void:
	var goal: Vector3 = game.point(mark)
	check(goal.is_finite() and await travel(goal), label + ": reached through ordinary touch-handler motion")
	var pos: Vector3 = game.actor.position
	check(pos.distance_to(goal) < .08 and game.actor.is_on_floor(), label + ": grounded within measured endpoint tolerance")
	print("PREPAY_POINT ", JSON.stringify({"point":label,"x":pos.x,"y":pos.y,"z":pos.z,"gap_m":pos.distance_to(goal)}))

func run() -> void:
	game = GAME.instantiate()
	root.add_child(game)
	check(game.bound, "exact default integrated scene binds")
	if not game.bound:
		quit(1)
		return
	await tick(10)
	var start: Vector3 = game.actor.position
	check(start.distance_to(game.point(START)) < .08 and game.actor.is_on_floor(), "actual authored fresh spawn; no position setter")
	check(still_unpaid(), "fresh camp hidden, both mechanisms inactive and no payment or persistence")
	check(game.ledger.stock.wood == 0 and game.ledger.collected.is_empty(), "fresh source owns no starter wood")
	check(game.wood_visuals["wood-b"].is_visible_in_tree() and game.wood_visuals["wood-c"].is_visible_in_tree(), "both ordinary loose sources initially visible")
	check(game.resource_tree.phase == "rooted", "original tree standing before ordinary travel")
	initial_ledger = var_to_bytes(game.ledger.snapshot())
	measure = true
	await route_point(TURN_A, "outward dry apron turn")
	await route_point(FIELD, "dry field sample")
	var first_direction: Vector3 = game.tree_facing()
	var at_field: Vector3 = game.actor.position
	await tick(26)
	check(at_field.distance_to(game.actor.position) < .02 and game.actor.is_on_floor(), "stopped field dwell")
	await route_point(TURN_B, "ordinary turn toward return")
	var new_direction: Vector3 = game.tree_facing()
	check(first_direction.dot(new_direction) < .50, "observed native heading changed across turn")
	await route_point(START, "return to original unpaid spawn")
	check(observed >= 100 and grounded_dry == observed, "every sampled tick dry grounded outside crossing reservation")
	check(observed == unchanged and observed == inactive, "every sampled tick preserved absolute prepayment and ledger state")
	check(min_wood_c > .68 and game.resource_tree.phase == "rooted", "never entered loose wood-c reach and no tree action")
	print("PREPAY_RESULT ", JSON.stringify({"checks":checks,"failed":failures,"observed":observed,"grounded_dry":grounded_dry,"ledger_unchanged":unchanged,"camp_inactive":inactive,"min_wood_c_m":min_wood_c,"min_shore_m":min_shore}))
	quit(0 if failures == 0 else 1)
