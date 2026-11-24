extends SceneTree
## Disposable synthetic handler test, not OS/device routing.
var failures := 0
var checks := 0
var opening
var button_point: Vector2
var move_point := Vector2(450, 375)
const MIRROR := InputEvent.DEVICE_ID_EMULATION

func check(value: bool, label: String) -> void:
	checks += 1
	if not value:
		failures += 1
		push_error(label)

func _initialize() -> void:
	call_deferred("run")

func touch(at: Vector2, device_id: int, finger := 4, down := true) -> void:
	var ev := InputEventScreenTouch.new()
	ev.device = device_id
	ev.index = finger
	ev.position = at
	ev.pressed = down
	opening._input(ev)

func click(at: Vector2, device_id: int, down := true, button := MOUSE_BUTTON_LEFT) -> void:
	var ev := InputEventMouseButton.new()
	ev.device = device_id
	ev.button_index = button
	ev.position = at
	ev.pressed = down
	opening._input(ev)

func key(echo: bool) -> void:
	var ev := InputEventKey.new()
	ev.pressed = true
	ev.echo = echo
	ev.physical_keycode = KEY_E
	opening._input(ev)

func run() -> void:
	if not OS.get_cmdline_user_args().is_empty():
		push_error("No profile or command-line user arguments are allowed for this fixture")
		quit(2)
		return
	opening = (load("res://opening.tscn") as PackedScene).instantiate()
	root.add_child(opening)
	opening.set_physics_process(false)
	var south = opening.gates[0]
	var east = opening.gates[1]
	opening.actor.global_position = Vector3(0, 0, 5.3)
	opening.nearest_gate = south
	opening.gate_button.show()
	opening.gate_button.size = Vector2(192, 42)
	button_point = opening.gate_button.get_global_rect().get_center()

	check(not Input.emulate_mouse_from_touch and not Input.emulate_touch_from_mouse, "fixture expects effective emulation off")
	touch(button_point, 2)
	check(not south.target_open, "unearned real touch cannot toggle")
	south.set_earned(true)
	east.set_earned(true)
	touch(button_point, 2)
	check(south.target_open, "physical touch toggles")
	click(button_point, MIRROR)
	check(south.target_open, "mouse mirror after touch does not undo toggle")
	touch(button_point, MIRROR)
	check(south.target_open and opening.touch_id == -1, "tagged touch cannot toggle or acquire joystick")
	click(button_point, 3)
	check(not south.target_open, "separate real click is accepted immediately")
	touch(button_point, MIRROR)
	check(not south.target_open, "tagged touch before physical click does not toggle")
	click(button_point, 3)
	check(south.target_open, "physical click after mirror still toggles")
	click(button_point, MIRROR)
	check(south.target_open, "tagged mouse before physical touch does not toggle")
	touch(button_point, 2)
	check(not south.target_open, "physical touch after mirror still toggles")
	click(button_point, 3, false)
	click(button_point, 3, true, MOUSE_BUTTON_RIGHT)
	touch(button_point, 2, 4, false)
	check(not south.target_open, "release and right click do not toggle")
	touch(move_point, 2, 8)
	check(opening.touch_id == 8 and opening.touch_origin == move_point, "normal movement touch acquires joystick")
	touch(button_point, MIRROR, 9)
	touch(button_point, MIRROR, 9, false)
	check(not south.target_open and opening.touch_id == 8 and opening.touch_origin == move_point, "secondary tagged UI pair cannot affect held joystick")
	touch(button_point, 2, 10)
	check(south.target_open and opening.touch_id == 8, "physical button touch preserves different held joystick")
	touch(move_point, 2, 8, false)
	check(opening.touch_id == -1, "movement owner release still clears joystick")
	key(true)
	check(south.target_open, "keyboard echo ignored")
	key(false)
	check(not south.target_open and not east.target_open, "physical E toggles only the selected gate")

	print("Gate provenance fixture checks: ", checks, ", failures: ", failures)
	quit(0 if failures == 0 else 1)
