extends Control

const Simulation = preload("res://scripts/simulation.gd")
const Saves = preload("res://scripts/save_store.gd")
const UHD_PIXELS := 3840 * 2160
var sim = Simulation.new()
var scene_view: SubViewport
var world: Node3D
var camera: Camera3D
var sun: DirectionalLight3D
var actors: Dictionary = {}
var resource_visuals: Dictionary = {}
var defense_visuals: Dictionary = {}
var asset_cache: Dictionary = {}
var player_rig: Node3D
var carry_root: Node3D
var carry_count := -1
var furnace: Node3D
var heat_light: OmniLight3D
var status: Label
var objective: Label
var hint: Label
var joystick_origin := Vector2.ZERO
var joystick_current := Vector2.ZERO
var joystick_id := -1
var paused := false
var menu: PanelContainer
var save_timer := 0.0
var capture_frames := 0
var capture_directory := ""
var qa_mode := false
var render_review := false
var frame_intervals: Array = []
var last_frame_usec := 0
var warmup_frames := 180

func _ready():
	Engine.max_fps = 60
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--capture="):
			capture_directory = argument.trim_prefix("--capture=")
			qa_mode = true
		if argument == "--render-review": render_review = true
	# Review uses the same scene and materials at a disclosed smaller render size.
	# It never grants the 4K/60 performance gate.
	if not qa_mode:
		var saved := Saves.read_state()
		if not saved.is_empty():
			sim.restore(saved)
	scene_view = SubViewport.new()
	scene_view.own_world_3d = true
	scene_view.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	scene_view.msaa_3d = Viewport.MSAA_2X
	scene_view.scaling_3d_scale = 1.0
	add_child(scene_view)
	var display := TextureRect.new()
	display.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	display.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	display.stretch_mode = TextureRect.STRETCH_SCALE
	display.texture = scene_view.get_texture()
	display.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(display)
	world = Node3D.new()
	scene_view.add_child(world)
	build_environment()
	build_world()
	build_crew()
	build_hud()
	resized.connect(resize_render)
	resize_render()
	if qa_mode:
		DirAccess.make_dir_recursive_absolute(capture_directory)

func resize_render():
	if not is_instance_valid(scene_view): return
	var aspect := maxf(1.0, size.x / maxf(1.0, size.y))
	var pixels := 1280 * 720 if render_review else UHD_PIXELS
	var height := int(ceil(sqrt(float(pixels) / aspect)))
	scene_view.size = Vector2i(int(ceil(height * aspect)), height)
	if is_instance_valid(camera): camera.keep_aspect = Camera3D.KEEP_HEIGHT
	queue_redraw()

func build_environment():
	var environment := Environment.new()
	environment.background_mode = Environment.BG_COLOR
	environment.background_color = Color("577b9a")
	environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	environment.ambient_light_color = Color("c1d9f0")
	environment.ambient_light_energy = 0.38
	environment.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	environment.tonemap_exposure = 0.9
	environment.fog_enabled = true
	environment.fog_light_color = Color("89adcc")
	environment.fog_density = 0.007
	var sky := WorldEnvironment.new()
	sky.environment = environment
	world.add_child(sky)
	sun = DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-48, -32, 0)
	sun.light_color = Color("e4f0ff")
	sun.light_energy = 1.05
	sun.shadow_enabled = true
	sun.directional_shadow_max_distance = 45
	world.add_child(sun)
	camera = Camera3D.new()
	camera.projection = Camera3D.PROJECTION_ORTHOGONAL
	# Unity orthographicSize is a half-height; Godot's size is the full span.
	camera.size = float(sim.contract.camera.size) * 2.0
	camera.far = 100
	world.add_child(camera)
	camera.current = true

func model(asset: String, parent: Node3D, p := Vector3.ZERO) -> Node3D:
	var path := "res://assets/" + asset + ".glb"
	if not asset_cache.has(path):
		asset_cache[path] = load(path)
	var instance: Node3D = asset_cache[path].instantiate()
	parent.add_child(instance)
	instance.position = p
	return instance

