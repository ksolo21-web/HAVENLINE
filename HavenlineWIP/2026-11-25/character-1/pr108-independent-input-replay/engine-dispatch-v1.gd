extends SceneTree
const LEVEL = preload("res://previews/integrated_opening.tscn")
const POINTER := Vector2(450, 375)
var game
var failures := 0
var finger := 30

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
	Input.parse_input_event(ev)

func tap_at(down: bool) -> void:
	var ev := InputEventScreenTouch.new()
	ev.device = 1
	ev.index = finger
	ev.position = POINTER
	ev.pressed = down
	Input.parse_input_event(ev)

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
		Input.parse_input_event(ev)
		await ticks(1)
	tap_at(false)
	await ticks(3)
	return game.bound and game.actor.is_on_floor() and pl(game.actor.position).distance_to(pl(target)) < .06

func require(ok: bool, label: String) -> bool:
	record(label, "observed" if ok else "unavailable", ok)
	if not ok:
		print("BLOCKED: downstream observations not attempted")
		quit(3)
	return ok

func run() -> void:
	game = LEVEL.instantiate()
	root.add_child(game)
	await ticks(10)
	if not require(game.bound and not game.persist_requested and is_instance_valid(game.resource_rock), "exact integrated rock and disposable runtime"):
		return
	if not require(await walk([-3.0, 7.0]) and await walk([2.0, 7.0]) and game.ledger.stock.wood == 2, "ordinary loose wood"):
		return
	if not require(await walk([-.35, 6.0]) and await walk([-.85, 6.0]) and game._tree_is_target(), "ordinary west-facing tree approach"):
		return
	for _i in range(3):
		await press(KEY_F)
		await ticks(21)
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
	print("OBSERVATION through-wall rock address predicate=", game._rock_is_target())
	var count_was: int = rock.strikes
	var paid: Dictionary = game.ledger.snapshot()
	await press(KEY_F)
	record("no mining through solid camp wall", "strike %d → %d; wall hit yes" % [count_was, rock.strikes], rock.strikes == count_was)
	if not require(await walk([0.0, 2.0]), "ordinary south gate approach"):
		return
	await press(KEY_E)
	await ticks(70)
	if not require(await walk([0.0, 5.3]) and await walk([-6.0, 5.3]) and await walk([-6.0, 4.1]) and game._rock_is_target() and not game._tree_is_target(), "dry outside route and legal facing"):
		return
	count_was = rock.strikes
	finger += 1
	tap_at(true)
	await ticks(3)
	tap_at(false)
	await ticks(3)
	record("ordinary default touch at legal stone approach", "strike %d → %d; no dedicated mining prompt in pinned source" % [count_was, rock.strikes], rock.strikes > count_was)
	while rock.strikes < 3:
		count_was = rock.strikes
		await press(KEY_F)
		await ticks(23)
		if rock.strikes <= count_was:
			record("legal outside F advances rock", "stalled at %d; downstream award unobservable" % rock.strikes, false)
			quit(3)
			return
	record("three hit native rock completion", "phase=%s tally=%d" % [rock.phase, rock.strikes], rock.phase == "mined" and rock.strikes == 3)
	record("typed stone award", "snapshot typed keys=%s stock=%s" % [str(game.ledger.stock.keys()), str(game.ledger.stock)], int(game.ledger.stock.get("stone", 0)) > 0)
	record("no wood side effect or paid receipt mutation", "wood=%s" % str(game.ledger.stock.wood), paid.stock.wood == game.ledger.stock.wood and paid.receipt == game.ledger.receipt)
	quit(0 if failures == 0 else 1)
