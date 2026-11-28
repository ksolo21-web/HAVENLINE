extends "res://tests/qa_worker_jobs.gd"

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
	check(game.set_player_character(2) and game.set_companion_character(true), "paid companion enabled from the opening")
	var reached := false
	for i in 18000:
		tick(1. / 60.)
		if worker.phase == "mining" and worker.bank_hit:
			reached = true
			break
	check(reached, "the first mining contact occurred in live work")
	if reached:
		var bank: Node3D = worker.assigned_bank
		var before: Dictionary = game.inventory.snapshot()
		var old_strikes: int = bank.strikes
		var old_token: int = bank.last_sequence
		check(game.set_companion_character(false), "the original survivor can be restored during mining")
		check(game.set_companion_character(true), "the compact survivor can be re-enabled during the approach")
		check(worker.phase == "mining_approach" and worker.assigned_bank == bank and not worker.route.is_empty(), "the route refits the stance at that bank")
		check(bank.strikes == old_strikes and bank.last_sequence == old_token and game.inventory.snapshot() == before, "switches conserve the hit and ledger")
		for i in 1800:
			tick(1. / 60.)
			if bank.strikes > old_strikes: break
		check(bank.strikes == old_strikes + 1 and bank.last_sequence > old_token, "the resumed swing performs one new strike")
	print("MINING_SWITCH ", JSON.stringify({"checks": checks, "failures": errors}))
	await Session.drain_field_audio(self, game)
	game.queue_free()
	await process_frame
	quit(int(not errors.is_empty()))
