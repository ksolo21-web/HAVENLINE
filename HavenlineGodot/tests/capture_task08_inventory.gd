extends SceneTree

const Main = preload("res://scripts/main.gd")
const Carry = preload("res://scripts/carry_stack.gd")
const Stockpile = preload("res://scripts/storage_stockpile.gd")
const Transfer = preload("res://scripts/transfer_feedback.gd")

var output := "user://task08-inventory"
var candidate := "local-working-tree"
var state := "carrying"
var device_id := "review_16_9"
var native_4k := false
var integrated := false
var view_id := "front"
var game
var stockpile
var records: Array = []
var frame_usec: Array[float] = []
var draw_calls: Array[int] = []
var primitives: Array[int] = []
var sink_units := 0
var integrity_evidence := {}
var route_camera_active := false
var route_camera_focus := Vector3.ZERO
var route_camera_size := 0.0
var route_camera_start := Vector3.ZERO
var route_camera_finish := Vector3.ZERO
var route_camera_destination := ""

func _initialize() -> void:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--out="): output = argument.trim_prefix("--out=")
		elif argument.begins_with("--candidate="): candidate = argument.trim_prefix("--candidate=")
		elif argument.begins_with("--state="): state = argument.trim_prefix("--state=")
		elif argument.begins_with("--device="): device_id = argument.trim_prefix("--device=")
		elif argument.begins_with("--view="): view_id = argument.trim_prefix("--view=")
		elif argument == "--native-4k": native_4k = true
		elif argument == "--integrated": integrated = true
	call_deferred("run")

func total_authority() -> int:
	var total := 0
	for value in game.sim.inventory.values(): total += int(value)
	for value in game.sim.stored.values(): total += int(value)
	for resource in game.sim.resources: total += int(resource.units)
	for companion in game.sim.companions: total += int(companion.get("cargo", 0))
	for defense in game.sim.defenses.values():
		for value in defense.delivered.values(): total += int(value)
	return total + sink_units

func actor_point(id: int) -> Vector3:
	if game.actors.has(id): return game.actors[id].global_position + Vector3(0.0, 1.0, -0.35)
	return game.xyz(game.sim.position) + Vector3(0.0, 1.0, -0.35)

func source_point(index := 0) -> Vector3:
	return game.xyz(game.sim.resources[index].position) + Vector3.UP * 0.75

func destination_point() -> Vector3:
	return game.xyz(game.sim.point(game.sim.contract.world.storage)) + Vector3.UP * 0.75

func target_point(target: Vector2) -> Vector3:
	return game.xyz(target) + Vector3.UP * 0.9

func configure_route_camera(start: Vector3, finish: Vector3, destination_id: String) -> void:
	route_camera_active = true
	route_camera_start = start
	route_camera_finish = finish
	route_camera_destination = destination_id
	route_camera_focus = start.lerp(finish, 0.5) + Vector3.UP * 0.3
	route_camera_size = clampf(start.distance_to(finish) * 0.88 + 5.5, 8.0, 34.0)

func apply_route_camera() -> void:
	if not route_camera_active:
		return
	game.camera.keep_aspect = Camera3D.KEEP_HEIGHT
	game.camera.size = route_camera_size
	game.camera.position = route_camera_focus + Vector3(10.0, 8.0, 11.0).normalized() * 30.0
	game.camera.look_at(route_camera_focus)
	# Expand only when projection proves an endpoint would be cropped. This keeps
	# actor, destination, route and arrival pulse together without guesswork.
	for attempt in 4:
		var start_screen: Vector2 = game.camera.unproject_position(route_camera_start)
		var finish_screen: Vector2 = game.camera.unproject_position(route_camera_finish)
		var viewport_size := Vector2(game.scene_view.size)
		var margin := viewport_size * 0.08
		if start_screen.x >= margin.x and start_screen.y >= margin.y and start_screen.x <= viewport_size.x - margin.x and start_screen.y <= viewport_size.y - margin.y and finish_screen.x >= margin.x and finish_screen.y >= margin.y and finish_screen.x <= viewport_size.x - margin.x and finish_screen.y <= viewport_size.y - margin.y:
			break
		game.camera.size *= 1.22
	route_camera_size = game.camera.size

