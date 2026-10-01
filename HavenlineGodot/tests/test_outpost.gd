extends SceneTree
const Sim = preload("res://scripts/outpost_simulation.gd")
const Legacy = preload("res://scripts/population_simulation.gd")
const Climate = preload("res://scripts/outpost_climate.gd")
const Surface = preload("res://scripts/outpost_surface.gd")
const Readout = preload("res://scripts/action_readout.gd")
const Saves = preload("res://scripts/save_store.gd")
var failures: Array = []
var checks: Array = []
func check(label: String, passed: bool):
	checks.append({"name":label,"passed":passed})
	if not passed: failures.append(label)
func step_at(s, where: Vector2, seconds: float):
	s.position=where; s.velocity=Vector2.ZERO
	for i in range(int(ceil(seconds*60.0))): s.step(1.0/60.0,Vector2.ZERO)
func _initialize():
	var c=Climate.new()
	check("New outpost starts in daylight",is_equal_approx(c.hour(),10.0) and c.daylight()>.99)
	check("Clear weather preserves original cooling",is_equal_approx(c.cold_multiplier(),1.0))
	check("No phantom elapsed time on construction",is_zero_approx(c.seconds))
	c.step(2.0)
	check("Suspension-sized delta is capped at one tenth second",is_equal_approx(c.seconds,.1))
	for invalid in [0.0,-1.0,NAN,INF]: c.step(invalid)
	check("Invalid time deltas cannot advance the clock",is_equal_approx(c.seconds,.1))
	c.seconds=600.0
	check("Evening clock correctly reaches 22:00",is_equal_approx(c.hour(),22.0) and c.daylight()<.01)
	check("Blizzard reaches authored maximum snowfall",c.weather().name=="Blizzard" and is_equal_approx(c.weather().snow,1.0))
	check("Night and blizzard increase cold exposure",c.cold_multiplier()>2.0)
	c.seconds=1200.0
	check("Full day wraps clock while advancing day count",is_equal_approx(c.hour(),10.0) and c.day_number()==2)
	for boundary in [180.,360.,540.,720.,900.,1080.]:
		c.seconds=boundary-.001; var before: Dictionary=c.weather()
		c.seconds=boundary+.001; var after: Dictionary=c.weather()
		check("Weather blends continuously at %.0fs" % boundary,absf(before.snow-after.snow)<.001 and absf(before.wind-after.wind)<.001)
	var saved:=c.snapshot(); var restored=Climate.new()
	check("Climate JSON round-trip retains exact state",restored.restore(JSON.parse_string(JSON.stringify(saved))) and restored.snapshot()==saved)
	for bad in [{"revision":true,"seconds":2},{"revision":1.5,"seconds":2},{"revision":2,"seconds":2},{"revision":1,"seconds":-1},{"revision":1,"seconds":INF},{"revision":1,"seconds":"12"},{"revision":1,"seconds":false},{"revision":1,"seconds":Climate.MAX_SECONDS+1},{"revision":1},{"revision":1,"seconds":2,"unexpected":0}]:
		var before: Dictionary=restored.snapshot()
		check("Malformed climate rejected transactionally: "+str(bad),not restored.restore(bad) and restored.snapshot()==before)
	var s=Sim.new()
	check("Original four custom identities remain active",s.lead==1 and s.companions.map(func(x): return x.id)==[2,3,4])
	check("Seven animal species and two human survivor sites remain",s.ENCOUNTER_SITES.size()==9 and not s.ENCOUNTER_SITES.has("pet_cat_01"))
	var old=Legacy.new(); old.elapsed=123.0
	check("Legacy saves migrate climate from recorded play time",s.restore(old.snapshot()) and is_equal_approx(s.climate.seconds,123.0))
	check("Migrated save becomes climate-aware",s.snapshot().has("climate"))
	var before: Dictionary=s.snapshot(); var invalid: Dictionary=before.duplicate(true)
	invalid.inventory.wood=700; invalid.climate.seconds=-1
	check("Bad extension cannot overwrite real inventory",not s.restore(invalid) and s.snapshot()==before)
	invalid=before.duplicate(true); invalid.inventory.wood=-1; invalid.climate.seconds=555
	check("Bad base save cannot overwrite valid climate",not s.restore(invalid) and s.snapshot()==before)
	invalid=before.duplicate(true); invalid.population={"schema":999}
	check("Bad NPC extension cannot overwrite climate or crew",not s.restore(invalid) and s.snapshot()==before)
	s=Sim.new(); s.threats_enabled=false; s.rescue_enabled=false; s.population.presentation_required=true
	step_at(s,Vector2(12,4),1.0)
	check("Gameplay and climate clocks advance at the same rate",is_equal_approx(s.elapsed,s.climate.seconds))
	check("Daytime outside warmth cools at baseline rate",is_equal_approx(s.temperature,99.35))
	s.climate.seconds=600.; s.temperature=80.0
	step_at(s,Vector2(12,4),1.0)
	check("Actual blizzard gameplay cools faster",is_equal_approx(s.temperature,80.0-.65*s.climate.cold_multiplier()) and s.temperature<79.0)
	step_at(s,Sim.point(s.contract.world.furnace)+Vector2(0,1),1.)
	check("Operating furnace warms even during blizzard",s.temperature>85.)
	s.durability=0.; var temp: float=s.temperature
	step_at(s,Sim.point(s.contract.world.furnace)+Vector2(0,1),.5)
	check("Broken furnace does not provide invisible heat",s.temperature<temp)
	s=Sim.new(); s.threats_enabled=false; s.rescue_enabled=false
	s.inventory.wood=18
	step_at(s,Sim.point(s.contract.world.furnace)+Vector2(0,1.5),3.1)
	check("Weather extension preserves wood-only L2 lock",s.level==1 and s.stored.wood==18)
	s.inventory.stone=6; step_at(s,s.position,1.1)
	check("Real timed deposits still reach exact L2 requirements",s.level==2 and is_equal_approx(s.warmth(),8.0))
	s=Sim.new(); step_at(s,s.resources[0].position+Vector2(0,1.1),.30)
	var d: Dictionary=Readout.describe(s)
	check("Gather indicator reflects the actual action clock",d.kind=="gather" and absf(d.progress-.30/.58)<.001)
	var progress: float=d.progress
	s.step(1.0/60.0,Vector2(.5,0))
	d=Readout.describe(s)
	check("Movement indicator pauses without discarding progress",d.paused_by_movement and is_equal_approx(d.progress,progress))
	s.action={}
	check("No permanent indicator without an action",Readout.describe(s).is_empty())
	s.action={"kind":"rescue","id":"survivor","position":Vector2.ZERO}; s.action_clocks["rescue:survivor"]=1.1
	check("Rescue ring uses the original 2.2 second timing",is_equal_approx(Readout.describe(s).progress,.5))
	s.action={"kind":"build","id":"north","position":Vector2.ZERO}; s.action_clocks["build:north"]=.12
	check("Construction ring uses real material transfer timing",is_equal_approx(Readout.describe(s).progress,.5))
	var path:="user://test-outpost-weather.json"
	s=Sim.new();s.climate.seconds=617.25;s.inventory.wood=10001
	check("Full extension saves through production save store",Saves.write_state(s.snapshot(),path)==OK)
	var loaded=Sim.new()
	check("Restart preserves weather, clock and unlimited resources",Saves.load_into(loaded,path)==path and loaded.inventory.wood==10001 and is_equal_approx(loaded.climate.seconds,617.25))
	s.climate.seconds=618.25
	check("Subsequent save preserves valid recovery backup",Saves.write_state(s.snapshot(),path)==OK)
	var bad: Dictionary=s.snapshot();bad.climate.seconds=-1
	var payload:=JSON.stringify(bad);var f:=FileAccess.open(path,FileAccess.WRITE)
	f.store_string(JSON.stringify({"schema":1,"payload":payload,"sha256":payload.sha256_text()}));f.close()
	check("Hash-valid malformed climate falls back to good backup",Saves.load_into(loaded,path)==path+".bak" and is_equal_approx(loaded.climate.seconds,617.25))
	for suffix in ["",".bak",".tmp",".bak.tmp"]:DirAccess.remove_absolute(path+suffix)
	var mesh:=Surface.mesh();var vertices: PackedVector3Array=mesh.surface_get_arrays(0)[Mesh.ARRAY_VERTEX]
	var normals: PackedVector3Array=mesh.surface_get_arrays(0)[Mesh.ARRAY_NORMAL]
	check("Terrain uses a continuous sculpted mesh",vertices.size()>10000 and mesh.get_faces().size()==int(Surface.HALF*2.0/Surface.STEP)*int(Surface.HALF*2.0/Surface.STEP)*6)
	var contact_ok:=true;var normals_ok:=true;var variation:=0.
	for i in range(0,vertices.size(),113):
		var v: Vector3=vertices[i]
		contact_ok=contact_ok and absf(v.y-Surface.height_at(Vector2(v.x,v.z)))<.00001
		# T02: the submerged nonwalkable bank has separate normal/winding tests.
		if Surface.lake_distance(Vector2(v.x,v.z))>1.2:
			normals_ok=normals_ok and normals[i].y>.9
		variation=maxf(variation,v.y)
	check("Ground contact sampler matches actual surface vertices",contact_ok)
	check("Snow surface faces upward with gentle ground slopes",normals_ok)
	check("Terrain has sculpted drift height instead of a flat plane",variation>.3)
	check("All six baked sound effects are present",["wind","fire","wood","stone","transfer","upgrade"].all(func(name):return FileAccess.file_exists("res://assets/audio/"+name+".wav")))
	print(JSON.stringify({"suite":"outpost_climate_and_presentation","passed":failures.is_empty(),"checks":checks,"failures":failures}))
	quit(0 if failures.is_empty() else 1)