func build_world():
	model("world/terrain", world)
	furnace = model("world/furnace", world, xyz(Simulation.point(sim.contract.world.furnace)))
	heat_light = OmniLight3D.new()
	heat_light.position = Vector3(0, 1.2, 0.6)
	heat_light.light_color = Color("ff913d")
	heat_light.light_energy = 3
	heat_light.omni_range = 5
	furnace.add_child(heat_light)
	model("world/storage", world, xyz(Simulation.point(sim.contract.world.storage)))
	for x in [-6.6, 6.6]:
		var shelter := model("world/shelter", world, Vector3(x, 0, -4.8))
		shelter.rotation.y = -0.12 if x < 0 else 0.12
	for index in range(sim.resources.size()):
		var node: Dictionary = sim.resources[index]
		var asset: String = "pine_" + str(1 + index % 3) if node.kind == "wood" else node.kind
		resource_visuals[node.id] = model("world/" + asset, world, xyz(node.position))
	for i in range(38):
		var a := i * TAU / 38.0
		var p := Vector3(cos(a) * (15.5 + sin(i * 12.2)), 0, sin(a) * 18.8)
		var tree := model("world/pine_" + str(1 + i % 3), world, p)
		tree.scale = Vector3.ONE * (0.85 + fmod(i * .17, .5))
		tree_rotation(tree, i)
	for side in sim.defenses:
		defense_visuals[side] = model("world/barricade", world, xyz(sim.defenses[side].position))
		defense_visuals[side].scale.y = 0.15

func tree_rotation(tree: Node3D, index: int):
	tree.rotation.y = index * 1.71

func xyz(p: Vector2) -> Vector3:
	return Vector3(p.x, 0, p.y)

func gather_meshes(node: Node, output: Array):
	if node is MeshInstance3D: output.append(node)
	for child in node.get_children(): gather_meshes(child, output)

func actor(id: int) -> Node3D:
	var root := Node3D.new()
	root.name = "Character" + str(id)
	world.add_child(root)
	var visual := model("characters/Character" + str(id), root)
	var meshes: Array = []
	gather_meshes(visual, meshes)
	var bounds := AABB()
	var first := true
	for mesh in meshes:
		var box: AABB = root.global_transform.affine_inverse() * mesh.global_transform * mesh.get_aabb()
		bounds = box if first else bounds.merge(box)
		first = false
	var factor := 1.75 / maxf(0.01, bounds.size.y)
	visual.scale *= factor
	visual.position = Vector3(-bounds.get_center().x, -bounds.position.y, -bounds.get_center().z) * factor
	var animation := find_animation_player(visual)
	if animation:
		for clip in animation.get_animation_list():
			if not clip.ends_with("RESET"):
				animation.get_animation(clip).loop_mode = Animation.LOOP_LINEAR
		root.set_meta("animation", animation)
	root.set_meta("visual", visual)
	return root

func find_animation_player(node: Node) -> AnimationPlayer:
	if node is AnimationPlayer: return node
	for child in node.get_children():
		var found := find_animation_player(child)
		if found: return found
	return null

func build_crew():
	for id in range(1, 5): actors[id] = actor(id)
	player_rig = actors[sim.lead]
	carry_root = Node3D.new()
	carry_root.position = Vector3(0, .65, -.42)
	player_rig.add_child(carry_root)

func animate(root: Node3D, speed: float):
	if not root.has_meta("animation"): return
	var animation: AnimationPlayer = root.get_meta("animation")
	var desired := "run" if speed > 4.3 else ("walk" if speed > .15 else "idle")
	for clip in animation.get_animation_list():
		if clip.to_lower().ends_with(desired):
			if animation.current_animation != clip: animation.play(clip, .16)
			# Use source cadence; integration locomotion review must verify sliding.
			animation.speed_scale = 1.0
			return

func update_carry():
	var count: int = sim.carried()
	if count == carry_count: return
	carry_count = count
	for child in carry_root.get_children(): child.queue_free()
	var shown := mini(count, 32)
	for i in range(shown):
		var sample := int(float(i) * count / maxf(1, shown))
		var kind := "wood"
		var cumulative := 0
		for resource in Simulation.KINDS:
			cumulative += sim.inventory[resource]
			if sample < cumulative:
				kind = resource
				break
		var piece := model("world/" + ("log" if kind == "wood" else kind), carry_root, Vector3((i % 3 - 1) * .19, (i / 3) * .10, 0))
		piece.rotation_degrees.x = 90
		piece.scale = Vector3.ONE * (.63 if kind == "wood" else .18)
	# Visual pooling is bounded; logical carrying is unlimited.
	# Growth continues logarithmically after 32 meshes without deleting inventory.
	carry_root.scale = Vector3.ONE * (1.0 + log(1.0 + maxf(0, count - 32) / 32.0) * .08)

func text_label(text: String, font_size: int, parent: Control) -> Label:
	var label := Label.new()
	label.text = text
	label.add_theme_font_size_override("font_size", font_size)
	label.add_theme_color_override("font_color", Color("f0f7ff"))
	label.add_theme_color_override("font_shadow_color", Color(0.015, .035, .07, .9))
	label.add_theme_constant_override("shadow_offset_x", 1)
	label.add_theme_constant_override("shadow_offset_y", 2)
	label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	parent.add_child(label)
	return label

