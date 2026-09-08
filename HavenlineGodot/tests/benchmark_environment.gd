extends SceneTree
# Real elapsed render-submission intervals. Never use --fixed-fps for this test.
# This is not Android display-presentation timing or a thermal certificate.
const FrameRecord = preload("res://scripts/performance_record.gd")
const Main = preload("res://scripts/main.gd")
var scene
var record = FrameRecord.new()
var duration := 60.0
var warmup := 10.0
var output := "user://environment-benchmark"
var began := 0
var previous := 0
var measured_began := 0
var measured_frames := 0
var resolutions_valid := true
var finished := false
var requested_duration := 60.0

func _initialize():
	for argument in OS.get_cmdline_args():
		if argument.begins_with("--fixed-fps"):
			push_error("Fixed-timestep screenshot runs are not performance benchmarks")
			quit(2)
			return
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--benchmark-seconds="):
			duration = clampf(argument.trim_prefix("--benchmark-seconds=").to_float(), 10.0, 3600.0)
		if argument.begins_with("--benchmark-warmup="):
			warmup = clampf(argument.trim_prefix("--benchmark-warmup=").to_float(), 2.0, 120.0)
		if argument.begins_with("--benchmark-output="):
			output = argument.trim_prefix("--benchmark-output=")
	requested_duration = duration
	call_deferred("begin")

func begin():
	if DisplayServer.get_name() == "headless":
		push_error("A headless no-render run is not a rendering benchmark")
		quit(2)
		return
	DirAccess.make_dir_recursive_absolute(output)
	scene = Main.new()
	scene.qa_mode = true # Never read, advance or write a player's save.
	scene.capture_directory = output
	scene.capture_frames = 1000 # Bypass the independent 12-frame screenshot exit.
	scene.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	root.add_child(scene)
	scene.size = Vector2(root.size)
	scene.resize_render()
	began = Time.get_ticks_usec()
	RenderingServer.frame_post_draw.connect(after_draw)

func after_draw():
	if finished: return
	var now := Time.get_ticks_usec()
	if float(now - began) / 1000000.0 < warmup:
		previous = 0
		return
	if measured_began == 0:
		measured_began = now
		scene.scene_view.get_texture().get_image().save_png(output.path_join("start-native.png"))
		previous = Time.get_ticks_usec() # Do not count the deliberate first readback.
		measured_began = previous
		return
	if previous > 0:
		record.sample(float(now - previous) / 1000.0)
		measured_frames += 1
	previous = now
	record.resolution(scene.scene_view.size)
	resolutions_valid = resolutions_valid and scene.scene_view.size.x >= 3840 and scene.scene_view.size.y >= 2160 and is_equal_approx(scene.scene_view.scaling_3d_scale, 1.0)
	var elapsed := float(now - measured_began) / 1000000.0
	# Exercise actual camera transforms without modifying resources or player saves.
	var views := ["front", "left", "rear", "side", "three-quarter"]
	scene.capture_view = views[int(elapsed / 12.0) % views.size()]
	if elapsed >= requested_duration:
		finished = true
		RenderingServer.frame_post_draw.disconnect(after_draw)
		finish.call_deferred()

func finish():
	var result: Dictionary = record.report()
	var gpu := RenderingServer.get_video_adapter_name()
	result["requested_seconds"] = requested_duration
	result["warmup_seconds"] = warmup
	result["platform"] = OS.get_name()
	result["model"] = OS.get_model_name()
	result["gpu"] = gpu
	result["renderer"] = RenderingServer.get_current_rendering_method()
	result["display_driver"] = DisplayServer.get_name()
	result["engine"] = Engine.get_version_info()
	result["environment_revision"] = scene.ENVIRONMENT_REVISION
	result["main_script_sha256"] = FileAccess.get_sha256("res://scripts/main.gd")
	result["kit_manifest_sha256"] = FileAccess.get_sha256("res://assets/environment_v2/manifest.json")
	result["native_dimensions_and_scale_maintained"] = resolutions_valid and measured_frames > 0
	result["fixed_timestep_used"] = false
	result["player_save_accessed"] = false
	result["software_renderer"] = "llvmpipe" in gpu.to_lower() or "lavapipe" in gpu.to_lower() or "swiftshader" in gpu.to_lower()
	result["scene_only"] = true
	result["physical_device_validated"] = false
	result["thermal_validated"] = false
	result["display_presentation_verified"] = false
	result["sustained_4k60_certified"] = false
	result["sample_gate_60fps"] = measured_frames >= 3600 and result.retained_seconds >= 60.0 and result.average_engine_fps >= 60.0 and result.p99_ms <= 1000.0 / 60.0 + .1 and resolutions_valid
	result["limitations"] = ["Render-submission intervals, not presented frames.", "A software or desktop run never certifies Android performance.", "Missing NPC art means this scene does not cover the completed game's full load.", "Thirty-minute physical-device and thermal evidence is still required."]
	result["draw_calls"] = scene.scene_view.get_render_info(Viewport.RENDER_INFO_TYPE_VISIBLE, Viewport.RENDER_INFO_DRAW_CALLS_IN_FRAME)
	result["primitives"] = scene.scene_view.get_render_info(Viewport.RENDER_INFO_TYPE_VISIBLE, Viewport.RENDER_INFO_PRIMITIVES_IN_FRAME)
	scene.scene_view.get_texture().get_image().save_png(output.path_join("end-native.png"))
	var file := FileAccess.open(output.path_join("benchmark.json"), FileAccess.WRITE)
	if file == null:
		push_error("Could not write benchmark evidence")
		quit(2)
		return
	file.store_string(JSON.stringify(result, "\t"))
	file.close()
	print("BENCHMARK_RESULT ", JSON.stringify(result))
	await scene.close_game()
