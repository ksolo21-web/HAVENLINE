extends SceneTree
const River=preload("res://scripts/river_geometry.gd")
const Surface=preload("res://scripts/outpost_surface.gd")
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
	var expected:Array=[Vector2(-31,-8.6),Vector2(-24,-7.2),Vector2(-17,-9),Vector2(-10,-6.8),Vector2(-3,-8.7),Vector2(4,-6.9),Vector2(11,-8.5),Vector2(19,-6.7),Vector2(25,-8.1),Vector2(31,-7.3)]
	check("Locked ten river anchors retained exactly",River.ANCHORS==expected)
	check("River version is persistent map-span v1",River.LAYOUT_VERSION=="river_v1_mapspan")
	var anchor_exact:=true;var c1:=true
	for i in range(expected.size()):
		var anchor:Vector2=expected[i];anchor_exact=anchor_exact and River.center_at_x(anchor.x).distance_to(anchor)<.00001
		if i>0 and i<expected.size()-1:c1=c1 and River.tangent_at_x(anchor.x-.001).dot(River.tangent_at_x(anchor.x+.001))>.9999
	check("Spline passes through every locked anchor",anchor_exact);check("Spline is C1-continuous through interior anchors",c1)
	var min_width:=999.0;var max_width:=0.0;var finite:=true;var current_crosses:=true
	for i in range(1241):
		var x:float=-31.0+float(i)*.05;var c:Vector2=River.center_at_x(x);var w:float=River.width_at_x(x)
		min_width=minf(min_width,w);max_width=maxf(max_width,w);finite=finite and c.is_finite() and is_finite(w)
	check("Full terrain river samples are finite",finite);check("Open-water width remains inside locked 3.2 to 4.6 range",min_width>=3.2 and max_width<=4.6)
	for side_value in [-14.2,14.2]:
		var side:float=float(side_value);var c:Vector2=River.center_at_x(side);var q:Dictionary=River.query(c);current_crosses=current_crosses and float(q.shore_distance)<-1.5
	check("Water continuously crosses both current east-west movement edges",current_crosses)
	var south_min:=999.0;var north_min:=999.0;var lane_dry:=true
	for i in range(285):
		var x:float=-14.2+float(i)*.1;var q:Dictionary=River.query(River.center_at_x(x));var center:Vector2=q.center;var n:Vector2=q.north_normal;var half_width:float=float(q.half_width)
		var south_crest:Vector2=center-n*(half_width+River.WET_EDGE+River.BANK_RUN);var north_build:Vector2=center+n*(half_width+River.WET_EDGE+River.BANK_RUN+River.SNOW_SHOULDER+River.BUILD_SETBACK)
		south_min=minf(south_min,south_crest.y-(-16.2));north_min=minf(north_min,16.2-north_build.y)
		var north_lane:Vector2=center+n*(half_width+River.WET_EDGE+River.BANK_RUN+River.SNOW_SHOULDER+.7);var south_lane:Vector2=center-n*(half_width+River.WET_EDGE+River.BANK_RUN+River.SNOW_SHOULDER+.7)
		lane_dry=lane_dry and River.shore_distance(north_lane)>1.4 and River.shore_distance(south_lane)>1.4
	check("Current south-bank traversable depth never below 4.5",south_min>=4.5);check("Current north unrestricted gross span never below 16.5",north_min>=16.5);check("Both bank route centerlines remain continuously dry",lane_dry)
	var work_safe:=true
	for z in range(-15,72,2):
		for x in range(-97,98,3):
			var p:=Vector2(float(x)/10.0,float(z)/10.0)
			if Surface.work_distance(p)<0:work_safe=work_safe and River.unrestricted_build_distance(p)>=0
	check("Core warm workfloor remains north of permanent-build setback",work_safe)
	var water:ArrayMesh=Surface.water_mesh();var wf:PackedVector3Array=water.get_faces();var water_ok:=water.get_surface_count()==1 and wf.size()/3>4000 and wf.size()/3<7000
	var min_x:=999.0;var max_x:=-999.0;var faces_ok:=true;var max_edge:=0.0
	for v in wf:min_x=minf(min_x,v.x);max_x=maxf(max_x,v.x)
	for i in range(0,wf.size(),3):
		var area:Vector3=(wf[i+1]-wf[i]).cross(wf[i+2]-wf[i]);faces_ok=faces_ok and area.y<-.000001
		for j in range(3):max_edge=maxf(max_edge,wf[i+j].distance_to(wf[i+(j+1)%3]))
	check("One coherent river water mesh stays within triangle budget",water_ok);check("River water mesh reaches both full terrain edges",min_x<=-31.0 and max_x>=31.0);check("River mesh faces are nondegenerate and consistently wound",faces_ok);check("River mesh uses short local triangles with no giant lake fan",max_edge<.65)
	var basin:=true;var bank_above:=true
	for row_value in River.plan_samples(.5):
		var row:Dictionary=row_value;var c:Vector2=row.center;var n:Vector2=row.north_normal;var h:float=float(row.width)*.5
		basin=basin and Surface.height_at(c)<Surface.WATER_Y-.35;bank_above=bank_above and Surface.height_at(c+n*(h+River.WET_EDGE+River.BANK_RUN))>Surface.WATER_Y+.08 and Surface.height_at(c-n*(h+River.WET_EDGE+River.BANK_RUN))>Surface.WATER_Y+.08
	check("Entire river channel is physically carved below water",basin);check("Both sculpted bank crests remain physically above water",bank_above)
	var sim=Sim.new();var dry_resources:=true
	for resource in sim.resources:dry_resources=dry_resources and River.shore_distance(resource.position)>=River.DEFAULT_DRY_MARGIN+.048 and Surface.height_at(resource.position)>Surface.WATER_Y+.05
	check("All runtime resource nodes migrate onto physically dry bank ground",dry_resources)
	var protected_structures:=true
	for key in ["leftTent","rightTent","northBarricade","southBarricade"]:protected_structures=protected_structures and River.unrestricted_build_distance(Sim.point(sim.contract.world[key]))>=-.001
	check("Permanent runtime structures clear the locked river build setback",protected_structures)
	var crossings_clear:=true
	for key in ["leftTent","rightTent","northBarricade","southBarricade","furnace","storage","campfire"]:crossings_clear=crossings_clear and not River.crossing_reserved(Sim.point(sim.contract.world[key]))
	check("Three future crossing reserves contain no permanent camp obstruction",crossings_clear)
	var source:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://data/reference-contract.json"));check("Historical source contract remains immutable",source.world.leftTent==[-6.6,0.0,-3.8] and source.world.forestGate==[0.0,0.0,-14.8])
	var migration_ok:=true;var side_ok:=true
	for side_value in [-1.0,1.0]:
		var side:float=float(side_value);var center:Vector2=River.center_at_x(2.0);var q:Dictionary=River.query(center);var wet:Vector2=Vector2(q.center)+Vector2(q.north_normal)*float(q.half_width)*.45*side
		sim=Sim.new();sim.position=wet;sim.inventory.wood=4321;sim.stored.stone=7654;var state:Dictionary=sim.snapshot();state.erase("river_layout_version")
		var restored=Sim.new();migration_ok=migration_ok and restored.restore(state) and restored.inventory.wood==4321 and restored.stored.stone==7654
		var rq:Dictionary=River.query(restored.position);side_ok=side_ok and float(rq.side)==side and float(rq.shore_distance)>=River.DEFAULT_DRY_MARGIN-.002 and Surface.height_at(restored.position)>Surface.WATER_Y+.05
	check("Lake-era wet saves migrate without losing inventory",migration_ok);check("Save migration preserves river side and recovers above water",side_ok)
	sim=Sim.new();sim.threats_enabled=false;sim.rescue_enabled=false;var q:Dictionary=River.query(River.center_at_x(0));sim.position=Vector2(q.center)+Vector2(q.north_normal)*(float(q.half_width)+.8)
	for _frame in range(360):sim.step(1.0/60.0,-Vector2(q.north_normal),true)
	var blocked:Dictionary=River.query(sim.position);check("Player sprint cannot tunnel through river or wet bank",float(blocked.side)>0 and float(blocked.shore_distance)>=River.DEFAULT_DRY_MARGIN-.002 and Surface.height_at(sim.position)>Surface.WATER_Y+.05)
	var game=Main.new();game.qa_mode=true;game.render_review=true;game.capture_directory="user://river-test";game.capture_frames=100;game.size=Vector2(1280,720);root.add_child(game);game.set_process(false);game.set_physics_process(false)
	check("Actual runtime water node is the map-spanning river",game.outpost_view.lake.name=="MapSpanningRiver" and game.outpost_view.lake.mesh==water);check("River shader remains opaque and lit",not game.outpost_view.lake_material.shader.code.contains("ALPHA") and not game.outpost_view.lake_material.shader.code.contains("unshaded"));check("Native render scale remains 1.0",game.scene_view.scaling_3d_scale==1.0);check("Approved forest instance count remains 586",game.reference_forest_evidence.instances==586)
	var flooded:=0
	for tree_value in Forest.placements(Vector2(14.2,16.2)):
		var tree:Dictionary=tree_value
		if River.shore_distance(tree.point)<=0.40:flooded+=1
	check("No approved T01 perimeter tree is flooded by the full-map river",flooded==0)
	game.outpost_audio.stop_all();await create_timer(.35).timeout;game.free();await process_frame
	print(JSON.stringify({"suite":"T02_mapspanning_river","checks":checks,"failures":failures,"passed":failures.is_empty(),"min_width":min_width,"max_width":max_width,"south_bank_min_depth":south_min,"north_bank_min_span":north_min,"water_triangles":wf.size()/3,"max_water_edge":max_edge,"flooded_t01_trees":flooded,"gameplay_dry_margin":River.DEFAULT_DRY_MARGIN,"physical_4k60_verified":false,"independent_critic":false}))
	quit(0 if failures.is_empty() else 1)
