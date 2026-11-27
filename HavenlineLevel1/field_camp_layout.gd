extends Node3D
## Player-owned building positions are absolute XZ coordinates in the level.
## The original building nodes continue owning their receivers, stock and state.
signal layout_changed

const Rules = preload("res://field_progression.gd")
const LayoutHUD = preload("res://field_layout_hud.gd")
const NAMES := {"center_hearth":"Furnace","storage_wood":"Storehouse","camp_cooker":"Cooker",
	"saw_bench":"Saw bench","quarry_drill":"Quarry drill","watchtower":"Watchtower","north_counter":"Customer counter"}
const HEIGHT := {"center_hearth":1.70,"storage_wood":3.20,"camp_cooker":1.85,
	"saw_bench":1.65,"quarry_drill":2.55,"watchtower":3.25,"north_counter":1.44}
const CLEARANCE := .33
const COUNTER := "north_counter"
var world
var active := false
var chosen := ""
var candidate := Vector2.ZERO
var candidate_reason := ""
var preview_set := false
var positions := {}
var original := {}
var overlay
var map_camera := Camera3D.new()
var ghost := Node3D.new()
var ghost_material := StandardMaterial3D.new()
var pointer := -2
var start_pointer := Vector2.ZERO
var dragging := false
var on_button := false
var graph_rects: Array[Rect2] = []
var graph := AStar2D.new()
var route_radius := -1.
var route_stage := -1
var access_cache := {}

func install(host) -> void:
	world = host
	if not get_parent(): world.add_child(self)
	name = "CampLayout"
	for id: String in NAMES:
		original[id] = xz(building(id).global_position)
	original[COUNTER] = Vector2(world.counter.CENTER_X,world.field_env.COURTS.back().y)
	add_child(ghost)
	ghost.name = "BuildingPreview"
	ghost.hide()
	ghost_material.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA_DEPTH_PRE_PASS
	ghost_material.roughness = .77
	ghost_material.cull_mode = BaseMaterial3D.CULL_DISABLED
	map_camera.name = "LayoutCamera"
	map_camera.projection = Camera3D.PROJECTION_ORTHOGONAL
	map_camera.keep_aspect = Camera3D.KEEP_HEIGHT
	add_child(map_camera)
	overlay = LayoutHUD.new()
	world.opening_hud.get_parent().add_child(overlay)
	overlay.install(self)
	world.get_viewport().size_changed.connect(_fit_map)
	world.get_window().focus_exited.connect(cancel_gesture)
	world.field_env.perimeter_changed.connect(_invalidate_routes)

static func xz(at:Vector3) -> Vector2:
	return Vector2(at.x,at.z)

static func on_ground(p:Vector2) -> Vector3:
	return Vector3(p.x,0,p.y)

func owned(id:String) -> bool:
	if id == COUNTER: return world.inventory.complete(Rules.SECOND)
	if id == Rules.STORAGE[0]: return Rules.house_tier(world.inventory)>0
	return NAMES.has(id) and world.inventory.complete(id)

func building(id:String) -> Node3D:
	match id:
		"center_hearth": return world.field_env.hearth_shell.get_parent_node_3d()
		"storage_wood": return world.depot.house
		"camp_cooker": return world.lakeshore.cooker
		"saw_bench": return world.processors.machines.wood
		"quarry_drill": return world.processors.machines.stone
		"watchtower": return world.defense_tower
		"north_counter": return world.counter
	return null

func center(id:String) -> Vector2:
	return positions.get(id,original[id])

func bounds() -> Rect2:
	var r: Array = world.layout.camp_rect_xz
	return Rect2(r[0],r[1],r[2]-r[0],r[3]-r[1])

