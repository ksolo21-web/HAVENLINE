extends SceneTree

const Transform = preload("res://scripts/world_transform.gd")
const TransformView = preload("res://scripts/world_transform_view.gd")
const Simulation = preload("res://scripts/simulation.gd")

var output := "user://task10-world-transform"
var candidate := "local-working-tree"
var capture_width := 1280
var capture_height := 720
var device_id := "baseline"
var device_check := false
var production_evidence := false
var engine
var view
var world: Node3D
var camera: Camera3D
var target_mesh: MeshInstance3D
var target_material: StandardMaterial3D
var state_label: Label
var records: Array[Dictionary] = []
var projection_records: Array[Dictionary] = []
var simulation := Simulation.new()
var debit_verified := false
var performance_peaks := {}
var motion_segments: Array[Dictionary] = []

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
		elif argument == "--production-evidence":
			production_evidence = true
	call_deferred("run")

func authoritative_debit(intent: Dictionary) -> Dictionary:
	var before := simulation.stored.duplicate(true)
	var carried_before := simulation.inventory.duplicate(true)
	var receipt: Dictionary = simulation.commit_world_transform_debit(intent)
	debit_verified = receipt.get("authority_applied", false) and receipt.get("authority_source") == "simulation" and not receipt.get("simulation_replayed", true)
	for kind in Simulation.KINDS:
		debit_verified = debit_verified and int(simulation.stored[kind]) == int(before[kind]) - int(intent.debits.get(kind, 0))
	debit_verified = debit_verified and simulation.inventory == carried_before
	if not debit_verified: return {}
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

	# All target geometry and actionable feedback are owned by the real view.
	# This screen-space caption identifies evidence without masking the target.
	var overlay := CanvasLayer.new()
	root.add_child(overlay)
	state_label = Label.new()
	overlay.add_child(state_label)
	state_label.position = Vector2(16, 0)
	state_label.set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_LEFT)
	state_label.offset_left = 16
	state_label.offset_top = -62
	state_label.add_theme_font_size_override("font_size", 20)
	state_label.add_theme_color_override("font_color", Color.WHITE)
	state_label.add_theme_constant_override("outline_size", 6)
	state_label.add_theme_color_override("font_outline_color", Color("101820"))

	camera = Camera3D.new()
	camera.current = true
	camera.fov = 44.0
	world.add_child(camera)

func configure_camera(angle: String) -> void:
	camera.fov = 44.0
	match angle:
		"front":
			camera.position = Vector3(0.0, 3.5, 7.5)
			camera.look_at(Vector3(0.0, 0.9, 0.0), Vector3.UP)
		"side":
			camera.position = Vector3(7.5, 3.5, 0.0)
			camera.look_at(Vector3(0.0, 0.9, 0.0), Vector3.UP)
		"three-quarter":
			camera.position = Vector3(5.6, 3.8, 6.2)
			camera.look_at(Vector3(0.0, 0.9, 0.0), Vector3.UP)
		"overhead":
			camera.position = Vector3(0.0, 9.0, 0.05)
			camera.fov = 40.0
			camera.look_at(Vector3(0.0, 0.8, 0.0), Vector3.FORWARD)
		"gameplay":
			camera.position = Vector3(5.2, 7.0, 8.7)
			camera.fov = 48.0
			camera.look_at(Vector3(0.0, 0.75, 0.0), Vector3.UP)
		"detail":
			# Keep this close enough to judge geometry but wide enough that the
			# state/disclaimer evidence remains fully inside frame at native 4K.
			camera.position = Vector3(3.5, 2.9, 5.2)
			camera.fov = 40.0
			camera.look_at(Vector3(0.0, 1.15, 0.0), Vector3.UP)
		_:
			camera.position = Vector3(5.6, 3.8, 6.2)
			camera.look_at(Vector3(0.0, 0.9, 0.0), Vector3.UP)

