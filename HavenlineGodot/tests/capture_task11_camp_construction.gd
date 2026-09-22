extends SceneTree

const Transform = preload("res://scripts/world_transform.gd")
const FrameworkView = preload("res://scripts/world_transform_view.gd")
const CampView = preload("res://scripts/camp_construction_view.gd")

var output := "user://task11-camp-review"
var candidate := "local-working-tree"
var profile := "standard"
var world: Node3D
var camera: Camera3D
var scenario: Node3D
var engine
var framework_view
var camp_view
var records: Array[Dictionary] = []
var failures: Array[String] = []

const INVENTORY := {"wood": 100, "stone": 100, "metal": 20, "fuel": 10}
const ANGLES := ["front", "three-quarter", "side", "overhead"]
const STANDARD_STATES := [
	"foundation_ready",
	"foundation_preview",
	"foundation_complete",
	"reinforced_blocked",
	"reinforced_preview",
	"reinforced_complete",
]
const NATIVE_STATES := [
	"foundation_preview",
	"foundation_complete",
	"reinforced_blocked",
	"reinforced_complete",
]
const NATIVE_ANGLES := ["front", "three-quarter"]
const CPU_WARMUP_FRAMES := 60
const CPU_SAMPLE_FRAMES := 180

func _initialize() -> void:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--out="):
			output = argument.trim_prefix("--out=")
		elif argument.begins_with("--candidate="):
			candidate = argument.trim_prefix("--candidate=")
		elif argument.begins_with("--profile="):
			profile = argument.trim_prefix("--profile=")
	call_deferred("run")

func simulation_ack(intent: Dictionary) -> Dictionary:
	var receipt := intent.duplicate(true)
	receipt["authority_source"] = "simulation"
	receipt["authority_applied"] = true
	return receipt

func add_environment() -> void:
	world = Node3D.new()
	world.name = "T11ReviewWorld"
	root.add_child(world)

	var environment_node := WorldEnvironment.new()
	var environment := Environment.new()
	environment.background_mode = Environment.BG_COLOR
	environment.background_color = Color("101821")
	environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	environment.ambient_light_color = Color("d9e9f1")
	environment.ambient_light_energy = 0.72
	environment_node.environment = environment
	world.add_child(environment_node)

	var key := DirectionalLight3D.new()
	key.rotation_degrees = Vector3(-54.0, -28.0, 0.0)
	key.light_energy = 1.9
	key.shadow_enabled = true
	world.add_child(key)

	var fill := DirectionalLight3D.new()
	fill.rotation_degrees = Vector3(-35.0, 145.0, 0.0)
	fill.light_energy = 0.55
	fill.shadow_enabled = false
	world.add_child(fill)

	var floor := MeshInstance3D.new()
	var plane := PlaneMesh.new()
	plane.size = Vector2(16.0, 16.0)
	floor.mesh = plane
	var floor_material := StandardMaterial3D.new()
	floor_material.albedo_color = Color("243541")
	floor_material.roughness = 0.93
	floor.material_override = floor_material
	world.add_child(floor)

	camera = Camera3D.new()
	camera.current = true
	camera.fov = 44.0
	world.add_child(camera)

func configure_camera(angle: String) -> void:
	camera.fov = 44.0
	match angle:
		"front":
			camera.position = Vector3(0.0, 4.2, 9.2)
			camera.look_at(Vector3(0.0, 1.45, 0.0), Vector3.UP)
		"three-quarter":
			camera.position = Vector3(7.0, 5.0, 7.4)
			camera.look_at(Vector3(0.0, 1.45, 0.0), Vector3.UP)
		"side":
			camera.position = Vector3(9.2, 4.2, 0.0)
			camera.look_at(Vector3(0.0, 1.45, 0.0), Vector3.UP)
		"overhead":
			camera.position = Vector3(0.0, 11.2, 0.08)
			camera.fov = 42.0
			camera.look_at(Vector3(0.0, 0.8, 0.0), Vector3.FORWARD)
		_:
			camera.position = Vector3(7.0, 5.0, 7.4)
			camera.look_at(Vector3(0.0, 1.45, 0.0), Vector3.UP)

