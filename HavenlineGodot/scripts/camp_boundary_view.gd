class_name HavenlineCampBoundaryView
extends Node3D

const Boundary=preload("res://scripts/camp_boundary.gd")
const Surface=preload("res://scripts/outpost_surface.gd")
const Scenery=preload("res://scripts/scenery_batch.gd")
const FENCE_ROOT_SINK := 0.04
var fence_batch:MultiMeshInstance3D
var post_batch:MultiMeshInstance3D
var descriptor:Dictionary={}

func _mesh(game,asset:String)->ArrayMesh:
	if not game.merged_cache.has(asset):
		var path="res://assets/environment_v2/"+asset.trim_prefix("world/")+".glb"
		assert(ResourceLoader.exists(path),"Missing authored Task 3 boundary asset: "+path)
		game.merged_cache[asset]=Scenery.compile(load(path))
	return game.merged_cache[asset]

func _segment_transform(a:Vector2,b:Vector2)->Transform3D:
	var pa:=Vector3(a.x,Surface.height_at(a)-FENCE_ROOT_SINK,a.y);var pb:=Vector3(b.x,Surface.height_at(b)-FENCE_ROOT_SINK,b.y)
	var x_axis:=(pb-pa).normalized()
	var z_axis:=x_axis.cross(Vector3.UP).normalized()
	if z_axis.length_squared()<.001:z_axis=Vector3.FORWARD
	var y_axis:=z_axis.cross(x_axis).normalized()
	var length:=pa.distance_to(pb)
	var basis:=Basis(x_axis,y_axis,z_axis).scaled(Vector3(length/Boundary.PANEL_SOURCE_LENGTH,1.0,1.0))
	return Transform3D(basis,(pa+pb)*.5)

func _post_transform(p:Vector2,tangent:Vector2)->Transform3D:
	var angle:=atan2(tangent.y,tangent.x)
	return Transform3D(Basis(Vector3.UP,-angle),Vector3(p.x,Surface.height_at(p),p.y))

func configure(game):
	name="Task03CampBoundary"
	var fence_transforms:Array[Transform3D]=[]
	for panel in Boundary.panel_specs():fence_transforms.append(_segment_transform(panel.a,panel.b))
	for leaf in Boundary.gate_leaf_specs():fence_transforms.append(_segment_transform(leaf.a,leaf.b))
	fence_batch=Scenery.instances(_mesh(game,"world/barricade"),fence_transforms,self)
	fence_batch.name="AuthoredTimberFenceAndOpenGateLeaves"
	var post_transforms:Array[Transform3D]=[]
	for gate in Boundary.gate_specs():
		var tangent:Vector2=gate.tangent
		post_transforms.append(_post_transform(gate.a,tangent))
		post_transforms.append(_post_transform(gate.b,tangent))
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
	descriptor["primitive_fence_meshes_created"]=false
	descriptor["draw_batches"]=2
