extends "res://tests/qa_snow_truck.gd"

var output_path := OS.get_environment("CANOPY_FIX_DIR")
var captures := {}
var movie := StreamPeerTCP.new()
var record_movie := int(OS.get_environment("CANOPY_MOVIE_PORT"))>0
var rendered_frames := 0
var last_recorded_tick := -1
var sample_gaps := 0


func _initialize() -> void:
	run.call_deferred()

func capture(name: String) -> void:
	await process_frame
	RenderingServer.force_draw(false)
	var image := root.get_texture().get_image()
	_assert(name + " uses the full gameplay raster", image.get_size()==root.size and image.save_jpg(output_path.path_join(name+".jpg"),.89)==OK)
	captures[name] = {"raster":[image.get_width(),image.get_height()],"zoom":field.get_zoom_ratio(),
		"player":pt(field.actor.global_position),"camera":pt(camera.global_position)}

func sequence_step() -> void:
	await physics_frame
	if not record_movie or Engine.get_physics_frames()%2!=0: return
	await process_frame
	var tick := Engine.get_physics_frames()
	if last_recorded_tick>=0 and tick!=last_recorded_tick+2: sample_gaps+=1
	last_recorded_tick=tick
	RenderingServer.force_draw(false)
	if movie.put_data(root.get_texture().get_image().save_jpg_to_buffer(.83))==OK:
		rendered_frames+=1

func start_movie() -> void:
	movie.connect_to_host("127.0.0.1",int(OS.get_environment("CANOPY_MOVIE_PORT")))
	for _step in 30:
		movie.poll()
		if movie.get_status()==StreamPeerTCP.STATUS_CONNECTED: break
		await process_frame
	_assert("continuous gameplay capture connected",movie.get_status()==StreamPeerTCP.STATUS_CONNECTED)

func pinch() -> void:
	var center := Vector2(root.get_visible_rect().size)*Vector2(.48,.45)
	field.clear_touch()
	touch(6,center-Vector2(18,0),true)
	touch(7,center+Vector2(18,0),true)
	await sequence_step()
	for index in 12:
		var gap := 18.+float(index+1)*5.
		for side in 2:
			var drag := InputEventScreenDrag.new()
			drag.index = 6+side
			drag.position = center+Vector2(gap*(-1. if side==0 else 1.),0)
			root.push_input(drag,true)
		await sequence_step()
	touch(6,center-Vector2(78,0),false)
	touch(7,center+Vector2(78,0),false)
	for _step in 8: await sequence_step()

func run() -> void:
	field = load("res://field_opening.tscn").instantiate()
	root.add_child(field)
	camera = field.camera
	truck = field.snow_truck
	for _step in 10: await physics_frame
	field.encounters.remaining = 900.
	for wolf in field.enemies.duplicate(): field.encounters._remove(wolf)
	var pad: Vector3 = field.carry.receivers.center_hearth.global_position
	field.actor.global_position = pad + Vector3(0.,.008,.33)
	field.previous_dry_position = field.actor.global_position
	for _step in 50: await physics_frame
	var sources := {}
	var base: int = field.CONIFERS.size()
	var matching_rows: Array[Dictionary] = []
	for row: Dictionary in field.forest.records:
		if int(row.variant)>=base and not row.get("occupied",false): matching_rows.append(row)
	for i in 3:
		var scene: PackedScene = field.field_env.pine_scenes[base+i]
		var dimensions: Vector2 = field.field_env.pine_shapes[base+i]
		var path := "res://assets/reference_forest/bank_pine_%d.glb" % (i+1)
		var copies := matching_rows.filter(func(row: Dictionary) -> bool: return int(row.variant)==base+i).size()
		_assert("bank %d is instanced from the tracked GLB" % (i+1), scene.resource_path==path and copies>0)
		sources[path] = {"sha256":FileAccess.get_sha256(path),"extent":[dimensions.x,dimensions.y],"active_rows":copies}
	await capture("01-Grove-normal")
	if record_movie:
		await start_movie()
		for _step in 18: await sequence_step()
	matching_rows.sort_custom(func(a: Dictionary, b: Dictionary) -> bool:
		return a.transform.origin.distance_squared_to(field.actor.global_position) < b.transform.origin.distance_squared_to(field.actor.global_position))
	var grove: Dictionary = matching_rows[0]
	var target: Vector3 = grove.transform.origin
	origin = Vector2(root.get_visible_rect().size)*Vector2(.28,.71)
	var before: Vector3 = field.actor.global_position
	for _step in 240:
		var heading: Vector3 = target-field.actor.global_position
		heading.y=0
		if heading.length()<=2.9: break
		steer(_heading(heading.normalized()))
		await sequence_step()
	steer(Vector2.ZERO)
	for _step in 28: await sequence_step()
	_assert("standard touch reached the bank", before.distance_to(field.actor.global_position)>1. and field.actor.global_position.distance_to(target)<3.25)
	_assert("near grove switches to the same harvest asset", is_instance_valid(grove.live) and not grove.proxy_visible and grove.live.crown_size.is_equal_approx(field.field_env.pine_shapes[grove.variant]))
	if not record_movie: await capture("02-Grove-approach")
	await pinch()
	_assert("standard two-finger pinch reached two-times zoom",field.get_zoom_ratio()>=1.98)
	if record_movie:
		for _step in 38: await sequence_step()
		movie.disconnect_from_host()
		_assert("retained at least two seconds of consecutive gameplay",rendered_frames>=60 and sample_gaps==0)
	await capture("03-Grove-pinch")
	print("CANOPY_EXACT ", JSON.stringify({"movie_frames":rendered_frames,"sample_gaps":sample_gaps,"checks":checks,"sources":sources,"captures":captures,"renderer":RenderingServer.get_video_adapter_name()}))
	await _close_field()
	quit(int(checks.values().has(false)))
