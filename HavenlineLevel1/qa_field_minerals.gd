extends SceneTree
## With no flags this stages a legacy ledger in a fresh, guarded profile and
## launches two actual game processes, one on each side of the migration.
const Inventory = preload("res://field_inventory.gd")
const Store = preload("res://field_save.gd")
const Rules = preload("res://field_progression.gd")
const Scene = preload("res://field_opening.tscn")
const SAMPLES := {"coal":3,"slate":4,"metal":5}
var checks := {}

func check(label: String, ok: bool) -> void:
	checks[label]=ok
	if not ok: push_error(label)

func _initialize() -> void: call_deferred("run")

func carried_units_are_separate(world) -> bool:
	# Each X/Z seat holds only one material family, at every occupied level.
	var occupied := {}
	var families := {}
	for kind: String in Inventory.KINDS:
		var displayed := 0
		for packet: Node3D in world.carry.pieces.get("carry/" + kind, []):
			if not packet.is_visible_in_tree():
				continue
			if occupied.has(packet.position):
				return false
			occupied[packet.position] = kind
			var seat := Vector2(packet.position.x, packet.position.z)
			if families.has(seat) and families[seat] != kind:
				return false
			families[seat] = kind
			displayed += 1
		if displayed != int(world.inventory.carried[kind]):
			return false
	return true

func staged_ledger() -> Inventory:
	var ledger:=Inventory.new()
	ledger.configure(Rules.offers({"wood":3}))
	return ledger

func old_profile(directory:String) -> void:
	var ledger:=Inventory.new()
	ledger.configure(Rules.old_offers())
	for id: String in [Rules.HEARTH,Rules.FIRST,"storage_wood"]:
		for kind: String in ledger.costs[id]:
			for i in int(ledger.costs[id][kind]):
				ledger.collect("%s-%s-%d"%[id,kind,i],kind)
				ledger.payment(id,kind,false)
	ledger.collect("stocked-old-wood","wood")
	ledger.deposit("wood")
	ledger.collect("carried-old-wood","wood")
	ledger.collect("carried-old-stone","stone")
	var state:=ledger.snapshot()
	state.version=2
	state.erase("legacy_prices")
	state.erase("settlement")
	for kind in Inventory.MINERALS:
		state.stored.erase(kind)
		state.carried.erase(kind)
	var payload:=JSON.stringify(state)
	var file:=FileAccess.open(directory.path_join(Store.PRIMARY),FileAccess.WRITE)
	file.store_string(JSON.stringify({"format":1,"sha256":payload.sha256_text(),"payload":payload}))
	file.close()

func orchestrate() -> void:
	var profile := OS.get_temp_dir().path_join("havenline-l1-v3-minerals-%s-%s"%[OS.get_process_id(),Time.get_ticks_usec()])
	DirAccess.make_dir_absolute(profile)
	var marker:=FileAccess.open(profile.path_join(Store.Profile.SENTINEL),FileAccess.WRITE)
	marker.store_string(Store.Profile.MARK)
	marker.close()
	old_profile(profile)
	for mode in ["--mineral-migrate","--mineral-reopen"]:
		var out := []
		var code:=OS.execute(OS.get_executable_path(),PackedStringArray(["--headless","--path",ProjectSettings.globalize_path("res://"),"--script","res://qa_field_minerals.gd","--",Store.Profile.FLAG+profile,mode]),out,true)
		for line in out: print(line)
		check(mode,code==0)
	print(JSON.stringify(checks))
	quit(1 if false in checks.values() else 0)

