extends "res://tests/capture_task02.gd"
# Reuses the actual scene/sampling helpers; these are disclosed QA cameras.
func run():
	DirAccess.make_dir_recursive_absolute(output)
	game=Main.new();game.qa_mode=true;game.render_review=not native
	game.capture_directory=output;game.capture_frames=100
	game.size=Vector2(3840,2160) if native else Vector2(1280,720)
	root.add_child(game);game.set_process(false);game.set_physics_process(false)
	normal_at(Vector2(-6.5,-9.0));await snap("long-lake-gameplay-west")
	normal_at(Vector2(0,-9.0));await snap("long-lake-gameplay-centre")
	normal_at(Vector2(8.0,-9.0));await snap("long-lake-gameplay-east")
	focus_at(Vector2(0,-10.8),Vector3(0,25,24),22.0);await snap("lake-entire-east-west")
	focus_at(Vector2(0,-13.85),Vector3(0,32,.01),20.0);await snap("lake-top-down-extent")
	focus_at(Vector2(-13.6,-13.5),Vector3(-5,12,13),8.0);await snap("lake-west-bank")
	focus_at(Vector2(13.6,-13.5),Vector3(5,12,13),8.0);await snap("lake-east-bank")
	focus_at(Vector2(0,-13.85),Vector3(0,13,-14),18.0);await snap("lake-rear-shore")
	focus_at(Vector2(0,-10.8),Vector3(0,25,24),22.0)
	# Match the same view under recorded clear/night/weather states.
	for setting in [["day",0.0],["dusk",400.0],["night",930.0],["dawn",990.0],["blizzard-night",630.0],["day-return",0.0]]:
		game.sim.climate.seconds=float(setting[1]);game.outpost_view.sync(game.sim,.1,false)
		await snap("lake-condition-"+str(setting[0]))
		var weather: Dictionary=game.sim.climate.weather()
		records[-1]["hour"]=game.sim.climate.hour()
		records[-1]["weather"]=weather
		records[-1]["daylight"]=game.sim.climate.daylight()
	var report={"task":"T02-lake-correction","renderer":RenderingServer.get_current_rendering_method(),"device":RenderingServer.get_video_adapter_name(),"captures":records,"forest":game.reference_forest_evidence,"outpost":game.outpost_view.evidence(game.sim),"east_west_is_world_x":true,"playable_extent_x":[-14.2,14.2],"lake_extent_x":[-15.2,15.2],"disclosed_qa_cameras":true,"native_frames_are_not_physical_fps_evidence":true,"task_approved":false}
	var f=FileAccess.open(output.path_join("capture.json"),FileAccess.WRITE);f.store_string(JSON.stringify(report,"\t"));f.close()
	game.outpost_audio.stop_all();await create_timer(.35).timeout;game.free();await process_frame;quit()
