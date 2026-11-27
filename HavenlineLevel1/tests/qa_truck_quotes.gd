extends SceneTree

const Inventory = preload("res://field_inventory.gd")
const Progress = preload("res://field_progression.gd")
const STANDARD := {"wood":44,"stone":34,"metal":24,"coal":12}
const AUTOMATED := {"wood":50,"stone":38,"metal":26,"coal":12}
var checks := {}
var receipts := 0

func _initialize() -> void:
	var standard := camp()
	buy(standard,Progress.GARAGE)
	check("garage exposes the standard quote",standard.offer_open(Progress.TRUCK) and standard.remaining(Progress.TRUCK)==STANDARD)
	issue(standard,"wood",1)
	check("standard quote accepts its first payment",standard.payment(Progress.TRUCK,"wood",false))
	for id: String in Progress.LINES: buy(standard,id)
	check("later automation leaves the exposed quote and tender intact",standard.costs[Progress.TRUCK]==STANDARD and standard.remaining(Progress.TRUCK).wood==43)
	var saved: Dictionary = standard.snapshot()
	check("existing quote and partial payment restore",read(saved) and read(saved).remaining(Progress.TRUCK).wood==43)
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
	issue(automated,"wood",45)
	check("advanced quote accepts tender beyond the default bill",automated.payment(Progress.TRUCK,"wood",false,45))
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
	print("TRUCK_QUOTE ",JSON.stringify(checks))
	quit(1 if false in checks.values() else 0)

func check(label: String, valid: bool) -> void:
	checks[label] = valid
	if not valid: push_error(label)

func new_ledger() -> Inventory:
	var ledger := Inventory.new()
	assert(ledger.configure(Progress.offers()))
	return ledger

func camp() -> Inventory:
	var ledger := new_ledger()
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
