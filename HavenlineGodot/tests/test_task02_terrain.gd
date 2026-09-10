extends SceneTree
const Surface=preload("res://scripts/outpost_surface.gd")
const Main=preload("res://scripts/main.gd")
const Sim=preload("res://scripts/outpost_simulation.gd")
const Forest=preload("res://scripts/reference_forest.gd")
var checks: Array=[]
var failures: Array=[]
func check(name:String,passed:bool):
	checks.append({"name":name,"passed":passed})
	if not passed:failures.append(name)
func _initialize():call_deferred("run")
func run():
	var mesh:=Surface.mesh()
	var arrays:=mesh.surface_get_arrays(0)
	var vertices:PackedVector3Array=arrays[Mesh.ARRAY_VERTEX]
	var normals:PackedVector3Array=arrays[Mesh.ARRAY_NORMAL]
	var indices:PackedInt32Array=arrays[Mesh.ARRAY_INDEX]
	check("Single coherent indexed terrain surface",mesh.get_surface_count()==1 and indices.size()>vertices.size())
	check("Terrain budget below 125000 triangles",indices.size()/3<125000)
	check("Cached terrain mesh shared instead of rebuilding every frame",Surface.mesh()==mesh)
	var finite:=true;var upward:=true;var agreement:=true
	for i in range(vertices.size()):
		if not vertices[i].is_finite() or not normals[i].is_finite():finite=false
		if normals[i].y<=0 or absf(normals[i].length()-1)>.002:upward=false
		if absf(vertices[i].y-Surface.height_at(Vector2(vertices[i].x,vertices[i].z)))>.0001:agreement=false
	check("All terrain vertices and normals finite",finite)
	check("Every terrain normal normalized and upward",upward)
	check("Every ground vertex agrees with actor sampler",agreement)
	var topology:=true;var nonzero:=true
	for i in range(0,indices.size(),3):
		var a:=vertices[indices[i]];var b:=vertices[indices[i+1]];var c:=vertices[indices[i+2]]
		var cross:=(b-a).cross(c-a)
		if cross.y>=0:topology=false
		if cross.length_squared()<.00001:nonzero=false
	check("Every terrain face uses Godot clockwise winding",topology)
	check("No degenerate terrain triangles",nonzero)
	var interpolated:=true
	for i in range(0,indices.size(),1953):
		var a:=vertices[indices[i]];var b:=vertices[indices[i+1]];var c:=vertices[indices[i+2]]
		var p:Vector3=a*.22+b*.31+c*.47
		if absf(p.y-Surface.height_at(Vector2(p.x,p.z)))>.00015:interpolated=false
	check("Actor contact matches rendered triangle interiors",interpolated)
	var water:=Surface.water_mesh()
	check("Extended water is a bounded custom surface under 3000 triangles",water.get_faces().size()/3>2000 and water.get_faces().size()/3<3000)
	var edge_buried:=true;var water_faces:=true
	var wf:=water.get_faces()
	for v in wf:
		var q:=Vector2(v.x,v.z)
		if Surface.lake_distance(q)>.1 and Surface.height_at(q)<=Surface.WATER_Y+.10:edge_buried=false
	for i in range(0,wf.size(),3):
		if (wf[i+1]-wf[i]).cross(wf[i+2]-wf[i]).y>=-.000001:water_faces=false
	check("Every water mesh rim is buried under the actual bank",edge_buried)
	check("Water has no reversed or degenerate faces",water_faces)
	check("Lakebed below water",Surface.height_at(Surface.LAKE_CENTER)<Surface.WATER_Y-.5)
	check("Camp is not a circular mud patch",Surface.work_distance(Vector2(8,5))<0 and absf(Surface.height_at(Vector2(8,5)))<.02)
	check("Production bay is cleared land",Surface.work_distance(Vector2(-9,-9.5))<0 and Surface.lake_distance(Vector2(-9,-9.5))>.4)
	check("Bay to camp ground connection is continuous",Surface.work_distance(Vector2(-6.5,-7))<0)
	var sim:=Sim.new()
	var dry:=true;var smooth_routes:=true
	for r in sim.resources:
		if Surface.lake_distance(r.position)<.4:dry=false
	for p in [Vector2(0,.2),Vector2(-2.8,2.25),Vector2(-6.6,-4.8),Vector2(6.6,-4.8),Vector2(0,-10.7),Vector2(0,11.7),Sim.point(sim.contract.world.forestGate),Vector2(-12,-11)]:
		if Surface.lake_distance(p)<.4:dry=false
	check("Every original resource, station, gate and bear site stays dry",dry)
	for route in [[Vector2(0,6.2),Vector2(0,.2)],[Vector2(0,.2),Vector2(-6.5,-9)],[Vector2(0,.2),Sim.point(sim.contract.world.forestGate)],[Vector2(-6.5,-9),Vector2(-6.5,-11.3)]]:
		for i in range(51):
			var p:Vector2=route[0].lerp(route[1],float(i)/50.)
			var q:=p+Vector2(.05,0)
			if Surface.lake_distance(p)<.30 or absf(Surface.height_at(q)-Surface.height_at(p))>.08:smooth_routes=false
	check("Station and shore approach ground routes remain dry and traversable",smooth_routes)
	var projected:=true
	for z in range(-16,-11):
		for x in range(-14,-1):
			var p:=Vector2(x,z)
			var d:=Surface.land_position(p)
			if Surface.lake_distance(d)<.3199 or not d.is_finite() or absf(d.x)>14.2 or absf(d.y)>16.2:projected=false
	check("Shore projection stays dry AND within unchanged playable bounds",projected)
	check("Projection of dry land is identity",Surface.land_position(Vector2(0,6))==Vector2(0,6))
	sim.position=Surface.LAKE_CENTER;sim.inventory.wood=123
	var save:=sim.snapshot();var restored:=Sim.new()
	check("Legacy save on new lake restores without losing inventory",restored.restore(save) and restored.inventory.wood==123 and Surface.lake_distance(restored.position)>.319)
	sim.position=Vector2(-7.9,-11.3)
	for i in range(140):sim.step(.05,Vector2(0,-1),true)
	check("Continuous player movement cannot walk underwater",Surface.lake_distance(sim.position)>.319)
	sim.companions[0].position=Surface.LAKE_CENTER
	sim.step(.01,Vector2.ZERO)
	check("Companions use the same dry shoreline constraint",Surface.lake_distance(sim.companions[0].position)>.319)
	var game=Main.new();game.qa_mode=true;game.render_review=true;game.capture_directory="user://t02-unit";game.capture_frames=100;game.size=Vector2(1280,720)
	root.add_child(game);game.set_process(false);game.set_physics_process(false)
	check("Actual scene creates terrain and water",game.outpost_view.lake.mesh==water and game.outpost_view.terrain.mesh==mesh)
	check("Water uses custom opaque material",not game.outpost_view.lake_material.shader.code.contains("ALPHA ="))
	var t:float=game.sim.climate.seconds
	game.toggle_menu();game._physics_process(.1);game._process(.1)
	check("Water animation freezes on pause",game.outpost_view.lake_material.get_shader_parameter("sim_time")==t)
	game.toggle_menu();game._physics_process(.1);game._process(.1)
	check("Water animation resumes from game clock",game.outpost_view.lake_material.get_shader_parameter("sim_time")>t)
	check("All approved forest instances retained",game.reference_forest_evidence.instances==586)
	var seated:=true
	for placement in Forest.placements(Vector2(14.2,16.2)):
		for delta in [Vector2(.23,0),Vector2(-.23,0),Vector2(0,.23),Vector2(0,-.23)]:
			if Surface.height_at(placement.point)-.17*placement.scale>Surface.height_at(placement.point+delta*placement.scale):seated=false
	check("Approved T01 trees remain seated on new ground",seated)
	check("Native resolution is not reduced by terrain",game.scene_view.scaling_3d_scale==1)
	check("Existing character identities unchanged",game.actors.size()==4)
	game.outpost_audio.stop_all();await create_timer(.35).timeout;game.free();await process_frame
	print(JSON.stringify({"suite":"T02_terrain","checks":checks,"failures":failures,"passed":failures.is_empty(),"independent_critic":false,"physical_4k60_verified":false}))
	quit(0 if failures.is_empty() else 1)
