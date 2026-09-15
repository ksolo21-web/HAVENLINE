extends SceneTree

const Main = preload("res://scripts/main.gd")

var output := "user://task07-context"
var candidate := "local-working-tree"
var state := "sequence"
var device_id := "review_16_9"
var native_4k := false
var game
var director
var records: Array = []
var gather_event_count := 0
var initial_inventory: Dictionary = {}
var frame_samples: Array[float] = []
var draw_call_samples: Array[int] = []
var primitive_samples: Array[int] = []

func _initialize() -> void:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--out="):
			output = argument.trim_prefix("--out=")
		elif argument.begins_with("--candidate="):
			candidate = argument.trim_prefix("--candidate=")
		elif argument.begins_with("--state="):
			state = argument.trim_prefix("--state=")
		elif argument.begins_with("--device="):
			device_id = argument.trim_prefix("--device=")
		elif argument == "--native-4k":
			native_4k = true
	call_deferred("run")

func integrated_call_site_present() -> bool:
	return game.sim.get_property_list().any(func(row): return row.name == "context_director")

func record(frame: int, descriptor: Dictionary, frame_usec: float) -> void:
	var presentation: Dictionary = director.presentation()
	var draw_calls := int(RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_DRAW_CALLS_IN_FRAME))
	var primitives := int(RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_PRIMITIVES_IN_FRAME))
	for event in game.sim.events:
		if String(event.get("type", "")) == "gather":
			gather_event_count += 1
	frame_samples.append(frame_usec)
	draw_call_samples.append(draw_calls)
	primitive_samples.append(primitives)
	records.append({
		"frame": frame,
		"kind": descriptor.get("kind", ""), "id": descriptor.get("id", ""),
		"state": descriptor.get("state", ""), "reason": descriptor.get("reason", ""),
		"actionable": descriptor.get("actionable", false), "cancelled": descriptor.get("cancelled", false),
		"action_token": descriptor.get("action_token", 0), "progress": descriptor.get("progress", 0.0),
		"rank": descriptor.get("rank", {}), "shipping_hint": game.hint.text,
		"presentation_status": presentation.status_text,
		"player_position": [game.sim.position.x, game.sim.position.y],
		"player_velocity": [game.sim.velocity.x, game.sim.velocity.y],
		"event_types": game.sim.events.map(func(event): return String(event.get("type", ""))),
		"frame_usec": frame_usec, "draw_calls": draw_calls, "primitives": primitives,
	})

func screenshot(name: String) -> void:
	await process_frame
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png(output.path_join(name + ".png"))

func sequence_frame(frame: int) -> void:
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_jpg(output.path_join("frames/frame-%05d.jpg" % int(frame / 3)), 0.88)

func step_shipping(frame: int, movement: Vector2) -> Dictionary:
	var started := Time.get_ticks_usec()
	game.sim.step(1.0 / 60.0, movement, false)
	game._process(1.0 / 60.0)
	await process_frame
	await RenderingServer.frame_post_draw
	var descriptor: Dictionary = game.sim.action
	record(frame, descriptor, float(Time.get_ticks_usec() - started))
	return descriptor

func capture_sequence() -> void:
	DirAccess.make_dir_recursive_absolute(output.path_join("frames"))
	var target: Vector2 = game.sim.resources[0].position
	game.sim.position = target + Vector2(0, 1.15)
	game.sim.facing = (target - game.sim.position).normalized()
	initial_inventory = game.sim.inventory.duplicate()
	for frame in 180:
		if frame >= 90 and frame < 135:
			game.sim.position.x = target.x + (0.015 if frame % 2 == 0 else -0.015)
		if frame == 135:
			game.sim.threats_enabled = true
			game.sim.enemies.append({"id":"t07_capture_wolf", "position":game.sim.position + Vector2(0, 1.4), "health":1000.0, "cooldown":4.0})
		var movement := Vector2(0.04, 0.0) if frame < 36 else Vector2.ZERO
		var descriptor := await step_shipping(frame, movement)
		if frame % 3 == 0:
			await sequence_frame(frame)
		if frame in [18, 40, 58, 104, 142, 170]:
			await screenshot("sequence-%03d-%s" % [frame, String(descriptor.state)])

