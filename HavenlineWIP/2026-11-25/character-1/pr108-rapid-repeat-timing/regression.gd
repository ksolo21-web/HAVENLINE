extends SceneTree
const LEVEL = preload("res://previews/integrated_opening.tscn")
const POINTER := Vector2(450, 375)
var game
var failures := 0
var finger := 30
var completed := 0

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

func observe(source, player: AnimationPlayer, kit) -> Dictionary:
	return {
		"usec": Time.get_ticks_usec(), "strikes": source.strikes, "phase": source.phase,
		"cooldown": source.cooldown, "clip": String(player.current_animation),
		"position_s": player.current_animation_position if not player.current_animation.is_empty() else -1.0,
		"playing": player.is_playing(), "action": kit.action, "remaining_s": kit.action_left,
	}

func inspect_action(kind: String, source) -> void:
	var kit = game.character_kit
	var player: AnimationPlayer = kit._player
	var clip := StringName("l1_actions/" + kind)
	if not require(kit.ready and player.has_animation(clip), "%s exact runtime clip bound" % kind):
		return
	var imported_clip := player.get_animation(clip)
	var notifies := 0
	for idx in range(imported_clip.get_track_count()):
		if imported_clip.track_get_type(idx) == Animation.TYPE_METHOD:
			notifies += 1
	print("TIMING ", JSON.stringify({"type":"clip", "kind":kind, "duration_s":imported_clip.length,"method_tracks":notifies,"total_tracks":imported_clip.get_track_count()}))
	var before := observe(source, player, kit)
	button(KEY_F, true)
	var at_press := observe(source, player, kit)
	button(KEY_F, false)
	await create_timer(0.35).timeout
	var before_second := observe(source, player, kit)
	button(KEY_F, true)
	var at_second := observe(source, player, kit)
	button(KEY_F, false)
	var after_frames: Array[Dictionary] = []
	for _i in range(6):
		await process_frame
		after_frames.append(observe(source, player, kit))
	var elapsed := float(before_second.usec - at_press.usec) * 0.000001
	print("TIMING ", JSON.stringify({"type":"observations", "kind":kind, "elapsed_s":elapsed, "before":before, "first_dispatch_same_stack":at_press,"before_second":before_second,"second_dispatch_same_stack":at_second,"after_frames":after_frames}))
	if not require(at_press.strikes == before.strikes + 1 and before_second.strikes == at_press.strikes and before_second.cooldown <= 0.0 and before_second.remaining_s > 0.0 and elapsed >= 0.32 and elapsed <= 0.57, "%s first hit and actual second event overlap admitted" % kind):
		return
	var second_advances: bool = at_second.strikes == before_second.strikes + 1
	record(kind + " second resource impact is not immediate while first action is still active", "second changed=%s; prior clip %.6fs prior action %.6fs" % [second_advances, before_second.position_s, before_second.remaining_s], not second_advances)
	var progressed_without_rewind: bool = second_advances and before_second.playing and before_second.clip == String(clip) and before_second.position_s >= 0.03
	for item in after_frames:
		progressed_without_rewind = progressed_without_rewind and item.clip == String(clip) and item.position_s + 0.015 >= before_second.position_s
	record(kind + " repeated accepted hit has separate clip restart", "accepted=%s overlapping_clip_never_rewound=%s" % [second_advances, progressed_without_rewind], not progressed_without_rewind)
	completed += 1

func new_game() -> void:
	if is_instance_valid(game):
		game.queue_free()
		await process_frame
	game = LEVEL.instantiate()
	root.add_child(game)
	await ticks(10)

func run() -> void:
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
