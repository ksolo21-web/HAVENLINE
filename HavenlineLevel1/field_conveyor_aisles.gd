extends RefCounted
## A storehouse queue and an appliance use the same reachable serving floor
## as the player. This local grid exists only after a paid conveyor arrives.
const STEP:=.14
const Gauge=preload("res://field_conveyor_gauge.gd")
const SOLE:=.31
const Walk=preload("res://field_conveyor_crossings.gd")
var world
var grid:=AStarGrid2D.new()
var boundary:=Rect2()
var rail_cells:Dictionary={}
var buildings:Array[Rect2]=[]
var hearth:=Rect2()
var services:Dictionary={}
var paths:Dictionary={}
var public_cells:Dictionary={}
var ready:=false

static func _bucket(p:Vector2) -> Vector2i:return Vector2i(floori(p.x/.90),floori(p.y/.90))
func _key(p:Vector2) -> Vector2i:return Vector2i(((p-grid.offset)/STEP).round())
func _at(cell:Vector2i) -> Vector2:return grid.offset+Vector2(cell)*STEP
static func _closest(p:Vector2,a:Vector2,b:Vector2) -> Vector2:
	if a.distance_squared_to(b)<.000001:return a
	return Geometry2D.get_closest_point_to_segment(p,a,b)

func install(host,routes:Dictionary,gauge) -> void:
	world=host
	boundary=world.camp_layout.bounds()
	buildings=world.camp_layout.obstacles()
	hearth=world.camp_layout.footprint("center_hearth",world.camp_layout.center("center_hearth"))
	buildings.erase(hearth)
	for path:PackedVector3Array in routes.values():
		path=Walk.resample(path)
		for i in range(1,path.size()):
			var a:=path[i-1]
			var b:=path[i]
			if maxf(a.y,b.y)<-.12 or minf(a.y,b.y)>1.96:continue
			var first:=Walk.flat(a)
			var second:=Walk.flat(b)
			var half_width:=maxf(gauge.at(a),gauge.at(b))*.5+.002
			var reach:=Vector2.ONE*(half_width+.66)
			var low:=_bucket(first.min(second)-reach)
			var high:=_bucket(first.max(second)+reach)
			var record:=[first,second,half_width]
			for x in range(low.x,high.x+1):
				for z in range(low.y,high.y+1):
					var key:=Vector2i(x,z)
					if not rail_cells.has(key):rail_cells[key]=[]
					rail_cells[key].append(record)
	var court:=boundary.grow(-.35)
	grid.region=Rect2i(Vector2i.ZERO,Vector2i((court.size/STEP).floor())+Vector2i.ONE)
	grid.offset=court.position
	grid.cell_size=Vector2.ONE*STEP
	grid.diagonal_mode=AStarGrid2D.DIAGONAL_MODE_ONLY_IF_NO_OBSTACLES
	grid.update()
	var targets:={
		"store":Walk.flat(world.depot.apron.global_position),
		"wood":Walk.flat(world.processors.apron_position("wood")),
		"stone":Walk.flat(world.processors.apron_position("stone")),
		"meat":Walk.flat(world.lakeshore.apron_position()),
		"cooker_output":Walk.flat(world.lakeshore.output_apron_position()),
		"counter":Walk.flat(world.counter.service_point.global_position)}
	for y in grid.region.size.y:
		for x in grid.region.size.x:
			var cell:=Vector2i(x,y)
			var p:=_at(cell)
			if _body_clear(p,.36) and disc_clear(p,SOLE+.026):continue
			grid.set_point_solid(cell)
	var safe:=_free_cell(Vector2(1.72,1.8),false)
	if safe==Vector2i(-999,-999):return
	var todo:Array[Vector2i]=[safe]
	public_cells[safe]=true
	var best:Dictionary={}
	for id:String in targets:best[id]=INF
	var offset:=0
	while offset<todo.size():
		var at:=todo[offset]
		offset+=1
		var position:=_at(at)
		for id:String in targets:
			var closeness:float=position.distance_squared_to(targets[id])
			if closeness>=best[id] or closeness>20.:continue
			var p:=Vector3(position.x,0,position.y)
			var accepts:=false
			match id:
				"store":accepts=world.depot.at_loading_area(p)
				"wood","stone":accepts=world.processors.at_station(p)==id and not world.lakeshore.at_cooker(p)
				"meat":accepts=world.lakeshore.at_cooker(p)
				"cooker_output":accepts=world.lakeshore.at_output(p)
				"counter":accepts=world.counter.at_service(p)
			if accepts:
				best[id]=closeness
				services[id]=p
		for dir:Vector2i in [Vector2i.LEFT,Vector2i.RIGHT,Vector2i.UP,Vector2i.DOWN]:
			var next:=at+dir
			if public_cells.has(next) or not grid.region.has_point(next) or grid.is_point_solid(next):continue
			public_cells[next]=true
			todo.append(next)
	ready=true

