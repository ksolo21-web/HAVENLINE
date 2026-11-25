extends SceneTree
## No physical input bypass: sampled feet advance via _physics_process, _input
## receives the same touch/drag and gate/chop key events as regular gameplay.
const GAME = preload("res://previews/integrated_opening.tscn")
const Terrain = preload("res://terrain_source.gd")
const CENTER := Vector2(450, 375)
var game
var failures := 0
var checks := 0
var gesture := 10
var tick_count := 0
var grounded := 0

func _initialize() -> void:
	call_deferred("run")

func check(ok: bool, label: String) -> void:
	checks += 1
	if not ok:
		failures += 1
	print("%s %s tick=%d" % ["PASS" if ok else "FAIL", label, tick_count])

func tick(n: int) -> void:
	for i in range(n):
		await physics_frame
		tick_count += 1
		if game.actor.is_on_floor():
			grounded += 1

func send_touch(down: bool) -> void:
	var tap := InputEventScreenTouch.new()
	tap.device = 1
	tap.position = CENTER
	tap.index = gesture
	tap.pressed = down
	game._input(tap)

func press(code: Key) -> void:
	var event := InputEventKey.new()
	event.physical_keycode = code
	event.pressed = true
	game._input(event)

func travel(to: Vector3, limit := 200) -> bool:
	gesture += 1
	send_touch(true)
	for i in range(limit):
		var delta: Vector3 = to - game.actor.position
		delta.y = 0.0
		if delta.length() < .02 or not game.bound:
			break
		var locally := delta.rotated(Vector3.UP, -atan2(7.0, 11.0))
		var ev := InputEventScreenDrag.new()
		ev.index = gesture
		ev.position = CENTER + (Vector2(locally.x, locally.z) * 15.0).limit_length() * 82.0
		game._input(ev)
		await tick(1)
	send_touch(false)
	await tick(3)
	var p: Vector3 = game.actor.position
	return game.bound and Vector2(p.x, p.z).distance_to(Vector2(to.x, to.z)) < .05

func gate_cross(gate, approach: Array, opposite: Array, label: String) -> void:
	check(await travel(game.point(approach)), "%s gate real approach" % label)
	check(game.nearest_gate == gate and gate.interaction_in_range(game.actor.global_position), "%s gate seated-range binding" % label)
	press(KEY_E)
	await tick(70)
	check(gate.target_open and absf(gate.angle - PI * .5) < .002, "%s gate opens once actor is clear" % label)
	check(await travel(game.point(opposite)), "%s gate physical outward traversal" % label)
	check(await travel(game.point(approach)), "%s gate physical return traversal" % label)

# Test-only north perimeter bridge. A .04m positive overlap at each seam
# preserves closure; not a production counter, placement or interaction.
func fixture_body(id: String, local_x: float, width: float) -> StaticBody3D:
	var body := StaticBody3D.new()
	body.name = id
	body.collision_layer = 1
	game.camp_built.add_child(body)
	body.position = game.point([local_x, -4.0], .475)
	var c := CollisionShape3D.new()
	var b := BoxShape3D.new()
	b.size = Vector3(width, .95, .30)
	c.shape = b
	body.add_child(c)
	return body

func install_fixture() -> bool:
	var original: StaticBody3D = null
	var hits := 0
	for body in game.camp_colliders:
		if body.position.is_equal_approx(game.point([0.0, -4.0], .475)):
			var c := body.get_child(1) as CollisionShape3D
			if c != null and c.shape is BoxShape3D and c.shape.size.is_equal_approx(Vector3(10, .95, .30)):
				original = body
				hits += 1
	if hits != 1 or original == null or original.collision_layer != 1:
		return false
	var preserved_left := fixture_body("FixtureNorthLeft", -3.4125, 3.175)
	var bridge := fixture_body("FixtureCounterBridge", 0.0, 3.73)
	var preserved_right := fixture_body("FixtureNorthRight", 3.4125, 3.175)
	for body in [preserved_left, bridge, preserved_right]:
		if not body.position.is_finite():
			return false
	var left_right: float = preserved_left.position.x + 3.175 * .5
	var right_left: float = preserved_right.position.x - 3.175 * .5
	if absf((left_right - (bridge.position.x - 3.73 * .5)) - .04) > .00001 or absf(((bridge.position.x + 3.73 * .5) - right_left) - .04) > .00001:
		return false
	game.camp_colliders.erase(original)
	game.camp_colliders.append_array([preserved_left, bridge, preserved_right])
	original.collision_layer = 0
	original.hide()
	original.queue_free()
	return true

func blocked_at(local_x: float, initial_z: float, opposite_z: float, label: String) -> void:
	var from_inside := initial_z > -4.0
	check(await travel(game.point([local_x, initial_z])), label + " ordinary approach")
	check(not await travel(game.point([local_x, opposite_z]), 75), label + " opposite side denied")
	var local_z: float = game.actor.position.z - 5.8
	var signed := (local_z + 4.0) * (1.0 if from_inside else -1.0)
	check(signed >= .43 and signed <= .52 and game.actor.is_on_floor(), label + " stays grounded at collision stop")

