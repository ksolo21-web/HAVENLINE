extends SceneTree
const LEVEL = preload("res://previews/integrated_opening.tscn")
const POINTER := Vector2(450, 375)
var game
var failures := 0
var finger := 30
var completed := 0
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

func require(ok: bool, label: String) -> bool:
	record(label, "observed" if ok else "unavailable", ok)
	if not ok:
		print("BLOCKED: downstream observations not attempted")
		quit(3)
	return ok

func observe(kind: String, source, player: AnimationPlayer, kit) -> Dictionary:
	return {
		"usec": Time.get_ticks_usec(), "strikes": source.strikes, "phase": source.phase,
		"cooldown": source.cooldown, "clip": String(player.current_animation),
		"position_s": player.current_animation_position if not player.current_animation.is_empty() else -1.0,
		"playing": player.is_playing(), "action": kit.action, "remaining_s": kit.action_left,
		"input_seq": game.tree_input_sequence if kind == "chop" else game.rock_input_sequence,
		"source_seq": source.last_sequence, "ledger": game.ledger.snapshot(),
	}

func inspect_action(kind: String, source) -> void:
	var kit = game.character_kit
	var player: AnimationPlayer = kit._player
	var clip := StringName("l1_actions/" + kind)
	if not require(kit.ready and player.has_animation(clip), "%s exact runtime clip bound" % kind):
		return
	var before := observe(kind, source, player, kit)
	button(KEY_F, true)
	var at_press := observe(kind, source, player, kit)
	button(KEY_F, false)
	if not require(before.remaining_s <= 0.0 and at_press.strikes == before.strikes + 1 and at_press.remaining_s > 0.0 and at_press.input_seq == before.input_seq + 1 and at_press.source_seq == at_press.input_seq, "%s first F accepted from nonactive action" % kind):
		return
	await create_timer(0.35).timeout
	var before_second := observe(kind, source, player, kit)
	var elapsed := float(before_second.usec - at_press.usec) * 0.000001
	if not require(before_second.strikes == at_press.strikes and before_second.cooldown <= 0.0 and before_second.remaining_s > 0.0 and elapsed >= 0.32 and elapsed <= 0.57, "%s actual overlap with expired source cooldown" % kind):
		return
	button(KEY_F, true)
	var at_second := observe(kind, source, player, kit)
	button(KEY_F, false)
	var delta := 1 if baseline else 0
	record(kind + " overlap expected strike/sequence delta", "%s -> %s strikes; %s -> %s input seq; %s -> %s source seq" % [before_second.strikes, at_second.strikes, before_second.input_seq, at_second.input_seq, before_second.source_seq, at_second.source_seq], at_second.strikes == before_second.strikes + delta and at_second.input_seq == before_second.input_seq + delta and at_second.source_seq == before_second.source_seq + delta)
	record(kind + " overlap ledger unchanged", "paid/stock/pickup snapshot", at_second.ledger == before_second.ledger)
	if not baseline:
		record(kind + " rejected F leaves original action and resource untouched", "remaining %.6fs -> %.6fs" % [before_second.remaining_s, at_second.remaining_s], before_second.action == at_second.action and before_second.remaining_s == at_second.remaining_s and before_second.cooldown == at_second.cooldown and before_second.phase == at_second.phase and before_second.clip == at_second.clip and before_second.position_s == at_second.position_s and before_second.playing == at_second.playing)
	for i in range(100):
		if kit.action_left <= 0.0 and source.cooldown <= 0.0:
			break
		await physics_frame
	var next_before := observe(kind, source, player, kit)
	if not require(next_before.remaining_s <= 0.0 and next_before.cooldown <= 0.0, "%s existing action timer naturally expires" % kind):
		return
	button(KEY_F, true)
	var next_after := observe(kind, source, player, kit)
	button(KEY_F, false)
	record(kind + " legal F after action expiry advances once", "strikes %s -> %s; sequence %s -> %s" % [next_before.strikes, next_after.strikes, next_before.input_seq, next_after.input_seq], next_after.strikes == next_before.strikes + 1 and next_after.input_seq == next_before.input_seq + 1 and next_after.source_seq == next_after.input_seq and next_after.remaining_s > 0.0)
	print("TIMING ", JSON.stringify({"kind":kind,"baseline":baseline,"elapsed_s":elapsed,"first_before":before,"first_after":at_press,"overlap_before":before_second,"overlap_after":at_second,"next_before":next_before,"next_after":next_after}))
	completed += 1

func new_game() -> void:
	if is_instance_valid(game):
		game.queue_free()
		await process_frame
	game = LEVEL.instantiate()
	root.add_child(game)
	await ticks(10)

func run() -> void:
	baseline = "baseline" in OS.get_cmdline_user_args()
	await new_game()
	if not require(game.bound and not game.persist_requested, "exact integrated ephemeral tree scene"):
		return
	if not require(await walk([-.35, 6.0]) and await walk([-.85, 6.0]) and game._tree_is_target(), "physical tree approach using input events"):
		return
	await inspect_action("chop", game.resource_tree)
	if completed != 1:
		return
	await new_game()
	if not require(game.bound and not game.persist_requested, "exact integrated ephemeral rock scene"):
		return
	if not require(await walk([0.0, 5.3]) and await walk([-6.0, 5.3]) and await walk([-6.0, 4.1]) and game._rock_is_target() and not game._tree_is_target(), "physical outdoor rock approach using input events"):
		return
	await inspect_action("mine", game.resource_rock)
	if completed != 2:
		return
	quit(0 if failures == 0 else 1)
