class_name HavenlineChallengeDirector
extends RefCounted

## T13 deterministic, spend-blind Challenge Director.
## This file owns only challenge decisions. It never mutates T12 progression,
## economy/store state, combat content, or global persistence.

const AUTHORITY_ID := "T13-challenge-director-v1"
const POLICY_PATH := "res://data/challenge_director_v1.json"
const T12_FIELDS := ["current_level_id", "current_region_band_id", "completed_milestone_ids", "progression_intents"]
const PERFORMANCE_FIELDS := [
	"attempt_count",
	"success_count",
	"failure_count",
	"abandonment_count",
	"down_count",
	"recovery_count",
	"fast_completion_count",
	"slow_completion_count",
	"strong_streak",
	"struggle_streak",
	"evaluation_sequence",
]
const FORBIDDEN_KEY_FRAGMENTS := [
	"purchase",
	"spend",
	"premium",
	"vip",
	"store",
	"checkout",
	"offer",
	"entitlement",
	"sku",
	"payer",
	"billing",
	"advert",
	"ad_activity",
]
const PROFILE_NORMAL := "NORMAL"
const PROFILE_GM := "GM_CHALLENGE"

var policy: Dictionary = {}
var policy_hash := ""
var policy_valid := false

static func contract() -> Dictionary:
	return {
		"authority_id": AUTHORITY_ID,
		"version": "t13_challenge_director_v1",
		"deterministic": true,
		"spend_blind": true,
		"t12_fields": T12_FIELDS.duplicate(),
		"performance_fields": PERFORMANCE_FIELDS.duplicate(),
		"normal_profile": PROFILE_NORMAL,
		"game_master_profile": PROFILE_GM,
		"mutates_t12": false,
		"mutates_economy": false,
		"mutates_combat_content": false,
		"owns_global_persistence": false,
		"hidden_randomness_allowed": false,
		"wall_clock_input_allowed": false,
		"preactivation_maximum_state": "BUILT_PENDING_DEPENDENCY",
		"integration_allowed_before_t12_approval": false,
	}

static func _finite_number(value: Variant) -> bool:
	return (value is int or value is float) and is_finite(float(value))

static func _integer_number(value: Variant, minimum: int, maximum: int) -> bool:
	if not _finite_number(value):
		return false
	var number := float(value)
	return number >= float(minimum) and number <= float(maximum) and is_zero_approx(fmod(number, 1.0))

static func _valid_identifier(value: Variant, maximum := 128) -> bool:
	return value is String and not String(value).is_empty() and String(value).length() <= maximum

static func _valid_string_array(value: Variant, maximum := 64) -> bool:
	if not (value is Array) or value.size() > maximum:
		return false
	var seen := {}
	for item: Variant in value:
		if not _valid_identifier(item):
			return false
		var text := String(item)
		if text in seen:
			return false
		seen[text] = true
	return true

static func _safe_fallback_policy() -> Dictionary:
	return {
		"schema_version": 1,
		"policy_id": "t13.challenge.safe-fallback",
		"policy_version": "1.0.0-safe",
		"bands": [{
			"band_id": "safe",
			"threat_budget_multiplier": 0.85,
			"recovery_window_multiplier": 1.15,
			"wave_delay_multiplier": 1.15,
			"raw_enemy_hp_multiplier": 0.90,
			"raw_enemy_damage_multiplier": 0.90,
			"resource_yield_multiplier": 1.0,
			"concurrent_emergency_bonus": 0,
		}],
		"normal_profile": {
			"profile_id": PROFILE_NORMAL,
			"level_band_size": 100,
			"minimum_band_index": 0,
			"maximum_band_index": 0,
		},
		"thresholds": {
			"minimum_attempts_for_escalation": 999999,
			"escalation_success_rate": 1.0,
			"escalation_fast_completions": 999999,
			"escalation_strong_streak": 64,
			"recovery_failure_rate": 0.0,
			"recovery_down_count": 1,
			"recovery_abandonment_count": 1,
			"recovery_struggle_streak": 1,
			"deep_recovery_struggle_streak": 3,
		},
		"limits": {
			"maximum_count": 1000000,
			"maximum_streak": 64,
			"maximum_progression_intents": 128,
			"maximum_up_steps_per_evaluation": 1,
			"maximum_down_steps_per_evaluation": 1,
		},
		"gm_profile": {
			"profile_id": PROFILE_GM,
			"threat_target_ratio": 1.0,
			"threat_min_ratio": 1.0,
			"threat_max_ratio": 1.0,
			"threat_strong_ratio": 1.0,
			"recovery_window_ratio": 1.0,
			"wave_delay_ratio": 1.0,
			"raw_enemy_hp_ratio": 1.0,
			"raw_enemy_hp_ratio_cap": 1.0,
			"raw_enemy_damage_ratio": 1.0,
			"raw_enemy_damage_ratio_cap": 1.0,
			"concurrent_emergency_bonus": 0,
			"resource_yield_penalty_allowed": false,
			"no_new_permanent_controls": true,
		},
	}

