extends SceneTree
# Deliberate engine stepping, not ordinary input or device timing.
const Opening = preload("res://opening.tscn")
const ResourceTreeScript = preload("res://resource_tree.gd")
const SAFE := Vector3(-.52, 0, 6)
const OCCUPIED := Vector3(-3, 0, 5.68)
var failures := 0
var checks := 0

func _initialize() -> void:
	if not OS.get_cmdline_user_args().is_empty():
		push_error("Dwell fixture must not receive any save flags")
		quit(2)
		return
	call_deferred("run")

func check(ok: bool, label: String) -> void:
	checks += 1
	if not ok:
		failures += 1
		push_error(label)

func timing(label: String, deltas: Array, with_hold: bool) -> void:
	var game = Opening.instantiate()
	root.add_child(game)
	game.set_physics_process(false)
	game.actor.position = SAFE
	var tree: ResourceTreeScript = game.resource_tree
	for seq in range(1, 4):
		check(tree.strike("wood-a", seq, SAFE, Vector3.LEFT), label + ": deliberate accepted strike")
		if seq < 3:
			for i in 10:
				tree.advance(.04, SAFE, .31)
			check(game.ledger.stock.wood == 0, label + ": contact does not award")
	var first_terminal := -1
	var first_credit := -1
	var steps_after_terminal := 0
	var eligible := 0.0
	var ideal_basis := Basis(Vector3.UP.cross(ResourceTreeScript.FALL_DIR).normalized(), ResourceTreeScript.FALL_MAX)
	var actual_pivot := tree.get_child(0) as Node3D
	for tick in 200:
		var dt := float(deltas[tick % deltas.size()])
		var clamped := clampf(dt, 0.0, .04)
		game.step_tree(dt)
		if first_terminal < 0 and tree.falling_clock == ResourceTreeScript.FALL_SECONDS:
			first_terminal = tick
			check(actual_pivot.basis.is_equal_approx(ideal_basis), label + ": exact terminal shape")
			check(is_zero_approx(tree.settle_clock) and tree.phase == "falling" and game.ledger.stock.wood == 0, label + ": no dwell or credit on first terminal pose")
			if with_hold:
				game.actor.position = OCCUPIED
				for i in 6:
					game.step_tree(.09)
				check(tree.blocked and is_zero_approx(tree.settle_clock) and tree.phase == "falling" and game.ledger.stock.wood == 0, label + ": occupied dwell remains paused")
				check(game.actor.position == OCCUPIED and actual_pivot.basis.is_equal_approx(ideal_basis), label + ": occupancy does not move actor or departed pose")
				game.actor.position = SAFE
			game.step_tree(0.0)
			game.step_tree(-.04)
			check(is_zero_approx(tree.settle_clock) and game.ledger.stock.wood == 0, label + ": nonpositive steps make no progress")
		elif first_terminal >= 0:
			var before := eligible
			eligible += clamped
			steps_after_terminal += 1
			if game.ledger.stock.wood == 1:
				first_credit = tick
				check(eligible >= ResourceTreeScript.SETTLE_SECONDS, label + ": enough stationary time before credit")
				check(before < ResourceTreeScript.SETTLE_SECONDS, label + ": no extra eligible step after minimum")
				break
			check(eligible < ResourceTreeScript.SETTLE_SECONDS and tree.phase == "falling" and game.ledger.stock.wood == 0, label + ": incomplete dwell remains unpaid")
		else:
			check(game.ledger.stock.wood == 0, label + ": moving tree remains unpaid")
	check(first_terminal >= 0 and first_credit > first_terminal and tree.phase == "credited", label + ": completed after an observed terminal pose")
	check(game.ledger.collected == ["wood-a"] and game.actor.position == SAFE, label + ": stable one wood, no actor move")
	for i in 15:
		game.step_tree(.04)
	check(game.ledger.stock.wood == 1 and game.ledger.collected == ["wood-a"], label + ": no duplicate")
	print(label, " pose tick=", first_terminal, " credit tick=", first_credit, " eligible=", eligible, " steps=", steps_after_terminal)
	game.free()

func run() -> void:
	timing("60Hz", [1.0 / 60.0], false)
	timing("capped positive dt with blocked dwell", [.08], true)
	timing("mixed cadence", [.03, .011, .048, .017, 0.0], false)
	print("Stationary dwell fixture checks: ", checks, ", failures: ", failures)
	quit(0 if failures == 0 else 1)
