extends SceneTree

## Exact-scene T04 evidence. The isolated candidate applies the shipping
## composition component directly because main.gd remains integration-only.

const Main = preload("res://scripts/main.gd")
const Composition = preload("res://scripts/camera_composition.gd")
const Boundary = preload("res://scripts/camp_boundary.gd")

var output := "user://task04-camera"
var native := false
var game
var controller = Composition.new()
var records: Array = []

func _initialize() -> void:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--out="):
			output = argument.trim_prefix("--out=")
		if argument == "--native-4k":
			native = true
	call_deferred("run")

func world_at(point: Vector2, height := 0.0) -> Vector3:
	return game.xyz(point) + Vector3(0.0, height, 0.0)

func normalized_screen(point: Vector3) -> Array:
	var pixel: Vector2 = game.camera.unproject_position(point)
	var size := Vector2(game.scene_view.size)
	return [pixel.x / size.x, pixel.y / size.y]

func apply_composition(
	player: Vector2,
	velocity: Vector2,
	facing: Vector2,
	target: Variant,
	viewport: Vector2,
	snap_camera := true,
	delta := 1.0 / 60.0
) -> Dictionary:
	game.size = viewport
	game.resize_render()
	game.sim.position = player
	game.sim.velocity = velocity
	game.sim.facing = facing
	game.player_rig.position = world_at(player)
	var target_world: Variant = world_at(target, 0.7) if target is Vector2 else null
	var row := controller.compose(world_at(player), Vector3(velocity.x, 0.0, velocity.y), Vector3(facing.x, 0.0, facing.y), target_world, viewport, delta, snap_camera)
	game.camera.keep_aspect = row.keep_aspect
	game.camera.size = row.full_height
	game.camera.position = row.camera_position
	game.camera.look_at(row.focus)
	# A snap stands in for an already-settled shipping camera. Let the existing
	# opaque-dither pine cutaway reach that stable state instead of recording a
	# misleading single-frame transition pattern after a QA teleport.
	if snap_camera:
		for _step in range(6):
			game.update_foreground_visibility(world_at(player, 0.95), 0.05)
	else:
		game.update_foreground_visibility(world_at(player, 0.95), delta)
	game.outpost_view.sync(game.sim, delta, false)
	return row

func snap(name: String, viewport: Vector2, row: Dictionary, target: Variant = null) -> void:
	await process_frame
	await RenderingServer.frame_post_draw
	await process_frame
	await RenderingServer.frame_post_draw
	var image: Image = game.scene_view.get_texture().get_image()
	image.save_png(output.path_join(name + ".png"))
	var feet := world_at(game.sim.position)
	var head := feet + Vector3(0.0, 1.8, 0.0)
	var feet_screen: Vector2 = game.camera.unproject_position(feet)
	var head_screen: Vector2 = game.camera.unproject_position(head)
	var target_world: Variant = world_at(target, 0.7) if target is Vector2 else null
	records.append({
		"name": name,
		"requested_viewport": [viewport.x, viewport.y],
		"internal_size": [image.get_width(), image.get_height()],
		"render_scale": game.scene_view.scaling_3d_scale,
		"camera_full_height": game.camera.size,
		"camera_position": [game.camera.position.x, game.camera.position.y, game.camera.position.z],
		"focus": [row.focus.x, row.focus.y, row.focus.z],
		"player": [game.sim.position.x, game.sim.position.y],
		"player_anchor_normalized": normalized_screen(world_at(game.sim.position, 0.95)),
		"player_height_fraction": feet_screen.distance_to(head_screen) / float(image.get_height()),
		"target_anchor_normalized": normalized_screen(target_world) if target_world is Vector3 else null,
		"target_in_range": row.target_in_range,
		"draw_calls": game.scene_view.get_render_info(Viewport.RENDER_INFO_TYPE_VISIBLE, Viewport.RENDER_INFO_DRAW_CALLS_IN_FRAME),
		"submitted_primitives": game.scene_view.get_render_info(Viewport.RENDER_INFO_TYPE_VISIBLE, Viewport.RENDER_INFO_PRIMITIVES_IN_FRAME)
	})

func capture_aspects() -> void:
	var states := [
		["phone-16-9", Vector2(1920,1080)],
		["phone-20-9", Vector2(2400,1080)],
		["tablet-16-10", Vector2(2560,1600)],
		["tablet-4-3", Vector2(2732,2048)],
		["foldable-outer", Vector2(2520,1080)],
		["foldable-inner", Vector2(2208,1768)]
	]
	for state in states:
		controller = Composition.new()
		var row := apply_composition(Vector2(0.0, 4.8), Vector2(0,-1), Vector2(0,-1), Vector2(0.0,0.2), state[1], true)
		await snap("aspect-" + state[0], state[1], row, Vector2(0.0,0.2))

