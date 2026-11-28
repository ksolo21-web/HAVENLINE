extends RefCounted
## Reusable authoritative planning/quote logic. No scene, actor spawning or game approval.
## Quantities are logical units, never mesh counts. Callers persist the combined
## economy/custody snapshot atomically when a contribution or sale is committed.

const MAX_QUANTITY: int = 9007199254740991
var _catalog: Dictionary = {}
var _seed: int = 1
var _quotes: Dictionary = {}
var _requests: Dictionary = {}
var _counter_slots: Dictionary = {}
var _retirements: Dictionary = {}
var _retirement_authority_id: String = ""
var _retirement_authority: RefCounted
var _retirement_custodies: Dictionary = {}
var _pending_retirement: Dictionary = {}

func _no(reason: String, detail: Variant = null) -> Dictionary:
	return {"ok": false, "reason": reason, "detail": detail}

func _count(value: Variant) -> bool:
	return (typeof(value) == TYPE_INT or typeof(value) == TYPE_FLOAT) and is_finite(float(value)) and float(value) >= 0.0 and float(value) <= MAX_QUANTITY and float(value) == floor(float(value))

func _goods(value: Variant, allow_empty: bool = false) -> bool:
	if not value is Dictionary or (value.is_empty() and not allow_empty): return false
	for key in value:
		if not key is String or key.is_empty() or not _count(value[key]): return false
	return true

func _integers(value: Dictionary) -> Dictionary:
	var result: Dictionary = {}
	for key in value:
		if int(value[key]) > 0: result[key] = int(value[key])
	return result

func _fingerprint(value: Variant) -> String:
	return JSON.stringify(_canonical(value), "", true).sha256_text()

func _canonical(value: Variant) -> Variant:
	if value is Dictionary:
		var result: Dictionary = {}
		for key in value: result[key] = _canonical(value[key])
		return result
	if value is Array:
		var result: Array = []
		for element in value: result.append(_canonical(element))
		return result
	if typeof(value) == TYPE_FLOAT and is_finite(value) and abs(value) <= MAX_QUANTITY and value == floor(value): return int(value)
	return value

func configure(catalog: Dictionary, world_seed: int = 1) -> Dictionary:
	if not _catalog.is_empty(): return _no("already_configured")
	if not catalog.get("items") is Dictionary or not catalog.get("recipes", {}) is Dictionary or not catalog.get("plots", {}) is Dictionary:
		return _no("invalid_catalog")
	if str(catalog.get("version", "")).is_empty(): return _no("missing_catalog_version")
	for id in catalog.items:
		if not id is String or not catalog.items[id] is Dictionary: return _no("invalid_item")
		if catalog.items[id].has("processed") and not catalog.items[id].processed is bool: return _no("invalid_processed_classification", id)
		if not _count(catalog.items[id].get("unit_price", 0)): return _no("invalid_unit_price", id)
	for output in catalog.get("recipes", {}):
		if not catalog.recipes[output] is Dictionary: return _no("invalid_recipe", output)
		var recipe: Dictionary = catalog.recipes[output]
		if not catalog.items.has(output) or not _goods(recipe.get("inputs")) or not _count(recipe.get("output", 0)) or int(recipe.output) < 1:
			return _no("invalid_recipe", output)
		for input in recipe.inputs:
			if not catalog.items.has(input): return _no("unknown_recipe_input", input)
	for id in catalog.get("plots", {}):
		if not catalog.plots[id] is Dictionary: return _no("invalid_plot", id)
		var plot: Dictionary = catalog.plots[id]
		if not _goods(plot.get("base_cost", {}), true): return _no("invalid_plot_cost", id)
		for field in ["base_cost", "per_band", "per_tier"]:
			if not _goods(plot.get(field, {}), true): return _no("invalid_plot_cost", id)
			for item in plot.get(field, {}):
				if not catalog.items.has(item): return _no("unknown_plot_material", item)
		for row in plot.get("cost_rows", []):
			if not row is Dictionary or not _count(row.get("min_band")) or not _goods(row.get("cost")): return _no("invalid_cost_row", id)
			for item in row.cost:
				if not catalog.items.has(item): return _no("unknown_plot_material", item)
	for template in catalog.get("customer_templates", []):
		if not template is Dictionary or not _goods(template.get("items")) or not _goods(template.get("per_band", {}), true): return _no("invalid_customer_template")
		for item in template.get("per_band", {}):
			if not template.items.has(item): return _no("unbound_template_increment", item)
	_catalog = catalog.duplicate(true)
	_seed = world_seed
	return {"ok": true, "catalog_version": str(_catalog.version)}

func bind_retirement_authority(authority: RefCounted, custody: RefCounted) -> Dictionary:
	# Integration-only binding, established by the trusted world initializer.
	# Retirement itself accepts no caller-supplied world dictionary or flag.
	if _catalog.is_empty() or authority == null or custody == null: return _no("missing_retirement_authority")
	for method in ["retirement_authority_id", "capture_economy_snapshot", "validate_economy_snapshot"]:
		if not authority.has_method(method): return _no("invalid_retirement_authority")
	for method in ["customer_retirement_view", "bind_retirement_owner", "retire_unpaid_quote"]:
		if not custody.has_method(method): return _no("invalid_retirement_custody")
	var id: String = str(authority.retirement_authority_id())
	if id.is_empty() or (not _retirement_authority_id.is_empty() and id != _retirement_authority_id): return _no("retirement_authority_identity_mismatch")
	if _retirement_authority != null and _retirement_authority != authority: return _no("retirement_authority_already_bound")
	var view: Dictionary = custody.customer_retirement_view("")
	if not view.get("ok", false): return view
	var counter_id: String = str(view.counter_id)
	if _retirement_custodies.has(counter_id) and _retirement_custodies[counter_id] != custody: return _no("retirement_custody_already_bound")
	var bound: Dictionary = custody.bind_retirement_owner(self)
	if not bound.get("ok", false): return bound
	_retirement_authority = authority
	_retirement_authority_id = id
	_retirement_custodies[counter_id] = custody
	return {"ok": true, "authority_id": id, "counter_id": counter_id}

