extends SceneTree

## Isolated T05 quick-look harness. It renders the real authored GLBs with an
## existing shipping character for scale. Primitive floor/water shapes are
## disclosed review staging only; integrated gameplay evidence is a later gate.

const StationKit = preload("res://scripts/station_kit.gd")

var output := "user://task05-station-kit"
var native := false
var viewport: SubViewport
var world: Node3D
var camera: Camera3D
var environment: Environment
var sun: DirectionalLight3D
var fill: DirectionalLight3D
var kit: HavenlineStationKit
var scale_actor: Node3D
var stage_nodes: Array[Node3D] = []
var records: Array = []

func _initialize() -> void:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--out="):
			output = argument.trim_prefix("--out=")
		if argument == "--native-4k":
			native = true
	call_deferred("run")

func material(color: Color, roughness := 0.82, metallic := 0.0) -> StandardMaterial3D:
	var result := StandardMaterial3D.new()
	result.albedo_color = color
	result.roughness = roughness
	result.metallic = metallic
	return result

func stage_mesh(mesh: Mesh, mat: Material, position: Vector3) -> MeshInstance3D:
	var instance := MeshInstance3D.new()
	instance.mesh = mesh
	instance.material_override = mat
	instance.position = position
	instance.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON
	world.add_child(instance)
	stage_nodes.append(instance)
	return instance

func build_stage() -> void:
	var snow := PlaneMesh.new()
	snow.size = Vector2(38.0, 36.0)
	stage_mesh(snow, material(Color("d8eaf1"), 0.92), Vector3(0.0, -0.10, 0.0))

func clear_stage_accents() -> void:
	while stage_nodes.size() > 1:
		var node: Node3D = stage_nodes.pop_back()
		node.free()

func camp_stage() -> void:
	clear_stage_accents()
	var floor := BoxMesh.new()
	floor.size = Vector3(23.6, 0.10, 11.4)
	stage_mesh(floor, material(Color("b97651"), 0.94), Vector3(0.0, -0.04, 2.8))
	var snow_bank := TorusMesh.new()
	snow_bank.inner_radius = 10.8
	snow_bank.outer_radius = 11.2
	snow_bank.rings = 32
	snow_bank.ring_segments = 10
	stage_mesh(snow_bank, material(Color("edf7fa"), 0.96), Vector3(0.0, 0.02, 2.8))

func lakeshore_stage() -> void:
	clear_stage_accents()
	var water := PlaneMesh.new()
	water.size = Vector2(34.0, 8.2)
	stage_mesh(water, material(Color("1a91b9"), 0.22, 0.08), Vector3(0.0, -0.07, -7.2))
	var bank := BoxMesh.new()
	bank.size = Vector3(29.0, 0.10, 1.8)
	stage_mesh(bank, material(Color("aacfdc"), 0.86), Vector3(0.0, -0.03, -11.8))

func visit_meshes(node: Node, output_meshes: Array) -> void:
	if node is MeshInstance3D:
		output_meshes.append(node)
	for child in node.get_children():
		visit_meshes(child, output_meshes)

func build_scale_actor() -> Node3D:
	var root_node := Node3D.new()
	root_node.name = "ExistingShippingCharacterForScale"
	world.add_child(root_node)
	var visual: Node3D = load("res://assets/characters/Character1.glb").instantiate()
	root_node.add_child(visual)
	var meshes: Array = []
	visit_meshes(visual, meshes)
	var bounds := AABB()
	var first := true
	for mesh_node: MeshInstance3D in meshes:
		var box: AABB = root_node.global_transform.affine_inverse() * mesh_node.global_transform * mesh_node.get_aabb()
		bounds = box if first else bounds.merge(box)
		first = false
	var factor := 1.75 / maxf(0.01, bounds.size.y)
	visual.scale *= factor
	visual.position = Vector3(-bounds.get_center().x, -bounds.position.y, -bounds.get_center().z) * factor
	return root_node

func reset_kit() -> void:
	if is_instance_valid(kit):
		kit.free()
	kit = StationKit.new()
	kit.name = "IsolatedT05Candidate"
	world.add_child(kit)

func place_single(asset_id: String, position := Vector3.ZERO, rotation_y := 0.0) -> Node3D:
	reset_kit()
	var asset := kit.instantiate_asset(asset_id)
	asset.position = position
	asset.rotation.y = rotation_y
	kit.placed.append(asset)
	return asset

func set_camera(target: Vector3, view: String, full_height: float) -> void:
	var offset := Vector3(10.2, 11.8, 14.2)
	if view == "reverse":
		offset = Vector3(-10.2, 10.7, -14.2)
	elif view == "side":
		offset = Vector3(14.2, 9.8, 5.0)
	camera.position = target + offset
	camera.look_at(target + Vector3(0.0, 0.75, 0.0), Vector3.UP)
	camera.size = full_height

func set_condition(condition: String) -> void:
	match condition:
		"night":
			environment.background_color = Color("16263f")
			environment.ambient_light_color = Color("6886ad")
			environment.ambient_light_energy = 0.30
			sun.light_color = Color("7898cb")
			sun.light_energy = 0.34
			fill.light_color = Color("ff9b54")
			fill.light_energy = 0.55
		"blizzard":
			environment.background_color = Color("8caabb")
			environment.ambient_light_color = Color("c2d3dd")
			environment.ambient_light_energy = 0.52
			sun.light_color = Color("d9e6ec")
			sun.light_energy = 0.48
			fill.light_energy = 0.16
		_:
			environment.background_color = Color("6997b4")
			environment.ambient_light_color = Color("c8ddea")
			environment.ambient_light_energy = 0.55
			sun.light_color = Color("fff0d7")
			sun.light_energy = 1.05
			fill.light_color = Color("8dc8e8")
			fill.light_energy = 0.28