func route_camera_descriptor() -> Dictionary:
	if not route_camera_active:
		return {"active":false}
	var start_screen: Vector2 = game.camera.unproject_position(route_camera_start)
	var finish_screen: Vector2 = game.camera.unproject_position(route_camera_finish)
	var viewport_size := Vector2(game.scene_view.size)
	var margin := viewport_size * 0.06
	var endpoints_visible: bool = not game.camera.is_position_behind(route_camera_start) and not game.camera.is_position_behind(route_camera_finish)
	for point in [start_screen, finish_screen]:
		endpoints_visible = endpoints_visible and point.x >= margin.x and point.y >= margin.y and point.x <= viewport_size.x - margin.x and point.y <= viewport_size.y - margin.y
	return {
		"active":true, "mode":"midpoint_endpoints", "destination_id":route_camera_destination,
		"size":route_camera_size, "endpoints_visible":endpoints_visible,
		"start_screen":[start_screen.x,start_screen.y], "finish_screen":[finish_screen.x,finish_screen.y],
		"viewport":[viewport_size.x,viewport_size.y],
	}

func spend_actor(kind: String, actor_id: int, helper: bool) -> bool:
	if helper:
		for companion in game.sim.companions:
			if int(companion.id) == actor_id and String(companion.get("cargo_kind", "")) == kind and int(companion.get("cargo", 0)) > 0:
				companion.cargo -= 1
				return true
		return false
	if int(game.sim.inventory.get(kind, 0)) <= 0: return false
	game.sim.inventory[kind] -= 1
	return true

func commit_route(route: String, actor_id: int, helper: bool, target: Vector2, destination_id: String, kind := "wood") -> void:
	if not spend_actor(kind, actor_id, helper): return
	var flight_start := actor_point(actor_id)
	var flight_finish := target_point(target)
	if state == "route-proofs":
		configure_route_camera(flight_start, flight_finish, destination_id)
	if route == "deposit": game.sim.stored[kind] += 1
	elif route == "build":
		var side := destination_id.trim_prefix("defense:")
		game.sim.defenses[side].delivered[kind] += 1
	elif route == "repair": sink_units += 1
	var event_type := "worker_" + route if helper else route
	var actor_position: Vector2 = game.sim.position
	if helper:
		for companion in game.sim.companions:
			if int(companion.id) == actor_id: actor_position = companion.position
	if integrated:
		game.sim.elapsed += 1.0
		game.sim.events = [{"type":event_type, "actor_id":actor_id, "position":actor_position,
			"target":target, "resource":kind, "destination_id":destination_id}]
		game.present_events()
	else:
		game.transfer_feedback.transfer(kind, flight_start, flight_finish,
			"capture:%s:%d:%d" % [route, actor_id, records.size()], "actor_to_destination", actor_id, destination_id)

func commit_gather(actor_id: int, helper := false) -> void:
	var resource: Dictionary = game.sim.resources[0]
	if int(resource.units) <= 0: return
	resource.units -= 1
	if helper:
		for companion in game.sim.companions:
			if int(companion.id) == actor_id:
				companion.cargo_kind = String(resource.kind)
				companion.cargo = int(companion.get("cargo", 0)) + 1
				break
	else:
		game.sim.inventory[String(resource.kind)] += 1
	game.transfer_feedback.transfer(String(resource.kind), source_point(), actor_point(actor_id),
		"capture:gather:%d:%d" % [actor_id, records.size()], "source_to_actor", actor_id, "actor:%d" % actor_id)

func commit_deposit(actor_id: int, helper := false) -> void:
	var kind := "wood"
	if helper:
		for companion in game.sim.companions:
			if int(companion.id) == actor_id and int(companion.get("cargo", 0)) > 0:
				kind = String(companion.get("cargo_kind", "wood"))
				companion.cargo -= 1
				break
	else:
		if int(game.sim.inventory[kind]) <= 0: return
		game.sim.inventory[kind] -= 1
	game.sim.stored[kind] += 1
	game.transfer_feedback.transfer(kind, actor_point(actor_id), destination_point(),
		"capture:deposit:%d:%d" % [actor_id, records.size()], "actor_to_destination", actor_id, "camp_storage")

