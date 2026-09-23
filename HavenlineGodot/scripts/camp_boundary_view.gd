class_name HavenlineCampBoundaryView
extends Node3D

const Boundary=preload("res://scripts/camp_boundary.gd")
const Surface=preload("res://scripts/outpost_surface.gd")
const Scenery=preload("res://scripts/scenery_batch.gd")
const BOUNDARY_SHADER=preload("res://assets/t03_boundary_v2/t03_boundary_v2.gdshader")
const BOUNDARY_ASSET_ROOT := "res://assets/t03_boundary_v2/"
# Slightly deeper seating and a tiny visual-only overlap remove daylight slivers
# at joints on uneven/curved terrain. Collision still uses Boundary.panel_specs()
# exactly, so openings and gameplay widths do not change.
const FENCE_ROOT_SINK := 0.40
const VISUAL_JOIN_OVERLAP := 0.18
const VISUAL_CORNER_JOIN_OVERLAP := 0.28
const GATE_HINGE_OVERLAP := 0.12
# North/work leaves are a presentation-only readability correction. The
# authoritative gate specs/collision gaps remain in camp_boundary.gd.
const MAIN_WORK_VISUAL_LEAF_LENGTH := 1.30
const MAIN_WORK_VISUAL_OPEN_ANGLE := 0.70
const MAIN_WORK_GATE_HINGE_OVERLAP := 0.24
# River leaves use the same visual-only presentation rule: keep the authoritative
# crossing/collision contract, but turn a shorter framed panel toward the camera
# so the future crossing reads unmistakably as a gate.
const RIVER_VISUAL_LEAF_LENGTH := 1.40
const RIVER_VISUAL_OPEN_ANGLE := 0.72
const RIVER_GATE_VISUAL_HINGE_OVERLAP := 0.24
const GATE_LEAF_ROOT_SINK := 0.56
const TERRAIN_SEAT_SAMPLES := 7
const GATE_POST_ROOT_SINK := 0.40
const MAIN_GATE_POST_SCALE := 1.00
const MAIN_GATE_POST_HEIGHT_SCALE := 1.05
const WORK_GATE_POST_SCALE := 1.00
const WORK_GATE_POST_HEIGHT_SCALE := 1.00
const RIVER_GATE_POST_SCALE := 1.05
const RIVER_GATE_POST_HEIGHT_SCALE := 1.08
var fence_batch:MultiMeshInstance3D
var gate_leaf_batch:MultiMeshInstance3D
var post_batch:MultiMeshInstance3D
var descriptor:Dictionary={}
var _boundary_materials:Dictionary={}

func _material(key:String)->ShaderMaterial:
	if _boundary_materials.has(key):return _boundary_materials[key]
	var m:=ShaderMaterial.new()
	m.shader=BOUNDARY_SHADER
	match key:
		"timber":
			m.set_shader_parameter("base_color",Color(0.76,0.53,0.40,1.0));m.set_shader_parameter("roughness_value",0.86);m.set_shader_parameter("detail_strength",0.024);m.set_shader_parameter("detail_scale",3.2)
		"timber_dark":
			m.set_shader_parameter("base_color",Color(0.56,0.35,0.23,1.0));m.set_shader_parameter("roughness_value",0.89);m.set_shader_parameter("detail_strength",0.022);m.set_shader_parameter("detail_scale",3.4)
		"snow":
			m.set_shader_parameter("base_color",Color(0.95,0.985,1.0,1.0));m.set_shader_parameter("roughness_value",0.78);m.set_shader_parameter("detail_strength",0.025);m.set_shader_parameter("detail_scale",4.0)
		"blue":
			m.set_shader_parameter("base_color",Color(0.13,0.28,0.36,1.0));m.set_shader_parameter("roughness_value",0.46);m.set_shader_parameter("metallic_value",0.45);m.set_shader_parameter("detail_strength",0.025)
		"orange":
			m.set_shader_parameter("base_color",Color(0.98,0.66,0.22,1.0));m.set_shader_parameter("roughness_value",0.38);m.set_shader_parameter("metallic_value",0.10);m.set_shader_parameter("emission_color",Vector3(0.20,0.045,0.006));m.set_shader_parameter("detail_strength",0.015)
		"iron":
			m.set_shader_parameter("base_color",Color(0.20,0.15,0.10,1.0));m.set_shader_parameter("roughness_value",0.42);m.set_shader_parameter("metallic_value",0.70);m.set_shader_parameter("detail_strength",0.02)
		"stone":
			m.set_shader_parameter("base_color",Color(0.36,0.46,0.51,1.0));m.set_shader_parameter("roughness_value",0.95);m.set_shader_parameter("detail_strength",0.08);m.set_shader_parameter("detail_scale",4.5)
		"brass":
			m.set_shader_parameter("base_color",Color(0.66,0.42,0.17,1.0));m.set_shader_parameter("roughness_value",0.44);m.set_shader_parameter("metallic_value",0.62);m.set_shader_parameter("detail_strength",0.02)
		_:
			assert(false,"Unknown T03 authored boundary material: "+key)
	_boundary_materials[key]=m
	return m

