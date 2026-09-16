extends SceneTree

const Transform = preload("res://scripts/world_transform.gd")
const TransformView = preload("res://scripts/world_transform_view.gd")

var output := "user://task10-world-transform"
var candidate := "local-working-tree"
var capture_width := 1280
var capture_height := 720
var device_id := "baseline"
var device_check := false
var engine
var view
var world: Node3D
var camera: Camera3D
var target_mesh: MeshInstance3D
var target_material: StandardMaterial3D
var state_label: Label3D
var records: Array[Dictionary] = []

func _initialize() -> void:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--out="):
			output = argument.trim_prefix("--out=")
		elif argument.begins_with("--candidate="):
			candidate = argument.trim_prefix("--candidate=")
		elif argument.begins_with("--width="):
			capture_width = int(argument.trim_prefix("--width="))
		elif argument.begins_with("--height="):
			capture_height = int(argument.trim_prefix("--height="))
		elif argument.begins_with("--device-id="):
			device_id = argument.trim_prefix("--device-id=")
		elif argument == "--device-check":
			device_check = true
	call_deferred("run")

func simulation_ack(intent: Dictionary) -> Dictionary:
	var receipt := intent.duplicate(true)
	receipt["authority_source"] = "simulation"
	receipt["authority_applied"] = true
	return receipt

func add_environment() -> void:
	var environment_node := WorldEnvironment.new()
	var environment := Environment.new()
	environment.background_mode = Environment.BG_COLOR
	environment.background_color = Color("101820")
	environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	environment.ambient_light_color = Color("d6e7f0")
	environment.ambient_light_energy = 0.65
	environment_node.environment = environment
	world.add_child(environment_node)

	var light := DirectionalLight3D.new()
	light.rotation_degrees = Vector3(-52.0, -28.0, 0.0)
	light.light_energy = 1.8
	light.shadow_enabled = true
	world.add_child(light)

func add_fixture_scene() -> void:
	var floor := MeshInstance3D.new()
	var plane := PlaneMesh.new()
	plane.size = Vector2(8.0, 8.0)
	floor.mesh = plane
	var floor_material := StandardMaterial3D.new()
	floor_material.albedo_color = Color("23323d")
	floor_material.roughness = 0.88
	floor.material_override = floor_material
	world.add_child(floor)

	# Neutral target stays visually constant. Lifecycle state must come from
	# world_transform_view.gd, not from the capture harness recoloring the target.
	target_mesh = MeshInstance3D.new()
	var box := BoxMesh.new()
	box.size = Vector3(2.4, 1.4, 2.4)
	target_mesh.mesh = box
	target_mesh.position = Vector3(0.0, 0.72, 0.0)
	target_material = StandardMaterial3D.new()
	target_material.albedo_color = Color("8e98a3")
	target_material.roughness = 0.58
	target_mesh.material_override = target_material
	world.add_child(target_mesh)

	state_label = Label3D.new()
	state_label.position = Vector3(0.0, 2.45, 0.0)
	state_label.font_size = 56
	state_label.outline_size = 10
	state_label.modulate = Color.WHITE
	state_label.text = "T10 FRAMEWORK FIXTURE"
	world.add_child(state_label)

	var disclaimer := Label3D.new()
	disclaimer.position = Vector3(0.0, 2.08, 0.0)
	disclaimer.font_size = 30
	disclaimer.outline_size = 7
	disclaimer.text = "VIEW-OWNED LIFECYCLE EVIDENCE — NOT T11 CAMP CONTENT"
	world.add_child(disclaimer)

	camera = Camera3D.new()
	camera.current = true
	camera.fov = 44.0
	world.add_child(camera)

func configure_camera(angle: String) -> void:
	if angle == "front":
		camera.position = Vector3(0.0, 3.5, 7.5)
	else:
		camera.position = Vector3(5.6, 3.8, 6.2)
	camera.look_at(Vector3(0.0, 0.9, 0.0), Vector3.UP)

func capture_state(name: String, descriptor: Dictionary, angles: Array = ["front", "three-quarter"]) -> bool:
	state_label.text = "T10 • %s" % String(descriptor.lifecycle).to_upper()
	for raw_angle in angles:
		var angle := String(raw_angle)
		configure_camera(angle)
		await process_frame
		await RenderingServer.frame_post_draw
		var image := root.get_texture().get_image()
		if image == null or image.is_empty():
			return false
		var filename := "%s-%s.png" % [name, angle]
		var error := image.save_png(output.path_join(filename))
		if error != OK:
			return false
		records.append({
			"state": name,
			"angle": angle,
			"file": filename,
			"size": [image.get_width(), image.get_height()],
			"view": descriptor.duplicate(true),
		})
	return true

func write_manifest(manifest: Dictionary) -> bool:
	var file := FileAccess.open(output.path_join("manifest.json"), FileAccess.WRITE)
	if file == null:
		return false
	file.store_string(JSON.stringify(manifest, "  "))
	return true

