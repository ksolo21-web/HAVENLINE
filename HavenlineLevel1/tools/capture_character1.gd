extends SceneTree
## Headless-or-display capture of Character 1 from the Level 1 camera rig.
const Opening = preload("res://opening.tscn")
const OUT := "/opt/cursor/artifacts"
var game
var frames: Array[Image] = []

func _initialize() -> void:
	print("CAPTURE_START")
	call_deferred("run")

func run() -> void:
	DirAccess.make_dir_recursive_absolute(OUT)
	game = Opening.instantiate()
	root.add_child(game)
	await process_frame
	await process_frame
	await RenderingServer.frame_post_draw
	# Real opening camera, whole snow field. Then freeze gameplay motion so the
	# orbit and action shots keep that camera instead of the follow lerp.
	await shot(OUT + "/character1-game-camera.png")
	game.set_physics_process(false)
	var origin: Vector3 = game.camera.position - game.actor.position
	game.camera.size = 2.6
	var sheet: Array[Image] = []
	for label in ["front", "left", "back", "right"]:
		var yaw := 0.0
		if label == "left":
			yaw = PI * 0.5
		elif label == "back":
			yaw = PI
		elif label == "right":
			yaw = -PI * 0.5
		_orbit(origin, yaw)
		await process_frame
		await RenderingServer.frame_post_draw
		var image := _grab()
		image.save_png(OUT + "/character1-turn-" + label + ".png")
		sheet.append(image)
		await _record(12)
	await _action_at(game.resource_tree.global_position + Vector3(1.15, 0, 0), Vector3.LEFT, "chop")
	var chop := _grab()
	chop.save_png(OUT + "/character1-chop.png")
	sheet.append(chop)
	await _record(48)
	await _action_at(game.resource_rock.global_position + Vector3(1.15, 0, 0), Vector3.LEFT, "mine")
	var mine := _grab()
	mine.save_png(OUT + "/character1-mine.png")
	sheet.append(mine)
	await _record(48)
	_sheet(sheet).save_png(OUT + "/character1-turnaround-chop-mine.png")
	_encode()
	print("CAPTURE_OK")
	quit(0)

func _action_at(feet: Vector3, facing: Vector3, action: String) -> void:
	game.actor.position = feet
	game.actor.rotation.y = atan2(facing.x, facing.z)
	game.character_kit.action_left = 0.0
	game.character_kit.action = ""
	game.camera.size = 2.6
	_orbit(Vector3(7, 11, 11), 0.4)
	for _i in 8:
		game.character_kit.drive(1.0 / 30.0, 0.0, true, action == "chop", action == "mine", false)
		await process_frame
	game.character_kit.begin_action(action)
	for _i in 16:
		game.character_kit.drive(1.0 / 30.0, 0.0, true, action == "chop", action == "mine", false)
		game.camera.position = game.actor.position + Vector3(7, 11, 11).rotated(Vector3.UP, 0.4)
		game.camera.look_at(game.actor.position + Vector3(0, 0.9, 0))
		await process_frame
	await RenderingServer.frame_post_draw

func _orbit(offset: Vector3, yaw: float) -> void:
	var swung := offset.rotated(Vector3.UP, yaw)
	game.camera.position = game.actor.position + swung
	game.camera.look_at(game.actor.position + Vector3(0, 0.9, 0))

func _grab() -> Image:
	var image: Image = game.get_viewport().get_texture().get_image()
	if image.get_format() != Image.FORMAT_RGB8:
		image.convert(Image.FORMAT_RGB8)
	return image

func _record(count: int) -> void:
	for _i in count:
		var frame := _grab()
		frame.resize(960, 540, Image.INTERPOLATE_BILINEAR)
		frames.append(frame)
		await process_frame
		await RenderingServer.frame_post_draw

func shot(path: String) -> void:
	game.camera.size = 13.0
	game.camera.position = game.actor.position + Vector3(7, 11, 11)
	game.camera.look_at(game.actor.position)
	await process_frame
	await RenderingServer.frame_post_draw
	_grab().save_png(path)

func _sheet(images: Array[Image]) -> Image:
	var cell_w := 420
	var cell_h := 236
	var sheet := Image.create(cell_w * 3, cell_h * 2, false, Image.FORMAT_RGB8)
	sheet.fill(Color(0.16, 0.18, 0.2))
	for i in images.size():
		var copy: Image = images[i].duplicate()
		copy.resize(cell_w, cell_h, Image.INTERPOLATE_LANCZOS)
		sheet.blit_rect(copy, Rect2i(0, 0, cell_w, cell_h), Vector2i((i % 3) * cell_w, int(i / 3) * cell_h))
	return sheet

func _encode() -> void:
	var folder := OUT + "/character1-frames"
	DirAccess.make_dir_recursive_absolute(folder)
	for i in frames.size():
		frames[i].save_png("%s/frame_%04d.png" % [folder, i])
	print("FRAMES ", frames.size())