static func validate_policy(candidate: Dictionary) -> bool:
	if not _integer_number(candidate.get("schema_version"), 1, 1):
		return false
	if not _valid_identifier(candidate.get("policy_id")) or not _valid_identifier(candidate.get("policy_version")):
		return false
	var bands: Variant = candidate.get("bands")
	if not (bands is Array) or bands.is_empty() or bands.size() > 8:
		return false
	var ids := {}
	var previous_threat := -INF
	for row: Variant in bands:
		if not (row is Dictionary):
			return false
		var band_id := String(row.get("band_id", ""))
		if not _valid_identifier(band_id) or band_id in ids:
			return false
		ids[band_id] = true
		for field in [
			"threat_budget_multiplier",
			"recovery_window_multiplier",
			"wave_delay_multiplier",
			"raw_enemy_hp_multiplier",
			"raw_enemy_damage_multiplier",
			"resource_yield_multiplier",
		]:
			if not _finite_number(row.get(field)) or float(row[field]) <= 0.0:
				return false
		if not _integer_number(row.get("concurrent_emergency_bonus"), 0, 4):
			return false
		if not is_equal_approx(float(row.resource_yield_multiplier), 1.0):
			return false
		var threat := float(row.threat_budget_multiplier)
		if threat + 0.000001 < previous_threat:
			return false
		previous_threat = threat

	var normal: Variant = candidate.get("normal_profile")
	if not (normal is Dictionary) or normal.get("profile_id") != PROFILE_NORMAL:
		return false
	if not _integer_number(normal.get("level_band_size"), 1, 100):
		return false
	if not _integer_number(normal.get("minimum_band_index"), 0, bands.size() - 1):
		return false
	if not _integer_number(normal.get("maximum_band_index"), 0, bands.size() - 1):
		return false
	if int(normal.minimum_band_index) > int(normal.maximum_band_index):
		return false

	var thresholds: Variant = candidate.get("thresholds")
	if not (thresholds is Dictionary):
		return false
	for field in [
		"minimum_attempts_for_escalation",
		"escalation_fast_completions",
		"escalation_strong_streak",
		"recovery_down_count",
		"recovery_abandonment_count",
		"recovery_struggle_streak",
		"deep_recovery_struggle_streak",
	]:
		if not _integer_number(thresholds.get(field), 0, 1000000):
			return false
	for field in ["escalation_success_rate", "recovery_failure_rate"]:
		if not _finite_number(thresholds.get(field)):
			return false
		var value := float(thresholds[field])
		if value < 0.0 or value > 1.0:
			return false
	if int(thresholds.deep_recovery_struggle_streak) < int(thresholds.recovery_struggle_streak):
		return false

	var limits: Variant = candidate.get("limits")
	if not (limits is Dictionary):
		return false
	if not _integer_number(limits.get("maximum_count"), 1, 100000000):
		return false
	if not _integer_number(limits.get("maximum_streak"), 1, 10000):
		return false
	if not _integer_number(limits.get("maximum_progression_intents"), 0, 4096):
		return false
	if not _integer_number(limits.get("maximum_up_steps_per_evaluation"), 1, 2):
		return false
	if not _integer_number(limits.get("maximum_down_steps_per_evaluation"), 1, 2):
		return false

	var gm: Variant = candidate.get("gm_profile")
	if not (gm is Dictionary) or gm.get("profile_id") != PROFILE_GM:
		return false
	for field in [
		"threat_target_ratio",
		"threat_min_ratio",
		"threat_max_ratio",
		"threat_strong_ratio",
		"recovery_window_ratio",
		"wave_delay_ratio",
		"raw_enemy_hp_ratio",
		"raw_enemy_hp_ratio_cap",
		"raw_enemy_damage_ratio",
		"raw_enemy_damage_ratio_cap",
	]:
		if not _finite_number(gm.get(field)) or float(gm[field]) <= 0.0:
			return false
	if not is_equal_approx(float(gm.threat_target_ratio), 1.35):
		return false
	if not is_equal_approx(float(gm.threat_min_ratio), 1.25):
		return false
	if not is_equal_approx(float(gm.threat_max_ratio), 1.60):
		return false
	if not is_equal_approx(float(gm.recovery_window_ratio), 0.85):
		return false
	if not is_equal_approx(float(gm.wave_delay_ratio), 0.85):
		return false
	if not is_equal_approx(float(gm.raw_enemy_hp_ratio_cap), 1.10):
		return false
	if not is_equal_approx(float(gm.raw_enemy_damage_ratio_cap), 1.15):
		return false
	if float(gm.threat_strong_ratio) < float(gm.threat_target_ratio) or float(gm.threat_strong_ratio) > float(gm.threat_max_ratio):
		return false
	if float(gm.raw_enemy_hp_ratio) > float(gm.raw_enemy_hp_ratio_cap):
		return false
	if float(gm.raw_enemy_damage_ratio) > float(gm.raw_enemy_damage_ratio_cap):
		return false
	if not _integer_number(gm.get("concurrent_emergency_bonus"), 0, 2):
		return false
	if gm.get("resource_yield_penalty_allowed") is not bool or bool(gm.resource_yield_penalty_allowed):
		return false
	if gm.get("no_new_permanent_controls") is not bool or not bool(gm.no_new_permanent_controls):
		return false
	return true

