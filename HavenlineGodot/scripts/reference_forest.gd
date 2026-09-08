extends RefCounted
# T01: trees only. No changes to playable bounds, action/resource state or camera.
const Scenery = preload("res://scripts/scenery_batch.gd")
const Surface = preload("res://scripts/outpost_surface.gd")
const SPACING := 1.85
const CELL := 10.0

static func placements(bounds: Vector2) -> Array[Dictionary]:
	var result: Array[Dictionary] = []
	var rng := RandomNumberGenerator.new()
	rng.seed = 472091
	for row in range(-15,16):
		for column in range(-15,16):
			var p := Vector2(column*SPACING + (SPACING*.5 if posmod(row,2)==1 else 0.0), row*SPACING)
			p += Vector2(rng.randf_range(-.12,.12),rng.randf_range(-.12,.12))
			# Keep every authored trunk/crown outside the existing playable rectangle.
			# Boundary/route redesign is T03, not smuggled into this asset task.
			if absf(p.x) < bounds.x+1.7 and absf(p.y) < bounds.y+1.7: continue
			if absf(p.x) < 3.5: continue # Existing north/south approaches stay open.
			var scale_factor := rng.randf_range(.78,1.03)
			result.append({"point":p,"variant":1+posmod(row+column,3),"scale":scale_factor,"angle":rng.randf()*TAU,"cell":Vector2i(floori(p.x/CELL),floori(p.y/CELL))})
	return result

static func build(game) -> Dictionary:
	var groups := {}
	var places := placements(Vector2(game.sim.contract.world.boundX,game.sim.contract.world.boundZ))
	for record in places:
		var key := "%s:%d" % [record.cell,record.variant]
		if not groups.has(key): groups[key] = {"variant":record.variant,"transforms":[]}
		var p: Vector2 = record.point
		var transform := Transform3D(Basis(Vector3.UP,record.angle).scaled(Vector3.ONE*record.scale),Vector3(p.x,Surface.height_at(p),p.y))
		groups[key].transforms.append(transform)
	var batches := 0
	for key in groups:
		var group: Dictionary = groups[key]
		var asset := "world/pine_%d" % group.variant
		if not game.merged_cache.has(asset):
			game.merged_cache[asset] = Scenery.compile(load("res://assets/reference_forest/pine_%d.glb" % group.variant))
		var transforms: Array[Transform3D] = []
		transforms.assign(group.transforms)
		var batch := Scenery.instances(game.merged_cache[asset],transforms,game.world)
		batch.name = "ReferenceForest_%d" % batches
		batches += 1
	return {"task":"T01","instances":places.size(),"spatial_batches":batches,"no_playable_bounds_change":true,"physical_4k60_verified":false,"independent_critic_approved":false}

static func set_player_clearance(game, focus: Vector3, enabled: bool = true) -> int:
	# Shared shader parameters update three meshes, not hundreds of tree nodes.
	# The shader evaluates each MultiMesh instance's world transform separately.
	var updated := 0
	for variant in range(1,4):
		var key := "world/pine_%d" % variant
		if not game.merged_cache.has(key): continue
		var mesh: ArrayMesh = game.merged_cache[key]
		for surface in mesh.get_surface_count():
			var material = mesh.surface_get_material(surface)
			if material is ShaderMaterial:
				material.set_shader_parameter("player_focus_world",focus)
				material.set_shader_parameter("player_clearance_enabled",enabled)
				updated += 1
	return updated
