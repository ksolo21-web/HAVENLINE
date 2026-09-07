extends SceneTree
const Main = preload("res://scripts/main.gd")
const Record = preload("res://scripts/performance_record.gd")
const Scenery = preload("res://scripts/scenery_batch.gd")
const Surface = preload("res://scripts/outpost_surface.gd")
var checks: Array=[]
var failures: Array=[]
func check(label:String, passed:bool):
	checks.append({"name":label,"passed":passed})
	if not passed: failures.append(label)
func _initialize(): call_deferred("run")
func run():
	for size in [Vector2i(3840,2160),Vector2i(4320,2160),Vector2i(3200,2700),Vector2i(4320,1920)]:
		var record=Record.new()
		record.resolution(size)
		var expected:bool=size.x>=3840 and size.y>=2160
		check("Both native dimensions are required: %s"%str(size),record.report().minimum_dimensions_at_all_recorded_resolutions==expected)
	var record=Record.new()
	check("No resolution evidence is not native proof",not record.report().minimum_dimensions_at_all_recorded_resolutions)
	record.resolution(Vector2i(3840,2160));record.resolution(Vector2i(1920,1080));record.resolution(Vector2i(3840,2160))
	check("An intervening resolution drop invalidates the whole measured session",not record.report().minimum_dimensions_at_all_recorded_resolutions)
	for i in range(120): record.sample(1000.0/60.0)
	check("Synthetic perfect intervals never certify hardware",not record.report().sustained_4k60_certified and not record.report().physical_device_validated and not record.report().thermal_validated)
	check("Thirty-minute 60 Hz measurements fit without losing early samples",Record.CAPACITY>=108000)
	for name in ["pine_1","shelter","furnace"]:
		var packed:PackedScene=load("res://assets/environment_v2/%s.glb"%name)
		var original=packed.instantiate()
		var nodes:Array=[]
		Scenery.collect_meshes(original,Transform3D.IDENTITY,nodes)
		check("Authored kit has one identity-transform mesh: "+name,nodes.size()==1 and nodes[0].transform.is_equal_approx(Transform3D.IDENTITY))
		var source:ArrayMesh=nodes[0].node.mesh
		var retained:ArrayMesh=Scenery.compile(packed)
		check("Static optimization does not mutate the source resource: "+name,source!=retained)
		check("Imported LOD surface data survives compilation: "+name,source.get("_surfaces")==retained.get("_surfaces"))
		check("Imported shadow mesh is retained: "+name,source.shadow_mesh!=null and source.shadow_mesh==retained.shadow_mesh)
		original.free()
	var finite=true
	for i in range(80):
		var p=Vector2(sin(i*.47)*24,cos(i*.31)*24)
		if not is_finite(Surface.height_at(p)):finite=false
	check("Sculpted banks have finite shared ground-contact heights",finite)
	check("Mobile shadow filtering matches the reviewed desktop Mobile path",ProjectSettings.get_setting("rendering/lights_and_shadows/directional_shadow/soft_shadow_filter_quality.mobile")==ProjectSettings.get_setting("rendering/lights_and_shadows/directional_shadow/soft_shadow_filter_quality"))
	var game=Main.new()
	game.qa_mode=true;game.render_review=true;game.capture_frames=100
	game.capture_directory="user://render-budget-tests"
	game.size=Vector2(1280,720)
	root.add_child(game)
	game.set_process(false);game.set_physics_process(false)
	game.start_device_benchmark()
	var session=game.device_benchmark
	check("In-game measurements are visible while running",session.running and session.visible and session.stats.text.contains("Warm-up"))
	session._notification(NOTIFICATION_APPLICATION_PAUSED)
	check("App interruption resets the timing origin and is recorded",session.interruptions==1 and session.previous==0)
	session.warmed=31.0;session.previous=Time.get_ticks_usec()-20000
	game.paused=false;session.after_draw()
	check("Rendered samples use actual elapsed intervals",session.samples.count==1 and session.elapsed>=.019)
	check("A review-sized viewport cannot pass native size",not session.native_ok)
	session.finish(false)
	var report=JSON.parse_string(FileAccess.get_file_as_string(session.REPORT_PATH))
	check("Stopped test is saved but not called completed",report!=null and not report.completed_thirty_minutes)
	check("Device observer cannot manufacture performance approval",not report.sustained_4k60_certified and not report.display_presentation_verified and not report.thermal_validated)
	check("Completed/stopped UI shows measurements, not an invented score",session.stats.text.contains("not completed") and session.stop.text=="Close measurements")
	session.queue_free()
	game.outpost_audio.stop_all()
	await create_timer(.35).timeout
	game.free()
	await process_frame
	print(JSON.stringify({"suite":"native_render_budget","passed":failures.is_empty(),"checks":checks,"failures":failures}))
	quit(0 if failures.is_empty() else 1)
