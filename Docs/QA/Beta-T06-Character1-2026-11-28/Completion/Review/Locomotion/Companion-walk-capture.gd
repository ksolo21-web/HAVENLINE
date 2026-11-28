extends "res://tests/qa_worker_jobs.gd"

const STEP := 1. / 120.
const PANEL := Vector2i(256, 192)
const OFFSETS := [Vector3(0., .14, 1.), Vector3(0., .14, -1.), Vector3(1., .14, 0.), Vector3(-1., .14, 0.)]
var directory := OS.get_environment("T06_COMPANION_LEGS")
var metadata: Array[Dictionary] = []
var cameras: Array[Camera3D] = []
var views: Array[SubViewport] = []
var display: Node3D
var runner: Node3D
var local_frame := 0
var studio := World3D.new()

func add_views() -> void:
	for angle in OFFSETS:
		var view := SubViewport.new()
		view.size = PANEL
		view.world_3d = studio
		view.render_target_update_mode = SubViewport.UPDATE_ALWAYS
		root.add_child(view)
		var cam := Camera3D.new()
		cam.projection = Camera3D.PROJECTION_ORTHOGONAL
		cam.size = 1.27
		view.add_child(cam)
		cam.make_current()
		cameras.append(cam)
		views.append(view)

func walk(at: Vector3) -> bool:
	display.start_frame()
	var gait = runner.forester_gait
	gait.pivot_frame = false
	var arrived: bool = worker._walk(at, STEP)
	if runner.mode == "travel" and not gait.pivot_frame:
		gait.settle_contact(STEP, runner)
	else:
		gait.previous_points.clear()
		gait.marker.fill(-1)
		gait.correction.fill(Vector3.ZERO)
	display.advance(STEP, "capture_walkway", false)
	return arrived

func capture(label: String, pose_second: float, heading: float) -> void:
	var focus := runner.global_position + Vector3.UP * .49
	for side in cameras.size():
		var cam := cameras[side]
		cam.global_position = focus + Basis(Vector3.UP, heading) * Vector3(OFFSETS[side]) * 2.45
		cam.look_at(focus, Vector3.UP)
		cam.force_update_transform()
		RenderingServer.camera_set_transform(cam.get_camera_rid(), cam.global_transform)
	display.motion.rig.force_update_all_bone_transforms()
	await process_frame
	RenderingServer.force_draw(false)
	var panel := Image.create(PANEL.x * 2, PANEL.y * 2, false, Image.FORMAT_RGB8)
	for side in views.size():
		var frame := views[side].get_texture().get_image()
		frame.convert(Image.FORMAT_RGB8)
		panel.blit_rect(frame, Rect2i(Vector2i.ZERO, PANEL), Vector2i((side % 2) * PANEL.x, (side >> 1) * PANEL.y))
	var filename := "legs-%04d.jpg" % local_frame
	check(panel.save_jpg(directory.path_join(filename), .83) == OK, "rendered " + filename)
	var steering = runner.forester_gait
	var sole: Vector2 = display.gait._heights()
	var left: Transform3D = display.gait._boot_world(0)
	var right: Transform3D = display.gait._boot_world(1)
	metadata.append({"file":filename,"sequence":label,"second":pose_second,"yaw":runner.rotation.y,"actor":str(runner.global_position),"pace":display.speed,
		"locomotion":display.locomotion.current,"mode":runner.mode,"holding_turn":steering.pivot_frame,"pivot_step":steering.pivot_elapsed,
		"sole_height":[sole.x,sole.y],"boot_left":str(left),"boot_right":str(right)})
	local_frame += 1

func choose_lane() -> Vector3:
	for x in range(-15, 33, 3):
		for z in range(-36, -14, 3):
			var start := Vector3(x, 0, z)
			if not worker._travel_clear(start, start + Vector3(0,0,5), .36): continue
			if not worker._travel_clear(start, start + Vector3(4,0,0), .36): continue
			if not worker._travel_clear(start, start + Vector3(-4,0,0), .36): continue
			return start
	return Vector3.INF

