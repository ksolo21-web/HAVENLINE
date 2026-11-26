extends Node3D

const House = preload("res://field_storage_house.gd")
const Rules = preload("res://field_progression.gd")
const Layout = preload("res://field_stock_layout.gd")
const Offer = preload("res://field_offer_floor.gd")
const SITE := Vector3(-3.05,0,-3.45)
const APRON := Vector3(-3.05,0,-1.18)
const BIN_SCALE := .38
const BALANCE_PIXEL_SIZE := .0046
var house
var apron: Node3D
var shelves := Node3D.new()
var bins := {}
var labels := {}
var visit := ""
var offer := ""
var world

func install(host) -> void:
	world = host
	house = House.new()
	house.name = "NorthwestStorehouse"
	add_child(house)
	house.position = SITE
	house.configure(world.actor)
	house.door_motion.connect(func(opening:bool, at:Vector3):
		world._event("gate" if opening else "gate_latch",at))
	add_child(shelves)
	for kind: String in world.Inventory.KINDS:
		var bin := Node3D.new()
		bin.name = kind.capitalize()+"Shelf"
		shelves.add_child(bin)
		bin.global_position = house.bay_position(kind)
		bins[kind] = bin
		world.carry.define_storage(kind,bin)
		var label: Label3D = world.field_env.flat_label(bin,Vector3.ZERO,BALANCE_PIXEL_SIZE)
		label.rotation = Vector3.ZERO
		label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
		label.global_position = house.bay_label_position(kind)
		labels[kind] = label
	apron = Offer.new()
	add_child(apron)
	apron.install(world.field_env,Rules.STORAGE[0],APRON)
	apron.name = "StorehouseApron"
	for id: String in Rules.STORAGE:
		world.carry.define_receiver(id,apron)
	world.carry.set_storage_layout(landing_position,BIN_SCALE)

func landing_position(kind: String, index: int) -> Vector3:
	return bins[kind].to_global(Layout.position(kind,index)*BIN_SCALE)

func at_apron(at:Vector3) -> bool:
	return Vector2(at.x,at.z).distance_squared_to(Vector2(APRON.x,APRON.z)) <= 1.0

func refresh(active: bool) -> void:
	var ledger = world.inventory
	var tier: int = Rules.house_tier(ledger) if active else 0
	house.update_state(tier, ledger.stored)
	offer = Rules.next_storage(ledger) if active else ""
	apron.visible = active and ledger.complete(Rules.FIRST)
	if apron.visible:
		apron.set_depot(ledger,offer,tier > 0)
	for kind: String in bins:
		bins[kind].visible = active and ledger.storage_open(kind)
		var label: Label3D = labels[kind]
		label.text = shelf_quantity(Rules.units(ledger.stored[kind]))
		label.pixel_size = BALANCE_PIXEL_SIZE * minf(1.0, 3.25 / label.text.length())
	_update_interior()

func _process(_dt:float) -> void:
	if house: _update_interior()

func _update_interior() -> void:
	shelves.visible = house.is_interior_visible()

func step(at: Vector3) -> void:
	if not at_apron(at):
		visit = ""
		return
	if not apron.visible or visit == "done": return
	if visit.is_empty():
		if not offer.is_empty() and (Rules.house_tier(world.inventory)==0 or at.x>=APRON.x):
			visit = offer
		else:
			visit = "load"
	if visit == "load":
		for kind: String in world.Inventory.KINDS:
			if world.carry.deposit_storage(kind): break
	elif visit == offer:
		world.carry.contribute(visit)

static func shelf_quantity(amount: int) -> String:
	if amount < 1000:
		return str(amount)
	if amount == 1000000:
		return "1M"
	# A trailing plus marks a lower bound. Never round stock up across a price.
	return "%dk%s" % [floori(amount / 1000.0), "+" if amount % 1000 else ""]

func hint() -> String:
	var stock := PackedStringArray()
	for kind: String in world.Inventory.KINDS:
		if world.inventory.storage_open(kind):
			stock.append("%d %s" % [Rules.units(world.inventory.stored[kind]),world.Inventory.TITLES[kind].to_lower()])
	var amounts := "Stored · " + " · ".join(stock) if not stock.is_empty() else ""
	if visit == "done":
		return "Leave the apron to start another visit." + ("\n" + amounts if not amounts.is_empty() else "")
	if not offer.is_empty() and (visit != "load" or stock.is_empty()):
		var price := Rules.price_text(world.inventory.remaining(offer))
		var offer_text := "%s · %s" % [Rules.TITLES[offer], price]
		return offer_text if amounts.is_empty() else "Left: store · Right: " + offer_text + "\n" + amounts
	return amounts
