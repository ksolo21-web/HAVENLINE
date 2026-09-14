extends SceneTree

const Motion = preload("res://scripts/character1_motion.gd")
const SOURCE := "res://assets/characters/Character1.glb"

var output := "user://task06-capture"
var candidate := ""
var native_4k := false
var captures: Array[Dictionary] = []
var stage: Node3D
var actor: Node3D
var visual: Node3D
var player: AnimationPlayer
var skeleton: Skeleton3D
var camera: Camera3D

func _initialize() -> void:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--out="):
			output = argument.trim_prefix("--out=")
		elif argument.begins_with("--candidate="):
			candidate = argument.trim_prefix("--candidate=")
		elif argument == "--native-4k":
			native_4k = true
	if candidate.is_empty():
		candidate = "0000000000000000000000000000000000000000"
	call_deferred("run")

func find_skeleton(node: Node) -> Skeleton3D:
	if node is Skeleton3D:
		return node
	for child in node.get_children():
		var found := find_skeleton(child)
		if found:
			return found
	return null

func gather_meshes(node: Node, meshes: Array) -> void:
	if node is MeshInstance3D:
		meshes.append(node)
	for child in node.get_children():
		gather_meshes(child, meshes)

func normalize_character() -> void:
	var meshes: Array = []
	gather_meshes(visual, meshes)
	var bounds := AABB()
	var first := true
	for mesh in meshes:
		var box: AABB = actor.global_transform.affine_inverse() * mesh.global_transform * mesh.get_aabb()
		bounds = box if first else bounds.merge(box)
		first = false
	var factor := 1.75 / maxf(0.01, bounds.size.y)
	visual.scale *= factor
	visual.position = Vector3(-bounds.get_center().x, -bounds.position.y, -bounds.get_center().z) * factor

func setup_stage() -> void:
	stage = Node3D.new()
	stage.name = "T06EvidenceStage"
	root.add_child(stage)
	var world := WorldEnvironment.new()
	var environment := Environment.new()
	environment.background_mode = Environment.BG_COLOR
	environment.background_color = Color("#14283b")
	environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	environment.ambient_light_color = Color("#dceeff")
	environment.ambient_light_energy = 0.82
	environment.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	world.environment = environment
	stage.add_child(world)
	var key := DirectionalLight3D.new()
	key.rotation_degrees = Vector3(-48, -32, 0)
	key.light_color = Color("#fff2df")
	key.light_energy = 1.38
	key.shadow_enabled = true
	stage.add_child(key)
	var fill := DirectionalLight3D.new()
	fill.rotation_degrees = Vector3(-25, 145, 0)
	fill.light_color = Color("#9fcfff")
	fill.light_energy = 0.48
	fill.shadow_enabled = false
	stage.add_child(fill)
	var ground := MeshInstance3D.new()
	var plane := PlaneMesh.new()
	plane.size = Vector2(10, 10)
	var material := StandardMaterial3D.new()
	material.albedo_color = Color("#dbeeff")
	material.roughness = 0.93
	plane.material = material
	ground.mesh = plane
	ground.position.y = -0.012
	stage.add_child(ground)
	actor = Node3D.new()
	actor.name = "Character1"
	stage.add_child(actor)
	visual = load(SOURCE).instantiate()
	actor.add_child(visual)
	normalize_character()
	var installed := Motion.install(actor, "player_lead")
	assert(installed.passed, str(installed.errors))
	player = installed.player
	skeleton = installed.skeleton
	camera = Camera3D.new()
	camera.current = true
	camera.fov = 34.0
	stage.add_child(camera)
	set_view("front")

func set_view(view: String, detail := "body") -> void:
	var focus := Vector3(0, 0.92, 0)
	var radius := 4.15
	if detail == "feet":
		focus = Vector3(0, 0.22, 0)
		radius = 2.15
	elif detail == "hands":
		focus = Vector3(0, 1.05, -0.08)
		radius = 2.35
	match view:
		"front": camera.position = focus + Vector3(0, 0.42, radius)
		"rear": camera.position = focus + Vector3(0, 0.42, -radius)
		"left": camera.position = focus + Vector3(-radius, 0.42, 0)
		"right": camera.position = focus + Vector3(radius, 0.42, 0)
		"three-quarter": camera.position = focus + Vector3(radius * 0.70, 0.42, radius * 0.70)
		"overhead": camera.position = focus + Vector3(0.001, radius, 0.001)
		_: camera.position = focus + Vector3(0, 0.42, radius)
	camera.look_at(focus)

