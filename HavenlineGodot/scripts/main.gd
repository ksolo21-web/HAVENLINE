extends Control

const ENVIRONMENT_REVISION := "0.4.5-environment-candidate"
var scenery_instances: Array[GeometryInstance3D] = []
var scenery_origins: Array[Vector3] = []
var scenery_heights: Array[float] = []
var foreground_faded := 0
var scenery_cutaway: Array[float] = []

const Simulation = preload("res://scripts/outpost_simulation.gd")
const OutpostView = preload("res://scripts/outpost_view.gd")
const Surface = preload("res://scripts/outpost_surface.gd")
const ActionReadout = preload("res://scripts/action_readout.gd")
const OutpostAudio = preload("res://scripts/outpost_audio.gd")
var outpost_view: Node3D
var outpost_audio: Node
var action_readout: Control
var climate_status: Label
var environment: Environment
var capture_scenario := "opening"
const Saves = preload("res://scripts/save_store.gd")
const Scenery = preload("res://scripts/scenery_batch.gd")
const DeviceBenchmark = preload("res://scripts/device_benchmark.gd")
var device_benchmark: PanelContainer
const FrameRecord = preload("res://scripts/performance_record.gd")
const CarryStack = preload("res://scripts/carry_stack.gd")
const TransferFeedback = preload("res://scripts/transfer_feedback.gd")
const RenderPolicy = preload("res://scripts/render_policy.gd")
const PopulationView = preload("res://scripts/population_view.gd")
var population_view: Node3D
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
var carry_stacks: Dictionary = {}
var transfer_feedback: Node3D
var menu_column: VBoxContainer
var camp_button: Button
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
var performance_record := FrameRecord.new()
var merged_cache: Dictionary = {}
var no_batching := false
var capture_phase := 0.0
var last_frame_usec := 0
var warmup_frames := 180
var save_recovery_path := ""
var capture_motion := ""
var capture_view := "front"

func _ready():
	# Fail closed before loading a saved encounter: no invisible wolves/helper can
	# damage or secretly work in a scene that does not yet have their approved art.
	sim.population.presentation_required = true
	sim.threats_enabled = false
	sim.rescue_enabled = false
	sim.presented_actor_ids = [1,2,3,4]
	get_tree().quit_on_go_back = false
	get_tree().auto_accept_quit = false
	Engine.max_fps = 60
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--capture="):
			capture_directory = argument.trim_prefix("--capture=")
			qa_mode = true
		if argument == "--render-review": render_review = true
		if argument.begins_with("--motion="): capture_motion = argument.trim_prefix("--motion=")
		if argument == "--no-batching": no_batching = true
		if argument.begins_with("--phase="): capture_phase = clampf(argument.trim_prefix("--phase=").to_float(), 0, 1)
		if argument.begins_with("--view="): capture_view = argument.trim_prefix("--view=")
		if argument.begins_with("--scenario="): capture_scenario = argument.trim_prefix("--scenario=")
	# Review uses the same scene and materials at a disclosed smaller render size.
	# It never grants the 4K/60 performance gate.
	if not qa_mode:
		save_recovery_path = Saves.load_into(sim)
	else:
		apply_capture_scenario()
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
	outpost_view = OutpostView.new()
	world.add_child(outpost_view)
	outpost_view.configure(environment, sun, furnace, heat_light, sim)
	outpost_audio = OutpostAudio.new()
	add_child(outpost_audio)
	build_crew()
	population_view = PopulationView.new()
	world.add_child(population_view)
	population_view.configure(sim, resource_piece)
	transfer_feedback = TransferFeedback.new()
	transfer_feedback.loader = resource_piece
	world.add_child(transfer_feedback)
	build_hud()
	action_readout = ActionReadout.new()
	add_child(action_readout)
	action_readout.configure(sim, camera, scene_view)
	resized.connect(resize_render)
	resize_render()
	if qa_mode:
		DirAccess.make_dir_recursive_absolute(capture_directory)

