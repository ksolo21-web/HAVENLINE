extends "res://tests/test_docked.gd"
# Uses the critic's exact mount, movement and gate helpers; cameras exist only here.
var observer: Camera3D
var output_dir: String
var expected_size: Vector2i

func shot(tag: String, focus: Vector3, offset: Vector3, span: float, custom: bool) -> bool:
	var view: Camera3D = game.camera
	if custom:
		observer.global_position = focus + offset
		observer.look_at(focus)
		observer.size = span
		observer.make_current()
		view = observer
	await tick(12)
	await RenderingServer.frame_post_draw
	var image := root.get_texture().get_image()
	if image == null or image.is_empty() or image.get_size() != expected_size:
		check(false,"valid exact native texture "+tag)
		return false
	# Reject a black/flat/invalid readback without moving or adjusting candidate sources.
	var samples: Dictionary = {}
	for gy in range(1,8):
		for gx in range(1,8):
			samples[image.get_pixel(floori(expected_size.x*gx/8.0),floori(expected_size.y*gy/8.0))] = 1
	if samples.size() < 5:
		check(false,"nonflat live readback "+tag)
		return false
	var saved := image.save_png(output_dir.path_join(tag+".png"))
	var ns: Vector3 = game.to_global(game.point([0.0,-4.0]))
	var projected := []
	for x in [-5.0,-1.825,1.825,5.0]:
		projected.append(str(view.unproject_position(ns + Vector3(x,.475,0))))
	print("NATIVE_SHOT ",JSON.stringify({"tag":tag,"window":str(root.size),"rect":str(root.get_visible_rect()),"png":str(image.get_size()),"transform":str(view.global_transform),"size":view.size,"projection":view.projection,"observer_only":custom,"focus":str(focus),"north_bounds_and_seam_pixels":projected,"actor":str(game.actor.global_position),"south_angle":game.gates[0].angle,"east_angle":game.gates[1].angle,"paid":not game.ledger.receipt.is_empty()}))
	check(saved == OK,"native PNG "+tag)
	return saved == OK

func run() -> void:
	output_dir = OS.get_environment("HVN_DOCKED_STILLS")
	expected_size = Vector2i(1280,720)
	if DisplayServer.get_name() == "headless" or output_dir.is_empty() or not DirAccess.dir_exists_absolute(output_dir):
		quit(8)
		return
	game = GAME.instantiate()
	game.position = Vector3(2.0, 1.1, -3.0) # inherited critic mount's exact tested world frame
	root.add_child(game)
	await tick(10)
	if not game.bound or game.persist_requested or not game.ledger.receipt.is_empty() or game.camp_built.visible or root.size != expected_size:
		check(false,"exact clean rendered session")
		quit(9)
		return
	check(await travel(game.wood_anchors["wood-b"]),"first loose wood")
	check(await travel(game.wood_anchors["wood-c"]),"second loose wood")
	check(await travel(game.point([-.35,6.0])),"walk to standing tree approach")
	check(await travel(game.point([-.85,6.0])),"face standing tree")
	check(game.ledger.stock.wood == 2 and game.resource_tree.can_address(game.actor.global_position,game.tree_facing()),"two wood and in chop range")
	for i in range(3):
		press(KEY_F)
		await tick(21)
	check(await travel(game.point([.0,6.0])),"ordinary clear of fall")
	await tick(58)
	check(game.ledger.stock.wood == 3 and game.resource_tree.phase == "credited","all wood earned")
	check(await travel(game.point([0.0,3.30])) and game.ledger.receipt.is_empty(),"outside pay radius no debit")
	check(await travel(game.pad_anchor),"ordinary walk onto unchanged enabled pad")
	check(game.ledger.stock.wood == 0 and not game.ledger.receipt.is_empty() and game.camp_built.visible,"paid normally before mounting donor")
	if failures != 0 or not await install_fixture():
		quit(10)
		return
	var paid := var_to_bytes(game.ledger.snapshot())
	await gate_cross(game.gates[0],[0.0,2.0],[0.0,6.0],"South unchanged")
	check(await travel(game.point([2.0,1.9])),"interior cross")
	await gate_cross(game.gates[1],[3.0,0.0],[7.0,0.0],"East unchanged")
	check(await travel(game.point([2.0,-2.30])),"actual inboard view station")
	if failures != 0 or not await shot("01-native-game-camera-inboard",Vector3.ZERO,Vector3.ZERO,0.0,false):
		quit(11)
		return
	check(await travel(game.point([3.0,0.0])) and await travel(game.point([7.0,0.0])) and await travel(game.point([7.0,-5.70])) and await travel(game.point([2.0,-5.70])),"real exit then outboard viewing route")
	await tick(60)
	if failures != 0 or not await shot("02-native-game-camera-outboard",Vector3.ZERO,Vector3.ZERO,0.0,false):
		quit(12)
		return
	observer = Camera3D.new()
	observer.projection = Camera3D.PROJECTION_ORTHOGONAL
	observer.keep_aspect = game.camera.keep_aspect
	game.add_child(observer)
	var ns: Vector3 = game.to_global(game.point([0.0,-4.0]))
	for sign_value in [1.0,-1.0]:
		var side: float = sign_value
		var name_side := "inboard" if side > 0 else "outboard"
		if not await shot("full-"+name_side,ns + Vector3(0,.44,0),Vector3(5.5,7.0,side*10.0),8.8,true):
			quit(13)
			return
		for seam_value in [-1.825,1.825]:
			var x: float = seam_value
			var seam_name := "left" if x < 0 else "right"
			var target := ns + Vector3(x,.4,0)
			var game_span: float = game.camera.size
			if not await shot("seam-"+seam_name+"-"+name_side+"-game-scale",target,Vector3(2.75,5.5,side*8),game_span,true):
				quit(14)
				return
			if not await shot("seam-"+seam_name+"-"+name_side+"-close",target,Vector3(1.2,1.25,side*2.8),2.25,true):
				quit(15)
				return
	check(paid == var_to_bytes(game.ledger.snapshot()) and not game.persist_requested,"no fixture or observer ledger mutation")
	print("DOCKED_RENDER_RESULT checks=",checks," failures=",failures)
	quit(1 if failures else 0)
