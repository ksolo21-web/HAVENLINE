extends "res://tests/field_route.gd"

const SessionProof = preload("res://tests/lifecycle_test_profile.gd")

const Kit = preload("res://field_station_kit.gd")
const Pad = preload("res://field_station_pad.gd")
const Art = preload("res://field_art.gd")
var rows: Array = []
var forest_out := ""
var failures: Array[String] = []
var capture := true

func _initialize() -> void:
	run.call_deferred()

func _check(ok: bool,label:String) -> void:
	if not ok: failures.append(label)

func _coast(ticks: int) -> void:
	steer(Vector2.ZERO)
	for i in ticks: await physics_frame

func _view(label: String) -> void:
	await process_frame
	RenderingServer.force_draw(true,1./60.)
	root.get_texture().get_image().save_jpg(forest_out.path_join(label+".jpg"),.91)

func _pinch() -> void:
	var c := Vector2(root.get_visible_rect().size)*Vector2(.49,.40)
	field.clear_touch()
	touch(6,c-Vector2(18,0),true)
	touch(7,c+Vector2(18,0),true)
	await physics_frame
	for step in 12:
		var gap := 18.+float(step+1)*5.
		for j in 2:
			var drag := InputEventScreenDrag.new()
			drag.index = 6+j
			drag.position = c+Vector2(gap*(-1. if j==0 else 1.),0)
			root.push_input(drag,true)
		await physics_frame
	touch(6,c-Vector2(78,0),false)
	touch(7,c+Vector2(78,0),false)
	await _coast(5)

func run() -> void:
	capture = true
	forest_out = OS.get_environment("T01_OUT")
	root.size = Vector2i(960,540)
	root.borderless = true
	field = load("res://field_opening.tscn").instantiate()
	root.add_child(field)
	current_scene = field
	camera = field.camera
	await _coast(15)
	field.player_invulnerability = 100.
	_check(field.lakeshore.inlet_fixtures.get_child_count()==4,"four static fixtures installed in the actual game scene")
	var rack: Node3D = field.lakeshore.inlet_fixtures.get_node("FishingRackFixture")
	var cook: Vector3 = field.lakeshore.apron_position()
	var shore := Vector3(-21.45,0,13.17)
	var work: Vector3 = field.processors.machines["wood"].global_position.lerp(field.processors.machines["stone"].global_position,.48)+Vector3.RIGHT*1.85
	var mode := OS.get_environment("T05_MODE")
	if mode == "native":
		await screen(Vector2i(3840,2160))
		await stand(cook,"4K-cooker-trays")
		await stand(work,"4K-paid-workshops")
		await stand(Vector3(5.9,0,-3.4),"4K-service-and-defense")
	elif mode == "shore":
		await stand(shore,"Landscape-lakeshore")
		await screen(Vector2i(840,360))
		await stand(shore,"Cover-rotated-bank")
		await screen(Vector2i(546,492))
		await stand(shore,"Fold-inner-rotated-bank")
		await screen(Vector2i(896,672))
		await stand(shore,"Tablet-bank")
		await screen(Vector2i(360,840))
		await stand(shore,"Cover-bank")
		await screen(Vector2i(492,546))
		await stand(shore,"Fold-inner-bank")
		await stand(rack.global_position+rack.global_basis.z*2.38+Vector3(0,0,-1.10),"Fold-inner-rod-rack-touch")
		await _pinch()
		await _coast(28)
		await frame("Fold-inner-rod-rack-2x")
		await screen(Vector2i(960,540))
		await stand(Vector3(-21.8,0,11.),"Landscape-winch-processing")
		await _pinch()
		await _coast(28)
		await frame("Landscape-winch-processing-2x")
	elif mode == "detail":
		await screen(Vector2i(492,546))
		await stand(Vector3(-24.12707,0,20.3393),"Fold-inner-rack-approach")
		await _pinch()
		await _coast(24)
		await frame("Fold-inner-four-rods-2x")
		await screen(Vector2i(960,540))
		await stand(Vector3(-24.39018,0,7.363814),"Landscape-catch-crate")
		await _pinch()
		await _coast(24)
		await frame("Landscape-catch-crate-2x")
	elif mode == "production":
		await stand(cook,"Cooker-empty")
		field.set_physics_process(false)
		var journal: Dictionary = field.inventory.settlement
		var rules = field.settlement_loop.Rules
		for i in rules.Logistics.WORK_RACK+4:
			field.inventory.collect("station-kit-proof-meat-"+str(i),"meat")
			field.inventory.carried.meat -= 1
		journal.hoppers.meat = 4
		journal.work_seconds.meat = rules.CYCLE_SECONDS.meat*.52
		field.settlement_loop._present_production(.18)
		await frame("Cooker-running")
		_check(field.lakeshore.working,"existing cooker runs with raw queue")
		journal.cooked += rules.Logistics.WORK_RACK
		field.settlement_loop._present_production(.18)
		await frame("Cooker-full-stalled")
		_check(not field.lakeshore.working and journal.hoppers.meat>0,"full output pauses the existing production cycle")
	elif mode == "starter":
		await screen(Vector2i(492,546))
		await stand(field.field_env.buy_anchor.global_position+Vector3(2.35,0,.40),"Fold-inner-founding-pad")
		await _pinch()
		await _coast(28)
		await frame("Fold-inner-founding-pad-2x")
	else:
		await stand(cook,"Landscape-kitchen-empty")
		await stand(work,"Landscape-saw-drill-empty")
		await stand(Vector3(6.10,0,-3.44),"Landscape-counter-and-tower")
		await stand(cook,"Landscape-cooker-pinch-start")
		await _pinch()
		await _coast(28)
		await frame("Landscape-cooker-2x")
		await screen(Vector2i(896,672))
		await stand(field.depot.house.global_position+Vector3(.8,0,2.4),"Tablet-work-camp")
	var file := FileAccess.open(forest_out.path_join("Capture.json"),FileAccess.WRITE)
	file.store_string(JSON.stringify({"views":rows,"failures":failures,"renderer":RenderingServer.get_video_adapter_name()},"  "))
	file.close()
	await SessionProof.drain_field_audio(self,field)
	field.queue_free()
	for i in 6: await process_frame
	quit(int(not failures.is_empty()))

func screen(size: Vector2i) -> void:
	field.set_zoom_ratio(1.0)
	root.size = size
	for i in 6: await process_frame
	origin=Vector2(root.get_visible_rect().size)*Vector2(.24,.77)
	_check(root.size==size,"render size "+str(size))

func stand(at: Vector3, label: String) -> void:
	field.set_zoom_ratio(1.0)
	field.actor.global_position = at
	field.actor.velocity = Vector3.ZERO
	field.previous_dry_position = at
	await _coast(58)
	await frame(label)

func frame(label: String) -> void:
	await _view(label)
	rows.append({"file":label+".jpg","size":[root.size.x,root.size.y],"scale":root.scaling_3d_scale,
		"zoom":field.get_zoom_ratio(),"feet":pt(field.actor.global_position),"camera":pt(camera.global_position),
		"draws":RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_DRAW_CALLS_IN_FRAME),
		"triangles":RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_PRIMITIVES_IN_FRAME)})
