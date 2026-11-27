extends Node3D
## The chosen transport sheet uses cylindrical charcoal rollers, continuous
## enameled sideguards, bright coupling collars and perforated steel trestles.
## The fitted kit is instanced in batches. A curved guard is a continuous
## sweep through the same turning radius used by every moving load.
const Fittings = preload("res://field_conveyor_fittings.gd")
const KIT = preload("res://assets/conveyors/connected_transport_kit.glb")
const HALF := .210
const PROFILE := [Vector2(-.034,.014),Vector2(-.024,.025),Vector2(.018,.025),
	Vector2(.032,.010),Vector2(.032,-.116),Vector2(.020,-.135),
	Vector2(-.020,-.135),Vector2(-.034,-.119)]
var kit:Dictionary={}
var fitted=Fittings.new()
var instances:Dictionary={}
var used:Dictionary={}
var runs:Dictionary={}
var orange:=SurfaceTool.new()
var under:=SurfaceTool.new()
var guard_mat:=StandardMaterial3D.new()
var frame_mat:=StandardMaterial3D.new()
var sections:=0
var carriage_index:Dictionary={}

func setup() -> void:
	name="D01TransportKit"
	add_child(fitted)
	fitted.install()
	var prototype:Node3D=KIT.instantiate()
	for piece:MeshInstance3D in prototype.find_children("*","MeshInstance3D",true,false):
		kit[String(piece.name)]=piece.mesh
	prototype.free()
	guard_mat.albedo_color=Color("#ee8b23")
	guard_mat.metallic=.16
	guard_mat.roughness=.31
	guard_mat.cull_mode=BaseMaterial3D.CULL_BACK
	frame_mat.albedo_color=Color("#303942")
	frame_mat.metallic=.38
	frame_mat.roughness=.46
	frame_mat.cull_mode=BaseMaterial3D.CULL_DISABLED
	for target in [orange,under]:target.begin(Mesh.PRIMITIVE_TRIANGLES)

static func direction(forward:Vector3) -> Basis:
	var f:=forward
	f.y=0
	f=f.normalized()
	return Basis(Vector3.UP.cross(f),Vector3.UP,f)

func component(id:String,at:Vector3,forward:Vector3,scale_by:=Vector3.ONE) -> void:
	var key: String = id+str(at.snapped(Vector3.ONE*.026))
	if used.has(key):return
	used[key]=true
	if not instances.has(id):instances[id]=[]
	instances[id].append(Transform3D(direction(forward).scaled_local(scale_by),at))

func movable(id:String,at:Vector3,forward:Vector3) -> Node3D:
	# Independent hinge carrier keeps local rotations valid after relocating.
	var mount:=Node3D.new()
	add_child(mount)
	mount.transform=Transform3D(direction(forward),at)
	var part:=MeshInstance3D.new()
	part.mesh=kit[id]
	mount.add_child(part)
	return part

func dock(at:Vector3,outward:Vector3,inbound:bool) -> void:
	component("Dock",at,outward)
	component("InSign" if inbound else "OutSign",at,outward)
	component("Socket",at+outward.normalized()*.27,outward)
func socket(at:Vector3,outward:Vector3) -> void:
	component("Socket",at+outward.normalized()*.09,outward)

static func _tri(st:SurfaceTool,a:Vector3,b:Vector3,c:Vector3,n:Vector3) -> void:
	var order:=[a,c,b] if (b-a).cross(c-a).dot(n)>0 else [a,b,c]
	for p in order:
		st.set_normal(n)
		st.add_vertex(p)
static func _quad(st:SurfaceTool,a:Vector3,b:Vector3,c:Vector3,d:Vector3,n:Vector3) -> void:
	_tri(st,a,b,c,n)
	_tri(st,a,c,d,n)

