extends SceneTree

const Session = preload("res://tests/lifecycle_test_profile.gd")
var checks := {}

func _initialize() -> void:
	if not Session.isolated(self,"res://tests/qa_material_fence.gd"): run.call_deferred()

func run() -> void:
	var world = load("res://field_opening.tscn").instantiate()
	root.add_child(world)
	await process_frame
	world.set_physics_process(false)
	world.carry.set_physics_process(false)
	for index in world.inventory.costs.center_hearth.wood:
		world.inventory.collect("setup-%d" % index,"wood")
	world.inventory.payment("center_hearth","wood",false,world.inventory.carried.wood)
	world._apply_hearth(true,false)
	var anchor: Node3D = world.carry.receivers.expansion_1
	var north: float = world.layout.camp_rect_xz[1]
	world.actor.position = Vector3(-2.25,0,north+1.3)
	world.inventory.collect("owned-1","wood")
	world.carry.sync()
	var exterior := Vector3(-2.25,0,north-1.)
	checks["closed timber blocks loose pickup before credit"] = not world.carry.pickup("loose-1","wood",exterior) and not world.inventory.collected.has("loose-1")
	anchor.global_position = exterior
	checks["cross-wall purchase cannot reserve stock"] = not world.carry.contribute("expansion_1") and world.carry.flights.is_empty()
	anchor.global_position = world.actor.position + Vector3(.9,0,.2)
	checks["same-side payment launches"] = world.carry.contribute("expansion_1")
	world.carry.advance(.03)
	anchor.global_position = exterior
	world.carry.advance(1.)
	checks["new wall in a shipment path cancels its debit"] = world.carry.flights.is_empty() and world.inventory.carried.wood==1 and world.inventory.paid.expansion_1.wood==0
	anchor.global_position = world.actor.position + Vector3(.9,0,.2)
	checks["same-side payment can retry"] = world.carry.contribute("expansion_1")
	world.carry.advance(1.)
	checks["single receipt lands"] = world.inventory.carried.wood==0 and world.inventory.paid.expansion_1.wood==1
	print(JSON.stringify({"checks":checks,"passed":not checks.values().has(false)}))
	await Session.drain_field_audio(self,world)
	world.free()
	quit(int(checks.values().has(false)))
