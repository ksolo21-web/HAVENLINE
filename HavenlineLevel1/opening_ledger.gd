extends RefCounted
const COST := {"wood": 3}
const KNOWN_WOOD := ["wood-a", "wood-b", "wood-c"]
const OFFER := "center-hearth"
var collected: Array[String] = []
var stock := {"wood": 0}
var receipt: Dictionary = {}

static func _whole(value: Variant, n: int) -> bool:
	return (typeof(value) == TYPE_INT or typeof(value) == TYPE_FLOAT) and value == n

func snapshot() -> Dictionary:
	return {"version": 1, "collected": collected.duplicate(), "stock": stock.duplicate(true), "receipt": receipt.duplicate(true)}

func restore(data: Variant) -> bool:
	# Do not mutate any authority until all IDs, typed counts, and receipt agree.
	if not data is Dictionary or data.size() != 4 or not _whole(data.get("version"), 1):
		return false
	var incoming: Variant = data.get("collected")
	var incoming_stock: Variant = data.get("stock")
	var incoming_receipt: Variant = data.get("receipt")
	if not incoming is Array or not incoming_stock is Dictionary or incoming_stock.size() != 1 or not incoming_receipt is Dictionary:
		return false
	var verified: Array[String] = []
	for entry in incoming:
		if not entry is String or entry not in KNOWN_WOOD or entry in verified:
			return false
		verified.append(entry)
	var remaining := verified.size()
	var next_receipt := {}
	if not incoming_receipt.is_empty():
		if incoming_receipt.size() != 4 or incoming_receipt.get("offer") != OFFER or incoming_receipt.get("grant") != OFFER or not _whole(incoming_receipt.get("revision"), 1):
			return false
		var debit: Variant = incoming_receipt.get("typed_debit")
		if not debit is Dictionary or debit.size() != 1 or not _whole(debit.get("wood"), int(COST.wood)):
			return false
		remaining -= int(COST.wood)
		next_receipt = _completed_receipt()
	if remaining < 0 or not _whole(incoming_stock.get("wood"), remaining):
		return false
	collected = verified
	stock = {"wood": remaining}
	receipt = next_receipt
	return true

func _completed_receipt() -> Dictionary:
	return {"offer": OFFER, "typed_debit": COST.duplicate(), "grant": OFFER, "revision": 1}

func collect_wood(source: String) -> bool:
	if source not in KNOWN_WOOD or source in collected:
		return false
	collected.append(source)
	stock.wood += 1
	return true

func pay_center_hearth() -> bool:
	if not receipt.is_empty() or stock.wood < COST.wood:
		return false
	stock.wood -= COST.wood
	receipt = _completed_receipt()
	return true