func _section(a:Vector3,b:Vector3,ra:Vector3,rb:Vector3) -> void:
	if a.distance_squared_to(b)<.000001:return
	sections+=1
	for side:float in [-1.,1.]:
		for k in PROFILE.size():
			var q:Vector2=PROFILE[k]
			var w:Vector2=PROFILE[(k+1)%PROFILE.size()]
			var p1:=a+ra*(HALF+q.x)*side+Vector3.UP*q.y
			var p2:=a+ra*(HALF+w.x)*side+Vector3.UP*w.y
			var p3:=b+rb*(HALF+w.x)*side+Vector3.UP*w.y
			var p4:=b+rb*(HALF+q.x)*side+Vector3.UP*q.y
			var n:=((ra+rb).normalized()*(q.y-w.y)*side+Vector3.UP*(w.x-q.x)).normalized()
			_quad(orange,p1,p2,p3,p4,n)
	var top_a:=a-Vector3.UP*.070
	var top_b:=b-Vector3.UP*.070
	_quad(under,top_a-ra*.197,top_b-rb*.197,top_b+rb*.197,top_a+ra*.197,Vector3.UP)
	_quad(under,top_a-ra*.182-Vector3.UP*.025,top_a+ra*.182-Vector3.UP*.025,top_b+rb*.182-Vector3.UP*.025,top_b-rb*.182-Vector3.UP*.025,Vector3.DOWN)

# Merge coincident straight corridors at a shared output or pickup, so two
# typed routes cannot build two sets of flickering rollers on a common belt.
func _straight(a:Vector3,b:Vector3,axis:int) -> void:
	var along_a:float=a.x if axis==0 else a.z
	var along_b:float=b.x if axis==0 else b.z
	var offset:float=a.z if axis==0 else a.x
	var key:=Vector3i(axis,roundi(offset*1000),roundi(a.y*1000))
	if not runs.has(key):runs[key]=[]
	runs[key].append(Vector3(minf(along_a,along_b),maxf(along_a,along_b),signf(along_b-along_a)))

func survey(paths:Dictionary) -> void:
	# Do not put the feet of an overpass through the moving freight on
	# the lower belt. Count both endpoints on each short probe segment.
	for path:PackedVector3Array in paths.values():
		for i in range(1,path.size()):
			var a:=path[i-1]
			var b:=path[i]
			if a.y<0. or b.y<0.:continue
			var length:=a.distance_to(b)
			var steps:=maxi(1,ceili(length/.16))
			for j in steps:
				var p:=a.lerp(b,(j+.5)/steps)
				var key:=Vector2i(floori(p.x/.65),floori(p.z/.65))
				if not carriage_index.has(key):carriage_index[key]=[]
				carriage_index[key].append([p,direction(b-a).z])

func _pier_width(at:Vector3,tangent:Vector3) -> float:
	var key:=Vector2i(floori(at.x/.65),floori(at.z/.65))
	var wide:=1.
	for x in range(-1,2):
		for z in range(-1,2):
			for record:Array in carriage_index.get(key+Vector2i(x,z),[]):
				var p:Vector3=record[0]
				if p.y>at.y-.30:continue
				var delta:=p-at
				delta.y=0
				if delta.length()>.45:continue
				if absf(tangent.dot(record[1]))>.93 and delta.length()<.16:
					wide=2.12
				else:return 0.
	return wide

func _hardware(a:Vector3,b:Vector3,long_run:bool) -> void:
	var delta:=b-a
	var length:=delta.length()
	if length<.001:return
	var tangent:=delta.normalized()
	var inclined:=absf(tangent.y)>.13
	var pitch:=.09 if inclined else .094
	var pieces:=maxi(1,roundi(length/pitch))
	for j in pieces:
		component("InclineTread" if inclined else "Roller",a.lerp(b,(j+.5)/pieces),tangent)
	if not long_run:return
	var modules:=maxi(1,ceili(length/1.49))
	for i in modules:
		var p:=a.lerp(b,(i+.50)/modules)
		var leg_scale:=maxf(.14,p.y-.095)/.267
		for shift:float in [0.,-.26,.26]:
			var place:=p+tangent*shift*minf(1.,length)
			var wide:=_pier_width(place,tangent)
			if wide>0.:
				component("Trestle",Vector3(place.x,.006,place.z),tangent,Vector3(wide,leg_scale,1))
				break
		component("Coupler",p,tangent)
		if length>.84:
			component("Arrows",a.lerp(b,(i+.69)/modules),tangent)
		if (i==0 or i%3==2) and length>.91:
			component("VentedDrive",a.lerp(b,(i+.28)/modules)+direction(tangent).x*.122-Vector3.UP*.055,tangent,Vector3(1.11,1.2,1.1))

