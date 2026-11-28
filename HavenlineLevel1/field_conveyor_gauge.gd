extends RefCounted
## Fit the full-width D01 rollers only where the floor and neighboring lines
## allow it. Existing appliance throats and shared utility sockets stay narrow.
const SOCKET := .484
const WIDTH_STEP := .10
const FREIGHT := .984
const FOOD := 1.184
var boxes:Array[Rect2]=[]
var ends:Array[Vector3]=[]
var turns:Array[Vector4]=[]
var edges:Dictionary={}
var cache:Dictionary={}
var court:Rect2

func setup(world,routes:Dictionary,buffer:Vector3) -> void:
	court=world.camp_layout.bounds()
	boxes.assign(world.camp_layout.obstacles())
	# A courier must fit between an outside return line and the timber.
	# Respect the wall thickness plus one walking lane on the service side.
	var service_strip:=Rect2(court.position,Vector2(1.16,court.size.y))
	boxes.append(service_strip)
	for id:String in ["storage_wood","camp_cooker","saw_bench","quarry_drill"]:
		if world.camp_layout.owned(id):
			boxes.append_array(world.camp_layout.service_areas(id,world.camp_layout.center(id)))
	for lane:String in routes:
		var path:PackedVector3Array=routes[lane]
		for mouth:Vector3 in [path[0],path[-1]]:
			if not mouth.is_equal_approx(buffer) and not mouth in ends:ends.append(mouth)
		for i in range(1,path.size()):
			var a:=path[i-1]
			var b:=path[i]
			var edge:=[lane,a,b]
			var low:=_cell(a.min(b)-Vector3.ONE*FOOD)
			var high:=_cell(a.max(b)+Vector3.ONE*FOOD)
			for x in range(low.x,high.x+1):
				for z in range(low.y,high.y+1):
					var k:=Vector2i(x,z)
					if not edges.has(k):edges[k]=[]
					edges[k].append(edge)
			if i+1>=path.size():continue
			var d:=Vector2(b.x-a.x,b.z-a.z)
			var e:=Vector2(path[i+1].x-b.x,path[i+1].z-b.z)
			if d.length()>.15 or e.length()>.15:continue
			var angle:=absf(d.angle_to(e))
			if angle<.10 or angle>.60:continue
			var radius:=(d.length()+e.length())/(4.*sin(angle*.5))
			turns.append(Vector4(b.x,b.y,b.z,maxf(SOCKET,2.*radius-.045)))

static func width_step(width:float) -> int:
	return clampi(floori((width-SOCKET+.001)/WIDTH_STEP),0,7)

func fitted_width(p:Vector3) -> float:
	return SOCKET+width_step(at(p))*WIDTH_STEP

static func _cell(p:Vector3) -> Vector2i:return Vector2i(floori(p.x),floori(p.z))

func at(p:Vector3) -> float:
	var key:=Vector3i((p*200.).round())
	if cache.has(key):return cache[key]
	var pt:=Vector2(p.x,p.z)
	var room:=minf(minf(pt.x-court.position.x,court.end.x-pt.x),minf(pt.y-court.position.y,court.end.y-pt.y))*2.-.025
	for rect:Rect2 in boxes:
		room=minf(room,2.*pt.distance_to(pt.clamp(rect.position,rect.end))-.025)
	for end in ends:room=minf(room,SOCKET+p.distance_to(end)*.72)
	var nearby:Dictionary={}
	for edge:Array in edges.get(_cell(p),[]):
		var a:Vector3=edge[1]
		var b:Vector3=edge[2]
		var ba:=Vector2(b.x-a.x,b.z-a.z)
		var t:=clampf((pt-Vector2(a.x,a.z)).dot(ba)/maxf(.000001,ba.length_squared()),0.,1.)
		var q:=a.lerp(b,t)
		if absf(q.y-p.y)>.46:continue
		var d:=pt.distance_to(Vector2(q.x,q.z))
		nearby[edge[0]]=minf(d,nearby.get(edge[0],INF))
	var target:=FREIGHT
	for lane:String in nearby:
		var d:float=nearby[lane]
		if d<.025:
			if lane in ["meal","stored_meal","meal_to_store","meat"]:target=FOOD
		else:room=minf(room,d-.018)
	for turn in turns:
		var distance:=p.distance_to(Vector3(turn.x,turn.y,turn.z))
		room=minf(room,turn.w+.8*distance)
	var width:=clampf(room,SOCKET,target)
	cache[key]=width
	return width