func resize_render():
	if not is_instance_valid(scene_view): return
	var aspect := maxf(1.0, size.x / maxf(1.0, size.y))
	scene_view.size = RenderPolicy.internal_size(aspect, render_review)
	performance_record.resolution(scene_view.size)
	if is_instance_valid(camera): camera.keep_aspect = Camera3D.KEEP_HEIGHT
	layout_hud()
	queue_redraw()

func apply_capture_scenario():
	# Explicit QA fixtures only. Normal player saves/starts never use these values.
	if capture_scenario in ["warmth2", "night", "blizzard", "warmth4"]:
		sim.stored.wood = 18; sim.stored.stone = 6
		if capture_scenario == "warmth4":
			sim.stored.wood = 64; sim.stored.stone = 28; sim.stored.metal = 6
		sim.update_level()
	if capture_scenario == "night": sim.climate.seconds = 670.0
	if capture_scenario == "blizzard": sim.climate.seconds = 585.0
	if capture_scenario == "gather":
		sim.position = sim.resources[0].position + Vector2(0, 1.1)
		sim.action_clocks["gather:" + sim.resources[0].id] = 0.15

func build_environment():
	environment = Environment.new()
	environment.background_mode = Environment.BG_COLOR
	environment.background_color = Color("577b9a")
	environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	environment.ambient_light_color = Color("c1d9f0")
	environment.ambient_light_energy = 0.38
	environment.tonemap_mode = Environment.TONE_MAPPER_ACES
	environment.tonemap_exposure = 1.6
	# Reserve highlight headroom instead of clipping every sunlit snow surface.
	environment.tonemap_white = 6.0
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
	sun.directional_shadow_max_distance = 70
	world.add_child(sun)
	camera = Camera3D.new()
	camera.projection = Camera3D.PROJECTION_ORTHOGONAL
	# Unity orthographicSize is a half-height; Godot's size is the full span.
	camera.size = float(sim.contract.camera.size) * 2.0
	camera.near = 0.05
	camera.far = 180
	world.add_child(camera)
	camera.current = true

func model(asset: String, parent: Node3D, p := Vector3.ZERO) -> Node3D:
	var path := "res://assets/" + asset + ".glb"
	if asset.begins_with("world/"):
		# Authored replacement required: never silently display the retired blockout.
		path = "res://assets/environment_v2/" + asset.trim_prefix("world/") + ".glb"
		assert(ResourceLoader.exists(path), "Missing required winter environment mesh: " + path)
	if not asset_cache.has(path):
		asset_cache[path] = load(path)
	var instance: Node3D
	if asset.begins_with("world/") and not no_batching:
		if not merged_cache.has(asset):
			merged_cache[asset] = Scenery.compile(asset_cache[path])
			if asset.begins_with("world/pine_"):
				for i in merged_cache[asset].get_surface_count():
					var source_material: Material = merged_cache[asset].surface_get_material(i)
					if source_material is BaseMaterial3D:
						var leaf_material := ShaderMaterial.new()
						leaf_material.shader=load("res://shaders/evergreen.gdshader")
						leaf_material.set_shader_parameter("albedo_texture",source_material.albedo_texture)
						leaf_material.set_shader_parameter("normal_texture",source_material.normal_texture)
						leaf_material.set_shader_parameter("surface_roughness",source_material.roughness)
						merged_cache[asset].surface_set_material(i,leaf_material)
		instance = MeshInstance3D.new()
		instance.mesh = merged_cache[asset]
	else:
		instance = asset_cache[path].instantiate()
	parent.add_child(instance)
	instance.position = p
	if asset.begins_with("world/pine_") and instance is GeometryInstance3D:
		scenery_instances.append(instance)
		scenery_origins.append(p)
		scenery_heights.append(instance.mesh.get_aabb().end.y)
		scenery_cutaway.append(0.0)
	return instance