func validate_retirement_intent(intent: Dictionary, custody: RefCounted) -> bool:
	return not _pending_retirement.is_empty() and intent == _pending_retirement and _retirement_custodies.get(intent.get("counter_id")) == custody

func retire_unobtainable_customer(offer_key: String, tx_id: String) -> Dictionary:
	if tx_id.is_empty(): return _no("missing_retirement_transaction")
	if _requests.has(tx_id): return _no("request_id_payload_mismatch")
	var signature: String = _fingerprint([offer_key])
	if _retirements.has(tx_id):
		if _retirements[tx_id].signature != signature: return _no("request_id_payload_mismatch")
		var replay: Dictionary = _retirements[tx_id].receipt.duplicate(true)
		replay["replayed"] = true
		return replay
	if not _quotes.has(offer_key) or _quotes[offer_key].kind != "customer": return _no("unknown_customer_quote")
	var quote: Dictionary = _quotes[offer_key]
	if quote.status not in ["OPEN", "PAUSED"] or not quote.paid.is_empty(): return _no("customer_quote_already_final")
	if _retirement_authority == null or not _retirement_custodies.has(quote.target): return _no("retirement_authority_not_bound")
	var custody: RefCounted = _retirement_custodies[quote.target]
	var view: Dictionary = custody.customer_retirement_view(offer_key)
	if not view.get("ok", false): return view
	if view.get("settled", false) or view.get("retired", false): return _no("custody_quote_already_final")
	# A whole reserved basket already exists, independent of depleted inputs.
	# It must complete or return normally; it cannot justify a price reroll.
	if not view.get("reserved_items", {}).is_empty(): return _no("reserved_basket_is_already_obtainable")
	var captured: Variant = _retirement_authority.capture_economy_snapshot()
	if not captured is Dictionary: return _no("invalid_authoritative_snapshot")
	var captured_copy: Dictionary = _canonical(captured).duplicate(true)
	if captured_copy.get("authority_id") != _retirement_authority_id or not _count(captured_copy.get("revision")) or not captured_copy.get("world") is Dictionary: return _no("invalid_authoritative_snapshot")
	var world: Dictionary = captured_copy.world.duplicate(true)
	# All stock inside the custody component comes from its actual ledger.
	# The adapter may supply disjoint external inventory, never a duplicate
	# aggregate inventory containing these same counter/actor/storage items.
	if not world.get("inventory", {}) is Dictionary or not world.get("inventory", {}).is_empty(): return _no("ambiguous_retirement_inventory_use_external_inventory")
	if not _goods(world.get("external_inventory", {}), true) or not _goods(world.get("reserved", {}), true): return _no("invalid_authoritative_inventory")
	for field in ["sources", "plots", "rebuild_costs"]:
		if not world.get(field, {}) is Dictionary: return _no("invalid_authoritative_world", field)
	for field in ["tools", "unlocks", "available_plots"]:
		if not world.get(field, []) is Array: return _no("invalid_authoritative_world", field)
	if not _count(world.get("level", 1)) or int(world.get("level", 1)) < 1: return _no("invalid_authoritative_level")
	world.inventory = _integers(world.get("external_inventory", {}))
	for item in view.inventory:
		if int(world.inventory.get(item, 0)) > MAX_QUANTITY - int(view.inventory[item]): return _no("quantity_overflow")
		world.inventory[item] = int(world.inventory.get(item, 0)) + int(view.inventory[item])
	var proof: Dictionary = prove(quote.items, world)
	if proof.ok: return _no("customer_basket_still_obtainable", proof)
	var unavailable_reasons: Array = ["insufficient_reachable_source", "missing_recipe_tool", "locked_item", "locked_recipe", "locked_producer", "plot_not_currently_purchasable", "unreachable_producer", "required_producer_upgrade_not_available", "producer_output_cannot_fit_one_cycle", "dependency_cycle"]
	if proof.reason not in unavailable_reasons: return _no("invalid_proof_is_not_infeasibility", proof)
	# No awaits: revalidate source revision and custody just before committing
	# both retirement records. The parent persists both owners atomically.
	if not _retirement_authority.validate_economy_snapshot(captured_copy): return _no("authoritative_snapshot_changed")
	var current_view: Dictionary = custody.customer_retirement_view(offer_key)
	if not current_view.get("ok", false) or current_view.revision != view.revision: return _no("custody_changed_during_retirement")
	_pending_retirement = {"quote_id": offer_key, "counter_id": str(quote.target), "target_generation": int(quote.target_generation), "ordinal": int(quote.identity.ordinal), "items": quote.items.duplicate(true), "payout": int(quote.payout), "expected_custody_revision": str(view.revision), "authority_id": _retirement_authority_id, "source_revision": int(captured_copy.revision), "source_snapshot_hash": _fingerprint(captured_copy), "failure_reason": str(proof.reason), "transaction_id": tx_id}
	var cancelled: Dictionary = custody.retire_unpaid_quote(self, _pending_retirement.duplicate(true), "quote-retirement:" + tx_id)
	_pending_retirement.clear()
	if not cancelled.get("ok", false): return cancelled
	quote.status = "RETIRED"
	quote["retirement_transaction_id"] = tx_id
	var receipt: Dictionary = {"ok": true, "kind": "customer_quote_retired", "id": tx_id, "quote_id": offer_key, "counter_id": str(quote.target), "target_generation": int(quote.target_generation), "ordinal": int(quote.identity.ordinal), "items": quote.items.duplicate(true), "promised_payout": int(quote.payout), "cash_created": 0, "returned_items": cancelled.get("returned_items", {}).duplicate(true), "custody_receipt": cancelled.duplicate(true), "authority_id": _retirement_authority_id, "source_revision": int(captured_copy.revision), "source_snapshot_hash": _fingerprint(captured_copy), "failure_reason": str(proof.reason), "committed": true}
	_retirements[tx_id] = {"signature": signature, "receipt": receipt.duplicate(true)}
	return receipt.duplicate(true)