func footprint(id:String, at:Vector2) -> Rect2:
	var size: Rect2
	match id:
		"center_hearth":
			var radius:float = world.field_env.hearth_footprint.shape.radius
			size = Rect2(-radius,-radius,2.*radius,2.*radius)
		"storage_wood": size = world.depot.FOOTPRINT
		"camp_cooker": size = world.lakeshore.BODY
		"saw_bench": size = world.processors.FOOTPRINT.wood
		"quarry_drill": size = world.processors.FOOTPRINT.stone
		"watchtower": size = world.defense_tower.FOOTPRINT
		"north_counter": size = Rect2(-world.counter.HALF_BAY,-.955,world.counter.HALF_BAY*2.,1.91)
	return Rect2(size.position+at,size.size)

func footprint_outline(id:String, at:Vector2) -> PackedVector2Array:
	if id!=Rules.HEARTH: return corners(footprint(id,at))
	var ring:=PackedVector2Array()
	var radius:float=world.field_env.hearth_footprint.shape.radius
	for i in 32: ring.append(at+Vector2.from_angle(TAU*i/32.)*radius)
	return ring

func _intersects(body:Rect2, circular:bool, box:Rect2, padding:float) -> bool:
	if not circular: return body.grow(padding).intersects(box)
	var c:=body.get_center()
	return c.distance_to(c.clamp(box.position,box.end))<body.size.x*.5+padding

func service_areas(id:String, at:Vector2) -> Array[Rect2]:
	var result:Array[Rect2] = []
	match id:
		"camp_cooker":
			result.append(Rect2(at+Vector2(-1.38,.68),Vector2(2.76,.95)))
		"saw_bench":
			result.append(Rect2(at+Vector2(-.10,.85),Vector2(1.10,.96)))
		"quarry_drill":
			result.append(Rect2(at+Vector2(-.45,1.10),Vector2(1.40,.98)))
		"north_counter":
			result.append(Rect2(at+Vector2(-1.61,.955),Vector2(3.22,1.03)))
		"storage_wood":
			var delta := at-xz(world.depot.SITE)
			for mark in [world.depot.apron,world.depot.upgrade_mark]:
				if mark==world.depot.upgrade_mark and Rules.next_storage(world.inventory).is_empty(): continue
				var p:Vector2 = xz(world.depot.APRON if mark==world.depot.apron else world.depot.UPGRADE_AT)
				result.append(_plot_rect(mark,delta+p))
	return result

func _plot_rect(mark:Node3D, at:Vector2) -> Rect2:
	var edges: MeshInstance3D = mark.get_node("Brackets")
	var box := Transform3D(mark.global_basis * edges.transform.basis,Vector3.ZERO) * edges.get_aabb()
	return Rect2(at+Vector2(box.position.x,box.position.z),Vector2(box.size.x,box.size.z))

func _fixed_clearance() -> Array[Rect2]:
	var r := bounds()
	var gap:float = world.gates[0].HALF_SPAN+.20
	var list:Array[Rect2] = [
		Rect2(-gap,r.end.y-2.65,gap*2.,2.65),
		Rect2(r.end.x-2.65,-gap,2.65,gap*2.),
		Rect2(1.72-.47,1.8-.47,.94,.94)
	]
	for id:String in world.offer_floors:
		if world.inventory.complete(id): continue
		var plot:Node3D = world.offer_floors[id]
		list.append(_plot_rect(plot,xz(plot.global_position)))
	return list

func _snap(id:String, raw:Vector2) -> Vector2:
	if id!=COUNTER: return raw.snapped(Vector2(.25,.25))
	var r := bounds()
	var offset:float = world.counter.HALF_BAY+.50
	var x := snappedf(raw.x,.5)
	if absf(raw.y-r.position.y)>1.55 or x<r.position.x+offset or x>r.end.x-offset: return raw.snapped(Vector2(.25,.25))
	return Vector2(x,r.position.y)

