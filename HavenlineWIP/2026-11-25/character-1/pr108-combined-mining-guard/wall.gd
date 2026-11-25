extends SceneTree
const LEVEL = preload("res://previews/integrated_opening.tscn")
const POINTER := Vector2(450, 375)
var game
var failures := 0
var finger := 30
var baseline := false

func _initialize() -> void:
	call_deferred("run")

func record(label: String, observed: String, ok: bool) -> void:
	if not ok:
		failures += 1
	print("WITNESS ", label, " | ", observed, " | ", "PASS" if ok else "FAIL")

func ticks(n: int) -> void:
	for _i in range(n):
		await physics_frame

func button(key: Key, down: bool) -> void:
	var ev := InputEventKey.new()
	ev.physical_keycode = key
	ev.pressed = down
	game._input(ev)

func tap_at(down: bool) -> void:
	var ev := InputEventScreenTouch.new()
	ev.device = 1
	ev.index = finger
	ev.position = POINTER
	ev.pressed = down
	game._input(ev)

func press(key: Key) -> void:
	button(key, true)
	await ticks(2)
	button(key, false)
	await ticks(1)

func pl(pos: Vector3) -> Vector2:
	return Vector2(pos.x, pos.z)

func walk(xz: Array) -> bool:
	var target: Vector3 = game.point(xz)
	if not target.is_finite():
		return false
	finger += 1
	tap_at(true)
	for _i in range(240):
		var delta: Vector3 = target - game.actor.position
		delta.y = 0.0
		if delta.length() < 0.027 or not game.bound:
			break
		var local := delta.rotated(Vector3.UP, -atan2(7.0, 11.0))
		var ev := InputEventScreenDrag.new()
		ev.device = 1
		ev.index = finger
		ev.position = POINTER + (Vector2(local.x, local.z) * 15.0).limit_length() * 82.0
		game._input(ev)
		await ticks(1)
	tap_at(false)
	await ticks(3)
	return game.bound and game.actor.is_on_floor() and pl(game.actor.position).distance_to(pl(target)) < .06

func wait_ready(source) -> bool:
	for i in range(100):
		if game.character_kit.action_left <= 0.0 and source.cooldown <= 0.0:
			return true
		await physics_frame
	return false

func require(ok: bool, label: String) -> bool:
	record(label, "observed" if ok else "unavailable", ok)
	if not ok:
		print("BLOCKED: downstream observations not attempted")
		quit(3)
	return ok

func run() -> void:
	baseline = "baseline" in OS.get_cmdline_user_args()
	game = LEVEL.instantiate()
	root.add_child(game)
	await ticks(10)
	if not require(game.bound and not game.persist_requested and is_instance_valid(game.resource_rock), "exact integrated rock and disposable runtime"):
		return
	var got_b := await walk([-3.0, 7.0])
	print("OBSERVATION loose b reach=", got_b, " actor=", game.actor.position, " stock=", game.ledger.stock)
	var got_c := await walk([2.0, 7.0]) if got_b else false
	print("OBSERVATION loose c reach=", got_c, " actor=", game.actor.position, " stock=", game.ledger.stock)
	if not require(got_b and got_c and game.ledger.stock.wood == 2, "ordinary loose wood"):
		return
	if not require(await walk([-.35, 6.0]) and await walk([-.85, 6.0]) and game._tree_is_target(), "ordinary west-facing tree approach"):
		return
	for i in range(3):
		if not require(await wait_ready(game.resource_tree), "tree active/cooldown naturally elapsed"):
			return
		await press(KEY_F)
		if not require(game.resource_tree.strikes == i + 1, "legal tree F advances exactly once before camp"):
			return
	if not require(game.resource_tree.strikes == 3, "actual F accepted three wood actions"):
		return
	if not require(await walk([0.0, 6.0]), "clear falling tree sweep"):
		return
	await ticks(58)
	if not require(game.ledger.stock.wood == 3 and await walk([0.0, 2.4]) and not game.ledger.receipt.is_empty(), "physical pad charges three wood"):
		return
	if not require(await walk([-4.1, 3.0]) and await walk([-4.5, 3.0]), "inside western wall stop"):
		return
	var rock: Node3D = game.resource_rock
	var from: Vector3 = game.actor.global_position + Vector3.UP * 0.35
	var to := Vector3(rock.global_position.x, from.y, rock.global_position.z)
	var query := PhysicsRayQueryParameters3D.create(from, to, 1, [game.actor.get_rid()])
	var hit: Dictionary = game.actor.get_world_3d().direct_space_state.intersect_ray(query)
	if not require(hit.get("collider") in game.camp_colliders and not game._tree_is_target(), "solid western wall and source-facing candidate"):
		return
	var count_was: int = rock.strikes
	var sequence_was: int = game.rock_input_sequence
	var paid: Dictionary = game.ledger.snapshot()
	record("wall target selection", "target=%s; baseline=%s" % [game._rock_is_target(), baseline], game._rock_is_target() == baseline)
	await press(KEY_F)
	record("west-wall F", "strike %d → %d" % [count_was, rock.strikes], rock.strikes == count_was + (1 if baseline else 0))
	record("west-wall ledger unchanged", "wood=%s" % str(game.ledger.stock.wood), paid == game.ledger.snapshot())
	if not baseline:
		record("blocked mining input unconsumed", "sequence %s → %s" % [sequence_was, game.rock_input_sequence], game.rock_input_sequence == sequence_was)
	if not require(await walk([0.0, 2.0]), "ordinary south gate approach"):
		return
	await press(KEY_E)
	await ticks(70)
	if not require(await walk([0.0, 5.3]) and await walk([-6.0, 5.3]) and await walk([-6.0, 4.1]) and game._rock_is_target() and not game._tree_is_target(), "dry outside route and legal facing"):
		return
	var outdoor_y: float = game.actor.global_position.y + 0.35
	var outdoors_origin := Vector3(game.actor.global_position.x, outdoor_y, game.actor.global_position.z)
	var outdoors_target := Vector3(rock.global_position.x, outdoor_y, rock.global_position.z)
	var outdoors_ray := PhysicsRayQueryParameters3D.create(outdoors_origin, outdoors_target, 1, [game.actor.get_rid()])
	record("outside ray clear", "clear command path", game.actor.get_world_3d().direct_space_state.intersect_ray(outdoors_ray).is_empty())
	while rock.strikes < 3:
		if not require(await wait_ready(rock), "rock active/cooldown naturally elapsed"):
			return
		count_was = rock.strikes
		await press(KEY_F)
		if not require(rock.strikes == count_was + 1, "legal outdoor F advances exactly once"):
			return
	record("stone exhausted after three accepted hits", "phase=%s tally=%d" % [rock.phase, rock.strikes], rock.phase == "mined" and rock.strikes == 3)
	record("ledger unchanged since payment", "wood=%s" % str(game.ledger.stock.wood), paid == game.ledger.snapshot())
	quit(0 if failures == 0 else 1)
