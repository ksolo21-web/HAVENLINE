extends SceneTree

const Main = preload("res://scripts/main.gd")
const Harvest = preload("res://scripts/harvest_presentation.gd")

const DEVICE_SIZES := {
	"phone_16_9":Vector2(1920,1080), "phone_20_9":Vector2(2400,1080),
	"tablet_16_10":Vector2(2560,1600), "tablet_4_3":Vector2(2732,2048),
	"foldable_outer":Vector2(2520,1080), "foldable_inner":Vector2(2208,1768),
}
const VIEWS := ["front","front-right","right","rear-right","rear","rear-left","left","front-left","overhead","detail"]

var output := "user://task09-harvesting"
var resource_kind := "wood"
var mode := "sequence"
var view_id := "front"
var device_id := "phone_16_9"
var candidate := "local-working-tree"
var native_4k := false
var game
var source: Dictionary
var records: Array[Dictionary] = []
var frame_usec: Array[float] = []
var draw_calls: Array[int] = []
var primitives: Array[int] = []
var action_token := 901

func _initialize() -> void:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--out="): output = argument.trim_prefix("--out=")
		elif argument.begins_with("--resource="): resource_kind = argument.trim_prefix("--resource=")
		elif argument.begins_with("--mode="): mode = argument.trim_prefix("--mode=")
		elif argument.begins_with("--view="): view_id = argument.trim_prefix("--view=")
		elif argument.begins_with("--device="): device_id = argument.trim_prefix("--device=")
		elif argument.begins_with("--candidate="): candidate = argument.trim_prefix("--candidate=")
		elif argument == "--native-4k": native_4k = true
	call_deferred("run")

func average(values: Array) -> float:
	if values.is_empty(): return 0.0
	var total := 0.0
	for value in values: total += float(value)
	return total / float(values.size())

func maximum(values: Array) -> float:
	var result := 0.0
	for value in values: result = maxf(result,float(value))
	return result

func source_point() -> Vector3:
	return game.xyz(source.position) + Vector3.UP * 0.75

func actor_point() -> Vector3:
	return game.xyz(game.sim.position) + Vector3.UP * 0.95

func focus_review_visibility() -> void:
	# Review captures exercise the shipping simulation and world positions, but
	# unrelated foreground art must not hide the selected actor, source, tool,
	# carry, transfer, or impact pixels. The authored terrain and lighting remain.
	var selected_visual: Node3D = game.resource_visuals[String(source.id)]
	var visible_roots: Array[Node] = [
		game.sun, game.camera, game.outpost_view, game.player_rig,
		selected_visual, game.transfer_feedback, game.harvest_presentation,
	]
	for child in game.world.get_children():
		if child is Node3D and not child is WorldEnvironment and child not in visible_roots:
			(child as Node3D).visible = false

func source_cutaway() -> float:
	var selected_visual: Node3D = game.resource_visuals[String(source.id)]
	if selected_visual is GeometryInstance3D:
		var value: Variant = (selected_visual as GeometryInstance3D).get_instance_shader_parameter("cutaway")
		if value is float: return value
	return 0.0

func source_harvest_reveal() -> float:
	var selected_visual: Node3D = game.resource_visuals[String(source.id)]
	if selected_visual is GeometryInstance3D:
		var value: Variant = (selected_visual as GeometryInstance3D).get_instance_shader_parameter("harvest_reveal")
		if value is float: return value
	return 0.0

func source_contact_surface_opaque() -> bool:
	if resource_kind != "wood": return true
	var selected_visual: Node3D = game.resource_visuals[String(source.id)]
	if not selected_visual is MeshInstance3D: return false
	var selected_mesh: Mesh = (selected_visual as MeshInstance3D).mesh
	for surface_index in selected_mesh.get_surface_count():
		var material: Material = selected_mesh.surface_get_material(surface_index)
		if material is ShaderMaterial and material.resource_name.to_lower() == "trunk":
			var shader_material := material as ShaderMaterial
			return shader_material.shader.code.contains("local_harvest_reveal") and shader_material.shader.code.contains("harvest_reveal_side") and shader_material.shader.code.contains("harvest_contact_band") and is_equal_approx(float(shader_material.get_shader_parameter("harvest_contact_surface")),1.0)
	return false

