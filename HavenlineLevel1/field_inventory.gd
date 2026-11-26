extends RefCounted

const KINDS := ["wood", "stone", "meat"]
const MAX_COUNT := 1000000

var costs := {}
var paid := {}
var collected := {}
var carried := {"wood": 0, "stone": 0, "meat": 0}
var stored := {"wood": 0, "stone": 0, "meat": 0}

func configure(offers: Dictionary) -> bool:
	if not costs.is_empty() or offers.is_empty():
		return false
	for id in offers:
		if not id is String or id.is_empty() or not offers[id] is Dictionary or offers[id].is_empty():
			return false
		for kind in offers[id]:
			if kind not in KINDS or not _natural(offers[id][kind]) or offers[id][kind] == 0:
				return false
	costs = offers.duplicate(true)
	for id in costs:
		paid[id] = {}
		for kind in costs[id]:
			paid[id][kind] = 0
	return true

func collect(source_token: String, kind: String) -> bool:
	if source_token.is_empty() or collected.has(source_token) or kind not in KINDS or collected.size() >= MAX_COUNT:
		return false
	collected[source_token] = kind
	carried[kind] += 1
	return true

func deposit(kind: String) -> bool:
	if kind not in KINDS or carried[kind] == 0:
		return false
	carried[kind] -= 1
	stored[kind] += 1
	return true

func payment(id: String, kind: String, from_storage: bool) -> bool:
	if not costs.has(id) or not costs[id].has(kind) or paid[id][kind] >= costs[id][kind]:
		return false
	var stock := stored if from_storage else carried
	if stock[kind] == 0:
		return false
	stock[kind] -= 1
	paid[id][kind] += 1
	return true

func remaining(id: String) -> Dictionary:
	var result := {}
	for kind in costs.get(id, {}):
		result[kind] = int(costs[id][kind]) - int(paid[id][kind])
	return result

func complete(id: String) -> bool:
	if not costs.has(id):
		return false
	for count in remaining(id).values():
		if count > 0:
			return false
	return true

func snapshot() -> Dictionary:
	return {"version": 1, "collected": collected.duplicate(), "carried": carried.duplicate(), "stored": stored.duplicate(), "paid": paid.duplicate(true)}

static func _natural(value: Variant) -> bool:
	if typeof(value) != TYPE_INT and typeof(value) != TYPE_FLOAT:
		return false
	return value >= 0 and value <= MAX_COUNT and value == int(value)

func restore(data: Variant) -> bool:
	if not data is Dictionary or data.size() != 5 or data.get("version") != 1:
		return false
	for key in ["collected", "carried", "stored", "paid"]:
		if not data.get(key) is Dictionary:
			return false
	if data.collected.size() > MAX_COUNT or data.paid.size() != costs.size():
		return false
	var balances := {"wood": 0, "stone": 0, "meat": 0}
	for token in data.collected:
		if not token is String or token.is_empty() or data.collected[token] not in KINDS:
			return false
		balances[data.collected[token]] += 1
	for stock in [data.carried, data.stored]:
		if stock.size() != KINDS.size():
			return false
		for kind in KINDS:
			if not _natural(stock.get(kind)):
				return false
			balances[kind] -= int(stock[kind])
	for id in costs:
		var subtotal: Variant = data.paid.get(id)
		if not subtotal is Dictionary or subtotal.size() != costs[id].size():
			return false
		for kind in costs[id]:
			if not _natural(subtotal.get(kind)) or subtotal[kind] > costs[id][kind]:
				return false
			balances[kind] -= int(subtotal[kind])
	if balances.values().any(func(n): return n != 0):
		return false
	collected = data.collected.duplicate()
	for kind in KINDS:
		carried[kind] = int(data.carried[kind])
		stored[kind] = int(data.stored[kind])
	for id in costs:
		for kind in costs[id]:
			paid[id][kind] = int(data.paid[id][kind])
	return true