func build_world():
	# The sculpted OutpostView surface replaces the flat terrain render only.
	# All original GLB source assets are retained unchanged.
	furnace = model("world/furnace", world, xyz(Simulation.point(sim.contract.world.furnace)))
	heat_light = OmniLight3D.new()
	heat_light.position = Vector3(0, 1.2, 0.6)
	heat_light.light_color = Color("ff913d")
	heat_light.light_energy = 3
	heat_light.omni_range = 5
	furnace.add_child(heat_light)
	model("world/storage", world, xyz(Simulation.point(sim.contract.world.storage)))
	for x in [-6.6, 6.6]:
		var shelter := model("world/shelter", world, xyz(Vector2(x, -4.8)))
		shelter.rotation.y = -0.12 if x < 0 else 0.12
	for index in range(sim.resources.size()):
		var node: Dictionary = sim.resources[index]
		var asset: String = "pine_" + str(1 + index % 3) if node.kind == "wood" else node.kind
		resource_visuals[node.id] = model("world/" + asset, world, xyz(node.position))
	# Irregular woodland groups instead of the old evenly spaced circular fence.
	for i in range(44):
		var a := float(i) * 2.399963
		var rx := 16.6 + sin(i * 7.13) * 3.8
		var rz := 19.0 + cos(i * 4.71) * 3.2
		var point := Vector2(cos(a) * rx, sin(a) * rz)
		# Keep entrances and the default camera's lower central view readable.
		if absf(point.x) < 4.8 and point.y > 13.0: continue
		var tree := model("world/pine_" + str(1 + i % 3), world, xyz(point))
		tree.scale = Vector3.ONE * (0.76 + fposmod(i * .137, .52))
		tree_rotation(tree, i)
	build_environment_dressing()
	for side in sim.defenses:
		defense_visuals[side] = model("world/barricade", world, xyz(sim.defenses[side].position))
		defense_visuals[side].scale.y = 0.15

func tree_rotation(tree: Node3D, index: int):
	tree.rotation.y = index * 1.71

func xyz(p: Vector2) -> Vector3:
	return Vector3(p.x, Surface.height_at(p), p.y)

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
	if id >= 2:
		var motion_path := "res://assets/motion/Character%d.res" % id
		if ResourceLoader.exists(motion_path):
			var skeleton := find_skeleton(visual)
			if skeleton:
				animation = AnimationPlayer.new()
				skeleton.add_child(animation)
				animation.root_node = NodePath("..")
				animation.add_animation_library("motion", load(motion_path))
				root.set_meta("motion_candidate", true)
		else:
			push_error("Missing baked crew motion: run res://tools/bake_crew_motion.gd")
	if animation:
		for clip in animation.get_animation_list():
			if not clip.ends_with("RESET"):
				animation.get_animation(clip).loop_mode = Animation.LOOP_LINEAR
		root.set_meta("animation", animation)
	root.set_meta("visual", visual)
	return root

func find_skeleton(node: Node) -> Skeleton3D:
	if node is Skeleton3D: return node
	for child in node.get_children():
		var found := find_skeleton(child)
		if found: return found
	return null

func find_animation_player(node: Node) -> AnimationPlayer:
	if node is AnimationPlayer: return node
	for child in node.get_children():
		var found := find_animation_player(child)
		if found: return found
	return null

func resource_piece(kind: String, parent: Node3D) -> Node3D:
	return model("world/" + ("log" if kind == "wood" else kind), parent)

func build_crew():
	for id in range(1, 5):
		actors[id] = actor(id)
		var stack := CarryStack.new()
		stack.loader = resource_piece
		stack.position = Vector3(0, .65, -.42)
		actors[id].add_child(stack)
		carry_stacks[id] = stack
	player_rig = actors[sim.lead]
	carry_root = carry_stacks[sim.lead]

func animate(root: Node3D, speed: float):
	if not root.has_meta("animation"): return
	var animation: AnimationPlayer = root.get_meta("animation")
	var desired := "run" if speed > 4.3 else ("walk" if speed > .15 else "idle")
	if qa_mode and not capture_motion.is_empty(): desired = capture_motion
	for clip in animation.get_animation_list():
		if clip.to_lower().ends_with(desired):
			if animation.current_animation != clip: animation.play(clip, 0.0 if qa_mode else .16)
			if qa_mode and not capture_motion.is_empty():
				animation.seek(animation.get_animation(clip).length * capture_phase, true)
				animation.speed_scale = 0.0
				return
			# Use source cadence; integration locomotion review must verify sliding.
			animation.speed_scale = 0.0 if paused else 1.0
			return

