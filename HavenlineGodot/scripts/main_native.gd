extends "res://scripts/main.gd"

const NativeSimulation = preload("res://scripts/native_simulation.gd")
const RenderPolicy = preload("res://scripts/native_render_policy.gd")
const FrameRecorder = preload("res://scripts/native_frame_recorder.gd")
const WorldRenderer = preload("res://scripts/native_world_renderer.gd")
var world_batch_report: Dictionary = {}
var recorder = FrameRecorder.new()
var diagnostics_label: Label
var job_controls: Dictionary = {}
var review_stamp: Label
var qa_animation := ""
var qa_angle := 0.0
var qa_pose_seconds := .35
var qa_menu := false
var _ui_ready := false
var _last_status := ""
var worker_carry: Dictionary = {}

func _ready():
	sim = NativeSimulation.new()
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--qa-animation="): qa_animation = argument.trim_prefix("--qa-animation=")
		if argument.begins_with("--qa-angle="): qa_angle = float(argument.trim_prefix("--qa-angle="))
		if argument.begins_with("--qa-time="): qa_pose_seconds = float(argument.trim_prefix("--qa-time="))
		if argument == "--qa-menu": qa_menu = true
	super._ready()
	Engine.max_fps = RenderPolicy.frame_target(DisplayServer.screen_get_refresh_rate()) if DisplayServer.get_name() != "headless" else 60
	DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_ENABLED)
	# Protect against invisible enemy damage, including restored mid-wave saves.
	sim.threat_presentation_ready = false
	_ui_ready = true
	layout_safe_hud()
	if qa_menu:
		toggle_menu()

func actor(id: int) -> Node3D:
	var instance := super.actor(id)
	if id in [2, 3, 4]:
		var path := "res://assets/animations/Character%d.res" % id
		if not ResourceLoader.exists(path):
			push_error("Missing derived locomotion library; run tools/build_locomotion.gd before export.")
			return instance
		var visual: Node3D = instance.get_meta("visual")
		var player := AnimationPlayer.new()
		player.name = "NativeLocomotionReview"
		visual.add_child(player)
		player.root_node = NodePath("..")
		player.add_animation_library("derived", load(path))
		instance.set_meta("animation", player)
	return instance

func build_environment():
	super.build_environment()
	sun.light_energy = .72
	for child in world.get_children():
		if child is WorldEnvironment:
			child.environment.ambient_light_energy = .26
			child.environment.tonemap_exposure = .82

func resize_render():
	if not is_instance_valid(scene_view): return
	var desired := RenderPolicy.dimensions(size, render_review)
	if scene_view.size != desired:
		scene_view.size = desired
		if recorder: recorder.reset_segment()
	scene_view.scaling_3d_scale = 1.0
	if is_instance_valid(camera): camera.keep_aspect = Camera3D.KEEP_HEIGHT
	if _ui_ready: layout_safe_hud()
	queue_redraw()

func build_hud():
	super.build_hud()
	var panel := StyleBoxFlat.new()
	panel.bg_color = Color("142838")
	panel.border_color = Color("668190")
	panel.set_border_width_all(2)
	panel.set_corner_radius_all(18)
	panel.content_margin_left = 28
	panel.content_margin_right = 28
	panel.content_margin_top = 22
	panel.content_margin_bottom = 22
	menu.add_theme_stylebox_override("panel", panel)
	var column: VBoxContainer = menu.get_child(0)
	var scroll := ScrollContainer.new()
	scroll.custom_minimum_size.y = 210
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	column.add_child(scroll)
	column.move_child(scroll, 1)
	var jobs := VBoxContainer.new()
	jobs.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	jobs.add_theme_constant_override("separation", 10)
	scroll.add_child(jobs)
	text_label("Crew assignments", 26, jobs)
	for c in sim.companions:
		# NPC5 remains a missing-art blocker; never substitute a core identity for it.
		if c.id > 4: continue
		var row := HBoxContainer.new()
		jobs.add_child(row)
		var label := text_label("Character %d" % c.id, 23, row)
		label.custom_minimum_size.x = 190
		var selection := OptionButton.new()
		selection.custom_minimum_size = Vector2(260, 52)
		selection.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		selection.add_theme_font_size_override("font_size", 23)
		for job in NativeSimulation.JOBS:
			selection.add_item({"follow":"Follow lead", "gather":"Gather wood (legacy)", "wood":"Gather wood", "stone":"Gather stone", "metal":"Gather metal", "fuel":"Gather fuel", "guard":"Guard north defense"}[job])
		selection.select(NativeSimulation.JOBS.find(c.job))
		row.add_child(selection)
		var worker_id: int = c.id
		selection.item_selected.connect(func(index): sim.assign_job(worker_id, NativeSimulation.JOBS[index]))
		job_controls[worker_id] = {"row":row, "label":label, "selection":selection}
	var diagnostics := Button.new()
	diagnostics.text = "Save performance report"
	diagnostics.add_theme_font_size_override("font_size", 23)
	diagnostics.custom_minimum_size.y = 52
	column.add_child(diagnostics)
	diagnostics.pressed.connect(write_diagnostics)
	diagnostics_label = text_label("Native 4K is configured; physical 4K/60 is not certified.", 20, column)
	diagnostics_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	diagnostics_label.custom_minimum_size.x = 480
	for child in column.get_children():
		if child is Button: child.add_theme_font_size_override("font_size", 23)
	menu.remove_child(column)
	var menu_scroll := ScrollContainer.new()
	menu_scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	menu.add_child(menu_scroll)
	column.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	menu_scroll.add_child(column)
	review_stamp = text_label("DEVELOPMENT REVIEW · not the finished game", 18, self)
	review_stamp.modulate = Color(.82, .90, .98, .9)

