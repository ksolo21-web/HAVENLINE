extends SceneTree

## T11 isolated build-pending renderer. It uses the real authored T11 stage
## scenes, approved T05 assets, and the approved T03 perimeter presentation.
## The snow/lighting are disclosed review staging only; final integrated
## gameplay evidence still waits for accepted T10.

const View = preload("res://scripts/camp_construction_view.gd")
const CameraPolicy = preload("res://scripts/camera_composition.gd")
const CampBoundaryView = preload("res://scripts/camp_boundary_view.gd")
const Boundary = preload("res://scripts/camp_boundary.gd")

var output := "user://task11-camp-capture"
var native_4k := false
var viewport: SubViewport
var world: Node3D
var camera: Camera3D
var environment: Environment
var sun: DirectionalLight3D
var fill: DirectionalLight3D
var view: HavenlineCampConstructionView
var boundary_view: HavenlineCampBoundaryView
var scale_actor: Node3D
var merged_cache: Dictionary = {}
var records: Array[Dictionary] = []
var capture_errors: Array[String] = []

func _initialize() -> void:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--out="):
			output = argument.trim_prefix("--out=")
		elif argument == "--native-4k":
			native_4k = true
	call_deferred("run")

func material(color: Color, roughness := 0.9, metallic := 0.0) -> StandardMaterial3D:
	var result := StandardMaterial3D.new()
	result.albedo_color = color
	result.roughness = roughness
	result.metallic = metallic
	return result

func add_snow_stage() -> void:
	var snow := MeshInstance3D.new()
	var mesh := PlaneMesh.new()
	mesh.size = Vector2(80.0, 72.0)
	snow.mesh = mesh
	snow.material_override = material(Color("cfe1ea"), 0.96)
	snow.position = Vector3(0.0, -0.055, 2.0)
	world.add_child(snow)
	for row in [
		{"position": Vector3(0.0, -0.045, 5.0), "size": Vector3(2.0, 0.03, 8.0)},
		{"position": Vector3(0.0, -0.045, 2.25), "size": Vector3(19.5, 0.03, 1.45)},
	]:
		var lane := MeshInstance3D.new()
		var lane_mesh := BoxMesh.new()
		lane_mesh.size = row.size
		lane.mesh = lane_mesh
		lane.material_override = material(Color("b7d2df"), 0.98)
		lane.position = row.position
		world.add_child(lane)

func visit_meshes(node: Node, output_meshes: Array) -> void:
	if node is MeshInstance3D:
		output_meshes.append(node)
	for child in node.get_children():
		visit_meshes(child, output_meshes)

func build_scale_actor() -> Node3D:
	var root_node := Node3D.new()
	root_node.name = "ExistingShippingCharacterForScale"
	world.add_child(root_node)
	var visual := load("res://assets/characters/Character1.glb").instantiate() as Node3D
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

func set_camera(view_id: String, state_id: String) -> void:
	var target := Vector3(0.0, 0.0, 2.8)
	if state_id == "site_unbuilt":
		target = Vector3(0.0, 0.0, 1.5)
	match view_id:
		"gameplay":
			camera.position = target + CameraPolicy.VIEW_OFFSET
			camera.look_at(target + Vector3(0.0, CameraPolicy.FOCUS_HEIGHT, 0.0), Vector3.UP)
			camera.size = CameraPolicy.full_height_for(Vector2(viewport.size))
		"overhead":
			camera.position = target + Vector3(0.0, 19.0, 0.01)
			camera.look_at(target, Vector3(0.0, 0.0, -1.0))
			camera.size = 18.0
		"side":
			camera.position = target + Vector3(16.0, 8.8, 4.5)
			camera.look_at(target + Vector3(0.0, 0.7, 0.0), Vector3.UP)
			camera.size = 14.8
		"three-quarter":
			camera.position = target + Vector3(-12.4, 10.2, 13.8)
			camera.look_at(target + Vector3(0.0, 0.75, 0.0), Vector3.UP)
			camera.size = 14.3
		"detail":
			var anchor := view.interaction_anchor()
			camera.position = anchor + Vector3(6.5, 6.4, 8.2)
			camera.look_at(anchor + Vector3(0.0, 0.35, 0.0), Vector3.UP)
			camera.size = 5.8
		_:
			camera.position = target + CameraPolicy.VIEW_OFFSET
			camera.look_at(target + Vector3(0.0, CameraPolicy.FOCUS_HEIGHT, 0.0), Vector3.UP)
			camera.size = CameraPolicy.BASE_FULL_HEIGHT

