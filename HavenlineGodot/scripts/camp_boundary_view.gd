class_name HavenlineCampBoundaryView
extends Node3D

const Boundary=preload("res://scripts/camp_boundary.gd")
const Surface=preload("res://scripts/outpost_surface.gd")
const Scenery=preload("res://scripts/scenery_batch.gd")
const BOUNDARY_SHADER=preload("res://assets/t03_boundary_v2/t03_boundary_v2.gdshader")
const BOUNDARY_ASSET_ROOT := "res://assets/t03_boundary_v2/"
# Iteration 11D: keep authored mesh scale/rhythm and derive each visible gate
# leaf from the family-specific geometry that also owns crossing authority.
const FENCE_SOURCE_LENGTH := 2.9409
const GATE_LEAF_SOURCE_LENGTH := 2.90
const FENCE_ROOT_SINK := 0.22
const VISUAL_JOIN_OVERLAP := 0.04
const SOUTH_VISUAL_JOIN_OVERLAP := VISUAL_JOIN_OVERLAP
const VISUAL_CORNER_JOIN_OVERLAP := VISUAL_JOIN_OVERLAP
# Rendering may not compress the authored palisade below a readable picket
# rhythm. Short residual rows keep their gate-side endpoint fixed; only an
# exterior corner may extend outward, while longer rows share a tiny internal
# overlap between adjacent visual panels. Collision/gate authority is untouched.
const SOUTH_VISUAL_MIN_PANEL_LENGTH := 1.62
const SOUTH_VISUAL_MAX_PANEL_LENGTH := Boundary.PANEL_TARGET + 0.10
const SOUTH_VISUAL_MAX_OUTER_EXTENSION := 0.95
const SOUTH_VISUAL_MAX_INTERNAL_EXTENSION := 0.08
# The scaled threshold post is about 0.35 wide. A 0.18 backset seats the leaf
# under the post without returning to the old 0.38 over-backset/dark seam.
const GATE_HINGE_OVERLAP := 0.18
const VISUAL_GATE_HINGE_BACKSET := GATE_HINGE_OVERLAP
const MAIN_WORK_VISUAL_LEAF_LENGTH := Boundary.GATE_LEAF_LENGTH
const MAIN_WORK_VISUAL_OPEN_ANGLE := Boundary.GATE_OPEN_ANGLE
const MAIN_WORK_GATE_HINGE_OVERLAP := VISUAL_GATE_HINGE_BACKSET
const RIVER_VISUAL_LEAF_LENGTH := Boundary.RIVER_GATE_LEAF_LENGTH
const RIVER_VISUAL_OPEN_ANGLE := Boundary.RIVER_GATE_OPEN_ANGLE
const RIVER_WEST_VISUAL_OPEN_ANGLE := Boundary.RIVER_GATE_OPEN_ANGLE
const RIVER_GATE_VISUAL_HINGE_OVERLAP := VISUAL_GATE_HINGE_BACKSET
const GATE_LEAF_HINGE_SINK := 0.08
const GATE_LEAF_ROOT_SINK := 0.10
const TERRAIN_SEAT_SAMPLES := 7
const GATE_POST_ROOT_SINK := 0.20
# Keep the same authored post footprint/height at every portal so threshold
# markers do not change category between north, work and river entrances.
const MAIN_GATE_POST_SCALE := 1.12
const MAIN_GATE_POST_HEIGHT_SCALE := 1.08
const WORK_GATE_POST_SCALE := 1.12
const WORK_GATE_POST_HEIGHT_SCALE := 1.08
const RIVER_GATE_POST_SCALE := 1.12
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
func _segment_transform(a:Vector2,b:Vector2,overlap:=0.0,root_sink:=FENCE_ROOT_SINK,end_root_sink:=-1.0,source_length:=FENCE_SOURCE_LENGTH,terrain_seat:=false)->Transform3D:
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
	var basis:=Basis(x_axis,y_axis,z_axis).scaled(Vector3(length/source_length,1.0,1.0))
	return Transform3D(basis,(pa+pb)*.5)

func _post_transform(p:Vector2,tangent:Vector2,visual_scale:=1.0,height_scale:=1.0)->Transform3D:
	var angle:=atan2(tangent.y,tangent.x)
	var basis:=Basis(Vector3.UP,-angle).scaled(Vector3(visual_scale,height_scale,visual_scale))
	return Transform3D(basis,Vector3(p.x,Surface.height_at(p)-GATE_POST_ROOT_SINK,p.y))

func _gate_leaf_transform(leaf:Dictionary,hinge_backset:float)->Transform3D:
	# Backset only the hinge edge beneath the authored threshold post. The free
	# edge stays fixed, so seam closure never steals visual or collision aperture.
	var a:=Vector2(leaf.a);var b:=Vector2(leaf.b)
	var direction:=(b-a).normalized()
	return _segment_transform(a-direction*hinge_backset,b,0.0,GATE_LEAF_HINGE_SINK,GATE_LEAF_ROOT_SINK,GATE_LEAF_SOURCE_LENGTH,false)