func capture_state(name: String, descriptor: Dictionary, angles: Array = ["front", "three-quarter"]) -> bool:
	state_label.text = "T10 NEUTRAL FRAMEWORK | %s\nReal delivered-resource authority | Not T11 content" % name.to_upper()
	for raw_angle in angles:
		var angle := String(raw_angle)
		configure_camera(angle)
		await process_frame
		await RenderingServer.frame_post_draw
		measure_performance()
		var image := root.get_texture().get_image()
		if image == null or image.is_empty():
			return false
		var filename := "%s-%s.png" % [name, angle]
		var error := image.save_png(output.path_join(filename))
		if error != OK:
			return false
		var readability: Dictionary = view.projected_readability(camera)
		if not readability.get("passed", false):
			push_error("Projected readability failed for %s/%s: %s" % [name, angle, JSON.stringify(readability)])
			return false
		records.append({
			"state": name,
			"angle": angle,
			"file": filename,
			"size": [image.get_width(), image.get_height()],
			"view": descriptor.duplicate(true),
			"projected_readability": readability,
		})
		projection_records.append({"state": name, "angle": angle, "projected_readability": readability})
	if device_check:
		for supplemental_angle in ["side", "three-quarter", "overhead", "gameplay", "detail"]:
			configure_camera(supplemental_angle)
			await process_frame
			await RenderingServer.frame_post_draw
			var supplemental: Dictionary = view.projected_readability(camera)
			if not supplemental.get("passed", false):
				push_error("Projected device readability failed for %s/%s: %s" % [name, supplemental_angle, JSON.stringify(supplemental)])
				return false
			projection_records.append({"state": name, "angle": supplemental_angle, "projected_readability": supplemental})
	return true

func measure_performance() -> void:
	var rss_output: Array = []
	var rss_status := OS.execute("ps", ["-o", "rss=", "-p", str(OS.get_process_id())], rss_output)
	var rss_mb := float(String(rss_output[0]).strip_edges().to_int()) / 1024.0 if rss_status == 0 and not rss_output.is_empty() else -1.0
	if rss_mb <= 0.0:
		push_error("Missing positive measured process RSS")
		quit(1)
		return
	var metrics := {
		"visible_triangles": Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME),
		"draw_calls": Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME),
		# Draw calls conservatively bound distinct submitted materials, including
		# internal Label3D font passes not exposed as scene material resources.
		"materials_visible": Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME),
		"texture_gpu_memory_mb": Performance.get_monitor(Performance.RENDER_TEXTURE_MEM_USED) / 1048576.0,
		"process_memory_mb": rss_mb,
		"physics_active_bodies": Performance.get_monitor(Performance.PHYSICS_3D_ACTIVE_OBJECTS),
		"animated_rigs_active": 0,
		"npc_companion_active_population": 0,
	}
	for key in metrics: performance_peaks[key] = maxf(float(performance_peaks.get(key, 0.0)), float(metrics[key]))

func write_manifest(manifest: Dictionary) -> bool:
	var file := FileAccess.open(output.path_join("manifest.json"), FileAccess.WRITE)
	if file == null:
		return false
	file.store_string(JSON.stringify(manifest, "  "))
	return true

func hold_motion(state: String) -> void:
	if device_check or production_evidence: return
	# Baseline is recorded at fixed 30 fps by Godot Movie Maker. Thirty frames
	# preserve one full second, including more than a full 1.4Hz pulse cycle.
	configure_camera("front")
	var start_frame := Engine.get_frames_drawn()
	for frame in 30:
		await process_frame
		await RenderingServer.frame_post_draw

	motion_segments.append({"state": state, "start_frame": start_frame, "end_frame": Engine.get_frames_drawn(), "fps": 30, "start_seconds": start_frame / 30.0, "end_seconds": Engine.get_frames_drawn() / 30.0})

