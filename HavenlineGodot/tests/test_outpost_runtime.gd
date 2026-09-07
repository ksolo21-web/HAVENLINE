extends SceneTree
const Main = preload("res://scripts/main.gd")
const Audio = preload("res://scripts/outpost_audio.gd")
const Surface = preload("res://scripts/outpost_surface.gd")
var checks: Array = []
var failures: Array = []
func check(label: String, passed: bool):
	checks.append({"name":label,"passed":passed})
	if not passed: failures.append(label)
func _initialize():
	call_deferred("run")
func run():
	# Actual application scene, isolated QA state: never read/write a player's save.
	var game = Main.new()
	game.qa_mode=true; game.render_review=true
	game.capture_directory="user://outpost-runtime-tests"
	game.size=Vector2(1280,720)
	root.add_child(game)
	game.set_process(false); game.set_physics_process(false)
	check("Snow highlights reserve real tone-map headroom",is_equal_approx(game.environment.tonemap_white,6.0))
	check("Actual game scene creates all four original crew actors",game.actors.size()==4)
	check("Absent NPC art remains fail-closed",game.population_view.nodes.is_empty() and not game.sim.threats_enabled and not game.sim.rescue_enabled)
	check("Weather terrain and bounded snowfall are instantiated",game.outpost_view.terrain.mesh!=null and game.outpost_view.snow.multimesh.instance_count==640)
	check("Initial thaw boundary matches actual gameplay radius",is_equal_approx(game.outpost_view.current_radius,game.sim.warmth()))
	game.sim.stored.wood=18;game.sim.stored.stone=6;game.sim.update_level()
	game._process(.1)
	check("Real upgrade begins an expanding visual thaw",game.outpost_view.current_radius>4.5 and game.outpost_view.current_radius<8.)
	check("Furnace animation uses the original furnace node",game.furnace.scale.x>1. and game.furnace.scale.x<1.085)
	check("Upgraded light reach follows gameplay warmth",is_equal_approx(game.heat_light.omni_range,9.5))
	check("HUD displays clock weather warmth and health",game.climate_status.text.contains("Day ") and game.climate_status.text.contains("Warmth") and game.climate_status.text.contains("Health"))
	game.toggle_menu()
	var clock: float=game.sim.climate.seconds
	var radius: float=game.outpost_view.current_radius
	game._physics_process(.1);game._process(.1)
	check("Camp menu freezes actual simulation and weather",game.paused and is_equal_approx(game.sim.climate.seconds,clock))
	check("Camp menu freezes thaw animation",is_equal_approx(game.outpost_view.current_radius,radius))
	check("Paused gameplay hides action feedback",not game.action_readout.visible)
	check("Pause suspends both ambient sound streams",game.outpost_audio.wind.stream_paused and game.outpost_audio.fire.stream_paused)
	game.toggle_menu();game._physics_process(.1);game._process(.1)
	check("Returning to camp resumes simulation without time debt",not game.paused and is_equal_approx(game.sim.climate.seconds,clock+.1))
	var start: Vector2=game.sim.position
	var touch:=InputEventScreenTouch.new();touch.index=7;touch.pressed=true;touch.position=Vector2(160,500)
	game._gui_input(touch)
	var drag:=InputEventScreenDrag.new();drag.index=7;drag.position=Vector2(260,500)
	game._gui_input(drag);game._physics_process(.1)
	check("Existing touch movement works with new UI",game.joystick_id==7 and game.sim.position.distance_to(start)>.01)
	game._notification(Node.NOTIFICATION_APPLICATION_PAUSED)
	check("Application pause clears captured touch and opens camp",game.paused and game.joystick_id == -1 and game.menu.visible)
	clock=game.sim.climate.seconds
	game._notification(Node.NOTIFICATION_APPLICATION_RESUMED);game._physics_process(.1)
	check("Application resume awaits deliberate return and cannot move",game.paused and is_equal_approx(game.sim.climate.seconds,clock) and game.joystick_id == -1)
	game.toggle_menu();game._process(.1)
	check("Lead root samples sculpted terrain after movement",is_equal_approx(game.player_rig.position.y,Surface.height_at(game.sim.position)))
	game.outpost_audio.settings_path="user://test-outpost-audio.cfg"
	check("Mute preference saves separately from game progress",game.outpost_audio.set_muted(true)==OK)
	game.outpost_audio.sync(game.sim,false,.1)
	check("Mute pauses ambient playback without pausing the game",game.outpost_audio.wind.stream_paused and not game.paused)
	var sound=Audio.new();sound.settings_path=game.outpost_audio.settings_path
	root.add_child(sound)
	check("A fresh audio instance restores mute preference",sound.muted)
	sound.set_muted(false)
	var events: Array=[]
	for i in range(12):events.append({"type":"deposit"})
	sound.consume(events)
	check("Crowded actions stay within the eight-voice three-event cap",sound.voices.size()==8 and sound.emitted_events==3)
	check("Ambient files have nonempty looping streams",sound.wind.stream.get_length()>10. and sound.fire.stream.get_length()>10. and sound.wind.stream.loop_mode==AudioStreamWAV.LOOP_FORWARD)
	DirAccess.remove_absolute(sound.settings_path)
	sound.stop_all();game.outpost_audio.stop_all()
	# Let the asynchronous audio mixer retire playback handles before exit.
	check("Shutdown detaches all ambience and effect resources",sound.streams.is_empty() and game.outpost_audio.streams.is_empty() and sound.wind.stream == null and game.outpost_audio.fire.stream == null)
	await create_timer(.35).timeout
	sound.free();game.free()
	await process_frame
	await process_frame
	print(JSON.stringify({"suite":"outpost_actual_scene_runtime","passed":failures.is_empty(),"checks":checks,"failures":failures,"physical_android_lifecycle_verified":false}))
	quit(0 if failures.is_empty() else 1)
