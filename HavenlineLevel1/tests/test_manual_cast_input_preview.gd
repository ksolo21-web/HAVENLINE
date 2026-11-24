extends "res://tests/test_integrated_manual_shore_route.gd"
const CastPreview = preload("res://previews/manual_cast_input_preview.tscn")

func dispatch_key(pressed: bool, echo := false) -> void:
	var event := InputEventKey.new()
	event.physical_keycode = KEY_G
	event.pressed = pressed
	event.echo = echo
	root.push_input(event, true)
	await process_frame

func dispatch_touch(i: int, at: Vector2, pressed: bool, device := 1) -> void:
	var event := InputEventScreenTouch.new()
	event.index = i
	event.device = device
	event.position = at
	event.pressed = pressed
	root.push_input(event, true)
	await process_frame

func dispatch_drag(i: int, at: Vector2, device: int) -> void:
	var event := InputEventScreenDrag.new()
	event.index = i
	event.device = device
	event.position = at
	root.push_input(event, true)
	await process_frame

func select_route_to_bank() -> void:
	check(await reach_segment(OUTSIDE_EAST, "east-outward"), "ordinary East aperture traversal")
	check(await reach_segment(BANK_CORRIDOR_TURN, "out-to-turn"), "ordinary dry corridor bend")
	check(await reach_segment(BANK_ANCHOR, "out-to-provisional-bank"), "ordinary grounded reach to provisional test stand")
	await tick(8)

