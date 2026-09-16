extends SceneTree

const Main = preload("res://scripts/main.gd")
const Harvest = preload("res://scripts/harvest_presentation.gd")

const DEVICE_SIZES := {
	"phone_16_9":Vector2(2400,1080), "phone_20_9":Vector2(2400,1080),
	"tablet_16_10":Vector2(2560,1600), "tablet_4_3":Vector2(2732,2048),
	"foldable_outer":Vector2(2520,1080), "foldable_inner":Vector2(2208,1768),
}
const VIEWS := ["front","front-right","right","rear-right","rear","rear-left","left","front-left"]

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

func configure_camera(frame := 0) -> void:
	var focus := actor_point().lerp(source_point(),0.55)
	var angle_index := VIEWS.find(view_id)
	if angle_index < 0: angle_index = 0
	var angle := TAU * float(angle_index) / float(VIEWS.size())
	var distance := 13.0 if mode == "device" else 8.2
	var offset := Vector3(sin(angle) * distance,5.0,cos(angle) * distance)
	game.camera.keep_aspect = Camera3D.KEEP_HEIGHT
	game.camera.size = 13.5 if mode == "device" else 6.4
	game.camera.global_position = focus + offset
	game.camera.look_at(focus + Vector3.UP * (0.08 * sin(float(frame) * 0.03)))

func canonical_action(progress: float) -> Dictionary:
	return {
		"kind":"gather", "id":String(source.id), "position":source.position,
		"resource":resource_kind, "source_id":String(source.id),
		"action_token":901 + ["wood","stone","metal","fuel"].find(resource_kind),
		"progress":clampf(progress,0.0,1.0), "role":"player_lead", "actionable":true,
	}

func capture_png(name: String) -> void:
	await process_frame
	root.get_texture().get_image().save_png(output.path_join(name + ".png"))

func capture_jpg(frame: int) -> void:
	await process_frame
	root.get_texture().get_image().save_jpg(output.path_join("frames/frame-%05d.jpg" % int(frame / 2)),0.91)

func sample(frame: int, progress: float) -> void:
	var started := Time.get_ticks_usec()
	game.sim.action = canonical_action(progress)
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
		"frame":frame, "raw_progress":progress,
		"source_units":int(source.units), "inventory":int(game.sim.inventory[resource_kind]),
		"harvest":game.harvest_presentation.descriptor(),
		"transfer":game.transfer_feedback.descriptor(),
		"frame_update_usec":update_usec, "draw_calls":draws, "primitives":prims,
	})

func commit(frame: int) -> void:
	var before_units := int(source.units)
	var before_inventory := int(game.sim.inventory[resource_kind])
	if before_units <= 0: return
	source.units = before_units - 1
	game.sim.inventory[resource_kind] = before_inventory + 1
	game.sim.action = canonical_action(0.0)
	game.sim.events = [{"type":"gather","position":source.position,"resource":resource_kind}]
	game.sim.elapsed += 1.0 / 60.0
	game.present_events()
	records.append({"frame":frame,"commit":true,"units_before":before_units,"units_after":int(source.units),"inventory_before":before_inventory,"inventory_after":int(game.sim.inventory[resource_kind])})

func capture_sequence() -> void:
	DirAccess.make_dir_recursive_absolute(output.path_join("frames"))
	for frame in 72:
		var progress := float(frame) / 30.0 if frame <= 30 else float(frame - 30) / 41.0
		if frame == 30: commit(frame)
		await sample(frame,progress)
		if frame % 2 == 0: await capture_jpg(frame)
		if frame in [0,21,30,41,71]:
			await capture_png("%s-%03d" % [resource_kind,frame])

func capture_tool_view() -> void:
	await sample(0,1.0)
	await sample(1,1.0)
	await capture_png("tool-%s-%s" % [resource_kind,view_id])

func capture_device_view() -> void:
	await sample(0,0.82)
	await sample(1,0.86)
	await capture_png("device-%s-%s" % [device_id,resource_kind])

func write_report() -> void:
	var report := {
		"task_id":"T09", "candidate":candidate, "mode":mode, "resource":resource_kind,
		"view":view_id, "device_state":device_id, "window":[root.size.x,root.size.y],
		"logical_size":[game.size.x,game.size.y], "internal_render":[game.scene_view.size.x,game.scene_view.size.y],
		"render_scale":game.scene_view.scaling_3d_scale, "native_4k_render":native_4k and game.scene_view.size.x >= 3840 and game.scene_view.size.y >= 2160,
		"physical_4k60_verified":false, "scenario_is_test_fixture":true,
		"simulation_authoritative":true, "harvest_contract":Harvest.contract(),
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
	if resource_kind not in ["wood","stone","metal","fuel"] or mode not in ["sequence","tool","device"]:
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
	for candidate_source in game.sim.resources:
		if String(candidate_source.kind) == resource_kind:
			source = candidate_source
			break
	if source.is_empty():
		push_error("T09 capture source missing: " + resource_kind)
		quit(3)
		return
	source.units = maxi(2,int(source.units))
	game.sim.position = source.position + Vector2(0.0,1.12)
	game.sim.facing = (source.position - game.sim.position).normalized()
	game.sim.velocity = Vector2.ZERO
	game.player_rig.position = game.xyz(game.sim.position)
	game.player_rig.rotation.y = atan2(game.sim.facing.x,game.sim.facing.y)
	if mode == "sequence": await capture_sequence()
	elif mode == "tool": await capture_tool_view()
	else: await capture_device_view()
	write_report()
	if is_instance_valid(game.outpost_audio): game.outpost_audio.stop_all()
	game.free()
	await process_frame
	quit(0)
