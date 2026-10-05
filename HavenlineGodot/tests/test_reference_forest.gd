extends SceneTree
const Forest = preload("res://scripts/reference_forest.gd")
const Scenery = preload("res://scripts/scenery_batch.gd")
var checks: Array = []
var failures: Array = []
func check(name: String, result: bool):
	checks.append({"name":name,"passed":result})
	if not result: failures.append(name)
func _initialize(): call_deferred("run")
func run():
	var bounds := Vector2(14.2,16.2)
	var records := Forest.placements(bounds)
	check("Dense framing has at least 350 authored trees",records.size()>=350)
	check("Forest placement deterministic",records==Forest.placements(bounds))
	var seen := {}; var safe := true; var lanes := true
	for r in records:
		var p: Vector2 = r.point
		if absf(p.x)<bounds.x+1.7 and absf(p.y)<bounds.y+1.7: safe=false
		if absf(p.x)<3.5: lanes=false
		seen[str(p)] = true
	check("No duplicate trunk positions",seen.size()==records.size())
	check("Decorative forest does not occupy playable bounds",safe)
	check("Existing north/south approaches remain open",lanes)
	var manifest=JSON.parse_string(FileAccess.get_file_as_string("res://assets/reference_forest/manifest.json"))
	check("Three new variants are registered",manifest.assets.size()==3)
	check("Generator cannot grant independent art approval",not manifest.independent_visual_approval)
	check("Generator cannot certify 4K60",not manifest.physical_4k60_verified)
	for a in manifest.assets:
		var scene: PackedScene=load("res://assets/reference_forest/%s.glb"%a.name)
		check("Authored variant imports: "+a.name,scene!=null)
		var mesh: ArrayMesh=Scenery.compile(scene)
		check("Separate snow/underside/trunk surfaces: "+a.name,mesh.get_surface_count()==3)
		check("Tree geometry under 10000 base triangles: "+a.name,a.triangles<10000)
		check("Model height remains reference scale: "+a.name,mesh.get_aabb().size.y>2.5 and mesh.get_aabb().size.y<4.0)
		var normals_ok:=true;var finite:=true;var textures_ok:=true
		for i in mesh.get_surface_count():
			var arrays=mesh.surface_get_arrays(i)
			for n in arrays[Mesh.ARRAY_NORMAL]:
				if not n.is_finite() or absf(n.length()-1.0)>.015:normals_ok=false
			for v in arrays[Mesh.ARRAY_VERTEX]:
				if not v.is_finite():finite=false
			var material: BaseMaterial3D=mesh.surface_get_material(i)
			if not material or not material.albedo_texture:textures_ok=false
		check("Finite vertices: "+a.name,finite)
		check("Unit finite shading normals: "+a.name,normals_ok)
		check("Actual authored surface maps: "+a.name,textures_ok)
	print(JSON.stringify({"suite":"reference_forest_T01","checks":checks,"failures":failures,"passed":failures.is_empty(),"independent_critic":false,"visual_score":null,"physical_4k60_certified":false}))
	quit(0 if failures.is_empty() else 1)