func configure_review_frame(frame: int) -> void:
	configure_camera(frame)
	# The shipping process updates foreground cutaway before this disclosed review
	# camera is installed. Re-evaluate the unchanged cutaway policy against the
	# camera that will actually produce the evidence frame, otherwise a selected
	# pine can retain a stale fully-discarded state from the gameplay camera.
	for visibility_step in 3:
		game.update_foreground_visibility(actor_point(),0.10)

func configure_camera(frame := 0) -> void:
	var actor := actor_point()
	var target := source_point()
	var focus := actor.lerp(target,0.55)
	var forward := target-actor
	forward.y = 0.0
	if forward.length_squared() <= 0.000001: forward = Vector3.FORWARD
	forward = forward.normalized()
	var right := Vector3(forward.z,0.0,-forward.x)
	if view_id == "overhead":
		game.camera.size = 4.0
		game.camera.global_position = focus + Vector3(0.001,9.0,0.001)
		game.camera.look_at(focus)
		return
	if view_id == "detail":
		# Wood needs a lateral actor-side view to separate the bounded trunk edge,
		# axe head, handle and both hands. The compact stone/metal/fuel sources need
		# the opposite source-side oblique: their actor-side view puts the authored
		# impact face between the camera and the tool even though contact is valid.
		var detail_direction := (right-forward*0.22).normalized()
		if resource_kind in ["stone","metal","fuel"]:
			detail_direction = (right+forward*0.85).normalized()
		game.camera.keep_aspect = Camera3D.KEEP_HEIGHT
		game.camera.size = 2.65
		game.camera.global_position = focus+detail_direction*3.65+Vector3.UP*2.20
		game.camera.look_at(focus+Vector3.UP*0.10)
		return
	var angle_index := VIEWS.find(view_id)
	if angle_index < 0: angle_index = 0
	angle_index = mini(7,angle_index)
	var angle := TAU * float(angle_index) / 8.0
	var distance := 8.0 if mode == "device" else 5.6
	var orbit_direction := (-forward*cos(angle)+right*sin(angle)).normalized()
	if mode in ["sequence","device"]:
		# Read the hand-handle-trunk line laterally instead of placing the source
		# between the review camera and tool. Shipping crown cutaway stays active.
		orbit_direction = (right-forward*0.18).normalized()
	var offset := orbit_direction*distance+Vector3.UP*(4.0 if mode == "device" else 3.2)
	game.camera.keep_aspect = Camera3D.KEEP_HEIGHT
	if mode == "sequence":
		game.camera.size = maxf(4.0,actor.distance_to(target)*0.92)
	elif mode == "device":
		game.camera.size = 5.6
	else:
		game.camera.size = 3.8
	game.camera.global_position = focus + offset
	game.camera.look_at(focus + Vector3.UP * (0.08 * sin(float(frame) * 0.03)))

func canonical_action(progress: float) -> Dictionary:
	return {
		"kind":"gather", "id":String(source.id), "position":source.position,
		"resource":resource_kind, "source_id":String(source.id),
		"action_token":action_token,
		"progress":clampf(progress,0.0,1.0), "role":"player_lead", "actionable":true,
	}

func capture_png(name: String) -> void:
	if mode != "asset": focus_review_visibility()
	await process_frame
	root.get_texture().get_image().save_png(output.path_join(name + ".png"))

func capture_jpg(frame: int) -> void:
	focus_review_visibility()
	await process_frame
	root.get_texture().get_image().save_jpg(output.path_join("frames/frame-%05d.jpg" % int(frame / 2)),0.91)

