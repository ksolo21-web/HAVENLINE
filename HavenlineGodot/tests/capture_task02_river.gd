extends "res://tests/capture_task02.gd"
const River=preload("res://scripts/river_geometry.gd")

func bank_point(x:float,north:bool,extra:=0.85)->Vector2:
	var q:=River.query(River.center_at_x(x));var side:=1.0 if north else -1.0
	return Vector2(q.center)+Vector2(q.north_normal)*(float(q.half_width)+River.WET_EDGE+River.BANK_RUN+River.SNOW_SHOULDER+extra)*side

func snap_named(name:String):
	await snap(name)
	records[-1]["river_layout_version"]=River.LAYOUT_VERSION

func run():
	DirAccess.make_dir_recursive_absolute(output)
	game=Main.new();game.qa_mode=true;game.render_review=not native
	game.capture_directory=output;game.capture_frames=100
	game.size=Vector2(3840,2160) if native else Vector2(1280,720)
	root.add_child(game);game.set_process(false);game.set_physics_process(false)
	# Full authored terrain proves the river already exists in land that is not
	# yet unlocked. These are disclosed QA cameras, not shipping camera settings.
	focus_at(Vector2(0,-7.8),Vector3(0,80,.01),70.0);await snap_named("river-plan-topdown")
	focus_at(Vector2(0,-7.8),Vector3(42,62,54),61.0);await snap_named("river-plan-oblique")
	focus_at(Vector2(0,-1.0),Vector3(0,45,.01),38.0);await snap_named("river-current-topdown")
	focus_at(Vector2(0,-2.0),Vector3(25,38,35),34.0);await snap_named("river-current-oblique")
	focus_at(River.center_at_x(-30.0),Vector3(0,14,17),11.0);await snap_named("river-west-entry")
	focus_at(River.center_at_x(30.0),Vector3(0,14,17),11.0);await snap_named("river-east-exit")
	var bend_x=[-24.0,-17.0,-10.0,-3.0,4.0,11.0,19.0,25.0]
	for i in range(bend_x.size()):
		focus_at(River.center_at_x(float(bend_x[i])),Vector3(0,14,17),10.5)
		await snap_named("river-bend-%02d"%i)
	if native:
		# 4K subset covers whole layout, both terrain edges, representative bends,
		# current playable relationship and close bank contact.
		focus_at(Vector2(0,-7.8),Vector3(0,80,.01),70.0);await snap_named("native-river-plan")
		focus_at(Vector2(0,-1.0),Vector3(0,45,.01),38.0);await snap_named("native-current-map")
		focus_at(River.center_at_x(-30.0),Vector3(0,14,17),11.0);await snap_named("native-west-entry")
		focus_at(River.center_at_x(30.0),Vector3(0,14,17),11.0);await snap_named("native-east-exit")
		for x in [-10.0,-3.0,4.0,11.0]:
			focus_at(River.center_at_x(x),Vector3(0,14,17),10.5);await snap_named("native-bend-%s"%str(int(x)).replace("-","m"))
		focus_at(bank_point(0,true,.25),Vector3(0,6,9),5.8);await snap_named("native-north-bank-contact")
		focus_at(bank_point(0,false,.25),Vector3(0,6,-9),5.8);await snap_named("native-south-bank-contact")
		focus_at(Vector2(0,2.8),Vector3(0,32,.01),24.0);await snap_named("native-camp-river-overhead")
	else:
		# Actual normal-gameplay cameras on both banks inside today's movement area.
		for item in [[-10.0,true,"north-west"],[0.0,true,"north-centre"],[10.0,true,"north-east"],[-10.0,false,"south-west"],[0.0,false,"south-centre"],[10.0,false,"south-east"]]:
			normal_at(bank_point(float(item[0]),bool(item[1])));await snap_named("river-gameplay-"+str(item[2]))
		focus_at(Vector2(0,2.8),Vector3(0,32,.01),24.0);await snap_named("camp-river-overhead")
		focus_at(Vector2(0,1.5),Vector3(18,24,27),23.0);await snap_named("camp-river-oblique")
		# Reserved crossings are empty terrain corridors in Task 2, not bridges.
		for i in range(River.CROSSING_X.size()):
			var x:=float(River.CROSSING_X[i]);focus_at(River.center_at_x(x),Vector3(0,19,.01),12.0)
			await snap_named("crossing-reserve-%02d"%i)
		focus_at(bank_point(0,true,.20),Vector3(0,6,9),5.8);await snap_named("north-bank-contact")
		focus_at(bank_point(0,false,.20),Vector3(0,6,-9),5.8);await snap_named("south-bank-contact")
		# Ordered simulation-time samples verify current continuity without claiming FPS.
		focus_at(River.center_at_x(0),Vector3(0,10,12),8.0)
		for i in range(6):
			game.sim.climate.seconds+=.45;game.outpost_view.sync(game.sim,.45,false);await snap_named("river-flow-%02d"%i)
		# Same camera across environmental conditions catches bank/material regressions.
		var held:=0
		for animation in game.world.find_children("*","AnimationPlayer",true,false):animation.pause();held+=1
		for setting in [["day",0.0],["dusk",400.0],["night",930.0],["dawn",990.0],["blizzard-night",630.0],["day-return",0.0]]:
			game.sim.climate.seconds=float(setting[1]);game.outpost_view.sync(game.sim,.1,false);await snap_named("river-condition-"+str(setting[0]))
			records[-1]["held_unrelated_animation_players"]=held
			records[-1]["hour"]=game.sim.climate.hour();records[-1]["weather"]=game.sim.climate.weather()
	var report={"task":"T02-river-v1-mapspan","renderer":RenderingServer.get_current_rendering_method(),"device":RenderingServer.get_video_adapter_name(),"captures":records,"forest":game.reference_forest_evidence,"outpost":game.outpost_view.evidence(game.sim),"locked_anchors":River.ANCHORS,"widths":River.WIDTHS,"current_movement_bounds":[-14.2,14.2,-16.2,16.2],"full_terrain_bounds":[-31.0,31.0,-31.0,31.0],"disclosed_qa_cameras":true,"motion_is_sampled_not_fps_evidence":true,"physical_phone_tablet_4k60_verified":false,"task_approved":false}
	var f=FileAccess.open(output.path_join("capture.json"),FileAccess.WRITE);f.store_string(JSON.stringify(report,"\t"));f.close()
	game.outpost_audio.stop_all();await create_timer(.35).timeout;game.free();await process_frame;quit()
