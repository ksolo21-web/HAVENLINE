extends SceneTree

const Guard := preload("res://customer/first_service_guard.gd")
const Queue := preload("res://customer/spatial_queue.gd")
const REV := "fixture-service-revision"
const COUNTER := "fixture-counter"
const ORDER := "fixture-order"
const FOOD := "fixture-ready-meal"
const ITEM := "fixture-prepared-record"
const ADMISSION := "fixture-durable-arrival"
const OBS := 4
var _checks := 0
var _bad := 0

func _check(ok: bool, label: String) -> void:
	_checks += 1
	if not ok:
		_bad += 1
		push_error(label)

func _put(base: Dictionary, key: String, value: Variant) -> Dictionary:
	var out := base.duplicate()
	out[key] = value
	return out

func _is_status(expected: String, actual: Dictionary) -> bool:
	return actual == {"status": expected}

func _initialize() -> void:
	var queue := Queue.new()
	var anchors := {"in": true, "front": true, "back": true, "out": true}
	_check(queue.configure({"approved_actor_free_route": true, "layout_revision": REV,
		"capacity": 2, "entrance": ["in"], "queue_slots": ["front", "back"], "departure": ["out"]}), "exact reservation owner config")
	_check(queue.reserve("A", {"layout_revision": REV, "serial": 1, "clear": anchors}) == "reserved", "real reviewed queue A")
	_check(queue.reserve("B", {"layout_revision": REV, "serial": 2, "clear": anchors}) == "reserved", "real reviewed queue B")
	var binding := {"admitted": true, "revision": REV, "counter_id": COUNTER, "order_id": ORDER,
		"ready_material": FOOD, "prepared_item_id": ITEM, "units": 2}
	var queue_snapshot := {"revision": REV, "counter_id": COUNTER, "serial": OBS,
		"reservations": queue.reservations(),
		"head_admission": {"id": ADMISSION, "actor_id": "A", "ticket": 1, "committed": true}}
	var stock := {"revision": REV, "counter_id": COUNTER, "serial": OBS,
		"prepared_item": {"id": ITEM, "material": FOOD, "ready": true, "available_units": 2},
		"ready_stock": {FOOD: 3, "fixture-unrelated-stock": 19}}
	var service := Guard.service_id(REV, COUNTER, ORDER, "A", 1, ADMISSION, ITEM, FOOD, 2)
	var request := {"revision": REV, "counter_id": COUNTER, "order_id": ORDER,
		"actor_id": "A", "ticket": 1, "admission_id": ADMISSION, "prepared_item_id": ITEM,
		"material": FOOD, "units": 2, "observed_serial": OBS, "service_id": service}
	var original := [binding.duplicate(true), queue_snapshot.duplicate(true), stock.duplicate(true), request.duplicate(true)]
	var okay := Guard.propose(binding, queue_snapshot, stock, OBS, request)
	var p: Dictionary = okay.get("proposal", {})
	_check(okay.get("status") == "proposal_only", "valid admission creates proposal only")
	_check(p.get("expected_serial") == OBS and p.get("material") == FOOD and p.get("units") == 2 and p.get("expected_units_before") == 3 and p.get("proposed_units_after") == 1, "one exact material debit proposal conserves stock")
	_check(p.get("prepared_item_id") == ITEM and p.get("expected_prepared_before") == 2 and p.get("proposed_prepared_after") == 0, "one exact prepared item loses representation of same units")
	var receipt: Dictionary = p.get("receipt", {})
	_check(receipt.get("kind") == "first_service_receipt" and receipt.get("service_id") == service and receipt.get("ticket") == 1 and receipt.get("admission_id") == ADMISSION and receipt.get("prepared_item_id") == ITEM, "exact receipt ties head and prepared item")
	_check(Guard.propose(binding, queue_snapshot, stock, OBS, request) == okay, "repeat proposal alone is not an authorization or commit")

	_check(_is_status("unbound", Guard.propose(null, queue_snapshot, stock, OBS, request)), "default no policy")
	_check(_is_status("unbound", Guard.propose(_put(binding, "admitted", 1), queue_snapshot, stock, OBS, request)), "truthy unadmitted policy")
	_check(_is_status("wrong_head", Guard.propose(binding, queue_snapshot, stock, OBS, _put(_put(request, "actor_id", "B"), "ticket", 2))), "second valid queue member cannot jump head")
	_check(_is_status("wrong_head", Guard.propose(binding, queue_snapshot, stock, OBS, _put(request, "ticket", 2))), "same actor cannot borrow ticket")
	_check(_is_status("wrong_material", Guard.propose(binding, queue_snapshot, stock, OBS, _put(request, "material", "fixture-unrelated-stock"))), "wrong stocked material cannot substitute")
	_check(_is_status("wrong_units", Guard.propose(binding, queue_snapshot, stock, OBS, _put(request, "units", 2.0))), "float units forbidden")
	_check(_is_status("wrong_prepared_item", Guard.propose(binding, queue_snapshot, stock, OBS, _put(request, "prepared_item_id", "other"))), "request must select exactly authorized prepared item")
	_check(_is_status("unconfirmed_prepared_item", Guard.propose(binding, queue_snapshot, _put(stock, "prepared_item", _put(stock["prepared_item"], "ready", false)), OBS, request)), "raw or unfinished preparation can never debit")
	_check(_is_status("unconfirmed_prepared_item", Guard.propose(binding, queue_snapshot, _put(stock, "prepared_item", _put(stock["prepared_item"], "id", "wrong")), OBS, request)), "right material without exact preparation id rejected")
	_check(_is_status("unconfirmed_admission", Guard.propose(binding, _put(queue_snapshot, "head_admission", _put(queue_snapshot["head_admission"], "committed", false)), stock, OBS, request)), "uncommitted actor admission cannot serve")
	_check(_is_status("unconfirmed_admission", Guard.propose(binding, _put(queue_snapshot, "head_admission", _put(queue_snapshot["head_admission"], "actor_id", "B")), stock, OBS, request)), "admission belongs to exact head")
	_check(_is_status("unconfirmed_admission", Guard.propose(binding, queue_snapshot, stock, OBS, _put(request, "admission_id", "wrong"))), "request cannot borrow another admission")
	for index in range(3):
		var inputs := [request, queue_snapshot, stock]
		inputs[index] = _put(inputs[index], "revision", "other-layout")
		_check(_is_status("wrong_revision", Guard.propose(binding, inputs[1], inputs[2], OBS, inputs[0])), "revision mismatch %s" % index)
	_check(_is_status("wrong_counter", Guard.propose(binding, queue_snapshot, stock, OBS, _put(request, "counter_id", "other"))), "counter binding")
	_check(_is_status("wrong_order", Guard.propose(binding, queue_snapshot, stock, OBS, _put(request, "order_id", "other"))), "order binding")
	_check(_is_status("insufficient_stock", Guard.propose(binding, queue_snapshot, _put(stock, "ready_stock", {FOOD: 1}), OBS, request)), "confirmed stock too small")
	_check(_is_status("unconfirmed_stock", Guard.propose(binding, queue_snapshot, _put(stock, "ready_stock", {FOOD: 3.0}), OBS, request)), "float stock cannot authorize")
	_check(_is_status("insufficient_prepared_stock", Guard.propose(binding, queue_snapshot, _put(stock, "prepared_item", _put(stock["prepared_item"], "available_units", 1)), OBS, request)), "other batches cannot satisfy exact item shortage")
	_check(_is_status("unconfirmed_prepared_item", Guard.propose(binding, queue_snapshot, _put(stock, "prepared_item", _put(stock["prepared_item"], "available_units", 4)), OBS, request)), "prepared amount cannot exceed confirmed total")
	_check(_is_status("stale_observation", Guard.propose(binding, queue_snapshot, stock, OBS + 1, request)), "stock serial cannot be older than trusted epoch")
	_check(_is_status("stale_observation", Guard.propose(binding, _put(queue_snapshot, "serial", OBS - 1), stock, OBS, request)), "queue serial cannot be older")
	_check(_is_status("stale_observation", Guard.propose(binding, queue_snapshot, stock, OBS, _put(request, "observed_serial", OBS - 1))), "request can never consume stale snapshot")
	_check(_is_status("wrong_service_id", Guard.propose(binding, queue_snapshot, stock, OBS, _put(request, "service_id", "other"))), "caller cannot mint a second service nonce")
	var restock := _put(stock, "ready_stock", {FOOD: 0})
	_check(_is_status("already_committed", Guard.propose(binding, queue_snapshot, restock, OBS, request, receipt)), "exact replay status only even after stock reduced")
	var pending := _put(receipt, "kind", "pending")
	_check(_is_status("receipt_conflict", Guard.propose(binding, queue_snapshot, stock, OBS, request, pending)), "pending metadata cannot masquerade as commit")
	var wrong_receipt := _put(receipt, "ticket", 1.0)
	_check(_is_status("receipt_conflict", Guard.propose(binding, queue_snapshot, stock, OBS, request, wrong_receipt)), "receipt numeric coercion forbidden")
	_check(original == [binding, queue_snapshot, stock, request] and queue.reservations() == queue_snapshot["reservations"], "every proposal rejects mutation of snapshots, queue and stock")
	print("FIRST_SERVICE_GUARD %d/%d" % [_checks - _bad, _checks])
	quit(0 if _bad == 0 else 1)
