extends "res://tests/qa_snow_truck.gd"

func _initialize() -> void:
	run.call_deferred()

func run() -> void:
	field = load("res://field_opening.tscn").instantiate()
	root.add_child(field)
	camera = field.camera
	truck = field.snow_truck
	origin = root.get_visible_rect().size * Vector2(.30,.72)
	var mode := OS.get_environment("T02_COLD_MODE")
	if mode == "legacy":
		for i in 8: await physics_frame
	field.player_invulnerability = 60.
	if mode == "legacy":
		_assert("baseline has no river system",not "river" in field)
		_assert("existing profile opens",not field.persist_blocked and field.inventory.complete("center_hearth"))
		_assert("owned garage and truck settle",_fund("snow_garage") and _fund("snow_truck"))
		_assert("held wood and truck cargo recorded",field.inventory.collect("t02-cold-avatar-wood","wood") and field.inventory.vehicle_collect("t02-cold-truck-meat","meat"))
		field.actor.global_position = Vector3(-18.,0.,-34.7)
		truck.body.global_position = Vector3(-20.,0.,-33.25)
		truck.record_position()
		var loose := Vector3(-24.,0.,-34.7)
		field._place_drop("stone-81500","stone",loose,loose,0.,.4)
		field.drop_id = 81501
		field._persist_world()
		_assert("baseline persisted a real profile",not field.persist_blocked and FileAccess.file_exists(field.field_save.directory.path_join(field.field_save.PRIMARY)))
	elif mode == "migrated":
		var river = field.river
		var expected: Vector3 = river.safe_feet(Vector3(-18.,0.,-34.7),float(field.layout.actor_radius))
		var expected_truck: Vector3 = river.safe_feet(Vector3(-20.,0.,-33.25),truck.HALF_WIDTH)
		_assert("old coordinates intersect new water",expected.z != -34.7 and expected_truck.z != -33.25)
		_assert("cold open preserves both owned offers and cargo",not field.persist_blocked and truck.owned() and truck.state().cargo.get("meat",0)==1 and field.inventory.carried.wood>=1)
		_assert("player cold restore keeps its original bank",field.actor.global_position.distance_to(expected)<.05)
		_assert("parked truck cold restore stays on its original bank",truck.body.global_position.distance_to(expected_truck)<.05 and absf(float(truck.state().park[1])-expected_truck.z)<.05)
		_assert("loose drop retains its ID and is moved to dry ground",field.drops.has("stone-81500") and river.is_dry(Vector2(field.drops["stone-81500"].at.x,field.drops["stone-81500"].at.z),.10))
		var ends: PackedVector2Array = river.crossing_approaches(truck.HALF_WIDTH)
		truck.body.global_position = Vector3(ends[1].x,0.,ends[1].y+1.0)
		truck.body.rotation.y = 0.0
		field.actor.global_position = truck.body.global_position+Vector3(0,0,1.92)
		for i in 6: await physics_frame
		_assert("drive prompt is visible at truck",truck.hud.visible)
		await _key()
		_assert("player input mounts the migrated truck",truck.mounted)
		steer(_heading(Vector3.FORWARD))
		var stayed_dry := true
		for i in 160:
			await physics_frame
			var feet := Vector2(truck.body.position.x,truck.body.position.z)
			stayed_dry = stayed_dry and river.is_dry(feet,truck.HALF_WIDTH)
			if feet.y < ends[0].y-.3: break
		steer(Vector2.ZERO)
		print("Mounted endpoint ",truck.body.position," approach ",ends," dry ",stayed_dry)
		_assert("the actual mounted truck drives across the ice corridor",stayed_dry and truck.body.position.z < ends[0].y-.3)
		_assert("cargo remains in the truck after crossing",truck.state().cargo.get("meat",0)==1)
		await _key()
		_assert("dismount finds dry ground",not truck.mounted and river.is_dry(Vector2(field.actor.position.x,field.actor.position.z),float(field.layout.actor_radius)))
		field._persist_world()
		_assert("new save records the river identity and water clock",not field.persist_blocked and field.inventory.world_state.river_layout==river.LAYOUT_VERSION and is_equal_approx(float(field.inventory.world_state.river_time),river.flow_time))
	else:
		_assert("known fixture mode",false)
	print("T02_COLD ",JSON.stringify({"stage":mode,"checks":checks,"player":str(field.actor.position),"truck":str(truck.body.position),"cargo":truck.state().get("cargo",{})}))
	await Profile.drain_field_audio(self,field)
	field.queue_free()
	for i in 6: await process_frame
	quit(1 if false in checks.values() else 0)