func _body_clear(p:Vector2,margin:=.323) -> bool:
	if p.distance_squared_to(hearth.get_center())<pow(hearth.size.x*.5+margin,2):return false
	for box:Rect2 in buildings:
		if p.distance_squared_to(p.clamp(box.position,box.end))<margin*margin:return false
	return true

func _body_line(a:Vector2,b:Vector2,margin:float) -> bool:
	if not _body_clear(a,margin) or not _body_clear(b,margin):return false
	if _closest(hearth.get_center(),a,b).distance_to(hearth.get_center())<hearth.size.x*.5+margin:return false
	var span:=Rect2(a,Vector2.ZERO).expand(b).grow(margin+.002)
	for box in buildings:
		if not span.intersects(box):continue
		var vertices:=[box.position,Vector2(box.end.x,box.position.y),box.end,Vector2(box.position.x,box.end.y)]
		for i in 4:
			var p:Vector2=vertices[i]
			var q:Vector2=vertices[(i+1)%4]
			if Geometry2D.segment_intersects_segment(a,b,p,q)!=null:return false
			if p.distance_squared_to(_closest(p,a,b))<margin*margin:return false
	return true

func _step_clear(a:Vector2,b:Vector2) ->bool:
	return _body_line(a,b,.331) and line_clear(a,b,.309)

# A foot exactly tangent to a rounded building corner needs one step out to
# the clear grid before it can use a long diagonal waypoint.
func _escape(start:Vector2,aim:Vector2) -> Vector2:
	var cell:=_key(start)
	var best:=INF
	var result:=start
	for dx in range(-2,3):
		for dz in range(-2,3):
			var id:=cell+Vector2i(dx,dz)
			if not grid.region.has_point(id) or grid.is_point_solid(id):continue
			var p:=_at(id)
			if p.distance_to(start)<.045:continue
			if not _body_line(start,p,.288) or not line_clear(start,p,.277):continue
			var score:=p.distance_to(aim)+p.distance_to(start)*.28
			if score<best:
				result=p
				best=score
	return result

func disc_clear(p:Vector2,radius:float) -> bool:
	for seg:Array in rail_cells.get(_bucket(p),[]):
		var radius2:=pow(radius+float(seg[2]),2)
		if p.distance_squared_to(_closest(p,seg[0],seg[1]))<radius2:return false
	return true

func line_clear(a:Vector2,b:Vector2,radius:float,bodies:=false) -> bool:
	if bodies and not _body_line(a,b,radius+.006):return false
	var steps:=maxi(1,ceili(a.distance_to(b)/.075))
	for i in steps+1:
		var at:=a.lerp(b,float(i)/steps)
		if not disc_clear(at,radius):return false
	return true

