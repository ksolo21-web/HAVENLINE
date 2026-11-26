extends SceneTree
## Exact boundary and activation regression at each paid footprint. Positions immediately
## beside the line intentionally isolate inclusive/exclusive arithmetic from touch input.
const World = preload("res://field_opening.tscn")
var failures: Array[String] = []
var checks := 0

func check(value: bool, label: String) -> void:
	checks += 1
	if not value:
		failures.append(label)
		push_error(label)

func visible_slots(kit) -> Vector2i:
	var total := Vector2i.ZERO
	for slot in kit.slots:
		total.x += int(slot.axe.visible) + int(slot.pickaxe.visible)
		total.y += int(slot.trail.visible)
	return total

func test_threshold(world, gate: Node3D, normal: Vector3, stage: int) -> void:
	var kit = world.character_kit
	var center := gate.global_position
	var label := "%s stage %d" % [gate.name, stage]
	world.actor.global_position = center + normal * .04
	world._step_character(1./60.,0.)
	check(kit.active and visible_slots(kit) == Vector2i(3,3), label + " active 4 cm outside")
	for point: Vector3 in [center,center-normal*.04]:
		world.actor.global_position = point
		world._step_character(1./60.,0.)
		var turn: int = kit.turn_id
		var elapsed: float = kit.elapsed
		for j in 65:
			world._step_character(1./60.,0.)
		check(not kit.active and kit.equipped == "" and visible_slots(kit) == Vector2i.ZERO, label + " all meshes and ribbons hidden")
		check(kit.turn_id == turn and kit.elapsed == elapsed and kit.hit_this_turn.is_empty(), label + " idle through full turn")
		check(not kit.crosses_surface(world.surfaces[world.resource_rock][0],world.surfaces[world.resource_rock][1]), label + " no stored sweep hits")
	world.actor.global_position = center + normal*.04
	world._step_character(1./60.,0.)
	check(kit.active and visible_slots(kit) == Vector2i(3,3), label + " active on first exterior step")

func _initialize() -> void:
	call_deferred("run")

func run() -> void:
	var world = World.instantiate()
	root.add_child(world)
	for i in 3: await physics_frame
	world.set_physics_process(false)
	var kit = world.character_kit
	world.actor.global_position = Vector3.ZERO
	world._step_character(1./60.,0.)
	check(kit.active and visible_slots(kit) == Vector2i(1,1), "unpaid clearing still harvests")
	kit.set_upgraded(true)
	for stage in [1,2,3]:
		world.field_env.set_perimeter(stage,false)
		test_threshold(world,world.gates[0],Vector3.BACK,stage)
		test_threshold(world,world.gates[1],Vector3.RIGHT,stage)
	world.actor.global_position = Vector3.ZERO
	var event_start: int = world.events.size()
	var contacts_start: int = world.contacts.size()
	for j in 70:
		world._physics_process(1./60.)
	var forbidden := ["swing","equip_axe","equip_pickaxe","impact_wood","impact_stone","player_attack"]
	var leaked: bool = world.events.slice(event_start).any(func(event): return event.event in forbidden)
	check(not leaked, "complete field tick emits no swing/equip/strike event inside")
	check(world.contacts.size() == contacts_start, "complete field tick makes no hit inside")
	kit = null
	world.queue_free()
	for j in 16:
		OS.delay_msec(12)
		await process_frame
	print(JSON.stringify({"suite":"world_orbit","checks":checks,"failures":failures}))
	quit(int(not failures.is_empty()))
