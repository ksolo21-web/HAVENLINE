extends SceneTree

const Receipt := preload("res://customer/first_arrival_reconciliation.gd")
var _checks := 0
var _failures := 0

func _check(label: String, condition: bool) -> void:
	_checks += 1
	if not condition:
		_failures += 1
		push_error(label)

func _expect(label: String, expected: String, result: Dictionary) -> void:
	_check(label + ": " + str(result), result == {"status": expected, "actor_id": ""})

func _initialize() -> void:
	var binding := {"revision": "revision-1", "scope": "scope-1", "counter": "counter-1", "bootstrap": "bootstrap-1"}
	var stored := _put(binding, "kind", "first_arrival_receipt")
	var original := [binding.duplicate(true), stored.duplicate(true)]
	# Before promotion only the pending file would exist. It is outside the
	# canonical input channel. Accidentally passing it still denies recovery.
	_expect("pre-promotion cold replay", Receipt.NO_COMMIT, Receipt.reconcile(binding, binding, null))
	_expect("pending data can't impersonate canonical", Receipt.RECEIPT_REJECTED, Receipt.reconcile(binding, binding, _put(stored, "kind", "pending")))
	_expect("actor without receipt isn't retained silently", Receipt.ACTOR_CONFLICT, Receipt.reconcile(binding, binding, null, "orphan"))
	# Promotion survived; no acknowledgement or actor exists in the new scene.
	var replay := Receipt.reconcile(binding, binding, stored)
	var actor_id: String = replay["actor_id"]
	_check("lost acknowledgement restores candidate by exact receipt", replay["status"] == Receipt.RESTORE_CANDIDATE and actor_id.length() == 64)
	var reordered := {"bootstrap": "bootstrap-1", "scope": "scope-1", "counter": "counter-1", "revision": "revision-1"}
	_check("reordered identity gives same cold candidate", Receipt.reconcile(reordered, binding, stored) == replay)
	_check("same actor already present is not a second restore", Receipt.reconcile(binding, binding, stored, actor_id) == {"status": Receipt.ALREADY_PRESENT, "actor_id": actor_id})
	_expect("wrong existing actor", Receipt.ACTOR_CONFLICT, Receipt.reconcile(binding, binding, stored, "other"))
	_expect("malformed registry value", Receipt.ACTOR_CONFLICT, Receipt.reconcile(binding, binding, stored, false))
	for key in ["revision", "scope", "counter", "bootstrap"]:
		var wrong := _put(binding, key, "wrong")
		_expect("mismatched observed before commit " + key, Receipt.BINDING_REJECTED, Receipt.reconcile(binding, wrong, null))
		_expect("mismatched observed after commit " + key, Receipt.BINDING_REJECTED, Receipt.reconcile(binding, wrong, stored, actor_id))
		_expect("mismatched canonical " + key, Receipt.RECEIPT_REJECTED, Receipt.reconcile(wrong, wrong, stored))
		var rebound := Receipt.reconcile(wrong, wrong, _put(wrong, "kind", "first_arrival_receipt"))
		_check("distinct canonical identity " + key, rebound["status"] == Receipt.RESTORE_CANDIDATE and rebound["actor_id"] != actor_id)
	for invalid in [null, {}, "", {"revision": " "}, _put(binding, "extra", 1)]:
		_expect("invalid identity " + str(invalid), Receipt.BINDING_REJECTED, Receipt.reconcile(invalid, invalid, stored))
	for invalid in [false, "", "malformed JSON", {}, binding, _put(stored, "extra", 1), _put(stored, "scope", 3)]:
		_expect("invalid canonical metadata " + str(invalid), Receipt.RECEIPT_REJECTED, Receipt.reconcile(binding, binding, invalid))
	var a := _put(_put(binding, "counter", "a|b"), "bootstrap", "c")
	var b := _put(_put(binding, "counter", "a"), "bootstrap", "b|c")
	var a_result := Receipt.reconcile(a, a, _put(a, "kind", "first_arrival_receipt"))
	var b_result := Receipt.reconcile(b, b, _put(b, "kind", "first_arrival_receipt"))
	_check("delimiters cannot alias full binding", a_result["status"] == Receipt.RESTORE_CANDIDATE and b_result["status"] == Receipt.RESTORE_CANDIDATE and a_result["actor_id"] != b_result["actor_id"])
	_check("no input mutation", original == [binding, stored])
	print("first_arrival_reconciliation: %d/%d" % [_checks - _failures, _checks])
	quit(0 if _failures == 0 else 1)

func _put(source: Dictionary, key: String, value: Variant) -> Dictionary:
	var result := source.duplicate()
	result[key] = value
	return result
