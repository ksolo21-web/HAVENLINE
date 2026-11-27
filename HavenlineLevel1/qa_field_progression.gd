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
	test_price_contracts()
	var staged := ledger()
	check("No premature storage purchase",not staged.offer_open("storage_wood") and not staged.deposit("wood"))
	check("Hearth opens only expansion",fund(staged,Rules.HEARTH) and staged.offer_open(Rules.FIRST))
	check("First expansion opens only starter house",fund(staged,Rules.FIRST) and Rules.next_storage(staged)=="storage_wood" and not staged.offer_open("storage_stone"))
	for id: String in Rules.STORAGE:
		check("Insufficient funds "+id,not staged.payment(id,"wood",false))
		staged.collect("partial-"+id,"wood")
		check("Partial payment "+id,staged.payment(id,"wood",false))
		var fresh := ledger()
		check("Resume partial "+id,fresh.restore(staged.snapshot()) and fresh.snapshot()==staged.snapshot())
		staged=fresh
		check("Built "+id,fund(staged,id) and staged.storage_open(id.trim_prefix("storage_")))
		check("No duplicate debit "+id,not staged.payment(id,"wood",false))
	check("East expansion unlocks after all 3 tiers",staged.offer_open(Rules.SECOND) and not staged.offer_open(Rules.TOWER))
	check("Retains tier and downstream goals",fund(staged,Rules.SECOND) and fund(staged,Rules.TOWER) and fund(staged,Rules.AXES) and Rules.house_tier(staged)==3)
	check("Reject reordered unrelated completion",tampered_order_rejected(staged))
	# The original v2 schema let all 3 corners be purchased after expansion 1.
	# Reproduce a mixed historical ledger with meat owned and stone part-funded.
	var history := Inventory.new()
	history.configure(_former_recipes())
	fund(history,Rules.HEARTH)
	fund(history,Rules.FIRST)
	history.staged = false
	fund(history,"storage_meat")
	history.build_order.append("storage_meat")
	history.collect("old-partial-stone","wood")
	history.payment("storage_stone","wood",false)
	history.collect("old-meat","meat")
	history.deposit("meat")
	history.staged = true
	var original := historical_snapshot(history)
	original.version=3
	original.erase("legacy_prices")
	original.erase("settlement")
	var migrated := ledger()
	check("Historical out-of-order purchase and partial retained",migrated.restore(original) and original_receipts_equal(migrated.paid,original.paid) and migrated.build_order==original.build_order and migrated.remaining("storage_wood")==Rules.OFFERS.storage_wood)
	check("Visual tier independent from earned bays",Rules.house_tier(migrated)==3 and migrated.storage_open("meat") and not migrated.storage_open("wood") and not migrated.storage_open("stone"))
	check("Historical missing tiers funded in order",Rules.next_storage(migrated)=="storage_wood" and fund(migrated,"storage_wood") and migrated.remaining("storage_stone").wood==1 and fund(migrated,"storage_stone"))
	check("No historical double charge",migrated.stored.meat==1 and migrated.complete("storage_meat") and not migrated.offer_open("storage_meat") and migrated.offer_open(Rules.SECOND))
	var old := Inventory.new()
	old.configure({"center_hearth":{"wood":3},"orbit_upgrade":{"stone":2,"meat":1}})
	fund(old,Rules.HEARTH)
	fund(old,Rules.AXES)
	old.collect("old-stored","meat")
	old.deposit("meat")
	var modern:=ledger()
	check("Migrate funded old axes and exact balances",modern.restore(old.snapshot()) and modern.complete(Rules.AXES) and modern.build_order==[Rules.HEARTH,Rules.AXES] and modern.stored.meat==1 and modern.remaining(Rules.FIRST)==Rules.OFFERS[Rules.FIRST])
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

func _former_recipes() -> Dictionary:
	var offers := Rules.offers()
	offers.merge(Rules.old_offers(), true)
	return offers