func _band(world: Dictionary) -> int:
	return clampi((maxi(1, int(world.get("level", 1))) - 1) / 10, 0, 9)

func _unlocked(definition: Dictionary, world: Dictionary) -> bool:
	if int(world.get("level", 1)) < int(definition.get("min_level", 1)): return false
	for flag in definition.get("unlocks", []):
		if flag not in world.get("unlocks", []): return false
	return true

func _bill(plot_id: String, tier: int, world: Dictionary) -> Dictionary:
	if not _catalog.get("plots", {}).has(plot_id): return _no("unknown_plot", plot_id)
	var definition: Dictionary = _catalog.plots[plot_id]
	var bill: Dictionary = definition.get("base_cost", {}).duplicate(true)
	var band: int = _band(world)
	var chosen_band: int = -1
	for row in definition.get("cost_rows", []):
		if int(row.min_band) <= band and int(row.min_band) > chosen_band:
			bill = row.cost.duplicate(true)
			chosen_band = int(row.min_band)
	# Authored increments; never read wealth, purchase history, VIP or current stock.
	for field in ["per_band", "per_tier"]:
		var factor: int = band if field == "per_band" else maxi(0, tier - 1)
		for item in definition.get(field, {}):
			if int(definition[field][item]) > 0 and factor > MAX_QUANTITY / int(definition[field][item]): return _no("quantity_overflow")
			var addition: int = int(definition[field][item]) * factor
			if addition < 0 or int(bill.get(item, 0)) > MAX_QUANTITY - addition: return _no("quantity_overflow")
			bill[item] = int(bill.get(item, 0)) + addition
	if not _goods(bill): return _no("invalid_generated_bill", plot_id)
	return {"ok": true, "items": _integers(bill)}

func _ensure_plot(id: String, state: Dictionary, world: Dictionary) -> Dictionary:
	if not _catalog.get("plots", {}).has(id): return _no("unknown_producer", id)
	var definition: Dictionary = _catalog.plots[id]
	if not _unlocked(definition, world): return _no("locked_producer", id)
	var live: Dictionary = state.plots.get(id, {})
	if live.get("reachable", true) == false: return _no("unreachable_producer", id)
	var furnace: String = str(world.get("furnace_id", "center_hearth"))
	var token: String = "plot:" + id
	if state.visiting.has(token): return _no("dependency_cycle", token)
	state.visiting[token] = true
	if bool(definition.get("requires_furnace", false)) and bool(state.blackout):
		if id == furnace:
			state.visiting.erase(token)
			return _no("furnace_self_dependency")
		var restored: Dictionary = _ensure_plot(furnace, state, world)
		if not restored.ok:
			state.visiting.erase(token)
			return restored
	for predecessor in definition.get("requires", []):
		var prerequisite: Dictionary = _ensure_plot(str(predecessor), state, world)
		if not prerequisite.ok:
			state.visiting.erase(token)
			return prerequisite
	if live.get("owned", false) and live.get("operational", false) and int(live.get("hp", 1)) > 0:
		if id == furnace: state.blackout = false
		state.visiting.erase(token)
		return {"ok": true}
	if id not in world.get("available_plots", []):
		state.visiting.erase(token)
		return _no("plot_not_currently_purchasable", id)
	var cost: Dictionary = _bill(id, 1, world)
	if world.get("rebuild_costs", {}).has(id):
		var recovery: Variant = world.rebuild_costs[id]
		cost = {"ok": true, "items": _integers(recovery)} if _goods(recovery) else _no("invalid_rebuild_bill")
	if not cost.ok:
		state.visiting.erase(token)
		return cost
	var items: Array = cost.items.keys()
	items.sort()
	for item in items:
		var paid: Dictionary = _fulfill(str(item), int(cost.items[item]), state, world)
		if not paid.ok:
			state.visiting.erase(token)
			return paid
	state.plots[id] = {"owned": true, "operational": true, "reachable": true, "hp": 1, "tier": 1, "generation": int(live.get("generation", 0)) + 1}
	state.steps.append({"action": "rebuild_producer" if live.get("owned", false) else "buy_producer", "plot": id, "cost": cost.items.duplicate(true), "result_tier": 1})
	if id == furnace: state.blackout = false
	state.visiting.erase(token)
	return {"ok": true}

