extends Control
## Track the game's existing movable touch origin. Pointer events keep going to the world.
var world
var offset := Vector2.ZERO


func install(host) -> void:
	world = host
	name = "MovementThumbstick"
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	hide()


func _process(_delta: float) -> void:
	if not is_instance_valid(world):
		return
	if world.touch_id < 0 or world.trial_camera.pinching:
		hide()
		return
	var offset_now: Vector2 = (world.touch_now - world.touch_origin).limit_length(82.) * .52
	if not visible or offset.distance_squared_to(offset_now) > .04:
		offset = offset_now
		queue_redraw()
	position = world.touch_origin
	show()


func _draw() -> void:
	draw_circle(Vector2.ZERO, 50., Color("#152a3c55"), true, -1, true)
	draw_arc(Vector2.ZERO, 48., 0., TAU, 48, Color("#fcf1cda6"), 2., true)
	draw_circle(offset + Vector2(0, 2), 21., Color("#0e253775"), true, -1, true)
	draw_circle(offset, 20., Color("#fff4dcb0"), true, -1, true)
	draw_arc(offset, 19., 0., TAU, 32, Color("#ffffedb3"), 1., true)
