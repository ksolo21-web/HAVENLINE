extends SceneTree

var world
var checks := {}

func _initialize() -> void:
	run.call_deferred()

func run() -> void:
	world = load("res://field_opening.tscn").instantiate()
	root.add_child(world)
	current_scene = world
	var book = world.inventory
	var earned = book.snapshot()
	var totals := {}
	var balance := {}
	for kind in book.KINDS:
		totals[kind] = 0
	for kind in earned.collected.values():
		totals[kind] += 1
	for kind in totals:
		var accounted := int(earned.carried[kind]) + int(earned.stored[kind])
		for cost in earned.paid.values():
			accounted += int(cost.get(kind, 0))
		balance[kind] = totals[kind] - accounted

	checks["Earned profile and built first perimeter restored"] = world.field_ready and not world.persist_blocked and world.camp_active and world.field_env.perimeter_stage == 1
	checks["The paid hearth is physically visible"] = world.field_env.hearth_shell.is_visible_in_tree() and book.complete("center_hearth")
	checks["First purchase consumed exactly twenty wood bundles"] = earned.build_order == ["center_hearth"] and earned.paid.center_hearth == {"wood":20}
	checks["First expansion retains four wood and three stone bundles"] = earned.paid.expansion_1 == {"wood":4, "stone":3} and book.remaining("expansion_1") == {"wood":8, "stone":3}
	checks["Two meat bundles remain in the pack with no other carried stock"] = earned.carried.meat == 2 and earned.carried.values().reduce(func(a,b): return a+b, 0) == 2
	checks["The original 29 unique receipts conserve all six materials"] = earned.collected.size() == 29 and totals.wood == 24 and totals.stone == 3 and totals.meat == 2 and not balance.values().any(func(delta): return delta != 0)
	checks["Cash and storage remain at their earned zero balances"] = earned.settlement.served == 0 and not earned.stored.values().any(func(n): return n != 0)
	var active := []
	for id in world.offer_floors:
		if world.offer_floors[id].is_visible_in_tree():
			active.append(id)
	checks["Only the uncompleted first expansion currently shows a construction mat"] = world.next_project == "expansion_1" and active == ["expansion_1"] and book.offer_open("expansion_1")
	var gate_states := {}
	var original:Vector3 = world.actor.global_position
	for gate in world.gates:
		var id := str(gate.gate_id).to_lower()
		world.actor.global_position = gate.to_global(Vector3(0,0,-1.65))
		for step in 84:
			world.step_technical_gates(1./60.)
		gate_states[id] = {"angle_degrees":rad_to_deg(gate.angle), "leaves":gate._leaf_bodies.size(), "visible":gate.is_visible_in_tree()}
	world.actor.global_position = original
	world.previous_dry_position = original
	var pass_gates := gate_states.size() == 2
	for id in gate_states:
		var gate_state:Dictionary = gate_states[id]
		pass_gates = pass_gates and gate_state.visible and gate_state.leaves == 2 and gate_state.angle_degrees > 89.
	checks["Both distinct two-leaf gates open to player proximity"] = pass_gates
	world._persist_world()
	checks["Normal game save succeeds"] = not world.persist_blocked
	var result := {"cold": "--reopen" in OS.get_cmdline_user_args(), "checks":checks, "ledger_version":earned.version, "paid": {"hearth":earned.paid.center_hearth,"expansion":earned.paid.expansion_1}, "remaining":book.remaining("expansion_1"),"carried":earned.carried, "stored":earned.stored,"cash":earned.settlement.served,"source_receipts":earned.collected.size(),"typed_receipt_totals":totals,"typed_balance_delta":balance,"gates":gate_states,"visible_offers":active}
	print("SIGNED_EARNED_OPENING ",JSON.stringify(result))
	world.set_physics_process(false)
	world.carry.set_physics_process(false)
	world.sound.stop_playback()
	for tick in 10:
		OS.delay_msec(20)
		await process_frame
	world.queue_free()
	for tick in 6:
		await process_frame
	quit(int(checks.values().has(false)))
