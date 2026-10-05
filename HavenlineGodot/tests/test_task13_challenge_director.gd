extends SceneTree

const Director = preload("res://scripts/challenge_director.gd")

var checks: Array[Dictionary] = []
var failures: Array[String] = []

func check(label: String, passed: bool, detail: Variant = null) -> void:
	checks.append({"name": label, "passed": passed, "detail": detail})
	if not passed:
		failures.append(label)

func context(level: int) -> Dictionary:
	return {
		"current_level_id": "t12.level.%03d" % level,
		"current_region_band_id": "band_%02d" % int((level - 1) / 10),
		"completed_milestone_ids": [],
		"progression_intents": [],
	}

func window(sequence: int, overrides: Dictionary = {}) -> Dictionary:
	var row := {
		"attempt_count": 4,
		"success_count": 2,
		"failure_count": 1,
		"abandonment_count": 0,
		"down_count": 0,
		"recovery_count": 1,
		"fast_completion_count": 1,
		"slow_completion_count": 0,
		"strong_streak": 0,
		"struggle_streak": 0,
		"evaluation_sequence": sequence,
	}
	row.merge(overrides, true)
	return row

func _initialize() -> void:
	call_deferred("run")

func run() -> void:
	var director := Director.new()
	check("shipping policy configures", director.configure_from_file())
	var contract := Director.contract()
	check("authority id exact", contract.authority_id == "T13-challenge-director-v1")
	check("director is deterministic", contract.deterministic and not contract.hidden_randomness_allowed and not contract.wall_clock_input_allowed)
	check("normal path is spend blind", contract.spend_blind)
	check("T12 read boundary is exact", contract.t12_fields == ["current_level_id", "current_region_band_id", "completed_milestone_ids", "progression_intents"])
	check("director mutates no upstream authority", not contract.mutates_t12 and not contract.mutates_economy and not contract.mutates_combat_content)
	check("preactivation ceiling declared", contract.preactivation_maximum_state == "BUILT_PENDING_DEPENDENCY" and not contract.integration_allowed_before_t12_approval)

	var baseline := director.evaluate(context(1), window(1))
	check("baseline decision passes", baseline.passed and baseline.profile_id == "NORMAL" and baseline.band_index == 0)
	check("baseline is source-bound to policy", not baseline.policy_fallback and not baseline.policy_hash.is_empty())
	check("baseline never changes resource yield", is_equal_approx(float(baseline.coefficients.resource_yield_multiplier), 1.0))
	check("readability contract covers all C4 ownership boundaries",
		baseline.readability_contract.contract_version == "t13.readability.v1"
		and baseline.readability_contract.danger_band_id == baseline.band_id
		and int(baseline.readability_contract.danger_rank) == 1
		and int(baseline.readability_contract.danger_rank_max) == 10
		and baseline.readability_contract.interaction_target_contract == "preserve_upstream_context_target"
		and baseline.readability_contract.collection_feedback_contract == "preserve_upstream_collection_feedback"
		and baseline.readability_contract.resource_destination_contract == "preserve_upstream_delivery_destination"
		and not baseline.readability_contract.new_controls_required)

	var replay := director.evaluate(context(1), window(1))
	check("identical input replays byte-for-byte", replay == baseline)

	var spend_context := context(1)
	spend_context["purchase_history"] = [999]
	spend_context["premium_balance"] = 1000000
	var spend_window := window(1)
	spend_window["lifetime_spend"] = 999999
	spend_window["vip_tier"] = 99
	var spend_options := {"store_visits": 100, "billing_cohort": "whale"}
	var spend_result := director.evaluate(spend_context, spend_window, {}, spend_options)
	check("commerce-only changes cannot alter normal decision", spend_result == baseline)
	var audit := Director.audit_input_boundary(spend_context, spend_window, spend_options)
	check("separate boundary audit exposes forbidden commerce keys", not audit.passed and audit.forbidden_keys.size() >= 5)

	var weak_strong := director.evaluate(context(1), window(2, {
		"attempt_count": 4, "success_count": 4, "failure_count": 0,
		"fast_completion_count": 2, "strong_streak": 1,
	}), baseline)
	check("one strong window does not spike challenge", weak_strong.band_index == 0 and weak_strong.reason_codes.has("stable_band"))

	var strong := director.evaluate(context(1), window(2, {
		"attempt_count": 4, "success_count": 4, "failure_count": 0,
		"fast_completion_count": 2, "strong_streak": 2,
	}), baseline)
	check("sustained strong play raises exactly one band", strong.band_index == 1 and strong.reason_codes.has("strong_performance_escalation"))
	check("escalation emits explicit pressure and next action cues",
		strong.readability_contract.transition_state == "escalating"
		and strong.readability_contract.world_response_cue == "pressure_increasing"
		and strong.readability_contract.next_action_cue == "prepare_for_increased_pressure"
		and strong.readability_contract.presentation_update_required)

	var level_jump := director.evaluate(context(100), window(2), baseline)
	check("large progression jump is capped to one band", level_jump.base_band_index == 9 and level_jump.band_index == 1 and level_jump.reason_codes.has("progression_step_up"))
	var level_jump_second := director.evaluate(context(100), window(3), level_jump)
	check("progression continues one bounded step per evaluation", level_jump_second.band_index == 2)

	var high_previous := {"band_index": 9, "evaluation_sequence": 1}
	var struggle := director.evaluate(context(100), window(2, {
		"attempt_count": 4, "success_count": 1, "failure_count": 2,
		"abandonment_count": 1, "down_count": 2,
		"fast_completion_count": 0, "slow_completion_count": 1, "struggle_streak": 1,
	}), high_previous)
	check("struggle decision remains valid", bool(struggle.get("passed", false)), struggle.get("errors", []))
	check("struggle triggers one-step recovery", int(struggle.get("band_index", -1)) == 8 and Array(struggle.get("reason_codes", [])).has("recovery_deescalation"))
	check("recovery emits explicit easing and stabilization cues",
		struggle.readability_contract.transition_state == "recovering"
		and struggle.readability_contract.world_response_cue == "pressure_easing"
		and struggle.readability_contract.next_action_cue == "stabilize_and_recover"
		and struggle.readability_contract.presentation_update_required)
	var deep_struggle := director.evaluate(context(100), window(3, {
		"attempt_count": 4, "success_count": 1, "failure_count": 2,
		"abandonment_count": 1, "down_count": 2,
		"fast_completion_count": 0, "slow_completion_count": 1, "struggle_streak": 3,
	}), struggle)
	check("deep struggle decision remains valid", bool(deep_struggle.get("passed", false)), deep_struggle.get("errors", []))
	check("sustained struggle can deepen recovery but still one step per evaluation", int(deep_struggle.get("band_index", -1)) == 7)

	var neutral_hold := director.evaluate(context(1), window(2), {"band_index": 1, "evaluation_sequence": 1})
	check("neutral input preserves hysteresis above base", neutral_hold.band_index == 1 and neutral_hold.reason_codes.has("hysteresis_hold"))

	var stale := director.evaluate(context(1), window(2), {"band_index": 0, "evaluation_sequence": 2})
	check("stale previous sequence fails closed", not stale.passed and stale.errors.has("stale_or_replayed_previous_sequence"))
	var malformed := director.evaluate(context(1), window(1, {"attempt_count": 1, "success_count": 2}))
	check("impossible performance counts fail closed", not malformed.passed and malformed.errors.has("attempt_outcome_count_exceeds_attempts"))
	var invalid_profile := director.evaluate(context(1), window(1), {}, {"requested_profile": "VIP_HARD"})
	check("unknown profile fails closed", not invalid_profile.passed and invalid_profile.errors.has("invalid_requested_profile"))

	var normal_gm_baseline := director.evaluate(context(50), window(1))
	var unauthorized_gm := director.evaluate(context(50), window(1), {}, {"requested_profile": "GM_CHALLENGE", "gm_authorized": false})
	check("spoofed GM request falls to normal profile", unauthorized_gm.passed and unauthorized_gm.profile_id == "NORMAL" and unauthorized_gm.coefficients == normal_gm_baseline.coefficients)
	var gm := director.evaluate(context(50), window(1), {}, {"requested_profile": "GM_CHALLENGE", "gm_authorized": true})
	check("authorized GM profile resolves", gm.passed and gm.profile_id == "GM_CHALLENGE")
	check("GM readability explicitly marks owner challenge",
		gm.readability_contract.world_response_cue == "owner_challenge_elevated"
		and gm.readability_contract.next_action_cue == "prepare_for_owner_challenge"
		and not gm.readability_contract.new_controls_required)
	check("GM threat target is exact", is_equal_approx(float(gm.gm_relative.threat_ratio), 1.35))
	check("GM recovery and wave ratios are exact", is_equal_approx(float(gm.gm_relative.recovery_window_ratio), 0.85) and is_equal_approx(float(gm.gm_relative.wave_delay_ratio), 0.85))
	check("GM raw inflation caps are respected", float(gm.gm_relative.raw_enemy_hp_ratio) <= 1.10 and float(gm.gm_relative.raw_enemy_damage_ratio) <= 1.15)
	check("GM adds one meaningful emergency", int(gm.gm_relative.concurrent_emergency_bonus) == 1)
	check("GM never reduces resource yield", is_equal_approx(float(gm.coefficients.resource_yield_multiplier), 1.0))
	var gm_apex := director.evaluate(context(100), window(1), {}, {"requested_profile": "GM_CHALLENGE", "gm_authorized": true})
	check("GM apex remains below explicit absolute threat cap", gm_apex.passed and float(gm_apex.coefficients.threat_budget_multiplier) <= float(gm_apex.gm_relative.absolute_threat_budget_multiplier_cap) + 0.000001)
	check("GM apex remains below explicit absolute raw caps", float(gm_apex.coefficients.raw_enemy_hp_multiplier) <= float(gm_apex.gm_relative.absolute_enemy_hp_multiplier_cap) + 0.000001 and float(gm_apex.coefficients.raw_enemy_damage_multiplier) <= float(gm_apex.gm_relative.absolute_enemy_damage_multiplier_cap) + 0.000001)
	check("GM advisory pressure adds coordinated variety without new controls", gm_apex.advisory_pressure_directives.size() >= 6)

	var gm_strong := director.evaluate(context(50), window(2, {
		"attempt_count": 4, "success_count": 4, "failure_count": 0,
		"fast_completion_count": 2, "strong_streak": 2,
	}), normal_gm_baseline, {"requested_profile": "GM_CHALLENGE", "gm_authorized": true})
	check("GM strong ratio stays inside approved envelope", float(gm_strong.gm_relative.threat_ratio) >= 1.25 and float(gm_strong.gm_relative.threat_ratio) <= 1.60)
	var gm_struggle := director.evaluate(context(50), window(2, {
		"attempt_count": 4, "success_count": 1, "failure_count": 2,
		"abandonment_count": 1, "down_count": 2, "struggle_streak": 2,
	}), normal_gm_baseline, {"requested_profile": "GM_CHALLENGE", "gm_authorized": true})
	check("GM recovery never falls below GM minimum ratio", is_equal_approx(float(gm_struggle.gm_relative.threat_ratio), 1.25))

	var gm_spend_context := context(50)
	gm_spend_context["vip_tier"] = 999
	var gm_spend_options := {"requested_profile": "GM_CHALLENGE", "gm_authorized": true, "lifetime_spend": 1000000}
	check("authorized GM remains spend blind", director.evaluate(gm_spend_context, window(1), {}, gm_spend_options) == gm)

	var policy_data: Variant = JSON.parse_string(FileAccess.get_file_as_string("res://data/challenge_director_v1.json"))
	check("shipping policy JSON parses", policy_data is Dictionary)
	if policy_data is Dictionary:
		var threat_deltas := {}
		var pressure_profiles := {}
		var pressure_vocabulary := {}
		var maximum_adjacent_ratio := 1.0
		for band_index in policy_data.bands.size():
			var band: Dictionary = policy_data.bands[band_index]
			pressure_profiles[String(band.pressure_profile_id)] = true
			for directive: Variant in band.pressure_directives:
				pressure_vocabulary[String(directive)] = true
			if band_index > 0:
				var previous_band: Dictionary = policy_data.bands[band_index - 1]
				var delta_key := "%.3f" % (float(band.threat_budget_multiplier) - float(previous_band.threat_budget_multiplier))
				threat_deltas[delta_key] = true
				maximum_adjacent_ratio = max(maximum_adjacent_ratio, float(band.threat_budget_multiplier) / float(previous_band.threat_budget_multiplier))
		check("nonlinear progression uses varied threat increments", threat_deltas.size() >= 4, threat_deltas.keys())
		check("all ten bands carry distinct challenge styles", pressure_profiles.size() == 10, pressure_profiles.keys())
		check("pressure vocabulary spans at least six challenge axes", pressure_vocabulary.size() >= 6, pressure_vocabulary.keys())
		var protection: Dictionary = policy_data.upgrade_protection
		check("adjacent adaptation respects upgrade counter cap", maximum_adjacent_ratio <= float(protection.maximum_immediate_threat_counter_ratio) + 0.000001, maximum_adjacent_ratio)
		var preserved_advantage := float(protection.minimum_meaningful_upstream_gain_ratio) / maximum_adjacent_ratio
		check("policy guarantees minimum preserved upgrade advantage", preserved_advantage + 0.000001 >= float(protection.minimum_preserved_advantage_ratio), preserved_advantage)
		check("milestone metadata is explicitly excluded from challenge scoring", protection.milestone_metadata_is_scoring_input == false)

		var bad_policy: Dictionary = policy_data.duplicate(true)
		bad_policy.gm_profile.threat_target_ratio = 2.0
		var fallback := Director.new()
		check("malformed policy activates safe fallback", not fallback.configure(bad_policy))
		var fallback_decision := fallback.evaluate(context(100), window(1))
		check("fallback never increases challenge", fallback_decision.passed and fallback_decision.policy_fallback and float(fallback_decision.coefficients.threat_budget_multiplier) <= 0.85)

	var monotonic := true
	var previous_threat := -1.0
	var paired_spend_blind := true
	var cold_start_band_ids := {}
	for level in 100:
		var level_number := level + 1
		var ordinary := director.evaluate(context(level_number), window(1))
		var altered := context(level_number)
		altered["purchase_history"] = [level_number * 1000]
		var altered_window := window(1)
		altered_window["premium_balance"] = level_number * 100000
		var paired := director.evaluate(altered, altered_window)
		paired_spend_blind = paired_spend_blind and paired == ordinary
		var threat := float(ordinary.coefficients.threat_budget_multiplier)
		monotonic = monotonic and threat + 0.000001 >= previous_threat
		previous_threat = threat
		cold_start_band_ids[String(ordinary.band_id)] = true
	check("cold-start level progression is monotonic across 1-100", monotonic)
	check("difficulty exposes ten distinct 10-level progression bands", cold_start_band_ids.size() == 10, cold_start_band_ids.keys())
	check("100-level spend-blind equivalence matrix passes", paired_spend_blind)

	var samples: Array[int] = []
	var benchmark_iterations: int = 2000
	var total_usec: int = 0
	var benchmark_valid := true
	for _iteration in benchmark_iterations:
		var sample_start: int = Time.get_ticks_usec()
		var result: Dictionary = director.evaluate(context(51), window(1))
		var elapsed_usec: int = Time.get_ticks_usec() - sample_start
		benchmark_valid = benchmark_valid and bool(result.get("passed", false))
		total_usec += elapsed_usec
		samples.append(elapsed_usec)
	check("all benchmark evaluations remain valid", benchmark_valid)
	samples.sort()
	var p95_index: int = min(samples.size() - 1, int(floor(float(samples.size()) * 0.95)))
	var p95_usec: int = samples[p95_index]
	var mean_usec: float = float(total_usec) / float(benchmark_iterations)
	check("pure decision mean stays bounded", mean_usec < 500.0, mean_usec)
	check("pure decision p95 stays bounded", p95_usec < 1500, p95_usec)

	print(JSON.stringify({
		"suite": "T13_challenge_director",
		"checks": checks,
		"failures": failures,
		"passed": failures.is_empty(),
		"check_count": checks.size(),
		"benchmark_iterations": benchmark_iterations,
		"benchmark_mean_usec": mean_usec,
		"benchmark_p95_usec": p95_usec,
		"spend_blind_matrix_levels": 100,
		"integration_allowed": false,
		"task_approved": false,
		"isolated_state": "BUILT_PENDING_DEPENDENCY",
	}))
	quit(0 if failures.is_empty() else 1)
