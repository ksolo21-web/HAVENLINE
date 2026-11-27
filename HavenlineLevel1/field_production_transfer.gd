extends Node3D
## Goods on the machine remain in the station's own space throughout the cycle.
## The settlement journal exclusively owns quantities, pickup, and payments.
const Art = preload("res://field_art.gd")
const DISH = preload("res://assets/customer_counter/cooked_game_meat.glb")
const PLANKS = preload("res://assets/shore_workshops/finished_planks.glb")
const BLOCK = preload("res://assets/shore_workshops/dressed_block.glb")
const FINISHED = {"wood": PLANKS, "stone": BLOCK, "meat": DISH}

# Visible mouths of the saw blade, drill bit, and cooker chamber.
const TOOL = {
	"wood": Vector3(.20, 1.13, -.20),
	"stone": Vector3(-.72,.19,.35),
	"meat": Vector3(-.30,.70,.34),
}
const EXIT = {
	"wood": Vector3(-.12,.84,.36),
	"stone": Vector3(-.73,.18,.46),
	"meat": Vector3(.34,.70,.33),
}

var world
var raw_goods := {}
var finished_goods := {}
var inlets := {}
var outlets := {}
var rollers: Array[Node] = []
var saw_log: Node3D
var meal_rack := Node3D.new()
var raw_tray := Node3D.new()
var shown_raw := -1
var shown_meals := -1


func setup(host) -> void:
	world = host
	name = "LocalMaterialTransfers"
	var cooker: Node3D = world.lakeshore.cooker
	rollers = cooker.find_children("WorkRoller*", "MeshInstance3D", true, false)
	raw_tray.name = "RawStock"
	cooker.add_child(raw_tray)
	raw_tray.position = world.lakeshore.cooker_input.position
	meal_rack.name = "CookedStock"
	cooker.add_child(meal_rack)
	meal_rack.position = world.lakeshore.cooker_output.position
	for kind: String in FINISHED:
		var machine: Node3D
		if kind == "meat":
			machine = cooker
			inlets[kind] = world.lakeshore.cooker_input.position
			outlets[kind] = meal_rack.position
		else:
			var tray: Node3D = world.processors.trays[kind]
			machine = tray.get_parent()
			if kind == "wood":
				saw_log = machine.find_child("TimberWorkpiece", true, false)
				saw_log.show()
			inlets[kind] = machine.to_local(world.processors.input_position(kind))
			outlets[kind] = tray.position
		raw_goods[kind] = _mount(machine, Art.make(kind), "MovingInput")
		finished_goods[kind] = _mount(machine, FINISHED[kind].instantiate(), "MovingOutput")


func _mount(machine: Node3D, art: Node3D, label: String) -> Node3D:
	art.name = label
	machine.add_child(art)
	art.hide()
	return art


func _meal_slot(index: int) -> Vector3:
	return Vector3(0, floori(index / 2.0) * .265, (-.145 if index % 2 == 0 else .145))


func set_raw_stock(amount: int) -> void:
	if amount == shown_raw: return
	shown_raw = amount
	while raw_tray.get_child_count() < amount:
		var i := raw_tray.get_child_count()
		var cut := Art.make("meat",.47)
		raw_tray.add_child(cut)
		cut.position = Vector3(0.,floori(i/2.)*.105,(i%2-.5)*.26)
		cut.rotation.y = .11 if i%2 else -.11
	for i in raw_tray.get_child_count(): raw_tray.get_child(i).visible = i < amount

func set_meal_stock(amount: int) -> void:
	var total := clampi(amount, 0, 4)
	if total == shown_meals:
		return
	shown_meals = total
	while meal_rack.get_child_count() < total:
		var item: Node3D = DISH.instantiate()
		item.name = "Portion%d" % (meal_rack.get_child_count() + 1)
		item.position = _meal_slot(meal_rack.get_child_count())
		meal_rack.add_child(item)
	for i in meal_rack.get_child_count():
		(meal_rack.get_child(i) as Node3D).visible = i < total


func _landing(kind: String) -> Vector3:
	var result: Vector3 = outlets[kind]
	if kind == "meat":
		return result + _meal_slot(clampi(shown_meals, 0, 3))
	var count := clampi(preload("res://field_logistics.gd").rack(world.inventory.settlement,kind), 0, 3)
	if kind == "wood":
		return result + Vector3.UP * (.25 * count)
	return result + Vector3(0, floori(count / 2.0) * .235, (count % 2 - .5) * .33)


func show_cycle(kind: String, fraction: float) -> void:
	var raw: Node3D = raw_goods[kind]
	var product: Node3D = finished_goods[kind]
	raw.visible = fraction >= 0.0 and fraction < .42
	product.visible = fraction >= .59 and fraction <= 1.0
	if kind == "wood":
		raw.visible = fraction >= 0.0 and fraction < .23
		# The actual golden-faced timber remains in its clamp between jobs.
		var feed := smoothstep(.23, .68, fraction) * (1.-smoothstep(.74,1.0,fraction))
		saw_log.position = Vector3.ZERO.lerp(Vector3(-.18,0,.18),feed)
	elif kind == "meat":
		# One cut leaves the queue for the current cooking cycle. The remaining
		# paid cuts stay visibly stacked in the separate raw bin.
		var waiting: int = world.inventory.settlement.hoppers.meat
		set_raw_stock(maxi(0, waiting - (1 if fraction >= 0. else 0)))
	if fraction < 0.0:
		return
	if kind == "meat":
		for roller: Node3D in rollers:
			roller.rotation.z = -TAU * 4.0 * fraction
	if raw.visible:
		var entry: Vector3 = inlets[kind]
		raw.position = entry.lerp(TOOL[kind], smoothstep(.0, .42, fraction))
	if product.visible:
		var target := _landing(kind)
		var source: Vector3 = EXIT[kind]
		# The bed feeds across the nearest end of the rack. Settle onto the
		# top of the actual stock, then yield to its durable representation.
		var t := smoothstep(.59, 1.0, fraction)
		if kind == "wood":
			var lip := Vector3(-.37,.84,.78)
			source = source.lerp(lip, minf(t * 2.0, 1.0))
			product.position = source.lerp(target, maxf(t * 2.0 - 1.0, 0.0))
		else:
			product.position = source.lerp(target, t)