func _fulfill(item: String, amount: int, state: Dictionary, world: Dictionary) -> Dictionary:
	if amount <= 0: return {"ok": true}
	if not _catalog.items.has(item): return _no("unknown_item", item)
	if not _unlocked(_catalog.items[item], world): return _no("locked_item", item)
	var token: String = "item:" + item
	if state.visiting.has(token): return _no("dependency_cycle", token)
	var available: int = int(state.stock.get(item, 0))
	var from_stock: int = mini(available, amount)
	state.stock[item] = available - from_stock
	var remaining: int = amount - from_stock
	if remaining == 0:
		state.steps.append({"action": "use_owned_stock", "item": item, "quantity": from_stock})
		return {"ok": true}
	state.visiting[token] = true
	var source: Dictionary = state.sources.get(item, {})
	if not source.is_empty() and source.get("reachable", false) and _unlocked(source, world):
		var tool: String = str(source.get("tool", ""))
		if tool.is_empty() or tool in world.get("tools", []):
			var offered: int = remaining if source.get("renewable", false) else mini(remaining, int(source.get("quantity", 0)))
			if offered > 0:
				if not source.get("renewable", false): source.quantity = int(source.quantity) - offered
				state.steps.append({"action": "manual_acquire", "item": item, "quantity": offered, "source": str(source.get("id", item)), "tool": tool})
				remaining -= offered
	if remaining > 0 and _catalog.get("recipes", {}).has(item):
		var recipe: Dictionary = _catalog.recipes[item]
		if not _unlocked(recipe, world):
			state.visiting.erase(token)
			return _no("locked_recipe", item)
		var tool: String = str(recipe.get("tool", ""))
		if not tool.is_empty() and tool not in world.get("tools", []):
			state.visiting.erase(token)
			return _no("missing_recipe_tool", tool)
		var producer: String = str(recipe.get("producer", ""))
		if not producer.is_empty():
			var ready: Dictionary = _ensure_plot(producer, state, world)
			if not ready.ok:
				state.visiting.erase(token)
				return ready
			if int(state.plots[producer].get("tier", 1)) < int(recipe.get("producer_tier", 1)):
				state.visiting.erase(token)
				return _no("required_producer_upgrade_not_available", producer)
		var per_cycle: int = int(recipe.output)
		var cycles: int = remaining / per_cycle
		if remaining % per_cycle > 0: cycles += 1
		var capacity: int = int(recipe.get("output_capacity", per_cycle))
		if capacity < per_cycle:
			state.visiting.erase(token)
			return _no("producer_output_cannot_fit_one_cycle", item)
		var inputs: Array = recipe.inputs.keys()
		inputs.sort()
		for input in inputs:
			var quantity: int = int(recipe.inputs[input])
			if quantity > 0 and cycles > MAX_QUANTITY / quantity:
				state.visiting.erase(token)
				return _no("quantity_overflow")
			var obtained: Dictionary = _fulfill(str(input), quantity * cycles, state, world)
			if not obtained.ok:
				state.visiting.erase(token)
				return obtained
		if cycles > MAX_QUANTITY / per_cycle:
			state.visiting.erase(token)
			return _no("quantity_overflow")
		state.stock[item] = int(state.stock.get(item, 0)) + cycles * per_cycle - remaining
		state.steps.append({"action": "produce_and_collect", "item": item, "cycles": cycles, "quantity": cycles * per_cycle, "producer": producer, "output_capacity": capacity})
		remaining = 0
	state.visiting.erase(token)
	if remaining > 0: return _no("insufficient_reachable_source", {"item": item, "missing": remaining})
	return {"ok": true}

func prove(requested_items: Dictionary, world: Dictionary) -> Dictionary:
	if _catalog.is_empty() or not _goods(requested_items): return _no("invalid_request")
	if not _goods(world.get("inventory", {}), true) or not _goods(world.get("reserved", {}), true): return _no("invalid_world_stock")
	var stock: Dictionary = _integers(world.get("inventory", {}))
	for item in world.get("reserved", {}):
		if int(world.reserved[item]) > int(stock.get(item, 0)): return _no("reservation_exceeds_stock", item)
		stock[item] = int(stock.get(item, 0)) - int(world.reserved[item])
	for item in world.get("sources", {}):
		var source: Variant = world.sources[item]
		if not source is Dictionary or not _count(source.get("quantity", 0)): return _no("invalid_source", item)
	var state: Dictionary = {"stock": stock, "sources": world.get("sources", {}).duplicate(true), "plots": world.get("plots", {}).duplicate(true), "steps": [], "visiting": {}, "blackout": bool(world.get("blackout", false))}
	var ordered: Array = requested_items.keys()
	ordered.sort()
	for item in ordered:
		var result: Dictionary = _fulfill(str(item), int(requested_items[item]), state, world)
		if not result.ok:
			result["completed_prefix"] = state.steps.duplicate(true)
			return result
	return {"ok": true, "steps": state.steps.duplicate(true), "remaining_stock": state.stock.duplicate(true), "requested": _integers(requested_items), "uses_order_reward": false}

