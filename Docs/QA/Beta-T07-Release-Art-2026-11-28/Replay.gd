extends "res://tests/qa_snow_truck.gd"

var run_at := OS.get_environment("T07_GAMEPLAY_RUN")
var capture_kind := OS.get_environment("T07_GAMEPLAY_MODE")
var movie := StreamPeerTCP.new()
var frames := 0
var video_frames := 0
var frame_step := maxi(1, int(OS.get_environment("T07_FRAME_STEP")))
var previous_tick := -1
var skipped_ticks := 0
var start_tick := -1
var capture_events: Array[Dictionary] = []

func _initialize() -> void:
	run.call_deferred()

func capture(badge := "") -> void:
	await physics_frame
	await process_frame
	var sample := Engine.get_physics_frames()
	if start_tick < 0: start_tick = sample
	if previous_tick >= 0 and sample != previous_tick + 1: skipped_ticks += 1
	previous_tick = sample
	var sample_movie := frames % frame_step == 0
	var image: Image
	if sample_movie or not badge.is_empty():
		RenderingServer.force_draw(false)
		image = root.get_texture().get_image()
	if sample_movie:
		var transferred := movie.put_data(image.save_jpg_to_buffer(.86))
		if transferred != OK:
			printerr("Movie encoder stopped accepting frames: ",transferred)
			quit(2)
			return
		video_frames += 1
		if video_frames%20==0:
			print("Rendered ",video_frames," native frames")
	if not badge.is_empty():
		image.save_jpg(run_at.path_join(badge + ".jpg"),.83)
		capture_events.append({"frame":frames,"physics_frame":sample,"state":badge,
			"context":field.context.descriptor.get("state",""),"plot_due":field.inventory.remaining("center_hearth").wood,
			"shutter":truck.opening,"truck_position":pt(truck.body.global_position),"player_position":pt(field.actor.global_position)})
	frames += 1

func frame_for(count: int) -> void:
	for step in count:
		await capture()

func clear_ambient_threats() -> void:
	for wolf in field.enemies.duplicate(): field.encounters._remove(wolf)
	field.encounters.remaining = 900.

func context_route() -> void:
	var pad: Vector3 = field.carry.receivers.center_hearth.global_position
	var costs: int = field.inventory.remaining("center_hearth").wood
	for index in costs:
		field.inventory.collect("t07-video-wood-"+str(index),"wood")
	field.carry.sync(true)
	field.actor.global_position = pad + Vector3(0.,0.,2.18)
	field.previous_dry_position = field.actor.global_position
	field.actor.rotation.y = PI
	for count in 50: await physics_frame
	await capture("01-approach")
	steer(_heading(Vector3.FORWARD))
	var exposed := false
	for step in 43:
		var noticed: bool = field.context.descriptor.get("state") == "blocked_movement"
		var badge := "02-moving-plot-focus" if noticed and not exposed else ""
		await capture(badge)
		exposed = exposed or noticed
		if field.actor.global_position.distance_to(pad) < .24:break
	_assert("moving approach never funded the plot",field.inventory.remaining("center_hearth").wood == costs and exposed and field.carry.flights.is_empty())
	steer(Vector2.ZERO)
	var sending := false
	var previewed := false
	for step in 58:
		var flying: bool = not field.carry.flights.is_empty()
		var acquiring: bool = field.field_env.hearth_payment_focus and not flying and field.carry.flights.is_empty()
		var badge := "03-packets-launched" if flying and not sending else ("02b-ready-before-payment" if acquiring and not previewed else "")
		await capture(badge)
		previewed = previewed or acquiring
		sending = sending or flying
		if field.inventory.remaining("center_hearth").wood < costs:break
	_assert("turns green before the first flight or receipt",previewed)
	_assert("stopping launched parcels and paid first receipt",sending and field.inventory.remaining("center_hearth").wood < costs)
	var due: int = field.inventory.remaining("center_hearth").wood
	var airborne := 0
	for packet in field.carry.flights: airborne += int(packet.units)
	var return_point: Vector3 = field.actor.global_position
	steer(_heading(Vector3.BACK))
	await capture("04-release-and-move")
	await frame_for(20)
	_assert("moving away never added a payment beyond launched parcels",field.inventory.remaining("center_hearth").wood >= due-airborne)
	steer(Vector2.ZERO)
	await capture()
	for step in 90:
		var distance: Vector3 = return_point - field.actor.global_position
		distance.y = 0.0
		if distance.length() < .55: break
		steer(_heading(distance.normalized()))
		await capture()
	steer(Vector2.ZERO)
	var revealed := false
	for step in 245:
		var built: bool = field.camp_active
		await capture("05-camp-reveal" if built and not revealed else "")
		revealed = revealed or built
		if revealed and frames >= 180:break
	await frame_for(3)
	_assert("re-entry finishes payment and camp reveal exactly once",revealed and field.inventory.complete("center_hearth") and field.inventory.build_order.count("center_hearth")==1)