func local_guide(a:Vector3,b:Vector3) -> void:
	var motion:=b-a
	if absf(motion.y)>.04 and Vector2(motion.x,motion.z).length()<.08:
		component("LiftFrame",Vector3(a.x,minf(a.y,b.y),a.z)-Vector3.BACK*.15,Vector3.BACK,Vector3(1,absf(motion.y)/.35,1))
		return
	if Vector2(motion.x,motion.z).length()<.03:return
	var side:=direction(motion).x*.57
	_section(a,b,side,side)
	var count:=maxi(1,roundi(motion.length()/.10))
	for i in count:
		component("Roller",a.lerp(b,(i+.5)/count),motion,Vector3(.58,.70,1.))

func track(path:PackedVector3Array) -> void:
	var skip_to:=-1
	for i in range(1,path.size()):
		if i<=skip_to:continue
		var corner_end:int=fitted.place_corner(path,i-1,_pier_width) if path[i-1].y>=0 and path[i].y>=0 else i-1
		if corner_end>=i:
			skip_to=corner_end
			continue
		var a:=path[i-1]
		var b:=path[i]
		var delta:=b-a
		if delta.length_squared()<.00001:continue
		if Vector2(delta.x,delta.z).length()<.003:continue
		if a.y<-.12 and b.y<-.12:
			var underground:=direction(delta).x
			_section(a,b,underground,underground)
			_hardware(a,b,false)
			continue
		var side:=direction(delta).x
		var prev:=side
		var next:=side
		if i>1:
			var other:=direction(a-path[i-2]).x
			if side.dot(other)>.88:prev=(side+other).normalized()
		if i+1<path.size():
			var other:=direction(path[i+1]-b).x
			if side.dot(other)>.88:next=(side+other).normalized()
		if absf(delta.y)<.0001 and (absf(delta.x)<.0001 or absf(delta.z)<.0001):
			_straight(a,b,0 if absf(delta.z)<.0001 else 1)
		else:
			var key: String="Bend"+str(a.snapped(Vector3.ONE*.003))+str(b.snapped(Vector3.ONE*.003))
			if used.has(key):continue
			used[key]=true
			if fitted.place_span(a,b,_pier_width):continue
			_section(a,b,prev,next)
			_hardware(a,b,delta.length()>.40)

func _emit_run(key:Vector3i,lo:float,hi:float,forward:float) -> void:
	var z_or_x:=key.y/1000.
	var y:=key.z/1000.
	var a:=Vector3(lo,y,z_or_x) if key.x==0 else Vector3(z_or_x,y,lo)
	var b:=Vector3(hi,y,z_or_x) if key.x==0 else Vector3(z_or_x,y,hi)
	if forward<0:
		var swap:=a
		a=b
		b=swap
	if fitted.place_span(a,b,_pier_width):return
	var side:=direction(b-a).x
	_section(a,b,side,side)
	_hardware(a,b,hi-lo>.28)

func finish() -> void:
	for key:Vector3i in runs:
		var spans:Array=runs[key]
		spans.sort_custom(func(a,b):return a.x<b.x)
		var lo:float=spans[0].x
		var hi:float=spans[0].y
		var forward:float=spans[0].z
		for i in range(1,spans.size()):
			var next:Vector3=spans[i]
			if next.x<=hi+.006:
				hi=maxf(hi,next.y)
			else:
				_emit_run(key,lo,hi,forward)
				lo=next.x
				hi=next.y
				forward=next.z
		_emit_run(key,lo,hi,forward)
	for span:Array in fitted.suspended:
		var a:Vector3=span[0]
		var b:Vector3=span[1]
		var tangent:Vector3=span[2]
		for t:float in [.10,.90]:
			var at:=a.lerp(b,t)
			var wide:=_pier_width(at,tangent)
			if wide==0.:continue
			component("Trestle",Vector3(at.x,.006,at.z),tangent,Vector3(wide,maxf(.17,at.y-.13)/.267,1))
	fitted.finish()
	if sections:
		for pair in [[orange,guard_mat,"AmberSideguards"],[under,frame_mat,"RollerCradles"]]:
			var skin:=MeshInstance3D.new()
			skin.name=pair[2]
			skin.mesh=pair[0].commit()
			skin.material_override=pair[1]
			add_child(skin)
	for id:String in instances:
		var xforms:Array=instances[id]
		var batch:=MultiMesh.new()
		batch.transform_format=MultiMesh.TRANSFORM_3D
		batch.mesh=kit[id]
		batch.instance_count=xforms.size()
		for i in xforms.size():batch.set_instance_transform(i,xforms[i])
		var draw:=MultiMeshInstance3D.new()
		draw.name=id+"Modules"
		draw.multimesh=batch
		add_child(draw)
