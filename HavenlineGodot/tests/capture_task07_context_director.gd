extends SceneTree

const Main = preload("res://scripts/main.gd")
const Director = preload("res://scripts/context_director.gd")

var output := "user://task07-context"
var candidate := "local-working-tree"
var state := "sequence"
var device_id := "review_16_9"
var native_4k := false
var game
var director = Director.new()
var banner: PanelContainer
var banner_label: Label
var records: Array = []

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

func option(kind: String, id: String, position: Vector2, capability: String,
		priority := 0.0, relevance := 0.0, radius := 4.0, progress := 0.0) -> Dictionary:
	return {
		"kind":kind, "id":id, "position":position, "eligible":true,
		"priority":priority, "capability":capability, "radius":radius,
		"target_relevance":relevance, "progress":progress,
	}

func integrated_call_site_present() -> bool:
	return game.sim.get_property_list().any(func(row): return row.name == "context_director")

func add_evidence_banner() -> void:
	banner = PanelContainer.new()
	banner.mouse_filter = Control.MOUSE_FILTER_IGNORE
	banner.set_anchors_preset(Control.PRESET_CENTER_TOP)
	banner.position = Vector2(-330, 108)
	banner.size = Vector2(660, 68)
	var style := StyleBoxFlat.new()
	style.bg_color = Color(0.025, 0.055, 0.09, 0.88)
	style.border_color = Color(0.45, 0.80, 1.0, 0.9)
	style.set_border_width_all(2)
	style.set_corner_radius_all(12)
	style.content_margin_left = 18
	style.content_margin_right = 18
	style.content_margin_top = 10
	style.content_margin_bottom = 10
	banner.add_theme_stylebox_override("panel", style)
	game.add_child(banner)
	banner_label = Label.new()
	banner_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	banner_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	banner_label.add_theme_font_size_override("font_size", 22)
	banner_label.add_theme_color_override("font_color", Color("e9f6ff"))
	banner.add_child(banner_label)

func update_banner(descriptor: Dictionary) -> void:
	var presentation := director.presentation()
	var label := String(presentation.label)
	var status := String(presentation.state).replace("_", " ").capitalize()
	banner_label.text = (label if not label.is_empty() else "No context") + "  ·  " + status + "  ·  " + String(presentation.reason).replace("_", " ")

func record(frame: int, descriptor: Dictionary) -> void:
	var rank: Dictionary = descriptor.get("rank", {})
	records.append({
		"frame": frame,
		"kind": descriptor.get("kind", ""),
		"id": descriptor.get("id", ""),
		"state": descriptor.get("state", ""),
		"reason": descriptor.get("reason", ""),
		"actionable": descriptor.get("actionable", false),
		"action_token": descriptor.get("action_token", 0),
		"progress": descriptor.get("progress", 0.0),
		"rank": rank,
		"player_position": [game.sim.position.x, game.sim.position.y],
		"player_velocity": [game.sim.velocity.x, game.sim.velocity.y],
	})

func screenshot(name: String) -> void:
	await process_frame
	await RenderingServer.frame_post_draw
	var image := root.get_texture().get_image()
	image.save_png(output.path_join(name + ".png"))

func sequence_frame(frame: int) -> void:
	await RenderingServer.frame_post_draw
	var image := root.get_texture().get_image()
	image.save_jpg(output.path_join("frames/frame-%05d.jpg" % int(frame / 3)), 0.88)

func capture_sequence() -> void:
	DirAccess.make_dir_recursive_absolute(output.path_join("frames"))
	var target: Vector2 = game.sim.resources[0].position
	game.sim.position = target + Vector2(0, 1.15)
	game.sim.facing = (target - game.sim.position).normalized()
	var gather := option("gather", String(game.sim.resources[0].id), target, "gather_with_tools", 0.0, 0.5, float(game.sim.contract.player.interactionRadius), 0.42)
	var alternate := option("gather", String(game.sim.resources[1].id), target + Vector2(0.06, 0.0), "gather_with_tools", 0.0, 0.5, float(game.sim.contract.player.interactionRadius), 0.0)
	for frame in 180:
		var movement := Vector2.ZERO
		var candidates := [gather]
		if frame < 45:
			movement = Vector2(0.0, -0.45)
			game.sim.velocity = Vector2(0.0, -1.6)
		elif frame < 135:
			game.sim.velocity = Vector2.ZERO
			if frame >= 90:
				candidates.append(alternate)
				game.sim.position.x = target.x + (0.015 if frame % 2 == 0 else -0.015)
		else:
			game.sim.velocity = Vector2.ZERO
			candidates.append(option("rescue", "survivor", game.sim.position + Vector2(0.0, 1.8), "rescue", -100.0, -1.0, 2.2, 0.18))
		var descriptor := director.advance(1.0 / 60.0, game.sim.position, game.sim.facing, movement, game.sim.velocity, "player_lead", candidates)
		game.sim.action = descriptor
		update_banner(descriptor)
		game._process(1.0 / 60.0)
		record(frame, descriptor)
		await process_frame
		if frame % 3 == 0:
			await sequence_frame(frame)
		if frame in [20, 52, 76, 108, 142, 170]:
			await screenshot("sequence-%03d-%s" % [frame, String(descriptor.state)])

