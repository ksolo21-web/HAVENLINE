extends SceneTree
# Historical filename retained so old CI references keep running. The previous
# east-west lake requirement is superseded by river_v1_mapspan.
const Surface=preload("res://scripts/outpost_surface.gd")
const River=preload("res://scripts/river_geometry.gd")
const Sim=preload("res://scripts/outpost_simulation.gd")
const Main=preload("res://scripts/main.gd")
const Forest=preload("res://scripts/reference_forest.gd")
var checks:Array=[]
var failures:Array=[]
func check(name:String,passed:bool):
	checks.append({"name":name,"passed":passed})
	if not passed:failures.append(name)
func _initialize():call_deferred("run")
func run():
	check("Historical test now targets the map-spanning river contract",River.LAYOUT_VERSION=="river_v1_mapspan")
	var alias_ok:=true;var span_ok:=true
	for i in range(125):
		var x:float=-31.0+float(i)*.5;var c:Vector2=River.center_at_x(x)
		alias_ok=alias_ok and absf(Surface.lake_distance(c)-Surface.river_distance(c))<.000001
		span_ok=span_ok and River.shore_distance(c)<-1.55
	check("Legacy lake_distance API is a pure river-distance compatibility alias",alias_ok)
	check("New water remains continuous across the full 62-unit terrain",span_ok)
	var source:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://data/reference-contract.json"));var untouched:=source.duplicate(true);var sim=Sim.new(source,2)
	check("Historical source contract stays byte-semantically unchanged",source==untouched and source.world.forestGate==[0.0,0.0,-14.8])
	check("Historical prices and opening progression remain unchanged",sim.contract.openingLoopTuning==source.openingLoopTuning)
	var migrated:=true;var cases:=0
	for x_value in [-14.0,-9.0,-3.0,0.0,1.5,6.0,10.0,14.0]:
		var x:float=float(x_value);var q:Dictionary=River.query(River.center_at_x(x))
		for side_value in [-1.0,1.0]:
			var side:float=float(side_value);sim=Sim.new();sim.position=Vector2(q.center)+Vector2(q.north_normal)*float(q.half_width)*.25*side
			sim.inventory.wood=4321+cases;sim.stored.stone=7654+cases
			var old_state:Dictionary=sim.snapshot();old_state.erase("river_layout_version");var restored=Sim.new();cases+=1
			migrated=migrated and restored.restore(old_state) and restored.inventory.wood==4321+cases-1 and restored.stored.stone==7654+cases-1
			var rq:Dictionary=River.query(restored.position);migrated=migrated and float(rq.side)==side and float(rq.shore_distance)>=River.DEFAULT_DRY_MARGIN-.002 and Surface.height_at(restored.position)>Surface.WATER_Y+.05
	check("Lake-era saves on either future bank migrate without inventory loss and above water",migrated)
	var trees_dry:=true
	for tree_value in Forest.placements(Vector2(14.2,16.2)):
		var tree:Dictionary=tree_value;trees_dry=trees_dry and River.shore_distance(tree.point)>.4 and Surface.height_at(tree.point)>Surface.WATER_Y
	check("All 586 approved perimeter trees remain above river water",trees_dry)
	var game=Main.new();game.qa_mode=true;game.render_review=true;game.capture_frames=100;game.capture_directory="user://river-compatibility-test";game.size=Vector2(1280,720)
	root.add_child(game);game.set_process(false);game.set_physics_process(false)
	check("Runtime water node identifies the river rather than a lake",game.outpost_view.lake.name=="MapSpanningRiver")
	check("Water shader no longer contains fixed lake centre/half uniforms",not game.outpost_view.lake_material.shader.code.contains("lake_center") and not game.outpost_view.lake_material.shader.code.contains("lake_half"))
	var faces:PackedVector3Array=game.outpost_view.lake.mesh.get_faces();var short_edges:=true
	for i in range(0,faces.size(),3):
		for j in range(3):short_edges=short_edges and faces[i+j].distance_to(faces[i+(j+1)%3])<.65
	check("River is a single local-triangle surface, not the former stretched lake",short_edges and faces.size()/3>5000 and faces.size()/3<7000 and game.outpost_view.lake.mesh.get_surface_count()==1)
	check("Approved tree count and native render scale stay unchanged",game.reference_forest_evidence.instances==586 and game.scene_view.scaling_3d_scale==1.0)
	game.outpost_audio.stop_all();await create_timer(.35).timeout;game.free();await process_frame
	print(JSON.stringify({"suite":"T02_lake_era_to_river_compatibility","checks":checks,"failures":failures,"passed":failures.is_empty(),"legacy_cases":cases,"gameplay_dry_margin":River.DEFAULT_DRY_MARGIN,"physical_4k60_verified":false,"independent_critic":false}))
	quit(0 if failures.is_empty() else 1)