func _mesh(game,asset:String)->ArrayMesh:
	var cache_key:="t03-boundary-v2/"+asset
	if not game.merged_cache.has(cache_key):
		var path:=BOUNDARY_ASSET_ROOT+asset+".obj"
		assert(ResourceLoader.exists(path),"Missing authored Task 3 boundary asset: "+path)
		var source=load(path)
		assert(source is ArrayMesh,"T03 boundary source must import as ArrayMesh: "+path)
		var mesh:ArrayMesh=source.duplicate()
		for index in mesh.get_surface_count():
			var imported:=mesh.surface_get_material(index)
			var key:=""
			if imported!=null:key=String(imported.resource_name).to_lower()
			if key.is_empty():key=String(mesh.surface_get_name(index)).to_lower()
			assert(key in ["timber","timber_dark","snow","blue","orange","iron","stone","brass"],"Unmapped T03 boundary surface: "+key)
			mesh.surface_set_material(index,_material(key))
		game.merged_cache[cache_key]=mesh
	return game.merged_cache[cache_key]
func _segment_transform(a:Vector2,b:Vector2,overlap:=0.0,root_sink:=FENCE_ROOT_SINK,end_root_sink:=-1.0,terrain_seat:=false)->Transform3D:
	var aa:=a;var bb:=b
	var flat:=b-a
	if overlap>0.0 and flat.length_squared()>.0001:
		var d:=flat.normalized();aa-=d*overlap*.5;bb+=d*overlap*.5
	# A rigid authored panel follows the chord between its end points, while the
	# snow bank curves underneath it. Sampling the full chord prevents a local
	# terrain crown from leaving visible daylight below an otherwise sunk leaf.
	var height_a:=Surface.height_at(aa);var height_b:=Surface.height_at(bb)
	var start_sink:=root_sink
	var finish_sink:=root_sink if end_root_sink<0.0 else end_root_sink
	if terrain_seat:
		for sample in range(1,TERRAIN_SEAT_SAMPLES):
			var t:=float(sample)/float(TERRAIN_SEAT_SAMPLES)
			var p:=aa.lerp(bb,t)
			var chord_height:=lerpf(height_a,height_b,t)
			var required_sink:=maxf(0.0,chord_height-Surface.height_at(p))
			finish_sink=maxf(finish_sink,(required_sink-(1.0-t)*start_sink)/t)
	var pa:=Vector3(aa.x,height_a-start_sink,aa.y);var pb:=Vector3(bb.x,height_b-finish_sink,bb.y)
	var x_axis:=(pb-pa).normalized()
	var z_axis:=x_axis.cross(Vector3.UP).normalized()
	if z_axis.length_squared()<.001:z_axis=Vector3.FORWARD
	var y_axis:=z_axis.cross(x_axis).normalized()
	var length:=pa.distance_to(pb)
	var basis:=Basis(x_axis,y_axis,z_axis).scaled(Vector3(length/Boundary.PANEL_SOURCE_LENGTH,1.0,1.0))
	return Transform3D(basis,(pa+pb)*.5)

func _post_transform(p:Vector2,tangent:Vector2,visual_scale:=1.0,height_scale:=1.0)->Transform3D:
	var angle:=atan2(tangent.y,tangent.x)
	var basis:=Basis(Vector3.UP,-angle).scaled(Vector3(visual_scale,height_scale,visual_scale))
	return Transform3D(basis,Vector3(p.x,Surface.height_at(p)-GATE_POST_ROOT_SINK,p.y))

