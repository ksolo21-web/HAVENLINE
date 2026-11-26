extends RefCounted
## Receipts produced by Level 1's survivor, kitchen and trading counter.

const LEGACY := {"survivor_paid":false, "survivor_wood":0, "processed_wood":0, "processed_stone":0, "owl_hits":0, "rescued":false, "worker_carry_token":"", "worker_deliveries":0, "worker_receipts":[], "cooked":0, "served":0, "level":1}
const KINDS := ["wood", "stone", "meat"]
const HOPPER_CAPACITY := 4
const ROAST_RACK_CAPACITY := 4
const CYCLE_SECONDS := {"wood":1.45, "stone":1.45, "meat":1.65}
const EMPTY := {
	"survivor_paid":false, "survivor_wood":0, "processed_wood":0, "processed_stone":0,
	"owl_hits":0, "rescued":false, "worker_carry_token":"", "worker_deliveries":0,
	"worker_receipts":[], "cooked":0, "served":0, "level":1,
	"hoppers":{"wood":0, "stone":0, "meat":0},
	"work_seconds":{"wood":0.0, "stone":0.0, "meat":0.0}, "held_meal":0, "worker_supply":"",
}
const MAX_UNITS := 1000000

# An unserved v4 roast was already on the player's hand. Preserve its location.
static func from_legacy(previous: Variant) -> Variant:
	if not previous is Dictionary or previous.size() != LEGACY.size() or not previous.has_all(LEGACY.keys()):
		return null
	if not _count(previous.cooked) or not _count(previous.served):
		return null
	var in_hand := int(previous.cooked) - int(previous.served)
	if in_hand < 0 or in_hand > 1: return null
	var updated: Dictionary = EMPTY.duplicate(true)
	updated.merge(previous.duplicate(true), true)
	updated.held_meal = in_hand
	return updated

static func _count(value: Variant) -> bool:
	return (value is int or value is float) and is_finite(float(value)) and value == int(value) and value >= 0 and value <= MAX_UNITS

static func waiting_meals(state: Dictionary) -> int:
	return int(state.cooked) - int(state.served) - int(state.held_meal)


static func is_wood_drop(token: String) -> bool:
	var suffix := token.trim_prefix("wood-")
	return token.begins_with("wood-") and suffix.is_valid_int() and suffix.to_int() > 0 and suffix == str(suffix.to_int())

static func valid(state: Variant, paid_order: Array, credits: Dictionary, survivor_cost: int) -> bool:
	if not state is Dictionary or state.size() != EMPTY.size():
		return false
	if not state.get("survivor_paid") is bool or not state.get("rescued") is bool or not state.get("worker_carry_token") is String:
		return false
	for key in ["worker_deliveries", "cooked", "served", "level", "survivor_wood", "processed_wood", "processed_stone", "owl_hits", "held_meal"]:
		var value: Variant = state.get(key)
		if not _count(value):
			return false
	if (state.level != 1 and state.level != 2) or state.held_meal > 1 or waiting_meals(state) < 0 or waiting_meals(state) > ROAST_RACK_CAPACITY:
		return false
	for column in ["hoppers","work_seconds"]:
		if not state.get(column) is Dictionary or state[column].size() != KINDS.size() or not state[column].has_all(KINDS):
			return false
	for kind: String in KINDS:
		var units: Variant = state.hoppers[kind]
		var elapsed: Variant = state.work_seconds[kind]
		if not _count(units) or units > HOPPER_CAPACITY: return false
		if not (elapsed is float or elapsed is int) or not is_finite(float(elapsed)) or elapsed < 0 or elapsed > CYCLE_SECONDS[kind]: return false
		if units == 0 and elapsed != 0: return false
		if units > 0 and "expansion_2" not in paid_order: return false
	if not state.get("worker_supply") is String or (state.worker_supply != "" and (
			state.worker_supply not in KINDS or not state.rescued or "expansion_2" not in paid_order or state.worker_carry_token != "")):
		return false
	if state.survivor_wood > survivor_cost or state.survivor_paid != (state.survivor_wood == survivor_cost): return false
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
