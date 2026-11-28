extends "res://tests/field_route.gd"
const Session = preload("res://tests/lifecycle_test_profile.gd")
var output := OS.get_environment("HAVENLINE_PATCH_EVIDENCE")
var rows := []

func _initialize() -> void:
	run.call_deferred()

func picture(label: String, at: Vector3, zoom: float) -> void:
	field.actor.global_position=at
	field.previous_dry_position=at
	field.actor.velocity=Vector3.ZERO
	field.set_zoom_ratio(zoom)
	for i in 54:await physics_frame
	await process_frame
	RenderingServer.force_draw(false,1./60.)
	var still := root.get_texture().get_image()
	still.save_jpg(output.path_join(label+".jpg"),.91)
	var network = field.settlement_loop.conveyors.network
	var kits: Array = network.routes.keys()
	kits.sort()
	rows.append({"file":label+".jpg","size":[still.get_width(),still.get_height()],
		"scale":root.scaling_3d_scale,"zoom":field.get_zoom_ratio(),"feet":pt(field.actor.global_position),
		"camera":pt(camera.global_position),"paid_routes":kits,"line_load":field.inventory.settlement.line_load.duplicate(),
		"calls":RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_DRAW_CALLS_IN_FRAME),
		"triangles":RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_PRIMITIVES_IN_FRAME)})

func run() -> void:
	field=load("res://field_opening.tscn").instantiate()
	root.add_child(field)
	current_scene=field
	camera = field.camera
	for i in 8:await physics_frame
	var active = field.settlement_loop.conveyors.network
	var count := int(active.routes.size())
	await picture("Cooker-1x",Vector3(.82,0,-4.83),1.)
	await picture("Cooker-2x",Vector3(.82,0,-4.83),2.)
	await picture("Cooker-to-counter",Vector3(2.98,0,-4.1),1.45)
	await picture("Warehouse-feed-1x",Vector3(-4.6,0,-1.4),1.)
	await picture("Warehouse-feed-2x",Vector3(-4.6,0,-1.4),2.)
	await picture("Public-floor",Vector3(1.12,0,-1.95),1.)
	var receipt := FileAccess.open(output.path_join("Transport.json"),FileAccess.WRITE)
	receipt.store_string(JSON.stringify({"renderer":RenderingServer.get_video_adapter_name(),"views":rows,
		"initial_connected_lanes":count},"  "))
	receipt.close()
	await Session.drain_field_audio(self,field)
	field.queue_free()
	for i in 4:await process_frame
	quit(int(count!=8))
