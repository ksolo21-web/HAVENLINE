extends "res://tests/field_route.gd"

const Profile = preload("res://tests/lifecycle_test_profile.gd")
const TestScript := "res://tests/qa_snow_truck.gd"
var checks := {}
var truck

func _initialize() -> void:
	if not Profile.isolated(self,TestScript):
		run.call_deferred()

func _assert(key:String, predicate:bool) -> void:
	checks[key] = predicate
	if not predicate: print("FAILED TRUCK: ",key)

func _fund(id:String) -> bool:
	for kind in field.inventory.remaining(id):
		var due: int = field.inventory.remaining(id)[kind]
		if kind in field.inventory.KINDS:
			for index in due:
				field.inventory.collect("%s-%s-fixture-%d"%[id,kind,index],kind)
			if not field.inventory.payment(id,kind,false,due):return false
		else:
			var raw := "wood" if kind=="planks" else "stone"
			field.inventory.settlement["processed_"+raw] += due
			for index in due:
				var token := "%s-%s-fixture-%d"%[id,kind,index]
				field.inventory.collected[token] = raw
			field.inventory.settlement.hand_products[kind] += due
			if not field.inventory.payment(id,kind,false,due):return false
	field._inventory_changed()
	if field.persist_blocked: return false
	field._finish_purchase(id)
	return field.inventory.complete(id)

func _heading(direction: Vector3) -> Vector2:
	var right := camera.global_basis.x
	return Vector2(direction.dot(right), direction.dot(right.cross(Vector3.UP))).normalized()

func _hold(direction: Vector3,ticks:int) -> void:
	steer(_heading(direction))
	for count in ticks:await physics_frame
	steer(Vector2.ZERO)
	for count in 23:
		await physics_frame

func _key() -> void:
	var event := InputEventKey.new()
	event.physical_keycode = KEY_T
	event.pressed = true
	root.push_input(event,true)
	await physics_frame

func _blade_checks() -> void:
	var center: float = truck.BLADE_DEPTH
	var pine_at: Vector3 = truck.body.to_global(Vector3(0.,0.,center-.86))
	var bank_at: Vector3 = truck.body.to_global(Vector3(0.,0.,center-1.01))
	var wolf_at: Vector3 = truck.body.to_global(Vector3(0.,0.,center-.92))
	var side_at: Vector3 = truck.body.to_global(Vector3(.99,0.,center-.68))
	var miss_at: Vector3 = truck.body.to_global(Vector3(0.,0.,center-1.06))
	var pine := field.add_resource_source("truck-center-pine","wood",Vector2(pine_at.x,pine_at.z)) as Node3D
	var bank := field.add_resource_source("truck-center-bank","stone",Vector2(bank_at.x,bank_at.z)) as Node3D
	var side := field.add_resource_source("truck-side-pine","wood",Vector2(side_at.x,side_at.z)) as Node3D
	var miss := field.add_resource_source("truck-miss-pine","wood",Vector2(miss_at.x,miss_at.z)) as Node3D
	var wolf = field.encounters._add(wolf_at,false,998,wolf_at)
	var hp: int = wolf.hp
	truck.attack_delay = 0.
	truck._sweep_blades()
	_assert("central leading edge chops a rooted pine",pine.strikes==1)
	_assert("central leading edge mines a bank",bank.strikes==1)
	_assert("central leading edge damages a wolf once",wolf.hp==hp-2)
	_assert("side blade still chops and a target beyond reach stays untouched",side.strikes==1 and miss.strikes==0)
	truck._sweep_blades()
	_assert("blade cooldown prevents a duplicate hit",pine.strikes==1 and wolf.hp==hp-2)
	for id in ["truck-center-pine","truck-center-bank","truck-side-pine","truck-miss-pine"]:
		field.unload_resource_source(id)
	field.encounters._remove(wolf)
	truck.attack_delay = 0.