func layout_safe_hud():
	var physical := DisplayServer.window_get_size()
	var safe := Rect2i(Vector2i.ZERO, physical)
	if OS.get_name() == "Android": safe = DisplayServer.get_display_safe_area()
	var area := RenderPolicy.logical_safe_rect(size, physical, safe).grow(-28)
	if area.size.x < 300 or area.size.y < 200: area = Rect2(Vector2(20,20), size - Vector2(40,40))
	status.set_anchors_preset(Control.PRESET_TOP_LEFT)
	status.position = area.position
	status.size = Vector2(minf(440, area.size.x * .3), 75)
	objective.set_anchors_preset(Control.PRESET_TOP_LEFT)
	objective.position = area.position + Vector2(area.size.x*.27, 2)
	objective.size = Vector2(area.size.x*.48, 85)
	objective.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	hint.set_anchors_preset(Control.PRESET_TOP_LEFT)
	hint.position = area.position + Vector2(area.size.x*.22, area.size.y-92)
	hint.size = Vector2(area.size.x*.56, 50)
	hint.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	for child in get_children():
		if child is Button and child.text == "Camp":
			child.set_anchors_preset(Control.PRESET_TOP_LEFT)
			child.position = Vector2(area.end.x-140, area.position.y)
			child.size = Vector2(140,64)
	menu.set_anchors_preset(Control.PRESET_TOP_LEFT)
	menu.size = Vector2(minf(760,area.size.x-20), minf(710,area.size.y-20))
	menu.position = area.get_center() - menu.size*.5
	if review_stamp:
		review_stamp.position = Vector2(area.position.x, area.end.y-25)
		review_stamp.size = Vector2(area.size.x,30)

func switch_lead(id: int):
	var previous: int = sim.lead
	if id != previous:
		for state in worker_carry.values(): state.node.queue_free()
		worker_carry.clear()
	if id != previous and job_controls.has(id):
		var control: Dictionary = job_controls[id]
		job_controls.erase(id)
		job_controls[previous] = control
		control.label.text = "Character %d" % previous
		for connection in control.selection.item_selected.get_connections():
			control.selection.item_selected.disconnect(connection.callable)
		control.selection.item_selected.connect(func(index): sim.assign_job(previous, NativeSimulation.JOBS[index]))
	super.switch_lead(id)

func toggle_menu():
	super.toggle_menu()
	if not paused: recorder.reset_segment()
	else: recorder.last_usec = 0
	if _ui_ready: layout_safe_hud()

func measure_frame():
	if not paused and not qa_mode:
		recorder.sample(Time.get_ticks_usec(), scene_view.size)

