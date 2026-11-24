extends SceneTree
const Guard = preload("res://resources/resource_precommit.gd")
const Ledger = preload("res://opening_ledger.gd")
signal sentinel_signal
var checks: int = 0
var failures: int = 0

func _check(ok: bool, label: String) -> void:
	checks += 1
	if not ok:
		failures += 1
		push_error(label)

func _initialize() -> void:
	var legacy := Ledger.new()
	for id: String in Ledger.KNOWN_WOOD:
		legacy.collect_wood(id)
	var unpaid: Dictionary = legacy.snapshot()
	_check(legacy.pay_center_hearth(), "genuine V8 purchase fixture")
	var paid: Dictionary = legacy.snapshot()
	var restart: Variant = JSON.parse_string(JSON.stringify(paid))
	var state := {"carry":{"X":2,"Y":1}, "receivers":{"r":{"X":0},"q":{"Y":0}}, "receipts":{}}
	var policy := {"r":{"enabled":true,"limits":{"X":3}}, "q":{"enabled":true,"limits":{"Y":3}}}
	var order: Array = ["X", "Y"]
	var request := {"ticket":"t","receiver":"r","material":"X","units":1}
	var token := Guard.capture(4, paid, state, order, policy, "r", request)
	_check(not token.is_empty(), "valid paid capture")
	_check(Guard.capture(4, restart, state, order, policy, "r", request) == token, "legacy normalized cold value identical")
	_check(Guard.capture(4, unpaid, state, order, policy, "r", request).is_empty(), "unearned V8 receipt denies")
	var forged: Dictionary = paid.duplicate(true)
	forged["receipt"]["typed_debit"]["wood"] = 2
	_check(Guard.capture(4, forged, state, order, policy, "r", request).is_empty(), "invalid receipt fails")
	var before := var_to_bytes([paid, state, order, policy, request, token])
	var next := Guard.prepare(token, 4, restart, state, order, policy, "r", request)
	_check(next.get("next_generation") == 5, "prepare gives next generation, not effect")
	_check(next.get("next_state", {}).get("carry") == {"X":1,"Y":1}, "only typed row domain changes")
	_check(next.get("cue_after_commit") == ["t","r","X",1], "cue deferred by contract")
	_check(var_to_bytes([paid, state, order, policy, request, token]) == before, "all supplied data untouched")
	_check(Guard.prepare(token, 5, paid, state, order, policy, "r", request).is_empty(), "ABA generation difference denies")
	_check(Guard.prepare(token, 4.0, paid, state, order, policy, "r", request).is_empty(), "non-int generation denies")
	_check(Guard.prepare(token, 4, paid, state, order, policy, "q", request).is_empty(), "target change denies")
	_check(Guard.prepare(token, 4, paid, state, ["Y","X"], policy, "r", request).is_empty(), "row order change denies")
	var changed: Dictionary = state.duplicate(true)
	changed["carry"]["Y"] += 1
	_check(Guard.prepare(token, 4, paid, changed, order, policy, "r", request).is_empty(), "unrelated row drift denies")
	var changed_policy: Dictionary = policy.duplicate(true)
	changed_policy["r"]["limits"]["X"] += 1
	_check(Guard.prepare(token, 4, paid, state, order, changed_policy, "r", request).is_empty(), "policy change denies")
	var alternate: Dictionary = paid.duplicate(true)
	alternate["collected"].reverse()
	_check(Guard.prepare(token, 4, alternate, state, order, policy, "r", request).is_empty(), "valid but changed legacy state denies")
	var shadow: Dictionary = policy.duplicate(true)
	shadow["q"]["limits"]["wood"] = 1
	_check(Guard.capture(4, paid, state, order, shadow, "r", request).is_empty(), "shadow legacy wood in policy denies")
	changed = state.duplicate(true)
	changed["receivers"]["center-hearth"] = {}
	_check(Guard.capture(4, paid, changed, order, policy, "r", request).is_empty(), "shadow legacy receiver in state denies")
	changed = state.duplicate(true)
	changed["receipts"]["old"] = ["q","wood",1]
	_check(Guard.capture(4, paid, changed, order, policy, "r", request).is_empty(), "shadow legacy wood receipt denies")
	var swapped: Dictionary = request.duplicate(true)
	swapped["units"] = 2
	_check(Guard.prepare(token, 4, paid, state, order, policy, "r", swapped).is_empty(), "same ticket with changed units denies")
	swapped["units"] = 1
	swapped["ticket"] = "different"
	_check(Guard.prepare(token, 4, paid, state, order, policy, "r", swapped).is_empty(), "replacement ticket denies")
	var max_token := Guard.capture(9223372036854775807, paid, state, order, policy, "r", request)
	_check(Guard.prepare(max_token, 9223372036854775807, paid, state, order, policy, "r", request).is_empty(), "generation cannot wrap")
	# Exercise opaque objects outside the selected row and each unsafe Variant.
	var obj := Resource.new()
	obj.resource_name = "before"
	var rid := RenderingServer.canvas_create()
	for item: Variant in [obj, Callable(self, "_initialize"), sentinel_signal, rid]:
		var bad_state := state.duplicate(true)
		bad_state.receivers.q["unrelated"] = {"nested":[item]}
		_check(Guard.capture(4, paid, bad_state, order, policy, "r", request).is_empty(), "opaque value in unrelated receiver denied before capture")
		_check(Guard.prepare(token, 4, paid, bad_state, order, policy, "r", request).is_empty(), "opaque unrelated value denied before successor")
	RenderingServer.free_rid(rid)
	var ref_state := state.duplicate(true)
	ref_state.receivers.q["unrelated"] = obj
	var ref_token := Guard.capture(4, paid, ref_state, order, policy, "r", request)
	obj.resource_name = "after"
	_check(ref_token.is_empty() and Guard.prepare(ref_token, 4, paid, ref_state, order, policy, "r", request).is_empty(), "mutated Resource remains ineligible and is never returned")
	var bad_key := state.duplicate(true)
	bad_key.receivers.q[obj] = 0
	_check(Guard.capture(4, paid, bad_key, order, policy, "r", request).is_empty(), "mutable key outside selected row denies")
	var bad_rules := policy.duplicate(true)
	bad_rules.q.limits["unrelated"] = [INF]
	_check(Guard.capture(4, paid, state, order, bad_rules, "r", request).is_empty(), "nonfinite nested rule denies")
	var cycle: Array = []
	var cyclic: Dictionary = {"back":cycle}
	cycle.append(cyclic)
	var cyclic_state := state.duplicate(true)
	cyclic_state.receivers.q["unrelated"] = cyclic
	_check(Guard.capture(4, paid, cyclic_state, order, policy, "r", request).is_empty(), "mutually recursive containers deny before serialization")
	var cyclic_token: Dictionary = {"back":cycle}
	_check(Guard.prepare(cyclic_token, 4, paid, state, order, policy, "r", request).is_empty(), "cyclic forged token denies before serialization")
	cycle.clear()
	cyclic.clear()
	var object_typed: Array[Resource] = []
	var typed_request := request.duplicate(true)
	typed_request["opaque_typed_empty"] = object_typed
	_check(Guard.capture(4, paid, state, order, policy, "r", typed_request).is_empty(), "empty object-typed container metadata denies")
	var nested_safe := state.duplicate(true)
	nested_safe.receivers.q["notes"] = {"evidence":[1, "text", false, 0.25, null]}
	var nested_token := Guard.capture(4, paid, nested_safe, order, policy, "r", request)
	var nested_next := Guard.prepare(nested_token, 4, paid, nested_safe, order, policy, "r", request)
	_check(not nested_next.is_empty() and nested_next.next_state.receivers.q.notes == nested_safe.receivers.q.notes, "ordinary finite nested value data remains usable")
	print("Resource precommit guard: %d/%d checks" % [checks-failures, checks])
	quit(1 if failures else 0)