func _existing(key: String, identity: Dictionary) -> Dictionary:
	if not _quotes.has(key): return {}
	if _quotes[key].identity != identity: return _no("quote_key_reused_with_different_target")
	return {"ok": true, "replayed": true, "quote": _quotes[key].duplicate(true)}

func _store_quote(key: String, identity: Dictionary, items: Dictionary, payout: int, world: Dictionary, proof: Dictionary) -> Dictionary:
	var quote: Dictionary = {"id": key, "identity": identity.duplicate(true), "kind": identity.kind, "target": identity.target, "target_generation": int(identity.get("generation", 0)), "catalog_version": str(_catalog.version), "seed": _seed, "progression_level": int(world.get("level", 1)), "band": _band(world), "items": _integers(items), "payout": payout, "paid": {}, "status": "OPEN", "proof": proof.duplicate(true)}
	_quotes[key] = quote
	return {"ok": true, "quote": quote.duplicate(true)}

func quote_customer(offer_key: String, counter_id: String, ordinal: int, world: Dictionary) -> Dictionary:
	if offer_key.is_empty() or counter_id.is_empty() or ordinal < 0: return _no("invalid_offer_identity")
	var identity: Dictionary = {"kind": "customer", "target": counter_id, "ordinal": ordinal, "generation": int(world.get("counter_generation", 1))}
	var existing: Dictionary = _existing(offer_key, identity)
	if not existing.is_empty(): return existing
	if bool(world.get("blackout", false)): return _no("blackout_no_new_customers")
	if _counter_slots.has(counter_id):
		var old: Dictionary = _quotes[_counter_slots[counter_id]]
		if old.status not in ["SETTLED", "RETIRED"]: return _no("active_offer_slot_locked", old.id)
		if ordinal != int(old.identity.ordinal) + 1: return _no("offer_ordinal_must_be_next")
	elif ordinal != 0: return _no("initial_offer_ordinal_must_be_zero")
	var eligible: Array = []
	for template in _catalog.get("customer_templates", []):
		if _band(world) < int(template.get("min_band", 0)) or _band(world) > int(template.get("max_band", 9)): continue
		var basket: Dictionary = template.get("items", {}).duplicate(true)
		if not _goods(basket): continue
		var valid: bool = true
		for item in basket:
			if not _catalog.items.has(item) or not _catalog.items[item].get("processed", false): valid = false
			var increment: int = int(template.get("per_band", {}).get(item, 0)) * _band(world)
			if increment < 0 or int(basket[item]) > MAX_QUANTITY - increment: valid = false
			basket[item] = int(basket[item]) + increment
		if not valid: continue
		var proof: Dictionary = prove(basket, world)
		if proof.ok: eligible.append({"items": basket, "proof": proof})
	if eligible.is_empty(): return _no("no_obtainable_processed_basket")
	var chosen: int = posmod((str(_seed) + ":" + counter_id + ":" + str(ordinal)).hash(), eligible.size())
	var basket: Dictionary = eligible[chosen].items
	var payout: int = 0
	for item in basket:
		var price: int = int(_catalog.items[item].get("unit_price", 0))
		if price <= 0 or int(basket[item]) > MAX_QUANTITY / price: return _no("invalid_sale_value", item)
		var value: int = int(basket[item]) * price
		if payout > MAX_QUANTITY - value: return _no("quantity_overflow")
		payout += value
	var stored: Dictionary = _store_quote(offer_key, identity, basket, payout, world, eligible[chosen].proof)
	_counter_slots[counter_id] = offer_key
	return stored

func quote_project(offer_key: String, plot_id: String, target_tier: int, target_generation: int, world: Dictionary) -> Dictionary:
	if offer_key.is_empty() or target_tier < 1 or target_tier > MAX_QUANTITY or target_generation < 1: return _no("invalid_project_identity")
	var identity: Dictionary = {"kind": "project", "target": plot_id, "tier": target_tier, "generation": target_generation}
	var existing: Dictionary = _existing(offer_key, identity)
	if not existing.is_empty(): return existing
	var active: int = 0
	for quote in _quotes.values():
		if quote.kind == "project" and quote.identity == identity: return _no("target_obligation_already_quoted", quote.id)
		if quote.kind == "project" and quote.status != "COMPLETE": active += 1
	if active >= int(_catalog.get("max_project_quotes", 3)): return _no("active_project_limit")
	if not _catalog.get("plots", {}).has(plot_id) or not _unlocked(_catalog.plots[plot_id], world): return _no("locked_or_unknown_project")
	if plot_id not in world.get("available_plots", []): return _no("plot_not_currently_purchasable")
	var bill: Dictionary = _bill(plot_id, target_tier, world)
	if not bill.ok: return bill
	# A new plot cannot rely on its own future output. An existing lower tier
	# may supply an upgrade only with recipes that it already operates.
	var probe: Dictionary = world.duplicate(true)
	probe["available_plots"] = world.get("available_plots", []).duplicate()
	probe.available_plots.erase(plot_id)
	probe["plots"] = world.get("plots", {}).duplicate(true)
	if target_tier <= 1: probe.plots.erase(plot_id)
	elif int(probe.plots.get(plot_id, {}).get("tier", 0)) >= target_tier: return _no("upgrade_already_owned")
	var proof: Dictionary = prove(bill.items, probe)
	if not proof.ok: return _no("unobtainable_project_bill", proof)
	return _store_quote(offer_key, identity, bill.items, 0, world, proof)