func snap(frame_id: String, arrangement: String, condition: String, view: String) -> void:
	for _frame in range(4):
		await process_frame
	if DisplayServer.get_name() != "headless":
		await RenderingServer.frame_post_draw
	var image := viewport.get_texture().get_image()
	var path := output.path_join(frame_id + ".png")
	image.save_png(path)
	records.append({
		"id": frame_id,
		"path": frame_id + ".png",
		"arrangement": arrangement,
		"condition": condition,
		"view": view,
		"size": [image.get_width(), image.get_height()],
		"render_scale": viewport.scaling_3d_scale,
		"camera_full_height": camera.size,
		"draw_calls": viewport.get_render_info(Viewport.RENDER_INFO_TYPE_VISIBLE, Viewport.RENDER_INFO_DRAW_CALLS_IN_FRAME),
		"submitted_primitives": viewport.get_render_info(Viewport.RENDER_INFO_TYPE_VISIBLE, Viewport.RENDER_INFO_PRIMITIVES_IN_FRAME)
	})

func capture_arrangement(frame_id: String, arrangement: String, condition: String, view: String) -> void:
	reset_kit()
	kit.build_arrangement(arrangement)
	if arrangement == "camp":
		camp_stage()
		scale_actor.position = Vector3(1.4, 0.0, -2.0)
		set_camera(Vector3(0.0, 0.0, 2.8), view, 14.3)
	else:
		lakeshore_stage()
		scale_actor.position = Vector3(-8.1, 0.0, -13.5)
		set_camera(Vector3(3.0, 0.0, -14.0), view, 15.3)
	scale_actor.visible = true
	set_condition(condition)
	await snap(frame_id, arrangement, condition, view)

func capture_single(frame_id: String, asset_id: String, condition: String, view: String, full_height := 4.6) -> void:
	camp_stage()
	place_single(asset_id)
	scale_actor.position = Vector3(2.1, 0.0, 1.5)
	scale_actor.visible = true
	set_camera(Vector3(0.0, 0.0, 0.0), view, full_height)
	set_condition(condition)
	await snap(frame_id, asset_id, condition, view)

func setup_world() -> void:
	viewport = SubViewport.new()
	viewport.own_world_3d = true
	viewport.size = Vector2i(3840, 2160) if native else Vector2i(1280, 720)
	viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	viewport.msaa_3d = Viewport.MSAA_2X
	viewport.scaling_3d_scale = 1.0
	root.add_child(viewport)
	world = Node3D.new()
	viewport.add_child(world)
	environment = Environment.new()
	environment.background_mode = Environment.BG_COLOR
	environment.tonemap_mode = Environment.TONE_MAPPER_ACES
	environment.tonemap_exposure = 1.30
	environment.tonemap_white = 5.0
	environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	var sky := WorldEnvironment.new()
	sky.environment = environment
	world.add_child(sky)
	sun = DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-52.0, -34.0, 0.0)
	sun.shadow_enabled = true
	sun.directional_shadow_max_distance = 42.0
	world.add_child(sun)
	fill = DirectionalLight3D.new()
	fill.rotation_degrees = Vector3(-35.0, 142.0, 0.0)
	fill.shadow_enabled = false
	world.add_child(fill)
	camera = Camera3D.new()
	camera.projection = Camera3D.PROJECTION_ORTHOGONAL
	camera.near = 0.05
	camera.far = 100.0
	world.add_child(camera)
	camera.current = true
	build_stage()
	scale_actor = build_scale_actor()

func run() -> void:
	DirAccess.make_dir_recursive_absolute(output)
	setup_world()
	if native:
		await capture_arrangement("native-camp-day", "camp", "day", "front")
		await capture_arrangement("native-lakeshore-day", "lakeshore", "day", "front")
		await capture_single("native-hearth-day", "hearth_vessel", "day", "front", 4.4)
	else:
		await capture_arrangement("camp-day-front", "camp", "day", "front")
		await capture_arrangement("camp-day-reverse", "camp", "day", "reverse")
		await capture_arrangement("camp-night-front", "camp", "night", "front")
		await capture_arrangement("camp-blizzard-side", "camp", "blizzard", "side")
		await capture_arrangement("lakeshore-day-front", "lakeshore", "day", "front")
		await capture_arrangement("lakeshore-day-reverse", "lakeshore", "day", "reverse")
		await capture_arrangement("lakeshore-night-front", "lakeshore", "night", "front")
		await capture_single("close-hearth-front", "hearth_vessel", "day", "front", 4.4)
		await capture_single("close-counter-reverse", "service_counter", "day", "reverse", 4.2)
		await capture_single("close-fishing-side", "fishing_rack", "day", "side", 4.4)
		await capture_single("close-processing-front", "cooker_processor", "day", "front", 4.4)
		await capture_single("close-defense-reverse", "defense_platform", "day", "reverse", 4.8)
	var report := {
		"task": "T05-station-kit-v1",
		"capture_kind": "isolated-component-quick-look",
		"shipping_main_call_site_exercised": false,
		"primitive_stage_is_not_shipping_content": true,
		"existing_shipping_character_used_for_scale": true,
		"source_bound": true,
		"catalog_sha256": FileAccess.get_sha256(StationKit.CATALOG_PATH),
		"renderer": RenderingServer.get_current_rendering_method(),
		"device": RenderingServer.get_video_adapter_name(),
		"captures": records,
		"physical_4k60_verified": false,
		"task_approved": false
	}
	var file := FileAccess.open(output.path_join("capture.json"), FileAccess.WRITE)
	file.store_string(JSON.stringify(report, "\t"))
	file.close()
	await process_frame
	quit()
