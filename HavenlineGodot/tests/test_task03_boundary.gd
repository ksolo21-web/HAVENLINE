extends SceneTree
const Boundary=preload("res://scripts/camp_boundary.gd")
const River=preload("res://scripts/river_geometry.gd")
const Surface=preload("res://scripts/outpost_surface.gd")
const Sim=preload("res://scripts/outpost_simulation.gd")
const Main=preload("res://scripts/main.gd")
const Forest=preload("res://scripts/reference_forest.gd")
var checks:Array=[]
var failures:Array=[]
func check(name:String,value:bool):
	checks.append({"name":name,"passed":value})
	if not value:failures.append(name)
func _initialize():call_deferred("run")
func run_to(sim,target:Vector2,sprint:=false,frames:=1200)->bool:
	for _i in range(frames):
		var delta:Vector2=target-sim.position
		if delta.length()<.12:return true
		sim.step(1./60.,delta.normalized()*minf(1.0,delta.length()*2.0),sprint)
	return sim.position.distance_to(target)<.12
func segment_distance(p:Vector2,a:Vector2,b:Vector2)->float:
	var d:=b-a
	if d.length_squared()<.000001:return p.distance_to(a)
	return p.distance_to(a+d*clampf((p-a).dot(d)/d.length_squared(),0.0,1.0))
