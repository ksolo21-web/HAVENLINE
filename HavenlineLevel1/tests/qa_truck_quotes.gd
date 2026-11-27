extends SceneTree

const Inventory = preload("res://field_inventory.gd")
const Progress = preload("res://field_progression.gd")
const STANDARD := {"wood":24,"stone":16}
const AUTOMATED := {"wood":30,"stone":20}
const OLD_STANDARD := {"wood":44,"stone":34,"metal":24,"coal":12}
const OLD_AUTOMATED := {"wood":50,"stone":38,"metal":26,"coal":12}
var checks := {}
var receipts := 0

func _initialize() -> void:
	var standard := camp()
	buy(standard,Progress.GARAGE)
	check("garage exposes the standard quote",standard.offer_open(Progress.TRUCK) and standard.remaining(Progress.TRUCK)==STANDARD)
	issue(standard,"wood",1)
	check("standard quote accepts its first payment",standard.payment(Progress.TRUCK,"wood",false))
	for id: String in Progress.LINES: buy(standard,id)
	check("later automation leaves the exposed quote and tender intact",standard.costs[Progress.TRUCK]==STANDARD and standard.remaining(Progress.TRUCK).wood==23)
	var saved: Dictionary = standard.snapshot()
	check("existing quote and partial payment restore",read(saved) and read(saved).remaining(Progress.TRUCK).wood==23)
	saved.settlement.erase("truck_quote")
	check("pre-quote funded save retains the original bill",read(saved) and read(saved).costs[Progress.TRUCK]==STANDARD)
	saved.settlement.truck_quote = "automated"
	check("later construction cannot forge an earlier automated quote",not read(saved))

	var automated := camp()
	for id: String in Progress.LINES: buy(automated,id)
	buy(automated,Progress.GARAGE)
	check("an already automated camp receives the advanced quote",automated.offer_open(Progress.TRUCK) and automated.remaining(Progress.TRUCK)==AUTOMATED)
	saved = automated.snapshot()
	check("unfunded quote survives reload at first exposure",read(saved) and read(saved).remaining(Progress.TRUCK)==AUTOMATED)
	saved.settlement.erase("truck_quote")
	check("earlier v11 saves with the same installed lines keep the price they were shown",read(saved) and read(saved).remaining(Progress.TRUCK)==STANDARD)
	issue(automated,"wood",25)
	check("advanced quote accepts tender beyond the default bill",automated.payment(Progress.TRUCK,"wood",false,25))
	check("advanced tender and five-unit remainder restore",read(automated.snapshot()) and read(automated.snapshot()).remaining(Progress.TRUCK).wood==5)
	buy(automated,Progress.TRUCK)
	var vehicle: Dictionary = automated.vehicle_state()
	vehicle.hp = 40
	vehicle.purchases = 1
	check("completed purchase conserves the advanced receipt",read(automated.snapshot()) and read(automated.snapshot()).complete(Progress.TRUCK))
	check("wreck is an eligible replacement",automated.vehicle_wreck(false))
	for kind: String in STANDARD: issue(automated,kind,STANDARD[kind])
	check("replacement honors the same quote instead of charging the default",not automated.vehicle_repurchase() and automated.carried.wood==STANDARD.wood)
	for kind: String in AUTOMATED: issue(automated,kind,AUTOMATED[kind]-STANDARD[kind])
	check("complete replacement payment spends the exact quoted goods",automated.vehicle_repurchase() and vehicle.spent==AUTOMATED)
	vehicle.hp = 40
	check("replacement and original bill round-trip together",read(automated.snapshot()) and read(automated.snapshot()).vehicle_state().purchases==2)
	var old := camp(true)
	for id: String in Progress.LINES: buy(old,id)
	buy(old,Progress.GARAGE)
	check("legacy automated price matches the old build",old.remaining(Progress.TRUCK)==OLD_AUTOMATED)
	var tender := {"wood":50,"stone":14,"metal":9,"coal":2}
	for kind: String in tender:
		issue(old,kind,tender[kind])
		assert(old.payment(Progress.TRUCK,kind,false,tender[kind]))
	saved = old.snapshot()
	saved.version = 12
	var migrated := read(saved)
	check("old pending truck refunds every material once and opens the new raw quote",migrated and migrated.remaining(Progress.TRUCK)==AUTOMATED and migrated.offer_open(Progress.TRUCK) and migrated.carried=={"wood":50,"stone":14,"meat":0,"coal":2,"slate":0,"metal":9})
	check("reopening a migrated save does not refund a second time",migrated and read(migrated.snapshot()) and read(migrated.snapshot()).carried==migrated.carried)
	var invalid := saved.duplicate(true)
	invalid.paid.snow_truck.metal=27
	check("legacy tender outside the old quote is rejected",not read(invalid))
	buy(old,Progress.TRUCK)
	old.vehicle_state().purchases = 1
	old.vehicle_state().hp = 80
	saved = old.snapshot()
	saved.version = 12
	migrated = read(saved)
	check("completed legacy vehicle keeps its exact receipt and state",migrated and migrated.complete(Progress.TRUCK) and migrated.paid.snow_truck==OLD_AUTOMATED and migrated.vehicle_state().hp==80 and read(migrated.snapshot()))
	check("legacy truck can be wrecked",migrated and migrated.vehicle_wreck(false))
	if migrated:
		for kind: String in AUTOMATED:
			issue(migrated,kind,AUTOMATED[kind])
			assert(migrated.deposit(kind,AUTOMATED[kind]))
		check("legacy truck can be replaced using the storehouse and playtest quote",migrated.vehicle_repurchase() and migrated.vehicle_state().spent==AUTOMATED and migrated.stored.wood==0 and migrated.stored.stone==0)
		migrated.vehicle_state().hp = 80
		check("legacy truck replacement finalizes on reload",read(migrated.snapshot()) and read(migrated.snapshot()).vehicle_state().purchases==2)
	print("TRUCK_QUOTE ",JSON.stringify(checks))
	quit(1 if false in checks.values() else 0)

func check(label: String, valid: bool) -> void:
	checks[label] = valid
	if not valid: push_error(label)

func new_ledger(legacy := false) -> Inventory:
	var ledger := Inventory.new()
	var offers := Progress.offers()
	if legacy: offers[Progress.TRUCK] = OLD_STANDARD.duplicate()
	assert(ledger.configure(offers))
	return ledger

func camp(legacy := false) -> Inventory:
	var ledger := new_ledger(legacy)
	for id: String in [Progress.HEARTH,Progress.FIRST,"storage_wood","storage_stone","storage_meat",Progress.SECOND,"camp_cooker","saw_bench","quarry_drill"]:
		buy(ledger,id)
	return ledger

func read(snapshot: Dictionary) -> Inventory:
	var ledger := new_ledger()
	return ledger if ledger.restore(JSON.parse_string(JSON.stringify(snapshot))) else null

func issue(ledger: Inventory, kind: String, amount: int) -> void:
	for unit in amount:
		receipts += 1
		assert(ledger.collect("quote-payment-%d" % receipts,kind))

func buy(ledger: Inventory, id: String) -> void:
	var due: Dictionary = ledger.remaining(id)
	for kind: String in due:
		var amount: int = due[kind]
		if amount == 0: continue
		if kind in ["planks","blocks"]:
			var input := "wood" if kind == "planks" else "stone"
			issue(ledger,input,amount)
			ledger.carried[input] -= amount
			ledger.settlement["processed_"+input] += amount
			ledger.settlement.hand_products[kind] += amount
		else:
			issue(ledger,kind,amount)
		assert(ledger.payment(id,kind,false,amount))
	assert(ledger.complete(id))
