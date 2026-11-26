extends "res://tests/hvn_l1_combined_route.gd"
## Frame-read observation only: never changes frame/view/terrain/animation/game state.
const WRITER := ["fresh-spawn","paid-first-frame","south-bidirectional","east-bidirectional","writer-v2"]
const COLD := ["cold-v2-no-replay"]
var capture_dir := ""
var armed := 0
var draw_failures := 0
var drawn: Array[String] = []

func snapshot_state() -> Dictionary:
	var a = game.actor.position
	var camera = game.camera
	var offset: Vector3 = camera.position - a
	return {"tick":tick_count,"physics_frames":Engine.get_physics_frames(),
		"stock":int(game.ledger.stock.wood),"renewals":int(game.ledger.pine_occurrences),
		"paid":game.ledger.receipt==RECEIPT,"camp_visible":game.camp_built.is_visible_in_tree(),
		"pad_hidden":live_pad_hidden(),"hearth_center_paid":camp_ok(not game.ledger.receipt.is_empty()),
		"south_open":game.gates[0].target_open,"east_open":game.gates[1].target_open,
		"offset":[offset.x,offset.y,offset.z],"actor":[a.x,a.y,a.z]}

func checkpoint(phase: String) -> void:
	super.checkpoint(phase)
	if phase not in WRITER and phase not in COLD:
		return
	if armed != 0 or phase in drawn:
		draw_failures += 1
		print("DRAW_REJECT duplicate-or-overlapping-checkpoint ",phase)
		return
	armed += 1
	RenderingServer.frame_post_draw.connect(_draw.bind(phase,snapshot_state()), CONNECT_ONE_SHOT)

func _draw(phase: String, queued: Dictionary) -> void:
	armed -= 1
	var current := snapshot_state()
	var camera := game.camera as Camera3D
	var image := root.get_texture().get_image()
	if root.size != Vector2i(1280,720) or image == null or image.is_empty() or image.get_size() != Vector2i(1280,720):
		draw_failures += 1
		print("DRAW_REJECT frame-size-or-readback ",phase)
		return
	var view_direction := Vector3(7.0,11.0,11.0).normalized()
	if root.get_camera_3d() != camera or camera.projection != Camera3D.PROJECTION_ORTHOGONAL or not is_equal_approx(camera.size,13.0) or camera.global_basis.z.normalized().dot(view_direction)<.999999:
		draw_failures += 1
		print("DRAW_REJECT camera-custody ",phase)
		return
	for key in ["stock","renewals","paid","camp_visible","pad_hidden","hearth_center_paid","south_open","east_open"]:
		if queued[key] != current[key]:
			draw_failures += 1
			print("DRAW_REJECT checkpoint-drift ",phase," ",key)
			return
	if int(current.physics_frames)-int(queued.physics_frames) < 0 or int(current.physics_frames)-int(queued.physics_frames) > 1:
		draw_failures += 1
		print("DRAW_REJECT draw-outside-one-physics-step ",phase)
		return
	var hash := HashingContext.new()
	hash.start(HashingContext.HASH_SHA256)
	hash.update(image.get_data())
	var pixel_digest := hash.finish().hex_encode()
	var name := capture_dir.path_join(phase+".png")
	if FileAccess.file_exists(name) or image.save_png(name)!=OK:
		draw_failures+=1
		print("DRAW_REJECT destination ",phase)
		return
	drawn.append(phase)
	print("L1_POST_DRAW ",JSON.stringify({"phase":phase,"queued":queued,"draw":current,"viewport_px":[root.size.x,root.size.y],"image_px":[image.get_width(),image.get_height()],"camera_ortho":camera.size,"display":DisplayServer.get_name(),"pixel_sha256":pixel_digest}))

func finish(phase: String) -> void:
	# The final authoritative checkpoint normally quits immediately. Only this
	# observer waits one normal draw for its final capture; gameplay stays live.
	if armed>0:
		await RenderingServer.frame_post_draw
		if armed>0:
			await process_frame
	var expected: Array = WRITER if phase=="write" else COLD
	if drawn!=expected or armed!=0 or draw_failures!=0:
		print("DRAW_REJECT incomplete-or-invalid-order ",phase," ",drawn)
		quit(3)
		return
	print("L1_STOCK_POST_DRAW_OK ",phase," ",drawn.size())
	super.finish(phase)

func run() -> void:
	capture_dir=OS.get_environment("HVN_L1_STOCK_CAPTURE")
	if DisplayServer.get_name()!="X11" or capture_dir.is_empty() or not DirAccess.dir_exists_absolute(capture_dir):
		print("DRAW_REJECT display-or-owned-output")
		quit(2)
		return
	await super.run()