func _visual_gate_leaf_specs()->Array[Dictionary]:
	# Match the configured main/work and river gate families exactly.
	return Boundary.gate_leaf_specs()

func _visual_fence_specs()->Array[Dictionary]:
	# Curved river-side rows are sampled more finely than the authored mesh.
	# Group adjacent collision spans for rendering, then normalize ONLY visual
	# length so the picket rhythm cannot compress. Gate-side row endpoints stay
	# exact; a short corner residual may extend outward behind the side fence.
	var source:Array[Dictionary]=Boundary.panel_specs()
	var result:Array[Dictionary]=[]
	var i:=0
	while i<source.size():
		var row_id:=String(source[i].boundary)
		if not row_id.begins_with("south-"):
			result.append(source[i]);i+=1;continue
		var j:=i
		var total:=0.0
		while j<source.size() and String(source[j].boundary)==row_id:
			total+=float(source[j].length);j+=1
		var count:=j-i
		var groups:=maxi(1,ceili(total/Boundary.PANEL_TARGET))
		for g in range(groups):
			var first:=i+floori(float(g)*float(count)/float(groups))
			var last:=i+ceili(float(g+1)*float(count)/float(groups))-1
			var source_a:=Vector2(source[first].a)
			var source_b:=Vector2(source[last].b)
			var p0:=source_a
			var p1:=source_b
			var length:=p0.distance_to(p1)
			var internal_extension:=0.0
			var outer_extension:=0.0
			if length<SOUTH_VISUAL_MIN_PANEL_LENGTH:
				var direction:=(p1-p0).normalized()
				var shortage:=SOUTH_VISUAL_MIN_PANEL_LENGTH-length
				var can_extend_start:=g>0
				var can_extend_end:=g<groups-1
				var extension_sides:=int(can_extend_start)+int(can_extend_end)
				if extension_sides>0:
					var each:=shortage/float(extension_sides)
					assert(each<=SOUTH_VISUAL_MAX_INTERNAL_EXTENSION+.0001,"South fence internal visual overlap exceeded safe budget")
					if can_extend_start:p0-=direction*each
					if can_extend_end:p1+=direction*each
					internal_extension=each
				elif absf(source_a.x)>=Boundary.SIDE_X-.01:
					assert(shortage<=SOUTH_VISUAL_MAX_OUTER_EXTENSION+.0001,"South fence outer visual extension exceeded safe budget")
					p0-=direction*shortage;outer_extension=shortage
				elif absf(source_b.x)>=Boundary.SIDE_X-.01:
					assert(shortage<=SOUTH_VISUAL_MAX_OUTER_EXTENSION+.0001,"South fence outer visual extension exceeded safe budget")
					p1+=direction*shortage;outer_extension=shortage
				else:
					assert(false,"South visual row cannot preserve authored spacing without stealing a gate opening: "+row_id)
			var visual_length:=p0.distance_to(p1)
			assert(visual_length>=SOUTH_VISUAL_MIN_PANEL_LENGTH-.001 and visual_length<=SOUTH_VISUAL_MAX_PANEL_LENGTH+.001,"South visual fence length outside authored rhythm")
			var gate_endpoint_error:=0.0
			if g==0 and absf(source_a.x)<Boundary.SIDE_X-.01:gate_endpoint_error=maxf(gate_endpoint_error,p0.distance_to(source_a))
			if g==groups-1 and absf(source_b.x)<Boundary.SIDE_X-.01:gate_endpoint_error=maxf(gate_endpoint_error,p1.distance_to(source_b))
			result.append({
				"boundary":row_id,"a":p0,"b":p1,"mid":(p0+p1)*.5,
				"length":visual_length,"tangent":(p1-p0).normalized(),
				"spacing_internal_extension":internal_extension,
				"spacing_outer_extension":outer_extension,
				"gate_endpoint_error":gate_endpoint_error
			})
		i=j
	return result

