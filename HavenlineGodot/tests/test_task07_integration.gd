extends SceneTree

const Simulation = preload("res://scripts/simulation.gd")
const PopulationSimulation = preload("res://scripts/population_simulation.gd")

var checks: Array[Dictionary] = []
var failures: Array[String] = []

func check(label: String, passed: bool, detail: Variant = null) -> void:
	checks.append({"name": label, "passed": passed, "detail": detail})
	if not passed:
		failures.append(label)

func _initialize() -> void:
	call_deferred("run")

func run() -> void:
	var sim := Simulation.new()
	sim.threats_enabled = false
	check("shipping simulation owns one T07 director", sim.context_director != null)
	var target: Dictionary = sim.resources[0]
	sim.position = Vector2(target.position) + Vector2(0, 1.1)
	sim.facing = (Vector2(target.position) - sim.position).normalized()
	var before_preview := sim.snapshot()
	var preview := sim.choose_action()
	check("choose_action remains a pure preview", preview.kind == "gather" and sim.snapshot() == before_preview and sim.context_director.current_identity.is_empty())
	sim.step(0.06, Vector2.ZERO)
	check("shipping call site exposes acquisition dwell", sim.action.state == "acquiring" and not sim.action.actionable and sim.action_clocks.is_empty())
	sim.step(0.07, Vector2.ZERO)
	var key := "gather:" + String(target.id)
	check("shipping call site activates after stopped dwell", sim.action.state == "active" and sim.action.actionable and sim.action_clocks.has(key))
	var before_movement_clock := float(sim.action_clocks[key])
	sim.step(0.01, Vector2(0.0001, 0.0))
	check("any shipping movement cancels impact", sim.action.state == "blocked_movement" and sim.action.cancelled and is_equal_approx(float(sim.action_clocks[key]), before_movement_clock))
	sim.position = Vector2(target.position) + Vector2(0, 1.1)
	sim.velocity = Vector2.ZERO
	for frame in 13:
		sim.step(0.01, Vector2.ZERO)
	var duration := float(sim.tuning.gatherSecondsPerUnit[String(target.kind)])
	sim.action_clocks[key] = duration - 0.05
	var inventory_before := int(sim.inventory[String(target.kind)])
	var units_before := int(target.units)
	sim.step(0.05, Vector2.ZERO)
	var gather_events := sim.events.filter(func(event): return event.type == "gather")
	check("one authoritative step emits one impact", int(sim.inventory[String(target.kind)]) == inventory_before + 1 and int(target.units) == units_before - 1 and gather_events.size() == 1)
	var post_impact := {"inventory": sim.inventory.duplicate(), "units": int(target.units)}
	sim.choose_action()
	check("director preview cannot duplicate an impact", sim.inventory == post_impact.inventory and int(target.units) == post_impact.units and sim.events.size() == 1)
	var saved := sim.snapshot()
	check("integrated snapshot has no T07 focus fields", not saved.has("context") and not saved.has("focus") and not saved.has("action_token"))
	check("successful restore resets ephemeral focus", sim.restore(saved) and sim.context_director.current_identity.is_empty())
	sim.step(0.06, Vector2.ZERO)
	check("restored context must reacquire", sim.action.state in ["acquiring", "idle"] and not sim.action.actionable)

	var blocked := Simulation.new()
	blocked.presented_actor_ids = [2, 3, 4]
	blocked.step(0.2, Vector2.ZERO)
	var blocked_display := blocked.context_director.presentation()
	check("unpresented lead fails visibly and safely", blocked.action.state == "blocked_actor" and blocked_display.visible and blocked_display.blocked and blocked.events.is_empty())

	var population := PopulationSimulation.new()
	population.stored.wood = 18
	population.stored.stone = 6
	population.update_level()
	population.threats_enabled = false
	population.population.spawn_customer()
	var customer: Dictionary = population.population.customers[0]
	customer.position = population.population.COUNTER
	customer.state = "waiting"
	customer.order_kind = "wood"
	population.position = population.population.COUNTER
	population.inventory.wood = 1
	for frame in 40:
		population.step(0.01, Vector2.ZERO)
	check("population service uses integrated director once", population.population.credits == int(customer.price) and population.inventory.wood == 0)

	print(JSON.stringify({"suite":"task07_integration", "passed":failures.is_empty(), "checks":checks, "failures":failures}))
	quit(0 if failures.is_empty() else 1)