func update_carry():
	carry_stacks[sim.lead].update_inventory(sim.inventory)
	for companion in sim.companions:
		if not carry_stacks.has(companion.id): continue
		var inventory := {"wood":0,"stone":0,"metal":0,"fuel":0}
		inventory[companion.get("cargo_kind","wood")] = companion.get("cargo",0)
		carry_stacks[companion.id].update_inventory(inventory)

func present_events():
	action_readout.consume(sim.events)
	outpost_audio.consume(sim.events)
	for event in sim.events:
		var kind: String = event.get("resource", "")
		if kind.is_empty(): continue
		var target: Vector3 = xyz(event.get("target",event.position)) + Vector3(0,.75,0)
		var origin := xyz(sim.position) + Vector3(0,1.0,-.35)
		if event.has("actor_id"): origin = xyz(event.position) + Vector3(0,1.0,-.35)
		if event.type in ["gather","worker_gather"]: transfer_feedback.transfer(kind,target,origin)
		elif event.type in ["deposit","worker_deposit","build","worker_build","repair","worker_repair","customer_sale"]:
			transfer_feedback.transfer(kind,origin,target)

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
	climate_status = text_label("", 18, self)
	climate_status.position = Vector2(40, 76)
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
	camp_button = pause_button
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
	menu.size = Vector2(780,570)
	menu.position = size / 2 - menu.size / 2
	var padding := MarginContainer.new()
	for side in ["left","right","top","bottom"]:
		padding.add_theme_constant_override("margin_" + side,24)
	menu.add_child(padding)
	menu_column = VBoxContainer.new()
	menu_column.add_theme_constant_override("separation",16)
	var scroll := ScrollContainer.new()
	scroll.custom_minimum_size = Vector2(0, 440)
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	padding.add_child(scroll)
	menu_column.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.add_child(menu_column)
	rebuild_menu()

func rebuild_menu():
	for child in menu_column.get_children():
		menu_column.remove_child(child)
		child.queue_free()
	text_label("HAVENLINE · Outpost crew",32,menu_column)
	if is_instance_valid(population_view):
		var pop = sim.population
		var summary := "Customers %d · Recruits %d · Pets %d · Supply tokens %d" % [pop.customers.size(), pop.recruits.size(), pop.pets.size(), pop.credits]
		text_label(summary, 20, menu_column)
		if population_view.scenes.is_empty():
			var pending := text_label("NPC models pending — no placeholder people or invisible workers.", 18, menu_column)
			pending.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	var leads := HBoxContainer.new()
	menu_column.add_child(leads)
	for id in [1,2]:
		var choice := Button.new()
		choice.text = ("Leading · " if id == sim.lead else "Lead with ") + "Character " + str(id)
		choice.custom_minimum_size = Vector2(345,64)
		choice.add_theme_font_size_override("font_size",24)
		leads.add_child(choice)
		choice.pressed.connect(func(): switch_lead(id))
	for companion in sim.companions:
		if not actors.has(companion.id): continue
		var id: int = companion.id
		var row := HBoxContainer.new()
		row.add_theme_constant_override("separation",14)
		menu_column.add_child(row)
		var name_label := text_label("Character " + str(id),24,row)
		name_label.custom_minimum_size.x = 180
		var job := OptionButton.new()
		var resource := OptionButton.new()
		for value in Simulation.CrewWork.JOBS: job.add_item(value.capitalize())
		for value in Simulation.KINDS: resource.add_item(value.capitalize())
		job.select(Simulation.CrewWork.JOBS.find(companion.job))
		resource.select(Simulation.KINDS.find(companion.get("resource_kind","wood")))
		job.custom_minimum_size = Vector2(240,64)
		resource.custom_minimum_size = Vector2(210,64)
		for control in [job,resource]:
			control.add_theme_font_size_override("font_size",24)
			row.add_child(control)
		resource.disabled = companion.job != "gather"
		job.item_selected.connect(func(index):
			sim.assign_job(id, Simulation.CrewWork.JOBS[index], Simulation.KINDS[resource.selected])
			resource.disabled = Simulation.CrewWork.JOBS[index] != "gather")
		resource.item_selected.connect(func(index):
			sim.assign_job(id, Simulation.CrewWork.JOBS[job.selected], Simulation.KINDS[index]))
	build_population_menu()
	var audio_toggle := CheckButton.new()
	audio_toggle.text = "Outpost sound"
	audio_toggle.button_pressed = not outpost_audio.muted
	audio_toggle.custom_minimum_size.y = 56
	menu_column.add_child(audio_toggle)
	audio_toggle.toggled.connect(func(enabled): outpost_audio.set_muted(not enabled))
	var explanation := text_label("Move to act. Crew assignments never replace your movement control.",20,menu_column)
	explanation.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	explanation.custom_minimum_size.y = 48
	var benchmark_button := Button.new()
	benchmark_button.text = "Measure native 4K frame timing · 30 minutes"
	benchmark_button.custom_minimum_size.y = 64
	benchmark_button.add_theme_font_size_override("font_size",22)
	menu_column.add_child(benchmark_button)
	benchmark_button.pressed.connect(start_device_benchmark)
	var resume := Button.new()
	resume.text = "Return to the outpost"
	resume.custom_minimum_size.y = 64
	resume.add_theme_font_size_override("font_size",24)
	menu_column.add_child(resume)
	resume.pressed.connect(toggle_menu)
	call_deferred("layout_hud")