func write_diagnostics():
	var report: Dictionary = recorder.report({
		"game":"HAVENLINE", "engine":Engine.get_version_info().string,
		"os":OS.get_name(), "model":OS.get_model_name(),
		"renderer":RenderingServer.get_current_rendering_method(),
		"adapter":RenderingServer.get_video_adapter_name(),
		"internal_dimensions":[scene_view.size.x,scene_view.size.y],
		"render_scale":scene_view.scaling_3d_scale,
		"frame_cap":Engine.max_fps, "review_render":render_review, "forest_batching":world_batch_report
	})
	DirAccess.make_dir_recursive_absolute("user://diagnostics")
	var path := "user://diagnostics/native-performance.json"
	var file := FileAccess.open(path, FileAccess.WRITE)
	if file == null:
		diagnostics_label.text = "Report could not be saved (error %d)." % FileAccess.get_open_error()
		return
	file.store_string(JSON.stringify(report,"\t") + "\n")
	file.close()
	diagnostics_label.text = "Report saved. %d callback samples; not a device certification." % recorder.count

func _process(dt: float):
	super._process(dt)
	if not is_instance_valid(world): return
	for root_actor in actors.values():
		if not root_actor.has_meta("animation"): continue
		var animation: AnimationPlayer = root_actor.get_meta("animation")
		animation.speed_scale = 0.0 if paused else 1.0
		if qa_mode and qa_animation in ["idle","walk","run"]:
			for clip in animation.get_animation_list():
				if clip.ends_with(qa_animation):
					animation.play(clip)
					animation.seek(qa_pose_seconds,true)
					animation.speed_scale = 0.0
	if qa_mode and qa_angle != 0:
		var focus := xyz(sim.position) + Vector3(0,.95,0)
		camera.position = focus + Vector3(0,6.8,8.6).rotated(Vector3.UP,deg_to_rad(qa_angle))
		camera.look_at(focus)
	for worker in sim.companions:
		if actors.has(worker.id): sync_worker_cargo(worker)
	if sim.gate_open():
		objective.text = "Opening tasks complete · enemy presentation is not finished"

func _notification(what: int):
	super._notification(what)
	if what in [NOTIFICATION_APPLICATION_PAUSED, NOTIFICATION_APPLICATION_RESUMED]:
		if recorder:
			if what == NOTIFICATION_APPLICATION_RESUMED: recorder.reset_segment()
			else: recorder.last_usec = 0
		if _ui_ready: call_deferred("layout_safe_hud")

func _exit_tree():
	if not qa_mode or capture_directory.is_empty(): return
	var path := capture_directory.path_join("render-evidence.json")
	if not FileAccess.file_exists(path): return
	var report = JSON.parse_string(FileAccess.get_file_as_string(path))
	if not report is Dictionary: return
	report["active_script"] = get_script().resource_path
	report["active_script_sha256"] = FileAccess.get_sha256(get_script().resource_path)
	report["native_simulation_sha256"] = FileAccess.get_sha256("res://scripts/native_simulation.gd")
	report["source_character1_sha256"] = FileAccess.get_sha256("res://assets/characters/Character1.glb")
	report["pose_fixture"] = {"animation":qa_animation, "seconds":qa_pose_seconds, "camera_angle_degrees":qa_angle}
	report["forest_batching"] = world_batch_report
	report["human_visual_approval"] = false
	report["whole_rig_approval"] = false
	report["evidence_scope"] = "Actual engine-rendered visual fixture. Not physical Android frame-presentation evidence."
	var file := FileAccess.open(path,FileAccess.WRITE)
	if file:
		file.store_string(JSON.stringify(report,"\t") + "\n")
		file.close()

func sync_worker_cargo(worker: Dictionary):
	var id: int = worker.id
	var count: int = worker.get("cargo", 0)
	var kind: String = worker.get("cargo_kind", "wood")
	var state: Dictionary = worker_carry.get(id,{})
	if state.is_empty():
		var holder := Node3D.new()
		holder.name = "WorkerCargo"
		holder.position = Vector3(0,.78,-.42)
		actors[id].add_child(holder)
		state = {"node":holder,"count":-1,"kind":""}
		worker_carry[id] = state
	if state.count == count and state.kind == kind: return
	state.count = count
	state.kind = kind
	for child in state.node.get_children(): child.queue_free()
	for index in range(mini(count,4)):
		var piece := model("world/" + ("log" if kind == "wood" else kind), state.node, Vector3((index%2-.5)*.23,(index/2)*.18,0))
		piece.rotation_degrees.x = 90
		piece.scale = Vector3.ONE * (.65 if kind == "wood" else .22)

func model(asset: String, parent: Node3D, p := Vector3.ZERO) -> Node3D:
	var instance := super.model(asset,parent,p)
	instance.set_meta("source_asset",asset)
	return instance

func build_world():
	super.build_world()
	world_batch_report = WorldRenderer.batch_static_forest(world,resource_visuals)
