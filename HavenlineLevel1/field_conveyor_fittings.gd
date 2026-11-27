extends Node3D
## Actual D01 image-to-3D furnished modules, with unchanged texture UVs.
## Each type shares a MultiMesh per original textured surface. INSTANCE_CUSTOM
## supplies measured deck and port dimensions instead of stretching the feet.
const BASE := "res://assets/conveyors/Meshy/"
const SHADER := preload("res://assets/conveyors/fitted_transport.gdshader")
const WIDTH := .484
var specs:Dictionary={}
var meshes:Dictionary={}
var transforms:Dictionary={}
var values:Dictionary={}
var counts:Dictionary={}
var suspended:Array=[]
var used:Dictionary={}
static var library:Dictionary={}

func install() -> void:
	name="MeshyConveyorModules"
	var file:=BASE+"modules.json"
	if not FileAccess.file_exists(file):return
	if library.is_empty():
		var contents=JSON.parse_string(FileAccess.get_file_as_string(file))
		if not contents is Dictionary:return
		for family:String in ["straight","corner","incline"]:
			if not contents.has(family):continue
			var entry:Dictionary=contents[family]
			var path:String=entry.file
			if not path.begins_with("res://"):path=BASE+path
			if not ResourceLoader.exists(path):continue
			var instance:Node3D=(load(path) as PackedScene).instantiate()
			var metal:=ArrayMesh.new()
			_bake(instance,Transform3D.IDENTITY,metal,entry,family)
			instance.free()
			if metal.get_surface_count():
				library[family]=[entry,metal]
				if family=="corner":library["left_corner"]=[entry,_left_handed(metal)]
	for family:String in library:
		specs[family]=library[family][0]
		meshes[family]=library[family][1]
		transforms[family]=[]
		values[family]=[]
		counts[family]=0

static func _bake(node:Node,outer:Transform3D,combined:ArrayMesh,entry:Dictionary,family:String) -> void:
	var pose:=outer
	if node is Node3D:pose*=node.transform
	if node is MeshInstance3D and node.mesh:
		var geometry:Mesh=node.mesh
		for i in geometry.get_surface_count():
			var tool:=SurfaceTool.new()
			tool.begin(Mesh.PRIMITIVE_TRIANGLES)
			tool.append_from(geometry,i,pose)
			var surface:=tool.commit()
			var mat:=ShaderMaterial.new()
			mat.shader=SHADER
			var original:Material=node.get_active_material(i)
			if original is StandardMaterial3D:
				mat.set_shader_parameter("pigment_map",original.albedo_texture)
				mat.set_shader_parameter("tint",original.albedo_color)
				mat.set_shader_parameter("metalness",original.metallic)
				mat.set_shader_parameter("roughness",original.roughness)
			mat.set_shader_parameter("foot_piece",String(node.name).to_lower().begins_with("foot"))
			if entry.has("deck_profile"):
				mat.set_shader_parameter("transition",Vector2(entry.deck_profile[1][0],entry.deck_profile[2][0]))
			mat.set_shader_parameter("source_run",float(entry.end[2]))
			mat.set_shader_parameter("source_rise",float(entry.end[1]))
			mat.set_shader_parameter("source_width",float(entry.width))
			mat.set_shader_parameter("source_foot",float(entry.foot_y))
			mat.set_shader_parameter("curved",family=="corner")
			mat.set_shader_parameter("source_radius",float(entry.get("radius",entry.end[2])))
			combined.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,surface.surface_get_arrays(0))
			combined.surface_set_material(combined.get_surface_count()-1,mat)
	for child in node.get_children():_bake(child,pose,combined,entry,family)

# Godot's compatibility renderer can flip backface lighting when a MultiMesh
# instance has a negative determinant. Mirror source surface winding explicitly
# and keep all world transforms right-handed.
static func _left_handed(source:ArrayMesh) -> ArrayMesh:
	var output:=ArrayMesh.new()
	for i in source.get_surface_count():
		var arr:=source.surface_get_arrays(i)
		var triangles:PackedInt32Array=arr[Mesh.ARRAY_INDEX]
		if triangles.is_empty():
			for j in arr[Mesh.ARRAY_VERTEX].size():triangles.append(j)
		for j in range(0,triangles.size(),3):
			var temp:=triangles[j+1]
			triangles[j+1]=triangles[j+2]
			triangles[j+2]=temp
		arr[Mesh.ARRAY_INDEX]=triangles
		output.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,arr)
		var mat:ShaderMaterial=source.surface_get_material(i).duplicate()
		mat.set_shader_parameter("left_handed",true)
		output.surface_set_material(i,mat)
	return output

