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
const FRAME_PAD := 0.08
const LANE_HALF := 3.5

static func _trunk_seated(p: Vector2, scale_factor: float) -> bool:
	var centre:=Surface.height_at(p)-.17*scale_factor
	for offset in [Vector2(.23,0),Vector2(-.23,0),Vector2(0,.23),Vector2(0,-.23)]:
		if centre>Surface.height_at(p+offset*scale_factor): return false
	return true

static func _outside_frame(p:Vector2,bounds:Vector2)->bool:
	return not (absf(p.x)<bounds.x+1.7 and absf(p.y)<bounds.y+1.7) and absf(p.x)>=LANE_HALF

static func _preserve_t01_frame(candidate:Vector2,original:Vector2,bounds:Vector2)->Vector2:
	var p:=candidate
	var bx:=bounds.x+1.7;var by:=bounds.y+1.7
	# Preserve whichever original perimeter side(s) made this a T01 decorative
	# forest placement. A later river repair may move along the bank, but may not
	# turn a perimeter tree into playable-area scenery or close the N/S lane.
	if absf(original.x)>=bx:
		var sign_x:=1.0 if original.x>=0.0 else -1.0
		p.x=sign_x*maxf(absf(p.x),bx+FRAME_PAD)
	if absf(original.y)>=by:
		var sign_y:=1.0 if original.y>=0.0 else -1.0
		p.y=sign_y*maxf(absf(p.y),by+FRAME_PAD)
	if absf(p.x)<LANE_HALF:
		var lane_sign:=1.0 if original.x>=0.0 else -1.0
		p.x=lane_sign*(LANE_HALF+FRAME_PAD)
	return p

static func _river_safe_tree_point(original: Vector2, scale_factor: float,bounds:Vector2) -> Vector2:
	# Preserve the original point whenever the new river did not affect it.
	if River.shore_distance(original)>=RIVER_TREE_MARGIN and _trunk_seated(original,scale_factor): return original
	var original_query:=River.query(original)
	var side:=float(original_query.side)
	var p:=_preserve_t01_frame(River.dry_position(original,RIVER_TREE_MARGIN),original,bounds)
	# Reconcile all three invariants together: same river side/margin, original T1
	# perimeter envelope/lane, and seated trunk. Nothing changes identity/asset.
	for _iteration in range(16):
		p=_preserve_t01_frame(p,original,bounds)
		if River.shore_distance(p)<RIVER_TREE_MARGIN-.002:
			p=_preserve_t01_frame(River.dry_position(p,RIVER_TREE_MARGIN+.01),original,bounds)
		if River.shore_distance(p)>=RIVER_TREE_MARGIN-.002 and _outside_frame(p,bounds) and _trunk_seated(p,scale_factor):
			return p
		var q:=River.query(p)
		p+=Vector2(q.north_normal)*side*.25
	return _preserve_t01_frame(p,original,bounds)

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
			if absf(original.x) < LANE_HALF: continue
			var scale_factor := rng.randf_range(.78,1.03)
			var p:=_river_safe_tree_point(original,scale_factor,bounds)
			result.append({"point":p,"original_point":original,"river_relocated":p.distance_squared_to(original)>.000001,
				"variant":1+posmod(row+column,3),"scale":scale_factor,"angle":rng.randf()*TAU,
				"cell":Vector2i(floori(p.x/CELL),floori(p.y/CELL))})
	return result

static func build(game) -> Dictionary:
	var groups := {}
	var bounds:=Vector2(game.sim.contract.world.boundX,game.sim.contract.world.boundZ)
	var places := placements(bounds)
	var relocated:=0;var max_shift:=0.0;var frame_safe:=true;var river_safe:=true
	for record in places:
		if record.river_relocated:
			relocated+=1;max_shift=maxf(max_shift,Vector2(record.point).distance_to(Vector2(record.original_point)))
		frame_safe=frame_safe and _outside_frame(record.point,bounds)
		river_safe=river_safe and River.shore_distance(record.point)>=RIVER_TREE_MARGIN-.002
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
		"t01_frame_safe":frame_safe,"river_margin_safe":river_safe,
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