func _gate_escape() -> void:
	var gate: Node3D = field.gates[0]
	truck.body.position = gate.to_global(Vector3(1.14,0.,-3.5))
	truck.body.rotation.y = gate.rotation.y + PI
	truck.drive_speed = 0.
	var inward := gate.global_basis.z
	await _hold(inward,65)
	var corner: Vector3 = gate.to_local(truck.body.position)
	await _hold(-inward,45)
	var cleared: Vector3 = gate.to_local(truck.body.position)
	_assert("returns steering control after contacting a gate corner",cleared.z < corner.z - 1.1)
	_assert("vehicle cannot shortcut through the pedestrian gate corner",corner.z < -.15)
	truck.body.position = truck.garage.to_global(Vector3(0,0,-4.8))
	truck.body.rotation.y = truck.garage.rotation.y
	truck.drive_speed = 0.

func run() -> void:
	field = load("res://field_opening.tscn").instantiate()
	root.add_child(field)
	camera = field.camera
	truck = field.snow_truck
	origin = root.get_visible_rect().size * Vector2(.30,.72)
	for count in 6:await physics_frame
	_assert("a fresh camp boots",not field.persist_blocked)
	_assert("garage and truck begin locked",not field.inventory.offer_open("snow_garage") and not field.inventory.offer_open("snow_truck"))
	for id in ["center_hearth","expansion_1","storage_wood","storage_stone","storage_meat","expansion_2"]:
		_assert("setup: "+id,_fund(id))
		if id=="center_hearth":
			for count in 14:await physics_frame
	_assert("truck stays locked until garage is built",field.inventory.offer_open("snow_garage") and not field.inventory.offer_open("snow_truck"))
	_assert("pay separate garage offer",_fund("snow_garage"))
	_assert("garage replaces a fence section and keeps both walk gates",field.layout.walls_xz.size()==7 and field.gates.size()==2 and truck.garage.visible)
	_assert("pay separate truck offer",_fund("snow_truck"))
	for count in 5:await physics_frame
	_assert("durable owned truck starts at full health",truck.state().purchases==1 and truck.state().hp==truck.MAX_HP and not field.persist_blocked)
	_assert("whole new truck is parked in the bay",truck.parked())
	field.actor.global_position = truck.body.position + Vector3(0,0,-1.9)
	await physics_frame
	await _key()
	_assert("mounted using player input",truck.mounted)
	await _hold(Vector3.BACK,100)
	print("SNOW TRUCK OUT ",truck.body.position, " door=",truck.opening, " hp=",truck.state().hp)
	_assert("normal thumbstick drives out through garage",truck.body.position.z>8. and not field.field_env.is_inside_camp(truck.body.position))
	var tire_prints := 0
	for chunk in field.tracks.chunks.values():
		for mark in chunk.marks:
			if mark.tire and not field.field_env.is_inside_camp(mark.p):tire_prints+=1
	_assert("moving truck leaves paired treads outside camp",tire_prints>=4)
	_blade_checks()
	var drop_id := "truck-native-wood-1"
	field._place_drop(drop_id,"wood",truck.body.position,truck.body.position,0.,0.)
	for count in 23:await physics_frame
	_assert("ground pickup goes into truck, not player pack",truck.state().cargo.get("wood",0)==1 and field.inventory.carried.wood==0 and not field.drops.has(drop_id))
	var source_at := Vector2(truck.body.position.x,truck.body.position.z+3.32)
	var ore: Node3D = field.add_resource_source("truck-test-ore","metal",source_at)
	steer(_heading(Vector3.BACK))
	for count in 114:
		await physics_frame
		if field.lifecycle.cooling.has("truck-test-ore"):break
	steer(Vector2.ZERO)
	for count in 29:await physics_frame
	_assert("driven blades break a real metal bank",is_instance_valid(ore) and field.lifecycle.cooling.has("truck-test-ore"))
	_assert("all eight metal bundles go to truck exactly once",truck.state().cargo.get("metal",0)==8)
	var stock_before: int=field.inventory.stored.wood
	var metal_before: int=field.inventory.stored.metal
	steer(_heading(Vector3.FORWARD))
	for count in 260:
		await physics_frame
		if truck.body.position.z<=2.85: break
	steer(Vector2.ZERO)
	for count in 46:await physics_frame
	print("SNOW TRUCK IN ",truck.body.position, " parked=",truck.parked()," door=",truck.opening)
	_assert("reverse returns into garage and parks",truck.parked())
	_assert("park transfers the entire cargo once",truck.state().cargo.is_empty() and field.inventory.stored.wood==stock_before+1 and field.inventory.stored.metal==metal_before+8 and not field.persist_blocked)
	await _hold(Vector3.FORWARD,125)
	var limit: Rect2 = truck._garage_hull(truck.body.position,truck.body.basis)
	_assert("held throttle docks fully and stops at rear while mounted",truck.mounted and truck.parked() and limit.end.y <= truck.BAY_DEPTH+.002 and limit.end.y>=truck.BAY_DEPTH-.08)
	_assert("shutter closes after the entire vehicle clears the opening",is_zero_approx(truck.opening) and truck.door.collision_layer!=0)
	_assert("remaining docked cannot credit the same cargo again",field.inventory.stored.wood==stock_before+1 and field.inventory.stored.metal==metal_before+8)
	await _key()
	_assert("restored player controls and backpack",not truck.mounted and field.hero_model.visible and field.carry.rack.visible and field.actor.collision_layer!=0)
	field.inventory.vehicle_collect("truck-native-salvage","stone")
	var stock_stone: int=field.inventory.carried.stone
	truck.receive_damage(truck.MAX_HP)
	_assert("interior wreck retains salvage",truck.state().wreck=="inside" and truck.state().salvage.get("stone",0)==1)
	field.actor.global_position=truck.body.position+Vector3(0,0,-1.83)
	await physics_frame
	await _key()
	_assert("recover interior cargo exactly once",truck.state().salvage.is_empty() and field.inventory.carried.stone==stock_stone+1 and not field.persist_blocked)
	for kind in field.inventory.costs.snow_truck:
		for count in field.inventory.costs.snow_truck[kind]:
			field.inventory.collect("truck-replacement-%s-%d"%[kind,count],kind)
	_assert("affordable replacement at the garage",truck.repair_or_replace() and truck.state().hp==truck.MAX_HP and truck.state().purchases==2)
	field.actor.global_position=truck._exit_position()
	field.actor.velocity=Vector3.ZERO
	for frame in 4:await physics_frame
	await _key()
	_assert("can drive the replacement truck",truck.mounted)
	await _hold(Vector3.BACK,104)
	_assert("replacement is completely outside camp",truck.body.position.z > 8.)
	await _gate_escape()
	_assert("replacement takes cargo before wreck",field.inventory.vehicle_collect("truck-native-lost","coal"))
	var fatal_contact := false
	for count in 48:
		if truck.damage_grace <= 0. and truck.receive_damage(truck.MAX_HP):
			fatal_contact = true
			break
		await physics_frame
	_assert("lethal contact applies after damage cooldown",fatal_contact)
	_assert("outside wreck loses cargo without salvage",truck.state().wreck=="outside" and truck.state().cargo.is_empty() and truck.state().salvage.is_empty() and truck.state().lost.get("coal",0)==1)
	_assert("save remains usable after all truck operations",not field.persist_blocked and not truck.mounted)
	var wreck_position:Vector3 = truck.body.position
	await _close_field()
	field = load("res://field_opening.tscn").instantiate()
	root.add_child(field)
	camera = field.camera
	truck = field.snow_truck
	for count in 6:await physics_frame
	_assert("outside loss survives cold reload",not field.persist_blocked and truck.state().wreck=="outside" and truck.state().lost.get("coal",0)==1 and truck.state().cargo.is_empty())
	_assert("outside wreck position survives cold reload",truck.body.position.distance_to(wreck_position)<.012 and not truck.mounted and field.hero_model.visible)
	await _close_field()
	print("SNOW_TRUCK_NATIVE ",JSON.stringify({"checks":checks}))
	quit(0 if checks.values().all(func(p):return p) else 1)

func _close_field() -> void:
	field.set_physics_process(false)
	field.carry.set_physics_process(false)
	await Profile.drain_field_audio(self,field)
	field.queue_free()
	for count in 3:await process_frame
