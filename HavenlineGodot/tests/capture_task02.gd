extends SceneTree
# Actual unchanged runtime scene with disclosed QA viewpoints. No APK or FPS claim.
const Main = preload("res://scripts/main.gd")
const Surface = preload("res://scripts/outpost_surface.gd")
var output := "user://task02"
var native := false
var game
var records: Array=[]
func _initialize():
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--out="): output=arg.trim_prefix("--out=")
		if arg=="--native-4k": native=true
	call_deferred("run")
func snap(name: String):
	await process_frame
	await RenderingServer.frame_post_draw
	await process_frame
	await RenderingServer.frame_post_draw
	var image: Image=game.scene_view.get_texture().get_image()
	image.save_png(output.path_join(name+".png"))
	records.append({"name":name,"size":[image.get_width(),image.get_height()],"render_scale":game.scene_view.scaling_3d_scale,"camera_position":[game.camera.position.x,game.camera.position.y,game.camera.position.z],"camera_basis":str(game.camera.basis),"camera_size":game.camera.size,"player":[game.sim.position.x,game.sim.position.y],"simulation_seconds":game.sim.climate.seconds,"draw_calls":game.scene_view.get_render_info(Viewport.RENDER_INFO_TYPE_VISIBLE,Viewport.RENDER_INFO_DRAW_CALLS_IN_FRAME),"submitted_primitives":game.scene_view.get_render_info(Viewport.RENDER_INFO_TYPE_VISIBLE,Viewport.RENDER_INFO_PRIMITIVES_IN_FRAME)})
func focus_at(p: Vector2, offset: Vector3, zoom: float):
	game.camera.size=zoom
	var target:=Vector3(p.x,Surface.height_at(p),p.y)
	game.camera.position=target+offset
	game.camera.look_at(target)
	game.update_foreground_visibility(game.xyz(game.sim.position)+Vector3(0,.95,0),.1)
func hide_nonterrain_diagnostic():
	for node in game.world.find_children("*","GeometryInstance3D",true,false):
		if node!=game.outpost_view.terrain and node!=game.outpost_view.lake:node.visible=false
func normal_at(p: Vector2):
	game.sim.position=Surface.land_position(p)
	game.capture_frames=0;game._process(.001);game.capture_frames=100
func run():
	DirAccess.make_dir_recursive_absolute(output)
	game=Main.new();game.qa_mode=true;game.render_review=not native
	game.capture_directory=output;game.capture_frames=100
	game.size=Vector2(3840,2160) if native else Vector2(1280,720)
	root.add_child(game);game.set_process(false);game.set_physics_process(false)
	normal_at(Vector2(0,6.2));await snap("workfloor-gameplay")
	normal_at(Vector2(-6.5,-9.0));await snap("lakeshore-gameplay")
	if native:
		focus_at(Vector2(-3,-4),Vector3(22,36,31),25.0);await snap("native-overview")
		focus_at(Vector2(-7.9,-13.7),Vector3(0,16,13),10.0);await snap("native-shore-detail")
		focus_at(Vector2(9.7,4),Vector3(7,9,12),7.0);await snap("native-snow-join")
		focus_at(Vector2(0,.3),Vector3(0,36,.01),21.0);await snap("native-workfloor-overhead")
	else:
		focus_at(Vector2(-3,-4),Vector3(22,36,31),25.0);await snap("terrain-overview")
		focus_at(Vector2(0,.3),Vector3(0,36,.01),21.0);await snap("workfloor-overhead")
		focus_at(Vector2(-7.9,-13.7),Vector3(0,16,13),10.0);await snap("lakeshore-detail")
		focus_at(Vector2(-7.9,-13.7),Vector3(-13,16,-13),10.0);await snap("lakeshore-rear")
		focus_at(Vector2(9.7,4),Vector3(7,9,12),7.0);await snap("snow-workfloor-join")
		normal_at(Vector2(12.4,0));await snap("approved-forest-contact")
		focus_at(Vector2(-2.5,-7),Vector3(0,17,12),9.0);await snap("bay-connection")
		focus_at(Vector2(-7.9,-13.5),Vector3(0,16,13),9.0)
		for i in range(6):
			game.sim.climate.seconds+=.4;game.outpost_view.sync(game.sim,.4,false)
			await snap("water-motion-%02d"%i)
		var ground_route: Array[Vector2]=[Vector2(0,6.2),Vector2(2.2,3),Vector2(2.2,-2.2),Vector2(-2.2,-2.2),Vector2(-2.2,-6.8),Vector2(-2.2,-9),Vector2(-4.5,-9),Vector2(-6.5,-9)]
		for i in range(ground_route.size()):
			normal_at(ground_route[i]);await snap("route-camera-%02d"%i)
		game.sim.climate.seconds=630.0;game.outpost_view.sync(game.sim,.1,false)
		normal_at(Vector2(-6.5,-9));await snap("lakeshore-night")
	# Supplementary terrain-only diagnostics make bank thickness and snow
	# shaping visible without roofs/trees concealing the ground. Normal gameplay
	# frames above are retained; this is NOT the shipping visibility state.
	game.sim.climate.seconds=0.0;game.outpost_view.sync(game.sim,0.0,false)
	focus_at(Vector2(9.5,3.0),Vector3(4,3,6),5.0);hide_nonterrain_diagnostic();await snap("terrain-only-floor-profile")
	records[-1]["terrain_only_diagnostic"]=true
	focus_at(Vector2(-7.6,-12.3),Vector3(0,3.5,8),7.2);hide_nonterrain_diagnostic();await snap("terrain-only-bank-profile")
	records[-1]["terrain_only_diagnostic"]=true
	var report={"task":"T02","renderer":RenderingServer.get_current_rendering_method(),"device":RenderingServer.get_video_adapter_name(),"captures":records,"forest":game.reference_forest_evidence,"outpost":game.outpost_view.evidence(game.sim),"camera_views_are_disclosed_qa_states":true,"motion_is_sampled_not_fps_evidence":true,"physical_phone_tablet_4k60_verified":false,"task_approved":false}
	var f=FileAccess.open(output.path_join("capture.json"),FileAccess.WRITE);f.store_string(JSON.stringify(report,"\t"));f.close()
	game.outpost_audio.stop_all();await create_timer(.35).timeout;game.free();await process_frame;quit()