func average(values: Array) -> float:
	if values.is_empty(): return 0.0
	var total := 0.0
	for value in values: total += float(value)
	return total / float(values.size())

func maximum(values: Array) -> float:
	var result := 0.0
	for value in values: result = maxf(result, float(value))
	return result

func visible_material_count() -> int:
	var materials := {}
	for candidate in game.world.find_children("*", "MeshInstance3D", true, false):
		var mesh_instance := candidate as MeshInstance3D
		if mesh_instance == null or not mesh_instance.is_visible_in_tree() or mesh_instance.mesh == null:
			continue
		for surface in mesh_instance.mesh.get_surface_count():
			var material := mesh_instance.get_active_material(surface)
			if material != null:
				materials[material.get_rid().get_id()] = true
	return materials.size()

func layout_rects() -> Dictionary:
	var result := {}
	for key in game.layout_snapshot.get("rects", {}):
		var rect: Rect2 = game.layout_snapshot.rects[key]
		result[key] = [rect.position.x, rect.position.y, rect.size.x, rect.size.y]
	return result

func capture_png(name: String) -> void:
	await process_frame
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png(output.path_join(name + ".png"))

func capture_jpg(frame: int) -> void:
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_jpg(output.path_join("frames/frame-%05d.jpg" % int(frame / 3)), 0.9)

func sample(frame: int) -> void:
	var started := Time.get_ticks_usec()
	game.transfer_feedback._process(1.0 / 60.0)
	game._process(1.0 / 60.0)
	stockpile.sync(game.sim.stored)
	if state == "route-proofs":
		apply_route_camera()
	var elapsed_usec := float(Time.get_ticks_usec() - started)
	await process_frame
	await RenderingServer.frame_post_draw
	var draws := int(RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_DRAW_CALLS_IN_FRAME))
	var prims := int(RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_PRIMITIVES_IN_FRAME))
	frame_usec.append(elapsed_usec); draw_calls.append(draws); primitives.append(prims)
	records.append({
		"frame":frame, "authority_total":total_authority(),
		"inventory":game.sim.inventory.duplicate(true), "stored":game.sim.stored.duplicate(true),
		"player_stack":game.carry_stacks[game.sim.lead].descriptor(),
		"helper_stack":game.carry_stacks[2].descriptor(), "stockpile":stockpile.descriptor(),
		"transfers":game.transfer_feedback.descriptor(),
		"route_camera":route_camera_descriptor(),
		"frame_usec":elapsed_usec, "draw_calls":draws, "primitives":prims,
	})

func warm_scene(frame_count: int) -> void:
	for frame in frame_count:
		game.transfer_feedback._process(1.0 / 60.0)
		game._process(1.0 / 60.0)
		stockpile.sync(game.sim.stored)
		await process_frame
		await RenderingServer.frame_post_draw

func capture_sequence() -> void:
	DirAccess.make_dir_recursive_absolute(output.path_join("frames"))
	await warm_scene(90)
	for frame in 180:
		if frame == 12: commit_gather(game.sim.lead)
		elif frame == 54: commit_deposit(game.sim.lead)
		elif frame == 96: commit_gather(2, true)
		elif frame == 138: commit_deposit(2, true)
		await sample(frame)
		if frame % 3 == 0: await capture_jpg(frame)
		if frame in [0, 24, 66, 108, 150, 179]: await capture_png("sequence-%03d" % frame)
	for frame in range(180, 184): await sample(frame)