func run() -> void:
	game = CastPreview.instantiate()
	game.position = Vector3(2, 1.1, -3.0)
	root.add_child(game)
	if not game.bound or not is_instance_valid(game.cast_button):
		check(false, "exact opt-in source and tested binding ready")
		quit(1)
		return
	await tick(10)
	check(not game.persist_requested and not game.cast_button.visible, "opt-in action hidden until eligible; no persistence")
	await dispatch_key(true)
	await dispatch_key(false)
	check(game.cast_intent_count == 0, "engine-dispatched G from spawn has no effect")
	await earn_camp()
	if failures:
		quit(1)
		return
	var snapshot := var_to_bytes(game.ledger.snapshot())
	check(await travel(game.point([2.0, 1.9])), "ordinary inside-camp route")
	check(await reach_segment(INSIDE_EAST, "inside-east"), "normal movement to earned East interaction")
	var gate_button: Button = game.gate_button
	check(gate_button.visible and not game.cast_button.visible, "East gate control shown but cast is not")
	await dispatch_touch(300, gate_button.get_global_rect().get_center(), true)
	await dispatch_touch(300, gate_button.get_global_rect().get_center(), false)
	await tick(75)
	check(game.gates[1].target_open and absf(game.gates[1].angle - PI * .5) < .002 and not game.gates[0].target_open, "engine-dispatched East gate tap opens only gate, no cast conflict")
	check(game.cast_intent_count == 0 and game.touch_id == -1, "gate tap did not produce cast or steal movement")
	await select_route_to_bank()
	var button: Button = game.cast_button
	var rect := button.get_global_rect()
	var at := rect.get_center()
	check(button.visible and button.text == "Cast [G]", "visible optional action only on actual eligible dry-bank stance")
	check(rect.size.y >= 48.0 and not rect.intersects(gate_button.get_global_rect()) and not rect.intersects(game.tree_button.get_global_rect()), "cast hit target legible-sized and separate from gate/tree slots")
	var label_font := button.get_theme_font("font")
	var label_size := button.get_theme_font_size("font_size")
	check(label_font.get_string_size("Input noted", HORIZONTAL_ALIGNMENT_LEFT, -1, label_size).x <= rect.size.x - button.get_theme_stylebox("normal").get_minimum_size().x, "whole acknowledgment label fits same slot")

	await dispatch_key(true)
	check(game.cast_intent_count == 1 and game.last_cast_intent.status == "intent" and button.text == "Input noted", "ordinary engine G gives exactly one validated intent and visible acknowledgment")
	await dispatch_key(true, true)
	await dispatch_key(true)
	await dispatch_touch(301, at, true)
	await dispatch_touch(301, at, false)
	check(game.cast_intent_count == 1 and game.touch_id == -1, "held key plus touch or echo yields no duplicate or movement owner")
	await dispatch_key(false)

	await dispatch_touch(302, Vector2(530, 388), true)
	check(game.touch_id == 302, "ordinary movement owns separate gesture")
	await dispatch_touch(303, at, true)
	await dispatch_touch(303, at, false)
	check(game.cast_intent_count == 1 and game.touch_id == 302, "cast tap while movement held cannot steal either operation")
	await dispatch_touch(302, Vector2(530, 388), false)
	await dispatch_touch(304, at, true, InputEvent.DEVICE_ID_EMULATION)
	await dispatch_touch(304, at, false, InputEvent.DEVICE_ID_EMULATION)
	check(game.cast_intent_count == 1 and game.touch_id == -1, "emulated cast touch yields no intent or movement")

	await dispatch_touch(305, at, true)
	check(game.cast_intent_count == 2 and button.text == "Input noted" and game.touch_id == -1, "new physical touch gives one intent, no movement")
	await dispatch_touch(305, at, true)
	await dispatch_touch(306, at, false)
	await dispatch_touch(305, at, true)
	check(game.cast_intent_count == 2 and game.touch_id == -1, "held touch and mismatched release do not duplicate")
	await dispatch_touch(305, at, false)

	await dispatch_key(true)
	check(game.cast_intent_count == 3, "new deliberate keyboard edge after proper touch release")
	check(await reach_segment(BANK_CORRIDOR_TURN, "leave-bank-while-held"), "ordinary travel leaves the casting footprint while key held")
	check(not button.visible and game.cast_intent_count == 3, "outside footprint hides action, no duplicate while traveling")
	check(await reach_segment(BANK_ANCHOR, "reenter-bank-while-held"), "ordinary travel re-enters same provisional anchor")
	await tick(8)
	check(button.visible and button.text == "Cast [G]", "re-entry requires new acknowledgement")
	await dispatch_key(true, true)
	await dispatch_key(true)
	check(game.cast_intent_count == 3, "travel re-entry plus held/echo does not recast")
	await dispatch_key(false)
	await dispatch_key(true)
	check(game.cast_intent_count == 4 and button.text == "Input noted", "normal release and new press produces exactly one new intent")
	await dispatch_key(false)
	var start_count: int = game.cast_intent_count
	await dispatch_touch(751, at, true, 1)
	check(game.cast_intent_count == start_count + 1 and game._cast_touch_device == 1, "legitimate touch retains both exact source fields")
	await dispatch_drag(751, at + Vector2(160, 0), 2)
	await dispatch_drag(751, at + Vector2(160, 0), InputEvent.DEVICE_ID_EMULATION)
	check(game._cast_touch == 751 and game._cast_touch_device == 1 and game.touch_id == -1, "same-index foreign/emulated drags alter neither owner")
	await dispatch_touch(751, at, false, 2)
	await dispatch_touch(751, at, false, InputEvent.DEVICE_ID_EMULATION)
	await dispatch_touch(751, at, true, 1)
	check(game._cast_touch == 751 and game.cast_intent_count == start_count + 1, "foreign/emulated same-index releases cannot rearm held cast")
	await dispatch_touch(751, at + Vector2(170, 0), false, 1)
	check(game._cast_touch < 0 and game._cast_owner == "", "legitimate owner release outside target re-arms")
	await dispatch_key(true)
	check(game.cast_intent_count == start_count + 2, "deliberate new G after exact touch release")
	await dispatch_touch(753, Vector2(530,388), true, 1)
	await dispatch_key(false)
	check(game._cast_owner == "" and game.touch_id == 753, "owned keyboard release remains allowed during movement")
	await dispatch_key(true)
	await dispatch_key(false)
	check(game.cast_intent_count == start_count + 2 and game.touch_id == 753, "new keyboard edge during movement cannot steal or cast")
	await dispatch_touch(753, Vector2(530,388), false, 1)
	await dispatch_key(true)
	await dispatch_key(false)
	check(game.cast_intent_count == start_count + 3 and game.touch_id == -1, "movement release permits deliberate G re-entry")
	check(var_to_bytes(game.ledger.snapshot()) == snapshot and not game.persist_requested, "no grant, cast result, receipt, stock or save after all accepted inputs")

	# Existing integrated opening structurally does not instantiate this fixture.
	game.queue_free()
	await process_frame
	game = GAME.instantiate()
	root.add_child(game)
	await tick(3)
	check(game.bound and game.get_script().resource_path == "res://previews/integrated_opening.gd" and not ("cast_button" in game), "ordinary integrated preview retains no cast action")
	print("manual cast input preview checks=", checks, " failures=", failures)
	quit(1 if failures else 0)
