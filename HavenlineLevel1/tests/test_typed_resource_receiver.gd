extends SceneTree
const Receiver = preload("res://resources/typed_receiver.gd")
var checks: int = 0
var failures: int = 0

func _check(value: bool, label: String) -> void:
	checks += 1
	if not value:
		failures += 1
		push_error(label)

func _initialize() -> void:
	var order: Array = ["TYPE_A", "TYPE_B"]
	var initial := {
		"carry": {"TYPE_A": 63, "TYPE_B": 5},
		"receivers": {"R_A": {"TYPE_A": 0}, "R_B": {"TYPE_B": 1}, "R_DISABLED": {"TYPE_B": 0}},
		"receipts": {},
	}
	var policy := {
		"R_A": {"enabled": true, "limits": {"TYPE_A": 64}},
		"R_B": {"enabled": true, "limits": {"TYPE_B": 4}},
		"R_DISABLED": {"enabled": false, "limits": {"TYPE_B": 4}},
	}
	var original: Dictionary = initial.duplicate(true)
	var original_policy: Dictionary = policy.duplicate(true)
	var before_bytes := var_to_bytes(initial)
	var req := {"ticket": "one", "receiver": "R_A", "material": "TYPE_A", "units": 52}
	var result: Dictionary = Receiver.plan_transfer(initial, order, policy, "R_A", req)
	_check(not result.is_empty(), "52 type-A units plan")
	var first: Dictionary = result.get("next_state", {})
	_check(Receiver.project_rows(first, order) == [["TYPE_A", 11], ["TYPE_B", 5]], "two ordered carry rows")
	_check(first.get("receivers") == {"R_A": {"TYPE_A": 52}, "R_B": {"TYPE_B": 1}, "R_DISABLED": {"TYPE_B": 0}}, "credits only exact receiver")
	_check(result.get("cue_after_commit") == ["one", "R_A", "TYPE_A", 52], "explicit postcommit intent")
	_check(initial == original and var_to_bytes(initial) == before_bytes and policy == original_policy, "planning mutates no caller data")
	_check(Receiver.plan_transfer(first, order, policy, "R_A", req).is_empty(), "same ticket rejected")
	var next_req := {"ticket": "two", "receiver": "R_B", "material": "TYPE_B", "units": 3}
	var second_result: Dictionary = Receiver.plan_transfer(first, order, policy, "R_B", next_req)
	var second: Dictionary = second_result.get("next_state", {})
	_check(Receiver.project_rows(second, order) == [["TYPE_A", 11], ["TYPE_B", 2]], "second row debited without cross-debit")
	_check(second.get("receivers") == {"R_A": {"TYPE_A": 52}, "R_B": {"TYPE_B": 4}, "R_DISABLED": {"TYPE_B": 0}}, "exact capacity accepted")
	_check(first.get("receipts") == {"one": ["R_A", "TYPE_A", 52]}, "second planning does not mutate first")
	var negatives: Array = [
		[initial, order, "R_B", req, "stale active binding"],
		[initial, order, "R_A", {"ticket": "x", "receiver":"R_A", "material":"TYPE_B", "units":1}, "cross-row substitution"],
		[initial, order, "R_DISABLED", {"ticket":"x","receiver":"R_DISABLED","material":"TYPE_B","units":1}, "disabled target"],
		[initial, order, "R_A", {"ticket":"x","receiver":"R_A","material":"TYPE_A","units":true}, "bool count"],
		[initial, order, "R_A", {"ticket":"x","receiver":"R_A","material":"TYPE_A","units":1.0}, "float count"],
		[initial, order, "R_A", {"ticket":"x","receiver":"R_A","material":"TYPE_A","units":0}, "zero count"],
		[initial, order, "R_A", {"ticket":"x","receiver":"R_A","material":"TYPE_A","units":64}, "insufficient row"],
		[initial, order, "R_B", {"ticket":"x","receiver":"R_B","material":"TYPE_B","units":4}, "insufficient capacity"],
		[initial, ["TYPE_A", "TYPE_A"], "R_A", req, "repeat order"],
		[first, order, "R_B", {"ticket":"one","receiver":"R_B","material":"TYPE_B","units":1}, "mutated replay"],
	]
	for variant: Array in negatives:
		var input: Dictionary = variant[0]
		var seal := var_to_bytes(input)
		var denied: Dictionary = Receiver.plan_transfer(input, variant[1], policy, variant[2], variant[3])
		_check(denied.is_empty() and var_to_bytes(input) == seal, variant[4])
	var malformed: Dictionary = initial.duplicate(true)
	malformed["receivers"]["R_A"]["TYPE_A"] = -1
	_check(Receiver.plan_transfer(malformed, order, policy, "R_A", req).is_empty(), "malformed target rejects")
	var large: Dictionary = initial.duplicate(true)
	var large_policy: Dictionary = policy.duplicate(true)
	large["receivers"]["R_A"]["TYPE_A"] = 9223372036854775806
	large_policy["R_A"]["limits"]["TYPE_A"] = 9223372036854775807
	var large_req := {"ticket":"max","receiver":"R_A","material":"TYPE_A","units":2}
	_check(Receiver.plan_transfer(large, order, large_policy, "R_A", large_req).is_empty(), "capacity rejects without overflow")
	large_req["units"] = 1
	var max_plan: Dictionary = Receiver.plan_transfer(large, order, large_policy, "R_A", large_req)
	_check(max_plan.get("next_state", {}).get("receivers", {}).get("R_A", {}).get("TYPE_A") == 9223372036854775807, "exact int64 boundary")
	_check(policy == original_policy, "policy remains byte-for-value unchanged")
	print("Typed carry/receiver: %d/%d checks" % [checks - failures, checks])
	quit(1 if failures else 0)