func toggle_menu():
	paused = not paused
	menu.visible = paused
	if paused: rebuild_menu()
	transfer_feedback.set_process(not paused)
	joystick_id = -1
	if paused and not qa_mode:
		Saves.write_state(sim.snapshot())
		write_performance_record()
	queue_redraw()

func switch_lead(id: int):
	if sim.select_lead(id):
		carry_root = carry_stacks[id]
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
	population_view.sync(dt)
	present_events()
	save_timer += dt
	if save_timer >= 10 and not qa_mode:
		save_timer = 0
		Saves.write_state(sim.snapshot())

func _process(dt: float):
	if not is_instance_valid(world): return
	population_view.pause_animations(paused)
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
	outpost_view.sync(sim, dt, paused)
	outpost_audio.sync(sim, paused, dt)
	# Preserve the close zoom; a short look-ahead includes roofs above the player.
	var focus := xyz(sim.position) + Vector3(0, .95, -3.6)
	var offset := Vector3(0, 6.8, 8.6)
	if qa_mode and capture_scenario in ["shelter-detail","shelter-detail-rear"]:
		focus=xyz(Vector2(-6.6,-4.8))+Vector3(0,1.45,0);camera.size=5.1;offset=Vector3(4,3.6,7)
	elif qa_mode and capture_scenario == "furnace-detail":
		focus=xyz(Vector2(0,.2))+Vector3(0,1.0,0);camera.size=3.8;offset=Vector3(4,3.6,7)
	elif qa_mode and capture_scenario == "tree-detail":
		focus=xyz(sim.resources[0].position)+Vector3(0,2.35,0);camera.size=6.6;offset=Vector3(4,3.6,7)
	if qa_mode:
		if capture_view == "side": offset = Vector3(8.6, 6.8, 0)
		elif capture_view == "left": offset = Vector3(-8.6, 6.8, 0)
		elif capture_view == "rear": offset = Vector3(0, 6.8, -8.6)
		elif capture_view == "three-quarter": offset = Vector3(8.6, 6.8, 8.6)
		elif capture_view == "overhead": offset = Vector3(0.001, 16.0, 0.001)
	var desired := focus + offset
	# Orthographic framing is unchanged when translated along the viewing ray.
	# Moving the camera back prevents its near plane cutting foreground scenery.
	desired += offset.normalized() * 18.0
	camera.position = camera.position.lerp(desired, 1 - exp(-8.6 * dt)) if capture_frames > 0 else desired
	camera.look_at(focus)
	update_foreground_visibility(xyz(sim.position)+Vector3(0,.95,0), dt)
	status.text = "HEAT %d   ·   %d carried" % [sim.level, sim.carried()]
	var hour: float = sim.climate.hour()
	climate_status.text = "Day %d · %02d:%02d · %s\nWarmth %d%%  ·  Health %d%%" % [sim.climate.day_number(), int(hour), int(floor(fposmod(hour,1.0)*60.0)), sim.climate.weather().name, roundi(sim.temperature), roundi(sim.health)]
	action_readout.refresh(dt, paused)
	if sim.level < 2:
		objective.text = "Furnace · %d/18 wood + %d/6 stone" % [mini(sim.stored.wood, 18), mini(sim.stored.stone, 6)]
	elif not sim.rescued: objective.text = "Warmth restored · approach the survivor" if sim.rescue_enabled else "Warmth restored · rescue art pending"
	elif not sim.defenses.north.built: objective.text = "Build the north defense   ·   8 wood + 3 stone"
	else: objective.text = "Outpost restored · threat art pending"
	if not sim.action.is_empty():
		hint.text = {"gather":"Gathering", "deposit":"Delivering", "build":"Building", "repair":"Repairing", "defense_repair":"Repairing", "rescue":"Rescuing", "enemy":"Defending", "npc_rescue":"Welcoming a companion", "customer_service":"Serving a customer"}.get(sim.action.kind, "")
	else: hint.text = ""
	# Presentation capability gates live in simulation, not frame-rate-dependent
	# timer rewrites. Active saved encounters remain intact but cannot hurt invisibly.
	measure_frame()
	capture_frames += 1
	if qa_mode and capture_frames == 12:
		await RenderingServer.frame_post_draw
		get_viewport().get_texture().get_image().save_png(capture_directory.path_join("gameplay.png"))
		scene_view.get_texture().get_image().save_png(capture_directory.path_join("native-scene.png"))
		var report := {"renderer": RenderingServer.get_current_rendering_method(), "device": RenderingServer.get_video_adapter_name(), "window": [get_viewport().size.x, get_viewport().size.y], "internal_render": [scene_view.size.x, scene_view.size.y], "render_scale": scene_view.scaling_3d_scale, "render_review": render_review, "performance_certified": false, "characters": actors.keys(), "source_clips": {}}
		report["environment_revision"] = ENVIRONMENT_REVISION
		report["environment_kit"] = JSON.parse_string(FileAccess.get_file_as_string("res://assets/environment_v2/manifest.json"))
		report["foreground_faded"] = foreground_faded
		report["camera_near"] = camera.near
		report["camera_focus_distance"] = camera.position.distance_to(focus)
		report["npc_population"] = population_view.evidence()
		report["outpost"] = outpost_view.evidence(sim)
		report["capture_scenario"] = capture_scenario
		report["scenario_is_test_fixture"] = capture_scenario != "opening"
		report["action_readout"] = action_readout.descriptor
		report["audio_event_count"] = outpost_audio.emitted_events
		report["custom_c2_c4_rig_review_deferred"] = true
		report["scene_script_sha256"] = FileAccess.get_file_as_string("res://scripts/main.gd").sha256_text()
		report["camera_full_height"] = camera.size
		report["capture_motion"] = capture_motion
		report["capture_view"] = capture_view
		report["crew_motion_is_unapproved_candidate"] = true
		report["threats_enabled"] = sim.threats_enabled
		report["source_glbs_modified"] = false
		report["capture_phase"] = capture_phase
		report["scenery_batched"] = not no_batching
		report["draw_calls"] = scene_view.get_render_info(Viewport.RENDER_INFO_TYPE_VISIBLE, Viewport.RENDER_INFO_DRAW_CALLS_IN_FRAME)
		report["primitives"] = scene_view.get_render_info(Viewport.RENDER_INFO_TYPE_VISIBLE, Viewport.RENDER_INFO_PRIMITIVES_IN_FRAME)
		report["performance"] = performance_record.report()
		for id in actors:
			var a: Node3D = actors[id]
			report.source_clips[str(id)] = Array(a.get_meta("animation").get_animation_list()) if a.has_meta("animation") else []
		var file := FileAccess.open(capture_directory.path_join("render-evidence.json"), FileAccess.WRITE)
		file.store_string(JSON.stringify(report, "\t"))
		file.close()
		await close_game()

