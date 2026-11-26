extends SceneTree

const Inventory = preload("res://field_inventory.gd")
const Rules = preload("res://field_progression.gd")
const Save = preload("res://field_save.gd")
var checks := {}
var serial := 0

func ledger() -> Inventory:
	var result := Inventory.new()
	result.configure(Rules.offers({"wood":3}))
	return result

func fund(book: Inventory,id: String) -> bool:
	for kind in book.remaining(id):
		for _i in int(book.remaining(id)[kind]):
			serial += 1
			book.collect("grant-"+str(serial),kind)
			if not book.payment(id,kind,false): return false
	return book.complete(id)

func check(key: String, ok: bool) -> void:
	checks[key]=ok
	if not ok: push_error(key)

func _initialize() -> void:
	var args := OS.get_cmdline_user_args()
	if "--native-read" in args or "--native-write" in args:
		var db := Save.new()
		var book := ledger()
		if not db.configure(PackedStringArray()): quit(1); return
		if "--native-write" in args:
			var ok := db.load_into(book)==ERR_FILE_NOT_FOUND and fund(book,Rules.HEARTH) and db.commit(book)==OK
			quit(0 if ok else 1)
		else:
			quit(0 if db.load_into(book)==OK and book.build_order==[Rules.HEARTH] else 1)
		return
	for sequence in [["storage_meat","storage_wood","storage_stone"],["storage_stone","storage_meat","storage_wood"]]:
		var book := ledger()
		book.collect("plenty","wood")
		check("No premature purchase or deposit "+sequence[0], not book.payment(Rules.FIRST,"wood",false) and not book.deposit("wood"))
		check("Paid hearth alone opens only expansion "+sequence[0],fund(book,Rules.HEARTH) and Rules.stage(book)==1 and book.offer_open(Rules.FIRST) and not book.offer_open(sequence[0]))
		check("Expansion opens three independent plots "+sequence[0],fund(book,Rules.FIRST) and Rules.stage(book)==2 and Rules.STORAGE.all(func(id):return book.offer_open(id)))
		var order := [Rules.HEARTH, Rules.FIRST]
		for id in sequence:
			book.collect("partial-"+id,"wood")
			check(id+" partial "+sequence[0],book.payment(id,"wood",false))
			var fresh := ledger()
			check(id+" partial reload "+sequence[0],fresh.restore(book.snapshot()) and fresh.snapshot()==book.snapshot())
			book=fresh
			check(id+" purchase "+sequence[0],fund(book,id))
			order.append(id)
			check(id+" remains owned "+sequence[0],book.build_order==order and book.storage_open(id.trim_prefix("storage_")))
			check(id+" cannot be bought twice "+sequence[0],not book.payment(id,"wood",false))
		check("Tower and axes wait for expansion2 "+sequence[0],not book.offer_open(Rules.TOWER) and not book.offer_open(Rules.AXES) and book.offer_open(Rules.SECOND))
		check("Build both beyond stage3 "+sequence[0],fund(book,Rules.SECOND) and Rules.stage(book)==3 and fund(book,Rules.TOWER) and fund(book,Rules.AXES))
		check("Reject reordered completion "+sequence[0],tampered_order_rejected(book))
	var old := Inventory.new()
	old.configure({"center_hearth":{"wood":3},"orbit_upgrade":{"stone":2,"meat":1}})
	fund(old,Rules.HEARTH)
	fund(old,Rules.AXES)
	old.collect("old-stored","meat")
	old.deposit("meat")
	var modern:=ledger()
	check("Migrate funded old axes and exact balances",modern.restore(old.snapshot()) and modern.complete(Rules.AXES) and modern.build_order==[Rules.HEARTH,Rules.AXES] and modern.stored.meat==1 and modern.remaining(Rules.FIRST).wood==3)
	check("Migration cannot spend unavailable stock",not modern.payment("storage_meat","meat",true))
	var restored:=ledger()
	check("Migrated equipment purchase order round-trips",restored.restore(modern.snapshot()) and restored.snapshot()==modern.snapshot())
	var path := "/tmp/havenline-l1-v3-worldqa-" + str(OS.get_process_id()) + "-" + str(Time.get_ticks_usec())
	DirAccess.make_dir_absolute(path)
	var marker := FileAccess.open(path.path_join(Save.Profile.SENTINEL),FileAccess.WRITE)
	marker.store_string(Save.Profile.MARK)
	marker.close()
	var opts := PackedStringArray([Save.Profile.FLAG + path])
	var previous := Save.new()
	var next := Save.new()
	var fresh := ledger()
	check("Original field save written through old schema",previous.configure(opts) and previous.commit(old)==OK)
	check("Existing field save reopens through modern migration",next.configure(opts) and next.load_into(fresh)==OK and fresh.snapshot()==modern.snapshot())
	fund(fresh,Rules.FIRST)
	check("Post-migration stage commits atomically",next.commit(fresh)==OK)
	var restarted:=ledger()
	check("Reload retains grandfathered equipment, stock and new stage",next.load_into(restarted)==OK and restarted.snapshot()==fresh.snapshot())
	var dir:=DirAccess.open(path)
	dir.remove(Save.PRIMARY)
	dir.remove(Save.Profile.SENTINEL)
	DirAccess.remove_absolute(path)
	print(JSON.stringify(checks))
	quit(0 if not false in checks.values() else 1)

func tampered_order_rejected(book:Inventory) -> bool:
	var corrupt:=book.snapshot()
	corrupt.build_order.reverse()
	var before:=book.snapshot()
	return not book.restore(corrupt) and before==book.snapshot()
