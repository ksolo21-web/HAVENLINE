extends SceneTree
# Actual Mobile-rendered visibility/depletion fixtures, not marketing frames.
const Main = preload("res://scripts/main.gd")
const Forest = preload("res://scripts/reference_forest.gd")
const Scenery = preload("res://scripts/scenery_batch.gd")
var out := "user://task01-clearance"
var game
var native_4k := false
func _initialize():
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--out="):out=arg.trim_prefix("--out=")
		if arg=="--native-4k":native_4k=true
	call_deferred("run")
func image(name: String):
	await process_frame;await RenderingServer.frame_post_draw
	game.scene_view.get_texture().get_image().save_png(out.path_join(name+".png"))
func run():
	DirAccess.make_dir_recursive_absolute(out)
	game=Main.new();game.qa_mode=true;game.render_review=not native_4k;game.capture_frames=100
	game.capture_directory=out;game.size=Vector2(3840,2160) if native_4k else Vector2(1280,720);root.add_child(game)
	game.set_process(false);game.set_physics_process(false)
	game.capture_frames=0;game._process(.001);game.capture_frames=100
	var focus: Vector3=game.xyz(game.sim.position)+Vector3(0,.95,0)
	game.camera.size=6.0;game.camera.position=focus+Vector3(0,12,28);game.camera.look_at(focus)
	var clearance_focus_screen:Vector2=game.camera.unproject_position(focus)
	var transforms: Array[Transform3D]=[Transform3D(Basis.IDENTITY,game.xyz(game.sim.position+Vector2(0,2.4)))]
	var fixture=Scenery.instances(game.merged_cache["world/pine_1"],transforms,game.world)
	fixture.name="T01ClearanceFixture"
	Forest.set_player_clearance(game,focus,false)
	fixture.visible=false;await image("clearance-baseline")
	fixture.visible=true;await image("clearance-disabled")
	Forest.set_player_clearance(game,focus,true);await image("clearance-enabled")
	fixture.queue_free();await process_frame
	var resource=game.sim.resources[0]
	var tree: MeshInstance3D=game.resource_visuals[resource.id]
	var old_position: Vector3=tree.position;var old_units:int=resource.units
	tree.position=transforms[0].origin
	Forest.set_player_clearance(game,focus,false)
	for step in range(6):
		var index=game.scenery_instances.find(tree)
		game.scenery_cutaway[index]=float(step)/5.0
		tree.set_instance_shader_parameter("cutaway",float(step)/5.0)
		await image("resource-clearance-%02d"%step)
	resource.units=0;game.update_foreground_visibility(focus,.1)
	await image("resource-depleted")
	var depleted_hidden:=not tree.visible
	# Restore the real resource at its original location. The diagnostic moves
	# the lead adjacent and observes the actual visibility controller. It never
	# forces the restored mesh visible or replaces the game with an image.
	resource.units=old_units;tree.position=old_position
	var adjacent:=Vector2(old_position.x+3.0,old_position.z-1.0)
	if adjacent.x>game.sim.contract.world.boundX:adjacent.x=old_position.x-3.0
	game.sim.position=adjacent;game.capture_frames=0;game._process(.001);game.capture_frames=100
	var restored_focus: Vector3=game.xyz(game.sim.position)+Vector3(0,.95,0)
	var target:=old_position+Vector3(0,1.55,0)
	game.camera.size=4.9;game.camera.position=target+Vector3(6,4,10);game.camera.look_at(target)
	for frame in range(6):
		game.update_foreground_visibility(restored_focus,.1)
		await process_frame;await RenderingServer.frame_post_draw
	var restored_visible:=tree.visible
	var restored_cutaway:float=tree.get_instance_shader_parameter("cutaway")
	await image("resource-restored")
	var report={"task":"T01","renderer":RenderingServer.get_current_rendering_method(),"device":RenderingServer.get_video_adapter_name(),"fixture_disclosed":true,"fixture_type":"actual sightline tree plus real resource depletion/restoration; restored view moves camera and lead adjacent to original resource","focus_screen":[clearance_focus_screen.x,clearance_focus_screen.y],"image_size":[game.scene_view.size.x,game.scene_view.size.y],"render_scale":game.scene_view.scaling_3d_scale,"depleted_tree_hidden":depleted_hidden,"original_units_restored":resource.units==old_units,"restored_tree_visible":restored_visible,"restored_cutaway":restored_cutaway,"restored_original_position":[tree.position.x,tree.position.y,tree.position.z],"restored_player_fixture":[adjacent.x,adjacent.y],"task_approved":false,"physical_4k60_verified":false}
	var f=FileAccess.open(out.path_join("clearance.json"),FileAccess.WRITE);f.store_string(JSON.stringify(report,"\t"));f.close()
	game.outpost_audio.stop_all();await create_timer(.35).timeout;game.free();await process_frame;quit()
