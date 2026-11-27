extends SceneTree
## Inventory-only coverage. No filesystem profile or production scene is opened.
const Ledger = preload("res://field_inventory.gd")
const Progress = preload("res://field_progression.gd")
const Rules = preload("res://field_settlement.gd")
const PURCHASE_ORDER = ["center_hearth","expansion_1","storage_wood","storage_stone","storage_meat","expansion_2","camp_cooker","saw_bench","quarry_drill"]
var checks := {}
var failures: Array[String] = []

func check(label: String, ok: bool) -> void:
	checks[label] = ok
	if not ok:
		failures.append(label)
		push_error(label)

func blank():
	var book = Ledger.new()
	book.configure(Progress.offers({"wood":3}))
	return book

func _initialize() -> void:
	var book = blank()
	var candidate = blank()
	for id: String in PURCHASE_ORDER:
		for kind: String in book.remaining(id):
			for n in int(book.remaining(id)[kind]):
				book.collect("%s-%s-%d"%[id,kind,n],kind)
				book.payment(id,kind,false)
	for kind: String in Rules.KINDS:
		for i in (8 + book.survivor_cost if kind=="wood" else 8): book.collect("trial-%s-%d"%[kind,i],kind)
	var journal: Dictionary = book.settlement
	for kind: String in Rules.KINDS:
		book.carried[kind] -= 2
		journal.hoppers[kind] = 2
		journal.work_seconds[kind] = .42
	journal.survivor_paid = true
	journal.survivor_wood = book.survivor_cost
	journal.rescued = true
	book.carried.wood -= book.survivor_cost
	book.carried.stone -= 1
	journal.worker_supply = "stone"
	var queued: Dictionary = JSON.parse_string(JSON.stringify(book.snapshot()))
	check("concurrent hopper and courier cargo conserve raw balances",candidate.restore(queued))
	check("partial machine time and airborne delivery survive JSON",candidate.settlement.work_seconds==journal.work_seconds and candidate.settlement.worker_supply=="stone")
	var stable: Dictionary = candidate.snapshot()
	var forged: Dictionary = queued.duplicate(true)
	forged.settlement.hoppers.wood -= 1
	check("missing hopper input rejected",not candidate.restore(forged) and candidate.snapshot()==stable)
	forged = queued.duplicate(true)
	forged.settlement.worker_supply = "meat"
	check("courier cannot change material type in transit",not candidate.restore(forged) and candidate.snapshot()==stable)
	forged = queued.duplicate(true)
	forged.settlement.worker_carry_token = "wood-303"
	check("courier hands cannot hold two jobs",not candidate.restore(forged))
	forged = queued.duplicate(true)
	forged.settlement.hoppers.wood = 5
	forged.carried.wood -= 3
	check("five loaded units rejected even if all are earned",not candidate.restore(forged))
	forged = queued.duplicate(true)
	forged.settlement.work_seconds.stone = 2
	check("future machine time rejected",not candidate.restore(forged))
	forged = queued.duplicate(true)
	forged.settlement.hoppers.wood = 0
	forged.carried.wood += 2
	check("an empty machine cannot bank work time",not candidate.restore(forged))
	journal.worker_supply = ""
	book.stored.stone += 1
	for kind: String in Rules.KINDS:
		journal.hoppers[kind] = 0
		journal.work_seconds[kind] = 0.0
		if kind == "meat":
			journal.cooked = 2
		else:
			journal["processed_"+kind] = 2
	check("finished two lots of every material and returned courier stock",candidate.restore(book.snapshot()))
	journal.held_meal = 1
	check("one roast on rack and one held",Rules.waiting_meals(journal)==1 and candidate.restore(book.snapshot()))
	journal.served += 1
	journal.held_meal = 0
	check("sale removes exactly the held roast",Rules.waiting_meals(journal)==1 and candidate.restore(book.snapshot()))
	var old: Dictionary = book.snapshot()
	old.version = 4
	old.erase("legacy_prices")
	old.erase("legacy_level2")
	var old_prices := Progress.old_offers()
	# The station purchases did not exist in v4. Return those debits to the
	# earned stock before recreating its actual eight-offer ledger.
	for id: String in Progress.MACHINES.values()+Progress.LINES:
		for kind: String in old.paid[id]:
			old.carried[kind] += old.paid[id][kind]
		old.paid.erase(id)
		old.build_order.erase(id)
	for id: String in old.build_order:
		for kind: String in old.paid[id]:
			old.carried[kind] += old.paid[id][kind] - old_prices[id][kind]
		old.paid[id] = old_prices[id].duplicate()
	old.carried.wood += old.settlement.survivor_wood - Progress.OLD_SURVIVOR_BUNDLES
	old.settlement.survivor_wood = Progress.OLD_SURVIVOR_BUNDLES
	for key in old.settlement.keys():
		if not Rules.LEGACY.has(key): old.settlement.erase(key)
	check("an old unserved receipt migrates onto its previous carrier",candidate.restore(JSON.parse_string(JSON.stringify(old))) and candidate.settlement.held_meal==1 and Rules.waiting_meals(candidate.settlement)==0)
	old.settlement.served = 0
	check("a forged old save cannot manufacture an extra carried meal",not candidate.restore(old))
	journal.cooked = 6
	book.carried.meat -= 4
	check("four-slot roast rack stops excess finished stock",not candidate.restore(book.snapshot()))
	journal.held_meal = 1
	check("four on rack and one held is valid",candidate.restore(book.snapshot()) and Rules.waiting_meals(journal)==4)
	print("CAMP_PRODUCTION_BALANCES ",JSON.stringify({"checks":checks,"failures":failures}))
	quit(0 if failures.is_empty() else 1)