func historical_snapshot(book: Inventory) -> Dictionary:
	var state := book.snapshot()
	state.erase("legacy_level2")
	for id in Rules.MACHINES.values()+Rules.LINES: state.paid.erase(id)
	for key in ["line_load","line_progress","counter_stock","product_store","dispatch_cursor"]: state.settlement.erase(key)
	state.settlement.erase("worker_load")
	state.settlement.erase("worker_meal")
	return state

func original_receipts_equal(new_paid: Dictionary, old_paid: Dictionary) -> bool:
	return old_paid.keys().all(func(id): return new_paid.get(id) == old_paid[id]) and Rules.MACHINES.values().all(func(id): return new_paid[id].values().all(func(count): return count == 0))

func test_price_contracts() -> void:
	# This is the shape and the 3/2 timber price schedule actually saved by
	# the Fold checkpoint. Keep fractional projects as receipts, not grants.
	for survivor_paid in [0,1,2]:
		var old := Inventory.new()
		old.configure(_former_recipes())
		fund(old,Rules.HEARTH)
		old.collect("old-expansion","wood")
		old.payment(Rules.FIRST,"wood",false)
		for n in survivor_paid:
			old.collect("rescue-%s"%n,"wood")
			old.carried.wood -= 1
		old.settlement.survivor_wood = survivor_paid
		old.settlement.survivor_paid = survivor_paid == 2
		var original := historical_snapshot(old)
		original.version = 5
		original.erase("legacy_prices")
		var upgraded := ledger()
		check("v5 partial expansion and earned camp migrate, survivor %s"%survivor_paid,
			upgraded.restore(JSON.parse_string(JSON.stringify(original))) and upgraded.complete(Rules.HEARTH)
			and upgraded.remaining(Rules.FIRST)=={"wood":2,"stone":1} and upgraded.remaining("storage_wood")==Rules.OFFERS.storage_wood
			and original_receipts_equal(upgraded.paid,original.paid) and upgraded.carried==old.carried and upgraded.collected==old.collected)
		check("v5 survivor contract and payment state retained, receipt %s"%survivor_paid,
			upgraded.survivor_cost==(Rules.SURVIVOR_BUNDLES if survivor_paid==0 else Rules.OLD_SURVIVOR_BUNDLES)
			and upgraded.settlement.survivor_wood==survivor_paid and upgraded.settlement.survivor_paid==(survivor_paid==2))
		var valid := upgraded.snapshot()
		var reopened := ledger()
		check("json round-trip of funded price locks %s"%survivor_paid,reopened.restore(JSON.parse_string(JSON.stringify(valid))) and reopened.snapshot()==valid)
		for invalid in ["storage_stone",Rules.HEARTH,"unknown"]:
			var forged := valid.duplicate(true)
			forged.legacy_prices.append(invalid)
			check("reject unauthorized or doubled price lock %s %s"%[invalid,survivor_paid],not reopened.restore(forged) and reopened.snapshot()==valid)
	var old := Inventory.new()
	old.configure(_former_recipes())
	old.collect("first-installment","wood")
	old.payment(Rules.HEARTH,"wood",false)
	var partial := historical_snapshot(old)
	partial.version = 3
	partial.erase("legacy_prices")
	partial.erase("settlement")
	var upgraded := ledger()
	check("old partially paid hearth still owes two packets",upgraded.restore(partial) and upgraded.remaining(Rules.HEARTH)=={"wood":2} and not upgraded.complete(Rules.HEARTH))
	check("old partial finishes without windfall; next expansion charges new price",fund(upgraded,Rules.HEARTH) and upgraded.collected.size()==3 and upgraded.remaining(Rules.FIRST)==Rules.OFFERS[Rules.FIRST])
	var clean := ledger()
	var old_blank := Inventory.new()
	old_blank.configure(_former_recipes())
	var no_receipts := historical_snapshot(old_blank)
	no_receipts.version = 3
	no_receipts.erase("legacy_prices")
	no_receipts.erase("settlement")
	check("unstarted old install sees the same 200 timber as fresh",clean.restore(no_receipts) and Rules.units(clean.remaining(Rules.HEARTH).wood)==200 and clean.legacy_prices.is_empty())
