extends SceneTree
const Surface=preload("res://scripts/outpost_surface.gd")
const River=preload("res://scripts/river_geometry.gd")
const Main=preload("res://scripts/main.gd")
const Sim=preload("res://scripts/outpost_simulation.gd")
const Forest=preload("res://scripts/reference_forest.gd")
var checks:Array=[];var failures:Array=[]
func check(name:String,passed:bool):checks.append({"name":name,"passed":passed});failures.append(name) if not passed else null
func _initialize():call_deferred("run")
func run():
	var mesh:ArrayMesh=Surface.mesh();var arrays:Array=mesh.surface_get_arrays(0)
	var vertices:PackedVector3Array=arrays[Mesh.ARRAY_VERTEX];var normals:PackedVector3Array=arrays[Mesh.ARRAY_NORMAL];var indices:PackedInt32Array=arrays[Mesh.ARRAY_INDEX]
	check("Single coherent indexed terrain surface",mesh.get_surface_count()==1 and indices.size()>vertices.size())
	check("Terrain budget below 125000 triangles",indices.size()/3<125000)
	check("Cached terrain mesh shared",Surface.mesh()==mesh)
	var finite:=true;var upward:=true;var agreement:=true
	for i in range(vertices.size()):
		finite=finite and vertices[i].is_finite() and normals[i].is_finite()
		upward=upward and normals[i].y>0 and absf(normals[i].length()-1.0)<.002
		agreement=agreement and absf(vertices[i].y-Surface.height_at(Vector2(vertices[i].x,vertices[i].z)))<.0001
	check("All terrain vertices and normals finite",finite);check("Every terrain normal normalized and upward",upward);check("Terrain vertices agree with actor sampler",agreement)
	var topology:=true;var nonzero:=true
	for i in range(0,indices.size(),3):
		var a:Vector3=vertices[indices[i]];var b:Vector3=vertices[indices[i+1]];var c:Vector3=vertices[indices[i+2]];var cross:Vector3=(b-a).cross(c-a)
		topology=topology and cross.y<0;nonzero=nonzero and cross.length_squared()>.00001
	check("Every terrain face uses Godot clockwise winding",topology);check("No degenerate terrain triangles",nonzero)
	var water:ArrayMesh=Surface.water_mesh();var wf:PackedVector3Array=water.get_faces()
	check("River water is one coherent bounded mesh",water.get_surface_count()==1 and wf.size()/3>5000 and wf.size()/3<7000)
	var water_faces:=true;var short_edges:=true
	for i in range(0,wf.size(),3):
		water_faces=water_faces and (wf[i+1]-wf[i]).cross(wf[i+2]-wf[i]).y<-.000001
		for j in range(3):short_edges=short_edges and wf[i+j].distance_to(wf[i+(j+1)%3])<.65
	check("River water has consistent nondegenerate faces",water_faces);check("River surface uses local triangles rather than a stretched lake fan",short_edges)
	var cross_sections:=true
	for row_value in River.plan_samples(.5):
		var row:Dictionary=row_value;var c:Vector2=row.center;var n:Vector2=row.north_normal;var h:=float(row.width)*.5
		cross_sections=cross_sections and Surface.height_at(c)<Surface.WATER_Y-.35
		cross_sections=cross_sections and Surface.height_at(c+n*(h+River.WET_EDGE+River.BANK_RUN))>Surface.WATER_Y+.08
		cross_sections=cross_sections and Surface.height_at(c-n*(h+River.WET_EDGE+River.BANK_RUN))>Surface.WATER_Y+.08
	check("Every sampled river cross-section has carved bed and raised banks",cross_sections)
	var work_safe:=true
	for z in range(-15,72,2):
		for x in range(-97,98,3):
			var p:=Vector2(float(x)/10.0,float(z)/10.0)
			if Surface.work_distance(p)<0:work_safe=work_safe and River.unrestricted_build_distance(p)>=0
	check("Warm production floor stays on the north buildable bank",work_safe)
	var sim=Sim.new();var dry:=true
	for resource in sim.resources:dry=dry and River.shore_distance(resource.position)>=.549
	for key in ["leftTent","rightTent","northBarricade","southBarricade","forestGate"]:dry=dry and River.shore_distance(Sim.point(sim.contract.world[key]))>=River.DEFAULT_DRY_MARGIN-.001
	check("Runtime resources, shelters, defenses and gate remain dry",dry)
	var centre:Vector2=River.center_at_x(0.0);sim.position=centre;sim.inventory.wood=123;sim.stored.stone=456
	var state:Dictionary=sim.snapshot();state.erase("river_layout_version");var restored=Sim.new()
	check("Legacy wet save restores without losing materials",restored.restore(state) and restored.inventory.wood==123 and restored.stored.stone==456 and River.shore_distance(restored.position)>=River.DEFAULT_DRY_MARGIN-.001)
	sim.companions[0].position=centre;sim.step(.01,Vector2.ZERO);check("Companions use the same dry river constraint",River.shore_distance(sim.companions[0].position)>=River.DEFAULT_DRY_MARGIN-.001)
	var game=Main.new();game.qa_mode=true;game.render_review=true;game.capture_directory="user://t02-river-unit";game.capture_frames=100;game.size=Vector2(1280,720)
	root.add_child(game);game.set_process(false);game.set_physics_process(false)
	check("Actual scene creates terrain and map-spanning river",game.outpost_view.lake.name=="MapSpanningRiver" and game.outpost_view.lake.mesh==water and game.outpost_view.terrain.mesh==mesh)
	check("River uses custom opaque lit material",not game.outpost_view.lake_material.shader.code.contains("ALPHA") and not game.outpost_view.lake_material.shader.code.contains("unshaded"))
	var t:float=game.sim.climate.seconds;game.toggle_menu();game._physics_process(.1);game._process(.1)
	check("River animation freezes on pause",game.outpost_view.lake_material.get_shader_parameter("sim_time")==t)
	game.toggle_menu();game._physics_process(.1);game._process(.1);check("River animation resumes from simulation clock",game.outpost_view.lake_material.get_shader_parameter("sim_time")>t)
	check("All approved forest instances retained",game.reference_forest_evidence.instances==586)
	var seated:=true
	for placement_value in Forest.placements(Vector2(14.2,16.2)):
		var placement:Dictionary=placement_value
		for delta in [Vector2(.23,0),Vector2(-.23,0),Vector2(0,.23),Vector2(0,-.23)]:
			if Surface.height_at(placement.point)-.17*placement.scale>Surface.height_at(placement.point+delta*placement.scale):seated=false
	check("Approved T01 trees remain seated on river terrain",seated)
	check("Native render scale remains exactly 1.0",game.scene_view.scaling_3d_scale==1.0);check("Existing four character identities remain loaded",game.actors.size()==4)
	game.outpost_audio.stop_all();await create_timer(.35).timeout;game.free();await process_frame
	print(JSON.stringify({"suite":"T02_river_terrain","checks":checks,"failures":failures,"passed":failures.is_empty(),"terrain_triangles":indices.size()/3,"water_triangles":wf.size()/3,"independent_critic":false,"physical_4k60_verified":false}))
	quit(0 if failures.is_empty() else 1)