func configure(candidate: Dictionary) -> bool:
	if validate_policy(candidate):
		policy = candidate.duplicate(true)
		policy_valid = true
	else:
		policy = _safe_fallback_policy()
		policy_valid = false
	policy_hash = JSON.stringify(policy).sha256_text()
	return policy_valid

func configure_from_file(path := POLICY_PATH) -> bool:
	if not FileAccess.file_exists(path):
		configure({})
		return false
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(path))
	if not (parsed is Dictionary):
		configure({})
		return false
	return configure(parsed)

static func _parse_level_id(value: Variant) -> int:
	if not (value is String):
		return -1
	var text := String(value)
	if text.length() != 13 or not text.begins_with("t12.level."):
		return -1
	var suffix := text.substr(10, 3)
	if not suffix.is_valid_int():
		return -1
	var level := int(suffix)
	if level < 1 or level > 100 or text != "t12.level.%03d" % level:
		return -1
	return level

func _normalize_context(context: Dictionary) -> Dictionary:
	var errors: Array[String] = []
	var level := _parse_level_id(context.get("current_level_id"))
	if level < 1:
		errors.append("invalid_current_level_id")
	var region := context.get("current_region_band_id")
	if not _valid_identifier(region):
		errors.append("invalid_current_region_band_id")
	var milestones: Variant = context.get("completed_milestone_ids")
	if not _valid_string_array(milestones):
		errors.append("invalid_completed_milestone_ids")
	var intents: Variant = context.get("progression_intents")
	var maximum_intents := int(policy.get("limits", {}).get("maximum_progression_intents", 0))
	if not (intents is Array) or intents.size() > maximum_intents:
		errors.append("invalid_progression_intents")
	return {
		"passed": errors.is_empty(),
		"errors": errors,
		"value": {
			"level": level,
			"current_level_id": String(context.get("current_level_id", "")),
			"current_region_band_id": String(region) if region is String else "",
			"completed_milestone_ids": milestones.duplicate() if milestones is Array else [],
			"progression_intent_count": intents.size() if intents is Array else 0,
		},
	}