func constrain(from:Vector3,to:Vector3,radius:float) -> Vector3:
	if rail_cells.is_empty():return to
	var p:=Walk.flat(to)
	if disc_clear(p,radius):return to
	var previous:=Walk.flat(from)
	var result:=p
	for iteration in 3:
		var moved:=false
		for seg:Array in rail_cells.get(_bucket(result),[]):
			var near:=_closest(result,seg[0],seg[1])
			var delta:=result-near
			var reach:=float(seg[2])+radius+.002
			if delta.length_squared()>=reach*reach:continue
			if delta.length_squared()<.000001:delta=previous-near
			if delta.length_squared()<.000001:delta=Vector2.RIGHT
			result=near+delta.normalized()*reach
			moved=true
		if not moved:break
	if _body_clear(result) and disc_clear(result,radius):
		return Vector3(result.x,to.y,result.y)
	return from

func _free_cell(p:Vector2,known_public:bool) -> Vector2i:
	var middle:=_key(p)
	if grid.region.has_point(middle) and not grid.is_point_solid(middle) and (not known_public or public_cells.has(middle)):return middle
	for r in range(1,17):
		var nearest:=Vector2i(-999,-999)
		var best:=INF
		for x in range(-r,r+1):
			for y in range(-r,r+1):
				if maxi(absi(x),absi(y))!=r:continue
				var test:=middle+Vector2i(x,y)
				if not grid.region.has_point(test) or grid.is_point_solid(test) or (known_public and not public_cells.has(test)):continue
				var dist:=p.distance_squared_to(_at(test))
				if dist<best:
					nearest=test
					best=dist
		if is_finite(best):return nearest
	return Vector2i(-999,-999)

func waypoint(from:Vector3,to:Vector3) -> Vector3:
	if not ready:return to
	var start:=Walk.flat(from)
	var aim:=Walk.flat(to)
	if not boundary.grow(.6).has_point(start) or not boundary.grow(.6).has_point(aim):
		return world.camp_layout.next_waypoint(from,to)
	if _step_clear(start,aim):return to
	if not _body_clear(start,.332) or not disc_clear(start,.309):
		var escape:=_escape(start,aim)
		if escape.distance_to(start)>.045:return Vector3(escape.x,to.y,escape.y)
	var a:=_free_cell(start,false)
	var b:=_free_cell(aim,true)
	if a==Vector2i(-999,-999) or b==Vector2i(-999,-999):return from
	var key:=Vector4i(a.x,a.y,b.x,b.y)
	if paths.has(key):
		var cached:Vector2=paths[key]
		if cached.distance_to(start)<.045 or not _step_clear(start,cached):paths.erase(key)
	if not paths.has(key):
		if paths.size()>768:paths.clear()
		var path:=grid.get_id_path(a,b)
		if path.is_empty():return from
		var next:=start
		for cell:Vector2i in path:
			var p:=_at(cell)
			if p.distance_to(start)<.05:continue
			if not _step_clear(start,p):break
			next=p
		if next.distance_to(start)<.045:next=_escape(start,aim)
		paths[key]=next
	var q:Vector2=paths[key]
	return Vector3(q.x,to.y,q.y)

# A saved position can be under a newly installed line after a layout update.
# Leave clear ground untouched; use the public grid for an obstructed arrival.
func resume_position(at: Vector3, radius: float) -> Vector3:
	var feet := Walk.flat(at)
	# The navigation grid routes couriers around buildings. A player saved
	# on the actual aisle inside the storehouse can safely remain there.
	if world.depot.house.on_walkable_aisle(at,radius) and disc_clear(feet,radius):return at
	if not ready or not boundary.has_point(feet):
		return at
	var cell := _free_cell(feet, true)
	if _body_clear(feet, radius) and disc_clear(feet, radius):
		# Gate thresholds sit outside the public interior grid. A clear approach
		# stays exactly where it was. Inside, also rule out fenced-off pockets.
		if not boundary.grow(-radius-.08).has_point(feet):
			return at
		if public_cells.has(cell) and _step_clear(feet, _at(cell)):
			return at
	if not public_cells.has(cell):
		return world.lifecycle.safe_start()
	var point := _at(cell)
	return Vector3(point.x, at.y, point.y)
