extends "res://tests/qa_storage_stream.gd"

var evidence := {}

func stop_and_wait(seconds: float) -> void:
	steer(Vector2.ZERO)
	for i in ceili(seconds*60.): await physics_frame

func approach(key: String, start: Vector3, goal: Vector3, kind: String, dest: String) -> void:
	field.actor.position = start
	field.actor.velocity = Vector3.ZERO
	await stop_and_wait(.15)
	var inv = field.inventory
	var stored_before: int = inv.stored[kind]
	var paid_before: int = 0 if dest == "storage" else inv.paid[dest][kind]
	var starting_load: int = inv.carried[kind]
	supply(kind, 3)
	field.carry.sync(true)
	var launch_at := Vector3.INF
	var launch_speed := 0.
	for i in 150:
		var arrived := move_to([goal.x,goal.z],.105)
		await physics_frame
		if not launch_at.is_finite() and field.carry.flights.any(func(f): return f.to == dest):
			launch_at = field.actor.global_position
			launch_speed = field.actor.velocity.slide(Vector3.UP).length()
		if arrived: break
	await stop_and_wait(1.1)
	var delta: int = inv.stored[kind]-stored_before if dest == "storage" else int(inv.paid[dest][kind])-paid_before
	verify(key+" starts in motion",launch_at.is_finite() and launch_speed > .4)
	verify(key+" commits the available load",delta >= 3 and delta <= 3 + starting_load)
	evidence[key]={"first_takeoff":str(launch_at),"speed":launch_speed,"deposited":delta,"target":dest,"end":str(field.actor.global_position)}

func run() -> void:
	field = Scene.instantiate()
	root.add_child(field)
	current_scene = field
	camera = field.camera
	await physics_frame
	var pad: Node3D = field.field_env.buy_anchor
	var e: Vector3 = pad.global_position
	await approach("Hearth east lip",e+Vector3(3.6,0,0),e+Vector3(1.75,0,0),"wood","center_hearth")
	await approach("Hearth west lip",e+Vector3(-3.6,0,0),e+Vector3(-1.75,0,0),"wood","center_hearth")
	await approach("Hearth north lip",e+Vector3(0,0,-3.2),e+Vector3(0,0,-1.48),"wood","center_hearth")
	await approach("Hearth south lip",e+Vector3(0,0,3.2),e+Vector3(0,0,1.48),"wood","center_hearth")
	# Pay the last instalments standing at the north edge, inside the future furnace.
	var hearth: Vector3 = field.point(field.layout.furnace_xz)
	field.actor.position = hearth + Vector3(0,0,.55)
	var due: int = field.inventory.remaining("center_hearth").wood
	supply("wood",due)
	field.carry.sync(true)
	await stop_and_wait(1.5)
	verify("North-side payer remains clear of the solid furnace",field.camp_active and field.actor.position.distance_to(hearth)>1.0)
	var restored: Vector3 = field.field_env.clear_hearth_footprint(hearth)
	verify("Exact-center legacy position resolves onto walkable camp ground",restored.distance_to(hearth)>1.0 and field.field_env.is_inside_camp(restored))
	for id in ["expansion_1","storage_wood"]: open_site(id)
	var site: Vector3 = field.depot.SITE
	await approach("Storehouse right wall",site+Vector3(3.5,0,-.48),site+Vector3(2.05,0,-.48),"meat","storage")
	await approach("Storehouse left wall",site+Vector3(-2.12,0,3.80),site+Vector3(-2.04,0,.52),"meat","storage")
	await approach("Storehouse front",site+Vector3(-1.20,0,4.60),site+Vector3(-1.20,0,2.20),"meat","storage")
	field.actor.position = Vector3(-5.9,0,-3.45)
	await stop_and_wait(.2)
	supply("meat",1)
	field.carry.sync(true)
	var prev: int = field.inventory.stored.meat
	await stop_and_wait(.75)
	verify("Outside palisade cannot feed through wall",prev==field.inventory.stored.meat)
	var up: Vector3 = field.depot.UPGRADE_AT
	await approach("Storehouse upgrade east lip",up+Vector3(3.15,0,1.8),up+Vector3(1.45,0,.70),"stone","storage_stone")
	field.set_physics_process(false)
	field.carry.set_physics_process(false)
	await Session.drain_field_audio(self,field)
	field.queue_free()
	for i in 3: await process_frame
	print("APPROACH7 ",JSON.stringify({"checks":checks,"measurements":evidence}))
	quit(1 if checks.values().has(false) else 0)
