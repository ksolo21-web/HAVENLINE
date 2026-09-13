extends SceneTree
# Reusable deterministic integration-evidence camera harness. QA-only camera and
# climate states; it does not alter shipping camera behavior or runtime scope.
const Main=preload("res://scripts/main.gd")
const Surface=preload("res://scripts/outpost_surface.gd")
var output="user://production-capture"
var focus=Vector2.ZERO
var candidate=""
var task_id=""
var build_id=""
var native=false
var game
var records:Array=[]

func _initialize():
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--out="):output=arg.trim_prefix("--out=")
		elif arg.begins_with("--focus="):
			var parts=arg.trim_prefix("--focus=").split(",")
			assert(parts.size()==2)
			focus=Vector2(float(parts[0]),float(parts[1]))
		elif arg.begins_with("--candidate="):candidate=arg.trim_prefix("--candidate=")
		elif arg.begins_with("--task="):task_id=arg.trim_prefix("--task=")
		elif arg.begins_with("--build-id="):build_id=arg.trim_prefix("--build-id=")
		elif arg=="--native-4k":native=true
	assert(candidate.length()==40 and task_id!="")
	call_deferred("run")

func focus_at(p:Vector2,offset:Vector3,zoom:float):
	var target=Vector3(p.x,Surface.height_at(p),p.y)
	game.camera.size=zoom
	game.camera.position=target+offset
	game.camera.look_at(target)
	game.update_foreground_visibility(game.xyz(game.sim.position)+Vector3(0,.95,0),.1)

func settle_and_snap(name:String,state:String):
	for _i in range(2):
		await process_frame
		await RenderingServer.frame_post_draw
	var image:Image=game.scene_view.get_texture().get_image()
	var path=output.path_join(name+".png")
	image.save_png(path)
	records.append({
		"name":name,"scene_state":state,
		"camera_position":[game.camera.position.x,game.camera.position.y,game.camera.position.z],
		"camera_basis":str(game.camera.basis),"camera_size":game.camera.size,
		"renderer":RenderingServer.get_current_rendering_method(),
		"resolution":[image.get_width(),image.get_height()],
		"render_scale":game.scene_view.scaling_3d_scale,
		"simulation_seconds":game.sim.climate.seconds,
		"draw_calls":game.scene_view.get_render_info(Viewport.RENDER_INFO_TYPE_VISIBLE,Viewport.RENDER_INFO_DRAW_CALLS_IN_FRAME),
		"submitted_primitives":game.scene_view.get_render_info(Viewport.RENDER_INFO_TYPE_VISIBLE,Viewport.RENDER_INFO_PRIMITIVES_IN_FRAME)
	})

func run():
	DirAccess.make_dir_recursive_absolute(output)
	game=Main.new();game.qa_mode=true;game.render_review=not native
	game.capture_directory=output;game.capture_frames=100
	game.size=Vector2(3840,2160) if native else Vector2(1280,720)
	root.add_child(game);game.set_process(false);game.set_physics_process(false)
	game.sim.position=Surface.land_position(focus);game._process(.001)

	var views=[
		["front",Vector3(0,8,10),8.0],
		["rear",Vector3(0,8,-10),8.0],
		["left",Vector3(-10,8,0),8.0],
		["right",Vector3(10,8,0),8.0],
		["three-quarter",Vector3(8,10,8),9.0],
		["detail",Vector3(3.2,4.2,4.0),4.5],
		["overhead",Vector3(0,18,.01),10.0]
	]
	for row in views:
		focus_at(focus,row[1],row[2]);await settle_and_snap(row[0],"static-"+row[0])
	game.sim.position=Surface.land_position(focus);game._process(.001)
	await settle_and_snap("gameplay-scale","normal-gameplay-scale")

	focus_at(focus,Vector3(8,10,8),9.0)
	for setting in [["condition-day",0.0],["condition-night",930.0],["condition-blizzard",630.0]]:
		game.sim.climate.seconds=float(setting[1]);game.outpost_view.sync(game.sim,.1,false)
		await settle_and_snap(String(setting[0]),String(setting[0]))

	var report={
		"harness":"production_capture_v1","task_id":task_id,"candidate_commit":candidate,
		"build_id":build_id,"native_4k":native,"focus":[focus.x,focus.y],
		"captures":records,"physical_device_performance_certified":false
	}
	var f=FileAccess.open(output.path_join("capture.json"),FileAccess.WRITE)
	f.store_string(JSON.stringify(report,"\t"));f.close()
	game.outpost_audio.stop_all();await create_timer(.25).timeout
	game.free();await process_frame;quit()
