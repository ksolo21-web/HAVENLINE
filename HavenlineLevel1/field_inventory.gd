extends RefCounted

const Progress = preload("res://field_progression.gd")
const Settlement = preload("res://field_settlement.gd")
var settlement := Settlement.EMPTY.duplicate(true)
var staged := false
var build_order: Array = []
var legacy_axes := false
var legacy_level2 := false
var world_state := {}

const ORIGINAL_KINDS := ["wood", "stone", "meat"]
const MINERALS := ["coal", "slate", "metal"]
const KINDS := ["wood", "stone", "meat", "coal", "slate", "metal"]
const EMPTY := {"wood":0, "stone":0, "meat":0, "coal":0, "slate":0, "metal":0}
const TITLES := {"wood":"Wood", "stone":"Stone", "meat":"Meat", "coal":"Coal", "slate":"Slate", "metal":"Metal ore"}

var configured_costs := {}
var costs := {}
var legacy_prices: Array = []
var survivor_cost: int:
	get:
		return Progress.OLD_SURVIVOR_BUNDLES if Progress.SURVIVOR in legacy_prices else Progress.SURVIVOR_BUNDLES
var paid := {}
var collected := {}
var carried := EMPTY.duplicate()
var stored := EMPTY.duplicate()

func configure(offers: Dictionary) -> bool:
	if not costs.is_empty() or offers.is_empty():
		return false
	for id in offers:
		if not id is String or id.is_empty() or not offers[id] is Dictionary or offers[id].is_empty():
			return false
		for kind in offers[id]:
			if kind not in KINDS or not _natural(offers[id][kind]) or offers[id][kind] == 0:
				return false
	staged = offers.has(Progress.FIRST)
	if staged and (offers.size() != Progress.PREREQUISITES.size() or not Progress.PREREQUISITES.keys().all(func(id): return offers.has(id))): return false
	configured_costs = offers.duplicate(true)
	costs = offers.duplicate(true)
	for id in costs:
		paid[id] = {}
		for kind in costs[id]:
			paid[id][kind] = 0
	return true

func collect(source_token: String, kind: String) -> bool:
	if source_token.is_empty() or collected.has(source_token) or kind not in KINDS:
		return false
	collected[source_token] = kind
	carried[kind] += 1
	return true

func deposit(kind: String, amount := 1) -> bool:
	if kind not in KINDS or amount <= 0 or carried[kind] < amount or not storage_open(kind):
		return false
	carried[kind] -= amount
	stored[kind] += amount
	return true

func payment(id: String, kind: String, from_storage: bool, amount := 1) -> bool:
	if from_storage and not storage_open(kind): return false
	return _pay_from(stored if from_storage else carried,id,kind,amount)

func worker_payment(id: String, kind: String, amount: int) -> bool:
	if not settlement.rescued or id in Progress.LINES: return false
	return _pay_from(settlement.worker_load,id,kind,amount)

func _pay_from(stock: Dictionary, id: String, kind: String, amount: int) -> bool:
	if amount <= 0 or not offer_open(id) or not costs[id].has(kind) or amount > costs[id][kind] - paid[id][kind]:
		return false
	if stock[kind] < amount:
		return false
	stock[kind] -= amount
	paid[id][kind] += amount
	if staged and complete(id): build_order.append(id)
	return true

func storage_open(kind: String) -> bool:
	if kind not in KINDS: return false
	# The starter shell already has a dedicated FOOD shelf. Historical saves
	# can own the old meat plot independently, so retain that entitlement too.
	if kind == "meat": return not staged or complete("storage_wood") or complete("storage_meat")
	return not staged or complete("storage_stone" if kind in MINERALS else "storage_" + kind)

func is_machine_owned(kind: String) -> bool:
	return Progress.MACHINES.has(kind) and complete(Progress.MACHINES[kind])

func offer_open(id: String) -> bool:
	if not costs.has(id) or complete(id): return false
	if not staged: return true
	# Validate historical receipts against the original independent prerequisites
	# during restore. New payments always fund the first missing house tier.
	if id in Progress.STORAGE and Progress.next_storage(self) != id: return false
	for predecessor in Progress.PREREQUISITES[id]:
		if not complete(predecessor): return false
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
	var state := {"version": 1, "collected": collected.duplicate(), "carried": carried.duplicate(), "stored": stored.duplicate(), "paid": paid.duplicate(true)}
	if staged:
		state.version = 8
		state.legacy_level2 = legacy_level2
		state.legacy_prices = legacy_prices.duplicate()
		state.build_order = build_order.duplicate()
		state.legacy_axes = legacy_axes
		state.world = world_state.duplicate(true)
		state.settlement = settlement.duplicate(true)
	return state

