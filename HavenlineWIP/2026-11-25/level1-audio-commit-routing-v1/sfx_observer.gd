extends "res://tests/fixture_integrated_disposable_opening.gd"
## Copies route memory, never mutates ledger, mixer, or authoritative scene.
var sfx_muted := false
var accepted_cues: Array[String] = []
var mixer_intents: Array[String] = []
var delivered: Dictionary = {}
var adapter_failures := 0

func _commit_opening_progress(next: Ledger) -> bool:
	var before := ledger.snapshot()
	if not super._commit_opening_progress(next):
		return false
	var after := ledger.snapshot()
	var key := classify_transition(before, after)
	if key.is_empty() or delivered.has(key):
		adapter_failures += 1
		return true
	delivered[key] = true
	accepted_cues.append(key)
	if not sfx_muted:
		mixer_intents.append(key)
	return true

static func classify_transition(before: Dictionary, after: Dictionary) -> String:
	if before.version != 1 or after.version != 1:
		return ""
	if before.receipt == after.receipt and before.receipt.is_empty() and after.stock.wood == before.stock.wood + 1 and after.collected.size() == before.collected.size() + 1:
		var key := String(after.collected[-1])
		if key in Ledger.KNOWN_WOOD and not key in before.collected and before.collected == after.collected.slice(0, -1):
			return "wood_pickup:" + key
	if before.receipt.is_empty() and before.collected == after.collected and before.stock.wood - after.stock.wood == int(Ledger.COST.wood) and after.receipt.get("offer") == Ledger.OFFER and after.receipt.get("grant") == Ledger.OFFER and after.receipt.get("revision") == 1 and after.receipt.get("typed_debit") == Ledger.COST:
		return "hearth_build:center-hearth:1"
	return ""