func _visual_gate_leaf_specs()->Array[Dictionary]:
	# Collision/opening authority remains in camp_boundary.gd. Presentation-only
	# leaf lengths/angles keep every framed X-braced panel readable in normal
	# gameplay views without changing route or collision geometry.
	var result:Array[Dictionary]=[]
	for gate in Boundary.gate_specs():
		var a:Vector2=gate.a;var b:Vector2=gate.b;var tangent:Vector2=gate.tangent;var mid:Vector2=gate.center
		var inward:=(Boundary.CAMP_CENTER-mid).normalized()
		var visual_length:=RIVER_VISUAL_LEAF_LENGTH if gate.kind=="river" else MAIN_WORK_VISUAL_LEAF_LENGTH
		var visual_angle:=RIVER_VISUAL_OPEN_ANGLE if gate.kind=="river" else MAIN_WORK_VISUAL_OPEN_ANGLE
		var left_dir:=tangent.rotated(visual_angle)
		if left_dir.dot(inward)<0:left_dir=tangent.rotated(-visual_angle)
		var right_dir:=(-tangent).rotated(visual_angle)
		if right_dir.dot(inward)<0:right_dir=(-tangent).rotated(-visual_angle)
		result.append({"gate":gate.id,"kind":gate.kind,"hinge":a,"a":a,"b":a+left_dir*visual_length,"length":visual_length,"open_angle":visual_angle})
		result.append({"gate":gate.id,"kind":gate.kind,"hinge":b,"a":b,"b":b+right_dir*visual_length,"length":visual_length,"open_angle":visual_angle})
	return result