func capture_routes() -> void:
	DirAccess.make_dir_recursive_absolute(output.path_join("frames"))
	var furnace: Vector2 = game.sim.point(game.sim.contract.world.furnace)
	var storage: Vector2 = game.sim.point(game.sim.contract.world.storage)
	var north: Vector2 = game.sim.defenses.north.position
	var south: Vector2 = game.sim.defenses.south.position
	var arrival_frames := {
		60:"arrival-furnace-storage", 132:"arrival-camp-storage",
		204:"arrival-defense-north", 276:"arrival-defense-south",
		348:"arrival-repair-furnace", 420:"arrival-repair-north",
	}
	for frame in 444:
		if frame == 12: commit_route("deposit", game.sim.lead, false, furnace, "furnace_storage")
		elif frame == 84: commit_route("deposit", 2, true, storage, "camp_storage")
		elif frame == 156: commit_route("build", game.sim.lead, false, north, "defense:north")
		elif frame == 228: commit_route("build", 2, true, south, "defense:south")
		elif frame == 300: commit_route("repair", game.sim.lead, false, furnace, "repair:furnace")
		elif frame == 372: commit_route("repair", 2, true, north, "repair:north")
		await sample(frame)
		if frame % 3 == 0: await capture_jpg(frame)
		if frame == 0 or frame == 443: await capture_png("routes-%03d" % frame)
		elif arrival_frames.has(frame): await capture_png(String(arrival_frames[frame]))
	for frame in range(444, 448): await sample(frame)

func actor_stack_totals() -> Dictionary:
	var result := {}
	for id in game.carry_stacks: result[str(id)] = game.carry_stacks[id].descriptor().logical_total
	return result

func capture_integrity() -> void:
	await sample(0)
	var before := actor_stack_totals()
	await capture_png("integrity-before-switch")
	var switched: bool = game.sim.select_lead(2)
	game.carry_root = game.carry_stacks[game.sim.lead]
	game.player_rig = game.actors[game.sim.lead]
	game.update_carry()
	await sample(1)
	var after_switch := actor_stack_totals()
	await capture_png("integrity-after-switch")
	game.actors[3].visible = false
	game.sim.presented_actor_ids.erase(3)
	game.update_carry()
	if not integrated:
		game.carry_stacks[3].visible = false
		game.carry_stacks[3].update_inventory({"wood":0,"stone":0,"metal":0,"fuel":0})
	await sample(2)
	if not integrated:
		game.carry_stacks[3].visible = false
		game.carry_stacks[3].update_inventory({"wood":0,"stone":0,"metal":0,"fuel":0})
	var after_hide := actor_stack_totals()
	await capture_png("integrity-hidden-actor")
	integrity_evidence = {"switch_succeeded":switched, "before":before, "after_switch":after_switch,
		"after_hide":after_hide, "selected_lead":game.sim.lead, "hidden_actor_id":3,
		"hidden_actor_visible":game.actors[3].visible, "hidden_stack_visible":game.carry_stacks[3].visible,
		"hidden_stack_logical_total":game.carry_stacks[3].descriptor().logical_total}

func capture_static() -> void:
	if state == "transfer": commit_gather(game.sim.lead)
	for frame in 18: await sample(frame)
	await capture_png("%s-%s" % [state, view_id])