func configure(game):
	name="Task03CampBoundary"
	var fence_transforms:Array[Transform3D]=[]
	var visual_fence_specs:=_visual_fence_specs()
	var south_visual_total:=0.0
	var south_visual_count:=0
	var south_visual_min:=999.0
	var south_visual_max:=0.0
	var south_visual_outer_extension_max:=0.0
	var south_visual_internal_extension_max:=0.0
	var south_visual_gate_endpoint_error_max:=0.0
	var south_corners:=[Boundary.south_point(-Boundary.SIDE_X),Boundary.south_point(Boundary.SIDE_X)]
	for panel in visual_fence_specs:
		var is_south:=String(panel.boundary).begins_with("south-")
		var overlap:=SOUTH_VISUAL_JOIN_OVERLAP if is_south else VISUAL_JOIN_OVERLAP
		if south_corners.any(func(c):return Vector2(panel.a).distance_to(c)<.01 or Vector2(panel.b).distance_to(c)<.01):overlap=maxf(overlap,VISUAL_CORNER_JOIN_OVERLAP)
		fence_transforms.append(_segment_transform(panel.a,panel.b,overlap))
		if is_south:
			var visual_length:=Vector2(panel.a).distance_to(Vector2(panel.b))
			south_visual_total+=visual_length;south_visual_count+=1
			south_visual_min=minf(south_visual_min,visual_length)
			south_visual_max=maxf(south_visual_max,visual_length)
			south_visual_outer_extension_max=maxf(south_visual_outer_extension_max,float(panel.get("spacing_outer_extension",0.0)))
			south_visual_internal_extension_max=maxf(south_visual_internal_extension_max,float(panel.get("spacing_internal_extension",0.0)))
			south_visual_gate_endpoint_error_max=maxf(south_visual_gate_endpoint_error_max,float(panel.get("gate_endpoint_error",0.0)))
	fence_batch=Scenery.instances(_mesh(game,"fence_panel"),fence_transforms,self)
	fence_batch.name="ReferencePalisadeFence"
	var gate_leaf_transforms:Array[Transform3D]=[]
	for leaf in _visual_gate_leaf_specs():
		gate_leaf_transforms.append(_gate_leaf_transform(leaf,VISUAL_GATE_HINGE_BACKSET))
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
	descriptor["south_visual_grouping_from_panel_specs"]=true
	descriptor["south_visual_spacing_normalized"]=true
	descriptor["south_visual_panel_instances"]=south_visual_count
	descriptor["south_visual_panel_average_length"]=south_visual_total/float(maxi(1,south_visual_count))
	descriptor["south_visual_min_panel_length"]=south_visual_min
	descriptor["south_visual_max_panel_length"]=south_visual_max
	descriptor["south_visual_outer_extension_max"]=south_visual_outer_extension_max
	descriptor["south_visual_internal_extension_max"]=south_visual_internal_extension_max
	descriptor["south_visual_gate_endpoint_error_max"]=south_visual_gate_endpoint_error_max
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
	descriptor["fence_source_length"]=FENCE_SOURCE_LENGTH
	descriptor["gate_leaf_source_length"]=GATE_LEAF_SOURCE_LENGTH
	descriptor["uniform_gate_presentation"]=false
	descriptor["gate_presentation_uses_authoritative_family_geometry"]=true
	descriptor["rigid_gate_leaf_endpoint_seating"]=true
	descriptor["fence_root_sink"]=FENCE_ROOT_SINK
	descriptor["visual_join_overlap"]=VISUAL_JOIN_OVERLAP
	descriptor["south_visual_join_overlap"]=SOUTH_VISUAL_JOIN_OVERLAP
	descriptor["visual_corner_join_overlap"]=VISUAL_CORNER_JOIN_OVERLAP
	descriptor["gate_hinge_overlap"]=GATE_HINGE_OVERLAP
	descriptor["main_work_visual_gate_leaf_length"]=MAIN_WORK_VISUAL_LEAF_LENGTH
	descriptor["main_work_visual_gate_open_angle"]=MAIN_WORK_VISUAL_OPEN_ANGLE
	descriptor["main_work_gate_hinge_overlap"]=MAIN_WORK_GATE_HINGE_OVERLAP
	descriptor["river_visual_gate_leaf_length"]=RIVER_VISUAL_LEAF_LENGTH
	descriptor["river_visual_gate_open_angle"]=RIVER_VISUAL_OPEN_ANGLE
	descriptor["river_west_visual_gate_open_angle"]=RIVER_WEST_VISUAL_OPEN_ANGLE
	descriptor["river_gate_visual_hinge_overlap"]=RIVER_GATE_VISUAL_HINGE_OVERLAP
	var river_visual_clear_min:=999.0
	for gate in Boundary.gate_specs():
		if gate.kind=="river":
			var clear_angle:=RIVER_WEST_VISUAL_OPEN_ANGLE if gate.id=="river--9.0" else RIVER_VISUAL_OPEN_ANGLE
			river_visual_clear_min=minf(river_visual_clear_min,float(gate.width)-2.0*RIVER_VISUAL_LEAF_LENGTH*cos(clear_angle))
	descriptor["river_visual_clear_width_min"]=river_visual_clear_min
	descriptor["river_visual_clearance_pass"]=river_visual_clear_min>=Boundary.RIVER_VISUAL_CLEARANCE_MIN
	descriptor["river_gate_leaf_visual_transform_only"]=true
	descriptor["gate_leaf_hinge_backset_is_start_only"]=true
	descriptor["threshold_post_contact_repair"]="authoritative-leaf-geometry-plus-post-width-hinge-backset"
	descriptor["visual_gate_leaf_transform_only"]=true
	descriptor["gate_leaf_root_sink"]=GATE_LEAF_ROOT_SINK
	descriptor["gate_leaf_hinge_sink"]=GATE_LEAF_HINGE_SINK
	descriptor["terrain_seat_samples"]=TERRAIN_SEAT_SAMPLES
	descriptor["terrain_crown_applied_to_gate_leaves_only"]=false
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
