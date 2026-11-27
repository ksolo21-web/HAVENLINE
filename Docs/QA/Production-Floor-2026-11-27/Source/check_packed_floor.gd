extends SceneTree
## External desktop entry point for the Android export's normal field scene.
const Field = preload("res://field_opening.tscn")
const Profile = preload("res://opening_save.gd")
const Freight = preload("res://field_logistics.gd")

var game
var book
var ledger: Dictionary
var checks := {}
var phases_seen := {}
var visited := {}
var meals_sold := []
var aim_fired := false
var aim_hit := false
var saw_loaded_bolt := false
var saw_flying_bolt := false

func _initialize() -> void:
	call_deferred("run")

func holdings() -> Dictionary:
	return {"raw_meat":book.stored.meat,"at_cooker":ledger.hoppers.meat,"outfeed":Freight.rack(ledger,"meat"),
			"line_load":ledger.line_load.duplicate(),"shelf":ledger.product_store.meal,"counter":ledger.counter_stock,
			"cooked":ledger.cooked,"served":ledger.served,"wood":book.stored.wood,"stone":book.stored.stone}

func observe() -> void:
	for lane: String in ["meat","meal_to_store","stored_meal"]:
		if ledger.line_load[lane] > 0:
			visited[lane] = true
	var tower = game.defense_tower
	var art = tower.art
	saw_loaded_bolt = saw_loaded_bolt or art.bolt.is_visible_in_tree()
	for flight: Dictionary in tower.flights:
		saw_flying_bolt = saw_flying_bolt or (flight.mesh.mesh == art.bolt.mesh and not art.bolt.visible)
	for event: Dictionary in game.events:
		if event.event == "tower_fire":
			aim_fired = true
		if event.event == "tower_hit":
			aim_hit = true
	if meals_sold.is_empty() or meals_sold.back() != ledger.served:
		meals_sold.append(ledger.served)

func run() -> void:
	var args := OS.get_cmdline_user_args()
	if not Profile.new().configure(args):
		quit(2)
		return
	game = Field.instantiate()
	root.add_child(game)
	current_scene = game
	book = game.inventory
	ledger = book.settlement
	var phase := args[-1]
	checks["isolated normal paid field loaded"] = game.field_ready and not game.persist_blocked and book.complete("meal_conveyor") and book.complete("watchtower")
	var first := holdings()
	var parked: Vector3 = game.actor.position
	if phase == "stock":
		game.counter.arrival_clock = 180.
		checks["six raw portions and one cooked portion start in a paid food-only camp"] = book.stored.meat == 6 and ledger.cooked == 1 and ledger.served == 0 and not book.complete("supply_conveyors") and not ledger.rescued
		for tick in 6500:
			await physics_frame
			observe()
			if ledger.counter_stock == 2 and ledger.product_store.meal == 5 and ledger.cooked == 7:
				break
		checks["stock moves on all three serial legs"] = visited.size() == 3
		checks["empty counter stocks itself and excess meals reach the shelf"] = ledger.counter_stock == 2 and ledger.product_store.meal == 5 and ledger.served == 0 and game.counter.queue.is_empty()
		checks["all six portions cooked and every conveyor cleared"] = book.stored.meat == 0 and ledger.cooked == 7 and ledger.hoppers.meat == 0 and Freight.rack(ledger,"meat") == 0 and ledger.line_load == Freight.TRANSIT
		var tower = game.defense_tower
		checks["paid deck has a rigged operator, stock and loaded quarrel"] = tower.active and tower.art.crew.is_visible_in_tree() and tower.art.crew.rig.get_bone_count() >= 16 and tower.art.bow.is_visible_in_tree() and saw_loaded_bolt
		checks["normal field tower launches the displayed quarrel and hits a hostile"] = saw_flying_bolt and aim_fired and aim_hit
	elif phase == "serve":
		checks["cold launch restores two servings and five stored roasts"] = ledger.cooked == 7 and ledger.served == 0 and ledger.counter_stock == 2 and ledger.product_store.meal == 5
		game.counter.arrival_clock = 0.
		for tick in 7400:
			await physics_frame
			observe()
			if ledger.served == 7:
				break
		for tick in 120:await physics_frame
		checks["seven normal customers paid once each"] = meals_sold == [0,1,2,3,4,5,6,7] and game.events.any(func(e): return e.event == "meal_served")
		checks["all seven servings left the ledger exactly once"] = ledger.cooked == ledger.served and ledger.served == 7 and ledger.counter_stock == 0 and ledger.product_store.meal == 0 and ledger.line_load == Freight.TRANSIT
	elif phase == "reopen":
		checks["second cold launch restored all seven sales"] = ledger.served == 7 and ledger.cooked == 7 and ledger.product_store.meal == 0 and ledger.counter_stock == 0
		var fire = game.field_env.hearth_fire
		var warm: bool = fire.fired and fire.is_visible_in_tree()
		for name: String in ["CoalsUnderFlue","ArchedFirebox","FlueFlame","ChimneyDraft"]:
			var mesh = fire.get_node(name)
			warm = warm and mesh.is_visible_in_tree() and mesh.material_override is ShaderMaterial
		checks["paid hearth loads coal, firebox, vent and moving exhaust"] = warm and fire.chamber_light.is_visible_in_tree()
		# Place the actor on outside snow to apply an actual combat hit, then
		# return him to his saved camp spot and let the normal clock handle HP.
		game.actor.position = game.gates[0].global_position + Vector3.BACK * 2.
		game.actor.position.y = 0.
		game.previous_dry_position = game.actor.position
		game.player_invulnerability = 0.
		game._player_hit(7)
		var wounded: int = game.player_hp
		game.actor.position = parked
		game.previous_dry_position = parked
		var pulse := 0.0
		for tick in 202:
			await physics_frame
			pulse = maxf(pulse,fire.recovery_pulse)
		checks["hearth heals field damage at the normal camp spot, pulses and updates HUD"] = wounded == game.MAX_HP - 7 and game.player_hp == game.MAX_HP and game.opening_hud.health_bar.value == game.player_hp and pulse > .8
		phases_seen = {"field_hp":wounded,"healed_hp":game.player_hp,"peak_heat_pulse":pulse}
	else:
		checks["recognized scenario"] = false
	checks["carrier remained parked for the connected supply and service"] = game.actor.position.distance_to(parked) < .025 and not ledger.rescued and ledger.worker_supply == "" and ledger.worker_meal == 0 and ledger.held_meal == 0
	checks["unconnected materials remain on their original shelves"] = book.stored.wood == 3 and book.stored.stone == 3
	game._checkpoint_lifecycle()
	checks["journal checkpoint succeeds"] = not game.persist_blocked
	print("PACKED_FLOOR ",JSON.stringify({"phase":phase,"checks":checks,"initial":first,"final":holdings(),"lanes":visited.keys(),"paid_orders":meals_sold,"hearth":phases_seen}))
	game.set_physics_process(false)
	game.carry.set_physics_process(false)
	game.sound.stop_playback()
	for tick in 12:
		OS.delay_msec(20)
		await process_frame
	game.queue_free()
	for tick in 4: await process_frame
	quit(1 if false in checks.values() else 0)
