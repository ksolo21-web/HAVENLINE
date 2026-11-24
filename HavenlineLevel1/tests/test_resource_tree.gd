extends SceneTree
const Scene = preload("res://opening.tscn")
const ResourceTreeScript = preload("res://resource_tree.gd")
var failures := 0

func check(ok: bool, desc: String) -> void:
	if not ok:
		failures += 1
		push_error(desc)

func _initialize() -> void:
	if not OS.get_cmdline_user_args().is_empty():
		push_error("Tree fixture is memory-only; do not supply save flags")
		quit(2)
		return
	call_deferred("run")

func run() -> void:
	var game = Scene.instantiate()
	root.add_child(game)
	game.set_physics_process(false)
	var tree: ResourceTreeScript = game.resource_tree
	var safe := Vector3(-.52, 0, 6)
	var unsafe := Vector3(-3, 0, 5.68)
	check(tree.phase == "rooted" and game.ledger.stock.wood == 0, "baseline no reward")
	check(not tree.strike("wood-b", 1, safe, Vector3.LEFT), "wrong addressed source")
	check(not tree.strike("wood-a", 1, safe, Vector3.RIGHT), "wrong facing")
	check(not tree.strike("wood-a", 2, Vector3(1, 0, 6), Vector3.LEFT), "out of reach")
	check(tree.strike("wood-a", 3, safe, Vector3.LEFT), "first deliberate contact")
	check(not tree.strike("wood-a", 3, safe, Vector3.LEFT), "duplicate input")
	check(not tree.strike("wood-a", 4, safe, Vector3.LEFT), "cooldown blocks duplicate contacts")
	check(tree.strikes == 1 and tree.phase == "rooted" and game.ledger.stock.wood == 0, "one notch no wood")
	for tick in 24:
		tree.advance(1.0 / 60.0, safe, .31)
	check(tree.strike("wood-a", 5, safe, Vector3.LEFT), "second deliberate contact")
	check(tree.strikes == 2 and tree.phase == "rooted" and game.ledger.stock.wood == 0, "two notches no wood")
	for tick in 24:
		tree.advance(1.0 / 60.0, safe, .31)
	check(tree.strike("wood-a", 6, safe, Vector3.LEFT), "third accepted intent")
	tree.advance(.02, unsafe, .31)
	check(tree.blocked and is_zero_approx(tree.falling_clock) and game.ledger.stock.wood == 0, "occupied sweep cannot advance")
	game.actor.position = safe
	game.step_tree(.02)
	check(tree.phase == "falling" and (tree.get_child(0) as Node3D).basis != Basis.IDENTITY and game.ledger.stock.wood == 0, "model rotates before credit")
	for tick in 72:
		game.step_tree(1.0 / 60.0)
	check(tree.phase == "credited" and game.ledger.stock.wood == 1 and game.ledger.collected == ["wood-a"], "settled actual ledger credit")
	check(game.actor.position.is_equal_approx(safe), "tree didn't move actor")
	check(not tree.strike("wood-a", 7, safe, Vector3.LEFT), "no post-fall input")
	for tick in 30:
		game.step_tree(1.0 / 60.0)
	check(game.ledger.stock.wood == 1, "no repeat credit")
	var second = Scene.instantiate()
	root.add_child(second)
	second.set_physics_process(false)
	check(second.ledger.restore(game.ledger.snapshot()), "existing ledger can restore the collected ID")
	second.sync_progress_visuals()
	check(second.resource_tree.phase == "credited", "restore derives landed look, no new reward")
	second.actor.position = safe
	second.step_tree(.02)
	check(second.ledger.stock.wood == 1 and second.resource_tree.strikes == 3, "restore synchronization does not regrant")
	print("Resources tree fixture failures: ", failures)
	quit(0 if failures == 0 else 1)
