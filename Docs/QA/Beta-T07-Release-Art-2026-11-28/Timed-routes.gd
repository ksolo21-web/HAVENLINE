extends "res://tests/qa_snow_truck.gd"

func _initialize() -> void:
	run.call_deferred()

func describe(samples: Array[float]) -> Dictionary:
	samples.sort()
	return {
		"median": samples[samples.size() / 2],
		"p95": samples[ceili(.95 * samples.size()) - 1],
		"max": samples.back()
	}

func run() -> void:
	field = load("res://field_opening.tscn").instantiate()
	root.add_child(field)
	camera = field.camera
	truck = field.snow_truck
	origin = Vector2(root.get_visible_rect().size) * Vector2(.28, .71)
	for _step in 12: await physics_frame
	for id in ["center_hearth", "expansion_1", "storage_wood", "storage_stone", "storage_meat", "expansion_2", "camp_cooker", "saw_bench", "quarry_drill", "watchtower", "orbit_upgrade", "snow_garage", "snow_truck"]:
		_assert("funded " + id, _fund(id))
		for _step in 4: await physics_frame
	var trace: Dictionary = {}
	for leg in ["south_near", "east_return", "workshops"]:
		var bounds: Vector4 = field.field_env.COURTS[field.field_env.perimeter_stage - 1]
		match leg:
			"south_near": field.actor.global_position = Vector3(1.,0.,bounds.w+.4)
			"east_return": field.actor.global_position = Vector3(bounds.z+2.,0.,0.)
			"workshops": field.actor.global_position = Vector3.ZERO
		field.previous_dry_position = field.actor.global_position
		for _step in 150: await physics_frame
		var tick_wall_ms: Array[float] = []
		var skipped := 0
		var prior_tick := Engine.get_physics_frames()
		var prior_time := Time.get_ticks_usec()
		var context_states := {}
		for tick in 300:
			if tick % 100 == 0:
				steer(_heading(Vector3.FORWARD if tick == 0 else Vector3.BACK) if tick < 200 else Vector2.ZERO)
			await physics_frame
			var stamp := Time.get_ticks_usec()
			var frame := Engine.get_physics_frames()
			if prior_tick + 1 == frame: tick_wall_ms.append(float(stamp - prior_time)*.001)
			else: skipped += 1
			prior_tick = frame
			prior_time = stamp
			var state: String = field.context.descriptor.get("state", "")
			context_states[state] = 1+int(context_states.get(state,0))
		steer(Vector2.ZERO)
		trace[leg] = {"wall_ms_per_headless_tick": describe(tick_wall_ms), "samples": tick_wall_ms.size(), "skipped_simulation_ticks":skipped, "context_states":context_states}
	var output := {"renderer": RenderingServer.get_video_adapter_name(),
		"static_memory_mb": Performance.get_monitor(Performance.MEMORY_STATIC)/1048576.,
		"nodes": Performance.get_monitor(Performance.OBJECT_NODE_COUNT),
		"routes": trace, "fixtures": checks,
		"source": {"field": FileAccess.get_sha256("res://field_opening.gd"), "director":FileAccess.get_sha256("res://field_context_director.gd")}}
	print("T07_CONTEXT_ROUTE_METRICS ",JSON.stringify(output))
	await _close_field()
	quit(int(checks.values().has(false)))
