extends SceneTree
## This probe opens a copy of an existing trial journal. The authoring pass uses
## the Build 11 game to write both a walker's position and its own normal save.
const Scene = preload("res://field_opening.tscn")

func _initialize() -> void:
	call_deferred("run")

func run() -> void:
	var game = Scene.instantiate()
	root.add_child(game)
	current_scene = game
	var args := OS.get_cmdline_user_args()
	var expect_custom := "--custom" in args
	var prior_saw := "--kitchen" in args
	var writing := "--author" in args
	var old_snow := Vector3(-7.55, 0, -6.85)
	var result := {"field ready": game.field_ready and not game.persist_blocked, "paid machinery": game.inventory.is_machine_owned("wood") and game.inventory.is_machine_owned("stone")}
	if writing and not expect_custom and not prior_saw:
		game.actor.position = old_snow
		result["Build 11 save position is snow outside the fence"] = not game.field_env.is_inside_camp(game.actor.position)
	if writing and prior_saw:
		var point := Vector2(1.75,-4.50)
		result["Build 11 moved the saw into an open legacy bay"] = game.camp_layout.relocate("saw_bench",point)
	var placed: Dictionary = game.camp_layout.snapshot()
	if expect_custom:
		result["seven paid buildings recovered at the recorded locations"] = placed.size() == 7 and game.camp_layout.center("north_counter").is_equal_approx(Vector2(4,-9)) and game.camp_layout.center("camp_cooker").is_equal_approx(Vector2(4.75,2.75)) and game.camp_layout.center("storage_wood").is_equal_approx(Vector2(4.5,-2.5)) and game.camp_layout.center("saw_bench").is_equal_approx(Vector2(-3.5,2.5)) and game.camp_layout.center("quarry_drill").is_equal_approx(Vector2(7.75,-6.25)) and game.camp_layout.center("center_hearth").is_equal_approx(Vector2(-2.75,-2.5)) and game.camp_layout.center("watchtower").is_equal_approx(Vector2(8.,3.5))
	elif prior_saw:
		result["saved saw remains at its purchased location"] = game.camp_layout.center("saw_bench").is_equal_approx(Vector2(1.75,-4.50))
	elif not writing:
		var at: Vector2 = game.camp_layout.xz(game.actor.global_position)
		var yard = game.settlement_loop.conveyors.network.aisles
		result["previous snow save relocated outside the new saw"] = at.distance_to(Vector2(old_snow.x,old_snow.z)) > 1. and not game.camp_layout.footprint("saw_bench",game.camp_layout.center("saw_bench")).grow(float(game.layout.actor_radius)).has_point(at)
		result["arrival has a public walking route and clears all live belts"] = yard != null and yard.ready and yard.disc_clear(at,float(game.layout.actor_radius)) and yard.public_cells.has(yard._key(at))
	game._persist_world()
	result["normal save succeeds"] = not game.persist_blocked
	var pos: Vector3=game.actor.global_position
	print("RETURNING_CAMP ",JSON.stringify({"checks":result,"position":[pos.x,pos.y,pos.z],"layout":placed,"hp":game.player_hp,"purchases":game.inventory.build_order,"stored":game.inventory.stored,"served":game.inventory.settlement.served}))
	game.set_physics_process(false)
	game.carry.set_physics_process(false)
	game.sound.stop_playback()
	for tick in 12:
		OS.delay_msec(20)
		await process_frame
	game.queue_free()
	for tick in 4: await process_frame
	quit(0 if result.values().all(func(item): return item == true) else 2)
