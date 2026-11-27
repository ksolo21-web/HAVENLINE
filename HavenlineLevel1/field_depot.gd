extends Node3D

const House = preload("res://field_storage_house.gd")
const Rules = preload("res://field_progression.gd")
const Layout = preload("res://field_stock_layout.gd")
const Offer = preload("res://field_offer_floor.gd")
const SITE := Vector3(-3.05,0,-3.45)
const APRON := Vector3(-3.05,0,-1.18)
const BIN_SCALE := .38
const BALANCE_PIXEL_SIZE := .0046
const Reach = preload("res://field_reach.gd")
# Outer faces of the authored storehouse walls, in its local floor plane.
const FOOTPRINT := Rect2(-1.63,-1.17,3.26,2.35)
const UPGRADE_AT := Vector3(-2.18,0,.65)
var house
var apron: Node3D
var upgrade_mark: Node3D
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

func at_apron(at: Vector3) -> bool:
	return Reach.plot_distance(apron,at) <= Reach.NEAR

func loading_distance(at: Vector3) -> float:
	var d := Reach.plot_distance(apron,at)
	if house.visible:
		var local: Vector3 = house.to_local(at)
		d = minf(d,Reach.distance_to_rect(Vector2(local.x,local.z),FOOTPRINT))
	return d

func at_loading_area(at: Vector3) -> bool:
	return house.visible and loading_distance(at) <= Reach.NEAR

func on_upgrade_side(at: Vector3) -> bool:
	if not upgrade_mark.visible: return false
	var d := Reach.plot_distance(upgrade_mark,at)
	return d <= Reach.NEAR and d < loading_distance(at)

func target_at(at: Vector3) -> String:
	if not apron.visible: return ""
	# The approach to the loading door crosses the edge of the upgrade print.
	# A runner can unload in motion. Stopping beside that separate pad buys it.
	var resting: bool = not world.runner_requested_motion and Vector2(world.actor.velocity.x,world.actor.velocity.z).length_squared() < .09
	if resting and on_upgrade_side(at):
		return offer
	if loading_distance(at) <= Reach.NEAR: return world.carry.STOCK if house.tier > 0 else offer
	return ""

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

func pause_purchase(at: Vector3, paid_pad: Node3D = null) -> void:
	visit = "done"
	paused_on_upgrade = paid_pad == upgrade_mark if paid_pad else on_upgrade_side(at)

func step(at: Vector3, selected: String = "") -> void:
	if visit == "done":
		# Only an exit from the paid footprint arms its next tier.
		var paid_pad: Node3D = upgrade_mark if paused_on_upgrade else apron
		if Reach.plot_distance(paid_pad,at) <= Reach.NEAR:
			if selected == world.carry.STOCK and house.tier > 0:
				world.carry.visit(world.carry.STOCK)
			return
	if selected.is_empty():
		visit = ""
		return
	visit = "load" if selected == world.carry.STOCK else selected
	world.carry.visit(selected)

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
		return "%s · %s" % [Rules.TITLES[offer],Rules.price_text(world.inventory.remaining(offer))] + ("\nStop beside the upgrade plot to pay" if house.tier > 0 else "")
	if house.tier > 0 and not offer.is_empty():
		return "Unload beside the storehouse · Next: " + Rules.TITLES[offer] + " on the nearby plot" + ("\n"+amounts if not amounts.is_empty() else "")
	return amounts
