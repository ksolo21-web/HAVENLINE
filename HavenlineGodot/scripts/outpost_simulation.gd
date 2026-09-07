extends "res://scripts/population_simulation.gd"
const Climate = preload("res://scripts/outpost_climate.gd")
const PopulationSimulation = preload("res://scripts/population_simulation.gd")
var climate = Climate.new()

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
	return true
