extends Node3D
## D01–D07 transport, mounted only for purchased lanes. All positions returned
## here mark the top of the rollers, exactly where normalized cargo rests.
const Planner = preload("res://field_conveyor_planner.gd")
const Aisles=preload("res://field_conveyor_aisles.gd")
const Crossings = preload("res://field_conveyor_crossings.gd")
const Geometry = preload("res://field_conveyor_geometry.gd")
const ORDER := ["meal_to_store","stored_meal","meal","meat","wood","planks","stone","blocks"]
const DECK := {"meal_to_store":.85,"stored_meal":.85,"meal":.85,"meat":.31,
	"wood":.41,"stone":.41,"planks":.90,"blocks":.90}
var world
const COLD_DOCK_Z:=.28
const UTILITY_IN_Z:=.06
const UTILITY_OUT_Z:=-.67
var art
var routes:Dictionary={}
var route_signature:String=""
var crossings
var aisles
var lifts:Dictionary={}
var stop_arm:Node3D
var red_lamp:Node3D
var green_lamp:Node3D

func install(host) -> void:
	world=host
	name="ConnectedCampTransport"

func counter_buffer_position(index:int=0) -> Vector3:
	return world.counter.global_position+Vector3(-.64+.36*clampi(index,0,2),.85,1.45)

func storage_port(kind:String,inbound:bool) -> Vector3:
	var local:=Vector3(-1.646,.45,UTILITY_IN_Z if inbound else UTILITY_OUT_Z)
	if kind in ["meal","meal_to_store","stored_meal","cooked_meat","prepared","prepared_meals"]:
		local=Vector3(.55 if inbound else -.50,.98,-1.188)
	elif kind=="meat":
		local=Vector3(1.646,.35,COLD_DOCK_Z)
	return world.depot.house.global_position+local

# These short shelf-side guides are distinct from the outside network.
# The front aisle and original storehouse loading doors stay open.
func local_transfer(lane:String) -> PackedVector3Array:
	var house:Vector3=world.depot.house.global_position
	var cooked:=Vector3(.04,.98,-.92)+house
	var inside:=PackedVector3Array()
	match lane:
		"meal_to_store","stored_meal":
			var mouth:=storage_port("meal",lane=="meal_to_store")
			inside=PackedVector3Array([mouth,Vector3(mouth.x,.98+house.y,cooked.z),cooked])
			if lane=="stored_meal":inside.reverse()
		"planks","blocks":
			var shelf:=house+Vector3(-1.15,.39,.25 if lane=="planks" else -.56)
			var mouth:=storage_port("wood",true)
			var guide:=house+Vector3(-1.40,.45,UTILITY_IN_Z)
			inside=PackedVector3Array([mouth,guide,Vector3(guide.x,guide.y,shelf.z),shelf])
		"wood","stone":
			var shelf:Vector3=world.depot.bins[lane].global_position
			var mouth:=storage_port(lane,false)
			var lift:=house+Vector3(-1.43,.45,UTILITY_OUT_Z)
			inside=PackedVector3Array([shelf,Vector3(lift.x,shelf.y,shelf.z),Vector3(lift.x,shelf.y,lift.z),lift,mouth])
		"meat":
			var shelf:Vector3=world.depot.bins.meat.global_position
			var mouth:=storage_port("meat",false)
			var carrier:=house+Vector3(1.31,.35,-.92)
			inside=PackedVector3Array([shelf,Vector3(carrier.x,shelf.y,carrier.z),carrier,mouth])
	return inside

# Describes the wall socket and its clear service-side stub in outward order.
func _warehouse(kind:String,inbound:bool,deck:float) -> PackedVector3Array:
	var mouth:=storage_port(kind,inbound)
	var dir:=Vector3.LEFT if kind not in ["meat","meal"] else Vector3.FORWARD
	if kind=="meat":dir=Vector3.RIGHT
	var reach:=.46 if dir==Vector3.LEFT else .71
	if kind=="meal" and not inbound:reach=1.31
	var apron:=mouth+dir*reach
	apron.y=deck
	return PackedVector3Array([mouth,apron])

