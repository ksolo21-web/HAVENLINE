extends RefCounted
## A crossing has either a shared, mechanically interlocked port at one end
## or two separate decks. The lower item and both sideguards fit below the
## upper deck. Keep the manufacturer's incline short and accessible.
const WIDTH := .493
const HEADROOM := .49
const MIN_Y := .17
const MAX_Y := 2.18
const GRADE := 1.02
const STEP := .135
var index:Dictionary={}
var originals:Dictionary={}
var failures:Dictionary={}
var elevated:Dictionary={}

static func flat(p:Vector3) -> Vector2:return Vector2(p.x,p.z)
static func cell(p:Vector3) -> Vector2i:return Vector2i(floori(p.x/.51),floori(p.z/.51))
static func flow_distance(a:Vector3,b:Vector3) -> float:return flat(a).distance_to(flat(b))

static func resample(path:PackedVector3Array) -> PackedVector3Array:
	var out:=PackedVector3Array([path[0]])
	for i in range(1,path.size()):
		var steps:=maxi(1,ceili(flow_distance(path[i-1],path[i])/STEP))
		for j in range(1,steps+1):
			var p:=path[i-1].lerp(path[i],float(j)/steps)
			if out[-1].distance_squared_to(p)>.000001:out.append(p)
	return out

func _shared(a:String,b:String,p:Vector3,q:Vector3) -> bool:
	var pa:PackedVector3Array=originals[a]
	var pb:PackedVector3Array=originals[b]
	# The real socket plus diverter/merge accepts exactly one carrier
	# in this section. Raw inputs and finished material returns have
	# independent indexed utility mouths and reservation domains.
	for end:int in [0,-1]:
		if pa[end].distance_to(pb[end])>.015:continue
		if flow_distance(p,pa[end])<1.55 and flow_distance(q,pb[end])<1.55:return true
	return false

static func _limits(values:PackedFloat32Array,dist:PackedFloat32Array,low:bool) -> void:
	for step in [1,-1]:
		for k in range(1,values.size()):
			var i:int=k if step==1 else values.size()-1-k
			var prev:int=i-step
			var rise:=absf(dist[i]-dist[prev])*GRADE
			values[i]=maxf(values[i],values[prev]-rise) if low else minf(values[i],values[prev]+rise)

func fit(lane:String,path:PackedVector3Array) -> PackedVector3Array:
	originals[lane]=path
	var pts:=resample(path)
	var n:=pts.size()
	var lo:=PackedFloat32Array()
	var hi:=PackedFloat32Array()
	var dist:=PackedFloat32Array()
	lo.resize(n)
	hi.resize(n)
	dist.resize(n)
	lo.fill(MIN_Y)
	hi.fill(MAX_Y)
	lo[0]=pts[0].y
	hi[0]=pts[0].y
	lo[n-1]=pts[-1].y
	hi[n-1]=pts[-1].y
	for i in range(1,n):dist[i]=dist[i-1]+flow_distance(pts[i-1],pts[i])
	var overlaps:Dictionary={}
	for i in n:
		var pos:=pts[i]
		var key:=cell(pos)
		for x in range(-1,2):
			for z in range(-1,2):
				for record:Array in index.get(key+Vector2i(x,z),[]):
					var other:String=record[0]
					var a:Vector3=record[1]
					var b:Vector3=record[2]
					var ab:=flat(b)-flat(a)
					var t:=clampf((flat(pos)-flat(a)).dot(ab)/maxf(.00001,ab.length_squared()),0.,1.)
					var q:=a.lerp(b,t)
					if flow_distance(q,pos)>WIDTH or _shared(lane,other,pos,q):continue
					if not overlaps.has(other):overlaps[other]={}
					var values:Vector2=overlaps[other].get(i,Vector2(INF,-INF))
					overlaps[other][i]=Vector2(minf(q.y,values.x),maxf(q.y,values.y))
	var groups:Array=[]
	for other:String in overlaps:
		var values:Dictionary=overlaps[other]
		var ids:Array=values.keys()
		ids.sort()
		var start:=0
		for j in range(1,ids.size()+1):
			if j<ids.size() and int(ids[j])-int(ids[j-1])<3:continue
			var contact:Array=[]
			for k in range(start,j):
				var i:int=ids[k]
				var band:Vector2=values[i]
				contact.append(Vector3(i,band.x,band.y))
			groups.append(contact)
			start=j
	groups.sort_custom(func(a,b):return a.size()>b.size())
	_limits(lo,dist,true)
	_limits(hi,dist,false)
	var fit_limits:=_allocate(groups,0,pts,dist,lo,hi)
	if fit_limits.is_empty():
		failures[lane]=str(groups.size())+" crossing groups could not clear the two fixed dock heights"
		return PackedVector3Array()
	lo=fit_limits[0]
	hi=fit_limits[1]
	var out:=PackedVector3Array()
	for i in n:
		if lo[i]>hi[i]+.015:
			failures[lane]=[i,pts[i],lo[i],hi[i]]
			return PackedVector3Array()
		var p:=pts[i]
		p.y=clampf(p.y,lo[i],hi[i])
		if absf(p.y-pts[i].y)>.12:elevated[lane]=true
		if out.size()>=2:
			var a:Vector3=out[-1]-out[-2]
			var b:Vector3=p-out[-1]
			if a.normalized().dot(b.normalized())>.99995:out.remove_at(out.size()-1)
		out.append(p)
	for i in range(1,n):
		var a:Vector3=pts[i-1]
		var b:Vector3=pts[i]
		a.y=clampf(a.y,lo[i-1],hi[i-1])
		b.y=clampf(b.y,lo[i],hi[i])
		var key:=cell((a+b)*.5)
		if not index.has(key):index[key]=[]
		index[key].append([lane,a,b])
	return out

# Choose above/below for each uninterrupted contact as one unit. Earlier
# choices can constrain a neighboring rise; try its other grade before
# rejecting a connection, rather than making the choice per sample.
static func _allocate(groups:Array,k:int,pts:PackedVector3Array,dist:PackedFloat32Array,lo:PackedFloat32Array,hi:PackedFloat32Array) -> Array:
	if k==groups.size():return [lo,hi]
	var contact:Array=groups[k]
	var ways:Array=[]
	for above in [true,false]:
		var bound:=lo.duplicate() if above else hi.duplicate()
		var expense:=0.
		var viable:=true
		for v:Vector3 in contact:
			var i:=int(v.x)
			if above:
				bound[i]=maxf(bound[i],v.z+HEADROOM)
				expense+=maxf(0,bound[i]-pts[i].y)
				if bound[i]>hi[i]+.008:viable=false
			else:
				bound[i]=minf(bound[i],v.y-HEADROOM)
				expense+=maxf(0,pts[i].y-bound[i])
				if bound[i]<lo[i]-.008:viable=false
		if not viable:continue
		_limits(bound,dist,above)
		for i in pts.size():
			if (above and bound[i]>hi[i]+.008) or (not above and bound[i]<lo[i]-.008):
				viable=false
				break
		if viable:ways.append([expense,bound if above else lo,hi if above else bound])
	ways.sort_custom(func(a,b):return a[0]<b[0])
	for option:Array in ways:
		var solution:=_allocate(groups,k+1,pts,dist,option[1],option[2])
		if not solution.is_empty():return solution
	return []
