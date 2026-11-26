extends Node3D

const House = preload("res://field_storage_house.gd")
const Rules = preload("res://field_progression.gd")
const Layout = preload("res://field_stock_layout.gd")
const Offer = preload("res://field_offer_floor.gd")
const SITE := Vector3(-3.05,0,-3.45)
const APRON := Vector3(-3.05,0,-1.18)
const BIN_SCALE := .38
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
		var label: Label3D = world.field_env.flat_label(bin,Vector3.ZERO,.0046)
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
		labels[kind].text = str(ledger.stored[kind])
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

func hint() -> String:
	if visit == "done": return "Leave the apron to start another visit."
	var stock := PackedStringArray()
	for kind: String in world.Inventory.KINDS:
		if world.inventory.storage_open(kind):
			if kind not in world.Inventory.MINERALS or int(world.inventory.stored[kind])>0:
				stock.append("%d %s" % [world.inventory.stored[kind],world.Inventory.TITLES[kind].to_lower()])
	if not offer.is_empty() and (visit != "load" or stock.is_empty()):
		var price := Rules.price_text(world.inventory.remaining(offer))
		return "%s · %s" % [Rules.TITLES[offer], price] if stock.is_empty() else "Left: store · Right: %s · %s" % [Rules.TITLES[offer],price]
	return "Stored · " + " · ".join(stock)
