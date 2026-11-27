extends RefCounted
## A short flush inspection crossing keeps the upgraded floor open to a
## worker carrying a tall pack. Powered end lifts lower a carrier onto the
## same typed conveyor below the floor, then return it to daylight.
const Walk = preload("res://field_conveyor_crossings.gd")
const CLEAR := .72
const DROP := 2.68
var rail_index:Dictionary={}
var warehouse:=Vector3.ZERO
var walks:Array[PackedVector2Array]=[]
var hatches:Array=[]
var disconnected:Dictionary={}
var under:Array=[]

func _bucket(p:Vector2) -> Vector2i:return Vector2i(floori(p.x/.64),floori(p.y/.64))

func configure(world,routes:Dictionary) -> void:
	warehouse=world.depot.house.global_position
	for lane:String in routes:
		var route:PackedVector3Array=routes[lane]
		for i in range(1,route.size()):
			var a:=Walk.flat(route[i-1])
			var b:=Walk.flat(route[i])
			var low:=_bucket(a.min(b)-Vector2.ONE*.54)
			var high:=_bucket(a.max(b)+Vector2.ONE*.54)
			var record:=[lane,a,b]
			for x in range(low.x,high.x+1):
				for z in range(low.y,high.y+1):
					var key:=Vector2i(x,z)
					if not rail_index.has(key):rail_index[key]=[]
					rail_index[key].append(record)
	if not world.inventory.is_machine_owned("wood"):return
	var cooker:=Walk.flat(world.lakeshore.cooker.global_position)
	var south:=cooker+Vector2(.10,3.96)
	var neck:=cooker+Vector2(.10,1.36)
	var bend:=cooker+Vector2(-.28,1.01)
	var saw_access:=Walk.flat(world.processors.apron_position("wood"))
	walks.append(PackedVector2Array([south,neck,bend]))
	# Reach the same native interaction floor after a building move.
	var from:=Vector3(bend.x,0,bend.y)
	var to:=Vector3(saw_access.x,0,saw_access.y)
	for i in 12:
		var next:Vector3=world.camp_layout.next_waypoint(from,to,.31)
		if Walk.flow_distance(from,next)<.015:break
		walks.append(PackedVector2Array([Walk.flat(from),Walk.flat(next)]))
		from=next
		if Walk.flow_distance(next,to)<.02:break

func _inside(p:Vector3) -> bool:
	var q:=Walk.flat(p)
	for line in walks:
		for i in range(1,line.size()):
			var closest:=Geometry2D.get_closest_point_to_segment(q,line[i-1],line[i])
			if closest.distance_squared_to(q)<CLEAR*CLEAR:return true
	return false

static func _append(out:PackedVector3Array,p:Vector3) -> void:
	if not out.is_empty() and out[-1].distance_squared_to(p)<.000001:return
	if out.size()>=2:
		var a:Vector3=out[-1]-out[-2]
		var b:Vector3=p-out[-1]
		if a.normalized().dot(b.normalized())>.99999:out.remove_at(out.size()-1)
	out.append(p)

func _safe_shaft(lane:String,p:Vector3) -> bool:
	var at:=Walk.flat(p)
	for seg:Array in rail_index.get(_bucket(at),[]):
		if seg[0]==lane:continue
		var nearest:Vector2=Geometry2D.get_closest_point_to_segment(at,seg[1],seg[2])
		if at.distance_squared_to(nearest)<.490*.490:return false
	return true

func _private_hatch(lane:String,p:Vector3) -> Vector3:
	if _safe_shaft(lane,p):return p
	var local:=p-warehouse
	var inward:=Vector3.ZERO
	if absf(local.z+1.188)<.08 and absf(local.x)<1.49:inward=Vector3.BACK
	elif absf(local.x+1.646)<.08 and absf(local.z)<1.02:inward=Vector3.RIGHT
	elif absf(local.x-1.646)<.08 and absf(local.z)<1.02:inward=Vector3.LEFT
	if inward==Vector3.ZERO:return Vector3.INF
	for r:float in [.28,.38,.48,.58,.68]:
		var candidate:=p+inward*r
		if _safe_shaft(lane,candidate):return candidate
	return Vector3.INF