func _machine(kind:String,inbound:bool,deck:float) -> PackedVector3Array:
	var port:Vector3
	var dir:Vector3
	var node:Node3D
	var rect:Rect2
	if kind=="meat":
		node=world.lakeshore.cooker
		# Use get-stored local port coordinates: purchase pop-in is a
		# visual scale tween and must never collapse a permanent line.
		port=node.global_position+(world.lakeshore.cooker_input.position if inbound else world.lakeshore.cooker_output.position)
		dir=Vector3.LEFT if inbound else Vector3.RIGHT
		rect=world.lakeshore.BODY
	else:
		node=world.processors.machines[kind]
		port=node.global_position+(world.processors.INPUT[kind] if inbound else world.processors.OUTPUT[kind])
		dir=(Vector3.RIGHT if kind=="wood" else Vector3.LEFT) if inbound else Vector3.BACK
		rect=world.processors.FOOTPRINT[kind]
	var body:=Rect2(rect.position+Planner.xz(node.global_position),rect.size)
	var apron:=port
	if dir.x<0:apron.x=body.position.x-.34
	if dir.x>0:apron.x=body.end.x+.34
	if dir.z>0:apron.z=body.end.y+.38
	apron.y=deck
	return PackedVector3Array([port,apron])

func _counter() -> PackedVector3Array:
	var end:=counter_buffer_position(0)
	return PackedVector3Array([end,end+Vector3.RIGHT*1.17])

func _terminals(lane:String,deck:float) -> Array[PackedVector3Array]:
	match lane:
		"meal_to_store":return [_machine("meat",false,deck),_warehouse("meal",true,deck)]
		"stored_meal":return [_warehouse("meal",false,deck),_counter()]
		"meal":return [_machine("meat",false,deck),_counter()]
		"planks":return [_machine("wood",false,deck),_warehouse("wood",true,deck)]
		"blocks":return [_machine("stone",false,deck),_warehouse("stone",true,deck)]
	return [_warehouse(lane,false,deck),_machine(lane,true,deck)]

func _boxes() -> Array[Rect2]:
	var result:Array[Rect2]=[]
	var layout=world.camp_layout
	for id:String in layout.NAMES:
		if not layout.owned(id):continue
		result.append(layout.footprint(id,layout.center(id)).grow(Planner.PAD))
		# The whole front loading aisle stays accessible. Machine outfeed
		# and the staff pickup each use their designated side socket.
		if id in ["storage_wood","camp_cooker"]:
			for aisle:Rect2 in layout.service_areas(id,layout.center(id)):
				result.append(aisle.grow(.21))
				if id=="camp_cooker":
					# Reserve the throat from the public square to the cooker's
					# front so an installed return cannot enclose the work face.
					var entry:=Vector2(aisle.get_center().x+.22,aisle.end.y)
					result.append(Rect2(entry-Vector2(.58,.03),Vector2(1.16,2.55)))
	var court:Rect2=layout.bounds()
	var gap:float=world.gates[0].HALF_SPAN+.20
	result.append(Rect2(-gap,court.end.y-2.65,2*gap,2.65).grow(.23))
	result.append(Rect2(court.end.x-2.65,-gap,2.65,2*gap).grow(.23))
	result.append(Rect2(1.25,1.33,.94,.94).grow(.23))
	return result

func _plan(live_lanes:Array,ordering:Array,boxes:Array[Rect2],court:Rect2) -> Array:
	var check=Crossings.new()
	var result:Dictionary={}
	var occupied:Array=[]
	for lane:String in ordering:
		if not lane in live_lanes:continue
		var path:PackedVector3Array=PackedVector3Array()
		var start:=PackedVector3Array()
		var end:=PackedVector3Array()
		for trial in [[0.,1.],[0.,8.],[.27,3.],[-.22,4.],[.54,5.],[0.,0.]]:
			var deck:=clampf(float(DECK[lane])+float(trial[0]),.24,1.48)
			var pair:=_terminals(lane,deck)
			start=pair[0]
			end=pair[1]
			var lane_court:=court
			if lane in ["meal_to_store","stored_meal","meal"]:
				# Finished food moves along the back of the work row.
				# Bound each trunk by its two service-side sockets.
				var edge:=maxf(start[-1].z,end[-1].z)+.05
				lane_court.end=Vector2(court.end.x,minf(court.end.y,edge))
			var leave:=Planner.xz(start[-1]-start[-2]).normalized()
			var arrive:=Planner.xz(end[-1]-end[-2]).normalized()
			var axis:=Planner.route(Planner.xz(start[-1]),Planner.xz(end[-1]),lane_court,boxes,occupied,deck,trial[1],leave,arrive)
			if axis.is_empty():continue
			end.reverse()
			path=check.fit(lane,Planner.shaped(start,axis,end,deck))
			if not path.is_empty():
				check.failures.erase(lane)
				break
		if path.is_empty():continue
		result[lane]=path
		Planner.mark(path,occupied)
	return [result,check]
