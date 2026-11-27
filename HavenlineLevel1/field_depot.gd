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
const UPGRADE_AT := Vector3(-2.18,0,.65)
const UPGRADE_RADIUS := .81
var house
var apron: Node3D
var upgrade_mark: Node3D
var still_since := -1.0
var paused_on_upgrade := false
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
	upgrade_mark = Offer.new()
	add_child(upgrade_mark)
	upgrade_mark.install(world.field_env,"storage_stone",UPGRADE_AT)
	upgrade_mark.name = "StorehouseUpgradePlot"
	for id: String in Rules.STORAGE:
		world.carry.define_receiver(id,apron if id == Rules.STORAGE[0] else upgrade_mark)
	world.carry.set_storage_layout(landing_position,BIN_SCALE)

func landing_position(kind: String, index: int) -> Vector3:
	return bins[kind].to_global(Layout.position(kind,index)*BIN_SCALE)

func at_apron(at:Vector3) -> bool:
	return Vector2(at.x,at.z).distance_squared_to(Vector2(APRON.x,APRON.z)) <= 1.0

func at_loading_area(at:Vector3) -> bool:
	if not house.visible: return false
	var local:Vector3 = house.to_local(at)
	return absf(local.x) <= 1.05 and local.z >= -.73 and local.z <= 2.27

func on_upgrade_side(at:Vector3) -> bool:
	return Vector2(at.x,at.z).distance_squared_to(Vector2(UPGRADE_AT.x,UPGRADE_AT.z)) <= UPGRADE_RADIUS*UPGRADE_RADIUS

func refresh(active: bool) -> void:
	var ledger = world.inventory
	var tier: int = Rules.house_tier(ledger) if active else 0
	house.update_state(tier, ledger.stored)
	offer = Rules.next_storage(ledger) if active else ""
	apron.visible = active and ledger.complete(Rules.FIRST)
	upgrade_mark.visible = house.visible and not offer.is_empty()
	if upgrade_mark.visible:
		upgrade_mark.change_project(offer,ledger)
		upgrade_mark.set_due(ledger,offer,true)
		# Independent pre-tier saves can own a higher bay while the starter
		# receipt is still open. Its next missing upgrade uses this pad too.
		world.carry.define_receiver(offer,upgrade_mark)
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

func pause_purchase(at: Vector3) -> void:
	visit = "done"
	paused_on_upgrade = on_upgrade_side(at)
	still_since = -1.

func step(at: Vector3) -> void:
	var at_door := at_apron(at) or at_loading_area(at)
	var at_upgrade := upgrade_mark.visible and on_upgrade_side(at)
	if visit == "done":
		# Standing on a just-paid or restored plot cannot buy the next tier.
		var still_on_paid_plot := on_upgrade_side(at) if paused_on_upgrade else at_apron(at)
		if still_on_paid_plot: return
		visit = ""
	if not apron.visible or (not at_door and not at_upgrade):
		world.carry.stop_visit(world.carry.STOCK if visit == "load" else visit)
		visit = ""
		still_since = -1.
		return
	if not at_upgrade:
		if visit != "load": world.carry.stop_visit(visit)
		still_since = -1.
		visit = "load" if house.tier > 0 else offer
	elif visit != offer:
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
	if house.tier == 0 or (upgrade_mark.visible and on_upgrade_side(world.actor.position)):
		if visit == "done": return "Step off the plot to start the next upgrade."
		if offer.is_empty(): return amounts
		return "%s · %s" % [Rules.TITLES[offer],Rules.price_text(world.inventory.remaining(offer))] + ("\nStand on this plot to pay" if house.tier > 0 else "")
	if house.tier > 0 and not offer.is_empty():
		return "Door: unload · Next: " + Rules.TITLES[offer] + " on the nearby plot" + ("\n"+amounts if not amounts.is_empty() else "")
	return amounts
