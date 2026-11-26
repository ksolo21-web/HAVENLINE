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
	"wood": Vector3(.08, 1.09, .44),
	"stone": Vector3(0, .24, .19),
	"meat": Vector3(-.39, 1.06, .15),
}
const EXIT = {
	"wood": Vector3(-.18, 1.07, .52),
	"stone": Vector3(-.14, .28, .17),
	"meat": Vector3(.50, 1.075, .15),
}

var world
var raw_goods := {}
var finished_goods := {}
var inlets := {}
var outlets := {}
var rollers: Array[Node] = []
var saw_log: Node3D
var meal_rack := Node3D.new()
var shown_meals := -1


func setup(host) -> void:
	world = host
	name = "LocalMaterialTransfers"
	var cooker: Node3D = world.lakeshore.cooker
	rollers = cooker.find_children("WorkRoller*", "MeshInstance3D", true, false)
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
				saw_log.hide()
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
	var count := clampi(int(world.inventory.settlement["processed_" + kind]), 0, 3)
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
		saw_log.visible = fraction >= .23 and fraction < .68
		if saw_log.visible:
			var feed := smoothstep(.23, .68, fraction)
			saw_log.position = Vector3(.16, 0, 0).lerp(Vector3(-.15, -.018, .43), feed)
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
			var lip := Vector3(-.58, 1.05, .73)
			source = source.lerp(lip, minf(t * 2.0, 1.0))
			product.position = source.lerp(target, maxf(t * 2.0 - 1.0, 0.0))
		else:
			product.position = source.lerp(target, t)