static func _flat(p:Vector3) -> Vector2:return Vector2(p.x,p.z)
static func _dir(p:Vector2) -> Vector3:return Vector3(p.x,0,p.y)

func _place(family:String,a:Vector3,b:Vector3,forward:Vector3,run:float,mirror:bool,cut:bool) -> void:
	if mirror:family="left_corner"
	var key:=family+str(a.snapped(Vector3.ONE*.012))+str(b.snapped(Vector3.ONE*.012))
	if used.has(key):return
	used[key]=true
	if cut:suspended.append([a,b,forward])
	var side:=Vector3.UP.cross(forward)
	var basis:=Basis(side,Vector3.UP,forward)
	transforms[family].append(Transform3D(basis,Vector3(a.x,0,a.z)))
	values[family].append(Color(a.y/4.,b.y/4.,run/4.,1. if cut else 0.))
	counts[family]+=1

func place_span(a:Vector3,b:Vector3,clear_pier:Callable) -> bool:
	var delta:=_flat(b)-_flat(a)
	var length:=delta.length()
	var family:="incline" if absf(a.y-b.y)>.065 and absf(a.y-b.y)>.095*length else "straight"
	if not meshes.has(family):return false
	var nominal:float=float(specs[family].end[2])*WIDTH/float(specs[family].width)
	# Freight coming out of the paid cooker changes height over a shortened
	# adapter. The original guard/roller width stays fixed during this fit.
	var minimum_run:=maxf(.46,nominal*.28) if family=="incline" else maxf(.37,nominal*.43)
	if length<minimum_run:return false
	var modules:=maxi(1,roundi(length/nominal))
	var forward:=_dir(delta/length)
	for i in modules:
		var start:=a.lerp(b,float(i)/modules)
		var stop:=a.lerp(b,(i+1.)/modules)
		var cut:bool=clear_pier.call(start.lerp(stop,.5),forward)!=1. or clear_pier.call(start.lerp(stop,.15),forward)!=1. or clear_pier.call(start.lerp(stop,.85),forward)!=1.
		_place(family,start,stop,forward,length/modules,false,cut)
	return true

# Find a complete 90° arc from the actual path. The crossing planner may
# introduce height samples, so detect the shape in XZ independently of Y.
func place_corner(path:PackedVector3Array,first:int,clear_pier:Callable) -> int:
	if not meshes.has("corner") or first+5>=path.size():return first
	var p:=_flat(path[first])
	var q:=_flat(path[first+1])
	var r:=_flat(path[first+2])
	var u:=q-p
	var v:=r-p
	var det:=2.*u.cross(v)
	if absf(det)<.000035 or u.length()>.151:return first
	var offset:=Vector2(v.y*u.length_squared()-u.y*v.length_squared(),u.x*v.length_squared()-v.x*u.length_squared())/det
	var radius:=offset.length()
	if radius<WIDTH*.55 or radius>.67:return first
	var center:=p+offset
	var prev:=p-center
	var angle:=0.
	var last:=first
	for i in range(first+1,path.size()):
		var rad:=_flat(path[i])-center
		if absf(rad.length()-radius)>.009:break
		var turn:=prev.angle_to(rad)
		if turn*det<=0. or absf(turn)>.37:break
		angle+=turn
		last=i
		prev=rad
		if absf(angle)>=PI*.5-.016:break
	if absf(absf(angle)-PI*.5)>.038 or last-first<5:return first
	var entry:=p-center
	var forward:=_dir(entry.rotated(signf(angle)*PI*.5).normalized())
	var cut:=false
	for i in range(first,last+1):
		if clear_pier.call(path[i],forward)!=1.:cut=true
	_place("corner",path[first],path[last],forward,radius,angle>0,cut)
	return last

func finish() -> void:
	for family:String in meshes:
		var placements:Array=transforms[family]
		if placements.is_empty():continue
		var batched:=MultiMesh.new()
		batched.transform_format=MultiMesh.TRANSFORM_3D
		batched.use_custom_data=true
		batched.mesh=meshes[family]
		batched.instance_count=placements.size()
		var bounds:=AABB()
		for i in placements.size():
			batched.set_instance_transform(i,placements[i])
			batched.set_instance_custom_data(i,values[family][i])
			var box:=AABB((placements[i] as Transform3D).origin-Vector3(2,.25,2),Vector3(4,3,4))
			bounds=box if i==0 else bounds.merge(box)
		batched.custom_aabb=bounds
		var module:=MultiMeshInstance3D.new()
		module.name="D01"+family.capitalize()
		module.multimesh=batched
		add_child(module)