func build_hud():
	status = text_label("", 27, self)
	status.position = Vector2(40, 30)
	objective = text_label("", 25, self)
	objective.set_anchors_and_offsets_preset(Control.PRESET_CENTER_TOP)
	objective.position.y = 35
	objective.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	objective.size.x = 780
	objective.position.x = size.x / 2 - 390
	hint = text_label("Move close. Your survivor takes care of the rest.", 24, self)
	hint.set_anchors_and_offsets_preset(Control.PRESET_CENTER_BOTTOM)
	hint.position = Vector2(size.x / 2 - 350, size.y - 64)
	hint.size.x = 700
	hint.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	var pause_button := Button.new()
	add_child(pause_button)
	pause_button.text = "Camp"
	pause_button.add_theme_font_size_override("font_size", 26)
	pause_button.set_anchors_and_offsets_preset(Control.PRESET_TOP_RIGHT)
	pause_button.position = Vector2(size.x - 160, 28)
	pause_button.size = Vector2(122, 64)
	pause_button.pressed.connect(toggle_menu)
	menu = PanelContainer.new()
	add_child(menu)
	menu.visible = false
	menu.set_anchors_and_offsets_preset(Control.PRESET_CENTER)
	menu.position = size / 2 - Vector2(220, 150)
	menu.size = Vector2(440, 300)
	var column := VBoxContainer.new()
	column.add_theme_constant_override("separation", 20)
	menu.add_child(column)
	text_label("HAVENLINE · Camp", 32, column)
	for id in [1, 2]:
		var choice := Button.new()
		choice.text = "Lead with Character " + str(id)
		choice.custom_minimum_size.y = 64
		choice.add_theme_font_size_override("font_size", 26)
		column.add_child(choice)
		choice.pressed.connect(func(): switch_lead(id))
	var resume := Button.new()
	resume.text = "Continue"
	resume.custom_minimum_size.y = 60
	column.add_child(resume)
	resume.pressed.connect(toggle_menu)

func toggle_menu():
	paused = not paused
	menu.visible = paused
	joystick_id = -1
	if paused and not qa_mode: Saves.write_state(sim.snapshot())
	queue_redraw()

func switch_lead(id: int):
	if id != sim.lead:
		var previous: int = sim.lead
		for companion in sim.companions:
			if companion.id == id: companion.id = previous
		sim.lead = id
		carry_root.reparent(actors[id], false)
		player_rig = actors[id]
	toggle_menu()

func movement_input() -> Vector2:
	if paused: return Vector2.ZERO
	if joystick_id != -1: return ((joystick_current - joystick_origin) / 110.0).limit_length(1)
	var x := float(Input.is_physical_key_pressed(KEY_D) or Input.is_physical_key_pressed(KEY_RIGHT)) - float(Input.is_physical_key_pressed(KEY_A) or Input.is_physical_key_pressed(KEY_LEFT))
	var y := float(Input.is_physical_key_pressed(KEY_S) or Input.is_physical_key_pressed(KEY_DOWN)) - float(Input.is_physical_key_pressed(KEY_W) or Input.is_physical_key_pressed(KEY_UP))
	return Vector2(x, y).limit_length(1)

func _gui_input(event: InputEvent):
	if paused: return
	if event is InputEventScreenTouch:
		if event.pressed and joystick_id == -1 and event.position.x < size.x * .55 and event.position.y > size.y * .30:
			joystick_id = event.index
			joystick_origin = event.position
			joystick_current = event.position
		elif not event.pressed and event.index == joystick_id: joystick_id = -1
	elif event is InputEventScreenDrag and event.index == joystick_id:
		joystick_current = event.position
	elif event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT:
		if event.pressed and event.position.x < size.x * .55:
			joystick_id = -2
			joystick_origin = event.position
			joystick_current = event.position
		elif not event.pressed: joystick_id = -1
	elif event is InputEventMouseMotion and joystick_id == -2:
		joystick_current = event.position
	queue_redraw()

func _draw():
	if joystick_id != -1:
		draw_circle(joystick_origin, 112, Color(.68, .84, 1, .10))
		draw_arc(joystick_origin, 112, 0, TAU, 64, Color(.84, .92, 1, .42), 3, true)
		var offset := (joystick_current - joystick_origin).limit_length(110)
		draw_circle(joystick_origin + offset, 43, Color(.85, .93, 1, .5))

func _physics_process(dt: float):
	if paused or not is_instance_valid(world): return
	var direction := movement_input()
	sim.step(dt, direction, direction.length() > .82 and (joystick_id != -1 or Input.is_physical_key_pressed(KEY_SHIFT)))
	save_timer += dt
	if save_timer >= 10 and not qa_mode:
		save_timer = 0
		Saves.write_state(sim.snapshot())