func truck_route() -> void:
	for id in ["center_hearth","expansion_1","storage_wood","storage_stone","storage_meat","expansion_2","snow_garage","snow_truck"]:
		_assert("prepared purchase "+id,_fund(id))
		if id=="center_hearth":
			for count in 14:await physics_frame
	clear_ambient_threats()
	field.actor.global_position = truck._exit_position()
	field.previous_dry_position = field.actor.global_position
	for count in 55:await physics_frame
	await capture("01-boarding-approach")
	var press := InputEventKey.new()
	press.physical_keycode = KEY_T
	press.pressed = true
	root.push_input(press,true)
	await capture("02-mounted")
	_assert("mounted on the normal keyboard interaction",truck.mounted)
	steer(_heading(Vector3.BACK))
	await frame_for(100)
	await capture("03-through-shutter")
	_assert("truck drives through the shutter",truck.body.position.z > 8. and not field.field_env.is_inside_camp(truck.body.position))
	var ore_at := Vector2(truck.body.position.x,truck.body.position.z+3.32)
	var ore: Node3D = field.add_resource_source("filmed-center-metal","metal",ore_at)
	for count in 114:
		await capture()
		if field.lifecycle.cooling.has("filmed-center-metal"): break
	steer(Vector2.ZERO)
	await frame_for(27)
	await capture("04-metal-collected")
	_assert("driven blades depleted the actual bank",is_instance_valid(ore) and field.lifecycle.cooling.has("filmed-center-metal"))
	_assert("all eight released metal bundles are aboard",truck.state().cargo.get("metal",0)==8)
	var stored: int = field.inventory.stored.metal
	steer(_heading(Vector3.FORWARD))
	var docked_and_closed := false
	for count in 335:
		await capture()
		if truck.parked() and truck.opening <= .001 and not field.inventory.stored.metal==stored:
			docked_and_closed = true
			break
	await capture("05-docked-held-stick")
	await frame_for(24)
	var envelope: Rect2 = truck._garage_hull(truck.body.position,truck.body.basis)
	_assert("held joystick parked with closed shutter and full hull clear",docked_and_closed and truck.mounted and envelope.end.y<=truck.BAY_DEPTH+.002 and envelope.end.y>=truck.BAY_DEPTH-.08)
	_assert("unload preserved exactly eight bundles",truck.state().cargo.is_empty() and field.inventory.stored.metal==stored+8)
	steer(Vector2.ZERO)
	await frame_for(20)

func pinch_view() -> void:
	var center := Vector2(root.get_visible_rect().size)*Vector2(.48,.45)
	field.clear_touch()
	touch(6,center-Vector2(18,0),true)
	touch(7,center+Vector2(18,0),true)
	await physics_frame
	for i in 12:
		var gap := 18.+float(i+1)*5.
		for j in 2:
			var drag := InputEventScreenDrag.new()
			drag.index = 6+j
			drag.position = center+Vector2(gap*(-1. if j==0 else 1.),0)
			root.push_input(drag,true)
		await physics_frame
	touch(6,center-Vector2(78,0),false)
	touch(7,center+Vector2(78,0),false)
	for i in 5: await physics_frame
	_assert("ordinary pinch reaches a two-times view",field.get_zoom_ratio()>=1.99)
	await process_frame
	RenderingServer.force_draw(false)
	root.get_texture().get_image().save_jpg(run_at.path_join("06-pinch-2x.jpg"),.88)

func run() -> void:
	field = load("res://field_opening.tscn").instantiate()
	root.add_child(field)
	camera = field.camera
	truck = field.snow_truck
	origin = root.get_visible_rect().size * Vector2(.28,.71)
	for count in 9:await physics_frame
	clear_ambient_threats()
	movie.connect_to_host("127.0.0.1",int(OS.get_environment("T07_FRAME_PORT")))
	for attempt in 30:
		movie.poll()
		if movie.get_status() == StreamPeerTCP.STATUS_CONNECTED:break
		await process_frame
	if movie.get_status() != StreamPeerTCP.STATUS_CONNECTED:
		printerr("Could not open renderer stream")
		quit(2)
		return
	if capture_kind=="context":
		await context_route()
	else:
		await truck_route()
	movie.disconnect_from_host()
	if capture_kind=="context": await pinch_view()
	var result := {"mode":capture_kind,"renderer":RenderingServer.get_video_adapter_name(),"viewport":[root.size.x,root.size.y],
		"frames":frames,"rendered_video_frames":video_frames,"video_sample_stride":frame_step,"first_physics_frame":start_tick,"last_physics_frame":previous_tick,"nonconsecutive_physics_samples":skipped_ticks,
		"checks":checks,"events":capture_events,"source":{"context":FileAccess.get_sha256("res://field_context_director.gd"),"truck":FileAccess.get_sha256("res://field_snow_truck.gd")}}
	var trace := FileAccess.open(run_at.path_join("Gameplay.json"),FileAccess.WRITE)
	trace.store_string(JSON.stringify(result,"  "))
	trace.close()
	print("NATIVE_GAMEPLAY ", JSON.stringify(result))
	await _close_field()
	quit(int(checks.values().has(false)))