func capture_lifecycle(inventory: Dictionary) -> void:
	var angles: Array = ["front"] if device_check else (["front", "side", "three-quarter", "overhead", "gameplay", "detail"] if production_evidence else ["front", "three-quarter"])
	var states := ["ready", "blocked", "preview", "committing", "complete", "replay"]
	var ready_offer: Dictionary = engine.preview_transform("framework_anchor_seed_to_foundation", "capture-anchor", inventory)
	view.set_ready(ready_offer)
	if not await capture_state("ready", view.descriptor(), angles): quit(1); return
	await hold_motion("ready")
	var blocked: Dictionary = engine.preview_transform("framework_anchor_seed_to_foundation", "capture-anchor", {"wood": 7, "stone": 3})
	if blocked.passed or not view.show_blocked(blocked) or not await capture_state("blocked", view.descriptor(), angles): quit(1); return
	await hold_motion("blocked")
	var preview: Dictionary = engine.preview_transform("framework_anchor_seed_to_foundation", "capture-anchor", inventory)
	if not preview.passed or not view.show_preview(preview) or not await capture_state("preview", view.descriptor(), angles): quit(1); return
	await hold_motion("preview")
	var intent: Dictionary = engine.commit_transform("capture-tx", "framework_anchor_seed_to_foundation", "capture-anchor", inventory)
	if not intent.passed or not view.show_commit(intent) or not await capture_state("committing", view.descriptor(), angles): quit(1); return
	await hold_motion("committing")
	var accepted: Dictionary = engine.accept_authoritative_receipt(authoritative_debit(intent))
	var next_offer: Dictionary = engine.preview_transform("framework_anchor_foundation_to_reinforced", "capture-anchor", simulation.stored)
	if not accepted.passed or not view.mark_complete(accepted, next_offer) or not await capture_state("complete", view.descriptor(), angles): quit(1); return
	await hold_motion("complete")
	var stored_before := simulation.stored.duplicate(true)
	var component_before: Dictionary = engine.export_component_state()
	var view_before: Dictionary = view.descriptor()
	var replay_receipt: Dictionary = simulation.commit_world_transform_debit(intent)
	var replay: Dictionary = engine.accept_authoritative_receipt(replay_receipt)
	var replay_verified: bool = replay_receipt.get("simulation_replayed", false) and replay.get("replayed", false) and simulation.stored == stored_before and engine.export_component_state() == component_before and view.descriptor() == view_before
	if not replay_verified or not await capture_state("replay", view.descriptor(), angles): quit(1); return
	await hold_motion("replay")
	var final_view: Dictionary = view.descriptor()
	var manifest := {
		"task_id": "T10", "candidate": candidate,
		"mode": "real-authority-neutral-fixture", "device_id": device_id,
		"logical_size": [capture_width, capture_height],
		"capture_resolution": [capture_width, capture_height],
		"native_scale_1": capture_width == 3840 and capture_height == 2160,
		"fixture_only": false, "t11_content": false,
		"target_color_static": true, "view_owns_lifecycle_visuals": true,
		"real_t09_adapter_bound": true, "exact_debit_verified": debit_verified,
		"exact_replay_verified": replay_verified,
		"performance_peaks": performance_peaks,
		"renderer": RenderingServer.get_current_rendering_method() + "/" + RenderingServer.get_video_adapter_name(),
		"render_scale": root.scaling_3d_scale,
		"performance_scope": "neutral fixture; zero rigs/actors by construction; materials upper-bound from submitted draw calls; ps RSS for exact Godot PID; no physical certification",
		"motion_segments": motion_segments,
		"motion_frames_per_state": 30 if not device_check and not production_evidence else 0,
		"record_count": records.size(), "states": states, "angles": angles, "records": records,
		"projection_angles": ["front", "side", "three-quarter", "overhead", "gameplay", "detail"] if device_check or production_evidence else angles,
		"projection_record_count": projection_records.size(), "projection_records": projection_records,
		"view_visual_node_count": int(final_view.visual_node_count),
		"view_visual_build_count": int(final_view.visual_build_count),
		"final_target": engine.descriptor().targets["capture-anchor"].duplicate(true),
		"integration_allowed": false, "task_approved": false,
		"projected_readability_passed": projection_records.all(func(row): return row.get("projected_readability", {}).get("passed", false)),
		"passed": records.size() == states.size() * angles.size() and projection_records.size() == states.size() * (6 if device_check or production_evidence else angles.size()) and projection_records.all(func(row): return row.get("projected_readability", {}).get("passed", false)) and int(final_view.visual_node_count) == 4 and int(final_view.visual_build_count) == 1 and debit_verified and replay_verified,
	}
	if not write_manifest(manifest): quit(1); return
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
	# Neutral scene uses a seeded delivered balance; acquisition/delivery is
	# exercised separately by the real-authority integration suite.
	simulation.stored = inventory.duplicate(true)
	inventory = simulation.stored.duplicate(true)
	await capture_lifecycle(inventory)