func sample_shipping(frame: int, input: Vector2, phase: String) -> Dictionary:
	var started := Time.get_ticks_usec()
	var before_units := int(source.units)
	var before_inventory := int(game.sim.inventory[resource_kind])
	var before_distance: float = game.sim.position.distance_to(Vector2(source.position))
	# Advance the same shipping simulation/T07 call site used by _physics_process.
	# Node physics stays disabled so this deterministic evidence step cannot run
	# twice; no action, focus, progress, event, unit or inventory value is forged.
	game.sim.step(1.0 / 60.0,input)
	var shipping_events: Array = game.sim.events.duplicate(true)
	game.present_events()
	game._process(1.0 / 60.0)
	game.harvest_presentation._process(1.0 / 60.0)
	game.transfer_feedback._process(1.0 / 60.0)
	configure_review_frame(frame)
	var update_usec := float(Time.get_ticks_usec() - started)
	await process_frame
	var draws := int(RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_DRAW_CALLS_IN_FRAME))
	var prims := int(RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_PRIMITIVES_IN_FRAME))
	frame_usec.append(update_usec); draw_calls.append(draws); primitives.append(prims)
	var action: Dictionary = game.sim.action.duplicate(true)
	var authoritative_event := shipping_events.any(func(event): return String(event.get("type", "")) == "gather" and String(event.get("resource", "")) == resource_kind)
	var row := {
		"frame":frame, "phase":phase, "input":[input.x,input.y],
		"actor_position":[game.sim.position.x,game.sim.position.y],
		"distance_before":before_distance,
		"distance_after":game.sim.position.distance_to(Vector2(source.position)),
		"action_kind":String(action.get("kind", "")),
		"action_identity":String(action.get("identity", "")),
		"action_state":String(action.get("state", "idle")),
		"action_reason":String(action.get("reason", "")),
		"actionable":bool(action.get("actionable", false)),
		"action_token":int(action.get("action_token", 0)),
		"raw_progress":float(action.get("progress", 0.0)),
		"commit":authoritative_event,
		"authority":"outpost_simulation.step/context_director.advance",
		"authoritative_event":authoritative_event,
		"units_before":before_units,"units_after":int(source.units),
		"inventory_before":before_inventory,"inventory_after":int(game.sim.inventory[resource_kind]),
		"source_units":int(source.units), "inventory":int(game.sim.inventory[resource_kind]),
		"source_visible":game.resource_visuals[String(source.id)].visible,
		"source_cutaway":source_cutaway(), "source_harvest_reveal":source_harvest_reveal(),
		"source_contact_surface_opaque":source_contact_surface_opaque(),
		"context":game.sim.context_director.presentation(),
		"harvest":game.harvest_presentation.descriptor(),
		"transfer":game.transfer_feedback.descriptor(),
		"carry":game.carry_stacks[game.sim.lead].descriptor(),
		"frame_update_usec":update_usec, "draw_calls":draws, "primitives":prims,
	}
	records.append(row)
	return row

func sample(frame: int, progress: float) -> void:
	var started := Time.get_ticks_usec()
	game.sim.action = canonical_action(progress)
	game._process(1.0 / 60.0)
	game.harvest_presentation._process(1.0 / 60.0)
	game.transfer_feedback._process(1.0 / 60.0)
	configure_review_frame(frame)
	var update_usec := float(Time.get_ticks_usec() - started)
	await process_frame
	var draws := int(RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_DRAW_CALLS_IN_FRAME))
	var prims := int(RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_PRIMITIVES_IN_FRAME))
	frame_usec.append(update_usec); draw_calls.append(draws); primitives.append(prims)
	records.append({
		"frame":frame, "raw_progress":progress,
		"source_units":int(source.units), "inventory":int(game.sim.inventory[resource_kind]),
		"source_visible":game.resource_visuals[String(source.id)].visible,
		"source_cutaway":source_cutaway(), "source_harvest_reveal":source_harvest_reveal(),
		"source_contact_surface_opaque":source_contact_surface_opaque(),
		"harvest":game.harvest_presentation.descriptor(),
		"transfer":game.transfer_feedback.descriptor(),
		"carry":game.carry_stacks[game.sim.lead].descriptor(),
		"frame_update_usec":update_usec, "draw_calls":draws, "primitives":prims,
	})

