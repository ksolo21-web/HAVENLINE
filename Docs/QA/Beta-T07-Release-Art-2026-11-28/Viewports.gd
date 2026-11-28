extends "res://tests/qa_snow_truck.gd"

var destination := OS.get_environment("T07_VIEWPORTS_OUT")
var witnesses := {}

func _initialize() -> void:
	run.call_deferred()

func capture(size: Vector2i, name: String) -> void:
	root.size = size
	for _step in 8: await physics_frame
	await process_frame
	RenderingServer.force_draw(false)
	var image := root.get_texture().get_image()
	_assert(name + " native raster matches requested size", image.get_size() == size)
	var save_result := image.save_jpg(destination.path_join(name+".jpg"),.87)
	_assert(name + " screenshot saved successfully", save_result == OK)
	witnesses[name] = {"raster": [image.get_width(), image.get_height()],
		"draw_calls":RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_DRAW_CALLS_IN_FRAME),
		"primitives": RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_PRIMITIVES_IN_FRAME),
		"objects": RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_OBJECTS_IN_FRAME),
		"texture_memory_mb": RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TEXTURE_MEM_USED)/1048576.}

func run() -> void:
	field = load("res://field_opening.tscn").instantiate()
	root.add_child(field)
	camera = field.camera
	truck = field.snow_truck
	for _step in 12: await physics_frame
	field.encounters.remaining = 900.
	for wolf in field.enemies.duplicate(): field.encounters._remove(wolf)
	await capture(Vector2i(540,1260),"phone-tall-opening")
	for id in ["center_hearth", "expansion_1", "storage_wood", "storage_stone", "storage_meat", "expansion_2", "camp_cooker", "saw_bench", "quarry_drill", "watchtower", "snow_garage", "snow_truck"]:
		_assert("funded "+id, _fund(id))
		for _step in 4: await physics_frame
	var south: Vector3 = field.gates[0].global_position
	field.actor.global_position = south + Vector3(0.,.008,1.15)
	field.previous_dry_position = field.actor.global_position
	origin = Vector2(root.get_visible_rect().size)*Vector2(.28,.71)
	steer(_heading(Vector3.FORWARD))
	for _step in 112:
		await physics_frame
		if field.actor.global_position.z < 2.65: break
	steer(Vector2.ZERO)
	_assert("entered the camp by the south gate using standard touch input", field.field_env.is_inside_camp(field.actor.global_position) and field.actor.global_position.z < 2.65)
	for _step in 18: await physics_frame
	await capture(Vector2i(540,1260),"folded-cover-camp")
	await capture(Vector2i(840,942),"foldable-open-camp")
	await capture(Vector2i(1024,768),"tablet-camp")
	print("T07_VIEWPORTS ",JSON.stringify({"renderer":RenderingServer.get_video_adapter_name(),
		"checks":checks,"layouts":witnesses,"field_art":FileAccess.get_sha256("res://field_environment.gd")}))
	await _close_field()
	quit(int(checks.values().has(false)))
