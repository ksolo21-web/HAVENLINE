extends SceneTree

var checks := {}
var game

func _initialize() -> void:
	call_deferred("run")

func check(label: String, condition: bool) -> void:
	checks[label] = condition

func tick(count: int) -> void:
	for i in count: game.settlement_loop.advance(1./60.)

func run() -> void:
	var scene = load("res://field_opening.tscn")
	game = scene.instantiate()
	root.add_child(game)
	game.set_physics_process(false)
	check("ordinary field and private earned save",game.scene_file_path=="res://field_opening.tscn" and game.field_ready and game.inventory.complete(game.Progress.SECOND) and not game.persist_blocked)
	var works = game.processors
	check("north row inside perimeter",game.field_env.is_inside_camp(works.APRONS.wood) and game.field_env.is_inside_camp(works.APRONS.stone) and game.field_env.is_inside_camp(game.lakeshore.APRON))
	check("empty saw hides timber workpiece",not game.settlement_loop.transfers.saw_log.visible)
	check("eight authored cooker rollers",game.settlement_loop.transfers.rollers.size()==8)
	var journal: Dictionary = game.inventory.settlement
	var starting: int = journal.processed_stone
	var before: int = game.inventory.carried.stone
	game.actor.global_position=works.APRONS.stone
	tick(24)
	check("stock physically moved into drill",journal.hoppers.stone==1 and game.inventory.carried.stone==before-1)
	game.actor.global_position=Vector3(4,0,1)
	tick(90)
	check("drill finished after operator departure",journal.processed_stone==starting+1 and journal.hoppers.stone==0)
	var raw: int=game.inventory.carried.meat
	game.actor.global_position=game.lakeshore.APRON
	tick(24)
	game.actor.global_position=Vector3(4,0,1)
	tick(102)
	check("stocked cooker runs away from player",game.inventory.carried.meat==raw-1 and journal.cooked>0 and game.settlement_loop.transfers.shown_meals>0)
	check("cooked portion remains at machine",journal.held_meal==0 and journal.served==0)
	game.actor.global_position=game.lakeshore.OUTPUT_APRON
	tick(1)
	check("collection at separate outlet",journal.held_meal==1)
	check("sealed north counter and outside customer",game.field_env.is_inside_camp(game.counter.service_point.global_position) and not game.field_env.is_inside_camp(game.counter.customer_point.global_position))
	var tower = game.defense_tower.art
	tower.update_sightline(Vector3(6.168,0,-4.102),game.camera)
	check("eastern tower clears the drill exit sightline",tower.cutaway_active)
	tower.update_sightline(Vector3(4.9,0,.2),game.camera)
	check("tower returns to its complete silhouette",not tower.cutaway_active)
	var passed: bool = not checks.values().has(false) and not game.persist_blocked
	print("PACKAGE_QA ",JSON.stringify({"passed":passed,"scene":game.scene_file_path,"checks":checks,"engine":Engine.get_version_info().string}))
	game.sound.stop_playback()
	game.queue_free()
	for i in 4: await process_frame
	quit(0 if passed else 1)
