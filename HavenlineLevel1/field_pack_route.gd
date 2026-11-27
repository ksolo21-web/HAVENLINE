extends RefCounted
## Visibility graph for the two large impassable shapes. Each size of animal
## shares its static graph; only a moving origin and goal are added per search.
var obstacles: Array[PackedVector2Array] = []
var bounds: Array[Rect2] = []
var graph := AStar2D.new()
var fence := Rect2()
var stage := -1
var bank := PackedVector2Array()
var bank_bounds := Rect2()

func _corners(r: Rect2) -> PackedVector2Array:
	return PackedVector2Array([r.position,Vector2(r.end.x,r.position.y),r.end,Vector2(r.position.x,r.end.y)])

func configure(world, size: float) -> void:
	var current: int = world.field_env.perimeter_stage
	if stage == current and (not bank.is_empty() or not world.lakeshore): return
	stage = current
	if world.lakeshore and bank.is_empty():
		var polys: Array[PackedVector2Array] = Geometry2D.offset_polygon(world.lakeshore.shore,size,Geometry2D.JOIN_ROUND)
		if not polys.is_empty():
			bank = polys[0]
			bank_bounds = world.lakeshore.bounds.grow(size+.01)
	obstacles.clear()
	bounds.clear()
	graph.clear()
	if current>0:
		var r: Vector4 = world.field_env.COURTS[current-1]
		fence = Rect2(r.x,r.y,r.z-r.x,r.w-r.y).grow(size)
		obstacles.append(_corners(fence))
		bounds.append(fence)
	else:
		fence = Rect2()
	if not bank.is_empty():
		obstacles.append(bank)
		bounds.append(bank_bounds)
	for box in bounds:
		for p in _corners(box.grow(.20)):
			if is_clear_ground(p): graph.add_point(graph.get_available_point_id(),p)
	var ids := graph.get_point_ids()
	for i in ids.size():
		for j in i:
			if clear_segment(graph.get_point_position(ids[i]),graph.get_point_position(ids[j])):
				graph.connect_points(ids[i],ids[j])

func is_clear_ground(p: Vector2) -> bool:
	return (not fence.has_area() or not fence.has_point(p)) and (bank.is_empty() or not bank_bounds.has_point(p) or not Geometry2D.is_point_in_polygon(p,bank))

func clear_segment(a: Vector2,b: Vector2) -> bool:
	var span := Rect2(a,Vector2.ZERO).expand(b).grow(.001)
	for i in obstacles.size():
		if not span.intersects(bounds[i],true): continue
		var poly := obstacles[i]
		for k in poly.size():
			if Geometry2D.segment_intersects_segment(a,b,poly[k],poly[(k+1)%poly.size()]) != null:
				return false
	return true

func _stand_off(at: Vector2) -> Vector2:
	# Players can stand directly outside a wall or at the water's edge closer
	# than a wolf's shoulder width. Aim for the nearest dry position on that face.
	for i in obstacles.size():
		if not bounds[i].has_point(at): continue
		var poly := obstacles[i]
		if not Geometry2D.is_point_in_polygon(at,poly): continue
		var near := at
		var smallest := INF
		for k in poly.size():
			var p := Geometry2D.get_closest_point_to_segment(at,poly[k],poly[(k+1)%poly.size()])
			var d := at.distance_squared_to(p)
			if d < smallest: near=p; smallest=d
		var out := (near-at).normalized()
		if out.length_squared() < .01: out=(near-bounds[i].get_center()).normalized()
		return near+out*.04
	return at

func route(a: Vector2,goal: Vector2) -> PackedVector2Array:
	var b := _stand_off(goal)
	if clear_segment(a,b): return PackedVector2Array([b])
	var start := graph.get_available_point_id()
	graph.add_point(start,a)
	var end := graph.get_available_point_id()
	graph.add_point(end,b)
	for id in graph.get_point_ids():
		if id in [start,end]: continue
		var vertex := graph.get_point_position(id)
		if clear_segment(a,vertex): graph.connect_points(start,id)
		if clear_segment(b,vertex): graph.connect_points(end,id)
	var path := graph.get_point_path(start,end)
	graph.remove_point(end)
	graph.remove_point(start)
	return path.slice(1) if path.size()>1 else PackedVector2Array()