func revalidate_quote(offer_key: String, world: Dictionary) -> Dictionary:
	if not _quotes.has(offer_key): return _no("unknown_quote")
	var quote: Dictionary = _quotes[offer_key]
	if quote.status == "RETIRED": return _no("customer_quote_retired")
	if quote.status in ["COMPLETE", "SETTLED"]: return {"ok": true, "settled": true, "quote": quote.duplicate(true)}
	if world.get("target_generations", {}).has(quote.target) and int(world.target_generations[quote.target]) != int(quote.target_generation): return _no("stale_target_generation")
	var due: Dictionary = {}
	for item in quote.items:
		var amount: int = int(quote.items[item]) - int(quote.paid.get(item, 0))
		if amount > 0: due[item] = amount
	var probe: Dictionary = world.duplicate(true)
	if quote.kind == "project":
		probe["available_plots"] = world.get("available_plots", []).duplicate()
		probe.available_plots.erase(quote.target)
		probe["plots"] = world.get("plots", {}).duplicate(true)
		if int(quote.identity.get("tier", 1)) <= 1: probe.plots.erase(quote.target)
	return prove(due, probe) if not due.is_empty() else {"ok": true, "remaining": {}}

func pause_quote(offer_key: String) -> Dictionary:
	if not _quotes.has(offer_key): return _no("unknown_quote")
	if _quotes[offer_key].status not in ["COMPLETE", "SETTLED", "RETIRED"]: _quotes[offer_key].status = "PAUSED"
	return {"ok": true, "quote": _quotes[offer_key].duplicate(true), "reroll_allowed": false}

func resume_quote(offer_key: String, world: Dictionary) -> Dictionary:
	var proof: Dictionary = revalidate_quote(offer_key, world)
	if not proof.ok: return proof
	if _quotes[offer_key].status == "PAUSED": _quotes[offer_key].status = "OPEN"
	return {"ok": true, "quote": _quotes[offer_key].duplicate(true)}

func rebind_customer_quote(offer_key: String, lifecycle: RefCounted, rebuild_receipt: Dictionary, world: Dictionary) -> Dictionary:
	if not _quotes.has(offer_key) or _quotes[offer_key].kind != "customer": return _no("unknown_customer_quote")
	var quote: Dictionary = _quotes[offer_key]
	if quote.status in ["SETTLED", "RETIRED"]: return _no("final_quote_cannot_rebind")
	if lifecycle == null or not lifecycle.has_method("validate_rebuild_receipt") or not lifecycle.validate_rebuild_receipt(rebuild_receipt): return _no("unvalidated_rebuild_receipt")
	if rebuild_receipt.get("asset_id") != quote.target or rebuild_receipt.get("paid") != true or rebuild_receipt.get("ordinary_only") != true or int(rebuild_receipt.get("tier", 0)) != 1 or int(rebuild_receipt.get("hp", 0)) <= 0: return _no("invalid_counter_rebuild")
	var new_generation: int = int(rebuild_receipt.get("generation", -1))
	if quote.get("rebind_request_id") == rebuild_receipt.get("request_id") and int(quote.target_generation) == new_generation:
		return {"ok": true, "replayed": true, "quote": quote.duplicate(true)}
	if int(rebuild_receipt.get("previous_generation", -1)) != int(quote.target_generation) or new_generation != int(quote.target_generation) + 1 or int(world.get("counter_generation", -1)) != new_generation: return _no("stale_counter_rebind")
	var proof: Dictionary = prove(quote.items, world)
	if not proof.ok: return _no("rebound_order_not_yet_obtainable", proof)
	quote.target_generation = new_generation
	quote.identity.generation = new_generation
	quote.status = "OPEN"
	quote["rebind_request_id"] = str(rebuild_receipt.request_id)
	quote["current_recovery_proof"] = proof.duplicate(true)
	return {"ok": true, "quote": quote.duplicate(true), "terms_unchanged": true}

func contribute(offer_key: String, tx_id: String, payer_id: String, payer_cargo: Dictionary, offered_items: Dictionary, target_generation: int) -> Dictionary:
	if tx_id.is_empty() or payer_id.is_empty() or not _goods(offered_items): return _no("invalid_payment")
	if _retirements.has(tx_id): return _no("request_id_payload_mismatch")
	var goods: Dictionary = _integers(offered_items)
	if goods.is_empty(): return _no("empty_payment")
	var signature: String = _fingerprint([offer_key, payer_id, goods, target_generation])
	if _requests.has(tx_id):
		if _requests[tx_id].signature != signature: return _no("request_id_payload_mismatch")
		var replay: Dictionary = _requests[tx_id].receipt.duplicate(true)
		replay["replayed"] = true
		return replay
	if not _quotes.has(offer_key) or not _goods(payer_cargo, true): return _no("unknown_quote_or_invalid_cargo")
	var quote: Dictionary = _quotes[offer_key]
	if quote.kind != "project" or quote.status != "OPEN": return _no("project_not_open")
	if int(quote.target_generation) != target_generation: return _no("stale_target_generation")
	for item in goods:
		if not quote.items.has(item) or int(goods[item]) > int(quote.items[item]) - int(quote.paid.get(item, 0)): return _no("overpayment_or_wrong_item")
		if int(payer_cargo.get(item, 0)) < int(goods[item]): return _no("insufficient_payer_stock")
	# All checks precede both debits and contribution updates; no awaits/contact callbacks here.
	for item in goods:
		payer_cargo[item] = int(payer_cargo.get(item, 0)) - int(goods[item])
		quote.paid[item] = int(quote.paid.get(item, 0)) + int(goods[item])
	var complete: bool = true
	for item in quote.items:
		if int(quote.paid.get(item, 0)) != int(quote.items[item]): complete = false
	if complete: quote.status = "COMPLETE"
	var receipt: Dictionary = {"ok": true, "kind": "project_payment", "id": tx_id, "quote_id": offer_key, "payer_id": payer_id, "target_generation": target_generation, "items": goods, "complete": complete, "committed": true}
	_requests[tx_id] = {"signature": signature, "receipt": receipt.duplicate(true)}
	return receipt

