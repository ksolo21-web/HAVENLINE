extends SceneTree
## An earned launch with more live bundles than the old ground limit, then a
## cold reopen. Exercise the normal physics pickup, rack flight and journal.
const Session = preload("res://tests/lifecycle_test_profile.gd")
const Store = preload("res://field_save.gd")
const Profile = preload("res://opening_save.gd")
const SCRIPT := "res://tests/qa_ground_sweep.gd"
const BUNDLES := 96
var changes := 0
var checks := {}

func _initialize() -> void:
	var args := OS.get_cmdline_user_args()
	if "--sweep" in args or "--reopen" in args:
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
	var file := FileAccess.open(directory.path_join(Store.PRIMARY),FileAccess.WRITE)
	file.store_buffer(FileAccess.get_file_as_bytes("res://tests/fixtures/camp_hud_paid.json"))
	file.close()
	var code := Session.child(SCRIPT,directory,"--sweep")
	if code == 0:
		code = Session.child(SCRIPT,directory,"--reopen")
	Session.remove_owned(directory)
	quit(code)

func token(i: int) -> String:
	return ("stone" if i % 2 else "meat") + "-" + str(72000+i)

func run() -> void:
	var field = load("res://field_opening.tscn").instantiate()
	root.add_child(field)
	var earn := "--sweep" in OS.get_cmdline_user_args()
	checks["earned three-tool camp resumed"] = not field.persist_blocked and field.inventory.complete("orbit_upgrade") and field.camp_active
	if earn:
		# Raise existing credit history independently of the empty pack.
		for i in 2500:
			field.inventory.collect("deep-receipt-%d"%i,"slate")
		field.inventory.deposit("slate",2500)
		field.actor.global_position = Vector3(24.,0.,11.)
		var at: Vector3 = field.actor.global_position
		for i in BUNDLES:
			var id := token(i)
			var angle := TAU * i / BUNDLES
			var p := at + Vector3(cos(angle),0.,sin(angle))*(2.02 if i%3 else .52)
			field._place_drop(id,id.get_slice("-",0),p,p,angle,.4)
		field.drop_id=73000
		field._persist_world()
		var loose: Array = field.lifecycle.snapshot().drops
		checks["all new loose receipts remain eligible before next step"] = loose.filter(func(row): return str(row[0]).get_slice("-",1).to_int()>=72000).size()==BUNDLES
		field.carry.inventory_changed.connect(func(): changes+=1)
		for step in 3: await physics_frame
		checks["one grouped save signs the near and edge pickup receipts"] = changes == 1
		checks["dense flight is bounded by material count"] = not field.carry.flights.is_empty() and field.carry.flights.size()<=2*field.carry.PICKUP_PIECES_PER_KIND
		for step in 25: await physics_frame
		checks["visual arrival performs no second pickup save"] = changes == 1
		field._persist_world()
	var valid := true
	for i in BUNDLES:
		var id := token(i)
		valid = valid and field.inventory.collected.get(id)==id.get_slice("-",0) and not field.drops.has(id)
	checks["all unique drops credited once, no stale ground copies"] = valid and field.inventory.carried.meat==BUNDLES/2 and field.inventory.carried.stone==BUNDLES/2 and not field.persist_blocked
	if not earn:
		# A concurrently opened journal can advance before this physics tick.
		# Preserve the unclaimed pickups and never overwrite the winning file.
		var writer := Store.new()
		var newer := preload("res://field_inventory.gd").new()
		var peer_ready := writer.configure(OS.get_cmdline_user_args()) and newer.configure(field.inventory.configured_costs) and writer.load_into(newer)==OK
		var saved := peer_ready and newer.collect("other-journal-meat","meat") and writer.commit(newer)==OK
		var p: Vector3 = field.actor.global_position
		field._place_drop("stone-78001","stone",p,p,0.,.42)
		field._step_drops(0.)
		checks["a concurrent write retains the pending ground pickup"] = saved and field.persist_blocked and field.drops.has("stone-78001") and not field.inventory.collected.has("stone-78001") and field.inventory.carried.stone==BUNDLES/2
		checks["the newer journal remains authoritative"] = writer.load_into(newer)==OK and newer.collected.has("other-journal-meat") and not newer.collected.has("stone-78001")
	print("GROUND_SWEEP ",JSON.stringify({"stage":"earn" if earn else "reopen","checks":checks}))
	await Session.drain_field_audio(self,field)
	field.queue_free()
	await process_frame
	quit(1 if false in checks.values() else 0)
