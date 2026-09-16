extends SceneTree

const Transform = preload("res://scripts/world_transform.gd")
const TransformView = preload("res://scripts/world_transform_view.gd")

var output := "user://task10-world-transform"
var candidate := "local-working-tree"
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

	target_mesh = MeshInstance3D.new()
	var box := BoxMesh.new()
	box.size = Vector3(2.4, 1.4, 2.4)
	target_mesh.mesh = box
	target_mesh.position = Vector3(0.0, 0.72, 0.0)
	target_material = StandardMaterial3D.new()
	target_material.roughness = 0.58
	target_mesh.material_override = target_material
	world.add_child(target_mesh)

	state_label = Label3D.new()
	state_label.position = Vector3(0.0, 2.25, 0.0)
	state_label.font_size = 56
	state_label.outline_size = 10
	state_label.modulate = Color.WHITE
	state_label.text = "T10 FRAMEWORK FIXTURE"
	world.add_child(state_label)

	var disclaimer := Label3D.new()
	disclaimer.position = Vector3(0.0, 1.88, 0.0)
	disclaimer.font_size = 30
	disclaimer.outline_size = 7
	disclaimer.text = "LIFECYCLE EVIDENCE — NOT T11 CAMP CONTENT"
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
	camera.look_at(Vector3(0.0, 0.85, 0.0), Vector3.UP)

func lifecycle_color(lifecycle: String) -> Color:
	match lifecycle:
		"ready": return Color("4f6b7a")
		"preview": return Color("e7a64a")
		"committing": return Color("5fa8d3")
		"complete": return Color("66b86a")
		_: return Color("777777")

func capture_state(name: String, descriptor: Dictionary) -> bool:
	target_material.albedo_color = lifecycle_color(String(descriptor.lifecycle))
	state_label.text = "T10 • %s" % String(descriptor.lifecycle).to_upper()
	for angle in ["front", "three-quarter"]:
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

func run() -> void:
	DirAccess.make_dir_recursive_absolute(output)
	root.size = Vector2i(1280, 720)
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
	world.add_child(view)
	if not view.configure("capture-anchor"):
		print(JSON.stringify({"passed": false, "error": "view_setup_failed"}))
		quit(1)
		return

	var inventory := {"wood": 20, "stone": 12, "metal": 2, "fuel": 1}
	view.set_ready()
	if not await capture_state("ready", view.descriptor()):
		print(JSON.stringify({"passed": false, "error": "ready_capture_failed"}))
		quit(1)
		return

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

	var manifest := {
		"task_id": "T10",
		"candidate": candidate,
		"mode": "dependency-independent-lifecycle-fixture",
		"fixture_only": true,
		"t11_content": false,
		"real_t09_adapter_bound": false,
		"record_count": records.size(),
		"states": ["ready", "preview", "committing", "complete"],
		"angles": ["front", "three-quarter"],
		"records": records,
		"final_target": engine.descriptor().targets["capture-anchor"].duplicate(true),
		"integration_allowed": false,
		"task_approved": false,
		"passed": records.size() == 8 and engine.descriptor().targets["capture-anchor"].state == "foundation",
	}
	var file := FileAccess.open(output.path_join("manifest.json"), FileAccess.WRITE)
	if file:
		file.store_string(JSON.stringify(manifest, "  "))
	print(JSON.stringify(manifest))
	quit(0 if manifest.passed else 1)