func run():
	var evidence:=Boundary.evidence();var gates:=Boundary.gate_specs();var panels:=Boundary.panel_specs()
	check("Locked side and north perimeter constants",Boundary.SIDE_X==12.4 and Boundary.NORTH_Z==8.8)
	check("Exactly six real gates",gates.size()==6)
	var gate_ids:=gates.map(func(g):return g.id)
	check("North west east and three river gates all present",["north-main","west-work","east-work","river--9.0","river-1.5","river-10.0"].all(func(id):return id in gate_ids))
	var widths_ok:=true
	for gate in gates:
		var minimum:=3.6 if gate.id=="north-main" else 3.4
		widths_ok=widths_ok and float(gate.width)>=minimum-.001
	check("Every gate meets its locked physical opening width",widths_ok)
	check("Authored fence is substantial and collision derives from same panel set",panels.size()>24 and evidence.panel_count==panels.size())
	var south_safe:=true;var reserved_clear:=true
	for i in range(249):
		var x:=-12.4+float(i)*.1
		south_safe=south_safe and River.shore_distance(Boundary.south_point(x))>=Boundary.SOUTH_FENCE_MARGIN-.002
	for panel in panels:
		if not String(panel.boundary).begins_with("south-"):continue
		for reserve in Boundary.RIVER_GATES:
			var lo:=float(reserve)-1.5;var hi:=float(reserve)+1.5
			var min_x:=minf(panel.a.x,panel.b.x);var max_x:=maxf(panel.a.x,panel.b.x)
			if max_x>lo+.001 and min_x<hi-.001:reserved_clear=false
	check("Curved south fence stays outside Task 2 permanent-build setback",south_safe)
	check("All three future crossing reserves remain free of permanent fence panels",reserved_clear)
	var lanes_dry:=true;var lanes_clear:=true;var lane_samples:=0
	for lane in Boundary.lane_polylines():
		var points:Array=lane.points
		for j in range(points.size()-1):
			var a:Vector2=points[j];var b:Vector2=points[j+1];var n:=maxi(1,ceili(a.distance_to(b)/.2))
			for k in range(n+1):
				var p:=a.lerp(b,float(k)/float(n));lane_samples+=1
				lanes_dry=lanes_dry and River.shore_distance(p)>=River.DEFAULT_DRY_MARGIN-.025
				for panel in panels:lanes_clear=lanes_clear and segment_distance(p,panel.a,panel.b)>=Boundary.COLLISION_RADIUS-.03
	check("All required work lanes stay on traversable dry terrain",lanes_dry)
	check("Work-lane centre lines do not run through visible fence collision",lanes_clear)
	var lane_ids:=Boundary.lane_polylines().map(func(row):return row.id)
	check("Lane network contains central cross shelter bank river connectors and three threshold aprons",Boundary.lane_polylines().size()==10 and lane_samples>275 and ["river-apron-west","river-apron-centre","river-apron-east"].all(func(id):return id in lane_ids))
	var sim:=Sim.new();sim.threats_enabled=false;sim.rescue_enabled=false;sim.population.enabled_templates.clear()
	var gate_walks:=true;var gate_sprints:=true
	for gate in gates:
		var center:Vector2=gate.center;var inward:Vector2=(Boundary.CAMP_CENTER-center).normalized()
		var inside:=center+inward*1.15;var outside:=center-inward*1.15
		if gate.kind=="river":outside=Boundary.bank_lane_point(float(gate.reserve_x))
		for sprint in [false,true]:
			sim.position=inside;sim.velocity=Vector2.ZERO
			var out_ok:=run_to(sim,outside,sprint,900)
			var back_ok:=run_to(sim,inside,sprint,900)
			if sprint:gate_sprints=gate_sprints and out_ok and back_ok
			else:gate_walks=gate_walks and out_ok and back_ok
	check("Player walks through all six visible gates in both directions",gate_walks)
	check("Player sprints through all six visible gates in both directions",gate_sprints)
	var blocked:=true;var tested_boundaries:Dictionary={}
	for panel in panels:
		var id:=String(panel.boundary)
		var family:="south" if id.begins_with("south-") else ("north" if id.begins_with("north-") else ("west" if id.begins_with("west-") else "east"))
		if tested_boundaries.has(family):continue
		tested_boundaries[family]=true
		var a:Vector2=panel.a;var b:Vector2=panel.b;var mid:Vector2=panel.mid;var tangent:Vector2=panel.tangent;var normal:=Vector2(-tangent.y,tangent.x)
		if (Boundary.CAMP_CENTER-mid).dot(normal)<0:normal=-normal
		var inside:=mid+normal*.9;var target:=mid-normal*1.1
		sim.position=inside;sim.velocity=Vector2.ZERO
		run_to(sim,target,true,240)
		blocked=blocked and (sim.position-mid).dot(normal)>0 and segment_distance(sim.position,a,b)>=Boundary.COLLISION_RADIUS-.02
	check("Visible north south east and west fence sections block sprint tunnelling",blocked and tested_boundaries.size()==4)
	var source=JSON.parse_string(FileAccess.get_file_as_string("res://data/reference-contract.json"));var historical=source.duplicate(true)
	var migrated:=Sim.new(source,1)
	check("Reference contract object and economy remain immutable",source==historical and migrated.tuning==source.openingLoopTuning)
	check("Shelters migrate onto locked lane endpoints",Sim.point(migrated.contract.world.leftTent).distance_to(Boundary.SHELTER_WEST)<.001 and Sim.point(migrated.contract.world.rightTent).distance_to(Boundary.SHELTER_EAST)<.001)
	migrated.position=panels[0].mid;migrated.inventory.wood=1234;migrated.stored.stone=567
	var save:=migrated.snapshot();var restored:=Sim.new()
	check("Save restore pushes player off visible fence without losing inventory",restored.restore(save) and restored.inventory.wood==1234 and restored.stored.stone==567 and segment_distance(restored.position,panels[0].a,panels[0].b)>=Boundary.COLLISION_RADIUS-.02)
	check("Task 2 river identity remains exact",River.LAYOUT_VERSION=="river_v1_mapspan" and River.ANCHORS[0]==Vector2(-31,-8.6) and River.ANCHORS[-1]==Vector2(31,-7.3))
	var trees_dry:=true;var trees_clear:=true
	for tree in Forest.placements(Vector2(14.2,16.2)):
		trees_dry=trees_dry and River.shore_distance(tree.point)>River.DEFAULT_DRY_MARGIN
		for panel in panels:trees_clear=trees_clear and segment_distance(tree.point,panel.a,panel.b)>1.0
	check("All 586 approved T01 forest instances remain dry",trees_dry and Forest.placements(Vector2(14.2,16.2)).size()==586)
	check("Static camp boundary does not collide with approved perimeter forest",trees_clear)
	var game=Main.new();game.qa_mode=true;game.render_review=true;game.capture_frames=100;game.capture_directory="user://t03-unit";game.size=Vector2(1280,720)
	root.add_child(game);game.set_process(false);game.set_physics_process(false)
	check("Live scene instantiates Task 3 boundary view",is_instance_valid(game.camp_boundary_view))
	var desc:Dictionary=game.camp_boundary_view.descriptor
	check("Fence visuals and collision use same authoritative panel count",desc.collision_panel_instances==panels.size() and desc.visual_collision_share_panel_authority is bool and desc.visual_collision_share_panel_authority)
	check("Six gates have twelve lantern posts and twelve open timber leaves",desc.gate_count==6 and desc.gate_post_instances==12 and desc.open_gate_leaf_instances==12)
	check("Gate leaves use polished general and river-specific opening geometry",is_equal_approx(Boundary.GATE_LEAF_LENGTH,1.35) and is_equal_approx(Boundary.GATE_OPEN_ANGLE,1.18) and is_equal_approx(Boundary.RIVER_GATE_LEAF_LENGTH,1.85) and is_equal_approx(Boundary.RIVER_GATE_OPEN_ANGLE,1.53) and is_equal_approx(Boundary.RIVER_LANE_HALF,1.55))
	var river_authority_ok:=Boundary.river_gate_contracts().size()==3
	var evidence_ids:Dictionary={}
	for contract in Boundary.river_gate_contracts():
		var route:Array=contract.route_points
		river_authority_ok=river_authority_ok and String(contract.authority_id)==Boundary.GATE_AUTHORITY_ID
		river_authority_ok=river_authority_ok and float(contract.visual_clear_width)>=Boundary.RIVER_VISUAL_CLEARANCE_MIN
		river_authority_ok=river_authority_ok and float(contract.width)>=3.4-.001 and float(contract.collision_reserved_width)==3.0
		river_authority_ok=river_authority_ok and route.size()==3 and Vector2(route[1]).distance_to(Vector2(contract.center))<.001
		river_authority_ok=river_authority_ok and Vector2(route[0]).distance_to(Boundary.bank_lane_point(float(contract.reserve_x)))<.001
		for kind in Boundary.RIVER_EVIDENCE_KINDS:
			var eid:=String(contract.evidence_ids[kind]);evidence_ids[eid]=true
	check("River gates share authoritative geometry for visual clearance routes and evidence",river_authority_ok and evidence_ids.size()==12 and evidence.required_river_gate_evidence_ids.size()==12 and evidence.all_river_visual_clearance_pass)
	check("Authored fence roots are deliberately sunk into terrain",is_equal_approx(float(desc.fence_root_sink),.08))
	check("Fence joins open leaves and river posts preserve strong terrain contact and threshold readability without changing collision",is_equal_approx(float(desc.visual_join_overlap),.10) and is_equal_approx(float(desc.visual_corner_join_overlap),.28) and is_equal_approx(float(desc.gate_leaf_root_sink),.30) and is_equal_approx(float(desc.gate_leaf_hinge_sink),.08) and int(desc.terrain_seat_samples)==7 and desc.terrain_crown_applied_to_gate_leaves_only and is_equal_approx(float(desc.river_gate_post_scale),1.35))
	var zero_progress_hidden:=true
	for side in game.sim.defenses:
		zero_progress_hidden=zero_progress_hidden and not game.defense_visuals[side].visible
	check("Zero-progress defense barricades do not appear as collapsed fence debris",zero_progress_hidden)
	check("No primitive Task 3 fence geometry is created",desc.primitive_fence_meshes_created is bool and not desc.primitive_fence_meshes_created and desc.draw_batches==2)
	check("Native render scale remains exactly one",game.scene_view.scaling_3d_scale==1.0)
	check("Approved river still reports mapspan layout",game.outpost_view.evidence(game.sim).river_layout_version==River.LAYOUT_VERSION)
	game.outpost_audio.stop_all();await create_timer(.35).timeout;game.free();await process_frame
	print(JSON.stringify({"suite":"T03_boundary_and_lanes","checks":checks,"failures":failures,"passed":failures.is_empty(),"lane_samples":lane_samples,"panel_count":panels.size(),"gate_count":gates.size(),"independent_critic":false,"physical4k60_verified":false}))
	quit(0 if failures.is_empty() else 1)
