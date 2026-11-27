extends SceneTree

const Inventory = preload("res://field_inventory.gd")
const Progress = preload("res://field_progression.gd")
const Market = preload("res://field_market.gd")
const RAW := {"wood":18,"stone":12}
var checks := {}
var issued := 0

func _initialize() -> void:
	var stock := camp(false)
	check("new garage accepts ordinary wood and stone before any machines",stock.remaining(Progress.GARAGE)==RAW and stock.offer_open(Progress.GARAGE) and not stock.is_machine_owned("wood") and not stock.is_machine_owned("stone"))
	for kind: String in RAW:
		gather(stock,kind,RAW[kind])
		assert(stock.payment(Progress.GARAGE,kind,false,RAW[kind]))
	check("raw payment opens the truck and reopens at exact balances",stock.complete(Progress.GARAGE) and stock.offer_open(Progress.TRUCK) and read(stock.snapshot()) != null)

	var old := camp(true)
	var empty := read(build14(old))
	check("unfunded old garage gets the new raw quote",empty != null and empty.remaining(Progress.GARAGE)==RAW)
	put_processed(old,"planks",12)
	put_processed(old,"blocks",5)
	historic_market(old)
	var saved := build14(old)
	check("obsolete Build14 mixed quote cannot collect payment",not Market.sell(saved.settlement,11) and saved.settlement.market.earned==12)
	var resumed := read(saved)
	check("partly funded processed quote credits matching whole raw bundles",resumed != null and resumed.remaining(Progress.GARAGE)=={"wood":9,"stone":9})
	if resumed == null:
		finish()
		return
	check("legacy products still have actual construction receipt lines",resumed.paid.snow_garage=={"wood":0,"stone":0,"planks":12,"blocks":5} and resumed.settlement.market.construction_products=={"planks":12,"blocks":5})
	check("migration retires the single unsold quote and keeps financial history",resumed.settlement.market.order.is_empty() and resumed.settlement.served==10 and resumed.till_balance()==5 and resumed.settlement.market.earned == 12 and resumed.settlement.market.sold == {"meal":10,"planks":1,"blocks":0})
	check("all prior finished-goods accounts remain intact",resumed.settlement.market.counter_products=={"planks":1,"blocks":1} and resumed.settlement.product_store.planks==1 and resumed.settlement.hand_products=={"planks":1,"blocks":1})
	resumed.settlement.market.order = Market.new_order(11,1)
	check("next customer takes only a meal and pays only its price",Market.sell(resumed.settlement,11) and resumed.settlement.market.earned==13 and resumed.till_balance()==6 and resumed.settlement.market.counter_products.blocks==1)
	for kind: String in RAW:
		var due: int = resumed.remaining(Progress.GARAGE)[kind]
		gather(resumed,kind,due)
		assert(resumed.payment(Progress.GARAGE,kind,false,due))
	var reopened := read(resumed.snapshot())
	check("converted contract finalizes once and cold-reopens paid",reopened != null and reopened.snapshot().version==13 and reopened.complete(Progress.GARAGE) and reopened.offer_open(Progress.TRUCK) and reopened.paid.snow_garage=={"wood":9,"stone":9,"planks":12,"blocks":5})
	var forged := resumed.snapshot()
	forged.paid.snow_garage.planks += 1
	check("processed credits cannot be fabricated on an existing receipt",read(forged)==null)
	forged = resumed.snapshot()
	forged.settlement.market.order = {"id":12,"price":3,"goods":{"meal":1,"blocks":1}}
	check("current saves reject a new mixed order",read(forged)==null)

	old = camp(true)
	put_processed(old,"planks",23)
	put_processed(old,"blocks",19)
	resumed = read(build14(old))
	check("unpaid fractions keep near-complete legacy contract open",resumed != null and resumed.remaining(Progress.GARAGE)=={"wood":1,"stone":1} and not resumed.complete(Progress.GARAGE))
	put_processed(old,"planks",1)
	put_processed(old,"blocks",1)
	resumed = read(build14(old))
	check("fully paid Build14 garage keeps original processed receipt and truck eligibility",resumed != null and resumed.complete(Progress.GARAGE) and resumed.offer_open(Progress.TRUCK) and resumed.paid.snow_garage==Inventory.LEGACY_GARAGE_BILL and read(resumed.snapshot())!=null)
	finish()

func check(label: String, result: bool) -> void:
	checks[label] = result
	if not result: push_error(label)

func finish() -> void:
	print("BUILD15_ECONOMY ",JSON.stringify(checks))
	quit(1 if false in checks.values() else 0)

func read(snapshot: Dictionary) -> Inventory:
	var ledger := Inventory.new()
	assert(ledger.configure(Progress.offers()))
	return ledger if ledger.restore(JSON.parse_string(JSON.stringify(snapshot))) else null

func gather(ledger: Inventory, kind: String, amount: int) -> void:
	for unit in amount:
		issued += 1
		assert(ledger.collect("build15-economy-%d" % issued,kind))

func camp(legacy: bool) -> Inventory:
	var costs := Progress.offers()
	if legacy: costs[Progress.GARAGE] = Inventory.LEGACY_GARAGE_BILL
	var ledger := Inventory.new()
	assert(ledger.configure(costs))
	for id: String in [Progress.HEARTH,Progress.FIRST,"storage_wood","storage_stone","storage_meat",Progress.SECOND]:
		for kind: String in ledger.remaining(id):
			var quantity: int = ledger.remaining(id)[kind]
			gather(ledger,kind,quantity)
			assert(ledger.payment(id,kind,false,quantity))
	return ledger

func build14(ledger: Inventory) -> Dictionary:
	var state := ledger.snapshot()
	state.version = 11
	return state

func process_stock(ledger: Inventory, raw: String, quantity: int) -> void:
	gather(ledger,raw,quantity)
	ledger.carried[raw] -= quantity
	ledger.settlement["cooked" if raw=="meat" else "processed_"+raw] += quantity

func put_processed(ledger: Inventory, product: String, quantity: int) -> void:
	process_stock(ledger,"wood" if product=="planks" else "stone",quantity)
	ledger.settlement.hand_products[product] += quantity
	assert(ledger.payment(Progress.GARAGE,product,false,quantity))

func historic_market(ledger: Inventory) -> void:
	process_stock(ledger,"meat",12)
	process_stock(ledger,"wood",4)
	process_stock(ledger,"stone",2)
	var journal := ledger.settlement
	journal.served = 10
	journal.held_meal = 1
	journal.counter_stock = 1
	journal.market.sold = {"meal":10,"planks":1,"blocks":0}
	journal.market.earned = 12
	journal.market.counter_cash = 5
	journal.pocket_cash = 4
	journal.house_cash = 3
	journal.market.counter_products = {"planks":1,"blocks":1}
	journal.product_store.planks = 1
	journal.hand_products = {"planks":1,"blocks":1}
	journal.market.order = {"id":11,"goods":{"meal":1,"blocks":1},"price":3}
