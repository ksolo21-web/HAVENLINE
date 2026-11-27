extends SceneTree
## The same probe runs against the Android export's unmodified packed resources.
var game
var checks := {}

func _initialize() -> void:
	call_deferred("run")

func run() -> void:
	game = load("res://field_opening.tscn").instantiate()
	root.add_child(game)
	current_scene = game
	var cold := "--reopen" in OS.get_cmdline_user_args()
	var book = game.inventory
	var j:Dictionary = book.settlement
	checks["Loaded paid camp in disposable profile"] = game.field_ready and not game.persist_blocked and book.complete("supply_conveyors")
	checks["Eight typed cargo lanes in migrated ledger"] = j.line_load.size()==8 and book.snapshot().version==9
	if not cold:
		checks["All three Build 9 shipments and their progress survived"] = j.line_load.wood==1 and j.line_load.stone==1 and j.line_load.meat==1 and float(j.line_progress.wood)>0.
	else:
		checks["Previous sale and finished stock persisted"] = j.served==7 and j.product_store.planks==3 and j.product_store.blocks==3
	game.actor.position = game.field_env.hearth_shell.global_position+Vector3(0,0,2.)
	var belt=game.settlement_loop.conveyors
	var reached_board := false
	var heard_motor := false
	var observed_stock := false
	var observed_load := false
	for i in (75 if cold else 5600):
		await physics_frame
		heard_motor = heard_motor or game.sound._conveyor_gain>0.02
		var state:Dictionary=book.settlement
		observed_stock = observed_stock or state.counter_stock>0
		observed_load = observed_load or state.line_load.meal>0 or state.line_load.stored_meal>0
		reached_board = reached_board or (game.counter.belt_serving and game.counter.sale_committed)
		if not cold and state.served==7 and state.product_store.planks==3 and state.product_store.blocks==3: break
	checks["All owned channels have installed physical transport surfaces"] = belt.network.routes.size()==8 and belt.network.art!=null and belt.blocked_lane.is_empty()
	var fitted = belt.network.art.find_child("MeshyConveyorModules", true, false)
	var counts:Dictionary = fitted.counts.duplicate() if fitted else {}
	checks["Furnished straight, corner and inclined Meshy modules visible on paid lines"] = counts.get("straight",0)>0 and counts.get("corner",0)>0 and counts.get("incline",0)>0
	var house = game.depot.house
	var dock_hits := 0
	var outward_faces := 0
	for dock in [["wood",true],["wood",false],["meal",true],["meal",false]]:
		var expected:Vector3 = belt.network.storage_port(dock[0],dock[1])
		var frame_id := "FoodDockFrame" if dock[0]=="meal" else "UtilityDockFrame"
		for part in belt.network.art.get_children():
			if part is MeshInstance3D and part.mesh==house.dock_meshes[frame_id] and part.global_position.distance_to(expected)<.001:
				dock_hits+=1
				var exterior := Vector3.FORWARD if dock[0]=="meal" else Vector3.LEFT
				if part.global_transform.basis.z.normalized().dot(exterior)>.999: outward_faces+=1
				break
	checks["Food and utility signage faces the exterior on both incoming and outgoing warehouse loads"] = outward_faces==4
	checks["Four reference-derived food and utility frames seat on live warehouse mouths"] = dock_hits==4
	checks["Paid storehouse selects the fitted roof over its original and retains both service doors"] = house.connections_paid and house.connection_roof.get_child_count()>0 and house.parts.has("DoorLeft") and house.parts.has("DoorRight")
	if not cold:
		checks["Real moving stock starts mechanical ambience"] = heard_motor
	j=book.settlement
	checks["Materials became three planks and three dressed blocks on separate shelves"] = j.product_store.planks==3 and j.product_store.blocks==3
	checks["Six raw portions plus earlier sale settled exactly seven orders"] = j.served==7 and j.cooked==7 and j.counter_stock==0
	if not cold:
		checks["Stock travelled, stopped in the staff buffer and changed hands"] = observed_load and observed_stock and reached_board
	checks["A real operator reached the public worktop"] = game.counter.attendant!=null and game.counter.attendant.palm!=null
	game._persist_world()
	checks["Saved cleanly"] = not game.persist_blocked
	print("SIGNED_CAMP ",JSON.stringify({"checks":checks,"Meshy_modules":counts,"reopen":cold,"served":j.served,"product_store":j.product_store,"source_schema":8,"migrated_schema":book.snapshot().version}))
	game.set_physics_process(false)
	game.carry.set_physics_process(false)
	game.sound.stop_playback()
	for tick in 12:
		OS.delay_msec(20)
		await process_frame
	game.queue_free()
	for i in 6: await process_frame
	quit(int(checks.values().has(false)))
