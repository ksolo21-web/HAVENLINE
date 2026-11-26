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

# When a bank masks the player, the renderer temporarily overrides its surfaces.
# Compare either its saved ordinary surfaces or the materials actually on screen.
func bank_materials_match(visual: MeshInstance3D, proxy: Mesh, saved: Array = []) -> bool:
	if visual.mesh.get_surface_count() != proxy.get_surface_count(): return false
	for i in proxy.get_surface_count():
		var surface := visual.get_active_material(i)
		if not saved.is_empty():
			surface = saved[i] if saved[i] else visual.mesh.surface_get_material(i)
		if surface == null or surface != proxy.surface_get_material(i): return false
	return true

func check_bank_streaming(land: Node, sample: Dictionary, kind: String) -> void:
	var at := Vector3(sample.x, 0.0, sample.z)
	await place(at + Vector3(9.5, 0, 0))
	var chunk: Dictionary = land.chunks[land.chunk_for(at)]
	var rows: Array = chunk.sources.filter(func(r: Dictionary): return r.id == sample.id)
	if rows.size() != 1:
		check(kind+" has a single stable row", false)
		return
	var row: Dictionary = rows[0]
	check(kind+" shows the distant source proxy", row.proxy_visible and not is_instance_valid(row.live))
	# The bank promotes within five metres. Inspect its undamaged geometry
	# before approaching the automatic orbiting pickaxe's contact range.
	await place(at + Vector3(4.5,0,0))
	var live = world.lifecycle.loaded.get(row.id)
	if not is_instance_valid(live):
		check(kind+" promotes to a mineable bank", false)
		return
	check(kind+" promotes once with physical contact geometry", world.surfaces.has(live) and not row.proxy_visible and row.live == live)
	var meshes: Array[MeshInstance3D] = []
	world.meshes(live, meshes)
	var batches: Array = chunk.batches[row.variant]
	var parity := meshes.size() == batches.size() and not meshes.is_empty()
	for i in mini(meshes.size(), batches.size()):
		var batch: Dictionary = batches[i]
		var proxy_mesh: Mesh = batch.mesh.mesh
		var visual: MeshInstance3D = meshes[i]
		parity = parity and (live.global_transform * batch.local).is_equal_approx(visual.global_transform)
		parity = parity and proxy_mesh.get_aabb().is_equal_approx(visual.mesh.get_aabb()) and proxy_mesh.get_surface_count() == visual.mesh.get_surface_count()
		parity = parity and bank_materials_match(visual, proxy_mesh)
	check(kind+" proxy uses the live bank scale, transform, bounds and surfaces", parity)
	await place(at + Vector3(1.5,0,.4))
	var close_surfaces_match := true
	for i in mini(meshes.size(), batches.size()):
		var saved: Array = world.field_env.resource_sightline.opened.get(meshes[i], [])
		close_surfaces_match = close_surfaces_match and bank_materials_match(meshes[i], batches[i].mesh.mesh, saved)
	check(kind+" retains its authored surfaces during the close approach", close_surfaces_match)
	await place(at + Vector3(4.5,0,0))
	var restored: bool = row.live == live and not row.proxy_visible
	for i in mini(meshes.size(), batches.size()):
		restored = restored and bank_materials_match(meshes[i], batches[i].mesh.mesh)
	check(kind+" restores the ordinary material while the same bank is still live", restored)
	await place(at + Vector3(9.5,0,0))
	check(kind+" returns to proxy on release", row.proxy_visible and not is_instance_valid(row.live) and not world.lifecycle.loaded.has(row.id))

func run() -> void:
	world = load("res://field_opening.tscn").instantiate()
	root.add_child(world)
	await frames(20)
	var land = world.world_landscape
	check("Normal entry creates the streamed world", land != null and land.limit == 16)
	var counts := {"stone":0,"wood":0,"metal":0,"coal":0,"slate":0}
	var nearest := {}
	var clearance_ok := true
	var repeatable := true
	var legacy_digest := HashingContext.new()
	legacy_digest.start(HashingContext.HASH_SHA256)
	# This source definition without a host describes the original seeded world,
	# before the exterior inlet reserves its authored footprint.
	var original = land.get_script().new()
	original.district = land.district
	var shoreline_only := true
	var reserved := []
	var unique := {}
	var maximum := 0
	var minimum := 1000
	var occupied := 0
	for z in range(-16,16):
		for x in range(-16,16):
			var key := Vector2i(x,z)
			var rows: Array = land.describe_chunk(key)
			var expected := []
			for row in original.describe_chunk(key):
				if row.kind in ["wood","stone"]:
					legacy_digest.update(var_to_bytes([row.id,row.kind,row.variant,row.position,row.yaw,row.scale]))
				if world.lakeshore.reserves(row.position) or world.processors.reserves(row.position):
					reserved.append(row.id)
					var nearby := Rect2(-55,-4,44,41).has_point(Vector2(row.position.x,row.position.z))
					shoreline_only = shoreline_only and nearby and row.kind in ["wood","stone"]
				else:
					expected.append(row)
			shoreline_only = shoreline_only and rows == expected
			maximum = maxi(maximum,rows.size())
			minimum = mini(minimum,rows.size())
			if not rows.is_empty(): occupied+=1
			for row in rows:
				counts[row.kind]+=1
				if row.kind not in ["wood","stone"]:
					var point: Vector3 = row.position
					var distance := point.length()
					if not nearest.has(row.kind) or distance < nearest[row.kind].distance:
						nearest[row.kind] = {"id":row.id,"x":point.x,"z":point.z,"distance":distance}
					clearance_ok = clearance_ok and distance >= land.FIRST_MINERAL_RADIUS
					for other in rows:
						if other.id != row.id:
							clearance_ok = clearance_ok and point.distance_to(other.position) >= land.BANK_CLEARANCE
					repeatable = repeatable and land.describe_chunk(Vector2i(x,z)).back() == row
				unique[row.id]=true
	original.free()
	report["reserved_shoreline_ids"] = reserved
	check("Only sources in the authored exterior inlet are displaced",not reserved.is_empty() and shoreline_only)
	report["nearest_minerals"] = nearest
	report["census"] = {"resources":counts,"wood":counts.wood,"stone":counts.stone,"distinct_ids":unique.size(),"populated_chunks":occupied,"min_sources":minimum,"max_sources":maximum}
	check("All 1,024 chunks contain usable resources",occupied == 1024)
	check("All source keys are unique",unique.size() == counts.wood + counts.stone + counts.metal + counts.coal + counts.slate)
	check("All original source IDs, variants, transforms and ordering match the shipped map",legacy_digest.finish().hex_encode() == "cec2c42cd1b35a58bda20f42639445c0c05b9f9fd5d73339f578426ef6234c28")
	check("Mineral banks recur in distant districts",counts.metal >= 10 and counts.coal >= 10 and counts.slate >= 10)
	check("Mineral banks preserve the start, expedition and clearance",clearance_ok)
	check("Mineral district placement is deterministic",repeatable)
	check("One square kilometre contains both quarry and timber",counts.wood > 10000 and counts.stone > 1200)
	for kind: String in nearest:
		await check_bank_streaming(land, nearest[kind], kind)
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
		world.lifecycle.advance(world.lifecycle.wood_seconds+world.lifecycle.mining_seconds)
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
	await preload("res://tests/lifecycle_test_profile.gd").drain_field_audio(self, world)
	world.queue_free()
	await frames(6)
	quit(1 if false in checks.values() else 0)
