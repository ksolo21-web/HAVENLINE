extends RefCounted
## Opt-in Level 1 decision only: no spawning, charging, scene or persistence.
## The caller must derive these snapshots from an admitted binding, committed
## purchases and confirmed typed stock, not from player or UI input.

const DENIED := "denied"
const ELIGIBLE := "eligible_not_spawned"
const LEGACY := "legacy_unchanged"
const ALREADY_COMMITTED := "already_committed"
const RECEIPT_REJECTED := "receipt_rejected"

static func evaluate(binding: Variant, snapshot: Variant, arrival_receipt: Variant = null) -> String:
	if not (snapshot is Dictionary):
		return DENIED
	var level: Variant = snapshot.get("level")
	if not (level is int):
		return DENIED
	if level >= 2:
		return LEGACY
	if level != 1 or not (binding is Dictionary):
		return DENIED
	if not _is_true(binding.get("admitted")):
		return DENIED

	for key in ["revision", "scope_id", "counter_id", "bootstrap_type"]:
		if not _valid_id(binding.get(key)) or not _valid_id(snapshot.get(key)):
			return DENIED
		if snapshot[key] != binding[key]:
			return DENIED
	var units: Variant = binding.get("bootstrap_units")
	if not (units is int) or units <= 0:
		return DENIED

	# A durable replay is not a second effect or a new eligibility decision.
	# A non-null but malformed/conflicting canonical receipt must never be
	# treated as absence. Pending/temporary writes must not be passed here.
	if arrival_receipt != null:
		if not (arrival_receipt is Dictionary) or arrival_receipt.size() != 5:
			return RECEIPT_REJECTED
		if not _valid_id(arrival_receipt.get("kind")) or arrival_receipt["kind"] != "first_arrival_receipt":
			return RECEIPT_REJECTED
		for key in ["revision", "scope", "counter", "bootstrap"]:
			if not _valid_id(arrival_receipt.get(key)):
				return RECEIPT_REJECTED
		if arrival_receipt["revision"] != binding["revision"] or arrival_receipt["scope"] != binding["scope_id"] or arrival_receipt["counter"] != binding["counter_id"] or arrival_receipt["bootstrap"] != binding["bootstrap_type"]:
			return RECEIPT_REJECTED
		return ALREADY_COMMITTED

	for key in ["camp_paid", "counter_committed", "approved_actor_ready", "ingress_ready", "receipt_committed"]:
		if not _is_true(snapshot.get(key)):
			return DENIED
	# Missing or malformed duplicate state is unsafe to treat as false.
	var already: Variant = snapshot.get("arrival_already_committed")
	if not (already is bool) or already:
		return DENIED
	for pair in [["receipt_revision", "revision"], ["receipt_scope_id", "scope_id"], ["receipt_counter_id", "counter_id"], ["receipt_bootstrap_type", "bootstrap_type"]]:
		if not _valid_id(snapshot.get(pair[0])) or snapshot[pair[0]] != binding[pair[1]]:
			return DENIED
	var stock: Variant = snapshot.get("bootstrap_on_hand")
	if not (stock is int) or stock < units:
		return DENIED
	return ELIGIBLE

static func _valid_id(value: Variant) -> bool:
	return value is String and not value.is_empty() and value.strip_edges() == value

static func _is_true(value: Variant) -> bool:
	return value is bool and value
