extends RefCounted
## Connect the real ports through a rectilinear floor plan. Full contour corners
## stay available when a movable machine blocks either simple elbow.
static func segment_clear(a:Vector2,b:Vector2,boxes:Array[Rect2]) -> bool:
	var bounds:=Rect2(a,Vector2.ZERO).expand(b).grow(.001)
	for box:Rect2 in boxes:
		if bounds.intersects(box):return false
	return true

static func connect_ports(ports:PackedVector3Array,boxes:Array[Rect2],court:Rect2) -> PackedVector3Array:
	var a:=Vector2(ports[1].x,ports[1].z)
	var b:=Vector2(ports[2].x,ports[2].z)
	var xs:Array[float]=[a.x,b.x]
	var zs:Array[float]=[a.y,b.y]
	var blocked:Array[Rect2]=[]
	for raw:Rect2 in boxes:
		var box:=raw.grow(.12)
		# Aprons are themselves the openings to source and destination.
		if box.has_point(a) or box.has_point(b):continue
		blocked.append(box)
		for x:float in [box.position.x-.018,box.end.x+.018]:
			if not x in xs:xs.append(x)
		for z:float in [box.position.y-.018,box.end.y+.018]:
			if not z in zs:zs.append(z)
	xs.sort()
	zs.sort()
	var first:=Vector2i(xs.find(a.x),zs.find(a.y))
	var last:=Vector2i(xs.find(b.x),zs.find(b.y))
	var cost:Dictionary={first:0.}
	var parent:Dictionary={}
	var open:Array[Vector2i]=[first]
	while not open.is_empty():
		var best:=0
		for i in range(1,open.size()):
			if cost[open[i]]<cost[open[best]]:best=i
		var at:Vector2i=open.pop_at(best)
		if at==last:break
		var p:=Vector2(xs[at.x],zs[at.y])
		for step:Vector2i in [Vector2i.RIGHT,Vector2i.UP,Vector2i.LEFT,Vector2i.DOWN]:
			var n:=at+step
			if n.x<0 or n.y<0 or n.x>=xs.size() or n.y>=zs.size():continue
			var q:=Vector2(xs[n.x],zs[n.y])
			if not court.has_point(q) or not segment_clear(p,q,blocked):continue
			var trial:float=cost[at]+p.distance_to(q)
			if trial>=float(cost.get(n,INF))-.0001:continue
			cost[n]=trial
			parent[n]=at
			if not n in open:open.append(n)
	if not cost.has(last):return PackedVector3Array()
	var reverse:Array[Vector2]=[]
	var cur:=last
	while true:
		reverse.append(Vector2(xs[cur.x],zs[cur.y]))
		if cur==first:break
		cur=parent[cur]
	reverse.reverse()
	var path:=PackedVector3Array([ports[0]])
	var reduced:Array[Vector2]=[]
	for point:Vector2 in reverse:
		if reduced.size()>1 and absf((reduced[-1]-reduced[-2]).cross(point-reduced[-1]))<.00001:reduced.pop_back()
		reduced.append(point)
	for point:Vector2 in reduced:
		var at:=Vector3(point.x,.42,point.y)
		if path[-1].distance_to(at)>.002:path.append(at)
	path.append(ports[3])
	return path