func run_device_check(inventory: Dictionary) -> void:
	view.set_ready()
	var preview: Dictionary = engine.preview_transform("framework_anchor_seed_to_foundation", "capture-anchor", inventory)
	if not preview.passed or not view.show_preview(preview) or not await capture_state("preview", view.descriptor(), ["front"]):
		print(JSON.stringify({"passed": false, "error": "device_preview_capture_failed", "device_id": device_id}))
		quit(1)
		return

	var intent: Dictionary = engine.commit_transform("device-%s-tx" % device_id, "framework_anchor_seed_to_foundation", "capture-anchor", inventory)
	if not intent.passed or not view.show_commit(intent) or not await capture_state("committing", view.descriptor(), ["front"]):
		print(JSON.stringify({"passed": false, "error": "device_commit_capture_failed", "device_id": device_id}))
		quit(1)
		return

	var final_view: Dictionary = view.descriptor()
	var manifest := {
		"task_id": "T10",
		"candidate": candidate,
		"mode": "dependency-independent-device-layout-fixture",
		"device_id": device_id,
		"logical_size": [capture_width, capture_height],
		"fixture_only": true,
		"t11_content": false,
		"target_color_static": true,
		"view_owns_lifecycle_visuals": true,
		"real_t09_adapter_bound": false,
		"record_count": records.size(),
		"states": ["preview", "committing"],
		"angles": ["front"],
		"records": records,
		"view_visual_node_count": int(final_view.visual_node_count),
		"view_visual_build_count": int(final_view.visual_build_count),
		"integration_allowed": false,
		"task_approved": false,
		"passed": records.size() == 2 and int(final_view.visual_node_count) == 4 and int(final_view.visual_build_count) == 1,
	}
	if not write_manifest(manifest):
		manifest["passed"] = false
		manifest["error"] = "device_manifest_write_failed"
	print(JSON.stringify(manifest))
	quit(0 if manifest.passed else 1)

func run() -> void:
	if capture_width <= 0 or capture_height <= 0:
		print(JSON.stringify({"passed": false, "error": "invalid_capture_size"}))
		quit(1)
		return
	DirAccess.make_dir_recursive_absolute(output)
	root.size = Vector2i(capture_width, capture_height)
	world = Node3D.new()
	root.add_child(world)
	add_environment()
	add_fixture_scene()

	engine = Transform.new()
	if not engine.configure_from_file() or not engine.register_target("capture-anchor", "seed"):
		print(JSON.stringify({"passed": false, "error": "engine_setup_failed"}))
		quit(1)
		return
	view = TransformView.new()
	if not view.configure("capture-anchor"):
		print(JSON.stringify({"passed": false, "error": "view_setup_failed"}))
		quit(1)
		return
	world.add_child(view)
	await process_frame
	if not view.configure_readability(1.0):
		print(JSON.stringify({"passed": false, "error": "readability_setup_failed"}))
		quit(1)
		return

	var inventory := {"wood": 20, "stone": 12, "metal": 2, "fuel": 1}
	if device_check:
		await run_device_check(inventory)
		return

	view.set_ready()
	if not await capture_state("ready", view.descriptor()):
		print(JSON.stringify({"passed": false, "error": "ready_capture_failed"}))
		quit(1)
		return

	var blocked_preview: Dictionary = engine.preview_transform("framework_anchor_seed_to_foundation", "capture-anchor", {"wood": 7, "stone": 3})
	if blocked_preview.passed or not view.show_blocked(blocked_preview) or not await capture_state("blocked", view.descriptor()):
		print(JSON.stringify({"passed": false, "error": "blocked_capture_failed"}))
		quit(1)
		return

	view.set_ready()
	var preview: Dictionary = engine.preview_transform("framework_anchor_seed_to_foundation", "capture-anchor", inventory)
	if not preview.passed or not view.show_preview(preview) or not await capture_state("preview", view.descriptor()):
		print(JSON.stringify({"passed": false, "error": "preview_capture_failed"}))
		quit(1)
		return

	var intent: Dictionary = engine.commit_transform("capture-tx", "framework_anchor_seed_to_foundation", "capture-anchor", inventory)
	if not intent.passed or not view.show_commit(intent) or not await capture_state("committing", view.descriptor()):
		print(JSON.stringify({"passed": false, "error": "commit_capture_failed"}))
		quit(1)
		return

	var accepted: Dictionary = engine.accept_authoritative_receipt(simulation_ack(intent))
	if not accepted.passed or not view.mark_complete(accepted) or not await capture_state("complete", view.descriptor()):
		print(JSON.stringify({"passed": false, "error": "complete_capture_failed"}))
		quit(1)
		return

	var final_view: Dictionary = view.descriptor()
	var manifest := {
		"task_id": "T10",
		"candidate": candidate,
		"mode": "dependency-independent-view-owned-lifecycle-fixture",
		"fixture_only": true,
		"t11_content": false,
		"target_color_static": true,
		"view_owns_lifecycle_visuals": true,
		"real_t09_adapter_bound": false,
		"record_count": records.size(),
		"states": ["ready", "blocked", "preview", "committing", "complete"],
		"angles": ["front", "three-quarter"],
		"records": records,
		"view_visual_node_count": int(final_view.visual_node_count),
		"view_visual_build_count": int(final_view.visual_build_count),
		"final_target": engine.descriptor().targets["capture-anchor"].duplicate(true),
		"integration_allowed": false,
		"task_approved": false,
		"passed": records.size() == 10 and int(final_view.visual_node_count) == 4 and int(final_view.visual_build_count) == 1 and engine.descriptor().targets["capture-anchor"].state == "foundation",
	}
	if not write_manifest(manifest):
		manifest["passed"] = false
		manifest["error"] = "manifest_write_failed"
	print(JSON.stringify(manifest))
	quit(0 if manifest.passed else 1)