func _foundation_receipt() -> Dictionary:
	var intent: Dictionary = engine.commit_transform(
		"capture-foundation-bootstrap",
		"framework_anchor_seed_to_foundation",
		"camp-review",
		INVENTORY
	)
	if not bool(intent.get("passed", false)):
		return {}
	return engine.accept_authoritative_receipt(simulation_ack(intent))

func build_state(state: String) -> bool:
	if scenario != null and is_instance_valid(scenario):
		scenario.free()
	scenario = Node3D.new()
	scenario.name = "Scenario_" + state
	world.add_child(scenario)
	await process_frame

	engine = Transform.new()
	if not engine.configure_from_file():
		failures.append(state + ": T10 catalog failed to configure")
		return false
	if not engine.register_target("camp-review", "seed"):
		failures.append(state + ": target registration failed")
		return false

	var reinforced := state.begins_with("reinforced_")
	if reinforced:
		var bootstrap := _foundation_receipt()
		if bootstrap.is_empty() or not bool(bootstrap.get("passed", false)):
			failures.append(state + ": foundation bootstrap failed")
			return false

	framework_view = FrameworkView.new()
	framework_view.name = "FrameworkResponse"
	scenario.add_child(framework_view)
	camp_view = CampView.new()
	camp_view.name = "CampAuthoredResponse"
	scenario.add_child(camp_view)
	await process_frame

	if not framework_view.configure("camp-review"):
		failures.append(state + ": framework view configure failed")
		return false
	var construction_id := "camp_shelter_reinforced" if reinforced else "camp_shelter_foundation"
	if not camp_view.configure("camp-review", construction_id):
		failures.append(state + ": camp view configure failed")
		return false
	if not camp_view.set_placement_context(Vector3.ZERO, []):
		failures.append(state + ": valid placement unexpectedly blocked")
		return false

	var preview: Dictionary
	var intent: Dictionary
	var accepted: Dictionary
	if reinforced:
		preview = engine.preview_transform(
			"framework_anchor_foundation_to_reinforced",
			"camp-review",
			INVENTORY,
			["harvesting_online"]
		)
		match state:
			"reinforced_blocked":
				var blocked: Dictionary = engine.preview_transform(
					"framework_anchor_foundation_to_reinforced",
					"camp-review",
					INVENTORY
				)
				if bool(blocked.get("passed", true)):
					failures.append(state + ": prerequisite block missing")
					return false
				if not framework_view.show_blocked(blocked) or not camp_view.show_blocked(blocked):
					failures.append(state + ": blocked presentation failed")
					return false
			"reinforced_preview":
				if not framework_view.show_preview(preview) or not camp_view.show_preview(preview):
					failures.append(state + ": preview presentation failed")
					return false
			"reinforced_committing":
				intent = engine.commit_transform(
					"capture-reinforced",
					"framework_anchor_foundation_to_reinforced",
					"camp-review",
					INVENTORY,
					["harvesting_online"]
				)
				if not framework_view.show_commit(intent) or not camp_view.show_commit(intent):
					failures.append(state + ": committing presentation failed")
					return false
			"reinforced_complete":
				intent = engine.commit_transform(
					"capture-reinforced",
					"framework_anchor_foundation_to_reinforced",
					"camp-review",
					INVENTORY,
					["harvesting_online"]
				)
				if not framework_view.show_commit(intent) or not camp_view.show_commit(intent):
					failures.append(state + ": pre-complete commit failed")
					return false
				accepted = engine.accept_authoritative_receipt(simulation_ack(intent))
				if not framework_view.mark_complete(accepted) or not camp_view.mark_complete(accepted):
					failures.append(state + ": complete presentation failed")
					return false
	else:
		preview = engine.preview_transform(
			"framework_anchor_seed_to_foundation",
			"camp-review",
			INVENTORY
		)
		match state:
			"foundation_ready":
				framework_view.set_ready(preview)
				if not camp_view.show_ready():
					failures.append(state + ": ready presentation failed")
					return false
			"foundation_preview":
				if not framework_view.show_preview(preview) or not camp_view.show_preview(preview):
					failures.append(state + ": preview presentation failed")
					return false
			"foundation_committing":
				intent = engine.commit_transform(
					"capture-foundation",
					"framework_anchor_seed_to_foundation",
					"camp-review",
					INVENTORY
				)
				if not framework_view.show_commit(intent) or not camp_view.show_commit(intent):
					failures.append(state + ": committing presentation failed")
					return false
			"foundation_complete":
				intent = engine.commit_transform(
					"capture-foundation",
					"framework_anchor_seed_to_foundation",
					"camp-review",
					INVENTORY
				)
				if not framework_view.show_commit(intent) or not camp_view.show_commit(intent):
					failures.append(state + ": pre-complete commit failed")
					return false
				accepted = engine.accept_authoritative_receipt(simulation_ack(intent))
				if not framework_view.mark_complete(accepted) or not camp_view.mark_complete(accepted):
					failures.append(state + ": complete presentation failed")
					return false

	for _i in 4:
		await process_frame
	return true

