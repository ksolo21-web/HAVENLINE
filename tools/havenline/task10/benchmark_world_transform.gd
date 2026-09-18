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
	var pulse_samples: Array = []
	pulse_samples.resize(SAMPLES)
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
	var identity_before := presentation_identity()
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
		pulse_samples[i] = {"time": view._pulse_time, "scale": [view._ghost.scale.x, view._ghost.scale.y, view._ghost.scale.z], "y": view._ghost.position.y}
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
	return {"raw_pulse_samples": pulse_samples, "base_scale": [view._target_form_scale().x, view._target_form_scale().y, view._target_form_scale().z], "identity_before": identity_before, "identity_after": presentation_identity(), "view_visible": view.visible, "pulse_enabled": view.is_processing(), "state": state, "cycle": cycle, "warmup_frames": WARMUP, "samples": SAMPLES, "elapsed_seconds": elapsed, "frame_interval_ms": distribution(intervals), "process_proxy_ms": distribution(process_ms), "raw_frame_interval_ms": Array(intervals), "raw_process_proxy_ms": Array(process_ms), "rss_start_mb": rss_start, "rss_end_mb": rss_end, "rss_endpoint_peak_mb": maxf(rss_start, rss_end), "static_start_mb": static_start, "static_end_mb": static_end, "static_peak_mb": static_peak, "node_min": nodes_min, "node_max": nodes_max, "draw_min": draw_min, "draw_max": draw_max, "primitive_min": primitives_min, "primitive_max": primitives_max, "texture_min_mb": texture_min, "texture_max_mb": texture_max, "visual_build_count": visual_after.visual_build_count, "visual_node_count": visual_after.visual_node_count, "visual_apply_delta": visual_after.visual_apply_count - visual_before.visual_apply_count}

func presentation_identity() -> Dictionary:
	return {"descriptor": view.descriptor(), "view_id": view.get_instance_id(), "ring_mesh": view._ring.mesh.get_instance_id(), "ghost_mesh": view._ghost.mesh.get_instance_id(), "ring_material": view._ring_material.get_instance_id(), "ghost_material": view._ghost_material.get_instance_id(), "ring_color": str(view._ring_material.albedo_color), "ghost_color": str(view._ghost_material.albedo_color), "ghost_transparency": view._ghost_material.transparency, "label_text": view._beacon.text, "camera_transform": str(camera.global_transform), "camera_size": camera.size}

func isolate_update_cost() -> Dictionary:
	view.set_process(false)
	var gross := PackedFloat64Array()
	var empty := PackedFloat64Array()
	var calls := 100
	for batch in 20:
		await process_frame
		await RenderingServer.frame_post_draw
		var start := Time.get_ticks_usec()
		for i in calls:
			pass
		empty.append(float(Time.get_ticks_usec() - start) / calls)
		start = Time.get_ticks_usec()
		for i in calls:
			view._process(1.0 / 60.0)
		gross.append(float(Time.get_ticks_usec() - start) / calls)
	return {"batches": 20, "calls_per_batch": calls, "raw_gross_usec_per_call": Array(gross), "raw_empty_usec_per_call": Array(empty), "gross_usec_per_call": distribution(gross), "empty_usec_per_call": distribution(empty), "method": "Direct view._process(1/60), including transform setters and render command submission, with empty-loop overhead separately measured. Frame awaits are outside batches; this is not whole-frame CPU or GPU time."}

func capture_lifecycle(inventory: Dictionary) -> void:
	Engine.max_fps = 60
	DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_DISABLED)
	configure_camera("front")
	state_label.text = "T10 matched committing performance controls"
	var intent: Dictionary = engine.commit_transform("benchmark-tx", "framework_anchor_seed_to_foundation", "capture-anchor", inventory)
	if not intent.passed or not view.show_commit(intent): quit(1); return
	var phases: Array[Dictionary] = []
	var active_seconds := 0.0
	var idle_seconds := 0.0
	for cycle in CYCLES:
		for state in ["hidden", "frozen", "pulse"]:
			view.set_process(false)
			view._pulse_time = 0.0
			view._process(0.0)
			view.visible = state != "hidden"
			view.set_process(state == "pulse")
			var measured: Dictionary = await measure_phase(state, cycle)
			phases.append(measured)
			if state == "pulse": active_seconds += measured.elapsed_seconds
			elif state == "frozen": idle_seconds += measured.elapsed_seconds
			print(JSON.stringify({"cycle": cycle, "completed_control": state}))
	var deltas: Array[Dictionary] = []
	for cycle in CYCLES:
		var hidden: Dictionary = phases[cycle * 3]
		var frozen: Dictionary = phases[cycle * 3 + 1]
		var pulse: Dictionary = phases[cycle * 3 + 2]
		deltas.append({"cycle": cycle, "frame_mean_ms": pulse.frame_interval_ms.mean - frozen.frame_interval_ms.mean, "process_mean_ms": pulse.process_proxy_ms.mean - frozen.process_proxy_ms.mean, "presentation_frame_mean_ms": frozen.frame_interval_ms.mean - hidden.frame_interval_ms.mean, "presentation_process_mean_ms": frozen.process_proxy_ms.mean - hidden.process_proxy_ms.mean})
	var isolated: Dictionary = await isolate_update_cost()
	var report := {"task_id": "T10", "candidate_commit": candidate, "engine": Engine.get_version_info().string, "engine_version": Engine.get_version_info(), "renderer": RenderingServer.get_current_rendering_method() + "/" + RenderingServer.get_video_adapter_name(), "resolution": [capture_width, capture_height], "render_scale": root.scaling_3d_scale, "cycles": CYCLES, "frame_cap": 60, "fixed_fps": false, "measurement_io": false, "physical_certification": false, "cpu_frame_ms": null, "gpu_frame_ms_where_measurable": null, "method": "Warmed native4K software Vulkan matched committing fixture. Hidden baseline; visible frozen pulse-off; same presentation with pulse enabled. Pulse changes screen coverage, so pulse-minus-frozen includes rasterization, not pure CPU cost. Wall-clock post-draw intervals include pacing; TIME_PROCESS is a proxy. RSS endpoints via ps outside phases; static memory sampled each frame. No temperature, physical-device certification or hardware headroom claim.", "phases": phases, "isolated_update": isolated, "active_minus_idle": deltas, "active_seconds": active_seconds, "idle_seconds": idle_seconds, "active_duty_fraction": active_seconds / (active_seconds + idle_seconds), "passed": true}
	if not write_manifest(report): quit(1); return
	print(JSON.stringify({"passed": true, "candidate_commit": candidate, "phases": phases.size()}))
	quit(0)
