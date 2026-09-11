extends SceneTree
const Surface=preload("res://scripts/outpost_surface.gd")
const River=preload("res://scripts/river_geometry.gd")
const Sim=preload("res://scripts/outpost_simulation.gd")
var checks:Array=[]
var failures:Array=[]
func check(name:String,passed:bool):
	checks.append({"name":name,"passed":passed})
	if not passed:failures.append(name)
func _initialize():call_deferred("run")
func _settle(sim,p:Vector2,margin:float)->Vector2:
	return sim._bounded_dry(p,margin)
func run():
	var projection_sim=Sim.new()
	var dry:=true;var bounded:=true;var stable:=true;var above:=true;var samples:=0
	for zi in range(-162,163,2):
		for xi in range(-142,143,2):
			var p:=Vector2(float(xi),float(zi))*.1
			if River.shore_distance(p)>1.2:continue
			var q:=_settle(projection_sim,p,River.DEFAULT_DRY_MARGIN);var r:=_settle(projection_sim,q,River.DEFAULT_DRY_MARGIN);samples+=1
			dry=dry and River.shore_distance(q)>=River.DEFAULT_DRY_MARGIN-.002
			bounded=bounded and absf(q.x)<=14.2001 and absf(q.y)<=16.2001
			stable=stable and q.distance_to(r)<.002
			above=above and Surface.height_at(q)>Surface.WATER_Y+.05
	check("All sampled wet/bank positions settle onto dry river land",dry)
	check("All projected current-map positions remain inside movement bounds",bounded)
	check("Repeated bounded river projection is stable",stable)
	check("Recovered positions stand physically above river water",above)
	var lane_points:Array[Vector2]=[];var lanes_dry:=true
	for i in range(143):
		var x:float=-14.2+float(i)*.2;var q:Dictionary=River.query(River.center_at_x(x));var n:Vector2=q.north_normal
		var north:Vector2=Vector2(q.center)+n*(float(q.half_width)+River.WET_EDGE+River.BANK_RUN+River.SNOW_SHOULDER+.75)
		var south:Vector2=Vector2(q.center)-n*(float(q.half_width)+River.WET_EDGE+River.BANK_RUN+River.SNOW_SHOULDER+.75)
		lane_points.append(north);lane_points.append(south);lanes_dry=lanes_dry and River.shore_distance(north)>1.4 and River.shore_distance(south)>1.4
	check("North and south along-bank lane samples are continuously dry",lanes_dry)
	var sim=Sim.new();sim.threats_enabled=false;sim.rescue_enabled=false;sim.population.enabled_templates.clear()
	var movement_safe:=true
	for north in [true,false]:
		var q0:Dictionary=River.query(River.center_at_x(-13.5));var sign:=1.0 if north else -1.0
		sim.position=Vector2(q0.center)+Vector2(q0.north_normal)*(float(q0.half_width)+2.25)*sign
		for xi in range(-12,13,2):
			var q:Dictionary=River.query(River.center_at_x(float(xi)));var target:Vector2=Vector2(q.center)+Vector2(q.north_normal)*(float(q.half_width)+2.25)*sign
			var reached:=false
			for _frame in range(900):
				var delta:Vector2=target-sim.position
				if delta.length()<.12:reached=true;break
				sim.step(1.0/60.0,delta.normalized()*minf(1.0,delta.length()*2.0),false)
				movement_safe=movement_safe and River.shore_distance(sim.position)>=River.DEFAULT_DRY_MARGIN-.002 and Surface.height_at(sim.position)>Surface.WATER_Y+.05
			check(("North" if north else "South")+" bank route reaches x="+str(xi),reached)
	check("Real movement along both banks never enters river or submerged slope",movement_safe)
	var legacy_ok:=true;var legacy_cases:=0
	for x_value in [-14.0,-10.0,-6.0,-3.0,0.0,1.5,5.0,10.0,14.0]:
		var x:float=float(x_value);var q:Dictionary=River.query(River.center_at_x(x))
		for side_value in [-1.0,1.0]:
			var side:float=float(side_value);sim=Sim.new();sim.position=Vector2(q.center)+Vector2(q.north_normal)*float(q.half_width)*.35*side
			sim.inventory.wood=10000+legacy_cases;sim.stored.stone=20000+legacy_cases
			var state:Dictionary=sim.snapshot();state.erase("river_layout_version");var restored=Sim.new();legacy_cases+=1
			legacy_ok=legacy_ok and restored.restore(state) and restored.inventory.wood==10000+legacy_cases-1 and restored.stored.stone==20000+legacy_cases-1
			var rq:Dictionary=River.query(restored.position);legacy_ok=legacy_ok and float(rq.side)==side and float(rq.shore_distance)>=River.DEFAULT_DRY_MARGIN-.002 and Surface.height_at(restored.position)>Surface.WATER_Y+.05
	check("Legacy wet saves across both banks preserve state/side and recover above water",legacy_ok)
	var ground:=FileAccess.get_file_as_string("res://shaders/outpost_snow.gdshader");var water:=FileAccess.get_file_as_string("res://shaders/lakeshore_water.gdshader")
	check("Ground edge coverage still uses derivative antialiasing",ground.contains("fwidth(d)"))
	check("Ground shader reads authored river distance from terrain vertices",ground.contains("authored_distance=COLOR.rg*8.-4."))
	check("River has no refraction backbuffer, alpha pass or unshaded fallback",not water.contains("hint_screen_texture") and not water.contains("ALPHA") and not water.contains("unshaded"))
	var banks:=true
	for x_value in [-30.0,-24.0,-17.0,-10.0,-3.0,4.0,11.0,19.0,25.0,30.0]:
		var q:Dictionary=River.query(River.center_at_x(float(x_value)));var c:Vector2=q.center;var n:Vector2=q.north_normal;var h:=float(q.half_width)
		banks=banks and Surface.height_at(c+n*(h+River.WET_EDGE+River.BANK_RUN))>Surface.WATER_Y+.08 and Surface.height_at(c-n*(h+River.WET_EDGE+River.BANK_RUN))>Surface.WATER_Y+.08
	check("Representative full-map river bank crests are actual raised geometry",banks)
	print(JSON.stringify({"suite":"T02_river_surface_stress","checks":checks,"failures":failures,"passed":failures.is_empty(),"projection_samples":samples,"legacy_save_cases":legacy_cases,"lane_samples":lane_points.size(),"gameplay_dry_margin":River.DEFAULT_DRY_MARGIN,"physical_4k60_verified":false,"independent_critic":false}))
	quit(0 if failures.is_empty() else 1)
