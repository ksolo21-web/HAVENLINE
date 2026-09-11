extends "res://scripts/population_simulation.gd"
const Climate = preload("res://scripts/outpost_climate.gd")
const PopulationSimulation = preload("res://scripts/population_simulation.gd")
const Terrain = preload("res://scripts/outpost_surface.gd")
const River = preload("res://scripts/river_geometry.gd")
var climate = Climate.new()

static func _array_point(p: Vector2, y:=0.0) -> Array:
	return [p.x,y,p.y]

func _bounded_dry(p: Vector2, margin: float) -> Vector2:
	var q:=p
	for _iteration in range(3):
		q=Terrain.land_position(q,margin)
		q.x=clampf(q.x,-float(contract.world.boundX),float(contract.world.boundX))
		q.y=clampf(q.y,-float(contract.world.boundZ),float(contract.world.boundZ))
	return q

func _migrate_world_layout():
	# The source JSON remains immutable. Runtime locations that conflict with the
	# new river move to the nearest same-side dry bank; economic state is kept.
	contract=contract.duplicate(true)
	tuning=contract.openingLoopTuning
	for key in ["leftTent","rightTent","northBarricade","southBarricade"]:
		var raw:Array=contract.world[key];var q:=River.protected_build_position(point(raw))
		q=_bounded_dry(q,River.WET_EDGE+River.BANK_RUN+River.SNOW_SHOULDER+River.BUILD_SETBACK)
		contract.world[key]=_array_point(q,float(raw[1]))
	for key in ["survivor","forestGate"]:
		var raw:Array=contract.world[key];var q:=_bounded_dry(point(raw),0.50)
		contract.world[key]=_array_point(q,float(raw[1]))
	for kind in ["wood","stone"]:
		var relocated:Array=[]
		for raw in contract.world[kind+"Nodes"]:
			var q:=_bounded_dry(point(raw),0.55);relocated.append(_array_point(q,float(raw[1])))
		contract.world[kind+"Nodes"]=relocated
	for kind in ["metal","fuel"]:
		var key:=kind+"Node";var raw:Array=contract.world[key]
		var q:=_bounded_dry(point(raw),0.55);contract.world[key]=_array_point(q,float(raw[1]))
	# BaseSimulation built resource/defense records before this subclass migration.
	for resource in resources:
		if resource.kind in ["wood","stone"]:
			var index:=int(String(resource.id).trim_prefix(resource.kind))
			resource.position=point(contract.world[resource.kind+"Nodes"][index])
		else:
			resource.position=point(contract.world[resource.kind+"Node"])
	for side in defenses:
		defenses[side].position=point(contract.world[side+"Barricade"])
	position=_bounded_dry(position,River.DEFAULT_DRY_MARGIN)
	for c in companions:c.position=_bounded_dry(c.position,River.DEFAULT_DRY_MARGIN)

func _init(data: Dictionary = {}, chosen_lead: int = 1):
	super(data,chosen_lead)
	_migrate_world_layout()

func constrain_shoreline():
	var old:=position;var dry:=_bounded_dry(position,River.DEFAULT_DRY_MARGIN)
	if dry.distance_squared_to(old)>.000001:
		var normal:=(dry-old).normalized();position=dry
		if velocity.dot(normal)<0:velocity-=normal*velocity.dot(normal)
	for c in companions+enemies+population.actor_records():
		c.position=_bounded_dry(c.position,River.DEFAULT_DRY_MARGIN)

func step(dt: float, input_vector: Vector2, sprint := false):
	if dt<=0 or not is_finite(dt): return
	constrain_shoreline()
	super.step(dt,input_vector,sprint)
	constrain_shoreline()

func step_climate(dt: float):
	climate.step(dt)
	var safe := position.distance_to(point(contract.world.furnace)) < warmth() and durability > 0
	var rate := 8.0 if safe else -0.65 * climate.cold_multiplier()
	temperature = clampf(temperature + rate * dt, 0.0, 100.0)
	if safe: health = minf(100.0, health + 4.0 * dt)
	elif temperature <= 0.0: health = maxf(0.0, health - 3.0 * dt)
	if health <= 0.0:
		position = _bounded_dry(point(contract.player.spawn),River.DEFAULT_DRY_MARGIN)
		velocity = Vector2.ZERO
		health = 100.0
		temperature = 65.0
		events.append({"type":"recovery"})

func snapshot() -> Dictionary:
	var state: Dictionary = super.snapshot()
	state["climate"] = climate.snapshot()
	state["river_layout_version"] = River.LAYOUT_VERSION
	return state

func restore(state: Dictionary) -> bool:
	var version=state.get("river_layout_version","")
	if not version is String:return false
	if not String(version).is_empty() and String(version)!=River.LAYOUT_VERSION:return false
	var clock = Climate.new()
	if state.has("climate"):
		if not clock.restore(state.climate): return false
	else:
		var old_elapsed = state.get("elapsed", 0.0)
		if not Climate.numeric(old_elapsed) or old_elapsed < 0.0 or old_elapsed > Climate.MAX_SECONDS: return false
		clock.seconds = float(old_elapsed)
	var verifier = PopulationSimulation.new()
	if not verifier.restore(state): return false
	if not super.restore(state): return false
	climate = clock
	# super.restore may load lake-era positions and old resource records. Project
	# every actor/resource/defense back onto the same authored river geometry.
	_migrate_world_layout()
	constrain_shoreline()
	return true