func _record_metrics() -> Dictionary:
	return {
		"cpu_frame_ms": float(Performance.get_monitor(Performance.TIME_PROCESS)) * 1000.0,
		"draw_calls": int(Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME)),
		"visible_triangles": int(Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME)),
		"texture_gpu_memory_mb": float(Performance.get_monitor(Performance.RENDER_TEXTURE_MEM_USED)) / 1048576.0,
		"process_memory_mb": float(OS.get_static_memory_usage()) / 1048576.0,
	}

func save_capture(state: String, angle: String, suffix := "") -> bool:
	configure_camera(angle)
	for _i in 3:
		await process_frame
	await RenderingServer.frame_post_draw
	var image := root.get_texture().get_image()
	if image == null or image.is_empty():
		failures.append(state + "/" + angle + ": viewport image missing")
		return false
	var file_name := state + "__" + angle + suffix + ".png"
	var path := output.path_join(file_name)
	if image.save_png(path) != OK:
		failures.append(state + "/" + angle + ": image save failed")
		return false
	records.append({
		"kind": "image",
		"state": state,
		"angle": angle,
		"file": file_name,
		"sha256": FileAccess.get_sha256(path),
		"size": [image.get_width(), image.get_height()],
		"framework": framework_view.descriptor(),
		"camp": camp_view.descriptor(),
		"metrics": _record_metrics(),
	})
	return true

func capture_motion(state: String) -> void:
	if not await build_state(state):
		return
	configure_camera("three-quarter")
	for frame_index in 24:
		await process_frame
		if frame_index % 3 != 0:
			continue
		await RenderingServer.frame_post_draw
		var image := root.get_texture().get_image()
		var file_name := state + "__motion_%02d.png" % frame_index
		var path := output.path_join(file_name)
		if image == null or image.is_empty() or image.save_png(path) != OK:
			failures.append(state + ": motion frame save failed")
			return
		records.append({
			"kind": "motion_frame",
			"state": state,
			"angle": "three-quarter",
			"frame_index": frame_index,
			"file": file_name,
			"sha256": FileAccess.get_sha256(path),
			"size": [image.get_width(), image.get_height()],
			"framework": framework_view.descriptor(),
			"camp": camp_view.descriptor(),
			"metrics": _record_metrics(),
		})