# Unrelated purchases and repeated presentation refreshes leave the built
# hardware, public navigation grid, and all shared asset batches in place.
func _signature(lanes:Array) -> String:
	var ids:=lanes.duplicate()
	ids.sort()
	var fields:Array=[ids,world.camp_layout.bounds(),world.counter.active]
	for id:String in world.camp_layout.NAMES:
		if world.camp_layout.owned(id):fields.append([id,world.camp_layout.center(id)])
	return str(fields)

func rebuild(live_lanes:Array) -> Dictionary:
	var signature:=_signature(live_lanes)
	if signature==route_signature:return routes
	route_signature=signature
	for child in get_children():
		remove_child(child)
		child.queue_free()
	routes={}
	lifts.clear()
	crossings=null
	aisles=null
	stop_arm=null
	green_lamp=null
	red_lamp=null
	world.depot.house.configure_connections(live_lanes)
	if live_lanes.is_empty():return routes
	art=Geometry.new()
	add_child(art)
	art.setup()
	var boxes:=_boxes()
	var court:Rect2=world.camp_layout.bounds().grow(-.245)
	# Long lines can constrain a compact dock. Give them an earlier
	# turn before declaring a paid connection physically unavailable.
	var priorities:=[["stored_meal","meal_to_store","meal","stone","wood","planks","blocks","meat"],
		["stone","wood","meat","meal_to_store","stored_meal","meal","planks","blocks"],
		["planks","blocks","stone","wood","stored_meal","meal_to_store","meal","meat"],
		ORDER,["blocks","planks","stone","wood","meat","meal","stored_meal","meal_to_store"]]
	var work_area:=Rect2()
	for id:String in ["north_counter","storage_wood","camp_cooker","saw_bench","quarry_drill"]:
		if not world.camp_layout.owned(id):continue
		var rect:Rect2=world.camp_layout.footprint(id,world.camp_layout.center(id))
		work_area=rect if not work_area.has_area() else work_area.merge(rect)
	work_area=work_area.grow(.83).intersection(court)
	for allowed:Rect2 in [work_area,court]:
		for order:Array in priorities:
			var candidate:=_plan(live_lanes,order,boxes,allowed)
			if not crossings or candidate[0].size()>routes.size():
				routes=candidate[0]
				crossings=candidate[1]
			if routes.size()==live_lanes.size():break
		if routes.size()==live_lanes.size():break
	aisles=Aisles.new()
	aisles.install(world,routes)
	art.survey(routes)
	var modeled_ports:Dictionary={}
	for lane:String in routes:
		var path:PackedVector3Array=routes[lane]
		var start:=PackedVector3Array([path[0],path[1]])
		var end:=PackedVector3Array([path[-2],path[-1]])
		art.track(path)
		for terminal in [start,[end[-1],end[-2]]]:
			var mouth:Vector3=terminal[0]
			if modeled_ports.has(mouth):continue
			modeled_ports[mouth]=true
			if mouth.is_equal_approx(counter_buffer_position(0)):continue
			var outward:Vector3=terminal[1]-mouth
			outward.y=0
			if mouth.distance_to(world.depot.house.global_position)<2.2:
				var inbound:bool=mouth.is_equal_approx(storage_port("meal",true)) or mouth.is_equal_approx(storage_port("wood",true))
				if mouth.is_equal_approx(storage_port("meat",false)):
					art.dock(mouth,Vector3.RIGHT,false)
				else:
					var prepared:=mouth.is_equal_approx(storage_port("meal",true)) or mouth.is_equal_approx(storage_port("meal",false))
					# The fitted bezel faces the exterior even when the
					# warehouse shuttle runs toward the interior.
					outward=Vector3.FORWARD if prepared else Vector3.LEFT
					var frame:MeshInstance3D=world.depot.house.connection_frame(prepared,inbound)
					art.add_child(frame)
					frame.transform=Transform3D(Geometry.direction(outward),mouth)
					art.component("Socket",mouth+outward.normalized()*.27,outward)
			else:
				art.socket(mouth,outward)
		var local:=local_transfer(lane)
		for i in range(1,local.size()):
			art.local_guide(local[i-1],local[i])
			var a:=local[i-1]
			var b:=local[i]
			if absf(a.y-b.y)<.17 or Planner.xz(a).distance_to(Planner.xz(b))>.04:continue
			var key:="cold" if lane=="meat" else "utility"
			if lifts.has(key):continue
			var base:=a if a.y<b.y else b
			lifts[key]=[art.movable("LiftTray",base,Vector3.BACK),base,maxf(a.y,b.y)]
	# A typed utility outlet and receiving cassette share only their own
	# controlled entry. Both deliberately expose this motorized junction.
	if "wood" in routes and "stone" in routes:
		var stem:=_warehouse("wood",false,DECK.wood)
		art.component("Diverter",stem[-1],Vector3.LEFT)
	if "planks" in routes and "blocks" in routes:
		var stem:=_warehouse("wood",true,DECK.planks)
		art.component("Diverter",stem[-1],Vector3.RIGHT)
	if "meal" in routes and "meal_to_store" in routes:
		var junction:=_machine("meat",false,.85)
		art.component("Diverter",junction[-1],Vector3.RIGHT)

	if "stored_meal" in routes or "meal" in routes:
		var pickup:=counter_buffer_position(0)
		art.component("Pickup",pickup,Vector3.LEFT)
		var gate:=pickup+Vector3.RIGHT*1.01
		art.component("StopPost",gate,Vector3.LEFT)
		green_lamp=art.movable("ClearLamp",gate,Vector3.LEFT)
		red_lamp=art.movable("HoldLamp",gate,Vector3.LEFT)
		stop_arm=art.movable("GateArm",gate+Vector3.FORWARD*.198+Vector3.UP*.13,Vector3.LEFT)
		set_buffer_full(false)
	art.finish()
	return routes

