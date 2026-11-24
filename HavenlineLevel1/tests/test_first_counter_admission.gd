extends SceneTree

const Gate := preload("res://customer/first_counter_admission.gd")
var _checks := 0
var _failures := 0

func _expect(label: String, expected: String, binding: Variant, state: Variant, receipt: Variant = null) -> void:
	_checks += 1
	var observed := Gate.evaluate(binding, state, receipt)
	if observed != expected:
		_failures += 1
		push_error("%s: expected %s, observed %s" % [label, expected, observed])

func _initialize() -> void:
	var binding := {
		"admitted": true, "revision": "rev-test", "scope_id": "L1-test",
		"counter_id": "counter-test", "bootstrap_type": "food-test", "bootstrap_units": 2,
	}
	var state := {
		"level": 1, "revision": "rev-test", "scope_id": "L1-test",
		"counter_id": "counter-test", "bootstrap_type": "food-test",
		"camp_paid": true, "counter_committed": true, "approved_actor_ready": true,
		"ingress_ready": true, "receipt_committed": true, "arrival_already_committed": false,
		"receipt_revision": "rev-test", "receipt_scope_id": "L1-test",
		"receipt_counter_id": "counter-test", "receipt_bootstrap_type": "food-test",
		"bootstrap_on_hand": 2,
	}
	var receipt := {
		"kind": "first_arrival_receipt", "revision": "rev-test", "scope": "L1-test",
		"counter": "counter-test", "bootstrap": "food-test",
	}
	var original := [binding.duplicate(true), state.duplicate(true), receipt.duplicate(true)]
	_expect("default missing authority", Gate.DENIED, null, state)
	_expect("false admission", Gate.DENIED, _put(binding, "admitted", false), state)
	_expect("numeric admission", Gate.DENIED, _put(binding, "admitted", 1), state)
	_expect("valid exact stock", Gate.ELIGIBLE, binding, state)
	_expect("valid extra stock", Gate.ELIGIBLE, binding, _put(state, "bootstrap_on_hand", 3))
	_expect("legacy forwards without consulting bindings", Gate.LEGACY, null, {"level": 2}, "ignored")
	_expect("invalid level cannot forward", Gate.DENIED, binding, _put(state, "level", 2.0))
	_expect("no snapshot", Gate.DENIED, binding, null)
	_expect("preceding level", Gate.DENIED, binding, _put(state, "level", 0))
	_expect("purchase alone is insufficient", Gate.DENIED, binding, {"level": 1, "camp_paid": true, "counter_committed": true})
	for flag in ["camp_paid", "counter_committed", "approved_actor_ready", "ingress_ready", "receipt_committed"]:
		_expect("false " + flag, Gate.DENIED, binding, _put(state, flag, false))
		_expect("string " + flag, Gate.DENIED, binding, _put(state, flag, "true"))
	for key in ["revision", "scope_id", "counter_id", "bootstrap_type", "receipt_revision", "receipt_scope_id", "receipt_counter_id", "receipt_bootstrap_type"]:
		_expect("mismatched " + key, Gate.DENIED, binding, _put(state, key, "other"))
		_expect("empty " + key, Gate.DENIED, binding, _put(state, key, ""))
	for missing in ["arrival_already_committed", "receipt_revision", "admitted"]:
		var bad_binding := binding.duplicate()
		var bad_state := state.duplicate()
		bad_binding.erase(missing)
		bad_state.erase(missing)
		_expect("missing " + missing, Gate.DENIED, bad_binding, bad_state)
	for invalid in [0, -1, 2.0, "2", true, null]:
		_expect("invalid units " + str(invalid), Gate.DENIED, _put(binding, "bootstrap_units", invalid), state)
	for invalid in [1, -3, 2.0, "2", true, null]:
		_expect("invalid or short stock " + str(invalid), Gate.DENIED, binding, _put(state, "bootstrap_on_hand", invalid))
	_expect("arrival flag already true but no durable receipt", Gate.DENIED, binding, _put(state, "arrival_already_committed", true))
	_expect("arrival flag must be boolean", Gate.DENIED, binding, _put(state, "arrival_already_committed", 0))
	_expect("durable receipt is not a second eligibility", Gate.ALREADY_COMMITTED, binding, state, receipt)
	var after_sale := _put(_put(state, "bootstrap_on_hand", 0), "arrival_already_committed", true)
	_expect("durable replay after stock is consumed", Gate.ALREADY_COMMITTED, binding, after_sale, receipt)
	_expect("observed revision can't borrow canonical replay", Gate.DENIED, binding, _put(state, "revision", "other"), receipt)
	_expect("unadmitted replay", Gate.DENIED, _put(binding, "admitted", false), state, receipt)
	for key in ["kind", "revision", "scope", "counter", "bootstrap"]:
		_expect("corrupt durable receipt " + key, Gate.RECEIPT_REJECTED, binding, state, _put(receipt, key, "wrong"))
	_expect("pending receipt kind is not canonical", Gate.RECEIPT_REJECTED, binding, state, _put(receipt, "kind", "pending"))
	_expect("extra receipt field", Gate.RECEIPT_REJECTED, binding, state, _put(receipt, "extra", true))
	for invalid in [{}, false, "", []]:
		_expect("malformed durable receipt " + str(invalid), Gate.RECEIPT_REJECTED, binding, state, invalid)
	_checks += 1
	if original != [binding, state, receipt]:
		_failures += 1
		push_error("decision must not mutate caller state")
	print("first_counter_admission: %d/%d" % [_checks - _failures, _checks])
	quit(0 if _failures == 0 else 1)

func _put(source: Dictionary, key: String, value: Variant) -> Dictionary:
	var result := source.duplicate()
	result[key] = value
	return result