func reason(id:String, at:Vector2, proposed:Dictionary = {}, people:=true) -> String:
	if not owned(id): return "Purchase this building first"
	var body := footprint(id,at)
	var aisle := service_areas(id,at)
	var floor := bounds().grow(-.32)
	if id == COUNTER:
		if absf(at.y-bounds().position.y)>.001 or body.position.x<floor.position.x or body.end.x>floor.end.x:
			return "Use the north fence"
		if people and world.counter.sale_order!=0: return "Finish the current sale first"
	elif not floor.encloses(body): return "Keep the building inside the fence"
	if id=="watchtower" and at.x < bounds().end.x-4.: return "Keep the tower on the threat side"
	for use:Rect2 in aisle:
		if not floor.encloses(use): return "Leave space for loading"
	for other:String in NAMES:
		if other==id: continue
		var other_at:Vector2 = proposed.get(other,center(other))
		var their_body := footprint(other,other_at)
		# An unpaid pad can become a real machine later. Preserve its landing footprint.
		var collision:bool = _intersects(their_body,true,body,CLEARANCE) if other==Rules.HEARTH else _intersects(body,id==Rules.HEARTH,their_body,CLEARANCE)
		if collision: return "Leave room for the "+NAMES[other].to_lower()
		for use:Rect2 in aisle:
			if _intersects(their_body,other==Rules.HEARTH,use,.08): return "Clear the loading side"
		for other_use:Rect2 in service_areas(other,other_at):
			if _intersects(body,id==Rules.HEARTH,other_use,.08): return "Keep the "+NAMES[other].to_lower()+" accessible"
	for blocked:Rect2 in _fixed_clearance():
		if _intersects(body,id==Rules.HEARTH,blocked,.10): return "Keep the gate, plot and rescue lanes clear"
		for use:Rect2 in aisle:
			if use.intersects(blocked): return "Keep the working aisle clear"
	var key: Array = [id,at,world.inventory.build_order.size(),proposed.hash()]
	if not access_cache.has(key):
		if access_cache.size()>=128: access_cache.clear()
		access_cache[key]=_can_reach_working_sides(id,at,proposed)
	if not access_cache[key]: return "Keep a walking route to every station"
	if people:
		var walkers:Array = [world.actor]
		if world.survivor and world.survivor.actor.visible: walkers.append(world.survivor.actor)
		walkers.append_array(world.enemies)
		for walker in walkers:
			if not is_instance_valid(walker) or not walker.is_visible_in_tree(): continue
			var feet := Rect2(xz(walker.global_position),Vector2(.001,.001))
			if _intersects(body,id==Rules.HEARTH,feet,float(world.layout.actor_radius)+.07): return "Someone is standing here"
	return ""

# A legal-looking gap can still trap a worker if two buildings pinch the
# only path to a loading face. Check the paid layout with a player-sized disc.
func _can_reach_working_sides(moving:String, at:Vector2, proposed:Dictionary) -> bool:
	var floor:=bounds().grow(-float(world.layout.actor_radius)-.19)
	const CELL:=.25
	var grid:=AStarGrid2D.new()
	var count:=Vector2i((floor.size/CELL).floor())+Vector2i.ONE
	grid.region=Rect2i(Vector2i.ZERO,count)
	grid.diagonal_mode=AStarGrid2D.DIAGONAL_MODE_ONLY_IF_NO_OBSTACLES
	grid.update()
	var goals:Array[Vector2]=[Vector2(0.,floor.end.y-.55),Vector2(floor.end.x-.55,0.)]
	for offer:String in world.offer_floors:
		var pad:Vector2=xz(world.offer_floors[offer].global_position)
		if world.inventory.offer_open(offer) and floor.has_point(pad): goals.append(pad)
	for other:String in NAMES:
		if not owned(other): continue
		var pos:Vector2=at if other==moving else proposed.get(other,center(other))
		var body:=footprint(other,pos).grow(float(world.layout.actor_radius)+.04)
		var begin:=Vector2i(((body.position-floor.position)/CELL).ceil()).clamp(Vector2i.ZERO,count-Vector2i.ONE)
		var end:=Vector2i(((body.end-floor.position)/CELL).floor()).clamp(Vector2i.ZERO,count-Vector2i.ONE)
		if begin.x<=end.x and begin.y<=end.y: grid.fill_solid_region(Rect2i(begin,end-begin+Vector2i.ONE))
		for use:Rect2 in service_areas(other,pos): goals.append(use.get_center())
	var start:=Vector2i(((Vector2(1.72,1.8)-floor.position)/CELL).round()).clamp(Vector2i.ZERO,count-Vector2i.ONE)
	if grid.is_point_solid(start): return false
	for goal:Vector2 in goals:
		var end:=Vector2i(((goal-floor.position)/CELL).round()).clamp(Vector2i.ZERO,count-Vector2i.ONE)
		if grid.is_point_solid(end) or grid.get_id_path(start,end).is_empty(): return false
	return true

