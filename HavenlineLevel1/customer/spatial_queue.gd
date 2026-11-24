extends RefCounted
## Opt-in actor-free FIFO reservation contract. No spawn, payment or movement.
## An independent route authority supplies topology and exact clear snapshots.

var _layout := ""
var _ingress: Array = []
var _slots: Array = []
var _exit: Array = []
var _queue: Array = []
var _retired: Dictionary = {}
var _last_frame := 0
var _next_ticket := 1

func configure(binding: Variant) -> bool:
	if not _layout.is_empty() or not (binding is Dictionary):
		return false
	if not (binding.get("approved_actor_free_route") is bool) or not binding["approved_actor_free_route"]:
		return false
	if not _id(binding.get("layout_revision")):
		return false
	var amount: Variant = binding.get("capacity")
	if not (amount is int) or amount <= 0:
		return false
	var seen: Dictionary = {}
	for chain in ["entrance", "queue_slots", "departure"]:
		var anchors: Variant = binding.get(chain)
		if not (anchors is Array) or anchors.is_empty():
			return false
		if chain == "queue_slots" and anchors.size() != amount:
			return false
		for anchor in anchors:
			if not _id(anchor) or seen.has(anchor):
				return false
			seen[anchor] = true
	_layout = binding["layout_revision"]
	_ingress = binding["entrance"].duplicate()
	_slots = binding["queue_slots"].duplicate()
	_exit = binding["departure"].duplicate()
	return true

func reserve(actor_id: Variant, frame: Variant) -> String:
	# The trusted revision-bound frame is an observation, not actor authority.
	# Its newer serial must supersede stale evidence even when this actor is denied.
	var gate := _sample(frame)
	if not _id(actor_id):
		return "invalid_actor"
	if gate != "clear":
		return gate
	if _retired.has(actor_id):
		return "retired"
	for entry in _queue:
		if entry["actor_id"] == actor_id:
			return "already_reserved"
	if _queue.size() >= _slots.size():
		return "full"
	_queue.append({"actor_id": actor_id, "ticket": _next_ticket})
	_next_ticket += 1
	return "reserved"

func release_head(actor_id: Variant, frame: Variant) -> String:
	# The trusted revision-bound frame is an observation, not actor authority.
	# Its newer serial must supersede stale evidence even when this actor is denied.
	var gate := _sample(frame)
	if not _id(actor_id):
		return "invalid_actor"
	if gate != "clear":
		return gate
	if _queue.is_empty() or _queue[0]["actor_id"] != actor_id:
		return "not_head"
	_retired[actor_id] = true
	_queue.pop_front()
	return "released"

func reservations() -> Array:
	# Queue indices are planning destinations only, not actor positions.
	var result: Array = []
	for i in _queue.size():
		result.append({
			"actor_id": _queue[i]["actor_id"], "ticket": _queue[i]["ticket"], "anchor": _slots[i],
		})
	return result

func _sample(frame: Variant) -> String:
	if _layout.is_empty():
		return "unbound"
	if not (frame is Dictionary) or not _id(frame.get("layout_revision")) or frame["layout_revision"] != _layout:
		return "wrong_layout"
	var serial: Variant = frame.get("serial")
	if not (serial is int) or serial <= _last_frame:
		return "stale_observation"
	# For this binding, a newer incomplete/blocked observation supersedes the
	# prior one: retry must never fall back to prior clear evidence.
	_last_frame = serial
	var clear: Variant = frame.get("clear")
	var all_anchors := _ingress + _slots + _exit
	if not (clear is Dictionary) or clear.size() != all_anchors.size():
		return "incomplete_observation"
	var blocked := false
	for anchor in all_anchors:
		var fact: Variant = clear.get(anchor)
		if not (fact is bool):
			return "incomplete_observation"
		if not fact:
			blocked = true
	return "blocked" if blocked else "clear"

static func _id(value: Variant) -> bool:
	return value is String and not value.is_empty() and value.strip_edges() == value
