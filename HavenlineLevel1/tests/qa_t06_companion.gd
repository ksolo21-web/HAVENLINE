extends "res://tests/qa_worker_jobs.gd"
## Exercise the normal paid worker, its independent tools and the persistent
## appearance preference through actual travel and repeated harvest receipts.
const HERE := "res://tests/qa_t06_companion.gd"
const Companion := preload("res://field_companion_motion.gd")
const Motion := preload("res://field_character_motion.gd")
const C1 := "res://assets/characters/Character1Fresh.glb"

func run() -> void:
	if not Save.Profile.new().configure(OS.get_cmdline_user_args()):
		var profile := Session.make_directory()
		var status := Session.child(HERE, profile, "--core-companion")
		Session.remove_owned(profile)
		quit(status)
		return
	game = load("res://field_opening.tscn").instantiate()
	root.add_child(game)
	current_scene = game
	for i in 4: await physics_frame
	game.set_physics_process(false)
	worker = game.survivor
	setup_camp()
	var worker_actor: Node3D = worker.actor
	check(worker.core_motion == null and worker_actor.body_model.visible, "old saves keep the original forester")
	check(not game.set_companion_character(true), "Character 1 cannot occupy both roles")
	check(game.set_player_character(2), "alternate player character is available")
	var before: Dictionary = game.inventory.snapshot()
	check(game.set_companion_character(true), "Character 1 can join the paid survivor slot")
	if not worker.core_motion:
		quit(1)
		return
	var display: Node3D = worker.core_motion
	check(display.model.scene_file_path == C1 and FileAccess.get_sha256(C1) == Motion.MODEL_SHA256 and not worker_actor.body_model.visible, "companion uses the immutable Character 1 mesh")
	check(worker.actor == worker_actor and before == game.inventory.snapshot(), "appearance changes no actor, cargo, payment or work records")
	var tally := {"survivor_chop_contact": 0, "survivor_mine_contact": 0}
	var previous_id := 0
	var grip_error := {"chop": 0., "mine": 0.}
	var peak_sole_penetration := 0.
	var pivot_samples := 0
	var pivot_support_gap := 0.
	var pivot_support_slip := 0.
	var previous_pivot := {}
	var saw_run := false
	var saw_deposit := false
	for i in 18000:
		tick(1. / 60.)
		saw_run = saw_run or display.speed > 2. and display.locomotion.current == "run"
		saw_deposit = saw_deposit or display.cue == &"deposit"
		var steering = worker_actor.forester_gait
		if steering.pivot_frame:
			pivot_samples += 1
			var step: float = steering.pivot_elapsed if steering.pivot_elapsed >= 0. else 2. * steering.PIVOT_STEP
			var index: int = 1 - steering.pivot_first if step < steering.PIVOT_STEP else steering.pivot_first
			var ankle: Vector3 = display.gait._boot_world(index).origin
			var heights: Vector2 = display.gait._heights()
			pivot_support_gap = maxf(pivot_support_gap, heights[index] - worker_actor.global_position.y)
			if previous_pivot.get("side", -1) == index and float(previous_pivot.step) < step:
				pivot_support_slip = maxf(pivot_support_slip, (ankle - Vector3(previous_pivot.ankle)).slide(Vector3.UP).length())
			previous_pivot = {"step": step, "side": index, "ankle": ankle}
		else:
			previous_pivot.clear()
		if worker_actor.mode in ["chop", "mine"]:
			var mining: bool = worker_actor.mode == "mine"
			var grips: Array = Companion.PICK_GRIPS if mining else Companion.AXE_GRIPS
			var tool: Node3D = worker_actor.mining_tool if mining else worker_actor.tool
			if tool.visible:
				var palms: Dictionary = display.motion.sockets()
				for index in 2:
					var gap: float = tool.to_global(grips[index]).distance_to(palms["left_hand" if index == 0 else "right_hand"])
					grip_error[worker_actor.mode] = maxf(grip_error[worker_actor.mode], gap)
				var heights: Vector2 = display.gait._heights()
				peak_sole_penetration = maxf(peak_sole_penetration, worker_actor.global_position.y - minf(heights.x, heights.y))
		for entry: Dictionary in game.events.slice(previous_id):
			if tally.has(entry.event): tally[entry.event] += 1
		previous_id = game.events.size()
		if tally.survivor_chop_contact >= 3 and tally.survivor_mine_contact >= 3 and saw_deposit: break
	check(saw_run and saw_deposit and tally.survivor_chop_contact >= 3 and tally.survivor_mine_contact >= 3, "visible companion runs, works both real tools and deposits")
	check(maxf(grip_error.chop, grip_error.mine) <= .035 and peak_sole_penetration < .004, "companion gloves stay on approved tools with planted boots")
	check(pivot_samples >= 16 and pivot_support_gap < .004 and pivot_support_slip < .015, "live pivots preserve one planted boot")
	check(game.set_player_character(1) and worker.core_motion == null and worker_actor.body_model.visible and game.player_wardrobe.companion_selected, "lead switch restores forester while remembering choice")
	check(game.set_player_character(3) and worker.core_motion != null and worker.actor == worker_actor, "returning to a different lead restores the same hire")
	var expected: Dictionary = game.inventory.snapshot()
	game._persist_world()
	await Session.drain_field_audio(self, game)
	game.queue_free()
	await process_frame
	game = load("res://field_opening.tscn").instantiate()
	root.add_child(game)
	current_scene = game
	game.set_physics_process(false)
	worker = game.survivor
	var restored: Dictionary = game.inventory.snapshot()
	check(game.player_character() == 3 and worker.core_motion != null and not worker.actor.body_model.visible, "cold reload restores the chosen lead and companion")
	check(expected.settlement.worker_load == restored.settlement.worker_load and expected.stored == restored.stored and expected.settlement.worker_deliveries == restored.settlement.worker_deliveries, "reload conserves paid companion cargo and receipts")
	check(game.set_companion_character(false) and worker.core_motion == null and worker.actor.body_model.visible, "forester can be explicitly reselected")
	print("T06_COMPANION ", JSON.stringify({"checks": checks, "failures": errors, "work_contacts": tally, "grip_error_m": grip_error, "sole_penetration_m": peak_sole_penetration, "pivot_samples": pivot_samples, "pivot_gap_m": pivot_support_gap, "pivot_slip_m": pivot_support_slip}))
	await Session.drain_field_audio(self, game)
	game.queue_free()
	await process_frame
	quit(int(not errors.is_empty()))
