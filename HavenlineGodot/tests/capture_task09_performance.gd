extends SceneTree

# This probe is deliberately T09-type agnostic so the exact pre-claim base can
# run the same source. The workflow copies this evidence-only script into a
# detached base worktree, then compares that shipping scene with the candidate.
const Main = preload("res://scripts/main.gd")

var output := "user://task09-performance"
var candidate := "local-working-tree"
var expected_integrated := true
var samples: Array[float] = []
var draw_calls: Array[int] = []
var primitives: Array[int] = []

func _initialize() -> void:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--out="): output = argument.trim_prefix("--out=")
		elif argument.begins_with("--candidate="): candidate = argument.trim_prefix("--candidate=")
		elif argument == "--expect-base": expected_integrated = false
	call_deferred("run")

func percentile(values: Array[float], fraction: float) -> float:
	if values.is_empty(): return 0.0
	var ordered := values.duplicate()
	ordered.sort()
	return ordered[clampi(int(ceil(fraction * ordered.size())) - 1,0,ordered.size()-1)]

func average(values: Array) -> float:
	if values.is_empty(): return 0.0
	var total := 0.0
	for value in values: total += float(value)
	return total / float(values.size())

func maximum_value(values: Array) -> float:
	var result := 0.0
	for value in values: result = maxf(result,float(value))
	return result

func inventory_scene(node: Node, result: Dictionary) -> void:
	result.nodes += 1
	if node is MeshInstance3D and (node as MeshInstance3D).is_visible_in_tree():
		result.visible_meshes += 1
		var mesh_node := node as MeshInstance3D
		if mesh_node.mesh:
			for surface in mesh_node.mesh.get_surface_count():
				var material := mesh_node.get_active_material(surface)
				if material:
					result.material_ids[str(material.get_instance_id())] = true
					if material is ShaderMaterial and (material as ShaderMaterial).shader:
						result.shader_ids[str((material as ShaderMaterial).shader.get_instance_id())] = true
	if node is AnimationPlayer:
		result.animation_players += 1
		if not (node as AnimationPlayer).current_animation.is_empty(): result.active_animations += 1
	if node is Skeleton3D and (node as Skeleton3D).is_visible_in_tree(): result.visible_rigs += 1
	for child in node.get_children(): inventory_scene(child,result)