func _process(dt: float):
	if not is_instance_valid(world): return
	player_rig.position = xyz(sim.position)
	if sim.velocity.length() > .1:
		player_rig.rotation.y = lerp_angle(player_rig.rotation.y, atan2(sim.facing.x, sim.facing.y), 1 - exp(-16 * dt))
	animate(player_rig, sim.velocity.length())
	for companion in sim.companions:
		if not actors.has(companion.id): continue # Additional NPC art remains a release blocker.
		var root: Node3D = actors[companion.id]
		var target := xyz(companion.position)
		var motion := target - root.position
		root.position = target
		if motion.length() > .005: root.rotation.y = lerp_angle(root.rotation.y, atan2(motion.x, motion.z), .15)
		animate(root, motion.length() / maxf(dt, .001))
	for node in sim.resources:
		resource_visuals[node.id].visible = node.units > 0
	for side in sim.defenses:
		var d: Dictionary = sim.defenses[side]
		defense_visuals[side].scale.y = .15 + .85 * (float(d.delivered.wood + d.delivered.stone) / 11)
	update_carry()
	heat_light.light_energy = 3.0 + sin(sim.elapsed * 8) * .08
	heat_light.omni_range = sim.warmth()
	var focus := xyz(sim.position) + Vector3(0, .95, 0)
	var desired := focus + Vector3(0, 6.8, 8.6)
	camera.position = camera.position.lerp(desired, 1 - exp(-8.6 * dt)) if capture_frames > 0 else desired
	camera.look_at(focus)
	status.text = "HEAT %d   ·   %d carried" % [sim.level, sim.carried()]
	if sim.level < 2:
		objective.text = "Furnace   %d / 18 wood   ·   %d / 6 stone" % [mini(sim.stored.wood, 18), mini(sim.stored.stone, 6)]
	elif not sim.rescued: objective.text = "Warmth restored. Reach the frozen survivor."
	elif not sim.defenses.north.built: objective.text = "Build the north defense   ·   8 wood + 3 stone"
	else: objective.text = "Outpost restored · full threat presentation is still in development"
	if not sim.action.is_empty():
		hint.text = {"gather":"Gathering", "deposit":"Delivering", "build":"Building", "repair":"Repairing", "defense_repair":"Repairing", "rescue":"Rescuing", "enemy":"Defending"}.get(sim.action.kind, "")
	else: hint.text = ""
	# A missing enemy asset must never create invisible damage in a review APK.
	if sim.gate_open() and not sim.wave_active:
		sim.wave_timer = maxf(sim.wave_timer, 1.0)
	measure_frame()
	capture_frames += 1
	if qa_mode and capture_frames == 12:
		await RenderingServer.frame_post_draw
		get_viewport().get_texture().get_image().save_png(capture_directory.path_join("gameplay.png"))
		scene_view.get_texture().get_image().save_png(capture_directory.path_join("native-scene.png"))
		var report := {"renderer": RenderingServer.get_current_rendering_method(), "device": RenderingServer.get_video_adapter_name(), "window": [get_viewport().size.x, get_viewport().size.y], "internal_render": [scene_view.size.x, scene_view.size.y], "render_scale": scene_view.scaling_3d_scale, "render_review": render_review, "performance_certified": false, "characters": actors.keys(), "source_clips": {}}
		report["scene_script_sha256"] = FileAccess.get_file_as_string("res://scripts/main.gd").sha256_text()
		report["camera_full_height"] = camera.size
		for id in actors:
			var a: Node3D = actors[id]
			report.source_clips[str(id)] = Array(a.get_meta("animation").get_animation_list()) if a.has_meta("animation") else []
		var file := FileAccess.open(capture_directory.path_join("render-evidence.json"), FileAccess.WRITE)
		file.store_string(JSON.stringify(report, "\t"))
		file.close()
		get_tree().quit()

func measure_frame():
	var now := Time.get_ticks_usec()
	if last_frame_usec > 0 and not paused and capture_frames > warmup_frames:
		frame_intervals.append(float(now - last_frame_usec) / 1000.0)
		if frame_intervals.size() > 72000: frame_intervals.pop_front()
	last_frame_usec = now

func _notification(what: int):
	if what == NOTIFICATION_APPLICATION_PAUSED:
		paused = true
		joystick_id = -1
		if is_instance_valid(menu): menu.visible = true
		if not qa_mode and sim: Saves.write_state(sim.snapshot())
	elif what == NOTIFICATION_APPLICATION_RESUMED:
		last_frame_usec = 0
		joystick_id = -1
