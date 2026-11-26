extends RefCounted
## Receipts produced by Level 1's survivor, kitchen and trading counter.

const EMPTY := {"survivor_paid":false, "survivor_wood":0, "processed_wood":0, "processed_stone":0, "owl_hits":0, "rescued":false, "worker_carry_token":"", "worker_deliveries":0, "worker_receipts":[], "cooked":0, "served":0, "level":1}
const MAX_UNITS := 1000000

static func is_wood_drop(token: String) -> bool:
	var suffix := token.trim_prefix("wood-")
	return token.begins_with("wood-") and suffix.is_valid_int() and suffix.to_int() > 0 and suffix == str(suffix.to_int())

static func valid(state: Variant, paid_order: Array, credits: Dictionary) -> bool:
	if not state is Dictionary or state.size() != EMPTY.size():
		return false
	if not state.get("survivor_paid") is bool or not state.get("rescued") is bool or not state.get("worker_carry_token") is String:
		return false
	for key in ["worker_deliveries", "cooked", "served", "level", "survivor_wood", "processed_wood", "processed_stone", "owl_hits"]:
		var value: Variant = state.get(key)
		if not (value is int or value is float) or not is_finite(float(value)) or value != int(value) or value < 0 or value > MAX_UNITS:
			return false
	if (state.level != 1 and state.level != 2) or state.cooked < state.served or state.cooked - state.served > 1:
		return false
	if state.survivor_wood > 2 or state.survivor_paid != (state.survivor_wood == 2): return false
	if state.survivor_wood > 0 and "center_hearth" not in paid_order: return false
	if state.rescued and not state.survivor_paid: return false
	if state.owl_hits > 0 and not state.survivor_paid: return false
	if (state.processed_wood > 0 or state.processed_stone > 0) and "expansion_2" not in paid_order: return false
	if state.cooked > 0 and "expansion_2" not in paid_order: return false
	if not state.get("worker_receipts") is Array or state.worker_receipts.size() != state.worker_deliveries:
		return false
	if state.worker_deliveries > 0 or state.worker_carry_token != "":
		if not state.rescued or "storage_wood" not in paid_order: return false
	if state.worker_carry_token != "" and (not is_wood_drop(state.worker_carry_token) or credits.has(state.worker_carry_token)):
		return false
	var unique := {}
	for id in state.worker_receipts:
		if not id is String or not is_wood_drop(id) or unique.has(id) or credits.get(id) != "wood": return false
		unique[id] = true
	return state.level == 1 or ready_to_continue(state,paid_order)

static func ready_to_continue(state: Dictionary, paid_order: Array) -> bool:
	return state.rescued and state.worker_deliveries > 0 and state.served > 0 and state.processed_wood > 0 and state.processed_stone > 0 and state.owl_hits > 0 and paid_order.size() == 8
