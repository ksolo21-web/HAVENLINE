extends "res://tests/test_integrated_opening.gd"
## Exercise the integrated opening's ordinary physical movement and F input; no saves.

func approach_tree() -> void:
	check(await travel(game.point([-.35, 6.0])), "walk to the east side of the starter tree")
	check(await travel(game.point([-.85, 6.0])), "face west close enough to chop")
	check(game.resource_tree.can_address(game.actor.global_position, game.tree_facing()), "tree accepts ordinary input")

func fall_and_regrow(expected_wood: int) -> void:
	var tree = game.resource_tree
	var pivot := tree.get_child(0) as Node3D
	var start_wood := int(game.ledger.stock.wood)
	for strike in 2:
		press(KEY_F)
		await tick(21)
		check(tree.strikes == strike + 1 and tree.phase == "rooted" and pivot.is_visible_in_tree() and game.ledger.stock.wood == start_wood, "early chop keeps the standing tree and awards no wood: %d" % (strike + 1))
	press(KEY_F)
	await tick(21)
	check(tree.strikes == 3 and tree.phase == "falling" and tree.blocked and pivot.is_visible_in_tree() and game.ledger.stock.wood == start_wood, "last chop starts fall but waits for the player to move clear")
	check(await travel(game.point([.0, 6.0])), "move clear using ordinary input")
	for i in 65:
		if tree.phase == "credited":
			break
		await tick(1)
	check(tree.phase == "credited" and not pivot.is_visible_in_tree() and not game.tree_button.is_visible_in_tree(), "settled tree and chop prompt disappear")
	check(game.ledger.stock.wood == expected_wood and game.ledger.collected == ["wood-a"], "preserve exact one-time starter reward")
	check(not tree.can_address(tree.global_position + Vector3.RIGHT, Vector3.LEFT), "the missing tree cannot be addressed even at legal chop distance")
	var completed_at := tick_count
	press(KEY_F)
	await tick(299)
	check(tree.phase == "credited" and tree.strikes == 3 and not pivot.is_visible_in_tree() and game.ledger.stock.wood == expected_wood, "still absent just before five seconds; chop input cannot reset the clock")
	game.sync_progress_visuals()
	await tick(1)
	check(tick_count - completed_at == 300 and tree.phase == "rooted" and tree.strikes == 0 and pivot.is_visible_in_tree() and pivot.basis.is_equal_approx(Basis.IDENTITY), "tree regrows upright at five seconds / 300 physics ticks")
	game.sync_progress_visuals()
	check(tree.phase == "rooted" and pivot.is_visible_in_tree(), "published ledger sync cannot re-hide a regrown tree")
	for mark in tree._marks:
		check(not mark.visible, "old chop mark is cleared")
	check(game.ledger.stock.wood == expected_wood and game.ledger.collected == ["wood-a"], "regrowth does not grant loot")

func run() -> void:
	game = GAME.instantiate()
	root.add_child(game)
	if not game.bound or game.persist_requested:
		check(false, "integrated preview binds without a save")
		quit(1)
		return
	await tick(10)
	check(game.resource_tree.find_children("*", "CollisionObject3D", true, false).is_empty(), "starter pine has no physical collider before or after regrowth")
	await approach_tree()
	await fall_and_regrow(1)
	await approach_tree()
	await fall_and_regrow(1)
	check(game.ledger.receipt.is_empty() and not game.camp_built.visible, "repeat tree cuts cannot pay for the camp")
	print("integrated tree-regrowth checks=", checks, " failures=", failures)
	quit(1 if failures else 0)