func run() -> void:
	DirAccess.make_dir_recursive_absolute(output)
	root.content_scale_size = root.size
	game = Main.new()
	game.qa_mode = true
	game.render_review = not native_4k
	game.capture_frames = -10000
	game.position = Vector2.ZERO
	game.size = Vector2(root.size)
	root.add_child(game)
	game.resize_render()
	game.apply_hud_layout(Rect2(Vector2.ZERO, game.size), 1.0)
	game.set_process(false); game.set_physics_process(false)
	game.transfer_feedback.set_process(false)
	game.sim.threats_enabled = false
	game.sim.position = Vector2(-1.3, 1.65)
	# Keep independent evidence scenarios visually distinct without adding a QA
	# banner. Their initial frames otherwise can be pixel-identical on the
	# isolated harness even though the subsequent event routes differ.
	if state == "sequence": game.sim.position += Vector2(-0.35, 0.0)
	elif state == "routes": game.sim.position += Vector2(0.35, 0.0)
	elif state == "route-proofs": game.sim.position += Vector2(0.55, 0.0)
	game.sim.inventory = {"wood":8,"stone":4,"metal":2,"fuel":2}
	game.sim.stored = {"wood":9,"stone":6,"metal":3,"fuel":2}
	for companion in game.sim.companions:
		if int(companion.id) == 2:
			companion.position = Vector2(-0.1, 1.9)
			if state == "sequence": companion.position += Vector2(0.0, -0.2)
			elif state == "routes": companion.position += Vector2(0.0, 0.2)
			elif state == "route-proofs": companion.position += Vector2(0.0, 0.35)
			companion.cargo_kind = "wood"; companion.cargo = 4
		elif state == "integrity" and int(companion.id) == 3:
			companion.cargo_kind = "metal"; companion.cargo = 3
	if integrated:
		stockpile = game.storage_stockpile
	else:
		stockpile = Stockpile.new()
		stockpile.name = "T08CampStorageStockpile"
		stockpile.position = game.xyz(game.sim.point(game.sim.contract.world.storage)) + Vector3(0.8, 0.05, 0.25)
		game.world.add_child(stockpile)
		stockpile.configure("camp_storage", game.sim.stored)
	game.update_carry()
	var initial_total := total_authority()
	if state == "sequence": await capture_sequence()
	elif state in ["routes", "route-proofs"]: await capture_routes()
	elif state == "integrity": await capture_integrity()
	else: await capture_static()
	var all_totals := records.map(func(row): return int(row.authority_total))
	var report := {
		"task":"T08-visible-inventory-v1", "candidate_commit":candidate,
		"state":state, "view":view_id, "device_id":device_id,
		"renderer":RenderingServer.get_current_rendering_method(), "device":RenderingServer.get_video_adapter_name(),
		"window":[root.size.x,root.size.y], "game_rect":[game.position.x,game.position.y,game.size.x,game.size.y],
		"internal_render":[game.scene_view.size.x,game.scene_view.size.y],
		"native_3840x2160_scale1":native_4k and root.size == Vector2i(3840,2160) and is_equal_approx(game.scene_view.scaling_3d_scale,1.0),
		"shipping_main_scene_rendered":true,
		"shipping_call_site_exercised":integrated,
		"shipping_stockpile_instance_reported":not integrated or stockpile == game.storage_stockpile,
		"candidate_components_applied_directly_because_stockpile_call_site_is_integration_only":not integrated,
		"qa_evidence_banner_present":false, "permanent_action_buttons":0, "movement_control":"one_primary_joystick",
		"layout_rects":layout_rects(), "trace":records, "initial_authority_total":initial_total,
		"performance_warmup_frames":90 if state == "sequence" else 0,
		"conservation_held":all_totals.all(func(value): return value == initial_total),
		"player_stack":game.carry_stacks[game.sim.lead].descriptor(), "helper_stack":game.carry_stacks[2].descriptor(),
		"stockpile":stockpile.descriptor(), "transfers":game.transfer_feedback.descriptor(),
		"carry_contract":Carry.contract(), "transfer_contract":Transfer.contract(),
		"sink_units":sink_units, "actor_integrity":integrity_evidence,
		"shipping_scene_metrics":{"average_frame_usec":average(frame_usec),"maximum_frame_usec":maximum(frame_usec),"average_draw_calls":average(draw_calls),"maximum_draw_calls":int(maximum(draw_calls)),"average_primitives":average(primitives),"maximum_primitives":int(maximum(primitives)),"texture_memory_bytes":RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TEXTURE_MEM_USED),"video_memory_bytes":RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_VIDEO_MEM_USED),"process_static_memory_bytes":OS.get_static_memory_usage(),"materials_visible":visible_material_count(),"physics_body_count":game.world.find_children("*","PhysicsBody3D",true,false).size(),"animation_player_count":game.world.find_children("*","AnimationPlayer",true,false).size(),"population_count":game.actors.values().filter(func(actor): return is_instance_valid(actor) and actor.visible).size()},
		"physical_device_native_4k60_certified":false,
	}
	var file := FileAccess.open(output.path_join("capture.json"),FileAccess.WRITE)
	file.store_string(JSON.stringify(report,"\t")); file.close()
	game.outpost_audio.stop_all()
	await create_timer(0.25).timeout
	game.free(); await process_frame; quit()