func capture_directional_tracking() -> void:
	var viewport := Vector2(1920,1080)
	for state in [
		["north", Vector2(0,-1)],
		["east", Vector2(1,0)],
		["south", Vector2(0,1)],
		["west", Vector2(-1,0)]
	]:
		controller = Composition.new()
		var velocity: Vector2 = state[1] * 2.8
		var row := apply_composition(Vector2(0.0,2.4), velocity, state[1], null, viewport, true)
		await snap("direction-" + state[0], viewport, row)

func capture_target_and_transitions() -> void:
	var wide := Vector2(2400,1080)
	var inner := Vector2(2208,1768)
	controller = Composition.new()
	var player := Vector2(-4.2,4.0)
	var storage_target := Vector2(-2.8,2.25)
	var facing := (storage_target-player).normalized()
	var row := apply_composition(player, Vector2.ZERO, facing, storage_target, wide, true)
	await snap("target-inclusion-storage", wide, row, storage_target)
	row = apply_composition(player, Vector2.ZERO, facing, null, wide, false)
	await snap("target-release-damped", wide, row)
	row = apply_composition(player, Vector2.ZERO, facing, null, inner, false)
	await snap("resize-fold-inner-safe", inner, row)
	for _i in range(45):
		row = apply_composition(player, Vector2.ZERO, facing, null, inner, false)
	await snap("resize-fold-inner-settled", inner, row)

func capture_gameplay_context() -> void:
	var viewport := Vector2(1920,1080)
	controller = Composition.new()
	var west_gate: Vector2 = Boundary.gate_specs().filter(func(g): return g.id == "west-work")[0].center
	var row := apply_composition(Vector2(-8.7,2.4), Vector2(-1,0), Vector2(-1,0), west_gate, viewport, true)
	await snap("gameplay-west-gate", viewport, row, west_gate)
	controller = Composition.new()
	row = apply_composition(Vector2(-6.5,-9.0), Vector2(0,-1), Vector2(0,-1), Vector2(-8.0,-12.0), viewport, true)
	await snap("gameplay-lakeshore", viewport, row, Vector2(-8.0,-12.0))
	controller = Composition.new()
	row = apply_composition(Vector2(0.0,5.8), Vector2(0,-1), Vector2(0,-1), Vector2(0.0,0.2), viewport, true)
	await snap("gameplay-camp", viewport, row, Vector2(0.0,0.2))
	for condition in [["day",0.0],["night",930.0],["blizzard",630.0]]:
		game.sim.climate.seconds = condition[1]
		game.outpost_view.sync(game.sim, 0.1, false)
		await snap("condition-" + condition[0], viewport, row, Vector2(0.0,0.2))

func capture_native() -> void:
	var viewport := Vector2(3840,2160)
	controller = Composition.new()
	var row := apply_composition(Vector2(0.0,4.8), Vector2(0,-1), Vector2(0,-1), Vector2(0.0,0.2), viewport, true)
	await snap("native-gameplay-camp", viewport, row, Vector2(0.0,0.2))
	controller = Composition.new()
	row = apply_composition(Vector2(-6.5,-9.0), Vector2(0,-1), Vector2(0,-1), Vector2(-8.0,-12.0), viewport, true)
	await snap("native-gameplay-lakeshore", viewport, row, Vector2(-8.0,-12.0))
	controller = Composition.new()
	row = apply_composition(Vector2(9.0,-5.8), Vector2(0,-1), Vector2(0,-1), Boundary.river_approach_point(10.0), viewport, true)
	await snap("native-gameplay-east-river-gate", viewport, row, Boundary.river_approach_point(10.0))

func run() -> void:
	DirAccess.make_dir_recursive_absolute(output)
	game = Main.new()
	game.qa_mode = true
	game.render_review = not native
	game.capture_directory = output
	game.capture_frames = 100
	game.size = Vector2(3840,2160) if native else Vector2(1280,720)
	root.add_child(game)
	game.set_process(false)
	game.set_physics_process(false)
	if native:
		await capture_native()
	else:
		await capture_aspects()
		await capture_directional_tracking()
		await capture_target_and_transitions()
		await capture_gameplay_context()
	var report := {
		"task": "T04-reference-camera-v1",
		"candidate_component_applied_directly_because_main_is_integration_only": true,
		"renderer": RenderingServer.get_current_rendering_method(),
		"device": RenderingServer.get_video_adapter_name(),
		"camera_authority": Composition.descriptor(),
		"captures": records,
		"reference_pixels_sha256": "3c424b0df53c1c6de49018278779a4ef1ced58562e5b9dbb54fe276d13aa2ddb",
		"source_bound": true,
		"native_frames_are_not_physical_fps_evidence": true,
		"task_approved": false
	}
	var file := FileAccess.open(output.path_join("capture.json"), FileAccess.WRITE)
	file.store_string(JSON.stringify(report, "\t"))
	file.close()
	game.outpost_audio.stop_all()
	await create_timer(0.35).timeout
	game.free()
	await process_frame
	quit()
