extends SceneTree

const Ledger = preload("res://field_inventory.gd")
const Carry = preload("res://field_carry.gd")
const Art = preload("res://field_art.gd")
var failures: Array[String] = []
var grants: Array[String] = []
var arrivals := []

func _initialize() -> void:
	call_deferred("run")

func check(result: bool, label: String) -> void:
	if not result:
		failures.append(label)
		push_error(label)

func run() -> void:
	var offers := {"buy":{"wood":2, "stone":1, "meat":1}}
	var inventory := Ledger.new()
	check(inventory.configure(offers), "configure typed mixed cost")
	var carry := Carry.new()
	var actor := Node3D.new()
	root.add_child(actor)
	root.add_child(carry)
	carry.setup(inventory, actor, Art.make)
	carry.set_physics_process(false)
	for kind in Ledger.KINDS:
		var anchor := Node3D.new()
		root.add_child(anchor)
		anchor.position = Vector3(3 + 2*Ledger.KINDS.find(kind), 0, 0)
		carry.define_storage(kind, anchor)
	var buy := Node3D.new()
	root.add_child(buy)
	buy.position = Vector3(0, .1, 4)
	carry.define_receiver("buy", buy)
	carry.purchase_completed.connect(func(id): grants.append(id))
	carry.unit_landed.connect(func(kind, dest): arrivals.append([kind, dest]))
	for sample in [["T1","wood"],["T2","wood"],["R1","stone"],["R2","stone"],["T3","wood"]]:
		check(carry.pickup(sample[0],sample[1], Vector3(2,0,2)), "pickup "+sample[0])
	check(not carry.pickup("T1","meat",Vector3.ZERO), "unique source prevents grants across types")
	check(not carry.contribute("buy"), "in-air pickups unavailable to spend")
	actor.position += Vector3.RIGHT
	carry.advance(.31)
	check(arrivals.size()==5 and carry.flights.is_empty(), "pickups landed on moving actor")
	check(carry.pieces['carry/stone'][1].global_position.x>carry.pieces['carry/wood'][1].global_position.x, "wood and stone remain in distinct columns")
	check(not carry.deposit_storage("meat"), "empty plot does not dispatch")
	check(carry.deposit_storage("wood"), "first wood leaves for storage")
	var counter_before := inventory.snapshot()
	check(not carry.deposit_storage("wood"), "continuous overlap does not instantly redispatch")
	carry.advance(.17)
	check(carry.deposit_storage("wood"), "second wood flight after spacing")
	carry.advance(.31)
	check(inventory.stored.wood==2 and inventory.carried.wood==1, "two units now stored")
	check(counter_before.carried.wood==3 and counter_before.stored.wood==0, "snapshot mid-delivery retains sole ownership at source")
	var restored := Ledger.new()
	restored.configure(offers)
	check(restored.restore(JSON.parse_string(JSON.stringify(counter_before))), "interrupted activity can restore")
	check(carry.contribute("buy"), "first wood contribution from rack")
	carry.advance(.17)
	check(carry.contribute("buy"), "second wood contribution from storage")
	carry.advance(.17)
	check(carry.contribute("buy"), "stone contribution while second wood flies")
	carry.advance(.30)
	check(not inventory.complete("buy") and grants.is_empty(), "missing meat keeps buy concealed")
	check(inventory.paid.buy=={"wood":2,"stone":1,"meat":0}, "partial receipt exactly matches world arrivals")
	check(not carry.contribute("buy"), "surplus wood or stone cannot replace meat")
	var partial := inventory.snapshot()
	check(restored.restore(partial), "recover partial purchase")
	var corrupt := partial.duplicate(true)
	corrupt.paid.buy.wood=3
	check(not restored.restore(corrupt) and restored.snapshot()==partial, "reject overpayment without partial restore")
	corrupt=partial.duplicate(true)
	corrupt.stored.stone=1
	check(not restored.restore(corrupt), "reject invented storage quantity")
	check(carry.pickup("E1","meat",Vector3.ZERO),"enemy meat pickup")
	carry.advance(.4)
	check(carry.contribute("buy"),"last correct material dispatched")
	check(not inventory.complete("buy"), "remains concealed during final flight")
	carry.advance(.17)
	check(not carry.contribute("buy"),"final in-air contribution prevents double reservation")
	carry.advance(.31)
	check(grants==["buy"] and inventory.complete("buy"), "final arrival emits exactly one purchase")
	check(not carry.contribute("buy") and inventory.stored.wood==1 and inventory.carried.stone==1, "surplus retained and repeat denied")
	check(restored.restore(inventory.snapshot()) and restored.complete("buy"), "completed receipt survives restore")
	print(JSON.stringify({"failures":failures, "mesh_extents":carry.measured,"grants":grants,"arrivals":arrivals,"final":inventory.snapshot()}))
	quit(1 if not failures.is_empty() else 0)
