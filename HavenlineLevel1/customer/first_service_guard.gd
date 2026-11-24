extends RefCounted
## Pure first-service proposal. Caller supplies trusted current snapshots.
## No debit, arrival/release, payment, callback, or serialization of caller data.

static func service_id(revision: String, counter: String, order: String, actor: String, ticket: int, admission: String, prepared_item: String, material: String, units: int) -> String:
	return JSON.stringify(["havenline.l1.first-service/v1", revision, counter, order, actor, str(ticket), admission, prepared_item, material, str(units)]).sha256_text()

static func propose(binding: Variant, queue_observation: Variant, stock_observation: Variant, current_serial: Variant, request: Variant, committed_receipt: Variant = null) -> Dictionary:
	if not (binding is Dictionary) or not _true(binding.get("admitted")):
		return _status("unbound")
	for key in ["revision", "counter_id", "order_id", "prepared_item_id", "ready_material"]:
		if not _id(binding.get(key)):
			return _status("unbound")
	var units: Variant = binding.get("units")
	if not _positive(units):
		return _status("unbound")
	if not (request is Dictionary) or not (queue_observation is Dictionary) or not (stock_observation is Dictionary):
		return _status("bad_input")
	for frame in [request, queue_observation, stock_observation]:
		if not _id(frame.get("revision")) or frame["revision"] != binding["revision"]:
			return _status("wrong_revision")
		if not _id(frame.get("counter_id")) or frame["counter_id"] != binding["counter_id"]:
			return _status("wrong_counter")
	if not _id(request.get("order_id")) or request["order_id"] != binding["order_id"]:
		return _status("wrong_order")
	var serial: Variant = stock_observation.get("serial")
	if not _positive(serial) or not _positive(current_serial) or not _positive(queue_observation.get("serial")) or not _positive(request.get("observed_serial")) or serial != current_serial or queue_observation["serial"] != serial or request["observed_serial"] != serial:
		return _status("stale_observation")
	var reservations: Variant = queue_observation.get("reservations")
	if not (reservations is Array) or reservations.is_empty() or not (reservations[0] is Dictionary):
		return _status("wrong_head")
	var head: Dictionary = reservations[0]
	if not _id(head.get("actor_id")) or not _id(head.get("anchor")) or not _positive(head.get("ticket")):
		return _status("wrong_head")
	if not _id(request.get("actor_id")) or not _positive(request.get("ticket")) or request["actor_id"] != head["actor_id"] or request["ticket"] != head["ticket"]:
		return _status("wrong_head")
	var admission: Variant = queue_observation.get("head_admission")
	if not (admission is Dictionary) or not _id(admission.get("id")) or not _true(admission.get("committed")):
		return _status("unconfirmed_admission")
	if not _id(admission.get("actor_id")) or not _positive(admission.get("ticket")) or admission["actor_id"] != head["actor_id"] or admission["ticket"] != head["ticket"] or not _id(request.get("admission_id")) or request["admission_id"] != admission["id"]:
		return _status("unconfirmed_admission")
	if not _id(request.get("prepared_item_id")) or request["prepared_item_id"] != binding["prepared_item_id"]:
		return _status("wrong_prepared_item")
	if not _id(request.get("material")) or request["material"] != binding["ready_material"]:
		return _status("wrong_material")
	if not _positive(request.get("units")) or request["units"] != units:
		return _status("wrong_units")
	var receipt := {
		"kind": "first_service_receipt", "revision": binding["revision"], "counter_id": binding["counter_id"],
		"order_id": binding["order_id"], "actor_id": head["actor_id"], "ticket": head["ticket"],
		"admission_id": admission["id"], "prepared_item_id": binding["prepared_item_id"],
		"material": binding["ready_material"], "units": units,
	}
	receipt["service_id"] = service_id(receipt["revision"], receipt["counter_id"], receipt["order_id"], receipt["actor_id"], receipt["ticket"], receipt["admission_id"], receipt["prepared_item_id"], receipt["material"], receipt["units"])
	if not _id(request.get("service_id")) or request["service_id"] != receipt["service_id"]:
		return _status("wrong_service_id")
	# Null is verified absence. Never turn malformed or pending receipt data
	# into null upstream; this boundary rejects a nonmatching envelope.
	if committed_receipt != null:
		if not _same_exact_receipt(committed_receipt, receipt):
			return _status("receipt_conflict")
		return _status("already_committed")
	var ready: Variant = stock_observation.get("ready_stock")
	var material: String = receipt["material"]
	var prepared: Variant = stock_observation.get("prepared_item")
	if not (prepared is Dictionary) or not _id(prepared.get("id")) or prepared["id"] != receipt["prepared_item_id"] or not _id(prepared.get("material")) or prepared["material"] != material or not _true(prepared.get("ready")):
		return _status("unconfirmed_prepared_item")
	if not (ready is Dictionary) or not (ready.get(material) is int) or ready[material] < 0:
		return _status("unconfirmed_stock")
	var before: int = ready[material]
	if before < units:
		return _status("insufficient_stock")
	var prepared_units: Variant = prepared.get("available_units")
	if not (prepared_units is int) or prepared_units < 0 or prepared_units > before:
		return _status("unconfirmed_prepared_item")
	if prepared_units < units:
		return _status("insufficient_prepared_stock")
	return {"status": "proposal_only", "proposal": {
		"expected_serial": serial, "material": material, "prepared_item_id": receipt["prepared_item_id"], "units": units,
		"expected_units_before": before, "proposed_units_after": before - units,
		"expected_prepared_before": prepared_units, "proposed_prepared_after": prepared_units - units, "receipt": receipt,
	}}

static func _same_exact_receipt(value: Variant, expected: Dictionary) -> bool:
	if not (value is Dictionary) or value.size() != expected.size():
		return false
	for key in expected:
		var field: Variant = value.get(key)
		if typeof(field) != typeof(expected[key]) or field != expected[key]:
			return false
	return true

static func _status(value: String) -> Dictionary:
	return {"status": value}

static func _id(value: Variant) -> bool:
	return value is String and not value.is_empty() and value.strip_edges() == value

static func _true(value: Variant) -> bool:
	return value is bool and value

static func _positive(value: Variant) -> bool:
	return value is int and value > 0
