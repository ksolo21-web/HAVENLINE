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
var exhaustive_projections := false
var rendered_clearance_probe := false
var domain_profile := ""
var evidence_scale := 1.0
var logical_width := 0
var logical_height := 0
var anchor_only := false
var product_view_sha256 := ""
var probe_source := ""
var probe_capture_sha256 := ""
var probe_verifier_sha256 := ""
var probe_workflow_sha256 := ""
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
		elif argument == "--exhaustive-projections":
			exhaustive_projections = true
		elif argument == "--rendered-clearance-probe":
			rendered_clearance_probe = true
		elif argument.begins_with("--domain-profile="):
			domain_profile = argument.trim_prefix("--domain-profile=")
			rendered_clearance_probe = true
			exhaustive_projections = true
			device_check = true
		elif argument.begins_with("--readability-scale="):
			evidence_scale = float(argument.trim_prefix("--readability-scale="))
		elif argument.begins_with("--logical-width="):
			logical_width = int(argument.trim_prefix("--logical-width="))
		elif argument.begins_with("--logical-height="):
			logical_height = int(argument.trim_prefix("--logical-height="))
		elif argument == "--native4k-anchors":
			anchor_only = true
		elif argument.begins_with("--product-view-sha256="):
			product_view_sha256 = argument.trim_prefix("--product-view-sha256=")
		elif argument.begins_with("--probe-source="):
			probe_source = argument.trim_prefix("--probe-source=")
		elif argument.begins_with("--probe-capture-sha256="):
			probe_capture_sha256 = argument.trim_prefix("--probe-capture-sha256=")
		elif argument.begins_with("--probe-verifier-sha256="):
			probe_verifier_sha256 = argument.trim_prefix("--probe-verifier-sha256=")
		elif argument.begins_with("--probe-workflow-sha256="):
			probe_workflow_sha256 = argument.trim_prefix("--probe-workflow-sha256=")
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
	environment_node.name = "EvidenceEnvironment"
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
	floor.name = "EvidenceFloor"
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

func _save_viewport_image(path: String) -> bool:
	var image := root.get_texture().get_image()
	return image != null and not image.is_empty() and image.save_png(path) == OK

func _vector3_record(value: Vector3) -> Array:
	return [value.x, value.y, value.z]

func _transform_record(value: Transform3D) -> Dictionary:
	return {
		"basis_x": _vector3_record(value.basis.x),
		"basis_y": _vector3_record(value.basis.y),
		"basis_z": _vector3_record(value.basis.z),
		"origin": _vector3_record(value.origin),
	}

func _logical_viewport_record() -> Array:
	var logical := root.get_visible_rect().size
	return [int(round(logical.x)), int(round(logical.y))]

func _clearance_core_binding(name: String, angle: String, case_nonce: String) -> Dictionary:
	var visual_root := view.get_node("T10WorldResponse") as Node3D
	var label := view.get_node("T10WorldResponse/StatusLabel") as Label3D
	var ring := view.get_node("T10WorldResponse/StateRing") as MeshInstance3D
	var ghost := view.get_node("T10WorldResponse/PreviewVolume") as MeshInstance3D
	var resource_symbols_path := "res://assets/world_transform_v1/resource_symbols.tres"
	return {
		"case_nonce": case_nonce,
		"domain_profile": domain_profile,
		"evidence_scale": evidence_scale,
		"state": name,
		"angle": angle,
		"viewport": _logical_viewport_record(),
		"camera_transform": _transform_record(camera.transform),
		"camera_fov": camera.fov,
		"camera_projection": camera.projection,
		"camera_size": camera.size,
		"camera_near": camera.near,
		"camera_far": camera.far,
		"camera_keep_aspect": camera.keep_aspect,
		"visual_root_transform": _transform_record(visual_root.transform),
		"label_transform": _transform_record(label.transform),
		"ring_transform": _transform_record(ring.transform),
		"ghost_transform": _transform_record(ghost.transform),
		"lifecycle_descriptor": view.descriptor(),
		"dynamic_phase_seconds": float(view.get("_pulse_time")),
		"label_text": label.text,
		"label_realization": {
			"offset": [label.offset.x, label.offset.y],
			"width": label.width,
			"fixed_size": label.fixed_size,
			"pixel_size": label.pixel_size,
			"billboard": label.billboard,
			"no_depth_test": label.no_depth_test,
			"render_priority": label.render_priority,
			"outline_render_priority": label.outline_render_priority,
		},
		"font_identity": {
			"class": label.font.get_class(),
			"resource_path": label.font.resource_path,
			"resource_name": label.font.resource_name,
			"fallback_count": label.font.fallbacks.size(),
			"engine_version": Engine.get_version_info(),
			"font_size": label.font_size,
			"outline_size": label.outline_size,
			"resource_symbols_path": resource_symbols_path,
			"resource_symbols_sha256": FileAccess.get_sha256(resource_symbols_path),
		},
		"renderer": RenderingServer.get_current_rendering_method() + "/" + RenderingServer.get_video_adapter_name(),
		"product_source": candidate,
		"product_view_sha256": product_view_sha256,
		"probe_source": probe_source,
		"probe_capture_sha256": probe_capture_sha256,
		"probe_verifier_sha256": probe_verifier_sha256,
		"probe_workflow_sha256": probe_workflow_sha256,
	}

