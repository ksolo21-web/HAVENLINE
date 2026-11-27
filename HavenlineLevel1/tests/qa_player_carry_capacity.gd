extends SceneTree

const Session = preload("res://tests/lifecycle_test_profile.gd")
const Profile = preload("res://opening_save.gd")
const Inventory = preload("res://field_inventory.gd")
const Store = preload("res://field_save.gd")
const SELF := "res://tests/qa_player_carry_capacity.gd"
const STRESS_BUNDLES := 2500
var checks := {}

func _initialize() -> void:
	var args := OS.get_cmdline_user_args()
	if args.has("--earn") or args.has("--reopen"):
		var guard := Profile.new()
		if not guard.configure(args):
			quit(2)
			return
		run.call_deferred()
		return
	var directory := Session.make_directory()
	if directory.is_empty():
		quit(2)
		return
	var code := Session.child(SELF,directory,"--earn")
	if code == 0: code = Session.child(SELF,directory,"--reopen")
	Session.remove_owned(directory)
	quit(code)

func run() -> void:
	var world = load("res://field_opening.tscn").instantiate()
	root.add_child(world)
	await process_frame
	world.set_physics_process(false)
	var book: Inventory = world.inventory
	var earn := "--earn" in OS.get_cmdline_user_args()
	if earn:
		# Start one bundle below 1,000 on all six lanes. The next two entries
		# go through the same pickup, animation, HUD and save calls as play.
		for kind: String in Inventory.KINDS:
			for index in 99: book.collect("%s-%d" % [kind,index],kind)
		world.carry.sync()
		for kind: String in Inventory.KINDS:
			var crossed := true
			for index in [99,100]:
				crossed = world.carry.pickup("%s-%d" % [kind,index],kind,world.actor.global_position) and crossed
				world.carry.advance(1.)
			checks[kind + " crosses 1,000 on the HUD"] = crossed and world.opening_hud.numbers[kind].text == "1010"
			for index in range(101, STRESS_BUNDLES):
				book.collect("%s-%d" % [kind,index],kind)
		world._inventory_changed()
		checks["large pack saved"] = not world.persist_blocked
	for kind: String in Inventory.KINDS:
		checks[kind + " exact balance"] = int(book.carried[kind]) == STRESS_BUNDLES and world.opening_hud.numbers[kind].text == str(Inventory.Progress.units(STRESS_BUNDLES))
		checks[kind + " replay ignored"] = not book.collect("%s-100" % kind,kind)
	checks["compressed marked slot"] = FileAccess.get_file_as_bytes(world.field_save.directory.path_join(Store.PRIMARY)).slice(0,4).get_string_from_ascii() == "GCPF"
	var passed := not checks.values().has(false)
	print(JSON.stringify({"phase":"earn" if earn else "cold reopen","units_per_material":Inventory.Progress.units(STRESS_BUNDLES),"checks":checks,"passed":passed}))
	await Session.drain_field_audio(self,world)
	world.free()
	quit(0 if passed else 1)