func _apply(id:String, at:Vector2) -> void:
	var node := building(id)
	match id:
		"storage_wood": world.depot.position = on_ground(at-xz(world.depot.SITE))
		"camp_cooker": world.lakeshore.move_cooker(on_ground(at))
		"north_counter": world.counter.move_to_bay(at.x)
		_: node.global_position = Vector3(at.x,node.global_position.y,at.y)
	if at.is_equal_approx(original[id]): positions.erase(id)
	else: positions[id]=at

func relocate(id:String, at:Vector2) -> bool:
	if world.persist_blocked or not owned(id) or not at.is_finite(): return false
	var dest := _snap(id,at)
	if not reason(id,dest).is_empty(): return false
	var before := center(id)
	if before.is_equal_approx(dest): return true
	_apply(id,dest)
	world._persist_world()
	if world.persist_blocked:
		_apply(id,before)
		return false
	_invalidate_routes()
	layout_changed.emit()
	return true

func snapshot() -> Dictionary:
	var result := {}
	for id:String in positions:
		var p:Vector2 = positions[id]
		result[id] = [p.x,p.y]
	return result

func restore(data:Variant) -> bool:
	if not data is Dictionary or data.size()>NAMES.size(): return false
	var proposed := original.duplicate()
	for id in data:
		if not id is String or not NAMES.has(id) or not owned(id): return false
		var raw: Variant = data[id]
		if not raw is Array or raw.size()!=2: return false
		for n in raw:
			if not (n is int or n is float) or not is_finite(float(n)): return false
		proposed[id] = Vector2(raw[0],raw[1])
	for id:String in data:
		if not reason(id,proposed[id],proposed,false).is_empty(): return false
	for id:String in NAMES:
		if not center(id).is_equal_approx(proposed[id]): _apply(id,proposed[id])
	_invalidate_routes()
	layout_changed.emit()
	return true

func obstacles() -> Array[Rect2]:
	var bodies:Array[Rect2] = []
	for id:String in NAMES:
		if owned(id): bodies.append(footprint(id,center(id)))
	return bodies

func _invalidate_routes() -> void:
	access_cache.clear()
	route_radius = -1.

static func corners(rect:Rect2) -> PackedVector2Array:
	return PackedVector2Array([rect.position,Vector2(rect.end.x,rect.position.y),rect.end,Vector2(rect.position.x,rect.end.y)])

func _clear(a:Vector2,b:Vector2) -> bool:
	var span := Rect2(a,Vector2.ZERO).expand(b).grow(.001)
	for rect:Rect2 in graph_rects:
		if not span.intersects(rect) or rect.has_point(a) or rect.has_point(b): continue
		var poly := corners(rect)
		for index in 4:
			if Geometry2D.segment_intersects_segment(a,b,poly[index],poly[(index+1)%4])!=null:
				return false
	return true

