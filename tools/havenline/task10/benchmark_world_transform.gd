extends "res://tests/capture_task10_world_transform.gd"

# Fixed-size sample buffers; no screenshots, subprocesses or file I/O in phases.
const WARMUP := 120
const SAMPLES := 360
const CYCLES := 3

func rss_mb() -> float:
	var result: Array = []
	var status := OS.execute("ps", ["-o", "rss=", "-p", str(OS.get_process_id())], result)
	return float(String(result[0]).strip_edges().to_int()) / 1024.0 if status == 0 and not result.is_empty() else -1.0

func distribution(values: PackedFloat64Array) -> Dictionary:
	var sorted := values.duplicate()
	sorted.sort()
	var total := 0.0
	var first := 0.0
	var last := 0.0
	for i in values.size():
		total += values[i]
		if i < values.size() / 2: first += values[i]
		else: last += values[i]
	return {"count": values.size(), "mean": total / values.size(), "p95": sorted[int(ceil(values.size() * 0.95)) - 1], "p99": sorted[int(ceil(values.size() * 0.99)) - 1], "max": sorted[-1], "first_half_mean": first / (values.size() / 2), "last_half_mean": last / (values.size() / 2), "half_drift": (last - first) / (values.size() / 2)}

func measure_phase(state: String, cycle: int) -> Dictionary:
	for i in WARMUP:
		await process_frame
		await RenderingServer.frame_post_draw
	var intervals := PackedFloat64Array()
	var process_ms := PackedFloat64Array()
	intervals.resize(SAMPLES)
	process_ms.resize(SAMPLES)
	var rss_start := rss_mb()
	var static_start := Performance.get_monitor(Performance.MEMORY_STATIC) / 1048576.0
	var static_peak := static_start
	var nodes_min := get_node_count()
	var nodes_max := nodes_min
	var draw_min := INF
	var draw_max := 0.0
	var primitives_min := INF
	var primitives_max := 0.0
	var texture_min := INF
	var texture_max := 0.0
	var visual_before: Dictionary = view.descriptor()
	# Begin after external RSS query, excluding subprocess time.
	await process_frame
	await RenderingServer.frame_post_draw
	var started := Time.get_ticks_usec()
	var prior := started
	for i in SAMPLES:
		await process_frame
		await RenderingServer.frame_post_draw
		var now := Time.get_ticks_usec()
		intervals[i] = (now - prior) / 1000.0
		prior = now
		process_ms[i] = Performance.get_monitor(Performance.TIME_PROCESS) * 1000.0
		static_peak = maxf(static_peak, Performance.get_monitor(Performance.MEMORY_STATIC) / 1048576.0)
		nodes_min = mini(nodes_min, get_node_count())
		nodes_max = maxi(nodes_max, get_node_count())
		var draws := Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME)
		var primitives := Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME)
		var textures := Performance.get_monitor(Performance.RENDER_TEXTURE_MEM_USED) / 1048576.0
		draw_min = minf(draw_min, draws)
		draw_max = maxf(draw_max, draws)
		primitives_min = minf(primitives_min, primitives)
		primitives_max = maxf(primitives_max, primitives)
		texture_min = minf(texture_min, textures)
		texture_max = maxf(texture_max, textures)
	var elapsed := (prior - started) / 1000000.0
	var static_end := Performance.get_monitor(Performance.MEMORY_STATIC) / 1048576.0
	static_peak = maxf(static_peak, static_end)
	var rss_end := rss_mb()
	var visual_after: Dictionary = view.descriptor()
	return {"state": state, "cycle": cycle, "warmup_frames": WARMUP, "samples": SAMPLES, "elapsed_seconds": elapsed, "frame_interval_ms": distribution(intervals), "process_proxy_ms": distribution(process_ms), "raw_frame_interval_ms": Array(intervals), "raw_process_proxy_ms": Array(process_ms), "rss_start_mb": rss_start, "rss_end_mb": rss_end, "rss_endpoint_peak_mb": maxf(rss_start, rss_end), "static_start_mb": static_start, "static_end_mb": static_end, "static_peak_mb": static_peak, "node_min": nodes_min, "node_max": nodes_max, "draw_min": draw_min, "draw_max": draw_max, "primitive_min": primitives_min, "primitive_max": primitives_max, "texture_min_mb": texture_min, "texture_max_mb": texture_max, "visual_build_count": visual_after.visual_build_count, "visual_node_count": visual_after.visual_node_count, "visual_apply_delta": visual_after.visual_apply_count - visual_before.visual_apply_count}

func capture_lifecycle(inventory: Dictionary) -> void:
	Engine.max_fps = 60
	DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_DISABLED)
	configure_camera("front")
	state_label.text = "T10 bounded steady-state performance fixture"
	var preview: Dictionary = engine.preview_transform("framework_anchor_seed_to_foundation", "capture-anchor", inventory)
	var intent: Dictionary = engine.commit_transform("benchmark-tx", "framework_anchor_seed_to_foundation", "capture-anchor", inventory)
	if not preview.passed or not intent.passed: quit(1); return
	# Warm both material/font states before sampling either.
	view.set_ready(preview)
	for i in WARMUP:
		await process_frame
		await RenderingServer.frame_post_draw
	if not view.show_commit(intent): quit(1); return
	for i in WARMUP:
		await process_frame
		await RenderingServer.frame_post_draw
	var phases: Array[Dictionary] = []
	var active_seconds := 0.0
	var idle_seconds := 0.0
	for cycle in CYCLES:
		view.set_ready(preview)
		var idle: Dictionary = await measure_phase("idle", cycle)
		phases.append(idle)
		idle_seconds += idle.elapsed_seconds
		if not view.show_commit(intent): quit(1); return
		var active: Dictionary = await measure_phase("committing", cycle)
		phases.append(active)
		active_seconds += active.elapsed_seconds
	var deltas: Array[Dictionary] = []
	for cycle in CYCLES:
		var idle: Dictionary = phases[cycle * 2]
		var active: Dictionary = phases[cycle * 2 + 1]
		deltas.append({"cycle": cycle, "frame_mean_ms": active.frame_interval_ms.mean - idle.frame_interval_ms.mean, "process_mean_ms": active.process_proxy_ms.mean - idle.process_proxy_ms.mean})
	var report := {"task_id": "T10", "candidate_commit": candidate, "engine": Engine.get_version_info().string, "renderer": RenderingServer.get_current_rendering_method() + "/" + RenderingServer.get_video_adapter_name(), "resolution": [capture_width, capture_height], "render_scale": root.scaling_3d_scale, "cycles": CYCLES, "frame_cap": 60, "fixed_fps": false, "measurement_io": false, "physical_certification": false, "cpu_frame_ms": null, "gpu_frame_ms_where_measurable": null, "method": "Warmed native4K software Vulkan fixture; wall-clock post-draw intervals include frame pacing; Godot TIME_PROCESS is a process proxy, not hardware CPU/GPU timing. RSS endpoints via ps outside each phase; static memory sampled each frame. No temperature or physical-device certification.", "phases": phases, "active_minus_idle": deltas, "active_seconds": active_seconds, "idle_seconds": idle_seconds, "active_duty_fraction": active_seconds / (active_seconds + idle_seconds), "passed": true}
	if not write_manifest(report): quit(1); return
	print(JSON.stringify({"passed": true, "candidate_commit": candidate, "phases": phases.size()}))
	quit(0)