func _clearance_layer_record(file_name: String, core: Dictionary, isolation: Dictionary) -> Dictionary:
	var path := output.path_join(file_name)
	var core_json := JSON.stringify(core)
	return {
		"file": file_name,
		"sha256": FileAccess.get_sha256(path),
		"core": core,
		"core_json": core_json,
		"core_sha256": core_json.sha256_text(),
		"isolation": isolation,
	}

func _capture_clearance_layers(name: String, angle: String, case_nonce: String, normal_file: String, normal_core: Dictionary, process_was_enabled: bool) -> Dictionary:
	var visual_root := view.get_node_or_null("T10WorldResponse") as Node3D
	var label := view.get_node_or_null("T10WorldResponse/StatusLabel") as Label3D
	var ring := view.get_node_or_null("T10WorldResponse/StateRing") as MeshInstance3D
	var ghost := view.get_node_or_null("T10WorldResponse/PreviewVolume") as MeshInstance3D
	var floor := world.get_node_or_null("EvidenceFloor") as MeshInstance3D
	var environment_node := world.get_node_or_null("EvidenceEnvironment") as WorldEnvironment
	if visual_root == null or label == null or ring == null or ghost == null or floor == null or environment_node == null:
		return {"passed": false, "error": "missing_clearance_probe_nodes"}
	var label_was_visible := label.visible
	var ring_was_visible := ring.visible
	var ghost_was_visible := ghost.visible
	var floor_was_visible := floor.visible
	var background_was := environment_node.environment.background_color
	var label_modulate_was := label.modulate
	var label_outline_was := label.outline_modulate
	var caption_was_visible := state_label.visible
	var prefix := "%s-%s" % [name, angle]
	var error := ""
	var layer_records := {
		"normal": _clearance_layer_record(normal_file, normal_core, {
			"label_visible": true, "response_visible": true, "floor_visible": true,
			"caption_visible": true, "id_background": false, "label_id_white": false,
		}),
	}

	# R: response only.  B: actual background with both label and response
	# hidden.  LI/LB are deterministic label-ID passes: the response and floor
	# are hidden, the environment is black, and glyph plus outline are white.
	# The independent verifier uses LI-LB for complete label coverage and R-B
	# for response coverage, avoiding equal-RGB/outline occlusion blind spots.
	label.visible = false
	await process_frame
	await RenderingServer.frame_post_draw
	var response_file := "%s-response-only.png" % prefix
	if not _save_viewport_image(output.path_join(response_file)):
		error = "response_only_capture_failed"
	else:
		layer_records["response_only"] = _clearance_layer_record(response_file, _clearance_core_binding(name, angle, case_nonce), {
			"label_visible": false, "response_visible": true, "floor_visible": true,
			"caption_visible": true, "id_background": false, "label_id_white": false,
		})

	var background_file := "%s-background.png" % prefix
	if error.is_empty():
		ring.visible = false
		ghost.visible = false
		await process_frame
		await RenderingServer.frame_post_draw
		if not _save_viewport_image(output.path_join(background_file)):
			error = "background_capture_failed"
		else:
			layer_records["background"] = _clearance_layer_record(background_file, _clearance_core_binding(name, angle, case_nonce), {
				"label_visible": false, "response_visible": false, "floor_visible": true,
				"caption_visible": true, "id_background": false, "label_id_white": false,
			})

	var label_id_background_file := "%s-label-id-background.png" % prefix
	if error.is_empty():
		floor.visible = false
		environment_node.environment.background_color = Color.BLACK
		label.modulate = Color.WHITE
		label.outline_modulate = Color.WHITE
		label.visible = false
		state_label.visible = false
		await process_frame
		await RenderingServer.frame_post_draw
		if not _save_viewport_image(output.path_join(label_id_background_file)):
			error = "label_id_background_capture_failed"
		else:
			layer_records["label_id_background"] = _clearance_layer_record(label_id_background_file, _clearance_core_binding(name, angle, case_nonce), {
				"label_visible": false, "response_visible": false, "floor_visible": false,
				"caption_visible": false, "id_background": true, "label_id_white": true,
			})

	var label_id_file := "%s-label-id.png" % prefix
	if error.is_empty():
		label.visible = label_was_visible
		await process_frame
		await RenderingServer.frame_post_draw
		if not _save_viewport_image(output.path_join(label_id_file)):
			error = "label_id_capture_failed"
		else:
			layer_records["label_id"] = _clearance_layer_record(label_id_file, _clearance_core_binding(name, angle, case_nonce), {
				"label_visible": true, "response_visible": false, "floor_visible": false,
				"caption_visible": false, "id_background": true, "label_id_white": true,
			})

	label.visible = label_was_visible
	ring.visible = ring_was_visible
	ghost.visible = ghost_was_visible
	floor.visible = floor_was_visible
	environment_node.environment.background_color = background_was
	label.modulate = label_modulate_was
	label.outline_modulate = label_outline_was
	state_label.visible = caption_was_visible
	view.set_process(process_was_enabled)
	await process_frame
	if not error.is_empty():
		return {"passed": false, "error": error}
	return {
		"passed": true,
		"response_only_file": response_file,
		"background_file": background_file,
		"label_id_background_file": label_id_background_file,
		"label_id_file": label_id_file,
		"process_frozen": true,
		"mask_construction": "label=LI-LB;response=R-B;normal=N",
		"label_id_contract": "white glyph and outline on black; floor and response hidden",
		"case_nonce": case_nonce,
		"layer_records": layer_records,
	}

