extends RefCounted
## Static sightlines around the palisade and the lake. Distances follow the outside of the
## fence to an actual entrance, even when the closest point on the wall is behind camp.
const CLEARANCE := .76
const GATE_APPROACH := 1.12

var stage := -1
var gate_mask := -1
var points := PackedVector2Array()
var cost := PackedFloat32Array()
var exit_id := PackedInt32Array()
var goal_count := 0
var fence := Rect2()
var fence_outline := PackedVector2Array()
var lake_bounds := Rect2()
var bank := PackedVector2Array()
var river: Node3D
var actor_radius := .31
var last_feet := Vector2.INF
var via := -1
var shore_detour := Vector2.INF
var direction_target := Vector2.ZERO
var distance := 0.
var gate_index := -1

func _rect_vertices(r: Rect2) -> PackedVector2Array:
	return PackedVector2Array([r.position, Vector2(r.end.x,r.position.y), r.end, Vector2(r.position.x,r.end.y)])

func _crosses(a: Vector2, b: Vector2, outline: PackedVector2Array) -> bool:
	for i in outline.size():
		if Geometry2D.segment_intersects_segment(a,b,outline[i],outline[(i+1)%outline.size()]) != null:
			return true
	return false

func _clear(a: Vector2,b: Vector2) -> bool:
	if river and not river.travel_clear(a,b,actor_radius): return false
	var span := Rect2(a,Vector2.ZERO).expand(b)
	if stage>0 and span.intersects(fence,true) and _crosses(a,b,fence_outline):
		return false
	return bank.is_empty() or not span.intersects(lake_bounds,true) or not _crosses(a,b,bank)

func _rebuild(world, perimeter_stage: int, active_gates: int) -> void:
	stage = perimeter_stage
	gate_mask = active_gates
	last_feet = Vector2.INF
	via = -1
	points.clear()
	if stage == 0:
		var plot: Vector3 = world.field_env.buy_anchor.global_position
		points.append(Vector2(plot.x,plot.z))
		goal_count = 1
	else:
		var bounds: Vector4 = world.field_env.COURTS[stage-1]
		fence = Rect2(bounds.x,bounds.y,bounds.z-bounds.x,bounds.w-bounds.y).grow(CLEARANCE)
		fence_outline = _rect_vertices(fence)
		for i in world.gates.size():
			var pos: Vector3 = world.gates[i].global_position
			var outward := Vector2.DOWN if i==0 else Vector2.RIGHT
			points.append(Vector2(pos.x,pos.z)+outward*GATE_APPROACH)
		goal_count = world.gates.size()
		points.append_array(_rect_vertices(fence.grow(.18)))
	if world.lakeshore:
		if bank.is_empty():
			var shore: Array[PackedVector2Array] = Geometry2D.offset_polygon(world.lakeshore.shore,float(world.layout.actor_radius))
			if not shore.is_empty():
				bank = shore[0]
				lake_bounds = world.lakeshore.bounds.grow(float(world.layout.actor_radius)+.04)
		points.append_array(_rect_vertices(lake_bounds.grow(.65)))
	river = world.river
	actor_radius = float(world.layout.actor_radius)
	if river: points.append_array(river.navigation_points(actor_radius))
	var graph := AStar2D.new()
	for i in points.size(): graph.add_point(i,points[i])
	for i in points.size():
		for j in range(i):
			if _clear(points[i],points[j]): graph.connect_points(i,j)
	cost.resize(points.size())
	exit_id.resize(points.size())
	for i in points.size():
		cost[i] = INF
		exit_id[i] = -1
		for goal in goal_count:
			if stage>0 and not (gate_mask & (1<<goal)): continue
			var path := graph.get_point_path(i,goal)
			if path.is_empty(): continue
			var length := GATE_APPROACH if stage>0 else 0.
			for j in range(1,path.size()): length += path[j-1].distance_to(path[j])
			if length < cost[i]:
				cost[i] = length
				exit_id[i] = goal

func _outside_for_routing(feet: Vector2) -> Vector2:
	if stage==0 or not fence.has_point(feet): return feet
	# An actor physically touching the outer wall starts inside our planning clearance.
	# Project them to the same exterior face rather than drawing a shortcut across camp.
	var actual := fence.grow(-CLEARANCE)
	var p := feet
	if feet.x <= actual.position.x: p.x = fence.position.x-.01
	if feet.x >= actual.end.x: p.x = fence.end.x+.01
	if feet.y <= actual.position.y: p.y = fence.position.y-.01
	if feet.y >= actual.end.y: p.y = fence.end.y+.01
	return p

func update(world, feet: Vector2) -> bool:
	var active := 0
	if world.camp_active:
		for i in world.gates.size():
			if world.gates[i].active: active |= 1<<i
	var current_stage: int = world.field_env.perimeter_stage if world.camp_active else 0
	if current_stage != stage or active != gate_mask: _rebuild(world,current_stage,active)
	if stage > 0 and active == 0: return false
	var start := _outside_for_routing(feet)
	if not last_feet.is_finite() or start.distance_squared_to(last_feet)>.19*.19:
		last_feet = start
		var best := INF
		via = -1
		shore_detour = Vector2.INF
		for i in points.size():
			if exit_id[i]<0: continue
			if i>=goal_count and start.distance_squared_to(points[i])<.16*.16: continue
			var total := start.distance_to(points[i])+float(cost[i])
			if total<best and _clear(start,points[i]):
				best = total
				via = i
		if via < 0 and river:
			var detour: Vector2 = river.shore_detour(start,actor_radius)
			if start.distance_squared_to(detour) > .16*.16 and _clear(start,detour):
				for i in points.size():
					if exit_id[i] < 0: continue
					var total := detour.distance_to(points[i])+float(cost[i])
					if total < best and _clear(detour,points[i]):
						best = total
						via = i
						shore_detour = detour
	if via < 0: return false
	gate_index = exit_id[via] if stage>0 else -1
	if shore_detour.is_finite():
		direction_target = shore_detour
		distance = feet.distance_to(shore_detour)+shore_detour.distance_to(points[via])+float(cost[via])
		return true
	direction_target = points[via]
	distance = feet.distance_to(points[via])+float(cost[via])
	if via < goal_count and stage>0:
		var center: Vector3 = world.gates[gate_index].global_position
		var gate := Vector2(center.x,center.z)
		var outwards := (points[via]-gate).normalized()
		var difference := feet-gate
		if absf(difference.cross(outwards)) < .62 and difference.dot(outwards) < GATE_APPROACH+.3:
			direction_target = gate-outwards*.55
			distance = feet.distance_to(gate)
	return true
