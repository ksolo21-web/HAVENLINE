extends SceneTree

var world
func _initialize() -> void: call_deferred("run")

func target_for(kind: String, side: Vector3) -> Dictionary:
	for x in range(3,8):
		for z in range(-6,-2):
			var rows: Array = world.world_landscape.describe_chunk(Vector2i(x,z))
			for row in rows:
				if row.kind != kind: continue
				var approach: Vector3 = row.position + side * 3.3
				if not rows.any(func(r): return r.id != row.id and r.position.distance_to(approach)<4.55):
					return row
	return {}

func place(at: Vector3, side: Vector3, distance: float):
	world.actor.position = at + side * distance
	world.actor.velocity = Vector3.ZERO
	world.actor.rotation.y = atan2(-side.x,-side.z) + PI*.67
	world.camera.position = world.actor.position+Vector3(7,11,11)

func run() -> void:
	world=load("res://field_opening.tscn").instantiate()
	root.add_child(world)
	for i in 12: await physics_frame
	var kind:=OS.get_environment("RAIL_KIND")
	var enhanced:bool=world.inventory.complete("orbit_upgrade")
	var side:=Vector3.RIGHT if kind=="wood" else Vector3(1,0,-1).normalized()
	var row:=target_for(kind,side)
	if row.is_empty():
		quit(1)
		return
	var at:Vector3=row.position
	var hits_outside:=0
	place(at,side,4.50)
	for i in 200:
		await physics_frame
		var body=world.lifecycle.loaded.get(row.id)
		if body!=null: hits_outside=maxi(hits_outside,body.strikes)
	var extended_range_control:=0
	if not enhanced:
		place(at,side,3.30)
		for i in 150:
			await physics_frame
			var body=world.lifecycle.loaded.get(row.id)
			if body!=null: extended_range_control=maxi(extended_range_control,body.strikes)
	var gap:=3.30 if enhanced else (2.18 if kind=="wood" else 2.50)
	place(at,side,gap)
	var turns:=[]
	var geometry_witness:=[]
	var target=world.lifecycle.loaded.get(row.id)
	var previous=0
	for i in 280:
		await physics_frame
		if not target: target=world.lifecycle.loaded.get(row.id)
		if target and target.strikes>previous:
			previous=target.strikes
			turns.append(world.character_kit.turn_id)
			geometry_witness.append({"contact":str(world.character_kit.hit_position),"travel":str(world.character_kit.hit_travel),"tool":world.character_kit.equipped,"recorded_hits":previous,"actual_radius":world.actor.position.distance_to(at)})
			if previous>=3: break
	var report={"enhanced":enhanced,"actual_slots":world.character_kit.count,"resource":kind,"source":row.id,"at":str(at),"stand_off":gap,"outside_stand_off":4.5,"outside_hits":hits_outside,"starter_hits_at_enhanced_distance":null if enhanced else extended_range_control,"native_strikes":previous,"different_turns":turns,"actual_surface_contacts":geometry_witness}
	var ok=previous==3 and hits_outside==0 and extended_range_control==0 and turns[0]!=turns[1] and turns[1]!=turns[2]
	report["pass"]=ok
	print(JSON.stringify(report))
	world.sound.stop_playback()
	world.queue_free()
	for i in 14: await process_frame
	quit(0 if ok else 1)
