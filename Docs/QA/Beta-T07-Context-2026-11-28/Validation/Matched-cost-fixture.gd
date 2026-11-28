extends "res://tests/qa_t06_companion.gd"

func run() -> void:
	if not Save.Profile.new().configure(OS.get_cmdline_user_args()):
		quit(2)
		return
	game = load("res://field_opening.tscn").instantiate()
	root.add_child(game)
	current_scene = game
	for i in 4: await physics_frame
	game.set_physics_process(false)
	worker = game.survivor
	setup_camp()
	game.set_player_character(2)
	var selected := "--cost-c1-companion" in OS.get_cmdline_user_args()
	if selected and not game.set_companion_character(true):
		quit(2)
		return
	for tick_index in 320:
		tick(1. / 60.)
	var durations: Array[int] = []
	var motion_frames := 0
	var static_start := Performance.get_monitor(Performance.MEMORY_STATIC)
	for tick_index in 2640:
		var before := Time.get_ticks_usec()
		tick(1. / 60.)
		durations.append(Time.get_ticks_usec() - before)
		motion_frames += int(worker.actor.mode in ["chop", "mine"])
		if tick_index % 8 == 0: await process_frame
	durations.sort()
	print(JSON.stringify({"worker": "Character 1" if selected else "Forester", "samples": durations.size(), "paid_station_phase_frames": motion_frames, "median_us": durations[durations.size()/2], "p95_us": durations[floori(.95*(durations.size()-1))], "p99_us": durations[floori(.99*(durations.size()-1))], "static_start": static_start, "static_end": Performance.get_monitor(Performance.MEMORY_STATIC), "worker_actor_nodes": worker.actor.get_child_count(), "paid_camp": game.camp_active, "valid_ledger": not game.persist_blocked}))
	await Session.drain_field_audio(self,game)
	game.queue_free()
	await process_frame
	quit()

func tick(dt: float) -> void:
	if not "context" in game: game._step_receivers()
	super.tick(dt)
