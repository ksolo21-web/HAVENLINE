extends "res://tests/qa_worker_jobs.gd"
## Exercise live enemy contact, registered original companions, the existing
## worksite approaches and normal paid replacements in a disposable camp.

const HERE := "res://tests/qa_companion_replacement.gd"
const Crew = preload("res://field_crew.gd")

func _fund_pad(at: Vector3, kind: String, count: int, serial: String) -> void:
	game.actor.global_position = at
	for i in count:
		check(game.inventory.collect("%s-%d" % [serial,i],kind),"earned %s replacement receipt %d" % [serial,i])
	game.carry.sync()
	for i in 108:
		game.settlement_loop.works.advance(1.0/60.0)
		game.carry.advance(1.0/60.0)

func _stable_save() -> bool:
	var restored = game.Inventory.new()
	return restored.configure(game.inventory.configured_costs) and restored.restore(game.inventory.snapshot())

func run() -> void:
	if not Save.Profile.new().configure(OS.get_cmdline_user_args()):
		var path := Session.make_directory()
		var status := Session.child(HERE,path,"--companion-replacement")
		Session.remove_owned(path)
		quit(status)
		return
	game = load("res://field_opening.tscn").instantiate()
	root.add_child(game)
	current_scene = game
	for i in 4: await process_frame
	game.set_physics_process(false)
	game.set_process(false)
	worker = game.survivor
	setup_camp()
	_fund_pad(Crew.ROOST_AT,"meat",Crew.OWL_MEAT,"owl-first")
	var journal: Dictionary = game.inventory.settlement
	check(Crew.owns_owl(journal) and Crew.survivor_alive(journal),"the two original selections are live")
	var clearing := Vector3(4.0,0.0,11.1)
	worker.actor.global_position = clearing
	worker.actor.rotation.y = 0.0
	game.actor.global_position = Vector3(1.5,0.0,0.1)
	var wolf: Node3D = game.encounters._add(clearing+Vector3(0.0,0.0,1.01),true,999,clearing)
	wolf.rotation.y = 0.0
	check(not worker.provoked(wolf),"routine hostile is not pre-provoked by a wildlife hunter")
	check(worker.apply_enemy_contact(wolf,2) and journal.survivor_hp==Crew.SURVIVOR_HP-2,"actual enemy contact subtracts live survivor health")
	for i in 84:
		worker.advance(1.0/60.0)
		if worker.provoked(wolf):break
	check(worker.provoked(wolf) and wolf.hp<wolf.max_hp(),"visible survivor axe contact created retaliation")
	check(worker.apply_enemy_contact(wolf,20) and journal.survivor_hp==0 and not worker.can_defend(),"fatal enemy contact ends the survivor assignment")
	check(not worker.apply_enemy_contact(wolf,2),"a delayed contact cannot kill a worker twice")
	for i in 40:worker.advance(1.0/60.0)
	check(not worker.actor.is_visible_in_tree(),"defeated survivor has completed the visible fall")
	var bird: Node3D = game.owl
	bird.show()
	bird.global_position = clearing+Vector3(0.0,.62,.38)
	check(bird.apply_enemy_contact(wolf,20) and journal.owl_hp==0,"low and reachable owl can suffer lethal contact")
	check(not Crew.owns_owl(journal) and Crew.ever_owned_owl(journal),"original paid history is preserved when the roost reopens")
	check(_stable_save(),"both casualties persist without cloned balances")
	_fund_pad(game.settlement_loop.works.PLOT_AT,"wood",Crew.SURVIVOR_REPLACEMENT_WOOD,"survivor-return")
	_fund_pad(Crew.ROOST_AT,"meat",Crew.OWL_MEAT,"owl-return")
	worker.advance(1.0/60.0)
	bird.advance(1.0/60.0)
	check(journal.survivor_replacements==1 and journal.survivor_hp==Crew.SURVIVOR_HP and worker.actor.is_visible_in_tree(),"the separate paid survivor replacement returns at full health")
	check(journal.owl_replacements==1 and journal.owl_hp==Crew.OWL_HP and bird.visible,"the separate paid owl replacement returns at full health")
	check(_stable_save(),"committed replacement costs and active actors restore")
	print("COMPANION_REPLACEMENTS ",JSON.stringify({"checks":checks,"errors":errors,"survivor_hp":journal.survivor_hp,"owl_hp":journal.owl_hp,"survivor_replacements":journal.survivor_replacements,"owl_replacements":journal.owl_replacements}))
	await Session.drain_field_audio(self,game)
	game.queue_free()
	for i in 4: await process_frame
	quit(int(not errors.is_empty()))