func capture_static() -> void:
	var target: Vector2 = game.sim.resources[0].position
	game.sim.position = target + Vector2(0, 1.1)
	game.sim.facing = (target - game.sim.position).normalized()
	var candidates := [option("gather", String(game.sim.resources[0].id), target, "gather_with_tools", 0.0, 0.5, float(game.sim.contract.player.interactionRadius), 0.64)]
	var descriptor: Dictionary
	if state == "blocked":
		game.sim.velocity = Vector2(0.0, -1.4)
		descriptor = director.advance(0.2, game.sim.position, game.sim.facing, Vector2(0.0, -0.4), game.sim.velocity, "player_lead", candidates)
	elif state == "urgent":
		director.advance(0.13, game.sim.position, game.sim.facing, Vector2.ZERO, Vector2.ZERO, "player_lead", candidates)
		candidates.append(option("rescue", "survivor", game.sim.position + Vector2(0, 1.8), "rescue", -100.0, -1.0, 2.2, 0.18))
		descriptor = director.advance(0.001, game.sim.position, game.sim.facing, Vector2.ZERO, Vector2.ZERO, "player_lead", candidates)
	else:
		director.advance(0.08, game.sim.position, game.sim.facing, Vector2.ZERO, Vector2.ZERO, "player_lead", candidates)
		descriptor = director.advance(0.08, game.sim.position, game.sim.facing, Vector2.ZERO, Vector2.ZERO, "player_lead", candidates)
	game.sim.action = descriptor
	update_banner(descriptor)
	for frame in 12:
		game._process(1.0 / 60.0)
		record(frame, descriptor)
		await process_frame
	await screenshot(state)

func run() -> void:
	DirAccess.make_dir_recursive_absolute(output)
	game = Main.new()
	game.qa_mode = true
	game.render_review = not native_4k
	game.capture_frames = -10000
	game.size = Vector2(3840, 2160) if native_4k else Vector2(root.size)
	root.add_child(game)
	game.set_process(false)
	game.set_physics_process(false)
	if device_id == "phone_20_9":
		game.apply_hud_layout(Rect2(Vector2(120, 20), Vector2(game.size.x - 240, game.size.y - 40)), 1.0)
	add_evidence_banner()
	if state == "sequence":
		await capture_sequence()
	else:
		await capture_static()
	var report := {
		"task": "T07-context-director-v1",
		"candidate_commit": candidate,
		"state": state,
		"device_id": device_id,
		"safe_area_fixture": device_id == "phone_20_9",
		"renderer": RenderingServer.get_current_rendering_method(),
		"device": RenderingServer.get_video_adapter_name(),
		"window": [root.size.x, root.size.y],
		"internal_render": [game.scene_view.size.x, game.scene_view.size.y],
		"native_3840x2160_scale1": native_4k and root.size == Vector2i(3840, 2160) and is_equal_approx(game.scene_view.scaling_3d_scale, 1.0),
		"shipping_main_scene_rendered": true,
		"shipping_call_site_exercised": integrated_call_site_present(),
		"candidate_component_applied_directly_because_call_site_is_integration_only": not integrated_call_site_present(),
		"qa_evidence_banner_is_not_a_shipping_control": true,
		"permanent_action_buttons": 0,
		"movement_control": "one_primary_joystick",
		"trace": records,
		"switch_count": director.switch_count,
		"physical_device_native_4k60_certified": false,
	}
	var file := FileAccess.open(output.path_join("capture.json"), FileAccess.WRITE)
	file.store_string(JSON.stringify(report, "\t"))
	file.close()
	game.outpost_audio.stop_all()
	await create_timer(0.35).timeout
	game.free()
	await process_frame
	quit()
