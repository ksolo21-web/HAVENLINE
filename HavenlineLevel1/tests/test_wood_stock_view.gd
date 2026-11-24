extends SceneTree
const Opening = preload("res://opening.tscn")
const SAFE := Vector3(-.52, 0, 6)
var checks := 0
var failures := 0

class DenyingSave:
	func commit(_candidate: RefCounted) -> Error:
		return ERR_CANT_CREATE

func _initialize() -> void:
	if not OS.get_cmdline_user_args().is_empty():
		push_error("Run wood stock fixture without save flags")
		quit(2)
		return
	call_deferred("run")

func check(ok: bool, description: String) -> void:
	checks += 1
	if not ok:
		failures += 1
		push_error(description)

func fresh():
	var game = Opening.instantiate()
	root.add_child(game)
	game.set_physics_process(false)
	return game

func readout(game, amount: int) -> bool:
	var view = game.wood_stock_view
	return view.presented_units == amount and view.counter.visible == (amount > 0) and view.counter.text == ("WOOD x%d [DEV]" % amount) and is_instance_valid(view.payload) and view.payload.visible == (amount > 0)

func run() -> void:
	var game = fresh()
	var view = game.wood_stock_view
	check(readout(game, 0), "fresh zero hides count and actual payload")
	check(view.get_parent() == game.actor and view.find_children("*", "CollisionObject3D", true, false).is_empty(), "noncolliding actor-relative mount")
	var box: AABB = view.fitted_bounds
	var hero: AABB = view.measured_actor
	check(is_equal_approx(hero.size.y, 1.75) and box.end.z <= hero.position.z - .0249 and box.size.x <= .4001 and box.size.y <= .2201 and box.size.z <= .2401, "normalized exact C1 and conservative rear bounds")
	var instance_before: Node3D = view.payload
	game.actor.position = SAFE
	for seq in range(1,4):
		check(game.resource_tree.strike("wood-a", seq, SAFE, Vector3.LEFT), "source strike accepted")
		if seq < 3:
			for tick in 10:
				game.step_tree(.04)
			check(readout(game, 0), "notches award no onscreen wood")
	for tick in 60:
		if game.resource_tree.falling_clock >= .72:
			break
		game.step_tree(.04)
	check(game.resource_tree.falling_clock >= .72 and is_zero_approx(game.resource_tree.settle_clock) and readout(game, 0), "terminal pose alone remains zero")
	for tick in 15:
		game.step_tree(.04)
	check(readout(game, 1), "settled committed tree shows 1")
	game._collect_wood_source("wood-b")
	check(readout(game, 2), "next pickup shows 2")
	game._collect_wood_source("wood-c")
	check(readout(game, 3) and instance_before == view.payload, "third pickup shows 3 with one reused payload")
	var denied = fresh()
	check(denied.ledger.restore(game.ledger.snapshot()), "restore before pay")
	denied.sync_progress_visuals()
	check(readout(denied, 3), "restored unpaid stock shows 3")
	denied.persist_requested = true
	denied.save = DenyingSave.new()
	denied.actor.position = denied.point(denied.layout.pad_xz)
	game.actor.position = game.point(game.layout.pad_xz)
	check(not denied.fund_opening_receiver("center-hearth", "wood") and denied.persist_blocked and readout(denied, 3) and denied.ledger.receipt.is_empty(), "failed save retains preceding published readout")
	check(game.fund_opening_receiver("center-hearth", "wood") and readout(game, 0), "published spend hides at zero")
	check(game.ledger.collected.size() == 3 and not game.ledger.receipt.is_empty(), "collected IDs are not the stock count")
	var paid = fresh()
	check(paid.ledger.restore(game.ledger.snapshot()), "restore paid fixture")
	paid.sync_progress_visuals()
	check(readout(paid, 0) and paid.camp_built.visible and not paid.purchase_pad_view.scene_view.visible, "restored paid stock is hidden and camp/pad unchanged")
	print("Wood stock view checks: ", checks, ", failures: ", failures)
	quit(0 if failures == 0 else 1)
