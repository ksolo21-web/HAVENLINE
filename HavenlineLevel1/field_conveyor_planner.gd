extends RefCounted
## Orthogonal visibility graph around expanded physical footprints. Cargo runs
## on the filleted polyline handed to the mesh builder, including its inclines.
const PAD := .28
const BEND := .34

static func xz(p: Vector3) -> Vector2:
	return Vector2(p.x,p.z)

static func clear(a:Vector2,b:Vector2,boxes:Array[Rect2]) -> bool:
	var rect := Rect2(a,Vector2.ZERO).expand(b).grow(.0005)
	for box in boxes:
		if rect.intersects(box):return false
	return true

static func against_belts(a:Vector2,b:Vector2,segments:Array,deck:float) -> float:
	var h := absf(a.y-b.y)<.001
	var lo := minf(a.x,b.x) if h else minf(a.y,b.y)
	var hi := maxf(a.x,b.x) if h else maxf(a.y,b.y)
	var offset := a.y if h else a.x
	var penalty:=0.
	for seg:PackedFloat32Array in segments:
		if absf(seg[4]-deck)>.56: continue
		if bool(seg[0])==h:
			var overlap:=minf(hi,seg[3])-maxf(lo,seg[2])
			if overlap>.003 and absf(offset-seg[1])<.49:
				penalty+=overlap*4.
		elif seg[1]>=lo-.09 and seg[1]<=hi+.09 and offset>=seg[2]-.09 and offset<=seg[3]+.09:
			penalty+=.92
	return penalty

static func route(a:Vector2,b:Vector2,court:Rect2,boxes:Array[Rect2],segments:Array,deck:float,avoid:float=1.,leave:Vector2=Vector2.ZERO,arrive:Vector2=Vector2.ZERO) -> PackedVector2Array:
	var xs:Array[float]=[a.x,b.x,court.position.x+.01,court.end.x-.01]
	var ys:Array[float]=[a.y,b.y,court.position.y+.01,court.end.y-.01]
	for box:Rect2 in boxes:
		for border:float in [box.position.x-.016,box.end.x+.016]:
			if border>=court.position.x and border<=court.end.x and not border in xs:xs.append(border)
		for border:float in [box.position.y-.016,box.end.y+.016]:
			if border>=court.position.y and border<=court.end.y and not border in ys:ys.append(border)
	for seg:PackedFloat32Array in segments:
		if absf(seg[4]-deck)>.56:continue
		for offset:float in [-.52,.52]:
			var v:=float(seg[1])+offset
			if bool(seg[0]) and v>court.position.y and v<court.end.y and not v in ys:ys.append(v)
			if not bool(seg[0]) and v>court.position.x and v<court.end.x and not v in xs:xs.append(v)
	xs.sort()
	ys.sort()
	var graph:=AStar2D.new()
	var width:=xs.size()
	for j in ys.size():
		for i in xs.size():
			var p:=Vector2(xs[i],ys[j])
			if not court.has_point(p):continue
			if not clear(p,p,boxes):continue
			var cell:=j*width+i
			graph.add_point(cell,p)
			for prev:int in [cell-1,cell-width]:
				if (prev==cell-1 and i==0) or not graph.has_point(prev):continue
				var q:=graph.get_point_position(prev)
				if clear(q,p,boxes):graph.connect_points(cell,prev)
	var first:=ys.find(a.y)*width+xs.find(a.x)
	var last:=ys.find(b.y)*width+xs.find(b.x)
	if not graph.has_point(first) or not graph.has_point(last):return PackedVector2Array()
	# Direction forms part of the search state, so a small detour can win
	# a straighter line and avoid overlapping a previously built section.
	var first_key:=3*first+2
	var costs:Dictionary={first_key:0.}
	var parents:Dictionary={}
	var frontier:Array=[[a.distance_to(b),first_key]]
	var finish:=-1
	while not frontier.is_empty():
		var entry:Array=frontier.pop_back()
		var key:int=entry[1]
		var current:=floori(key/3.)
		var p:=graph.get_point_position(current)
		if float(entry[0])>float(costs[key])+p.distance_to(b)+.0001:continue
		if current==last:
			finish=key
			break
		for next:int in graph.get_point_connections(current):
			var q:=graph.get_point_position(next)
			# A dock releases onto its belt, and receives from the belt.
			# An immediate reversal would build two decks across the same lip.
			var step:=q-p
			if current==first and step.dot(leave)<-.00001:continue
			if next==last and step.dot(arrive)>.00001:continue
			var dir:=0 if absf(p.y-q.y)<.001 else 1
			var next_key:=next*3+dir
			var distance:float=costs[key]+p.distance_to(q)+avoid*against_belts(p,q,segments,deck)
			if key%3!=2 and key%3!=dir:distance+=BEND
			if distance>=float(costs.get(next_key,INF))-.0001:continue
			costs[next_key]=distance
			parents[next_key]=key
			var trial:=[distance+q.distance_to(b),next_key]
			frontier.insert(frontier.bsearch_custom(trial,func(x,y):return x[0]>y[0]),trial)
	if finish<0:return PackedVector2Array()
	var path:=PackedVector2Array()
	while finish!=first_key:
		path.append(graph.get_point_position(floori(finish/3.)))
		finish=parents[finish]
	path.append(a)
	path.reverse()
	return path

static func mark(path:PackedVector3Array,segments:Array) -> void:
	for i in range(1,path.size()):
		var a:=path[i-1]
		var b:=path[i]
		var h:=absf(a.z-b.z)<.0002
		if not h and absf(a.x-b.x)>.0002:continue
		if xz(a).distance_to(xz(b))<.35:continue
		segments.append(PackedFloat32Array([1. if h else 0.,a.z if h else a.x,minf(a.x,b.x) if h else minf(a.z,b.z),maxf(a.x,b.x) if h else maxf(a.z,b.z),(a.y+b.y)*.5]))

static func shaped(source:PackedVector3Array, axis:PackedVector2Array, dest:PackedVector3Array, deck:float) -> PackedVector3Array:
	var points:=PackedVector3Array()
	var all:=source.duplicate()
	for p in axis:all.append(Vector3(p.x,deck,p.y))
	for p in dest:all.append(p)
	for p in all:
		if not points.is_empty() and points[-1].distance_to(p)<.012:continue
		if points.size()>=2:
			var a:Vector3=points[-1]-points[-2]
			var b:Vector3=p-points[-1]
			if a.normalized().dot(b.normalized())>.9999:points.remove_at(points.size()-1)
		points.append(p)
	if points.size()<3:return points
	var result:=PackedVector3Array([points[0]])
	for i in range(1,points.size()-1):
		var before:=points[i-1]
		var corner:=points[i]
		var after:=points[i+1]
		var incoming:=xz(corner)-xz(before)
		var outgoing:=xz(after)-xz(corner)
		var v:=incoming.normalized()
		var w:=outgoing.normalized()
		if absf(v.dot(w))>.04 or incoming.length()<.06 or outgoing.length()<.06:
			result.append(corner)
			continue
		var r:=minf(.32,minf(incoming.length(),outgoing.length())*.46)
		var entry:=corner.lerp(before,r/incoming.length())
		var exit:=corner.lerp(after,r/outgoing.length())
		var center:=xz(corner)-v*r+w*r
		for j in 9:
			var t:=j/8.
			var d:=center+(-w*cos(t*PI*.5)+v*sin(t*PI*.5))*r
			result.append(Vector3(d.x,lerpf(entry.y,exit.y,t),d.y))
	result.append(points[-1])
	return result