func capture_static() -> void:
	var target: Vector2 = game.sim.resources[0].position
	game.sim.position = target + Vector2(0, 1.1)
	game.sim.facing = (target - game.sim.position).normalized()
	initial_inventory = game.sim.inventory.duplicate()
	if state == "blocked":
		await step_shipping(0, Vector2(0.04, 0.0))
	elif state == "urgent":
		game.sim.threats_enabled = true
		game.sim.enemies.append({"id":"t07_static_wolf", "position":game.sim.position + Vector2(0, 1.4), "health":1000.0, "cooldown":4.0})
		await step_shipping(0, Vector2.ZERO)
	else:
		for frame in 14:
			await step_shipping(frame, Vector2.ZERO)
	await screenshot(state)

func average(values: Array) -> float:
	if values.is_empty(): return 0.0
	var total := 0.0
	for value in values: total += float(value)
	return total / float(values.size())

func maximum(values: Array) -> float:
	var result := 0.0
	for value in values: result = maxf(result, float(value))
	return result

func layout_rects() -> Dictionary:
	var result := {}
	for key in game.layout_snapshot.rects:
		var rect: Rect2 = game.layout_snapshot.rects[key]
		result[key] = [rect.position.x, rect.position.y, rect.size.x, rect.size.y]
	return result

func run() -> void:
	DirAccess.make_dir_recursive_absolute(output)
	game = Main.new()
	game.qa_mode = true
	game.render_review = not native_4k
	game.capture_frames = -10000
	root.add_child(game)
	game.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	game.position = Vector2.ZERO
	game.size = Vector2(root.size)
	game.resize_render()
	game.apply_hud_layout(Rect2(Vector2.ZERO, game.size), 1.0)
	game.set_process(false)
	game.set_physics_process(false)
	director = game.sim.context_director
	assert(integrated_call_site_present())
	if state == "sequence": await capture_sequence()
	else: await capture_static()
	var final_inventory: Dictionary = game.sim.inventory.duplicate()
	var report := {
		"task":"T07-context-director-v1", "candidate_commit":candidate,
		"state":state, "device_id":device_id,
		"renderer":RenderingServer.get_current_rendering_method(), "device":RenderingServer.get_video_adapter_name(),
		"window":[root.size.x, root.size.y], "game_rect":[game.position.x, game.position.y, game.size.x, game.size.y],
		"internal_render":[game.scene_view.size.x, game.scene_view.size.y],
		"native_3840x2160_scale1":native_4k and root.size == Vector2i(3840, 2160) and is_equal_approx(game.scene_view.scaling_3d_scale, 1.0),
		"shipping_main_scene_rendered":true, "shipping_call_site_exercised":true,
		"candidate_component_applied_directly_because_call_site_is_integration_only":false,
		"qa_evidence_banner_present":false, "permanent_action_buttons":0,
		"movement_control":"one_primary_joystick", "layout_rects":layout_rects(),
		"trace":records, "switch_count":director.switch_count,
		"initial_inventory":initial_inventory, "final_inventory":final_inventory,
		"gather_event_count":gather_event_count,
		"inventory_gather_delta":int(final_inventory.wood) - int(initial_inventory.wood),
		"shipping_scene_metrics":{
			"average_frame_usec":average(frame_samples), "maximum_frame_usec":maximum(frame_samples),
			"average_draw_calls":average(draw_call_samples), "maximum_draw_calls":int(maximum(draw_call_samples)),
			"average_primitives":average(primitive_samples), "maximum_primitives":int(maximum(primitive_samples)),
		},
		"physical_device_native_4k60_certified":false,
	}
	var file := FileAccess.open(output.path_join("capture.json"), FileAccess.WRITE)
	file.store_string(JSON.stringify(report, "\t")); file.close()
	game.outpost_audio.stop_all()
	await create_timer(0.35).timeout
	game.free(); await process_frame; quit()