func mark_customer_settled(offer_key: String, sale_receipt: Dictionary) -> Dictionary:
	if not _quotes.has(offer_key): return _no("unknown_quote")
	var quote: Dictionary = _quotes[offer_key]
	if quote.status == "RETIRED": return _no("retired_quote_cannot_settle")
	if quote.kind != "customer" or sale_receipt.get("kind") != "sale" or sale_receipt.get("quote_id") != offer_key or sale_receipt.get("committed") != true or sale_receipt.get("items") != quote.items or int(sale_receipt.get("cash", -1)) != int(quote.payout): return _no("sale_receipt_mismatch")
	quote.status = "SETTLED"
	return {"ok": true, "quote": quote.duplicate(true)}

func snapshot() -> Dictionary:
	return {"version": 1, "catalog_hash": _fingerprint(_catalog), "seed": _seed, "quotes": _quotes.duplicate(true), "requests": _requests.duplicate(true), "counter_slots": _counter_slots.duplicate(true), "retirements": _retirements.duplicate(true), "retirement_authority_id": _retirement_authority_id}

func restore(saved: Dictionary) -> Dictionary:
	saved = _canonical(saved)
	if saved.get("version") != 1 or saved.get("catalog_hash") != _fingerprint(_catalog) or int(saved.get("seed", -1)) != _seed: return _no("snapshot_identity_mismatch")
	if not saved.get("quotes") is Dictionary or not saved.get("requests") is Dictionary or not saved.get("counter_slots") is Dictionary: return _no("invalid_snapshot")
	for id in saved.quotes:
		var quote: Variant = saved.quotes[id]
		if not quote is Dictionary or quote.get("id") != id or not _goods(quote.get("items")) or not _goods(quote.get("paid"), true) or not _count(quote.get("payout")) or not quote.get("identity") is Dictionary: return _no("invalid_saved_quote")
		if quote.get("status") not in ["OPEN", "PAUSED", "COMPLETE", "SETTLED", "RETIRED"] or quote.get("catalog_version") != str(_catalog.version): return _no("invalid_saved_quote_state")
		if quote.get("kind") not in ["project", "customer"] or quote.identity.get("kind") != quote.kind or quote.identity.get("target") != quote.get("target") or quote.identity.get("generation") != quote.get("target_generation"): return _no("invalid_saved_quote_identity")
		if not _count(quote.get("target_generation")) or int(quote.target_generation) < 1 or int(quote.get("seed", _seed + 1)) != _seed: return _no("invalid_saved_quote_identity")
		if _integers(quote.items).is_empty(): return _no("empty_saved_quote")
		for item in quote.items:
			if not _catalog.items.has(item) or int(quote.items[item]) <= 0: return _no("unknown_saved_item")
		for item in quote.paid:
			if not quote.items.has(item) or int(quote.paid[item]) > int(quote.items[item]): return _no("invalid_saved_contribution")
		if quote.kind == "project":
			if int(quote.payout) != 0 or quote.status in ["SETTLED", "RETIRED"]: return _no("invalid_project_state")
			if (quote.status == "COMPLETE") != (_integers(quote.paid) == _integers(quote.items)): return _no("invalid_project_completion")
		else:
			if int(quote.payout) < 1 or not quote.paid.is_empty() or quote.status == "COMPLETE": return _no("invalid_customer_state")
			for item in quote.items:
				if not _catalog.items[item].get("processed", false): return _no("raw_saved_customer_goods")
	# Payment journal must explain every committed contribution. Reject malformed
	# or fabricated completion state before assigning any restored state.
	var payment_totals: Dictionary = {}
	for request_id in saved.requests:
		var entry: Variant = saved.requests[request_id]
		if not entry is Dictionary or not entry.get("signature") is String or not entry.get("receipt") is Dictionary: return _no("invalid_saved_request")
		var receipt: Dictionary = entry.receipt
		if receipt.get("id") != request_id or receipt.get("kind") != "project_payment" or receipt.get("committed") != true or receipt.get("ok") != true or not _goods(receipt.get("items")) or not saved.quotes.has(receipt.get("quote_id")): return _no("invalid_saved_payment")
		var quote: Dictionary = saved.quotes[receipt.quote_id]
		if quote.kind != "project" or receipt.get("target_generation") != quote.target_generation or str(receipt.get("payer_id", "")).is_empty(): return _no("invalid_saved_payment_identity")
		if entry.signature != _fingerprint([str(receipt.quote_id), str(receipt.payer_id), _integers(receipt.items), int(receipt.target_generation)]): return _no("invalid_saved_request_signature")
		if not payment_totals.has(receipt.quote_id): payment_totals[receipt.quote_id] = {}
		for item in receipt.items:
			if not quote.items.has(item): return _no("invalid_saved_payment_item")
			payment_totals[receipt.quote_id][item] = int(payment_totals[receipt.quote_id].get(item, 0)) + int(receipt.items[item])
	for id in saved.quotes:
		if saved.quotes[id].kind == "project" and _integers(payment_totals.get(id, {})) != _integers(saved.quotes[id].paid): return _no("unexplained_saved_contributions")
	if not saved.get("retirements", {}) is Dictionary or not saved.get("retirement_authority_id", "") is String: return _no("invalid_retirement_journal")
	var saved_authority: String = str(saved.get("retirement_authority_id", ""))
	if not _retirement_authority_id.is_empty() and _retirement_authority_id != saved_authority: return _no("retirement_authority_identity_mismatch")
	for tx in saved.get("retirements", {}):
		if saved.requests.has(tx): return _no("saved_transaction_kind_collision")
		var entry: Variant = saved.retirements[tx]
		if not entry is Dictionary or not entry.get("receipt") is Dictionary: return _no("invalid_saved_retirement")
		var receipt: Dictionary = entry.receipt
		if receipt.get("id") != tx or receipt.get("kind") != "customer_quote_retired" or receipt.get("ok") != true or receipt.get("committed") != true or receipt.get("cash_created") != 0 or receipt.get("returned_items") != {} or not saved.quotes.has(receipt.get("quote_id")): return _no("invalid_saved_retirement_receipt")
		var quote: Dictionary = saved.quotes[receipt.quote_id]
		if quote.kind != "customer" or quote.status != "RETIRED" or quote.get("retirement_transaction_id") != tx or receipt.get("items") != quote.items or receipt.get("promised_payout") != quote.payout or receipt.get("ordinal") != quote.identity.get("ordinal") or receipt.get("counter_id") != quote.target or receipt.get("target_generation") != quote.target_generation: return _no("retirement_terms_mismatch")
		if saved_authority.is_empty() or receipt.get("authority_id") != saved_authority or not _count(receipt.get("source_revision")) or not receipt.get("source_snapshot_hash") is String or not receipt.get("failure_reason") is String or not receipt.get("custody_receipt") is Dictionary: return _no("invalid_retirement_authority_evidence")
		if entry.get("signature") != _fingerprint([str(receipt.quote_id)]): return _no("invalid_retirement_signature")
		var cancellation: Dictionary = receipt.custody_receipt
		if cancellation.get("kind") != "unpaid_quote_retired" or cancellation.get("quote_id") != receipt.quote_id or cancellation.get("cash_created") != 0 or cancellation.get("returned_items") != {} or cancellation.get("committed") != true: return _no("invalid_retirement_custody_receipt")
	for quote in saved.quotes.values():
		if quote.status == "RETIRED" and not saved.get("retirements", {}).has(quote.get("retirement_transaction_id")): return _no("retirement_missing_committed_journal")
	var obligations: Dictionary = {}
	var customer_frontiers: Dictionary = {}
	var customer_ordinals: Dictionary = {}
	for id in saved.quotes:
		var quote: Dictionary = saved.quotes[id]
		if quote.kind == "project":
			var obligation: String = _fingerprint(quote.identity)
			if obligations.has(obligation): return _no("duplicate_saved_obligation")
			obligations[obligation] = id
		else:
			if not quote.target is String or quote.target.is_empty() or not _count(quote.identity.get("ordinal")): return _no("invalid_customer_frontier_identity")
			var ordinal: int = int(quote.identity.ordinal)
			if not customer_ordinals.has(quote.target): customer_ordinals[quote.target] = {}
			if customer_ordinals[quote.target].has(ordinal): return _no("duplicate_saved_customer_ordinal")
			customer_ordinals[quote.target][ordinal] = id
			if not customer_frontiers.has(quote.target) or ordinal > int(customer_frontiers[quote.target].ordinal):
				customer_frontiers[quote.target] = {"id": id, "ordinal": ordinal}
	# Slot history cannot be erased or rolled back to a retired/settled
	# predecessor. Allow monotonic gaps from older valid snapshots, but every
	# counter must retain exactly its unique highest issued ordinal as frontier.
	if saved.counter_slots.size() != customer_frontiers.size(): return _no("missing_or_extra_saved_customer_frontier")
	for counter in customer_frontiers:
		if saved.counter_slots.get(counter) != customer_frontiers[counter].id: return _no("saved_customer_frontier_rolled_back")
	for quote in saved.quotes.values():
		if quote.kind == "customer" and int(quote.identity.ordinal) < int(customer_frontiers[quote.target].ordinal) and quote.status not in ["SETTLED", "RETIRED"]: return _no("active_customer_predecessor")
	for counter in saved.counter_slots:
		if not saved.quotes.has(saved.counter_slots[counter]): return _no("missing_saved_slot_quote")
		var quote: Dictionary = saved.quotes[saved.counter_slots[counter]]
		if quote.kind != "customer" or quote.target != counter: return _no("invalid_saved_slot_quote")
	_quotes = saved.quotes.duplicate(true)
	_requests = saved.requests.duplicate(true)
	_counter_slots = saved.counter_slots.duplicate(true)
	_retirements = saved.get("retirements", {}).duplicate(true)
	_retirement_authority_id = saved_authority
	return {"ok": true}
