extends SceneTree
## Fork an earned in-transit receipt into normal delivery and a blocked loading bay.
const Session = preload("res://tests/lifecycle_test_profile.gd")
const Save = preload("res://field_save.gd")
const SELF := "res://tests/qa_worker_supply.gd"
var game
var failures: Array[String] = []
var checked := 0

func _initialize() -> void:
	call_deferred("run")

func check(condition: bool, label: String) -> void:
	checked += 1
	if not condition: failures.append(label)

func fund(id: String) -> void:
	for kind: String in game.inventory.remaining(id):
		for i in int(game.inventory.remaining(id)[kind]):
			check(game.inventory.collect("supply-%s-%s-%d" % [id,kind,i],kind) and game.inventory.payment(id,kind,false),"fund "+id)

func to_shelf(kind: String, count: int) -> void:
	for i in count:
		check(game.inventory.collect("supply-stock-%s-%d" % [kind,i],kind) and game.inventory.deposit(kind),"store "+kind)

func pickup() -> void:
	for id in ["center_hearth","expansion_1","storage_wood","storage_stone","storage_meat","expansion_2"]: fund(id)
	game._apply_hearth(true,false)
	for i in 2: game.inventory.collect("supply-rescue-%d"%i,"wood")
	game.inventory.carried.wood -= 2
	var journal: Dictionary = game.inventory.settlement
	journal.survivor_wood = 2
	journal.survivor_paid = true
	journal.rescued = true
	to_shelf("wood",3)
	to_shelf("meat",1)
	to_shelf("stone",4)
	check(game.survivor._next_supply().is_empty(),"reserve all unpaid tower and axe costs")
	game.inventory.collect("extra-stone","stone")
	game.inventory.deposit("stone")
	game._inventory_changed()
	game.survivor.actor.position = game.survivor.READY
	game.survivor.phase = "waiting_storage"
	for i in 300:
		game.survivor.advance(1./60.)
		if game.survivor.phase == "supply_out": break
	check(journal.worker_supply=="stone" and game.inventory.stored.stone==4,"physical withdrawal debits one stone and persists cargo")
	check(game.survivor.actor.position.distance_to(game.depot.APRON)<.03,"survivor walked to the loading door")
	check(game.survivor.supply_model.get_child_count()>0,"worker carries the stone asset")
	for i in 60: game.survivor.advance(1./60.)
	check(game.survivor.actor.position.distance_to(game.depot.APRON)>1.5 and journal.hoppers.stone==0,"hopper remains empty while survivor crosses camp")
	game._persist_world()

func delivery(full: bool) -> void:
	var worker = game.survivor
	var journal: Dictionary = game.inventory.settlement
	check(journal.worker_supply=="stone" and worker.phase=="supply_out" and game.inventory.stored.stone==4,"cold load resumes one paid unit")
	if full:
		for i in 4:
			game.inventory.collect("full-hopper-%d"%i,"stone")
			game.inventory.carried.stone -= 1
			journal.hoppers.stone += 1
		game._inventory_changed()
	var lane_clear := true
	var reached_input := false
	var entered_bay := false
	for i in 1800:
		worker.advance(1./60.)
		var pos: Vector3 = worker.actor.position
		var house: Vector3 = pos-game.depot.SITE
		var in_house_wall := absf(house.x)<1.66 and absf(house.z)<1.25
		lane_clear = lane_clear and game.field_env.is_inside_camp(pos) and not in_house_wall
		if worker.phase == "supply_unload":
			reached_input = true
			entered_bay = pos.distance_to(game.processors.APRONS.stone)<.04
		if journal.worker_supply=="": break
	check(reached_input and entered_bay and lane_clear,"real survivor carried stone around the house to drill")
	check(journal.worker_supply=="","in-transit receipt clears once")
	var restored = game.Inventory.new()
	check(restored.configure(game.inventory.costs) and restored.restore(game.inventory.snapshot()),"all material conserved after delivery")
	if full:
		check(worker.actor.position.distance_to(game.depot.APRON)<.04,"full hopper sends survivor back to the loading door")
		check(game.inventory.stored.stone==5 and journal.hoppers.stone==4,"full hopper returns exactly one stone to shelf")
	else:
		check(game.inventory.stored.stone==4 and journal.hoppers.stone==1,"completed trip feeds one stone without player input")
		for i in 92: game.settlement_loop.advance_unattended(1./60.)
		check(journal.hoppers.stone==0 and journal.processed_stone==1,"autonomous drill finishes delivered stone once")
	check(game.inventory.stored.wood==3 and game.inventory.stored.meat==1,"other shelf balances unchanged")

func run() -> void:
	var args := OS.get_cmdline_user_args()
	var mode := ""
	for name in ["pickup","deliver","full"]:
		if name in args: mode=name
	if mode.is_empty():
		var first := Session.make_directory()
		var second := Session.make_directory()
		var status := Session.child(SELF,first,"pickup")
		if status==0: status = DirAccess.copy_absolute(first.path_join(Save.PRIMARY),second.path_join(Save.PRIMARY))
		if status==0: status = Session.child(SELF,first,"deliver")
		if status==0: status = Session.child(SELF,second,"full")
		Session.remove_owned(first)
		Session.remove_owned(second)
		quit(status)
		return
	var guard = Save.Profile.new()
	if not guard.configure(args):
		quit(2)
		return
	game = load("res://field_opening.tscn").instantiate()
	root.add_child(game)
	game.set_physics_process(false)
	game.actor.position = Vector3(4,0,1)
	if mode=="pickup": pickup()
	else: delivery(mode=="full")
	print(JSON.stringify({"phase":mode,"checks":checked,"failures":failures}))
	game.sound.stop_playback()
	game.queue_free()
	for i in 4: await process_frame
	quit(0 if failures.is_empty() else 1)