func run() -> void:
	game = GAME.instantiate()
	# Deliberate shifted scene world frame; terrain, props and actor translate together.
	game.position = Vector3(2.0, 1.1, -3.0)
	root.add_child(game)
	if not game.bound:
		check(false, "opening binds one exact dry terrain frame")
		quit(1)
		return
	await tick(10)
	check(not game.persist_requested and game.ledger.receipt.is_empty(), "only fresh ephemeral ledger")
	check(game.get_node_or_null("SnowGround_NoPaintedPaths") == null and game.ground.get_child_count() == 1, "one accepted ground and no flat layer")
	check(not game.camp_built.visible and game.camp_built.get_node("CampOnlySurface") is MeshInstance3D, "conformed receipt-only floor with no physical slab")
	var b: Vector3 = game.wood_anchors["wood-b"]
	var c: Vector3 = game.wood_anchors["wood-c"]
	var b_model: Node3D = game.wood_visuals["wood-b"]
	check(absf(b.y) > .04 and b_model.global_position.is_equal_approx(game.to_global(b)), "wood visual and stable nonzero terrain anchor share frame")
	check(absf(game.pad_anchor.y) > .04 and game.purchase_pad_view.global_position.is_equal_approx(game.to_global(game.pad_anchor)), "pad presentation and nonzero payment anchor share frame")
	check(await travel(game.point([-2.16, 7.0])), "walk using ordinary input to outside wood radius")
	check(game.ledger.stock.wood == 0 and game.wood_visuals["wood-b"].visible, "outside .68 does not credit")
	check(await travel(b), "walk to first elevated wood over physical terrain")
	check(game.ledger.stock.wood == 1 and game.ledger.collected == ["wood-b"] and not b_model.visible, "first pickup awards exactly once")
	await tick(7)
	check(game.ledger.stock.wood == 1, "standing on consumed wood never duplicates")
	check(await travel(c), "walk to second physical pickup")
	check(game.ledger.stock.wood == 2, "second distinct source exactly once")
	check(await travel(game.point([-.35, 6.0])), "approach east of tree")
	check(await travel(game.point([-.85, 6.0])), "face tree on westbound final approach")
	check(game.resource_tree.can_address(game.actor.global_position, game.tree_facing()), "real chop in range and facing")
	for i in range(3):
		press(KEY_F)
		await tick(21)
	check(game.resource_tree.phase == "falling" and game.resource_tree.blocked and game.ledger.stock.wood == 2, "occupied tree sweep blocks falling and credit")
	check(await travel(game.point([.0, 6.0])), "move clear of native tree sweep")
	await tick(58)
	check(game.ledger.stock.wood == 3 and game.resource_tree.phase == "credited", "normal chop gives third distinct resource")
	check(await travel(game.point([0.0, 3.30])), "walk outside elevated pad reach")
	check(game.ledger.stock.wood == 3 and game.ledger.receipt.is_empty() and not game.camp_built.visible, "outside .72 never pays, reveals or debits")
	game.purchase_pad_view.scene_view.hide()
	check(await travel(game.pad_anchor), "walk into disabled pad range")
	check(game.ledger.stock.wood == 3 and game.ledger.receipt.is_empty(), "inactive/hidden pad cannot debit even in range")
	game.purchase_pad_view.scene_view.show()
	await tick(3)
	check(game.ledger.stock.wood == 0 and not game.ledger.receipt.is_empty() and game.camp_built.visible, "same ordinary tick pays once from authorized seated pad")
	var paid := var_to_bytes(game.ledger.snapshot())
	await tick(10)
	check(paid == var_to_bytes(game.ledger.snapshot()), "standing on paid pad cannot pay again")
	var valid := install_fixture()
	check(valid, "exact north original exchanged for three touching bodies")
	if not valid:
		quit(1)
		return
	await tick(3)
	for gate in game.gates:
		for hinge_name in ["HingeLeft", "HingeRight"]:
			var h: Node3D = gate.get_node(hinge_name)
			var local: Vector3 = game.to_local(h.global_position)
			var sample := Terrain.sample(Vector2(local.x, local.z))
			check(sample.valid and absf(float(sample.height) - local.y) < .0001, "%s %s hinge seated on exact ground" % [gate.gate_id, hinge_name])
	await gate_cross(game.gates[0], [0.0, 2.0], [0.0, 6.0], "South")
	check(await travel(game.point([2.0, 1.9])), "inside cross-camp route east of hearth")
	await gate_cross(game.gates[1], [3.0, 0.0], [7.0, 0.0], "East")
	check(await travel(game.point([2.0, -2.30])), "east side approach around centered furnace")
	for x in [0.0, -1.825, 1.825]:
		await blocked_at(x, -2.65, -5.35, "inboard x=%.3f" % x)
	check(await travel(game.point([2.0, -2.30])), "return to inside apron")
	check(await travel(game.point([3.0, 0.0])), "existing open East approach")
	check(await travel(game.point([7.0, 0.0])), "exit through designated gate, not counter")
	check(await travel(game.point([7.0, -5.70])), "outside East to northern snow")
	check(await travel(game.point([2.0, -5.70])), "snow-side staging before counter")
	for x in [0.0, -1.825, 1.825]:
		await blocked_at(x, -5.45, -2.65, "outboard x=%.3f" % x)
	check(paid == var_to_bytes(game.ledger.snapshot()) and not game.persist_requested, "fixture does not change fresh opening receipt")
	check(grounded > 80, "actual CharacterBody floor contact across route")
	print("combined opening checks=", checks, " failures=", failures, " grounded=", grounded)
	quit(1 if failures else 0)