func measure_frame():
	var now := Time.get_ticks_usec()
	if last_frame_usec > 0 and not paused and capture_frames > warmup_frames:
		performance_record.sample(float(now - last_frame_usec) / 1000.0)
	last_frame_usec = now

func close_game():
	# Retire real audio playback before disposing the scene or renderer.
	set_process(false)
	set_physics_process(false)
	if is_instance_valid(outpost_audio): outpost_audio.stop_all()
	await get_tree().create_timer(.35).timeout
	get_tree().quit()

func _notification(what: int):
	if what == NOTIFICATION_WM_CLOSE_REQUEST:
		if not qa_mode: Saves.write_state(sim.snapshot())
		close_game()
	elif what == NOTIFICATION_WM_GO_BACK_REQUEST:
		if is_instance_valid(menu) and not paused: toggle_menu()
	elif what == NOTIFICATION_APPLICATION_PAUSED:
		paused = true
		joystick_id = -1
		if is_instance_valid(menu):
			menu.visible = true
			rebuild_menu()
		if is_instance_valid(transfer_feedback): transfer_feedback.set_process(false)
		if not qa_mode and sim:
			Saves.write_state(sim.snapshot())
			write_performance_record()
	elif what == NOTIFICATION_APPLICATION_RESUMED:
		last_frame_usec = 0
		joystick_id = -1

