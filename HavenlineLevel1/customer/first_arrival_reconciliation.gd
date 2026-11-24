extends RefCounted
## Read-only reconciliation after restart. No spawning, IO, stock or effects.
## The caller supplies canonical-verified metadata, not pending write content.

const NO_COMMIT := "no_commit"
const BINDING_REJECTED := "binding_rejected"
const RECEIPT_REJECTED := "receipt_rejected"
const ACTOR_CONFLICT := "actor_conflict"
const RESTORE_CANDIDATE := "restore_candidate"
const ALREADY_PRESENT := "already_present"
const _KEYS := ["revision", "scope", "counter", "bootstrap"]

static func reconcile(expected: Variant, observed: Variant, canonical: Variant, existing_actor_id: Variant = null) -> Dictionary:
	if not _identity_valid(expected) or not _identity_valid(observed):
		return _result(BINDING_REJECTED)
	if expected.size() != 4 or observed.size() != 4 or not _same_identity(expected, observed):
		return _result(BINDING_REJECTED)
	if canonical == null:
		return _result(NO_COMMIT if existing_actor_id == null else ACTOR_CONFLICT)
	if not _identity_valid(canonical):
		return _result(RECEIPT_REJECTED)
	if canonical.size() != 5 or not _valid_text(canonical.get("kind")):
		return _result(RECEIPT_REJECTED)
	if canonical["kind"] != "first_arrival_receipt" or not _same_identity(expected, canonical):
		return _result(RECEIPT_REJECTED)

	# Canonical array, not concatenation: distinct bindings cannot alias by
	# moving a delimiter from one value to another.
	var token := JSON.stringify([
		"havenline.level1.first-arrival/v1",
		expected["revision"], expected["scope"], expected["counter"], expected["bootstrap"],
	]).sha256_text()
	if existing_actor_id == null:
		return _result(RESTORE_CANDIDATE, token)
	if _valid_text(existing_actor_id) and existing_actor_id == token:
		return _result(ALREADY_PRESENT, token)
	return _result(ACTOR_CONFLICT)

static func _identity_valid(value: Variant) -> bool:
	if not (value is Dictionary):
		return false
	for key in _KEYS:
		if not _valid_text(value.get(key)):
			return false
	return true

static func _same_identity(a: Dictionary, b: Dictionary) -> bool:
	for key in _KEYS:
		if a[key] != b[key]:
			return false
	return true

static func _valid_text(value: Variant) -> bool:
	return value is String and not value.is_empty() and value.strip_edges() == value

static func _result(status: String, actor_id: String = "") -> Dictionary:
	return {"status": status, "actor_id": actor_id}
