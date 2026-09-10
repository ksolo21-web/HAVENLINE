extends SceneTree
const Surface=preload("res://scripts/outpost_surface.gd")
const Scenery=preload("res://scripts/scenery_batch.gd")
const Sim=preload("res://scripts/outpost_simulation.gd")
var checks: Array=[]
var failures: Array=[]
func check(name:String,passed:bool):
	checks.append({"name":name,"passed":passed})
	if not passed:failures.append(name)
func _initialize():call_deferred("run")
func run():
	var dry:=true;var bounded:=true;var stable:=true;var bank_clear:=true
	for y in range(-162, -114):
		for x in range(-142,-12):
			var p:=Vector2(x,y)*.1;var q:=Surface.land_position(p)
			dry=dry and Surface.lake_distance(q)>=.3199
			bounded=bounded and absf(q.x)<=14.2001 and absf(q.y)<=16.2001
			stable=stable and q.distance_to(Surface.land_position(q))<.0001
			bank_clear=bank_clear and Surface.height_at(q)>Surface.WATER_Y+.18
	check("6240 basin and rim positions project onto dry ground",dry)
	check("6240 projections stay inside the existing world bounds",bounded)
	check("Shore relocation is idempotent and cannot drift saves",stable)
	check("Every sampled projected point is above water with clearance",bank_clear)
	# Vector2 is float32; 0.0001 world units is the comparison tolerance at
	# original bound coordinates, not an expansion of the navigation boundary.
	var paths: Array=[];var unobstructed:=true;var route_length:=0.0;var avoids_buildings:=true
	var station_bounds: Array[AABB]=[]
	for record in [["shelter",Vector3(-6.6,0,-4.8),-.12],["shelter",Vector3(6.6,0,-4.8),.12],["furnace",Vector3(0,0,.2),0.0],["storage",Vector3(-2.8,0,2.25),0.0]]:
		var scene=load("res://assets/environment_v2/%s.glb"%record[0])
		var box: AABB=Transform3D(Basis(Vector3.UP,record[2]),record[1])*Scenery.compile(scene).get_aabb()
		station_bounds.append(box.grow(.25))
	# The exact connected workfloor route used by the capture camera, tested with
	# actual velocity/acceleration simulation rather than teleporting a marker.
	var sim:=Sim.new();sim.threats_enabled=false;sim.rescue_enabled=false
	sim.population.enabled_templates.clear();sim.position=Vector2(0,6.2)
	for target in [Vector2(2.2,3),Vector2(2.2,-2.2),Vector2(-2.2,-2.2),Vector2(-2.2,-6.8),Vector2(-2.2,-9),Vector2(-6.5,-9),Vector2(-6.5,-11.3)]:
		var reached:=false
		for frame in range(900):
			var delta: Vector2=target-sim.position
			if delta.length()<.09:reached=true;break
			var old:Vector2=sim.position
			sim.step(1.0/60.0,delta.normalized()*minf(1.0,delta.length()*2.),false)
			route_length+=sim.position.distance_to(old)
			unobstructed=unobstructed and Surface.lake_distance(sim.position)>.319
			for box in station_bounds:
				if sim.position.x>box.position.x and sim.position.x<box.end.x and sim.position.y>box.position.z and sim.position.y<box.end.z:avoids_buildings=false
		paths.append({"target":[target.x,target.y],"reached":reached,"position":[sim.position.x,sim.position.y]})
		check("Existing controls reach dry waypoint "+str(target),reached)
	check("The full workfloor-to-shore walk never crosses water",unobstructed)
	check("Ground route avoids all actual cabin/furnace/storage bounds plus clearance",avoids_buildings)
	var all_saved:=true
	for offset in [Vector2.ZERO,Vector2(4,0),Vector2(-4,0),Vector2(0,1.1),Vector2(0,-1.1)]:
		sim.position=Surface.LAKE_CENTER+offset;sim.inventory.wood=321;sim.stored.stone=765
		var a:=sim.snapshot();var restored:=Sim.new()
		all_saved=all_saved and restored.restore(a) and restored.inventory.wood==321 and restored.stored.stone==765 and Surface.lake_distance(restored.position)>.319
	check("Old basin saves retain carried and stored materials in all directions",all_saved)
	var ground=FileAccess.get_file_as_string("res://shaders/outpost_snow.gdshader")
	check("Ground edge coverage uses screen derivatives",ground.contains("fwidth(d)"))
	var water=FileAccess.get_file_as_string("res://shaders/lakeshore_water.gdshader")
	check("No full-screen refraction, backbuffer or transparent water pass",not water.contains("hint_screen_texture") and not water.contains("ALPHA="))
	print(JSON.stringify({"suite":"T02_surface_stress","checks":checks,"failures":failures,"passed":failures.is_empty(),"route_length":route_length,"waypoints":paths,"physical_4k60_verified":false,"independent_critic":false}))
	quit(0 if failures.is_empty() else 1)