func run() -> void:
	var args:=OS.get_cmdline_user_args()
	if "--mineral-migrate" not in args and "--mineral-reopen" not in args:
		orchestrate()
		return
	if not Store.Profile.new().requested(args) and not FileAccess.file_exists(OS.get_user_data_dir().path_join("MINERAL-QA")):
		push_error("Native mineral QA requires its own marked app-data directory.")
		quit(2)
		return
	var world=Scene.instantiate()
	root.add_child(world)
	world.set_physics_process(false)
	world.carry.set_physics_process(false)
	var ledger: Inventory=world.inventory
	check("normal scene save loaded",not world.persist_blocked)
	if "--mineral-migrate" in args:
		check("existing native receipts and zero minerals",ledger.complete("storage_wood") and Inventory.MINERALS.all(func(k):return ledger.carried[k]==0 and ledger.stored[k]==0))
		var before: Dictionary=ledger.paid.duplicate(true)
		for kind: String in SAMPLES:
			check(kind+" alone cannot pay for ordinary construction",not ledger.payment("expansion_2",kind,false))
			for i in int(SAMPLES[kind]):
				check(kind+" dispatches unique earned pickup "+str(i),world.carry.pickup("mine-qa-"+kind+str(i),kind,Vector3(2,0,1)))
			world.carry.advance(.4)
			check(kind+" separate backpack lane",carried_units_are_separate(world))
		check("visible six-material HUD and exact mineral counts",world.opening_hud.mineral_row.visible and Inventory.MINERALS.all(func(k):return int(world.opening_hud.numbers[k].text)==Rules.units(SAMPLES[k])))
		check("pickup preserves all existing receipts",before==ledger.paid)
		if not ledger.complete("storage_stone"):
			check("starter alone cannot bank ore",Inventory.MINERALS.all(func(k):return not world.carry.deposit_storage(k)))
			var attempts := 0
			for raw: String in ledger.remaining("storage_stone"):
				var remaining:int = ledger.remaining("storage_stone")[raw]
				attempts += remaining
				for n in maxi(0,remaining-ledger.carried[raw]-ledger.stored[raw]):
					ledger.collect("reinforce-%s-%d"%[raw,n],raw)
			for n in attempts:
				check("ordinary reinforced payment "+str(n),world.carry.contribute("storage_stone"))
				world.carry.advance(.4)
		var shelves := []
		for kind: String in SAMPLES:
			for i in int(SAMPLES[kind])-1:
				check(kind+" bank flight "+str(i),world.carry.deposit_storage(kind))
				var flight: Dictionary=world.carry.flights[0]
				world.carry.advance(.4)
				var pool: Array=world.carry.pieces["storage/"+kind]
				var target: Node3D=pool[mini(i,pool.size()-1)]
				check(kind+" landing meets its own bay",target.get_parent()==world.depot.bins[kind] and target.global_position.is_equal_approx(flight.mesh.global_position) and flight.kind==kind)
			var bay: Node3D=world.depot.bins[kind]
			check(kind+" distinct populated bin",not shelves.has(bay.global_position) and world.depot.labels[kind].text==str(Rules.units(SAMPLES[kind]-1)))
			shelves.append(bay.global_position)
		var damaged:=ledger.snapshot()
		damaged.stored.erase("slate")
		var unchanged:=ledger.snapshot()
		check("missing new balance rejected atomically",not ledger.restore(damaged) and ledger.snapshot()==unchanged)
	else:
		check("normal scene restored paid original order",ledger.complete("storage_stone") and ledger.snapshot().version==6)
		for kind: String in SAMPLES:
			check(kind+" typed balances reopen",ledger.carried[kind]==1 and ledger.stored[kind]==SAMPLES[kind]-1 and ledger.collected["mine-qa-"+kind+"0"]==kind and ledger.storage_open(kind))
			check(kind+" repeated token rejected",not world.carry.pickup("mine-qa-"+kind+"0",kind,Vector3.ZERO))
		print(JSON.stringify({"receipts":ledger.paid,"counts":{"carried":ledger.carried,"stored":ledger.stored},"schema":ledger.snapshot().version}))
	print(JSON.stringify(checks))
	world.sound.stop_playback()
	world.queue_free()
	for i in 4: await process_frame
	quit(1 if false in checks.values() else 0)
