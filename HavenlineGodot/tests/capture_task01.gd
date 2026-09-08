extends SceneTree
# Actual Mobile-renderer diagnostics. No game, critic or FPS approval.
const Main = preload("res://scripts/main.gd")
var out := "user://task01-capture"
var game
func _initialize():
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--out="):out=a.trim_prefix("--out=")
	call_deferred("run")
func save_frame(name: String):
	await process_frame
	await RenderingServer.frame_post_draw
	game.scene_view.get_texture().get_image().save_png(out.path_join(name+".png"))
func run():
	DirAccess.make_dir_recursive_absolute(out)
	game=Main.new();game.qa_mode=true;game.render_review=true;game.capture_frames=100
	game.capture_directory=out;game.size=Vector2(1280,720)
	root.add_child(game)
	game.set_process(false);game.set_physics_process(false)
	# Use the normal initial camera positioning, not an interpolated origin pose.
	game.capture_frames=0;game._process(1.0/60.0);game.capture_frames=100
	await save_frame("gameplay-integration")
	var gameplay_focus: Vector3=game.xyz(game.sim.position)+Vector3(0,.95,-3.6)
	for frame in range(12):
		var theta:=TAU*frame/12.0
		var offset:=Vector3(sin(theta)*8.6,6.8,cos(theta)*8.6)
		game.camera.position=gameplay_focus+offset+offset.normalized()*18.0
		game.camera.look_at(gameplay_focus)
		game.update_foreground_visibility(game.xyz(game.sim.position)+Vector3(0,.95,0),.1)
		await save_frame("integration-%02d"%frame)
	# Reachable forest-edge position: explicitly disclosed QA state, not new gameplay.
	game.sim.position=Vector2(12.4,0)
	game.capture_frames=0;game._process(1.0/60.0);game.capture_frames=100
	await save_frame("forest-boundary-gameplay")
	var allowed: Array = [game.camera,game.sun]
	for child in game.world.get_children():
		if child is WorldEnvironment:allowed.append(child)
		if child is VisualInstance3D or child is Node3D:
			if not child in allowed:child.visible=false
	var display_root:=Node3D.new();game.world.add_child(display_root)
	var variants: Array=[]
	for i in range(1,4):
		var t=game.model("world/pine_%d"%i,display_root,Vector3((i-2)*2.8,0,0))
		variants.append(t)
	var target:=Vector3(0,1.6,0)
	game.camera.size=4.6
	for index in range(3):
		for t in variants:t.visible=false
		variants[index].visible=true
		target=variants[index].position+Vector3(0,1.6,0)
		for pair in [["front",Vector3(0,3.2,10)],["rear",Vector3(0,3.2,-10)],["side",Vector3(10,3.2,0)],["three-quarter",Vector3(8,4,10)]]:
			game.camera.position=target+pair[1]
			game.camera.look_at(target)
			await save_frame("v%02d-%s"%[index+1,pair[0]])
	for t in variants:t.visible=false
	variants[0].visible=true
	target=variants[0].position+Vector3(0,1.6,0)
	for frame in range(24):
		var theta:=TAU*frame/24.0
		game.camera.position=target+Vector3(sin(theta)*11,3.2,cos(theta)*11)
		game.camera.look_at(target)
		await save_frame("orbit-%02d"%frame)
	var report={"task":"T01","renderer":RenderingServer.get_current_rendering_method(),"device":RenderingServer.get_video_adapter_name(),"internal_size":[game.scene_view.size.x,game.scene_view.size.y],"scale":game.scene_view.scaling_3d_scale,"asset_views_isolated":true,"camera_sequence_frames":24,"integration_camera_frames":12,"forest_edge_fixture_position":[12.4,0],"scene_script_sha256":FileAccess.get_file_as_string("res://scripts/main.gd").sha256_text(),"forest":game.reference_forest_evidence,"physical_4k60_verified":false,"visual_approval":false}
	var file=FileAccess.open(out.path_join("capture.json"),FileAccess.WRITE);file.store_string(JSON.stringify(report,"\t"));file.close()
	game.outpost_audio.stop_all();await create_timer(.35).timeout;game.free();await process_frame
	quit()