static func _natural(value: Variant) -> bool:
	if typeof(value) != TYPE_INT and typeof(value) != TYPE_FLOAT:
		return false
	return value >= 0 and is_finite(float(value)) and value == int(value)

func restore(data: Variant) -> bool:
	if not data is Dictionary: return false
	var old: bool = data.get("version") == 1
	var version:Variant=data.get("version")
	var current:bool = version==6 or version==7 or version==8
	var has_settlement: bool = current or data.get("version") == 4 or data.get("version") == 5
	if old:
		if data.size() != 5: return false
	elif not staged or (data.get("version") != 2 and data.get("version") != 3 and not has_settlement) or data.size() != (11 if version==7 or version==8 else (10 if current else (9 if has_settlement else 8))):
		return false
	for key in ["collected", "carried", "stored", "paid"]:
		if not data.get(key) is Dictionary:
			return false
	var incoming: Dictionary = data.paid.duplicate(true)
	var order: Array = []
	var old_axes := false
	if staged and old:
		if incoming.size()!=2 or not incoming.has(Progress.HEARTH) or not incoming.has(Progress.AXES): return false
		for id in costs:
			if not incoming.has(id):
				incoming[id]={}
				for kind in costs[id]: incoming[id][kind]=0
	elif staged:
		if not data.get("build_order") is Array or not data.get("world") is Dictionary or not data.get("legacy_axes") is bool: return false
		order=data.build_order.duplicate()
		old_axes=data.legacy_axes
	# In v1–6 expansion exposed equipment for free. Preserve the stock, goods
	# in flight through a hopper, and delivery history, but mint no purchase.
	if staged and not old and int(data.version) < 7:
		for id in Progress.MACHINES.values():
			if incoming.has(id):
				return false
			incoming[id] = {}
			for kind in costs[id]:
				incoming[id][kind] = 0
	if staged and not old and int(data.version) < 8:
		for id: String in Progress.LINES:
			if incoming.has(id): return false
			incoming[id]={}
			for kind: String in costs[id]: incoming[id][kind]=0
	if incoming.size() != costs.size():
		return false
	# Older field saves contain exactly three balances. Expand both tables
	# together, after validating their original keys and conservation.
	var types: Array = KINDS
	if data.version==2 or (old and data.carried.size()==ORIGINAL_KINDS.size()):
		types=ORIGINAL_KINDS
	var balances := EMPTY.duplicate()
	for token in data.collected:
		if not token is String or token.is_empty() or data.collected[token] not in types:
			return false
		balances[data.collected[token]] += 1
	for stock in [data.carried, data.stored]:
		if stock.size() != types.size():
			return false
		for kind in types:
			if not _natural(stock.get(kind)):
				return false
			balances[kind] -= int(stock[kind])
	var restored_costs := configured_costs.duplicate(true)
	var contracts: Array = []
	if current and not data.get("legacy_prices") is Array: return false
	if staged:
		var former := Progress.old_offers()
		for id in restored_costs:
			var submitted: Variant = incoming.get(id)
			if not submitted is Dictionary or not submitted.values().all(_natural): return false
			var started: bool = submitted.values().any(func(n): return n > 0)
			if started and (not current or id in data.legacy_prices):
				if not former.has(id): return false
				contracts.append(id)
				restored_costs[id] = former[id]
		if has_settlement and data.get("settlement") is Dictionary and _natural(data.settlement.get("survivor_wood")) and data.settlement.survivor_wood > 0:
			if not current or Progress.SURVIVOR in data.legacy_prices: contracts.append(Progress.SURVIVOR)
		# A contract can only name a real, already-funded plot once.
		if current and (data.legacy_prices.size() != contracts.size() or not contracts.all(func(id): return id in data.legacy_prices)): return false
	for id in restored_costs:
		var subtotal: Variant = incoming.get(id)
		if not subtotal is Dictionary or subtotal.size() != restored_costs[id].size():
			return false
		for kind in restored_costs[id]:
			if not _natural(subtotal.get(kind)) or subtotal[kind] > restored_costs[id][kind]:
				return false
			balances[kind] -= int(subtotal[kind])
	var next_settlement: Variant = data.get("settlement") if has_settlement else Settlement.EMPTY
	if data.version == 4:
		next_settlement = Settlement.from_legacy(next_settlement)
	if has_settlement and data.version < 7:
		next_settlement = Settlement.from_pre_worker(next_settlement)
	if has_settlement and data.version < 8:
		next_settlement = Settlement.from_pre_conveyors(next_settlement)
	var old_preview := false
	if version==7 or version==8:
		if not data.get("legacy_level2") is bool: return false
		old_preview = data.legacy_level2
	elif has_settlement and next_settlement is Dictionary:
		old_preview = next_settlement.get("level") == 2
	var survivor_due := Progress.OLD_SURVIVOR_BUNDLES if Progress.SURVIVOR in contracts else Progress.SURVIVOR_BUNDLES
	if not Settlement.valid(next_settlement,order,data.collected,survivor_due): return false
	if old_preview and next_settlement.level != 2: return false
	if next_settlement.level == 2 and not old_preview and not Settlement.ready_to_continue(next_settlement,order): return false
	for kind: String in Settlement.KINDS:
		balances[kind] -= int(next_settlement.hoppers[kind]) + int(next_settlement.line_load[kind])
	for kind: String in KINDS:
		balances[kind] -= int(next_settlement.worker_load[kind])
	if next_settlement.worker_supply != "": balances[next_settlement.worker_supply] -= 1
	balances.meat -= int(next_settlement.cooked)
	balances.wood -= int(next_settlement.survivor_wood) + int(next_settlement.processed_wood)
	balances.stone -= int(next_settlement.processed_stone)
	if balances.values().any(func(n): return n != 0):
		return false
	if staged:
		var finished: Array = []
		var funded: Array = []
		for id in restored_costs:
			var full := true
			for kind in restored_costs[id]:
				if int(incoming[id][kind]) > 0 and not funded.has(id): funded.append(id)
				if int(incoming[id][kind]) != int(restored_costs[id][kind]): full=false
			if full: finished.append(id)
		if old:
			order=finished.duplicate()
			old_axes=funded.has(Progress.AXES)
		if order.size()!=finished.size(): return false
		var earlier: Array = []
		for id in order:
			if not finished.has(id) or earlier.has(id): return false
			var required: Array = [Progress.HEARTH] if id==Progress.AXES and old_axes else Progress.PREREQUISITES[id]
			for previous in required:
				if not earlier.has(previous): return false
			earlier.append(id)
		for id in funded:
			var required: Array = [Progress.HEARTH] if id==Progress.AXES and old_axes else Progress.PREREQUISITES[id]
			for previous in required:
				if not finished.has(previous): return false
		if old_axes and not funded.has(Progress.AXES): return false
		costs=restored_costs
		legacy_prices=contracts
		build_order=order
		legacy_axes=old_axes
		legacy_level2=old_preview
		world_state={} if old else data.world.duplicate(true)
		settlement = next_settlement.duplicate(true)
		# JSON numbers are floats. Put validated receipts back in their native
		# integer types so in-memory transactions and reopened snapshots agree.
		for key in Settlement.EMPTY:
			if Settlement.EMPTY[key] is int: settlement[key] = int(settlement[key])
		for kind: String in KINDS:
			settlement.worker_load[kind] = int(settlement.worker_load[kind])
		for lane: String in Settlement.LINE_EMPTY:
			settlement.line_load[lane] = int(settlement.line_load[lane])
			settlement.line_progress[lane] = float(settlement.line_progress[lane])
		for kind: String in Settlement.KINDS:
			settlement.hoppers[kind] = int(settlement.hoppers[kind])
			settlement.work_seconds[kind] = float(settlement.work_seconds[kind])
	collected = data.collected.duplicate()
	for kind in KINDS:
		carried[kind] = int(data.carried.get(kind,0))
		stored[kind] = int(data.stored.get(kind,0))
	for id in costs:
		for kind in costs[id]:
			paid[id][kind] = int(incoming[id][kind])
	return true