func _prepare_graph(radius:float) -> void:
	graph.clear()
	graph_rects.clear()
	route_radius = radius
	route_stage = world.inventory.build_order.size()
	var floor := bounds().grow(-.19-radius)
	for solid in obstacles(): graph_rects.append(solid.grow(radius+.05))
	var index := 0
	for rect:Rect2 in graph_rects:
		for p in corners(rect.grow(.035)):
			if floor.has_point(p) and not graph_rects.any(func(r):return r.has_point(p)):
				graph.add_point(index,p)
				index+=1
	for i in index:
		for j in i:
			if _clear(graph.get_point_position(i),graph.get_point_position(j)): graph.connect_points(i,j)

func next_waypoint(from:Vector3, to:Vector3, radius:=.26) -> Vector3:
	if not world or not world.camp_active: return to
	var a := xz(from)
	var b := xz(to)
	if not bounds().grow(.55).has_point(a) or not bounds().grow(.55).has_point(b): return to
	if radius!=route_radius or route_stage!=world.inventory.build_order.size(): _prepare_graph(radius)
	if _clear(a,b): return to
	var start := graph.get_available_point_id()
	graph.add_point(start,a)
	var goal := graph.get_available_point_id()
	graph.add_point(goal,b)
	for i in graph.get_point_ids():
		if i==start or i==goal: continue
		var p := graph.get_point_position(i)
		if _clear(a,p): graph.connect_points(start,i)
		if _clear(b,p): graph.connect_points(goal,i)
	var path := graph.get_point_path(start,goal)
	graph.remove_point(start)
	graph.remove_point(goal)
	if path.size()<2: return from
	return Vector3(path[1].x,to.y,path[1].y)

func _fit_map() -> void:
	if not active or not is_inside_tree() or not map_camera.is_inside_tree() or not world.camera.is_inside_tree(): return
	var court := bounds()
	var focus := on_ground(court.get_center()) + Vector3.UP*.65
	var facing:Vector3 = world.camera.global_basis.z.normalized()
	map_camera.global_position = focus + facing*49.
	map_camera.look_at(focus)
	var screen := get_viewport().get_visible_rect().size
	var envelope := Rect2()
	var first := true
	for corner in corners(court.grow(.70)):
		for height:float in [0.,3.1]:
			var point := map_camera.to_local(on_ground(corner)+Vector3.UP*height)
			var p := Vector2(point.x,-point.y)
			envelope = Rect2(p,Vector2.ZERO) if first else envelope.expand(p)
			first=false
	var aspect := screen.aspect()
	map_camera.size = maxf(envelope.size.x/aspect,envelope.size.y)*1.08

func open() -> void:
	if active or not world.field_ready or not world.camp_active or world.persist_blocked or world.reset_time>0: return
	active=true
	chosen=""
	preview_set=false
	candidate_reason=""
	world.clear_touch()
	world.actor.velocity = Vector3.ZERO
	world.opening_hud.hide()
	_fit_map()
	map_camera.make_current()
	overlay.sync()

func close() -> void:
	if not active: return
	ghost.hide()
	active=false
	chosen=""
	preview_set=false
	cancel_gesture()
	world.camera.make_current()
	world.opening_hud.show()
	world.clear_touch()
	overlay.sync()

func select(at:Vector2) -> bool:
	var ray := map_camera.project_ray_origin(at)
	var dir := map_camera.project_ray_normal(at)
	var picked := ""
	var nearest := INF
	for id:String in NAMES:
		if not owned(id): continue
		var rect := footprint(id,center(id))
		var volume := AABB(on_ground(rect.position),Vector3(rect.size.x,HEIGHT[id],rect.size.y))
		var hit:Variant = volume.intersects_ray(ray,dir)
		if hit!=null and ray.distance_squared_to(hit)<nearest:
			picked = id
			nearest = ray.distance_squared_to(hit)
	if picked.is_empty(): return false
	chosen = picked
	_prepare_ghost()
	candidate = center(chosen)
	candidate_reason = ""
	preview_set = false
	overlay.sync()
	return true

