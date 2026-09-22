extends SceneTree

const Director = preload("res://scripts/challenge_director.gd")

func context(level: int) -> Dictionary:
	return {
		"current_level_id": "t12.level.%03d" % level,
		"current_region_band_id": "capture-band",
		"completed_milestone_ids": [],
		"progression_intents": [],
	}

func perf(sequence: int, overrides: Dictionary = {}) -> Dictionary:
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

func output_dir() -> String:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--out="):
			return arg.substr(6)
	return ProjectSettings.globalize_path("res://../task13-isolated-evidence")

func _initialize() -> void:
	call_deferred("run")

func run() -> void:
	var director := Director.new()
	var configured := director.configure_from_file()
	var baseline := director.evaluate(context(1), perf(1))
	var strong := director.evaluate(context(1), perf(2, {
		"attempt_count": 4, "success_count": 4, "failure_count": 0,
		"fast_completion_count": 2, "strong_streak": 2,
	}), baseline)
	var recovery := director.evaluate(context(100), perf(2, {
		"attempt_count": 4, "success_count": 1, "failure_count": 2,
		"abandonment_count": 1, "down_count": 2, "struggle_streak": 1,
	}), {"band_index": 9, "evaluation_sequence": 1})
	var gm := director.evaluate(context(51), perf(1), {}, {"requested_profile": "GM_CHALLENGE", "gm_authorized": true})
	var spoofed_gm := director.evaluate(context(51), perf(1), {}, {"requested_profile": "GM_CHALLENGE", "gm_authorized": false})
	var spend_context := context(1)
	spend_context["lifetime_spend"] = 999999
	var spend_perf := perf(1)
	spend_perf["vip_tier"] = 99
	var spend_equivalent := director.evaluate(spend_context, spend_perf) == baseline
	var replay_equivalent := director.evaluate(context(1), perf(1)) == baseline
	var manifest := {
		"task": "T13",
		"candidate": OS.get_environment("GITHUB_SHA"),
		"configured": configured,
		"policy_hash": baseline.get("policy_hash", ""),
		"scenarios": {
			"baseline": baseline,
			"strong_escalation": strong,
			"recovery": recovery,
			"authorized_gm": gm,
			"spoofed_gm": spoofed_gm,
		},
		"spend_blind_equivalence": spend_equivalent,
		"deterministic_replay_equivalence": replay_equivalent,
		"readability_contract_complete": (
			baseline.get("readability_contract", {}).get("contract_version", "") == "t13.readability.v1"
			and strong.get("readability_contract", {}).get("transition_state", "") == "escalating"
			and recovery.get("readability_contract", {}).get("transition_state", "") == "recovering"
			and gm.get("readability_contract", {}).get("world_response_cue", "") == "owner_challenge_elevated"
		),
		"integration_allowed": false,
		"task_approved": false,
		"isolated_state": "BUILT_PENDING_DEPENDENCY",
		"passed": configured and baseline.passed and strong.passed and recovery.passed and gm.passed and spoofed_gm.passed and spend_equivalent and replay_equivalent and (
			baseline.get("readability_contract", {}).get("contract_version", "") == "t13.readability.v1"
			and strong.get("readability_contract", {}).get("transition_state", "") == "escalating"
			and recovery.get("readability_contract", {}).get("transition_state", "") == "recovering"
			and gm.get("readability_contract", {}).get("world_response_cue", "") == "owner_challenge_elevated"
		),
	}
	var out := output_dir()
	DirAccess.make_dir_recursive_absolute(out)
	var file := FileAccess.open(out.path_join("manifest.json"), FileAccess.WRITE)
	if file == null:
		print(JSON.stringify({"passed": false, "error": "cannot_write_manifest", "out": out}))
		quit(1)
		return
	file.store_string(JSON.stringify(manifest, "\t") + "\n")
	file.close()
	print(JSON.stringify({
		"passed": manifest.passed,
		"scenario_count": manifest.scenarios.size(),
		"spend_blind_equivalence": spend_equivalent,
		"deterministic_replay_equivalence": replay_equivalent,
		"readability_contract_complete": manifest.readability_contract_complete,
		"isolated_state": "BUILT_PENDING_DEPENDENCY",
	}))
	quit(0 if manifest.passed else 1)