func capture_state(name: String, descriptor: Dictionary, angles: Array = ["front", "three-quarter"]) -> bool:
	state_label.text = "T10 NEUTRAL FRAMEWORK | %s\nReal delivered-resource authority | Not T11 content" % name.to_upper()
	var projection_failed := false
	var state_processing: bool = view.is_processing()
	if rendered_clearance_probe:
		view.set_process(false)
	for raw_angle in angles:
		var angle := String(raw_angle)
		configure_camera(angle)
		var process_was_enabled: bool = view.is_processing()
		if rendered_clearance_probe:
			view.set_process(false)
			# Bind the committing case to the exact maximum 1.18 pulse envelope;
			# every isolation layer then retains this frozen dynamic phase.
			if name == "committing":
				view.set("_pulse_time", 0.0)
				view._process(0.25 / TransformView.PULSE_HZ)
		# Apply the exact layout before the evidence frame.  The returned analytic
		# report is bound to this camera/state, but an independent raster mask is
		# authoritative for rendered clearance.
		var readability: Dictionary = view.projected_readability(camera)
		await process_frame
		await RenderingServer.frame_post_draw
		measure_performance()
		var image := root.get_texture().get_image()
		if image == null or image.is_empty():
			view.set_process(process_was_enabled)
			return false
		var filename := "%s-%s.png" % [name, angle]
		var error := image.save_png(output.path_join(filename))
		if error != OK:
			view.set_process(process_was_enabled)
			return false
		var record := {
			"state": name,
			"angle": angle,
			"file": filename,
			"size": [image.get_width(), image.get_height()],
			"view": descriptor.duplicate(true),
			"projected_readability": readability,
		}
		if rendered_clearance_probe:
			var case_key := candidate + ":" + probe_source + ":" + name + ":" + angle
			if not domain_profile.is_empty():
				case_key += ":" + domain_profile
			var case_nonce := case_key.sha256_text()
			var normal_core := _clearance_core_binding(name, angle, case_nonce)
			var layers: Dictionary = await _capture_clearance_layers(name, angle, case_nonce, filename, normal_core, process_was_enabled)
			if not layers.get("passed", false):
				return false
			record["rendered_clearance_layers"] = layers
		records.append(record)
		projection_records.append({"state": name, "angle": angle, "projected_readability": readability})
		if not readability.get("passed", false):
			projection_failed = true
			if exhaustive_projections:
				push_warning("Projected readability failed for %s/%s: %s" % [name, angle, JSON.stringify(readability)])
			else:
				push_error("Projected readability failed for %s/%s: %s" % [name, angle, JSON.stringify(readability)])
				return false
	if device_check and not rendered_clearance_probe:
		for supplemental_angle in ["side", "three-quarter", "overhead", "gameplay", "detail"]:
			configure_camera(supplemental_angle)
			await process_frame
			await RenderingServer.frame_post_draw
			var supplemental: Dictionary = view.projected_readability(camera)
			projection_records.append({"state": name, "angle": supplemental_angle, "projected_readability": supplemental})
			if not supplemental.get("passed", false):
				projection_failed = true
				if exhaustive_projections:
					push_warning("Projected device readability failed for %s/%s: %s" % [name, supplemental_angle, JSON.stringify(supplemental)])
				else:
					push_error("Projected device readability failed for %s/%s: %s" % [name, supplemental_angle, JSON.stringify(supplemental)])
					return false
	view.set_process(state_processing)
	return true if exhaustive_projections else not projection_failed

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
	var angles: Array = ["gameplay"] if rendered_clearance_probe else (["front"] if device_check else (["front", "side", "three-quarter", "overhead", "gameplay", "detail"] if production_evidence else ["front", "three-quarter"]))
	if not domain_profile.is_empty():
		angles = ["overhead"] if anchor_only else ["front", "side", "three-quarter", "overhead", "gameplay", "detail"]
	var states := ["ready", "blocked"] if anchor_only else ["ready", "blocked", "preview", "committing", "complete", "replay"]
	var ready_offer: Dictionary = engine.preview_transform("framework_anchor_seed_to_foundation", "capture-anchor", inventory)
	view.set_ready(ready_offer)
	if not await capture_state("ready", view.descriptor(), angles): quit(1); return
	await hold_motion("ready")
	var blocked: Dictionary = engine.preview_transform("framework_anchor_seed_to_foundation", "capture-anchor", {"wood": 7, "stone": 3})
	if blocked.passed or not view.show_blocked(blocked) or not await capture_state("blocked", view.descriptor(), angles): quit(1); return
	await hold_motion("blocked")
	var preview: Dictionary = engine.preview_transform("framework_anchor_seed_to_foundation", "capture-anchor", inventory)
	if not preview.passed or not view.show_preview(preview) or (not anchor_only and not await capture_state("preview", view.descriptor(), angles)): quit(1); return
	await hold_motion("preview")
	var intent: Dictionary = engine.commit_transform("capture-tx", "framework_anchor_seed_to_foundation", "capture-anchor", inventory)
	if not intent.passed or not view.show_commit(intent) or (not anchor_only and not await capture_state("committing", view.descriptor(), angles)): quit(1); return
	await hold_motion("committing")
	var accepted: Dictionary = engine.accept_authoritative_receipt(authoritative_debit(intent))
	var next_offer: Dictionary = engine.preview_transform("framework_anchor_foundation_to_reinforced", "capture-anchor", simulation.stored)
	if not accepted.passed or not view.mark_complete(accepted, next_offer) or (not anchor_only and not await capture_state("complete", view.descriptor(), angles)): quit(1); return
	await hold_motion("complete")
	var stored_before := simulation.stored.duplicate(true)
	var component_before: Dictionary = engine.export_component_state()
	var view_before: Dictionary = view.descriptor()
	var replay_receipt: Dictionary = simulation.commit_world_transform_debit(intent)
	var replay: Dictionary = engine.accept_authoritative_receipt(replay_receipt)
	var replay_verified: bool = replay_receipt.get("simulation_replayed", false) and replay.get("replayed", false) and simulation.stored == stored_before and engine.export_component_state() == component_before and view.descriptor() == view_before
	if not replay_verified or (not anchor_only and not await capture_state("replay", view.descriptor(), angles)): quit(1); return
	await hold_motion("replay")
	var final_view: Dictionary = view.descriptor()
	var manifest := {
		"task_id": "T10", "candidate": candidate,
		"mode": "real-authority-neutral-fixture", "device_id": device_id,
		"logical_size": _logical_viewport_record() if rendered_clearance_probe else [capture_width, capture_height],
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
		"projection_angles": angles if rendered_clearance_probe else (["front", "side", "three-quarter", "overhead", "gameplay", "detail"] if device_check or production_evidence else angles),
		"projection_record_count": projection_records.size(), "projection_records": projection_records,
		"exhaustive_projections": exhaustive_projections,
		"rendered_clearance_probe": rendered_clearance_probe,
		"domain_profile": domain_profile,
		"evidence_scale": evidence_scale,
		"rendered_clearance_committing_phase": "maximum_1.18" if rendered_clearance_probe else "",
		"rendered_clearance_identity": {
			"product_source": candidate,
			"product_view_sha256": product_view_sha256,
			"probe_source": probe_source,
			"probe_capture_sha256": probe_capture_sha256,
			"probe_verifier_sha256": probe_verifier_sha256,
			"probe_workflow_sha256": probe_workflow_sha256,
		} if rendered_clearance_probe else {},
		"rendered_clearance_triplet_count": records.size() if rendered_clearance_probe else 0,
		"projection_failure_count": projection_records.filter(func(row): return not row.get("projected_readability", {}).get("passed", false)).size(),
		"view_visual_node_count": int(final_view.visual_node_count),
		"view_visual_build_count": int(final_view.visual_build_count),
		"final_target": engine.descriptor().targets["capture-anchor"].duplicate(true),
		"integration_allowed": false, "task_approved": false,
		"projected_readability_passed": projection_records.all(func(row): return row.get("projected_readability", {}).get("passed", false)),
		"passed": records.size() == states.size() * angles.size() and projection_records.size() == states.size() * (angles.size() if rendered_clearance_probe else (6 if device_check or production_evidence else angles.size())) and projection_records.all(func(row): return row.get("projected_readability", {}).get("passed", false)) and int(final_view.visual_node_count) == 4 and int(final_view.visual_build_count) == 1 and debit_verified and replay_verified,
	}
	if not write_manifest(manifest): quit(1); return
	print(JSON.stringify(manifest))
	quit(0 if manifest.passed else 1)