func run() -> void:
	if not Save.Profile.new().configure(OS.get_cmdline_user_args()):
		quit(2)
		return
	game = load("res://field_opening.tscn").instantiate()
	root.add_child(game)
	current_scene = game
	await physics_frame
	game.set_physics_process(false)
	worker = game.survivor
	setup_camp()
	check(game.set_player_character(2) and game.set_companion_character(true),"paid Character 1 companion selected")
	runner = worker.actor
	display = worker.core_motion
	var lane := choose_lane()
	check(lane.is_finite(),"clear outdoor test space located via shipping route collision")
	if not lane.is_finite():
		quit(3)
		return
	var environment := Environment.new()
	environment.background_mode = Environment.BG_COLOR
	environment.background_color = Color("#aabecf")
	environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	environment.ambient_light_color = Color("#dde9f6")
	environment.ambient_light_energy = .68
	studio.environment = environment
	add_views()
	runner.reparent(views[0], true)
	var snow := MeshInstance3D.new()
	var plane := PlaneMesh.new()
	plane.size = Vector2(24.,24.)
	snow.mesh = plane
	var material := StandardMaterial3D.new()
	material.albedo_color = Color("#cfdce5")
	material.roughness = .92
	snow.material_override = material
	views[0].add_child(snow)
	snow.global_position = lane - Vector3.UP*.003
	var light := DirectionalLight3D.new()
	light.rotation_degrees = Vector3(-45., 28., 0.)
	light.light_energy = .62
	views[0].add_child(light)
	runner.global_position = lane
	runner.rotation.y = 0.
	display.previous_feet = Vector3.INF
	var start := lane + Vector3(0,0,5)
	walk(lane)
	var saw_run := false
	var arrived := false
	var run_frames := 0
	for n in 310:
		arrived = walk(start)
		saw_run = saw_run or display.locomotion.current == "run" and display.speed > 2.5
		if n % 6 == 0:
			await capture("launch-run-brake", n * STEP, 0.)
			run_frames += 1
		if arrived: break
	for n in 36:
		walk(start)
		if n % 6 == 0:
			await capture("settle", n * STEP, 0.)
	check(saw_run and arrived and run_frames >= 28 and display.speed < .06, "run starts, reaches sprint cadence, brakes and settles on its own route")
	for sign_ in [-1., 1.]:
		runner.global_position = lane
		runner.rotation.y = 0.
		display.previous_feet = Vector3.INF
		worker.travel_speed = 0.
		walk(lane)
		for n in 24: walk(lane)
		var port := lane + Vector3(3. * sign_, 0, 0)
		var frames := 0
		var pivoted := false
		for n in 85:
			walk(port)
			pivoted = pivoted or runner.forester_gait.pivot_frame
			if n % 5 == 0:
				await capture("left-90" if sign_ < 0. else "right-90", n * STEP, 0.)
				frames += 1
		check(pivoted and frames >= 15 and sign_ * rad_to_deg(runner.rotation.y) >= 85., "each lateral redirect shows the full planted turn and rollout")
	var record := FileAccess.open(directory.path_join("Companion-lower-legs.json"), FileAccess.WRITE)
	record.store_string(JSON.stringify({"checks":checks,"failures":errors,"samples":metadata,"source":{
		"character":FileAccess.get_sha256("res://assets/characters/Character1Fresh.glb"),
		"companion":FileAccess.get_sha256("res://field_companion_motion.gd"),
		"survivor":FileAccess.get_sha256("res://field_survivor.gd"),"gait":FileAccess.get_sha256("res://gait_motor.gd"),
		"motion":FileAccess.get_sha256("res://field_character_motion.gd")},"views":["front","rear","left","right"],
		"pixels":[PANEL.x*2,PANEL.y*2],"renderer":RenderingServer.get_video_adapter_name(),
		"diagnostic_camera": "native four-view diagnostic framing of the unaltered work-path simulation",
		"frame_seconds":{"launch-run-brake":.05,"settle":.05,"left-90":5.*STEP,"right-90":5.*STEP}}, "  "))
	record.close()
	await Session.drain_field_audio(self, game)
	runner.queue_free()
	game.queue_free()
	await process_frame
	quit(int(not errors.is_empty()))
