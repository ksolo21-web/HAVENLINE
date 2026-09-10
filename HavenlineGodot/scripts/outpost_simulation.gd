extends "res://scripts/population_simulation.gd"
const Climate = preload("res://scripts/outpost_climate.gd")
const PopulationSimulation = preload("res://scripts/population_simulation.gd")
var climate = Climate.new()
const Terrain = preload("res://scripts/outpost_surface.gd")

func constrain_shoreline():
	var dry := Terrain.land_position(position)
	if dry.distance_squared_to(position)>.000001:
		var normal := (dry-position).normalized()
		position=dry
		if velocity.dot(normal)<0: velocity-=normal*velocity.dot(normal)
	for c in companions+enemies+population.actor_records():
		c.position=Terrain.land_position(c.position)

func step(dt: float, input_vector: Vector2, sprint := false):
	if dt<=0 or not is_finite(dt): return
	# Coast collision belongs to the surface, not a decorative invisible barrier.
	constrain_shoreline()
	super.step(dt,input_vector,sprint)
	constrain_shoreline()

func step_climate(dt: float):
	climate.step(dt)
	var safe := position.distance_to(point(contract.world.furnace)) < warmth() and durability > 0
	# Clear daytime preserves the original base cooling rate. Shelter remains the
	# same furnace-radius rule; visuals consume this state, never the reverse.
	var rate := 8.0 if safe else -0.65 * climate.cold_multiplier()
	temperature = clampf(temperature + rate * dt, 0.0, 100.0)
	if safe: health = minf(100.0, health + 4.0 * dt)
	elif temperature <= 0.0: health = maxf(0.0, health - 3.0 * dt)
	if health <= 0.0:
		position = point(contract.player.spawn)
		velocity = Vector2.ZERO
		health = 100.0
		temperature = 65.0
		events.append({"type":"recovery"})

func snapshot() -> Dictionary:
	var state: Dictionary = super.snapshot()
	state["climate"] = climate.snapshot()
	return state

func restore(state: Dictionary) -> bool:
	var clock = Climate.new()
	if state.has("climate"):
		if not clock.restore(state.climate): return false
	else:
		# Old saves resume at their actual play time, not a fresh-weather reset.
		var old_elapsed = state.get("elapsed", 0.0)
		if not Climate.numeric(old_elapsed) or old_elapsed < 0.0 or old_elapsed > Climate.MAX_SECONDS: return false
		clock.seconds = float(old_elapsed)
	var verifier = PopulationSimulation.new()
	if not verifier.restore(state): return false
	if not super.restore(state): return false
	climate = clock
	constrain_shoreline()
	return true