func run() -> void:
	DirAccess.make_dir_recursive_absolute(output)
	var game = Main.new()
	game.qa_mode = true
	game.capture_frames = 1000
	game.size = Vector2(root.size)
	root.add_child(game)
	for frame in 5: await process_frame
	game.set_process(false)
	game.set_physics_process(false)
	var presenter = game.get("harvest_presentation")
	var integrated := presenter != null and is_instance_valid(presenter)
	if integrated != expected_integrated:
		push_error("T09 integration expectation mismatch")
		quit(2)
		return
	var source: Dictionary = game.sim.resources[0]
	game.sim.position = source.position + Vector2(0.0,1.12)
	game.sim.facing = (source.position-game.sim.position).normalized()
	game.sim.velocity = Vector2.ZERO
	game.player_rig.position = game.xyz(game.sim.position)
	var static_memory_start := Performance.get_monitor(Performance.MEMORY_STATIC)
	var node_count_after_warmup := 0
	var peak_fragments := 0
	var peak_pulses := 0
	for frame in 210:
		game.sim.action = {
			"kind":"gather", "id":String(source.id), "position":source.position,
			"action_token":901, "progress":fposmod(float(frame)/60.0,1.0),
			"role":"player_lead", "actionable":true,
		}
		if frame == 90:
			game.sim.events.clear()
			game.sim.perform_action(float(game.sim.tuning.gatherSecondsPerUnit[String(source.kind)]))
			game.sim.elapsed += 1.0/60.0
			game.present_events()
		var started := Time.get_ticks_usec()
		game._process(1.0/60.0)
		if integrated:
			presenter._process(1.0/60.0)
			game.transfer_feedback._process(1.0/60.0)
		RenderingServer.force_draw(false,0.0)
		if integrated:
			var live: Dictionary = presenter.descriptor()
			peak_fragments = maxi(peak_fragments,int(live.get("active_fragment_descriptors",0)))
			peak_pulses = maxi(peak_pulses,int(live.get("active_impact_pulses",0)))
		if frame == 120: node_count_after_warmup = int(game.world.get_tree().get_node_count())
		if frame >= 30:
			samples.append(float(Time.get_ticks_usec()-started)/1000.0)
			draw_calls.append(int(game.scene_view.get_render_info(Viewport.RENDER_INFO_TYPE_VISIBLE,Viewport.RENDER_INFO_DRAW_CALLS_IN_FRAME)))
			primitives.append(int(game.scene_view.get_render_info(Viewport.RENDER_INFO_TYPE_VISIBLE,Viewport.RENDER_INFO_PRIMITIVES_IN_FRAME)))
	var scene_inventory := {"nodes":0,"visible_meshes":0,"animation_players":0,"active_animations":0,"visible_rigs":0,"material_ids":{},"shader_ids":{}}
	inventory_scene(game.world,scene_inventory)
	var descriptor: Dictionary = presenter.descriptor() if integrated else {}
	var half := samples.size()/2
	var first_half: Array[float] = samples.slice(0,half)
	var last_half: Array[float] = samples.slice(half)
	var result := {
		"task":"T09", "candidate":candidate, "integrated":integrated,
		"method":"same-script exact-base versus integrated active-harvest render submission",
		"resolution":[game.scene_view.size.x,game.scene_view.size.y],
		"renderer":RenderingServer.get_current_rendering_method(), "gpu":RenderingServer.get_video_adapter_name(),
		"measured_frames":samples.size(), "warmup_frames":30,
		"average_ms":average(samples), "p95_ms":percentile(samples,0.95), "p99_ms":percentile(samples,0.99),
		"first_half_p95_ms":percentile(first_half,0.95), "last_half_p95_ms":percentile(last_half,0.95),
		"thermal_proxy_drift_ms":percentile(last_half,0.95)-percentile(first_half,0.95),
		"average_draw_calls":average(draw_calls), "maximum_draw_calls":maximum_value(draw_calls),
		"average_primitives":average(primitives), "maximum_primitives":maximum_value(primitives),
		"process_static_memory_mb":Performance.get_monitor(Performance.MEMORY_STATIC)/(1024.0*1024.0),
		"static_memory_growth_mb":maxf(0.0,Performance.get_monitor(Performance.MEMORY_STATIC)-static_memory_start)/(1024.0*1024.0),
		"texture_gpu_memory_mb":Performance.get_monitor(Performance.RENDER_TEXTURE_MEM_USED)/(1024.0*1024.0),
		"video_gpu_memory_mb":Performance.get_monitor(Performance.RENDER_VIDEO_MEM_USED)/(1024.0*1024.0),
		"scene_nodes":scene_inventory.nodes, "visible_meshes":scene_inventory.visible_meshes,
		"materials_visible":scene_inventory.material_ids.size(), "unique_shader_resources":scene_inventory.shader_ids.size(),
		"animation_players":scene_inventory.animation_players, "active_animations":scene_inventory.active_animations,
		"visible_rigs":scene_inventory.visible_rigs, "npc_companion_active_population":maxi(0,int(scene_inventory.visible_rigs)-1),
		"physics_active_bodies":Performance.get_monitor(Performance.PHYSICS_3D_ACTIVE_OBJECTS),
		"unchanged_active_state_node_count_stable":node_count_after_warmup == int(game.world.get_tree().get_node_count()),
		"maximum_fragment_descriptors":peak_fragments,
		"maximum_impact_pulses":peak_pulses,
		"physical_device_certified":false, "thermal_certified":false,
		"limitations":["Render-submission timings are software preflight, not display presentation.","Physical 4K/60 and thermal certification remain T68/T69."],
	}
	var file := FileAccess.open(output.path_join("performance.json"),FileAccess.WRITE)
	file.store_string(JSON.stringify(result,"\t")); file.close()
	print(JSON.stringify({"task":"T09","performance":true,"integrated":integrated,"frames":samples.size()}))
	if is_instance_valid(game.outpost_audio): game.outpost_audio.stop_all()
	await create_timer(0.35).timeout
	game.free()
	await process_frame
	await process_frame
	quit(0)
