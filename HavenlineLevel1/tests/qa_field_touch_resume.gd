extends SceneTree
const Session = preload("res://tests/lifecycle_test_profile.gd")
var game
var checks := {}

func _initialize() -> void:
	if not Session.isolated(self, "res://tests/qa_field_touch_resume.gd"):
		call_deferred("run")

func press(index: int, at: Vector2) -> void:
	var event := InputEventScreenTouch.new()
	event.position = at
	event.index = index
	event.pressed = true
	game._input(event)

func drag(index: int, at: Vector2) -> void:
	var event := InputEventScreenDrag.new()
	event.index = index
	event.position = at
	game._input(event)

func released() -> bool:
	return game.touch_id == -1 and game.trial_camera.fingers.is_empty() and game.hud_fingers.is_empty() and game.settlement_loop.finger == -1 and not game.trial_camera.pinching

func run() -> void:
	game = load("res://field_opening.tscn").instantiate()
	root.add_child(game)
	for i in 4: await physics_frame
	var origin := Vector2(440,440)
	press(3,origin)
	drag(3,origin+Vector2(65,0))
	checks["drag present before background"] = game.touch_id == 3 and game.touch_now.distance_to(game.touch_origin) == 65
	game.notification(Node.NOTIFICATION_APPLICATION_PAUSED)
	checks["background releases drag without Android up event"] = released()
	press(1,origin)
	press(6,origin+Vector2(190,0))
	checks["two fingers pinch before folding"] = game.trial_camera.pinching
	game.get_viewport().size_changed.emit()
	checks["fold releases both contacts"] = released()
	var quality: Rect2 = game.graphics.quality_button.get_global_rect()
	press(1,quality.get_center())
	checks["HUD holds its finger"] = game.hud_fingers.has(1)
	game.notification(Node.NOTIFICATION_APPLICATION_FOCUS_OUT)
	checks["interrupted HUD accepts future touches"] = released()
	press(3,origin)
	drag(3,origin+Vector2(72,0))
	checks["same Android finger ID can steer after resume"] = game.touch_id == 3 and game.touch_now.distance_to(game.touch_origin) == 72
	print(JSON.stringify({"suite":"touch_resume","checks":checks}))
	await Session.drain_field_audio(self,game)
	game.queue_free()
	for i in 4: await process_frame
	quit(1 if checks.values().has(false) else 0)
