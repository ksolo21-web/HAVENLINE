extends SceneTree
func _initialize() -> void: run.call_deferred()
func run() -> void:
	var scene:=String(ProjectSettings.get_setting("application/run/main_scene"))
	var game=load(scene).instantiate()
	root.add_child(game)
	for i in 3:await physics_frame
	var state:Dictionary=game.inventory.snapshot()
	var goal:int=int(OS.get_environment("HL_EXPECT_LEVEL"))
	var file:=FileAccess.open(OS.get_environment("HL_RELOAD_JSON"),FileAccess.WRITE)
	var journal:Dictionary=game.inventory.settlement.duplicate(true)
	var button:Button=game.opening_hud.level_continue
	var okay:bool=not game.persist_blocked and journal.level==goal and journal.rescued and journal.worker_deliveries>=1 and journal.served>=1 and game.settlement_loop.ready() and button.visible==(goal==1)
	file.store_string(JSON.stringify({"pass":okay,"scene":scene,"settlement":journal,"hud":game.opening_hud.prompt.text,"button_visible":button.is_visible_in_tree(),"button_text":button.text,"save_blocked":game.persist_blocked,"actors_position":[game.actor.position.x,game.actor.position.z],"inventory":state,"real_relaunch":true},"  "))
	file.close()
	game.sound.stop_playback();game.queue_free()
	var until:=Time.get_ticks_msec()+260
	while Time.get_ticks_msec()<until:await process_frame
	quit(0 if okay else 3)