func snap(relative: String, clip: String, phase: float, view: String, category: String, detail := "body") -> void:
	set_view(view, detail)
	await process_frame
	await RenderingServer.frame_post_draw
	var image := get_root().get_texture().get_image()
	var path := output.path_join(relative)
	DirAccess.make_dir_recursive_absolute(path.get_base_dir())
	assert(image.save_png(path) == OK)
	captures.append({
		"file": relative, "clip": clip, "phase": phase, "view": view,
		"category": category, "detail": detail,
		"resolution": [image.get_width(), image.get_height()],
		"draw_calls": get_root().get_render_info(Viewport.RENDER_INFO_TYPE_VISIBLE, Viewport.RENDER_INFO_DRAW_CALLS_IN_FRAME),
		"submitted_primitives": get_root().get_render_info(Viewport.RENDER_INFO_TYPE_VISIBLE, Viewport.RENDER_INFO_PRIMITIVES_IN_FRAME),
		"source_sha256": Motion.SOURCE_GLTF_SHA256
	})

func capture_phase(clip: String, phase: float, view: String, category: String, detail := "body") -> void:
	var name := Motion.LIBRARY + "/" + clip
	var animation := player.get_animation(name)
	player.play(name)
	player.seek(animation.length * phase, true)
	player.speed_scale = 0.0
	skeleton.force_update_all_bone_transforms()
	await snap("%s/%s-%03d.png" % [clip, view + ("-" + detail if detail != "body" else ""), roundi(phase * 100)], clip, phase, view, category, detail)

func capture_native_selection() -> void:
	for row in [
		["idle", 0.50, "front", "motion_cycle", "body"],
		["walk", 0.24, "three-quarter", "motion_cycle", "body"],
		["run", 0.49, "left", "contact_detail", "feet"],
		["chop", 0.56, "three-quarter", "contact_detail", "hands"],
		["rescue", 0.68, "right", "contact_detail", "body"],
		["turn_left_090", 0.52, "front", "motion_transition", "body"]
	]:
		await capture_phase(row[0], row[1], row[2], row[3], row[4])

func capture_full_review() -> void:
	for clip in Motion.LOOP_CLIPS:
		for index in range(17):
			await capture_phase(clip, float(index) / 16.0, "front", "motion_cycle")
		for phase in [0.0, 0.24, 0.49, 0.74]:
			for view in ["rear", "left", "right", "three-quarter"]:
				await capture_phase(clip, phase, view, "motion_cycle")
		if clip in ["walk", "run"]:
			for phase in [0.0, 0.12, 0.36, 0.49, 0.64, 0.86]:
				await capture_phase(clip, phase, "left", "contact_detail", "feet")
	for clip in Motion.TRANSITION_CLIPS:
		for index in range(9):
			await capture_phase(clip, float(index) / 8.0, "front", "motion_transition")
		await capture_phase(clip, 0.52, "three-quarter", "motion_transition")
	for clip in Motion.ACTION_CLIPS:
		for index in range(13):
			await capture_phase(clip, float(index) / 12.0, "front", "motion_cycle")
		var contact := float(Motion.ACTION_SPECS[clip].contact)
		for view in ["rear", "left", "right", "three-quarter"]:
			await capture_phase(clip, contact, view, "contact_detail")
		await capture_phase(clip, contact, "three-quarter", "contact_detail", "hands")
	for view in ["front", "rear", "left", "right", "three-quarter", "overhead"]:
		await capture_phase("idle", 0.50, view, "gameplay_state", "gameplay")

func run() -> void:
	DirAccess.make_dir_recursive_absolute(output)
	setup_stage()
	if native_4k:
		await capture_native_selection()
	else:
		await capture_full_review()
	var metadata := {
		"task":"T06-character1-motion-v1", "candidate_commit":candidate,
		"source_path":SOURCE, "source_sha256":FileAccess.get_sha256(SOURCE),
		"source_expected_sha256":Motion.SOURCE_GLTF_SHA256,
		"source_immutable":FileAccess.get_sha256(SOURCE) == Motion.SOURCE_GLTF_SHA256,
		"library":Motion.LIBRARY, "captures":captures,
		"full_review":not native_4k, "native_3840x2160_scale1":native_4k,
		"renderer":RenderingServer.get_current_rendering_method(),
		"device":RenderingServer.get_video_adapter_name(),
		"visible_meshes":2, "visible_materials":2, "animated_rigs_active":1,
		"physics_active_bodies":0, "npc_companion_active_population":0,
		"measurement_method":"Godot Viewport visible-frame counters plus exact staged scene inventory",
		"known_unmeasured_fields":["cpu_frame_ms","gpu_frame_ms","texture_gpu_memory_mb"],
		"contact_contract":actor.get_meta("t06_motion_contract"),
		"physical_device_certified":false, "task_approved":false
	}
	var file := FileAccess.open(output.path_join("capture.json"), FileAccess.WRITE)
	file.store_string(JSON.stringify(metadata, "\t"))
	file.close()
	print(JSON.stringify({"task":metadata.task,"captures":captures.size(),"source_immutable":metadata.source_immutable,"native_4k":native_4k}))
	quit(0 if metadata.source_immutable else 1)