func configure(game):
	name="Task03CampBoundary"
	var fence_transforms:Array[Transform3D]=[]
	var south_corners:=[Boundary.south_point(-Boundary.SIDE_X),Boundary.south_point(Boundary.SIDE_X)]
	for panel in Boundary.panel_specs():
		var overlap:=VISUAL_JOIN_OVERLAP
		if south_corners.any(func(c):return Vector2(panel.a).distance_to(c)<.01 or Vector2(panel.b).distance_to(c)<.01):overlap=VISUAL_CORNER_JOIN_OVERLAP
		fence_transforms.append(_segment_transform(panel.a,panel.b,overlap))
	fence_batch=Scenery.instances(_mesh(game,"fence_panel"),fence_transforms,self)
	fence_batch.name="ReferencePalisadeFence"
	var gate_leaf_transforms:Array[Transform3D]=[]
	for leaf in _visual_gate_leaf_specs():
		var hinge_overlap:=RIVER_GATE_VISUAL_HINGE_OVERLAP if leaf.kind=="river" else MAIN_WORK_GATE_HINGE_OVERLAP
		gate_leaf_transforms.append(_segment_transform(leaf.a,leaf.b,hinge_overlap,FENCE_ROOT_SINK,GATE_LEAF_ROOT_SINK,true))
	gate_leaf_batch=Scenery.instances(_mesh(game,"gate_leaf"),gate_leaf_transforms,self)
	gate_leaf_batch.name="ReferenceFramedOpenGateLeaves"
	var post_transforms:Array[Transform3D]=[]
	for gate in Boundary.gate_specs():
		var tangent:Vector2=gate.tangent
		var post_scale:=RIVER_GATE_POST_SCALE if gate.kind=="river" else (WORK_GATE_POST_SCALE if gate.kind=="work" else MAIN_GATE_POST_SCALE)
		var post_height:=RIVER_GATE_POST_HEIGHT_SCALE if gate.kind=="river" else (WORK_GATE_POST_HEIGHT_SCALE if gate.kind=="work" else MAIN_GATE_POST_HEIGHT_SCALE)
		post_transforms.append(_post_transform(gate.a,tangent,post_scale,post_height))
		post_transforms.append(_post_transform(gate.b,tangent,post_scale,post_height))
	post_batch=Scenery.instances(_mesh(game,"gate_post"),post_transforms,self)
	post_batch.name="GateLanternPosts"
	descriptor=Boundary.evidence()
	descriptor["fence_visual_instances"]=fence_transforms.size()
	descriptor["collision_panel_instances"]=Boundary.panel_specs().size()
	descriptor["open_gate_leaf_instances"]=gate_leaf_transforms.size()
	descriptor["gate_post_instances"]=post_transforms.size()
	descriptor["visual_collision_share_panel_authority"]=true
	descriptor["authored_fence_asset"]="t03_boundary_v2/fence_panel.obj"
	descriptor["authored_gate_leaf_asset"]="t03_boundary_v2/gate_leaf.obj"
	descriptor["authored_gate_post_asset"]="t03_boundary_v2/gate_post.obj"
	descriptor["boundary_asset_manifest"]="t03_boundary_v2/manifest.json"
	descriptor["runtime_material_family"]="ShaderMaterial/t03_boundary_v2.gdshader"
	descriptor["imported_standard_materials_active"]=false
	descriptor["authored_boundary_asset_family"]="t03_boundary_v2"
	descriptor["fence_root_sink"]=FENCE_ROOT_SINK
	descriptor["visual_join_overlap"]=VISUAL_JOIN_OVERLAP
	descriptor["visual_corner_join_overlap"]=VISUAL_CORNER_JOIN_OVERLAP
	descriptor["gate_hinge_overlap"]=GATE_HINGE_OVERLAP
	descriptor["main_work_visual_gate_leaf_length"]=MAIN_WORK_VISUAL_LEAF_LENGTH
	descriptor["main_work_visual_gate_open_angle"]=MAIN_WORK_VISUAL_OPEN_ANGLE
	descriptor["main_work_gate_hinge_overlap"]=MAIN_WORK_GATE_HINGE_OVERLAP
	descriptor["river_visual_gate_leaf_length"]=RIVER_VISUAL_LEAF_LENGTH
	descriptor["river_visual_gate_open_angle"]=RIVER_VISUAL_OPEN_ANGLE
	descriptor["river_gate_visual_hinge_overlap"]=RIVER_GATE_VISUAL_HINGE_OVERLAP
	var river_visual_clear_min:=999.0
	for gate in Boundary.gate_specs():
		if gate.kind=="river":
			river_visual_clear_min=minf(river_visual_clear_min,float(gate.width)-2.0*RIVER_VISUAL_LEAF_LENGTH*cos(RIVER_VISUAL_OPEN_ANGLE))
	descriptor["river_visual_clear_width_min"]=river_visual_clear_min
	descriptor["river_visual_clearance_pass"]=river_visual_clear_min>=Boundary.RIVER_VISUAL_CLEARANCE_MIN
	descriptor["river_gate_leaf_visual_transform_only"]=true
	descriptor["visual_gate_leaf_transform_only"]=true
	descriptor["gate_leaf_root_sink"]=GATE_LEAF_ROOT_SINK
	descriptor["gate_leaf_hinge_sink"]=FENCE_ROOT_SINK
	descriptor["terrain_seat_samples"]=TERRAIN_SEAT_SAMPLES
	descriptor["terrain_crown_applied_to_gate_leaves_only"]=true
	descriptor["gate_post_root_sink"]=GATE_POST_ROOT_SINK
	descriptor["main_gate_post_scale"]=MAIN_GATE_POST_SCALE
	descriptor["main_gate_post_height_scale"]=MAIN_GATE_POST_HEIGHT_SCALE
	descriptor["river_gate_post_scale"]=RIVER_GATE_POST_SCALE
	descriptor["river_gate_post_height_scale"]=RIVER_GATE_POST_HEIGHT_SCALE
	descriptor["work_gate_post_scale"]=WORK_GATE_POST_SCALE
	descriptor["work_gate_post_height_scale"]=WORK_GATE_POST_HEIGHT_SCALE
	descriptor["lane_compression_depth"]=Surface.T03_LANE_COMPRESSION_DEPTH
	descriptor["lane_rut_depth"]=Surface.T03_LANE_RUT_DEPTH
	descriptor["lane_shoulder_height"]=Surface.T03_LANE_SHOULDER_HEIGHT
	descriptor["primitive_fence_meshes_created"]=false
	descriptor["draw_batches"]=3
