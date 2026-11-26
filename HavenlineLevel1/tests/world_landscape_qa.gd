extends SceneTree
## Run with a fresh XDG_DATA_HOME or a marked disposable profile.
var world
var checks := {}
var report := {}

func _initialize() -> void:
	call_deferred("run")

func check(label_: String, ok: bool) -> void:
	checks[label_] = ok
	if not ok: push_error(label_)

func frames(count: int) -> void:
	for i in count: await physics_frame

func place(at: Vector3) -> void:
	world.actor.position = at
	world.actor.velocity = Vector3.ZERO
	world.camera.position = at + Vector3(7,11,11)
	await frames(20)

func run() -> void:
	world = load("res://field_opening.tscn").instantiate()
	root.add_child(world)
	await frames(20)
	var land = world.world_landscape
	check("Normal entry creates the streamed world", land != null and land.limit == 16)
	var counts := {"stone":0,"wood":0}
	var unique := {}
	var maximum := 0
	var minimum := 1000
	var occupied := 0
	for z in range(-16,16):
		for x in range(-16,16):
			var rows: Array = land.describe_chunk(Vector2i(x,z))
			maximum = maxi(maximum,rows.size())
			minimum = mini(minimum,rows.size())
			if not rows.is_empty(): occupied+=1
			for row in rows:
				counts[row.kind]+=1
				unique[row.id]=true
	report["census"] = {"wood":counts.wood,"stone":counts.stone,"distinct_ids":unique.size(),"populated_chunks":occupied,"min_sources":minimum,"max_sources":maximum}
	check("All 1,024 chunks contain usable resources",occupied == 1024)
	check("All source keys are unique",unique.size() == counts.wood + counts.stone)
	check("One square kilometre contains both quarry and timber",counts.wood > 10000 and counts.stone > 1200)
	var collision: StaticBody3D = world.get_node("SnowGround_NoPaintedPaths")
	var shape: BoxShape3D = collision.find_children("*","CollisionShape3D",false,false)[0].shape
	check("Ground collider is 1,024 metres square",shape.size.x == 1024.0 and shape.size.z == 1024.0)
	var normals = land.get_node("BoundarySnowDrifts").mesh.surface_get_arrays(0)[Mesh.ARRAY_NORMAL]
	var lit := Vector3.ZERO
	for n: Vector3 in normals: lit += n
	check("Snow ridge normals face the sky",lit.y > 0)
	var resident := 0
	var revisited := []
	var remote := Vector3(89,0,-69)
	for at in [remote,Vector3(510,0,510),Vector3(-510,0,-510),Vector3(-510,0,510),Vector3(510,0,-510), remote]:
		await place(at)
		resident = maxi(resident,land.chunks.size())
		var key: Vector2i=land.chunk_for(at)
		check("Loaded snow cell "+str(key),land.chunks.has(key))
		if at == remote:
			var group: Dictionary=land.chunks[key]
			var ids: Array=[]
			for row in group.sources: ids.append(row.id)
			if revisited.is_empty(): revisited=ids
			else: check("Revisited cell has identical resource IDs",ids==revisited)
	check("World keeps at most nine cells resident",resident<=9)
	report["max_resident_chunks"] = resident
	var samples: Array=land.describe_chunk(land.chunk_for(remote))
	var stone: Dictionary={}
	var pine: Dictionary={}
	for row in samples:
		if row.kind=="wood" and pine.is_empty(): pine=row
		if row.kind=="stone" and stone.is_empty(): stone=row
	for row: Dictionary in [pine,stone]:
		await place(row.position+Vector3(1.45,0,.42))
		var live=world.lifecycle.loaded.get(row.id)
		check("Streamed "+row.kind+" uses actual harvest object",is_instance_valid(live) and world.surfaces.has(live))
		if not is_instance_valid(live):continue
		world.lifecycle.deplete(live)
		await place(Vector3(-125,0,95))
		check("Unloading preserves "+row.kind+" cooldown",not world.lifecycle.loaded.has(row.id) and not world.is_source_available(row.id))
		await place(row.position+Vector3(1.45,0,.42))
		live=world.lifecycle.loaded.get(row.id)
		check("Revisiting cannot restore "+row.kind+" early",is_instance_valid(live) and not world.is_source_available(row.id))
		world.lifecycle.advance(world.lifecycle.wood_seconds+world.lifecycle.stone_seconds)
		check("Resource becomes harvestable after its timer "+row.kind,world.is_source_available(row.id) and live.phase in ["rooted","seated"])
	await place(Vector3(16,0,-4))
	# A real virtual stick travels past the old prototype boundary.
	var press := InputEventScreenTouch.new()
	press.index=0
	press.position=Vector2(360,535)
	press.pressed=true
	root.push_input(press,true)
	var drag := InputEventScreenDrag.new()
	drag.index=0
	var cam_right: Vector3=world.camera.global_basis.x
	var cam_near: Vector3=cam_right.cross(Vector3.UP)
	drag.position=press.position+Vector2(Vector3.RIGHT.dot(cam_right),Vector3.RIGHT.dot(cam_near))*95
	root.push_input(drag,true)
	await frames(270)
	press.pressed=false
	root.push_input(press,true)
	report["touch_travel_end_x"] = world.actor.position.x
	check("Live joystick travels beyond the previous snow boundary",world.actor.position.x>22)
	# Probe a genuine remote plateau under the capsule with the physics world.
	var here: Vector3=world.actor.position
	var hit=world.get_world_3d().direct_space_state.intersect_ray(PhysicsRayQueryParameters3D.create(here+Vector3.UP*3,here-Vector3.UP*2,1,[world.actor.get_rid()]))
	check("Actual walk on solid snow",not hit.is_empty() and absf(hit.position.y)<.02)
	report["checks"]=checks
	print("WORLD_LANDSCAPE_QA "+JSON.stringify(report))
	world.sound.stop_playback()
	await frames(25)
	world.queue_free()
	await frames(6)
	quit(1 if false in checks.values() else 0)