func commit(frame: int) -> void:
	var before_units := int(source.units)
	var before_inventory := int(game.sim.inventory[resource_kind])
	if before_units <= 0: return
	# Exercise the shipping simulation authority. The capture harness may pose the
	# presentation timeline, but it must never fabricate resource or inventory
	# mutations, nor invent the event consumed by T09/T08.
	game.sim.action = canonical_action(1.0)
	game.sim.events.clear()
	game.sim.perform_action(float(game.sim.tuning.gatherSecondsPerUnit[resource_kind]))
	game.sim.elapsed += 1.0 / 60.0
	game.present_events()
	var authoritative_event: bool = game.sim.events.size() == 1 and String(game.sim.events[0].get("type", "")) == "gather" and String(game.sim.events[0].get("resource", "")) == resource_kind
	records.append({
		"frame":frame, "commit":true, "authority":"outpost_simulation.perform_action",
		"authoritative_event":authoritative_event,
		"units_before":before_units,"units_after":int(source.units),
		"inventory_before":before_inventory,"inventory_after":int(game.sim.inventory[resource_kind]),
		"harvest":game.harvest_presentation.descriptor(),
	})

func sample_cancelled(frame: int) -> void:
	var started := Time.get_ticks_usec()
	game.sim.action = {"kind":"", "id":"", "position":source.position, "actionable":false, "reason":"movement_owns_locomotion"}
	game._process(1.0 / 60.0)
	game.harvest_presentation._process(1.0 / 60.0)
	game.transfer_feedback._process(1.0 / 60.0)
	configure_camera(frame)
	var update_usec := float(Time.get_ticks_usec() - started)
	await process_frame
	var draws := int(RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_DRAW_CALLS_IN_FRAME))
	var prims := int(RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_PRIMITIVES_IN_FRAME))
	frame_usec.append(update_usec); draw_calls.append(draws); primitives.append(prims)
	records.append({
		"frame":frame, "cancelled":true, "reason":"movement_owns_locomotion",
		"source_units":int(source.units), "inventory":int(game.sim.inventory[resource_kind]),
		"source_visible":game.resource_visuals[String(source.id)].visible,
		"source_cutaway":source_cutaway(), "source_harvest_reveal":source_harvest_reveal(),
		"source_contact_surface_opaque":source_contact_surface_opaque(),
		"harvest":game.harvest_presentation.descriptor(),
		"frame_update_usec":update_usec, "draw_calls":draws, "primitives":prims,
	})

