extends "res://tests/test_integrated_opening.gd"
## Private replay. No direct actor moves; ordinary input handler + physics.
func _initialize() -> void:
	call_deferred("run")

func run() -> void:
	root.size = Vector2i(1280,720)
	await process_frame
	game = GAME.instantiate()
	root.add_child(game)
	await tick(10)
	var cam := game.camera as Camera3D
	if cam == null or not game.bound:
		push_error("Camera or dry opening not admitted")
		quit(2)
		return
	var b := cam.global_transform.basis
	var right := Vector3(b.x.x,0,b.x.z).normalized()
	var forward := Vector3(b.z.x,0,b.z.z).normalized()
	check(right.dot(Vector3(11,0,-7).normalized()) > .99999 and forward.dot(Vector3(7,0,11).normalized()) > .99999, "camera horizontal axes match unchanged control yaw")
	var pitch := rad_to_deg(asin(clampf(b.z.y,-1,1)))
	check(pitch > 57.0 and pitch < 58.0, "elevated camera at RC2 pitch")
	check(is_equal_approx(cam.size,12.5), "existing RC1 landscape zoom invariant")
	for input: Vector2 in [Vector2.RIGHT, Vector2.DOWN, Vector2.LEFT, Vector2.UP]:
		await ordinary_cardinal(input,cam)
	check(game.ledger.receipt.is_empty(),"short controls test did not grant camp")
	root.size = Vector2i(414,896)
	await process_frame
	await process_frame
	var view := cam.get_viewport().get_visible_rect().size
	var want := clampf(9.0 * view.y / view.x,12.5,16.5) if view.y > view.x else 12.5
	check(is_equal_approx(cam.size,want),"viewport resize obeys inherited cap for engine's visible area")
	check(cam.global_transform.basis.is_equal_approx(b),"resize doesn't rotate control axes")
	root.size = Vector2i(1280,720)
	await process_frame
	await process_frame
	check(is_equal_approx(cam.size,12.5),"landscape span restores")
	print("camera control exact checks=",checks," failures=",failures)
	quit(1 if failures else 0)

func ordinary_cardinal(input: Vector2, cam: Camera3D) -> void:
	gesture += 1
	var before: Vector3 = game.actor.global_position
	send_touch(true)
	var ev := InputEventScreenDrag.new()
	ev.device = 1
	ev.index = gesture
	ev.position = CENTER + input * 82.0
	game._input(ev)
	check(game.touch_id == gesture,"gesture admitted "+str(input))
	await tick(6)
	send_touch(false)
	var after: Vector3 = game.actor.global_position
	# Compare both endpoints in ONE camera frame: cancels camera follow
	# translation. Project horizontal delta only, not slope elevation.
	var end := Vector3(after.x,before.y,after.z)
	var projected := cam.unproject_position(end)-cam.unproject_position(before)
	check(projected.dot(input) > .5 and absf(projected.cross(input)) < maxf(.25, projected.length()*.045),"touch moves horizontally in visually correct direction "+str(input)+" observed "+str(projected))
	await tick(2)