func write_performance_record():
	performance_record.write("user://performance-review.json", {
		"os":OS.get_name(), "model":OS.get_model_name(),
		"renderer":RenderingServer.get_current_rendering_method(),
		"gpu":RenderingServer.get_video_adapter_name(),
		"render_scale":scene_view.scaling_3d_scale if is_instance_valid(scene_view) else 0.0,
		"build":"0.4.5-environment-development", "review_resolution":render_review})

func layout_hud():
	if not is_instance_valid(status): return
	var safe := Rect2(Vector2.ZERO,size)
	if OS.has_feature("android"):
		var physical := Vector2(DisplayServer.window_get_size())
		var area := DisplayServer.get_display_safe_area()
		if physical.x > 0 and physical.y > 0 and area.size.x > 0 and area.size.y > 0:
			var factor := size / physical
			safe = Rect2(Vector2(area.position) * factor,Vector2(area.size) * factor).intersection(safe)
	status.position = safe.position + Vector2(32,28)
	climate_status.position = safe.position + Vector2(36,74)
	objective.size.x = minf(780,maxf(300,safe.size.x - 660))
	objective.position = Vector2(safe.get_center().x - objective.size.x / 2,safe.position.y + 34)
	hint.size.x = minf(780,safe.size.x - 96)
	hint.position = Vector2(safe.get_center().x - hint.size.x / 2,safe.end.y - 72)
	camp_button.position = Vector2(safe.end.x - 156,safe.position.y + 26)
	menu.position = safe.get_center() - menu.size / 2

func _unhandled_key_input(event: InputEvent):
	if event is InputEventKey and event.pressed and not event.echo and event.physical_keycode == KEY_ESCAPE:
		toggle_menu()
		get_viewport().set_input_as_handled()

func build_population_menu():
	var people: Array = sim.population.recruits + sim.population.pets
	for c in sim.companions:
		if c.id == 5 and sim.rescue_enabled:
			var opening: Dictionary = c.duplicate(true)
			opening["name"] = "Rescued survivor"
			opening["role"] = "survivor"
			people.append(opening)
	for person in people:
		var row := HBoxContainer.new()
		menu_column.add_child(row)
		var label := text_label(person.name, 22, row)
		label.custom_minimum_size.x = 200
		var job := OptionButton.new()
		var allowed: Array = sim.population.PET_JOBS if person.role == "pet" else Simulation.CrewWork.JOBS
		for choice in allowed: job.add_item(choice.capitalize())
		job.select(allowed.find(person.job))
		job.custom_minimum_size = Vector2(230, 64)
		row.add_child(job)
		var resource := OptionButton.new()
		for kind in Simulation.KINDS: resource.add_item(kind.capitalize())
		resource.select(Simulation.KINDS.find(person.resource_kind))
		resource.custom_minimum_size = Vector2(200, 64)
		resource.disabled = person.role == "pet" or person.job != "gather"
		row.add_child(resource)
		var id: int = person.id
		job.item_selected.connect(func(index):
			sim.assign_job(id, allowed[index], Simulation.KINDS[resource.selected])
			resource.disabled = allowed[index] != "gather")
		resource.item_selected.connect(func(index):
			sim.assign_job(id, allowed[job.selected], Simulation.KINDS[index]))

