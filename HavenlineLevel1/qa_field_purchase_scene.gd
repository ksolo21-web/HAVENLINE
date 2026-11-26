extends SceneTree

const Scene = preload("res://field_opening.tscn")
const Rules = preload("res://field_progression.gd")
var game
var checks := {}
var launched := 0
var clock := 0

func _initialize() -> void: call_deferred("run")

func check(id: String, value: bool) -> void:
	checks[id] = value
	if not value: push_error(id)

func approach(id: String, n: int) -> void:
	game.actor.global_position = game.carry.receivers[id].global_position
	for i in n:
		game._step_receivers()
		if game.carry.flights.size()>0: launched+=1
		game.carry.advance(1./60.)
		clock+=1

func run() -> void:
	game=Scene.instantiate()
	root.add_child(game)
	game.set_physics_process(false)
	game.carry.set_physics_process(false)
	if "--native-resume-final" in OS.get_cmdline_user_args():
		check("Independent native app slot reopened",game.field_save.native_profile and not game.persist_blocked)
		check("All eight purchases restored in original order",game.inventory.build_order==[Rules.HEARTH,Rules.FIRST,"storage_meat","storage_stone","storage_wood",Rules.SECOND,Rules.TOWER,Rules.AXES])
		check("Restored court has all three storage corners, no spent offer",game.field_env.perimeter_stage==3 and game.field_env.stock_anchors.values().all(func(a):return a.is_visible_in_tree()) and game.offer_floors.values().all(func(f):return not f.visible))
		print(JSON.stringify({"native_restart":checks}))
		game.sound.stop_playback()
		game.queue_free()
		for i in 4: await process_frame
		quit(1 if checks.values().has(false) else 0)
		return
	check("Actual game fresh save",not game.persist_blocked and game.inventory.build_order.is_empty())
	for kind in ["wood","stone","meat"]:
		for i in 30: game.inventory.collect(kind+str(i),kind)
	game.carry.sync()
	check("Only the central hearth payment is initially visible",game.field_env.buy_anchor.visible and game.offer_floors.values().all(func(f):return not f.is_visible_in_tree()))
	approach(Rules.HEARTH,100)
	check("Payment commits before hearth reveal",game.inventory.complete(Rules.HEARTH) and game.reveal_countdown>0.)
	game.reveal_countdown=-1.
	game._apply_hearth(true,true)
	check("Hearth reveals only first expansion and no storage",game.offer_floors[Rules.FIRST].is_visible_in_tree() and game.field_env.stock_anchors.values().all(func(a):return not a.is_visible_in_tree()) and not game.field_env.upgrade_anchor.is_visible_in_tree() and not game.offer_floors[Rules.AXES].is_visible_in_tree())
	approach(Rules.FIRST,130)
	check("Three corner offers appear on first expansion",Rules.STORAGE.all(func(id):return game.offer_floors[id].is_visible_in_tree()) and not game.offer_floors[Rules.SECOND].is_visible_in_tree())
	for id in ["storage_meat","storage_stone","storage_wood"]:
		approach(id,120)
		var kind: String=id.trim_prefix("storage_")
		check(id+" shows only purchased stock and does not dump same visit",game.inventory.complete(id) and game.field_env.stock_anchors[kind].is_visible_in_tree() and not game.offer_floors[id].is_visible_in_tree() and game.inventory.stored[kind]==0)
		game.actor.position=Vector3.ZERO
		game._step_receivers()
		approach(id,18)
		check(id+" re-entry deposits a separate physical unit",game.inventory.stored[kind]>0)
	check("Second expansion is the next build",game.offer_floors[Rules.SECOND].is_visible_in_tree() and not game.offer_floors[Rules.TOWER].is_visible_in_tree())
	approach(Rules.SECOND,160)
	check("East tower and extra axe pads unlock together",game.offer_floors[Rules.TOWER].is_visible_in_tree() and game.offer_floors[Rules.AXES].is_visible_in_tree())
	approach(Rules.TOWER,160)
	approach(Rules.AXES,120)
	check("All construction is paid and offerings retire",game.inventory.build_order==[Rules.HEARTH,Rules.FIRST,"storage_meat","storage_stone","storage_wood",Rules.SECOND,Rules.TOWER,Rules.AXES] and game.offer_floors.values().all(func(f):return not f.visible))
	check("Existing unit flights and authored purchase cues executed",launched>0 and game.events.any(func(e):return e.event=="spend_meat") and game.events.filter(func(e):return e.event=="purchase").size()==8)
	var loader=game.FieldSave.new()
	var restored=game.Inventory.new()
	restored.configure(Rules.offers({"wood":3}))
	var configured:bool=loader.configure(OS.get_cmdline_user_args())
	var read_error:int=loader.load_into(restored)
	var before:Dictionary=game.inventory.snapshot()
	var after:Dictionary=restored.snapshot()
	check("Disk contains this order, typed balances and lifecycle",configured and read_error==OK and before.build_order==after.build_order and before.carried==after.carried and before.stored==after.stored and before.paid==after.paid and restored.world_state.has("pack"))
	if read_error != OK: print("Save read failure: ",read_error, " ",game.persist_error)
	print(JSON.stringify({"scene_checks":checks,"route_physics_ticks":clock}))
	game.sound.stop_playback()
	game.queue_free()
	for i in 4: await process_frame
	quit(1 if checks.values().has(false) else 0)