func capture_sequence() -> void:
	DirAccess.make_dir_recursive_absolute(output.path_join("frames"))
	var frame := 0
	var target_identity := "gather:" + String(source.id)
	var interaction_radius := float(game.sim.contract.player.interactionRadius)
	var first_token := 0
	var approach_observed := false
	var focus_observed := false
	var commit_observed := false
	var focus_still := false
	while frame < 240 and not commit_observed:
		var delta: Vector2 = Vector2(source.position) - game.sim.position
		var input := delta.normalized() if delta.length() > interaction_radius * 0.70 else Vector2.ZERO
		var phase := "approach" if not input.is_zero_approx() else ("anticipation" if focus_observed else "focus_acquisition")
		var row: Dictionary = await sample_shipping(frame,input,phase)
		approach_observed = approach_observed or (phase == "approach" and float(row.distance_before) > interaction_radius and String(row.action_identity).is_empty())
		if String(row.action_identity) == target_identity and String(row.action_state) in ["acquiring","active"]:
			focus_observed = true
			if first_token == 0: first_token = int(row.action_token)
			if not focus_still:
				focus_still = true
				await capture_png("%s-focus-acquired" % resource_kind)
		commit_observed = commit_observed or bool(row.authoritative_event)
		if frame % 2 == 0: await capture_jpg(frame)
		if frame == 0: await capture_png("%s-approach" % resource_kind)
		if bool(row.authoritative_event): await capture_png("%s-committed-contact" % resource_kind)
		frame += 1
	if not approach_observed or not focus_observed or not commit_observed or first_token <= 0:
		push_error("T09 shipping approach/focus/commit evidence incomplete for " + resource_kind)
		return

	# Keep the committed T07 token visible through a bounded recovery window.
	for recovery_index in 18:
		var row: Dictionary = await sample_shipping(frame,Vector2.ZERO,"recovery")
		if frame % 2 == 0: await capture_jpg(frame)
		if recovery_index == 17: await capture_png("%s-recovery" % resource_kind)
		frame += 1

	# Move outside T07's release annulus so cancellation clears focus, then
	# approach again through the same shipping selector. Re-entry must receive a
	# new director-issued action token rather than a capture-authored token.
	var cancelled_observed := false
	var focus_cleared := false
	for cancel_index in 120:
		var away: Vector2 = (game.sim.position - Vector2(source.position)).normalized()
		if away.is_zero_approx(): away = Vector2.DOWN
		var row: Dictionary = await sample_shipping(frame,away,"cancellation")
		cancelled_observed = cancelled_observed or bool(row.context.get("cancelled",false)) or String(row.action_state) == "blocked_movement"
		focus_cleared = focus_cleared or String(row.action_identity).is_empty()
		if frame % 2 == 0: await capture_jpg(frame)
		if cancel_index == 0: await capture_png("%s-cancelled" % resource_kind)
		frame += 1
		if cancelled_observed and focus_cleared: break
	var reentry_token := 0
	var reentry_active := false
	var reentry_active_frames := 0
	for reentry_index in 240:
		var delta: Vector2 = Vector2(source.position) - game.sim.position
		var input := delta.normalized() if delta.length() > interaction_radius * 0.70 else Vector2.ZERO
		var row: Dictionary = await sample_shipping(frame,input,"reentry")
		if String(row.action_identity) == target_identity and bool(row.actionable):
			reentry_token = int(row.action_token)
			reentry_active = reentry_token > first_token
			reentry_active_frames += 1
		if frame % 2 == 0: await capture_jpg(frame)
		if reentry_active and reentry_active_frames == 1: await capture_png("%s-reentry" % resource_kind)
		frame += 1
		if reentry_active and reentry_active_frames >= 18: break
	if not cancelled_observed or not focus_cleared or not reentry_active:
		push_error("T09 shipping cancellation/re-entry evidence incomplete for " + resource_kind)
		return
	action_token = reentry_token + 1
	if frame % 2 == 1:
		await sample_shipping(frame,Vector2.ZERO,"reentry")
		frame += 1
	# Finish depletion only through the same simulation authority as shipping.
	# Keep the video cursor contiguous while logical commit records advance.
	var video_frame_cursor := frame
	var lifecycle_frame := frame
	while int(source.units) > 0:
		commit(lifecycle_frame)
		game._process(1.0 / 60.0)
		action_token += 1
		lifecycle_frame += 1
	game._process(1.0 / 60.0)
	records.append({"frame":lifecycle_frame,"depleted":true,"source_units":int(source.units),"source_visible":game.resource_visuals[source.id].visible})
	await capture_png("%s-depleted" % resource_kind)
	for video_frame in range(video_frame_cursor,video_frame_cursor+8,2): await capture_jpg(video_frame)
	# Let the unchanged 90-second simulation timer perform the respawn while the
	# lead is away from all harvest targets, then restore the evidence framing.
	var evidence_position: Vector2 = game.sim.position
	game.sim.position = Vector2(float(game.sim.contract.world.boundX),float(game.sim.contract.world.boundZ))
	game.sim.velocity = Vector2.ZERO
	for tick in 901: game.sim.step(0.1,Vector2.ZERO)
	game.sim.position = evidence_position
	game.sim.velocity = Vector2.ZERO
	game.player_rig.position = game.xyz(evidence_position)
	game._process(1.0 / 60.0)
	records.append({"frame":lifecycle_frame+1,"respawned":true,"source_units":int(source.units),"source_visible":game.resource_visuals[source.id].visible})
	await capture_png("%s-respawned" % resource_kind)
	for video_frame in range(video_frame_cursor+8,video_frame_cursor+16,2): await capture_jpg(video_frame)