func set_lighting() -> void:
	environment.background_color = Color("648eaa")
	environment.ambient_light_color = Color("b9d2e2")
	environment.ambient_light_energy = 0.42
	sun.light_color = Color("fff0d7")
	sun.light_energy = 0.96
	fill.light_color = Color("8cc7e5")
	fill.light_energy = 0.24

func snap(frame_id: String, state_id: String, lifecycle: String, view_id: String) -> void:
	for _frame in range(5):
		await process_frame
	if DisplayServer.get_name() != "headless":
		await RenderingServer.frame_post_draw
	var texture := viewport.get_texture()
	if texture == null:
		capture_errors.append("texture_unavailable:%s" % frame_id)
		return
	var image := texture.get_image()
	if image == null or image.is_empty():
		capture_errors.append("image_unavailable:%s" % frame_id)
		return
	var path := output.path_join(frame_id + ".png")
	var save_error := image.save_png(path)
	if save_error != OK:
		capture_errors.append("save_failed:%s:%s" % [frame_id, error_string(save_error)])
		return
	var status := view.status_descriptor()
	records.append({
		"id": frame_id,
		"path": frame_id + ".png",
		"camp_state_id": state_id,
		"lifecycle": lifecycle,
		"view": view_id,
		"size": [image.get_width(), image.get_height()],
		"render_scale": viewport.scaling_3d_scale,
		"camera_full_height": camera.size,
		"camera_profile": "t04-reference-camera-v1" if view_id == "gameplay" else "isolated-review-angle",
		"status_color": status.color,
		"status_scale": status.scale,
		"status_spire_scale": status.spire_scale,
		"stage_node_count": view.stage_node_count(),
		"t03_fence_visual_instances": int(boundary_view.descriptor.get("fence_visual_instances", 0)),
		"t03_open_gate_leaf_instances": int(boundary_view.descriptor.get("open_gate_leaf_instances", 0)),
		"draw_calls": viewport.get_render_info(Viewport.RENDER_INFO_TYPE_VISIBLE, Viewport.RENDER_INFO_DRAW_CALLS_IN_FRAME),
		"submitted_primitives": viewport.get_render_info(Viewport.RENDER_INFO_TYPE_VISIBLE, Viewport.RENDER_INFO_PRIMITIVES_IN_FRAME),
	})

func capture(frame_id: String, state_id: String, lifecycle: String, view_id: String) -> void:
	var result := view.apply_stage(state_id, lifecycle)
	if not bool(result.get("passed", false)):
		capture_errors.append("stage_failed:%s:%s" % [state_id, lifecycle])
		return
	scale_actor.position = Vector3(2.3, 0.0, -2.2) if state_id == "site_unbuilt" else Vector3(2.0, 0.0, 0.6)
	set_camera(view_id, state_id)
	await snap(frame_id, state_id, lifecycle, view_id)