func recess(lane:String,original:PackedVector3Array) -> PackedVector3Array:
	if walks.is_empty():return original
	var sample:=Walk.resample(original)
	if _inside(sample[0]) or _inside(sample[-1]):
		disconnected[lane]=["endpoint",sample[0],sample[-1]]
		return original
	var spans:Array[Vector2i]=[]
	var i:=1
	while i<sample.size()-1:
		if not _inside(sample[i]):
			i+=1
			continue
		var enter:=i-1
		while i<sample.size()-1 and _inside(sample[i]):i+=1
		var leave:=i
		# A vertical cassette needs a private shaft on BOTH decks. Place it
		# just outside the walkway where another route cannot cross its travel.
		while enter>0 and not _safe_shaft(lane,sample[enter]):enter-=1
		while leave<sample.size()-1 and not _safe_shaft(lane,sample[leave]):leave+=1
		if not _private_hatch(lane,sample[enter]).is_finite() or not _private_hatch(lane,sample[leave]).is_finite():
			disconnected[lane]=[enter,leave,sample.size(),sample[enter],sample[leave],_safe_shaft(lane,sample[enter]),_safe_shaft(lane,sample[leave])]
			return original
		if not spans.is_empty() and enter<=spans[-1].y+3:
			spans[-1]=Vector2i(spans[-1].x,maxi(leave,spans[-1].y))
		else:spans.append(Vector2i(enter,leave))
		i=maxi(leave,i+1)
	if spans.is_empty():return original
	var result:=PackedVector3Array()
	var last:=0
	for span in spans:
		for j in range(last,span.x+1):_append(result,sample[j])
		var lower:=PackedVector3Array()
		var first_hatch:=_private_hatch(lane,sample[span.x])
		var last_hatch:=_private_hatch(lane,sample[span.y])
		_append(result,first_hatch)
		_append(result,first_hatch-Vector3.UP*DROP)
		for j in range(span.x,span.y+1):
			_append(result,sample[j]-Vector3.UP*DROP)
			_append(lower,sample[j])
		under.append(lower)
		for edge:int in [span.x,span.y]:
			var dir:=sample[mini(edge+1,sample.size()-1)]-sample[maxi(0,edge-1)]
			dir.y=0.
			var top:=last_hatch if edge==span.y else first_hatch
			hatches.append([lane,top,dir.normalized()*(1. if edge==span.y else -1.),top.y-DROP])
		_append(result,last_hatch-Vector3.UP*DROP)
		_append(result,last_hatch)
		_append(result,sample[span.y])
		last=span.y+1
	for j in range(last,sample.size()):_append(result,sample[j])
	return result

func draw_walkway(art) -> void:
	if under.is_empty():return
	for strip in walks:
		for i in range(1,strip.size()):
			var a:=strip[i-1]
			var b:=strip[i]
			var length:=a.distance_to(b)
			if length<.04:continue
			var count:=maxi(1,roundi(length/.43))
			for j in count:
				var p:=a.lerp(b,(j+.5)/count)
				var covered:=false
				for route:PackedVector3Array in under:
					for k in range(1,route.size()):
						var left:=Walk.flat(route[k-1])
						var right:=Walk.flat(route[k])
						if left.distance_squared_to(right)<.00001:continue
						var closest:=Geometry2D.get_closest_point_to_segment(p,left,right)
						if p.distance_squared_to(closest)<.66*.66:
							covered=true
							break
					if covered:break
				if covered:
					art.component("ServiceGrate",Vector3(p.x,.003,p.y),Vector3(b.x-a.x,0,b.y-a.y),Vector3(1.90,1.,length/(.42*count)))