func set_buffer_full(full:bool) -> void:
	if not is_instance_valid(stop_arm):return
	stop_arm.rotation.z=0. if full else 1.12
	red_lamp.visible=full
	green_lamp.visible=not full


# The plate rises under the actual visible load. The indexed utility cassette
# serves either timber or mineral branches, one reservation at a time.
func present_lifts(goods:Dictionary) -> void:
	for key:String in lifts:
		var item:Array=lifts[key]
		var base:Vector3=item[1]
		var y:=base.y
		for lane:String in (["meat"] if key=="cold" else ["wood","stone"]):
			var model:Node3D=goods.get(lane)
			if model and model.visible:
				var at:=model.global_position
				if Planner.xz(base).distance_to(Planner.xz(at))<.14:y=clampf(at.y,base.y,item[2])
		item[0].position.y=y-base.y

func accessible_service(kind:String) -> Vector3:
	if not aisles:return Vector3.INF
	if kind in ["cooker","cooker_input"]:kind="meat"
	if kind in ["storage","warehouse"]:kind="store"
	return aisles.services.get(kind,Vector3.INF)

func walker_waypoint(from:Vector3,to:Vector3) -> Vector3:
	return aisles.waypoint(from,to) if aisles else world.camp_layout.next_waypoint(from,to)

func pedestrian_clear(from:Vector3,to:Vector3,radius:float=.31) -> bool:
	return not aisles or aisles.line_clear(Planner.xz(from),Planner.xz(to),radius,true)

func constrain_motion(from:Vector3,to:Vector3,radius:float) -> Vector3:
	return aisles.constrain(from,to,radius) if aisles else to
