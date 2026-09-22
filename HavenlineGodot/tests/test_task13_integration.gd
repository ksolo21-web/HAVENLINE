extends SceneTree

const Director = preload("res://scripts/challenge_director.gd")

var checks: Array[Dictionary] = []
var failures: Array[String] = []

func check(label: String, passed: bool, detail: Variant = null) -> void:
	checks.append({"name": label, "passed": passed, "detail": detail})
	if not passed:
		failures.append(label)

func context(level: int, intent_count := 0) -> Dictionary:
	var intents: Array = []
	for i in intent_count:
		intents.append({"intent_id": "synthetic-%d" % i, "ignored_by_t13_scoring": true})
	return {
		"current_level_id": "t12.level.%03d" % level,
		"current_region_band_id": "synthetic-band",
		"completed_milestone_ids": [],
		"progression_intents": intents,
	}

func perf(sequence: int) -> Dictionary:
	return {
		"attempt_count": 6,
		"success_count": 4,
		"failure_count": 1,
		"abandonment_count": 1,
		"down_count": 0,
		"recovery_count": 1,
		"fast_completion_count": 2,
		"slow_completion_count": 1,
		"strong_streak": 0,
		"struggle_streak": 0,
		"evaluation_sequence": sequence,
	}

func _initialize() -> void:
	call_deferred("run")

func run() -> void:
	var director := Director.new()
	check("shipping config valid", director.configure_from_file())
	var source := FileAccess.get_file_as_string("res://scripts/challenge_director.gd")
	check("runtime does not preload T12 implementation", not source.contains("progression_architecture.gd"))
	check("runtime does not preload simulation authority", not source.contains('preload("res://scripts/simulation.gd")'))
	check("runtime contains no random API", not source.contains("randf(") and not source.contains("randi(") and not source.contains("RandomNumberGenerator"))
	check("runtime contains no wall-clock scoring call", not source.contains("Time.get_unix") and not source.contains("Time.get_datetime"))

	var contract := Director.contract()
	check("T12 consumer boundary exact", contract.t12_fields == ["current_level_id", "current_region_band_id", "completed_milestone_ids", "progression_intents"])

	var ctx := context(26)
	var before := ctx.duplicate(true)
	var decision := director.evaluate(ctx, perf(1))
	check("synthetic T12 context is consumable", decision.passed and decision.band_index == 1)
	check("T12 context remains unmodified", ctx == before and not decision.mutated_upstream)

	var intent_free := director.evaluate(context(26, 0), perf(1))
	var intent_heavy := director.evaluate(context(26, 64), perf(1))
	check("progression intent payload cannot secretly tune difficulty", intent_free == intent_heavy)

	var replay_stable := true
	for i in 250:
		replay_stable = replay_stable and director.evaluate(context(51), perf(1)) == director.evaluate(context(51), perf(1))
	check("250 deterministic replay pairs are exact", replay_stable)

	var policy: Variant = JSON.parse_string(FileAccess.get_file_as_string("res://data/challenge_director_v1.json"))
	check("policy remains a dictionary", policy is Dictionary)
	if policy is Dictionary:
		var gm: Dictionary = policy.gm_profile
		check("Game Master target ratio matches current contract", is_equal_approx(float(gm.threat_target_ratio), 1.35))
		check("Game Master min/max match current contract", is_equal_approx(float(gm.threat_min_ratio), 1.25) and is_equal_approx(float(gm.threat_max_ratio), 1.60))
		check("Game Master recovery/wave ratios match current contract", is_equal_approx(float(gm.recovery_window_ratio), 0.85) and is_equal_approx(float(gm.wave_delay_ratio), 0.85))
		check("Game Master raw caps match current contract", is_equal_approx(float(gm.raw_enemy_hp_ratio_cap), 1.10) and is_equal_approx(float(gm.raw_enemy_damage_ratio_cap), 1.15))
		check("Game Master cannot add grind or controls", not gm.resource_yield_penalty_allowed and gm.no_new_permanent_controls)

	var gm_envelope_pass := true
	for level in [1, 26, 51, 76]:
		var normal := director.evaluate(context(level), perf(1))
		var gm := director.evaluate(context(level), perf(1), {}, {"requested_profile": "GM_CHALLENGE", "gm_authorized": true})
		var ratio := float(gm.coefficients.threat_budget_multiplier) / float(normal.coefficients.threat_budget_multiplier)
		gm_envelope_pass = gm_envelope_pass and ratio >= 1.25 and ratio <= 1.60
		gm_envelope_pass = gm_envelope_pass and is_equal_approx(float(gm.coefficients.resource_yield_multiplier), 1.0)
	check("GM envelope holds across all normal cold-start bands", gm_envelope_pass)

	var bounded_outputs := true
	for level in 100:
		var d := director.evaluate(context(level + 1), perf(1))
		bounded_outputs = bounded_outputs and d.passed and int(d.band_index) >= 0 and int(d.band_index) <= 3
		bounded_outputs = bounded_outputs and float(d.coefficients.threat_budget_multiplier) >= 0.90 and float(d.coefficients.threat_budget_multiplier) <= 1.25
	check("all 100 normal cold-start levels stay in declared envelope", bounded_outputs)

	var oversized := perf(1)
	oversized.attempt_count = 1000001
	check("unbounded performance counts fail closed", not director.evaluate(context(1), oversized).passed)
	var too_many_intents := context(1, 0)
	var intent_overflow: Array = []
	for i in 129:
		intent_overflow.append(i)
	too_many_intents.progression_intents = intent_overflow
	check("T12 intent input is bounded", not director.evaluate(too_many_intents, perf(1)).passed)

	var policy_before := JSON.stringify(policy)
	for i in 100:
		director.evaluate(context((i % 100) + 1), perf(1))
	check("evaluation never mutates loaded policy data", JSON.stringify(policy) == policy_before)

	print(JSON.stringify({
		"suite": "T13_integration_contract",
		"checks": checks,
		"failures": failures,
		"passed": failures.is_empty(),
		"check_count": checks.size(),
		"deterministic_replay_pairs": 250,
		"level_envelope_cases": 100,
		"gm_band_cases": 4,
		"t12_mutated": false,
		"integration_allowed": false,
		"task_approved": false,
		"isolated_state": "BUILT_PENDING_DEPENDENCY",
	}))
	quit(0 if failures.is_empty() else 1)
