extends SceneTree

const Queue := preload("res://customer/spatial_queue.gd")
const REV := "synthetic-two-agent-route-not-production"
const ANCHORS := ["in-lane", "in-threshold", "wait-one", "wait-two", "out-threshold", "out-lane"]
var _checks := 0
var _failures := 0

func _check(label: String, result: Variant, expected: Variant) -> void:
	_checks += 1
	if result != expected:
		_failures += 1
		push_error("%s: expected %s, saw %s" % [label, expected, result])

func _binding(clearance: Variant = true, capacity: Variant = 2) -> Dictionary:
	return {
		"approved_actor_free_route": clearance, "layout_revision": REV, "capacity": capacity,
		"entrance": ["in-lane", "in-threshold"], "queue_slots": ["wait-one", "wait-two"],
		"departure": ["out-threshold", "out-lane"],
	}

func _frame(serial: Variant, blocked: String = "", revision: String = REV) -> Dictionary:
	var facts := {}
	for anchor in ANCHORS:
		facts[anchor] = anchor != blocked
	return {"layout_revision": revision, "serial": serial, "clear": facts}

func _initialize() -> void:
	var queue := Queue.new()
	_check("default not admitted", queue.reserve("A", _frame(1)), "unbound")
	_check("not approved", queue.configure(_binding(false)), false)
	_check("truthy is not approved", queue.configure(_binding(1)), false)
	_check("no silent expansion", queue.configure(_binding(true, 3)), false)
	_check("no rounded capacity", queue.configure(_binding(true, 2.0)), false)
	_check("no implicit zero capacity", queue.configure(_binding(true, 0)), false)
	var aliases := _binding()
	aliases["departure"] = ["in-threshold", "out-lane"]
	_check("shared fixture anchor cannot impersonate separate proof", queue.configure(aliases), false)
	var blank := _binding()
	blank["entrance"] = [" "]
	_check("invalid anchor", queue.configure(blank), false)
	var binding := _binding()
	_check("two-slot actor-free binding", queue.configure(binding), true)
	binding["queue_slots"][0] = "caller-mutation"
	_check("cannot reconfigure live authority", queue.configure(_binding()), false)
	_check("no preexisting reservations", queue.reservations(), [])
	_check("other revision may not use clear sample", queue.reserve("A", _frame(999, "", "wrong")), "wrong_layout")
	_check("first ticket", queue.reserve("A", _frame(1)), "reserved")
	_check("same sample may not be used again", queue.reserve("B", _frame(1)), "stale_observation")
	_check("retry preserves same ticket", queue.reserve("A", _frame(2)), "already_reserved")
	_check("wrong actor type", queue.reserve(true, _frame(3)), "invalid_actor")
	_check("new obstruction blocks second agent", queue.reserve("B", _frame(5, "in-threshold")), "blocked")
	_check("older clear frame cannot undo newer obstruction", queue.reserve("B", _frame(4)), "stale_observation")
	var missing := _frame(6)
	missing["clear"].erase("out-lane")
	missing["clear"]["unrelated"] = true
	_check("equal-size wrong anchor set fails closed", queue.reserve("B", missing), "incomplete_observation")
	_check("missing evidence invalidates older usable frame", queue.reserve("B", _frame(5)), "stale_observation")
	var typed := _frame(7)
	typed["clear"]["wait-two"] = 1
	_check("non-boolean route sample", queue.reserve("B", typed), "incomplete_observation")
	_check("clear observation frees second reservation", queue.reserve("B", _frame(8)), "reserved")
	var expected := [
		{"actor_id": "A", "ticket": 1, "anchor": "wait-one"},
		{"actor_id": "B", "ticket": 2, "anchor": "wait-two"},
	]
	_check("monotonic first two tickets", queue.reservations(), expected)
	var leak := queue.reservations()
	leak[0]["actor_id"] = "outside"
	_check("reservation report is detached", queue.reservations(), expected)
	_check("capacity applies to third request", queue.reserve("C", _frame(9)), "full")
	_check("departure enforces FIFO", queue.release_head("B", _frame(10)), "not_head")
	_check("blocked exit cannot release head", queue.release_head("A", _frame(11, "out-threshold")), "blocked")
	_check("blocked exit cannot promote next", queue.reservations(), expected)
	_check("head releases on fresh clear evidence", queue.release_head("A", _frame(12)), "released")
	_check("remaining ticket keeps ID and order", queue.reservations(), [{"actor_id": "B", "ticket": 2, "anchor": "wait-one"}])
	_check("retired identity cannot reserve twice", queue.reserve("A", _frame(13)), "retired")
	_check("cycle frees one capacity slot", queue.reserve("C", _frame(14)), "reserved")
	_check("new ticket never reuses retired ticket", queue.reservations(), [
		{"actor_id": "B", "ticket": 2, "anchor": "wait-one"},
		{"actor_id": "C", "ticket": 3, "anchor": "wait-two"},
	])
	var guarded := Queue.new()
	_check("isolated authority regression setup", guarded.configure(_binding()), true)
	_check("isolated head 1", guarded.reserve("A", _frame(6)), "reserved")
	_check("isolated tail 2", guarded.reserve("B", _frame(7)), "reserved")
	var held := var_to_bytes(guarded.reservations())
	_check("wrong revision cannot poison current serial even alongside invalid actor", guarded.reserve(null, _frame(999, "out-lane", "wrong")), "invalid_actor")
	_check("float serial cannot poison current authority", guarded.reserve(null, _frame(900.0, "out-lane")), "invalid_actor")
	_check("legitimate serial after rejected authority", guarded.release_head("B", _frame(8)), "not_head")
	_check("invalid reserve cannot discard newer blocked frame", guarded.reserve(null, _frame(10, "out-lane")), "invalid_actor")
	_check("older clear cannot release after rejected actor reserve", guarded.release_head("A", _frame(9)), "stale_observation")
	_check("invalid reserve cannot alter reservation bytes", var_to_bytes(guarded.reservations()), held)
	var incomplete := _frame(15)
	incomplete["clear"]["out-lane"] = null
	_check("invalid release cannot discard newer incomplete frame", guarded.release_head(StringName("A"), incomplete), "invalid_actor")
	_check("older clear cannot promote after rejected actor release", guarded.release_head("A", _frame(14)), "stale_observation")
	_check("invalid release left head/tail bytes intact", var_to_bytes(guarded.reservations()), held)
	_check("newer valid clear can release exactly once", guarded.release_head("A", _frame(16)), "released")
	_check("invalid actors never allocate or retire a ticket", guarded.reserve("C", _frame(17)), "reserved")
	_check("legitimate follow-up retains tail 2 and allocates 3", guarded.reservations(), [
		{"actor_id":"B", "ticket":2, "anchor":"wait-one"},
		{"actor_id":"C", "ticket":3, "anchor":"wait-two"},
	])
	print("customer_spatial_queue: %d/%d" % [_checks - _failures, _checks])
	quit(0 if _failures == 0 else 1)
