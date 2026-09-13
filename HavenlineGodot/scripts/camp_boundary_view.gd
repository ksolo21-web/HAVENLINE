class_name HavenlineCampBoundaryView
extends Node3D

const Boundary=preload("res://scripts/camp_boundary.gd")
const Surface=preload("res://scripts/outpost_surface.gd")
const Scenery=preload("res://scripts/scenery_batch.gd")
# Slightly deeper seating and a tiny visual-only overlap remove daylight slivers
# at joints on uneven/curved terrain. Collision still uses Boundary.panel_specs()
# exactly, so openings and gameplay widths do not change.
const FENCE_ROOT_SINK := 0.40
const VISUAL_JOIN_OVERLAP := 0.10
const VISUAL_CORNER_JOIN_OVERLAP := 0.28
const GATE_HINGE_OVERLAP := 0.12
const GATE_LEAF_ROOT_SINK := 0.56
const TERRAIN_SEAT_SAMPLES := 7
const GATE_POST_ROOT_SINK := 0.40
const MAIN_GATE_POST_SCALE := 1.15
const MAIN_GATE_POST_HEIGHT_SCALE := 1.55
const WORK_GATE_POST_SCALE := 1.18
const WORK_GATE_POST_HEIGHT_SCALE := 1.65
const RIVER_GATE_POST_SCALE := 1.24
const RIVER_GATE_POST_HEIGHT_SCALE := 1.85
var fence_batch:MultiMeshInstance3D
var post_batch:MultiMeshInstance3D
var descriptor:Dictionary={}

func _mesh(game,asset:String)->ArrayMesh:
	if not game.merged_cache.has(asset):
		var path="res://assets/environment_v2/"+asset.trim_prefix("world/")+".glb"
		assert(ResourceLoader.exists(path),"Missing authored Task 3 boundary asset: "+path)
		game.merged_cache[asset]=Scenery.compile(load(path))
	return game.merged_cache[asset]

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

func configure(game):
	name="Task03CampBoundary"
	var fence_transforms:Array[Transform3D]=[]
	var south_corners:=[Boundary.south_point(-Boundary.SIDE_X),Boundary.south_point(Boundary.SIDE_X)]
	for panel in Boundary.panel_specs():
		var overlap:=VISUAL_JOIN_OVERLAP
		if south_corners.any(func(c):return Vector2(panel.a).distance_to(c)<.01 or Vector2(panel.b).distance_to(c)<.01):overlap=VISUAL_CORNER_JOIN_OVERLAP
		fence_transforms.append(_segment_transform(panel.a,panel.b,overlap))
	for leaf in Boundary.gate_leaf_specs():fence_transforms.append(_segment_transform(leaf.a,leaf.b,GATE_HINGE_OVERLAP,FENCE_ROOT_SINK,GATE_LEAF_ROOT_SINK,true))
	fence_batch=Scenery.instances(_mesh(game,"world/barricade"),fence_transforms,self)
	fence_batch.name="AuthoredTimberFenceAndOpenGateLeaves"
	var post_transforms:Array[Transform3D]=[]
	for gate in Boundary.gate_specs():
		var tangent:Vector2=gate.tangent
		var post_scale:=RIVER_GATE_POST_SCALE if gate.kind=="river" else (WORK_GATE_POST_SCALE if gate.kind=="work" else MAIN_GATE_POST_SCALE)
		var post_height:=RIVER_GATE_POST_HEIGHT_SCALE if gate.kind=="river" else (WORK_GATE_POST_HEIGHT_SCALE if gate.kind=="work" else MAIN_GATE_POST_HEIGHT_SCALE)
		post_transforms.append(_post_transform(gate.a,tangent,post_scale,post_height))
		post_transforms.append(_post_transform(gate.b,tangent,post_scale,post_height))
	post_batch=Scenery.instances(_mesh(game,"world/lantern_post"),post_transforms,self)
	post_batch.name="GateLanternPosts"
	descriptor=Boundary.evidence()
	descriptor["fence_visual_instances"]=fence_transforms.size()
	descriptor["collision_panel_instances"]=Boundary.panel_specs().size()
	descriptor["open_gate_leaf_instances"]=Boundary.gate_leaf_specs().size()
	descriptor["gate_post_instances"]=post_transforms.size()
	descriptor["visual_collision_share_panel_authority"]=true
	descriptor["authored_fence_asset"]="environment_v2/barricade.glb"
	descriptor["authored_gate_post_asset"]="environment_v2/lantern_post.glb"
	descriptor["fence_root_sink"]=FENCE_ROOT_SINK
	descriptor["visual_join_overlap"]=VISUAL_JOIN_OVERLAP
	descriptor["visual_corner_join_overlap"]=VISUAL_CORNER_JOIN_OVERLAP
	descriptor["gate_hinge_overlap"]=GATE_HINGE_OVERLAP
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
	descriptor["draw_batches"]=2
