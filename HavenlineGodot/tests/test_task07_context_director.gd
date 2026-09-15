extends SceneTree

const Director = preload("res://scripts/context_director.gd")
const Motion = preload("res://scripts/character1_motion.gd")
const Simulation = preload("res://scripts/simulation.gd")

var checks: Array[Dictionary] = []
var failures: Array[String] = []

func check(label: String, passed: bool, detail: Variant = null) -> void:
	checks.append({"name": label, "passed": passed, "detail": detail})
	if not passed:
		failures.append(label)

func option(kind: String, id: String, position: Vector2, capability: String,
		priority := 0.0, relevance := 0.0, radius := 4.0,
		progress := 0.0, eligible := true) -> Dictionary:
	return {
		"kind": kind, "id": id, "position": position, "eligible": eligible,
		"priority": priority, "capability": capability, "radius": radius,
		"target_relevance": relevance, "progress": progress,
	}

func selected(candidates: Array, role := "player_lead", facing := Vector2.DOWN) -> Dictionary:
	return Director.preview(Vector2.ZERO, facing, role, candidates)

func _initialize() -> void:
	call_deferred("run")

func run() -> void:
	var contract: Dictionary = Director.contract()
	check("contract version is exact", contract.version == "t07_context_director_v1")
	check("one primary movement joystick is preserved", contract.one_primary_movement_joystick)
	check("permanent action strip is absent", contract.permanent_action_buttons == 0)
	check("simulation remains authoritative", contract.simulation_authoritative and not contract.emits_gameplay_events)
	check("director never owns position or facing", not contract.owns_position_or_facing)
	check("context focus adds no save fields", contract.saved_fields.is_empty())
	check("ranking is spend blind", contract.spend_blind)
	check("three registered roles are exact", contract.roles == ["player_lead", "core_human_companion", "rescued_survivor_helper"])
	check("canonical action fields are exact", contract.canonical_fields == ["kind", "id", "position", "progress"])
	check("input population is explicitly capped", contract.maximum_input_candidates == 128 and contract.maximum_eligible_candidates == 96)

	var player_capabilities := Director.capabilities_for_role("player_lead")
	var companion_capabilities := Director.capabilities_for_role("core_human_companion")
	var helper_capabilities := Director.capabilities_for_role("rescued_survivor_helper")
	check("player capability map is registered", player_capabilities == ["gather_with_tools", "carry", "deposit", "build", "repair", "rescue", "attack", "hunt"])
	check("companion capability map is registered", companion_capabilities.has("guard") and not companion_capabilities.has("rescue"))
	check("rescued helper capability map is exact", helper_capabilities.has("heal") and helper_capabilities.has("attack") and not helper_capabilities.has("rescue"))
	check("unknown role has no capabilities", Director.capabilities_for_role("ghost_worker").is_empty())

	var malformed := [
		{},
		{"kind":"gather", "id":"bad", "position":Vector2.ZERO, "eligible":true, "priority":0.0, "capability":"gather_with_tools", "radius":0.0},
		{"kind":"future_economy", "id":"bad", "position":Vector2.ZERO, "eligible":true, "priority":999.0, "capability":"deposit", "radius":4.0},
		{"kind":"gather", "id":"nan", "position":Vector2.ZERO, "eligible":true, "priority":NAN, "capability":"gather_with_tools", "radius":4.0},
	]
	var malformed_result := selected(malformed)
	check("malformed candidates fail closed", malformed_result.state == "idle" and malformed_result.kind.is_empty())
	check("malformed candidates are counted", malformed_result.metrics.invalid_count == 4)

	var duplicate_result := selected([
		option("gather", "wood0", Vector2(0, 1), "gather_with_tools"),
		option("gather", "wood0", Vector2(0, 0.5), "gather_with_tools"),
	])
	check("duplicate stable identities are rejected", duplicate_result.kind.is_empty())
	check("duplicate identity is disclosed", duplicate_result.metrics.duplicate_identities == ["gather:wood0"])
	var preview_outside := selected([option("gather", "release_only", Vector2(0, 4.2), "gather_with_tools", 0.0, 0.0, 4.0)])
	check("preview cannot acquire inside release-only margin", preview_outside.state == "idle" and preview_outside.kind.is_empty())

	var eligibility_result := selected([
		option("enemy", "wolf0", Vector2(0, 0.3), "attack", 0.0, 1.0, 4.0, 0.0, false),
		option("gather", "wood0", Vector2(0, 1), "gather_with_tools"),
	])
	check("ineligible danger cannot resolve", eligibility_result.identity == "gather:wood0")
	var mismatch_result := selected([
		option("enemy", "spoofed", Vector2(0, 0.2), "deposit", 100.0, 1.0),
		option("gather", "wood0", Vector2(0, 1), "gather_with_tools"),
	])
	check("kind capability mismatch fails closed", mismatch_result.identity == "gather:wood0")
	var helper_result := selected([
		option("enemy", "wolf0", Vector2(0, 0.2), "attack"),
		option("repair", "north", Vector2(0, 1.0), "repair"),
	], "rescued_survivor_helper")
	check("helper resolves its registered attack capability", helper_result.identity == "enemy:wolf0")
	var companion_result := selected([
		option("rescue", "survivor", Vector2(0, 0.2), "rescue"),
		option("build", "north", Vector2(0, 1.0), "build"),
	], "core_human_companion")
	check("companion cannot borrow player rescue capability", companion_result.identity == "build:north")
	check("unknown role is visibly blocked", selected([option("gather", "wood0", Vector2.ZERO, "gather_with_tools")], "unknown").state == "blocked_role")
	check("missing presented actor is visibly blocked", Director.preview(Vector2.ZERO, Vector2.DOWN, "player_lead", [], false, true).reason == "actor_not_presented")
	check("not-ready actor is visibly blocked", Director.preview(Vector2.ZERO, Vector2.DOWN, "player_lead", [], true, false).reason == "actor_not_ready")

	var priority_result := selected([
		option("gather", "near", Vector2(0, 0.05), "gather_with_tools", 100.0, 1.0),
		option("rescue", "far", Vector2(0, 3.9), "rescue", -100.0, -1.0),
	])
	check("frozen safety band outranks candidate-declared priority", priority_result.identity == "rescue:far")
	var declared_result := selected([
		option("gather", "lower", Vector2(0, 1), "gather_with_tools", 1.0),
		option("gather", "higher", Vector2(0, 3), "gather_with_tools", 2.0),
	])
	check("declared priority is deterministic inside a frozen band", declared_result.identity == "gather:higher")
	var distance_result := selected([
		option("gather", "near", Vector2(0, 1), "gather_with_tools", 0.0, -1.0),
		option("gather", "far", Vector2(0, 2), "gather_with_tools", 0.0, 1.0),
	])
	check("distance precedes target relevance", distance_result.identity == "gather:near")
	var relevance_result := selected([
		option("gather", "relevant", Vector2(1, 1), "gather_with_tools", 0.0, 1.0),
		option("gather", "ordinary", Vector2(-1, 1), "gather_with_tools", 0.0, 0.0),
	])
	check("target relevance resolves equal distance", relevance_result.identity == "gather:relevant")
	var facing_result := selected([
		option("gather", "front", Vector2(0, 1), "gather_with_tools"),
		option("gather", "back", Vector2(0, -1), "gather_with_tools"),
	], "player_lead", Vector2.DOWN)
	check("facing resolves equal priority distance and relevance", facing_result.identity == "gather:front")
	var tie_options := [
		option("gather", "zeta", Vector2(1, 0), "gather_with_tools"),
		option("gather", "alpha", Vector2(-1, 0), "gather_with_tools"),
	]
	check("stable identity is final tie-break", selected(tie_options, "player_lead", Vector2.DOWN).identity == "gather:alpha")
	tie_options.reverse()
	check("candidate order cannot change a tied result", selected(tie_options, "player_lead", Vector2.DOWN).identity == "gather:alpha")
	var first_repeat := selected(tie_options)
	var repeats_stable := true
	for repeat in 100:
		repeats_stable = repeats_stable and selected(tie_options).identity == first_repeat.identity
	check("equal inputs remain stable across repeated resolution", repeats_stable)

	var spend_a := option("gather", "alpha", Vector2(1, 0), "gather_with_tools")
	spend_a["purchase"] = true
	spend_a["vip_tier"] = 99
	spend_a["hidden_personalization_score"] = 1000000
	var spend_b := option("gather", "beta", Vector2(-1, 0), "gather_with_tools")
	check("purchase VIP and personalization metadata cannot affect ranking", selected([spend_b, spend_a]).identity == "gather:alpha")

	var director := Director.new()
	var work := [option("gather", "wood0", Vector2(0, 1), "gather_with_tools", 0.0, 0.5, 2.0, 0.35)]
	var acquiring := director.advance(0.05, Vector2.ZERO, Vector2.DOWN, Vector2.ZERO, Vector2.ZERO, "player_lead", work)
	check("ordinary work observes acquire dwell", acquiring.state == "acquiring" and not acquiring.actionable)
	var active := director.advance(0.08, Vector2.ZERO, Vector2.DOWN, Vector2.ZERO, Vector2.ZERO, "player_lead", work)
	check("stopped eligible work becomes active after dwell", active.state == "active" and active.actionable)
	check("canonical output preserves target and progress", active.kind == "gather" and active.id == "wood0" and active.position == Vector2(0, 1) and is_equal_approx(active.progress, 0.35))
	check("descriptor declares no emitted impact", active.simulation_authoritative and not active.emits_gameplay_event)
	var stable_token := int(active.action_token)
	var held := director.advance(0.01, Vector2(0, 0.9), Vector2.DOWN, Vector2.ZERO, Vector2.ZERO, "player_lead", [
		option("gather", "wood0", Vector2(0, 1), "gather_with_tools", 0.0, 0.5, 2.0),
		option("gather", "wood1", Vector2(0, 0.91), "gather_with_tools", 0.0, 0.5, 2.0),
	])
	check("minimum hold timing prevents early ordinary switch", held.identity == "gather:wood0" and held.action_token == stable_token)
	for frame in 20:
		active = director.advance(1.0 / 60.0, Vector2(0.01 if frame % 2 == 0 else -0.01, 0), Vector2.DOWN, Vector2.ZERO, Vector2.ZERO, "player_lead", [
			option("gather", "wood0", Vector2(0, 1), "gather_with_tools", 0.0, 0.5, 2.0),
			option("gather", "wood1", Vector2(0, 1.04), "gather_with_tools", 0.0, 0.5, 2.0),
		])
	check("switch margin prevents nearby target thrash", active.identity == "gather:wood0" and active.action_token == stable_token and director.switch_count == 1)
	var released := director.advance(0.01, Vector2(0, -2.7), Vector2.DOWN, Vector2.ZERO, Vector2.ZERO, "player_lead", work)
	check("release margin is bounded", released.state == "idle")

	director.reset()
	var moving := director.advance(0.2, Vector2.ZERO, Vector2.DOWN, Vector2(0, 0.2), Vector2.ZERO, "player_lead", work)
	check("nonzero movement blocks contextual action", moving.state == "blocked_movement" and not moving.actionable and moving.reason == "movement_owns_locomotion")
	var stopped_first := director.advance(0.06, Vector2.ZERO, Vector2.DOWN, Vector2.ZERO, Vector2.ZERO, "player_lead", work)
	check("movement does not secretly accrue acquire dwell", stopped_first.state == "acquiring")
	var stopped_second := director.advance(0.07, Vector2.ZERO, Vector2.DOWN, Vector2.ZERO, Vector2.ZERO, "player_lead", work)
	check("stopped actor deterministically reacquires", stopped_second.state == "active")
	var velocity_block := director.advance(0.2, Vector2.ZERO, Vector2.DOWN, Vector2.ZERO, Vector2(0, 0.2), "player_lead", work)
	check("residual velocity blocks action entry", velocity_block.state == "blocked_movement")

	director.reset()
	var ordinary := director.advance(0.13, Vector2.ZERO, Vector2.DOWN, Vector2.ZERO, Vector2.ZERO, "player_lead", work)
	var urgent := director.advance(0.001, Vector2.ZERO, Vector2.DOWN, Vector2.ZERO, Vector2.ZERO, "player_lead", work + [option("enemy", "wolf0", Vector2(0, 1.9), "attack", -100.0, -1.0, 2.0)])
	check("immediate danger preempts ordinary work", ordinary.identity == "gather:wood0" and urgent.identity == "enemy:wolf0")
	check("urgent interrupt bypasses ordinary dwell", urgent.actionable and urgent.reason == "urgent_preemption")
	check("urgent interrupt receives one new action token", urgent.action_token == ordinary.action_token + 1)

	var display := director.presentation()
	check("presentation supplies text and color state", display.visible and display.label == "Defending" and display.color_and_text_state)
	check("presentation adds no permanent action buttons", display.permanent_action_buttons == 0)
	check("presentation keeps the one-joystick language", display.movement_control == "one_primary_joystick")
	director.advance(0.01, Vector2.ZERO, Vector2.DOWN, Vector2.ZERO, Vector2.ZERO, "player_lead", [], false, true)
	check("actor readiness failure is exposed in presentation", director.presentation().state == "blocked_actor")

	var many: Array = []
	for index in 160:
		many.append(option("gather", "node%03d" % index, Vector2(0, 0.5), "gather_with_tools"))
	var capped := selected(many)
	check("oversized candidate input is capped", capped.metrics.input_count == 160 and capped.metrics.inspected_count == 128 and capped.metrics.input_capped)
	check("eligible candidate list is capped", capped.metrics.eligible_count == 96 and capped.metrics.eligible_capped)
	check("cap retains deterministic identity ordering", capped.identity == "gather:node000")
	var benchmark_iterations := 2000
	var benchmark_start := Time.get_ticks_usec()
	for iteration in benchmark_iterations:
		Director.preview(Vector2(float(iteration % 7) * 0.001, 0), Vector2.DOWN, "player_lead", many)
	var benchmark_elapsed_usec := Time.get_ticks_usec() - benchmark_start
	var benchmark_usec_per_evaluation := float(benchmark_elapsed_usec) / float(benchmark_iterations)
	check("worst-population selection remains bounded", benchmark_usec_per_evaluation < 2500.0, benchmark_usec_per_evaluation)
	var non_finite := director.advance(0.01, Vector2.INF, Vector2.DOWN, Vector2.ZERO, Vector2.ZERO, "player_lead", work)
	check("non-finite runtime input fails closed", non_finite.state == "blocked_input")

	var sim := Simulation.new()
	var sim_candidates := Director.build_simulation_candidates(sim)
	check("approved simulation adapter produces canonical candidates", not sim_candidates.is_empty() and sim_candidates.all(func(row): return Director.preview(sim.position, sim.facing, "player_lead", [row]).has("kind")))
	var sim_snapshot := sim.snapshot()
	check("approved save snapshot contains no T07 context state", not sim_snapshot.has("context") and not sim_snapshot.has("focus") and not sim_snapshot.has("action_token"))
	var restore_sim := Simulation.new()
	check("approved save restores without T07 fields", restore_sim.restore(sim_snapshot))
	var reconstruction_a := Director.preview(restore_sim.position, restore_sim.facing, "player_lead", Director.build_simulation_candidates(restore_sim))
	var reconstruction_b := Director.preview(restore_sim.position, restore_sim.facing, "player_lead", Director.build_simulation_candidates(restore_sim))
	check("context reconstructs deterministically after reload", reconstruction_a.identity == reconstruction_b.identity)
	check("canonical output remains compatible with T06 selector", Motion.motion_for_action(active) == "chop" and Motion.motion_for_action(urgent) == "attack_contact")

	print(JSON.stringify({
		"suite": "task07_context_director", "passed": failures.is_empty(),
		"checks": checks, "failures": failures,
		"contract": contract,
		"performance": {"iterations": benchmark_iterations, "input_candidates": many.size(), "microseconds_per_evaluation": benchmark_usec_per_evaluation, "budget_microseconds": 2500.0},
		"selection_trace": {
			"priority": priority_result, "distance": distance_result,
			"relevance": relevance_result, "facing": facing_result,
			"tie_break": first_repeat, "movement": [moving, stopped_first, stopped_second],
			"urgent_preemption": [ordinary, urgent], "population_cap": capped,
		},
	}))
	quit(0 if failures.is_empty() else 1)