func capture_tool_view() -> void:
	await sample(0,1.0)
	await sample(1,1.0)
	await capture_png("tool-%s-%s" % [resource_kind,view_id])

func hide_visuals(node: Node) -> void:
	if node is VisualInstance3D and not (node is Light3D): (node as VisualInstance3D).visible = false
	for child in node.get_children(): hide_visuals(child)

func gather_bounds(node: Node, bounds: Dictionary) -> void:
	if node is MeshInstance3D and (node as MeshInstance3D).mesh:
		var mesh_node := node as MeshInstance3D
		var box: AABB = mesh_node.global_transform * mesh_node.get_aabb()
		bounds.value = box if not bounds.set else (bounds.value as AABB).merge(box)
		bounds.set = true
	for child in node.get_children(): gather_bounds(child,bounds)

func capture_asset_view() -> void:
	hide_visuals(game.world)
	for child in game.get_children():
		if child is Control and not (child is TextureRect): (child as Control).visible = false
	var profile: Dictionary = Harvest.profile_for_resource(resource_kind)
	var packed: PackedScene = load(String(profile.asset))
	var stage := Node3D.new()
	stage.name = "T09IsolatedToolTurntable"
	game.world.add_child(stage)
	var tool := packed.instantiate() as Node3D
	stage.add_child(tool)
	await process_frame
	var bounds := {"set":false,"value":AABB()}
	gather_bounds(tool,bounds)
	var box: AABB = bounds.value
	var scale_factor := 2.4 / maxf(0.01,maxf(box.size.x,maxf(box.size.y,box.size.z)))
	tool.scale = Vector3.ONE * scale_factor
	tool.position = -box.get_center() * scale_factor
	var angle_index := mini(7,maxi(0,VIEWS.find(view_id)))
	var angle := TAU * float(angle_index) / 8.0
	var focus := Vector3.ZERO
	var offset := Vector3(sin(angle)*4.2,2.8,cos(angle)*4.2)
	if view_id == "overhead": offset = Vector3(0.001,6.0,0.001)
	elif view_id == "detail": offset = Vector3(2.3,1.7,2.3)
	game.camera.keep_aspect = Camera3D.KEEP_HEIGHT
	game.camera.size = 2.7 if view_id != "detail" else 1.8
	game.camera.global_position = focus + offset
	game.camera.look_at(focus)
	await process_frame
	await capture_png("asset-%s-%s" % [String(profile.tool),view_id])

func capture_device_view() -> void:
	await sample(0,0.82)
	await capture_png("device-%s-%s-preimpact" % [device_id,resource_kind])
	commit(1)
	await sample(1,0.0)
	await capture_png("device-%s-%s-impact-transfer-carry" % [device_id,resource_kind])
	action_token += 1
	var lifecycle_frame := 2
	while int(source.units) > 0:
		commit(lifecycle_frame)
		game._process(1.0/60.0)
		action_token += 1
		lifecycle_frame += 1
	game._process(1.0/60.0)
	records.append({"frame":lifecycle_frame,"depleted":true,"source_units":int(source.units),"source_visible":game.resource_visuals[source.id].visible})
	await capture_png("device-%s-%s-depleted" % [device_id,resource_kind])
	var evidence_position: Vector2 = game.sim.position
	game.sim.position = Vector2(float(game.sim.contract.world.boundX),float(game.sim.contract.world.boundZ))
	game.sim.velocity = Vector2.ZERO
	for tick in 901: game.sim.step(0.1,Vector2.ZERO)
	game.sim.position = evidence_position
	game.sim.velocity = Vector2.ZERO
	game.player_rig.position = game.xyz(evidence_position)
	game._process(1.0/60.0)
	records.append({"frame":lifecycle_frame+1,"respawned":true,"source_units":int(source.units),"source_visible":game.resource_visuals[source.id].visible})
	await capture_png("device-%s-%s-respawned" % [device_id,resource_kind])