func _prepare_ghost() -> void:
	ghost.hide()
	for child in ghost.get_children():
		ghost.remove_child(child)
		child.queue_free()
	var original_node := building(chosen)
	var source:Node3D = original_node.get_node("AlfredNorthCounter") if chosen==COUNTER else original_node
	var base := Transform3D(Basis.IDENTITY,on_ground(center(chosen))).affine_inverse()
	for piece:MeshInstance3D in source.find_children("*","MeshInstance3D",true,false):
		if not piece.mesh or not piece.is_visible_in_tree(): continue
		var replica := MeshInstance3D.new()
		replica.mesh = piece.mesh
		replica.material_override = ghost_material
		replica.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		ghost.add_child(replica)
		replica.transform = base * piece.global_transform

func _update_ghost() -> void:
	ghost.visible = active and not chosen.is_empty() and preview_set
	if not ghost.visible: return
	ghost.global_position = on_ground(candidate)
	ghost_material.albedo_color = Color("#69dbaaaa") if candidate_reason.is_empty() else Color("#ff866c98")

func preview(at:Vector2) -> void:
	if chosen.is_empty(): return
	var floor_point:Variant = Plane(Vector3.UP,0.).intersects_ray(map_camera.project_ray_origin(at),map_camera.project_ray_normal(at))
	if floor_point==null: return
	candidate = _snap(chosen,xz(floor_point))
	candidate_reason = reason(chosen,candidate)
	preview_set = not candidate.is_equal_approx(center(chosen))
	_update_ghost()
	overlay.sync()

func confirm() -> void:
	if not preview_set or not candidate_reason.is_empty(): return
	if not relocate(chosen,candidate):
		candidate_reason = world.persist_error if world.persist_blocked else reason(chosen,candidate)
		overlay.sync()
		return
	chosen=""
	ghost.hide()
	preview_set=false
	candidate_reason=""
	overlay.sync()

func cancel_gesture() -> void:
	pointer=-2
	dragging=false
	on_button=false

func handle_input(event:InputEvent) -> bool:
	if not overlay: return false
	if event is InputEventKey and event.pressed and not event.echo:
		if active and event.physical_keycode==KEY_ESCAPE:
			close()
			return true
		if active and event.physical_keycode==KEY_ENTER:
			confirm()
			return true
		if event.physical_keycode==KEY_M and world.camp_active:
			if active: close()
			else: open()
			return true
	if not (event is InputEventScreenTouch or event is InputEventMouseButton or event is InputEventScreenDrag or event is InputEventMouseMotion): return active
	if event.device==InputEvent.DEVICE_ID_EMULATION: return active
	if event is InputEventMouseButton and event.button_index!=MOUSE_BUTTON_LEFT: return active
	var idx:int = event.index if event is InputEventScreenTouch or event is InputEventScreenDrag else -1
	if event is InputEventScreenTouch and event.canceled:
		if idx==pointer: cancel_gesture()
		return active
	if event is InputEventScreenDrag or event is InputEventMouseMotion:
		if active and idx==pointer and not on_button and not chosen.is_empty() and event.position.distance_to(start_pointer)>12.:
			dragging=true
			preview(event.position)
		return active
	if not event.pressed:
		if idx!=pointer: return active
		if active and dragging and not on_button: preview(event.position)
		cancel_gesture()
		return true
	if pointer!=-2: return active
	var point:Vector2 = event.position
	if not active:
		if not overlay.launcher.visible or not overlay.launcher.get_global_rect().has_point(point): return false
		open()
		pointer=idx
		on_button=true
		return true
	pointer=idx
	start_pointer=point
	on_button=true
	if overlay.done.get_global_rect().has_point(point): close()
	elif overlay.place.visible and overlay.place.get_global_rect().has_point(point): confirm()
	elif overlay.back.visible and overlay.back.get_global_rect().has_point(point):
		chosen=""
		ghost.hide()
		preview_set=false
		candidate_reason=""
		overlay.sync()
	else:
		on_button=false
		if chosen.is_empty(): select(point)
		else: preview(point)
	return true