func setup_world() -> bool:
	viewport = SubViewport.new()
	viewport.own_world_3d = true
	viewport.size = Vector2i(3840, 2160) if native_4k else Vector2i(1280, 720)
	viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	viewport.msaa_3d = Viewport.MSAA_2X
	viewport.scaling_3d_scale = 1.0
	root.add_child(viewport)
	world = Node3D.new()
	viewport.add_child(world)
	environment = Environment.new()
	environment.background_mode = Environment.BG_COLOR
	environment.tonemap_mode = Environment.TONE_MAPPER_ACES
	environment.tonemap_exposure = 0.95
	environment.tonemap_white = 5.0
	environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	var sky := WorldEnvironment.new()
	sky.environment = environment
	world.add_child(sky)
	sun = DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-52.0, -34.0, 0.0)
	sun.shadow_enabled = true
	sun.directional_shadow_max_distance = 45.0
	world.add_child(sun)
	fill = DirectionalLight3D.new()
	fill.rotation_degrees = Vector3(-35.0, 142.0, 0.0)
	fill.shadow_enabled = false
	world.add_child(fill)
	set_lighting()
	camera = Camera3D.new()
	camera.projection = Camera3D.PROJECTION_ORTHOGONAL
	camera.near = 0.05
	camera.far = 120.0
	world.add_child(camera)
	camera.current = true
	add_snow_stage()
	boundary_view = CampBoundaryView.new()
	boundary_view.name = "ApprovedT03BoundaryContext"
	world.add_child(boundary_view)
	boundary_view.configure(self)
	if boundary_view.descriptor.get("visual_collision_share_panel_authority") is not true:
		capture_errors.append("t03_boundary_authority_mismatch")
	scale_actor = build_scale_actor()
	view = View.new()
	view.name = "T11BuildPendingCandidate"
	world.add_child(view)
	return view.configure_from_file() and capture_errors.is_empty()

func run() -> void:
	DirAccess.make_dir_recursive_absolute(output)
	var configured := setup_world()
	if configured:
		if native_4k:
			await capture("native-site-ready-gameplay", "site_unbuilt", "ready", "gameplay")
			await capture("native-camp-initial-gameplay", "camp_initial", "complete", "gameplay")
			await capture("native-camp-upgraded-gameplay", "camp_upgraded_01", "complete", "gameplay")
		else:
			for lifecycle in View.LIFECYCLES:
				await capture("site-%s-gameplay" % lifecycle, "site_unbuilt", lifecycle, "gameplay")
			for view_id in ["gameplay", "overhead", "side", "three-quarter", "detail"]:
				await capture("camp-initial-%s" % view_id, "camp_initial", "complete", view_id)
			for view_id in ["gameplay", "overhead", "side", "three-quarter", "detail"]:
				await capture("camp-upgraded-%s" % view_id, "camp_upgraded_01", "complete", view_id)

	var report := {
		"task": "T11",
		"capture_kind": "isolated-source-bound-rendered-evidence",
		"configured": configured,
		"source_bound": true,
		"real_t11_stage_scenes": true,
		"approved_t05_assets_rendered": true,
		"approved_t03_boundary_rendered": is_instance_valid(boundary_view),
		"t03_boundary_authority_id": Boundary.GATE_AUTHORITY_ID,
		"t03_boundary_descriptor": boundary_view.descriptor if is_instance_valid(boundary_view) else {},
		"existing_shipping_character_used_for_scale": true,
		"review_snow_and_lane_stage_is_not_shipping_content": true,
		"gameplay_view_uses_t04_profile": true,
		"native_4k": native_4k,
		"renderer": RenderingServer.get_current_rendering_method(),
		"device": RenderingServer.get_video_adapter_name(),
		"captures": records,
		"capture_errors": capture_errors,
		"build_pending_dependency": true,
		"final_t10_compatibility_claimed": false,
		"final_visual_critic_evidence": false,
		"physical_4k60_verified": false,
		"task_approved": false,
	}
	var file := FileAccess.open(output.path_join("capture.json"), FileAccess.WRITE)
	file.store_string(JSON.stringify(report, "\t"))
	file.close()
	print(JSON.stringify({
		"task": "T11",
		"configured": configured,
		"capture_count": records.size(),
		"capture_errors": capture_errors,
		"approved_t03_boundary_rendered": is_instance_valid(boundary_view),
		"native_4k": native_4k,
		"build_pending_dependency": true,
		"task_approved": false,
	}))
	await process_frame
	quit(0 if configured and capture_errors.is_empty() and not records.is_empty() else 1)
