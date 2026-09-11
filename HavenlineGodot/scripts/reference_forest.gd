extends RefCounted
# T01 approved tree assets/count remain unchanged. Task 2's later full-map river
# may intersect perimeter placement points outside today's playable rectangle, so
# only those conflicting transforms move outward on the SAME river side.
const Scenery = preload("res://scripts/scenery_batch.gd")
const Surface = preload("res://scripts/outpost_surface.gd")
const River = preload("res://scripts/river_geometry.gd")
const SPACING := 1.85
const CELL := 10.0
const RIVER_TREE_MARGIN := 2.25

static func _trunk_seated(p: Vector2, scale_factor: float) -> bool:
	var centre:=Surface.height_at(p)-.17*scale_factor
	for offset in [Vector2(.23,0),Vector2(-.23,0),Vector2(0,.23),Vector2(0,-.23)]:
		if centre>Surface.height_at(p+offset*scale_factor): return false
	return true

static func _river_safe_tree_point(original: Vector2, scale_factor: float) -> Vector2:
	# Preserve the original point whenever the new river did not affect it.
	if River.shore_distance(original)>=RIVER_TREE_MARGIN and _trunk_seated(original,scale_factor): return original
	var original_query:=River.query(original)
	var side:=float(original_query.side)
	var p:=River.dry_position(original,RIVER_TREE_MARGIN)
	# Move only as far as necessary to seat the trunk on stable terrain beyond the
	# sculpted bank. This never crosses the river and never changes tree identity.
	for _iteration in range(8):
		if _trunk_seated(p,scale_factor): return p
		var q:=River.query(p)
		p+=Vector2(q.north_normal)*side*.25
	return p

static func placements(bounds: Vector2) -> Array[Dictionary]:
	var result: Array[Dictionary] = []
	var rng := RandomNumberGenerator.new()
	rng.seed = 472091
	for row in range(-15,16):
		for column in range(-15,16):
			var original := Vector2(column*SPACING + (SPACING*.5 if posmod(row,2)==1 else 0.0), row*SPACING)
			original += Vector2(rng.randf_range(-.12,.12),rng.randf_range(-.12,.12))
			# Keep the T01 inclusion rule exactly: no extra trees, no lost trees, and
			# no Task 3 boundary redesign hidden in this river compatibility repair.
			if absf(original.x) < bounds.x+1.7 and absf(original.y) < bounds.y+1.7: continue
			if absf(original.x) < 3.5: continue
			var scale_factor := rng.randf_range(.78,1.03)
			var p:=_river_safe_tree_point(original,scale_factor)
			result.append({"point":p,"original_point":original,"river_relocated":p.distance_squared_to(original)>.000001,
				"variant":1+posmod(row+column,3),"scale":scale_factor,"angle":rng.randf()*TAU,
				"cell":Vector2i(floori(p.x/CELL),floori(p.y/CELL))})
	return result

static func build(game) -> Dictionary:
	var groups := {}
	var places := placements(Vector2(game.sim.contract.world.boundX,game.sim.contract.world.boundZ))
	var relocated:=0;var max_shift:=0.0
	for record in places:
		if record.river_relocated:
			relocated+=1;max_shift=maxf(max_shift,Vector2(record.point).distance_to(Vector2(record.original_point)))
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
	return {"task":"T01","instances":places.size(),"spatial_batches":batches,
		"river_relocated_instances":relocated,"maximum_river_relocation":max_shift,
		"tree_assets_changed":false,"tree_count_changed":false,"same_side_relocation":true,
		"no_playable_bounds_change":true,"physical_4k60_verified":false,"independent_critic_approved":false}

static func set_player_clearance(game, focus: Vector3, enabled: bool = true) -> int:
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