func write_report() -> void:
	var report := {
		"task_id":"T09", "candidate":candidate, "mode":mode, "resource":resource_kind,
		"view":view_id, "device_state":device_id, "window":[root.size.x,root.size.y],
		"logical_size":[game.size.x,game.size.y], "internal_render":[game.scene_view.size.x,game.scene_view.size.y],
		"render_scale":game.scene_view.scaling_3d_scale, "native_4k_render":native_4k and game.scene_view.size.x >= 3840 and game.scene_view.size.y >= 2160,
		"physical_4k60_verified":false, "scenario_is_test_fixture":true,
		"review_visibility_policy":"selected_actor_source_effects_on_shipping_surface",
		"capture_progress_driver":"shipping_simulation_step" if mode == "sequence" else "presentation_fixture",
		"t07_selection_authority":"context_director.advance" if mode == "sequence" else "fixture_not_claimed",
		"commit_authority":"outpost_simulation.perform_action",
		"simulation_authoritative":records.any(func(record): return bool(record.get("commit",false)) and bool(record.get("authoritative_event",false))),
		"harvest_contract":Harvest.contract(),
		"final_harvest":game.harvest_presentation.descriptor(), "final_transfer":game.transfer_feedback.descriptor(),
		"samples":records, "performance":{
			"sample_count":frame_usec.size(), "average_update_usec":average(frame_usec), "maximum_update_usec":maximum(frame_usec),
			"average_draw_calls":average(draw_calls), "maximum_draw_calls":maximum(draw_calls),
			"average_primitives":average(primitives), "maximum_primitives":maximum(primitives),
		},
	}
	var file := FileAccess.open(output.path_join("capture-report.json"),FileAccess.WRITE)
	file.store_string(JSON.stringify(report,"\t"))
	file.close()

func run() -> void:
	if resource_kind not in ["wood","stone","metal","fuel"] or mode not in ["sequence","tool","asset","device"]:
		push_error("Invalid T09 capture request")
		quit(2)
		return
	DirAccess.make_dir_recursive_absolute(output)
	game = Main.new()
	game.size = DEVICE_SIZES.get(device_id,Vector2(2400,1080))
	root.add_child(game)
	for frame in 5: await process_frame
	game.set_process(false)
	game.set_physics_process(false)
	game.harvest_presentation.set_process(false)
	game.transfer_feedback.set_process(false)
	# Discard incidental startup presentation before measuring this isolated source.
	game.harvest_presentation.reset()
	for candidate_source in game.sim.resources:
		if String(candidate_source.kind) == resource_kind:
			source = candidate_source
			break
	if source.is_empty():
		push_error("T09 capture source missing: " + resource_kind)
		quit(3)
		return
	focus_review_visibility()
	action_token += ["wood","stone","metal","fuel"].find(resource_kind) * 100
	# Opening sources sit outside the protected camp fence. Start on their camp
	# side and approach outward so T03 collision remains active and the actor can
	# reach the interaction annulus without teleporting across a boundary.
	var approach_axis := -Vector2(source.position).normalized() if mode == "sequence" else Vector2(source.position).normalized()
	if mode == "sequence" and resource_kind == "metal":
		# The ore source is on the dry far bank. Begin farther along that same bank
		# so the evidence shows a traversable approach without crossing the frozen
		# river or teleporting directly into the interaction annulus.
		approach_axis = Vector2(0.0,-1.0)
	if approach_axis.is_zero_approx(): approach_axis = Vector2.DOWN
	game.sim.position = Vector2(source.position) + approach_axis * (float(game.sim.contract.player.interactionRadius) + (2.2 if mode == "sequence" else -0.73))
	game.sim.facing = (source.position - game.sim.position).normalized()
	game.sim.velocity = Vector2.ZERO
	game.player_rig.position = game.xyz(game.sim.position)
	game.player_rig.rotation.y = atan2(game.sim.facing.x,game.sim.facing.y)
	if mode == "sequence": await capture_sequence()
	elif mode == "tool": await capture_tool_view()
	elif mode == "asset": await capture_asset_view()
	else: await capture_device_view()
	write_report()
	if is_instance_valid(game.outpost_audio): game.outpost_audio.stop_all()
	await create_timer(0.35).timeout
	game.free()
	await process_frame
	await process_frame
	quit(0)