func run() -> void:
	if capture_width <= 0 or capture_height <= 0:
		print(JSON.stringify({"passed": false, "error": "invalid_capture_size"}))
		quit(1)
		return
	if rendered_clearance_probe:
		var actual_view_sha256 := FileAccess.get_sha256("res://scripts/world_transform_view.gd")
		var actual_capture_sha256 := FileAccess.get_sha256("res://tests/capture_task10_world_transform.gd")
		if candidate.length() != 40 or probe_source.length() != 40 or product_view_sha256.length() != 64 or probe_capture_sha256.length() != 64 or probe_verifier_sha256.length() != 64 or probe_workflow_sha256.length() != 64:
			print(JSON.stringify({"passed": false, "error": "incomplete_rendered_clearance_identity"}))
			quit(1)
			return
		if actual_view_sha256 != product_view_sha256 or actual_capture_sha256 != probe_capture_sha256:
			print(JSON.stringify({"passed": false, "error": "rendered_clearance_source_hash_mismatch", "actual_view_sha256": actual_view_sha256, "actual_capture_sha256": actual_capture_sha256}))
			quit(1)
			return
	if not domain_profile.is_empty() and (logical_width <= 0 or logical_height <= 0 or not is_finite(evidence_scale) or evidence_scale < 0.85 or evidence_scale > 1.35):
		quit(2)
		return
	DirAccess.make_dir_recursive_absolute(output)
	root.size = Vector2i(capture_width, capture_height)
	if not domain_profile.is_empty():
		root.content_scale_size = Vector2i(logical_width, logical_height)
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
	if not view.configure_readability(evidence_scale):
		print(JSON.stringify({"passed": false, "error": "readability_setup_failed"}))
		quit(1)
		return

	var inventory := {"wood": 20, "stone": 12, "metal": 2, "fuel": 1}
	# Neutral scene uses a seeded delivered balance; acquisition/delivery is
	# exercised separately by the real-authority integration suite.
	simulation.stored = inventory.duplicate(true)
	inventory = simulation.stored.duplicate(true)
	await capture_lifecycle(inventory)
