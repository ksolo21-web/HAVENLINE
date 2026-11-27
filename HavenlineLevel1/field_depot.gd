extends Node3D

const House = preload("res://field_storage_house.gd")
const Rules = preload("res://field_progression.gd")
const Layout = preload("res://field_stock_layout.gd")
const Offer = preload("res://field_offer_floor.gd")
const SITE := Vector3(-3.05,0,-3.45)
const APRON := Vector3(-3.05,0,-1.18)
const BIN_SCALE := .38
const BALANCE_PIXEL_SIZE := .0046
const UPGRADE_PAUSE := .16
const UPGRADE_SPOT := Vector3(.62,.026,.06)
var house
var apron: Node3D
var upgrade_mark: Label3D
var still_since := -1.0
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
	upgrade_mark = world.field_env.flat_label(self,APRON+UPGRADE_SPOT,.012)
	upgrade_mark.text = "↑"
	upgrade_mark.name = "UpgradeArrow"
	upgrade_mark.modulate = Color("#ffe8a3")
	upgrade_mark.outline_modulate = Color("#3f301e")
	upgrade_mark.outline_size = 7
	upgrade_mark.visible = false
	for id: String in Rules.STORAGE:
		world.carry.define_receiver(id,apron)
	world.carry.set_storage_layout(landing_position,BIN_SCALE)

func landing_position(kind: String, index: int) -> Vector3:
	return bins[kind].to_global(Layout.position(kind,index)*BIN_SCALE)

func at_apron(at:Vector3) -> bool:
	return Vector2(at.x,at.z).distance_squared_to(Vector2(APRON.x,APRON.z)) <= 1.0

func at_loading_area(at:Vector3) -> bool:
	if not house.visible: return false
	var local:Vector3 = house.to_local(at)
	return absf(local.x) <= 1.05 and local.z >= -.73 and local.z <= 2.27 and not on_upgrade_side(at)

func on_upgrade_side(at:Vector3) -> bool:
	return at_apron(at) and at.x >= APRON.x+.34 and at.z >= APRON.z-.50

func refresh(active: bool) -> void:
	var ledger = world.inventory
	var tier: int = Rules.house_tier(ledger) if active else 0
	house.update_state(tier, ledger.stored)
	offer = Rules.next_storage(ledger) if active else ""
	apron.visible = active and ledger.complete(Rules.FIRST)
	upgrade_mark.visible = house.visible and not offer.is_empty()
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
	var at_pad := at_apron(at)
	var indoors := at_loading_area(at)
	var upgrade_side := on_upgrade_side(at)
	if not at_pad and not indoors:
		world.carry.stop_visit(world.carry.STOCK if visit == "load" else visit)
		visit = ""
		still_since = -1.
		return
	if not apron.visible: return
	if visit == "done":
		# A completed purchase cannot chain into the next one. Walking inside
		# starts unloading without having to reverse out of the building.
		if not indoors or at.z >= APRON.z-.50: return
		visit = "load"
	if house.tier == 0:
		visit = offer
	elif not upgrade_side or offer.is_empty():
		if visit == offer: world.carry.stop_visit(offer)
		still_since = -1.
		visit = "load"
	elif visit != offer:
		# Walking through the corner is navigation. Entering the marked edge
		# and stopping is the deliberate upgrade, even straight from the door.
		if visit == "load" and _unload_pending():
			world.carry.visit(world.carry.STOCK)
			return
		world.carry.stop_visit(world.carry.STOCK)
		visit = "upgrade"
		if world.actor.velocity.slide(Vector3.UP).length_squared() > .40*.40:
			still_since = -1.
		elif still_since < 0.:
			still_since = world.carry.clock
		elif world.carry.clock-still_since >= UPGRADE_PAUSE:
			visit = offer
	if visit == "load":
		world.carry.visit(world.carry.STOCK)
	elif visit == offer and not offer.is_empty():
		world.carry.visit(offer)

func _unload_pending() -> bool:
	for kind: String in world.Inventory.KINDS:
		if world.inventory.storage_open(kind) and world.inventory.carried[kind] > 0: return true
	return false

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
		return "Enter to unload. Step away to start another purchase." + ("\n" + amounts if not amounts.is_empty() else "")
	if not offer.is_empty() and (at_apron(world.actor.position) or visit != "load" or stock.is_empty()):
		var price := Rules.price_text(world.inventory.remaining(offer))
		var offer_text := "%s · %s" % [Rules.TITLES[offer], price]
		if amounts.is_empty(): return offer_text
		return ("Stop on ↑ · " + offer_text if on_upgrade_side(world.actor.position) else "Door: store · Stop on ↑ to upgrade") + "\n" + amounts
	return "Unloading into the marked shelves." + ("\n" + amounts if not amounts.is_empty() else "")
