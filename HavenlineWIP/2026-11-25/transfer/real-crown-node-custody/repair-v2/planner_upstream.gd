extends RefCounted
## Opt-in transfer planning. Does not commit, save, or emit effects.
## Policy and active receiver must come from trusted runtime bindings.

static func _id(value: Variant) -> bool:
	return typeof(value) == TYPE_STRING and not value.is_empty()

static func _count(value: Variant) -> bool:
	return typeof(value) == TYPE_INT and value >= 0

static func project_rows(state: Dictionary, order: Array) -> Array:
	var stock: Variant = state.get("carry")
	if typeof(stock) != TYPE_DICTIONARY or order.size() != 2 or stock.size() != 2:
		return []
	if not _id(order[0]) or not _id(order[1]) or order[0] == order[1]:
		return []
	for material: String in order:
		if not _count(stock.get(material)):
			return []
	return [[order[0], stock[order[0]]], [order[1], stock[order[1]]]]

## Empty result means denied; original dictionaries are not mutated.
## The caller must commit next_state before presenting cue, never on replay.
static func plan_transfer(state: Dictionary, order: Array, policy: Dictionary, active_receiver: String, request: Dictionary) -> Dictionary:
	if project_rows(state, order).is_empty():
		return {}
	var receiver: Variant = request.get("receiver")
	var material: Variant = request.get("material")
	var ticket: Variant = request.get("ticket")
	var units: Variant = request.get("units")
	if not _id(receiver) or not _id(material) or not _id(ticket) or not _count(units):
		return {}
	if receiver != active_receiver or not order.has(material) or units == 0:
		return {}
	var receipts: Variant = state.get("receipts")
	var receivers: Variant = state.get("receivers")
	if typeof(receipts) != TYPE_DICTIONARY or typeof(receivers) != TYPE_DICTIONARY:
		return {}
	if receipts.has(ticket):
		return {}
	var rule: Variant = policy.get(receiver)
	var target: Variant = receivers.get(receiver)
	if typeof(rule) != TYPE_DICTIONARY or typeof(target) != TYPE_DICTIONARY:
		return {}
	if typeof(rule.get("enabled")) != TYPE_BOOL or not rule["enabled"]:
		return {}
	var limits: Variant = rule.get("limits")
	if typeof(limits) != TYPE_DICTIONARY:
		return {}
	var limit: Variant = limits.get(material)
	var current: Variant = target.get(material)
	if not _count(limit) or not _count(current) or current > limit:
		return {}
	# Subtract first, so admitted addition cannot overflow an int64.
	if units > state["carry"][material] or units > limit - current:
		return {}
	var next: Dictionary = state.duplicate(true)
	next["carry"][material] -= units
	next["receivers"][receiver][material] += units
	next["receipts"][ticket] = [receiver, material, units]
	return {"next_state": next, "cue_after_commit": [ticket, receiver, material, units]}
