extends SceneTree
# T02 user correction: the lake spans both east/west playable boundaries.
const Surface=preload("res://scripts/outpost_surface.gd")
const Sim=preload("res://scripts/outpost_simulation.gd")
const Main=preload("res://scripts/main.gd")
const Forest=preload("res://scripts/reference_forest.gd")
var checks: Array=[]
var failures: Array=[]
func check(name: String, result: bool):
	checks.append({"name":name,"passed":result})
	if not result: failures.append(name)
func _initialize(): call_deferred("run")
func run():
	var sim=Sim.new()
	var bounds: Vector2=Vector2(sim.contract.world.boundX,sim.contract.world.boundZ)
	check("Lake is centred east-west",Surface.LAKE_CENTER.x==0.0)
	check("Lake width exceeds the full playable east-west width",Surface.LAKE_HALF.x>bounds.x)
	check("East-west length is at least 2.9 times the prior lake",Surface.LAKE_HALF.x/5.2>=2.9)
	check("Existing water elevation and north-south centre preserved",Surface.WATER_Y==-.34 and absf(Surface.LAKE_CENTER.y+13.85)<.00001)
	var continuous:=true;var below:=true
	for i in range(569):
		var p:=Vector2(-bounds.x+float(i)*.05,Surface.LAKE_CENTER.y)
		continuous=continuous and Surface.lake_distance(p)<-.7
		below=below and Surface.height_at(p)<Surface.WATER_Y-.25
	check("Water uninterrupted across 569 samples from west to east boundary",continuous)
	check("Actual basin below water across entire east-west span",below)
	var dry:=true;var bounded:=true;var stable:=true;var same_x:=true
	var projections:=0
	for z in range(-162,-108):
		for x in range(-142,143):
			var p:=Vector2(x,z)*.1;var q:=Surface.land_position(p)
			projections+=1
			dry=dry and Surface.lake_distance(q)>.3199 and Surface.height_at(q)>Surface.WATER_Y+.18
			bounded=bounded and absf(q.x)<=bounds.x+.0001 and absf(q.y)<=bounds.y+.0001
			stable=stable and q.distance_to(Surface.land_position(q))<.0001
			same_x=same_x and absf(p.x-q.x)<.00001
	check("All 15390 wet/rim/north-strip positions recover to dry connected land",dry)
	check("Every recovery remains within playable bounds",bounded)
	check("Recovery is idempotent and does not drift saved positions",stable)
	check("Recovery preserves X rather than ejecting actors past map ends",same_x)
	var source=JSON.parse_string(FileAccess.get_file_as_string("res://data/reference-contract.json"))
	var original=source.duplicate(true);var custom=Sim.new(source,2)
	check("Historical source contract not edited or mutated in memory",source==original and source.world.forestGate==[0.0,0.0,-14.8])
	var gate: Vector2=Sim.point(custom.contract.world.forestGate)
	check("Existing forest approach resolved onto connected near shore",Surface.lake_distance(gate)>.49 and gate.y>Surface.LAKE_CENTER.y)
	check("No gameplay prices or unlock rules changed",custom.contract.openingLoopTuning==source.openingLoopTuning)
	var save_ok:=true
	for x in [-14.2,-12.,-6.,0.,6.,12.,14.2]:
		for z in [-16.2,-15.2,-13.85,-12.5]:
			sim.position=Vector2(x,z);sim.inventory.wood=4321;sim.stored.stone=7654
			var state=sim.snapshot();var restored=Sim.new()
			save_ok=save_ok and restored.restore(state) and restored.inventory.wood==4321 and restored.stored.stone==7654
			save_ok=save_ok and Surface.lake_distance(restored.position)>.319 and restored.position.y>Surface.LAKE_CENTER.y
	check("28 legacy wet/north-bank saves preserve inventory and return to connected shore",save_ok)
	var walking:=true
	sim=Sim.new();sim.threats_enabled=false;sim.rescue_enabled=false;sim.population.enabled_templates.clear()
	sim.position=Vector2(-13.5,-11.1)
	for target in [Vector2(13.5,-11.1),Vector2(-13.5,-11.1),gate]:
		var reached:=false
		for frame in range(3200):
			var delta: Vector2=target-sim.position
			if delta.length()<.1: reached=true;break
			sim.step(1./60.,delta.normalized()*minf(1.,delta.length()*2.),false)
			walking=walking and Surface.lake_distance(sim.position)>.319
		check("Real controls reach lakeside waypoint "+str(target),reached)
	check("Walking east-west and to the gate never crosses water",walking)
	var keep_dry:=true
	for x in [-14.,-7.,0.,7.,14.]:
		sim.position=Vector2(x,-11.3)
		for frame in range(240):
			sim.step(1./60.,Vector2.UP,true)
			keep_dry=keep_dry and Surface.lake_distance(sim.position)>.319 and sim.position.y>Surface.LAKE_CENTER.y
	check("Sprinting into all five lake sectors cannot tunnel through water",keep_dry)
	var trees_dry:=true
	for tree in Forest.placements(bounds):
		trees_dry=trees_dry and Surface.lake_distance(tree.point)>.4 and Surface.height_at(tree.point)>Surface.WATER_Y
	check("All 586 approved perimeter tree positions remain above water",trees_dry)
	var game=Main.new();game.qa_mode=true;game.render_review=true;game.capture_frames=100;game.capture_directory="user://lake-correction-test";game.size=Vector2(1280,720)
	root.add_child(game);game.set_process(false);game.set_physics_process(false)
	for material in [game.outpost_view.ground_material,game.outpost_view.lake_material]:
		check("Shader coast shares exact runtime lake centre and dimensions",material.get_shader_parameter("lake_center")==Surface.LAKE_CENTER and material.get_shader_parameter("lake_half")==Surface.LAKE_HALF)
	var faces: PackedVector3Array=game.outpost_view.lake.mesh.get_faces()
	var short_edges:=true
	for i in range(0,faces.size(),3):
		for j in range(3):
			short_edges=short_edges and faces[i+j].distance_to(faces[i+(j+1)%3])<.61
	check("Single water surface uses short coherent triangles under 3000",short_edges and faces.size()/3>2000 and faces.size()/3<3000 and game.outpost_view.lake.mesh.get_surface_count()==1)
	check("Approved tree count and native render scale unchanged",game.reference_forest_evidence.instances==586 and game.scene_view.scaling_3d_scale==1.)
	game.outpost_audio.stop_all();await create_timer(.35).timeout;game.free();await process_frame
	print(JSON.stringify({"suite":"T02_east_west_lake","checks":checks,"failures":failures,"passed":failures.is_empty(),"projection_samples":projections,"physical_4k60_verified":false,"independent_critic":false}))
	quit(0 if failures.is_empty() else 1)