func run_cpu_probe() -> void:
	var probe_engine = Transform.new()
	if not probe_engine.configure_from_file():
		print(JSON.stringify({"schema_version":1,"task_id":"T11","candidate":candidate,"passed":false,"reason":"T10 catalog failed to configure","sample_count":0}))
		quit(1)
		return
	if not probe_engine.register_target("perf-camp", "seed"):
		print(JSON.stringify({"schema_version":1,"task_id":"T11","candidate":candidate,"passed":false,"reason":"performance target registration failed","sample_count":0}))
		quit(1)
		return
	var inventory := {"wood":100,"stone":100,"metal":20,"fuel":10}
	var foundation_intent: Dictionary = probe_engine.commit_transform("perf-foundation","framework_anchor_seed_to_foundation","perf-camp",inventory)
	if not bool(foundation_intent.get("passed", false)):
		print(JSON.stringify({"schema_version":1,"task_id":"T11","candidate":candidate,"passed":false,"reason":"foundation intent failed","sample_count":0}))
		quit(1)
		return
	var foundation_receipt: Dictionary = probe_engine.accept_authoritative_receipt(simulation_ack(foundation_intent))
	if not bool(foundation_receipt.get("passed", false)) or not bool(foundation_receipt.get("applied", false)):
		print(JSON.stringify({"schema_version":1,"task_id":"T11","candidate":candidate,"passed":false,"reason":"foundation bootstrap receipt failed","sample_count":0}))
		quit(1)
		return
	var probe_view = CampView.new()
	root.add_child(probe_view)
	await process_frame
	if not probe_view.configure("perf-camp", "camp_shelter_reinforced") or not probe_view.set_placement_context(Vector3.ZERO, []):
		print(JSON.stringify({"schema_version":1,"task_id":"T11","candidate":candidate,"passed":false,"reason":"reinforced camp view failed to configure","sample_count":0}))
		quit(1)
		return
	var reinforced_intent: Dictionary = probe_engine.commit_transform("perf-reinforced","framework_anchor_foundation_to_reinforced","perf-camp",inventory,["harvesting_online"])
	if not bool(reinforced_intent.get("passed", false)) or not probe_view.show_commit(reinforced_intent):
		print(JSON.stringify({"schema_version":1,"task_id":"T11","candidate":candidate,"passed":false,"reason":"reinforced committing state failed","sample_count":0}))
		quit(1)
		return
	for _i in CPU_WARMUP_FRAMES:
		await process_frame
	var samples: Array[float] = []
	for _i in CPU_SAMPLE_FRAMES:
		await process_frame
		var value_ms := float(Performance.get_monitor(Performance.TIME_PROCESS)) * 1000.0
		if is_finite(value_ms) and value_ms >= 0.0:
			samples.append(value_ms)
	if samples.size() != CPU_SAMPLE_FRAMES:
		print(JSON.stringify({"schema_version":1,"task_id":"T11","candidate":candidate,"passed":false,"reason":"incomplete CPU frame sample set","sample_count":samples.size()}))
		quit(1)
		return
	samples.sort()
	var p95_index := int(floor(float(samples.size() - 1) * 0.95))
	var total := 0.0
	for value in samples:
		total += value
	var report := {
		"schema_version":1,
		"task_id":"T11",
		"candidate":candidate,
		"passed":true,
		"state":"reinforced_committing",
		"warmup_frames":CPU_WARMUP_FRAMES,
		"sample_count":samples.size(),
		"fixed_fps":60,
		"cpu_frame_statistic":"p95_after_warmup",
		"cpu_frame_ms_p95":samples[p95_index],
		"cpu_frame_ms_max":samples[-1],
		"cpu_frame_ms_mean":total / float(samples.size()),
		"measurement_method":"Godot headless fixed-fps 60 process-time probe from authorized T11 capture harness; no PNG encoding or software raster timing in CPU sample",
		"physical_4k60_certified":false
	}
	print(JSON.stringify(report))
	quit(0)

func run() -> void:
	if profile == "cpu-probe":
		await run_cpu_probe()
		return
	DirAccess.make_dir_recursive_absolute(output)
	add_environment()
	await process_frame
	var states := NATIVE_STATES if profile == "native4k" else STANDARD_STATES
	var angles := NATIVE_ANGLES if profile == "native4k" else ANGLES
	for state in states:
		if not await build_state(state):
			continue
		for angle in angles:
			await save_capture(state, angle)
	if profile == "standard":
		await capture_motion("foundation_committing")
		await capture_motion("reinforced_committing")

	var hashes := {}
	for row in records:
		hashes[row.sha256] = true
	var manifest := {
		"schema_version": 1,
		"task_id": "T11",
		"candidate": candidate,
		"profile": profile,
		"record_count": records.size(),
		"unique_image_hashes": hashes.size(),
		"states": states,
		"angles": angles,
		"records": records,
		"failures": failures,
		"passed": failures.is_empty() and records.size() > 0 and hashes.size() == records.size(),
		"fixture_only": true,
		"task_approved": false,
		"physical_4k60_certified": false,
	}
	var manifest_path := output.path_join("manifest.json")
	FileAccess.open(manifest_path, FileAccess.WRITE).store_string(JSON.stringify(manifest, "\t") + "\n")
	print(JSON.stringify(manifest))
	quit(0 if manifest.passed else 1)