func _normalize_performance(performance: Dictionary) -> Dictionary:
	var errors: Array[String] = []
	var limits: Dictionary = policy.limits
	var maximum_count := int(limits.maximum_count)
	var maximum_streak := int(limits.maximum_streak)
	var value := {}
	for field in PERFORMANCE_FIELDS:
		var upper := maximum_streak if field in ["strong_streak", "struggle_streak"] else maximum_count
		if not _integer_number(performance.get(field), 0, upper):
			errors.append("invalid_%s" % field)
			value[field] = 0
		else:
			value[field] = int(performance[field])
	if int(value.success_count) + int(value.failure_count) + int(value.abandonment_count) > int(value.attempt_count):
		errors.append("attempt_outcome_count_exceeds_attempts")
	if int(value.fast_completion_count) + int(value.slow_completion_count) > int(value.success_count):
		errors.append("completion_bucket_count_exceeds_successes")
	return {"passed": errors.is_empty(), "errors": errors, "value": value}

func _normalize_previous(previous: Dictionary, evaluation_sequence: int) -> Dictionary:
	if previous.is_empty():
		return {"passed": true, "errors": [], "present": false, "band_index": -1, "evaluation_sequence": -1}
	var errors: Array[String] = []
	var band_count := int(policy.bands.size())
	if not _integer_number(previous.get("band_index"), 0, band_count - 1):
		errors.append("invalid_previous_band_index")
	if not _integer_number(previous.get("evaluation_sequence"), 0, int(policy.limits.maximum_count)):
		errors.append("invalid_previous_evaluation_sequence")
	elif int(previous.evaluation_sequence) >= evaluation_sequence:
		errors.append("stale_or_replayed_previous_sequence")
	return {
		"passed": errors.is_empty(),
		"errors": errors,
		"present": true,
		"band_index": int(previous.get("band_index", 0)),
		"evaluation_sequence": int(previous.get("evaluation_sequence", 0)),
	}

func _normalize_options(options: Dictionary) -> Dictionary:
	var errors: Array[String] = []
	var requested := options.get("requested_profile", PROFILE_NORMAL)
	if not (requested is String) or String(requested) not in [PROFILE_NORMAL, PROFILE_GM]:
		errors.append("invalid_requested_profile")
		requested = PROFILE_NORMAL
	var authorized: Variant = options.get("gm_authorized", false)
	if authorized is not bool:
		errors.append("invalid_gm_authorized")
		authorized = false
	return {"passed": errors.is_empty(), "errors": errors, "requested_profile": String(requested), "gm_authorized": bool(authorized)}

static func _failure(errors: Array, evaluation_sequence := -1) -> Dictionary:
	return {
		"passed": false,
		"errors": errors.duplicate(),
		"authority_id": AUTHORITY_ID,
		"evaluation_sequence": evaluation_sequence,
		"challenge_change_allowed": false,
		"spend_blind": true,
		"mutated_upstream": false,
	}