func build_environment_dressing():
	# Non-interactive set dressing avoids the existing opening objectives and lanes.
	# Meshes are shared; low ground dressing is grouped into material batches.
	var groups := {"snow_rock": [], "winter_shrub": []}
	for i in range(56):
		var a := i * 2.399963
		var p := Vector2(cos(a) * (11.8 + fposmod(i * .831, 8.0)), sin(a) * (14.3 + fposmod(i * .713, 7.0)))
		if absf(p.x) < 3.5: continue
		var blocked := false
		for r in sim.resources:
			if p.distance_to(r.position) < 1.8: blocked = true
		for x in [-6.6,6.6]:
			if p.distance_to(Vector2(x,-4.8)) < 2.6: blocked = true
		if blocked: continue
		var asset := "snow_rock" if i % 3 == 0 else "winter_shrub"
		var scale_factor := .60 + fposmod(i * .191,.85)
		groups[asset].append(Transform3D(Basis(Vector3.UP, i * 1.71).scaled(Vector3.ONE * scale_factor), xyz(p)))
	for asset in groups:
		var path: String = "res://assets/environment_v2/" + asset + ".glb"
		var mesh := Scenery.compile(load(path))
		var transforms: Array[Transform3D] = []
		transforms.assign(groups[asset])
		Scenery.instances(mesh, transforms, world)
	for p in [Vector2(-3.8,-.7),Vector2(3.8,-.7),Vector2(-3.5,-9.5),Vector2(3.5,-9.5)]:
		model("world/lantern_post",world,xyz(p))
		var light := OmniLight3D.new()
		light.position = xyz(p) + Vector3(.33,1.43,0)
		light.light_color = Color("ffc081")
		light.light_energy = .72
		light.omni_range = 3.3
		light.shadow_enabled = false
		world.add_child(light)

func update_foreground_visibility(focus: Vector3, dt: float):
	# Smooth opaque-dither cutaway for crowns hiding the lead; no transparent sorting.
	# Gameplay nodes remain alive; visibility is not a change to resource state.
	foreground_faded = 0
	var view := camera.global_transform.affine_inverse()
	var target := view * (focus + Vector3(0,.05,0))
	for i in range(scenery_instances.size()):
		var tree := scenery_instances[i]
		if not is_instance_valid(tree): continue
		var base: Vector3 = view * tree.global_position
		var top: Vector3 = view * (tree.global_position + Vector3(0,scenery_heights[i] * tree.scale.y,0))
		var depth_front := maxf(base.z,top.z) > target.z + 1.4
		var covers := absf(base.x-target.x) < 2.0 and target.y > minf(base.y,top.y)-.65 and target.y < maxf(base.y,top.y)+.65
		# A depleted resource stays hidden even when camera occlusion changes.
		var depleted := false
		for r in sim.resources:
			if resource_visuals.get(r.id) == tree and r.units <= 0: depleted = true
		var target_cutaway := 1.0 if depth_front and covers else 0.0
		scenery_cutaway[i]=move_toward(scenery_cutaway[i],target_cutaway,clampf(dt,0,.10)*4.0)
		tree.set_instance_shader_parameter("cutaway",scenery_cutaway[i])
		tree.visible = not depleted
		if scenery_cutaway[i] > .01: foreground_faded += 1

func start_device_benchmark():
	if is_instance_valid(device_benchmark): device_benchmark.queue_free()
	if paused: toggle_menu()
	device_benchmark = DeviceBenchmark.new()
	add_child(device_benchmark)
	device_benchmark.configure(self)