func evaluate(progression_context: Dictionary, performance_window: Dictionary, previous_decision: Dictionary = {}, options: Dictionary = {}) -> Dictionary:
	if policy.is_empty():
		configure({})
	var context_result := _normalize_context(progression_context)
	var performance_result := _normalize_performance(performance_window)
	var evaluation_sequence := int(performance_result.value.get("evaluation_sequence", -1))
	var previous_result := _normalize_previous(previous_decision, evaluation_sequence)
	var options_result := _normalize_options(options)
	var errors: Array = []
	errors.append_array(context_result.errors)
	errors.append_array(performance_result.errors)
	errors.append_array(previous_result.errors)
	errors.append_array(options_result.errors)
	if not errors.is_empty():
		return _failure(errors, evaluation_sequence)

	var context: Dictionary = context_result.value
	var performance: Dictionary = performance_result.value
	var thresholds: Dictionary = policy.thresholds
	var normal: Dictionary = policy.normal_profile
	var minimum_band := int(normal.minimum_band_index)
	var maximum_band := int(normal.maximum_band_index)
	var level_band_size := int(normal.level_band_size)
	var base_band := min(maximum_band, max(minimum_band, int(floor(float(int(context.level) - 1) / float(level_band_size)))))

	var attempts := int(performance.attempt_count)
	var successes := int(performance.success_count)
	var failures := int(performance.failure_count)
	var abandonments := int(performance.abandonment_count)
	var denominator := max(1, attempts)
	var success_rate := float(successes) / float(denominator)
	var failure_rate := float(failures + abandonments) / float(denominator)

	var struggling := int(performance.struggle_streak) >= int(thresholds.recovery_struggle_streak) and (
		failure_rate >= float(thresholds.recovery_failure_rate)
		or int(performance.down_count) >= int(thresholds.recovery_down_count)
		or abandonments >= int(thresholds.recovery_abandonment_count)
		or int(performance.slow_completion_count) >= 2
	)
	var strong := not struggling and attempts >= int(thresholds.minimum_attempts_for_escalation) and (
		success_rate >= float(thresholds.escalation_success_rate)
		and int(performance.fast_completion_count) >= int(thresholds.escalation_fast_completions)
		and int(performance.strong_streak) >= int(thresholds.escalation_strong_streak)
		and int(performance.down_count) == 0
	)

	var desired_band := base_band
	if struggling:
		var recovery_depth := 2 if int(performance.struggle_streak) >= int(thresholds.deep_recovery_struggle_streak) else 1
		desired_band = max(minimum_band, base_band - recovery_depth)
	elif strong:
		desired_band = min(maximum_band, base_band + 1)

	var reasons: Array[String] = ["progression_level_band"]
	var selected_band := base_band
	if previous_result.present:
		var current_band := int(previous_result.band_index)
		selected_band = current_band
		if desired_band > current_band:
			if base_band > current_band:
				selected_band = min(desired_band, current_band + int(policy.limits.maximum_up_steps_per_evaluation))
				reasons.append("progression_step_up")
			elif strong:
				selected_band = min(desired_band, current_band + int(policy.limits.maximum_up_steps_per_evaluation))
				reasons.append("strong_performance_escalation")
			else:
				reasons.append("hysteresis_hold")
		elif desired_band < current_band:
			if struggling:
				selected_band = max(desired_band, current_band - int(policy.limits.maximum_down_steps_per_evaluation))
				reasons.append("recovery_deescalation")
			else:
				reasons.append("hysteresis_hold")
		else:
			reasons.append("stable_band")
	else:
		reasons.append("cold_start")

	var requested_profile := String(options_result.requested_profile)
	var gm_authorized := bool(options_result.gm_authorized)
	var profile_id := PROFILE_NORMAL
	if requested_profile == PROFILE_GM:
		if gm_authorized:
			profile_id = PROFILE_GM
			reasons.append("gm_authorized")
		else:
			reasons.append("gm_unauthorized_fallback")

	var band: Dictionary = policy.bands[selected_band]
	var coefficients := {
		"threat_budget_multiplier": float(band.threat_budget_multiplier),
		"recovery_window_multiplier": float(band.recovery_window_multiplier),
		"wave_delay_multiplier": float(band.wave_delay_multiplier),
		"raw_enemy_hp_multiplier": float(band.raw_enemy_hp_multiplier),
		"raw_enemy_damage_multiplier": float(band.raw_enemy_damage_multiplier),
		"resource_yield_multiplier": float(band.resource_yield_multiplier),
		"concurrent_emergency_bonus": int(band.concurrent_emergency_bonus),
	}
	var gm_relative := {}
	if profile_id == PROFILE_GM:
		var gm: Dictionary = policy.gm_profile
		var threat_ratio := float(gm.threat_target_ratio)
		if struggling:
			threat_ratio = float(gm.threat_min_ratio)
		elif strong:
			threat_ratio = float(gm.threat_strong_ratio)
		threat_ratio = min(float(gm.threat_max_ratio), max(float(gm.threat_min_ratio), threat_ratio))
		coefficients.threat_budget_multiplier *= threat_ratio
		coefficients.recovery_window_multiplier *= float(gm.recovery_window_ratio)
		coefficients.wave_delay_multiplier *= float(gm.wave_delay_ratio)
		coefficients.raw_enemy_hp_multiplier *= min(float(gm.raw_enemy_hp_ratio), float(gm.raw_enemy_hp_ratio_cap))
		coefficients.raw_enemy_damage_multiplier *= min(float(gm.raw_enemy_damage_ratio), float(gm.raw_enemy_damage_ratio_cap))
		coefficients.concurrent_emergency_bonus += int(gm.concurrent_emergency_bonus)
		coefficients.resource_yield_multiplier = 1.0
		gm_relative = {
			"threat_ratio": threat_ratio,
			"recovery_window_ratio": float(gm.recovery_window_ratio),
			"wave_delay_ratio": float(gm.wave_delay_ratio),
			"raw_enemy_hp_ratio": min(float(gm.raw_enemy_hp_ratio), float(gm.raw_enemy_hp_ratio_cap)),
			"raw_enemy_damage_ratio": min(float(gm.raw_enemy_damage_ratio), float(gm.raw_enemy_damage_ratio_cap)),
			"concurrent_emergency_bonus": int(gm.concurrent_emergency_bonus),
		}

	var fingerprint_payload := [
		int(context.level),
		int(performance.attempt_count),
		int(performance.success_count),
		int(performance.failure_count),
		int(performance.abandonment_count),
		int(performance.down_count),
		int(performance.recovery_count),
		int(performance.fast_completion_count),
		int(performance.slow_completion_count),
		int(performance.strong_streak),
		int(performance.struggle_streak),
		evaluation_sequence,
		int(previous_result.band_index),
		int(previous_result.evaluation_sequence),
		profile_id,
		gm_authorized,
		policy_hash,
	]
	return {
		"passed": true,
		"errors": [],
		"authority_id": AUTHORITY_ID,
		"policy_id": String(policy.policy_id),
		"policy_version": String(policy.policy_version),
		"policy_hash": policy_hash,
		"policy_fallback": not policy_valid,
		"profile_id": profile_id,
		"band_id": String(band.band_id),
		"band_index": selected_band,
		"base_band_index": base_band,
		"coefficients": coefficients,
		"gm_relative": gm_relative,
		"reason_codes": reasons,
		"evaluation_sequence": evaluation_sequence,
		"input_fingerprint": JSON.stringify(fingerprint_payload).sha256_text(),
		"spend_blind": true,
		"mutated_upstream": false,
		"challenge_change_allowed": true,
	}

static func _scan_forbidden_keys(value: Variant, path: String, found: Array[String]) -> void:
	if value is Dictionary:
		for raw_key: Variant in value:
			var key := String(raw_key)
			var lower := key.to_lower()
			for fragment in FORBIDDEN_KEY_FRAGMENTS:
				if lower.contains(fragment):
					found.append(path + key)
					break
			_scan_forbidden_keys(value[raw_key], path + key + ".", found)
	elif value is Array:
		for index in value.size():
			_scan_forbidden_keys(value[index], path + "[%d]." % index, found)

static func audit_input_boundary(progression_context: Dictionary, performance_window: Dictionary, options: Dictionary = {}) -> Dictionary:
	var found: Array[String] = []
	_scan_forbidden_keys(progression_context, "progression_context.", found)
	_scan_forbidden_keys(performance_window, "performance_window.", found)
	_scan_forbidden_keys(options, "options.", found)
	found.sort()
	var unique: Array[String] = []
	for item in found:
		if item not in unique:
			unique.append(item)
	return {
		"passed": unique.is_empty(),
		"forbidden_keys": unique,
		"normal_evaluator_reads_only_whitelisted_fields": true,
	}
