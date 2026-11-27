extends RefCounted
## Standalone exact-custody boundary, not vehicle physics or game integration.
## World observations come ONLY from one bound trusted adapter. Scene validation,
## source contact and complete-world atomic persistence remain adapter obligations.

const Count = preload("res://exact_count.gd")
const SCHEMA := "havenline.vehicle.rules.v1"
const METHODS := ["vehicle_authority_id", "capture_vehicle_bootstrap", "validate_vehicle_bootstrap", "capture_vehicle_observation", "validate_vehicle_observation", "authorize_vehicle_restore"]

var _adapter: Object
var _genesis: Dictionary = {}
var _state: Dictionary = {}
var _events: Array = []
var _requests: Dictionary = {}
var _busy := false

func initialize(adapter: Object) -> Dictionary:
	if not _genesis.is_empty():
		return _fail("already_initialized")
	if not _adapter_valid(adapter):
		return _fail("invalid_adapter")
	var initial: Variant = adapter.capture_vehicle_bootstrap()
	if not initial is Dictionary or not _json_tree(initial) or not adapter.validate_vehicle_bootstrap(initial):
		return _fail("untrusted_bootstrap")
	var built := _initial_state(initial)
	if not built.ok:
		return built
	if initial.authority_id != adapter.vehicle_authority_id():
		return _fail("authority_mismatch")
	_adapter = adapter
	_genesis = initial.duplicate(true)
	_state = built.state
	return {"ok": true, "authority_id": initial.authority_id}

func admit_quote(quote_id: String, request_id: String) -> Dictionary:
	return _dispatch("admit_quote", {"quote_id": quote_id}, request_id)

func purchase(quote_id: String, request_id: String) -> Dictionary:
	return _dispatch("purchase", {"quote_id": quote_id}, request_id)

func rebind_quote_garage(quote_id: String, request_id: String) -> Dictionary:
	return _dispatch("rebind_quote", {"quote_id": quote_id}, request_id)

func rebind_quote_payer(quote_id: String, payer_id: String, payer_generation: int, request_id: String) -> Dictionary:
	return _dispatch("rebind_payer", {"quote_id": quote_id, "payer_id": payer_id, "payer_generation": payer_generation}, request_id)

func storage_destroyed(storage_id: String, generation: int, request_id: String) -> Dictionary:
	return _dispatch("storage_destroyed", {"storage_id": storage_id, "generation": generation}, request_id)

func reopen_storage(storage_id: String, previous_generation: int, request_id: String) -> Dictionary:
	return _dispatch("reopen_storage", {"storage_id": storage_id, "previous_generation": previous_generation}, request_id)

func load_cargo(vehicle_id: String, generation: int, source_id: String, source_generation: int, items: Dictionary, request_id: String) -> Dictionary:
	return _dispatch("load", {"vehicle_id": vehicle_id, "generation": generation, "source_id": source_id, "source_generation": source_generation, "items": items.duplicate(true)}, request_id)

func park_and_unload(vehicle_id: String, generation: int, request_id: String) -> Dictionary:
	return _dispatch("dock", {"vehicle_id": vehicle_id, "generation": generation}, request_id)

func apply_contact_damage(vehicle_id: String, generation: int, contact_id: String, request_id: String) -> Dictionary:
	return _dispatch("damage", {"vehicle_id": vehicle_id, "generation": generation, "contact_id": contact_id}, request_id)

func claim_inside_salvage(cache_id: String, account_id: String, generation: int, request_id: String) -> Dictionary:
	return _dispatch("claim", {"cache_id": cache_id, "account_id": account_id, "generation": generation}, request_id)

func state() -> Dictionary:
	return _state.duplicate(true)

func snapshot() -> Dictionary:
	return {"schema": SCHEMA, "genesis": _genesis.duplicate(true), "events": _events.duplicate(true), "state_digest": Count.canonical(_state).sha256_text()}

func restore(saved: Variant, adapter: Object) -> Dictionary:
	# Restore is not a player-facing rollback API. The full-world save authority
	# must admit this exact snapshot and its epoch before replay occurs.
	if _busy or not _adapter_valid(adapter):
		return _fail("invalid_adapter_or_busy")
	if _adapter != null and _adapter != adapter:
		return _fail("adapter_identity_changed")
	if not saved is Dictionary or not _json_tree(saved) or not _keys(saved, ["schema", "genesis", "events", "state_digest"]):
		return _fail("invalid_snapshot_shape")
	if saved.schema != SCHEMA or not saved.genesis is Dictionary or not saved.events is Array or not saved.state_digest is String:
		return _fail("invalid_snapshot_schema")
	if not adapter.authorize_vehicle_restore(saved):
		return _fail("restore_not_authorized_by_world")
	saved = Count.normalize_json(saved)
	var built := _initial_state(saved.genesis)
	if not built.ok or saved.genesis.get("authority_id") != adapter.vehicle_authority_id():
		return _fail("invalid_genesis")
	var candidate: Dictionary = built.state
	var requests: Dictionary = {}
	for event in saved.events:
		if not event is Dictionary or not _keys(event, ["request_id", "operation", "parameters", "facts", "receipt"]):
			return _fail("invalid_event_shape")
		if not _id(event.request_id) or requests.has(event.request_id) or not event.operation is String or not event.parameters is Dictionary or not event.facts is Dictionary or not event.receipt is Dictionary:
			return _fail("invalid_or_duplicate_event")
		var result := _reduce(candidate, event.operation, event.parameters, event.facts)
		if not result.ok:
			return _fail("invalid_event_transition:" + result.reason)
		result["request_id"] = event.request_id
		result["sequence"] = str(requests.size() + 1)
		if Count.canonical(result) != Count.canonical(event.receipt):
			return _fail("receipt_mismatch")
		requests[event.request_id] = {"payload": _payload(event.operation, event.parameters), "receipt": result.duplicate(true)}
	if not _conserved(candidate) or Count.canonical(candidate).sha256_text() != saved.state_digest:
		return _fail("state_digest_or_conservation_mismatch")
	# Assignment happens only after every event and inventory has passed.
	_adapter = adapter
	_genesis = saved.genesis.duplicate(true)
	_state = candidate
	_events = saved.events.duplicate(true)
	_requests = requests
	return {"ok": true, "events": str(_events.size())}

func audit() -> Dictionary:
	return {"ok": not _state.is_empty() and _conserved(_state), "events": str(_events.size()), "game_integration": false}

func _dispatch(operation: String, parameters: Dictionary, request_id: String) -> Dictionary:
	if _state.is_empty() or _adapter == null or not is_instance_valid(_adapter):
		return _fail("uninitialized")
	if _busy:
		return _fail("reentrant_command")
	if not _id(request_id):
		return _fail("invalid_request_id")
	if not _json_tree(parameters):
		return _fail("invalid_json_parameters")
	var payload := _payload(operation, parameters)
	if _requests.has(request_id):
		if _requests[request_id].payload != payload:
			return _fail("request_payload_changed")
		return _requests[request_id].receipt.duplicate(true)
	_busy = true
	var observation: Variant = _adapter.capture_vehicle_observation(operation, parameters.duplicate(true))
	if not observation is Dictionary or not _json_tree(observation) or not _keys(observation, ["authority_id", "revision", "operation", "parameters", "facts"]) or observation.authority_id != _genesis.authority_id or not Count.valid(observation.revision) or observation.operation != operation or Count.canonical(observation.parameters) != Count.canonical(parameters) or not observation.facts is Dictionary:
		_busy = false
		return _fail("invalid_world_observation")
	var frozen: Dictionary = observation.duplicate(true)
	if not _adapter.validate_vehicle_observation(frozen):
		_busy = false
		return _fail("stale_world_observation")
	var candidate := _state.duplicate(true)
	var result := _reduce(candidate, operation, parameters, frozen.facts)
	if result.ok and not _conserved(candidate):
		result = _fail("conservation_failure")
	if result.ok and not _adapter.validate_vehicle_observation(frozen):
		result = _fail("world_changed_before_commit")
	if result.ok:
		result["request_id"] = request_id
		result["sequence"] = str(_events.size() + 1)
		_state = candidate
		_events.append({"request_id": request_id, "operation": operation, "parameters": parameters.duplicate(true), "facts": frozen.facts.duplicate(true), "receipt": result.duplicate(true)})
		_requests[request_id] = {"payload": payload, "receipt": result.duplicate(true)}
	_busy = false
	return result

func _reduce(s: Dictionary, operation: String, p: Dictionary, f: Dictionary) -> Dictionary:
	match operation:
		"admit_quote": return _quote(s, p, f)
		"purchase": return _purchase(s, p, f)
		"rebind_quote": return _rebind_quote(s, p, f)
		"rebind_payer": return _rebind_payer(s, p, f)
		"storage_destroyed": return _storage_destroyed(s, p, f)
		"reopen_storage": return _reopen_storage(s, p, f)
		"load": return _load(s, p, f)
		"dock": return _dock(s, p, f)
		"damage": return _damage(s, p, f)
		"claim": return _claim(s, p, f)
	return _fail("unknown_operation")

func _quote(s: Dictionary, p: Dictionary, f: Dictionary) -> Dictionary:
	if not _keys(p, ["quote_id"]) or not _id(p.quote_id) or not _keys(f, ["quote", "garage", "acquisition_proof_id"]):
		return _fail("invalid_quote_shape")
	var q: Variant = f.quote
	if not q is Dictionary or not _keys(q, ["id", "vehicle_id", "next_generation", "garage_id", "garage_generation", "camp_id", "payer_id", "payer_generation", "bill", "max_hp", "catalogue_version"]):
		return _fail("invalid_quote")
	if q.id != p.quote_id or not _id(q.vehicle_id) or not _id(q.camp_id) or not _id(q.garage_id) or not _id(q.catalogue_version) or not _id(f.acquisition_proof_id) or not _positive_integer(q.next_generation) or not _positive_integer(q.garage_generation) or not _positive_integer(q.max_hp):
		return _fail("invalid_quote_fields")
	if not _items_valid(q.bill, s.resources, true) or not _account(s, q.payer_id, q.payer_generation):
		return _fail("invalid_bill_or_payer")
	if not _garage_valid(f.garage, q.garage_id, q.camp_id) or f.garage.generation != q.garage_generation:
		return _fail("garage_not_ready")
	if s.quotes.has(q.id):
		return _fail("quote_already_admitted")
	for vehicle in s.vehicles.values():
		if vehicle.alive and vehicle.garage_id == q.garage_id:
			return _fail("garage_bay_occupied")
	var expected := 1
	if s.vehicles.has(q.vehicle_id):
		if s.vehicles[q.vehicle_id].alive:
			return _fail("vehicle_already_alive")
		expected = int(s.vehicles[q.vehicle_id].generation) + 1
	if q.next_generation != expected:
		return _fail("wrong_next_generation")
	for other in s.quotes.values():
		if not other.used and (other.garage_id == q.garage_id or (other.vehicle_id == q.vehicle_id and other.next_generation == q.next_generation)):
			return _fail("existing_frozen_quote")
	var saved: Dictionary = q.duplicate(true)
	saved["used"] = false
	s.quotes[q.id] = saved
	return {"ok": true, "operation": "admit_quote", "quote_id": q.id, "bill": q.bill.duplicate(true)}

func _purchase(s: Dictionary, p: Dictionary, f: Dictionary) -> Dictionary:
	if not _keys(p, ["quote_id"]) or not s.quotes.has(p.quote_id) or not _keys(f, ["garage", "acquisition_proof_id"]):
		return _fail("unknown_quote_or_invalid_purchase")
	var q: Dictionary = s.quotes[p.quote_id]
	if q.used or not _id(f.acquisition_proof_id):
		return _fail("quote_spent_or_missing_current_acquisition_proof")
	if not _garage_valid(f.garage, q.garage_id, q.camp_id) or f.garage.generation != q.garage_generation:
		return _fail("garage_generation_changed_or_unready")
	if not _account(s, q.payer_id, q.payer_generation) or not _has_items(s.accounts[q.payer_id].items, q.bill):
		return _fail("unfunded")
	if s.vehicles.has(q.vehicle_id) and (s.vehicles[q.vehicle_id].alive or int(s.vehicles[q.vehicle_id].generation) + 1 != q.next_generation):
		return _fail("stale_vehicle_generation")
	for vehicle in s.vehicles.values():
		if vehicle.alive and vehicle.garage_id == q.garage_id:
			return _fail("garage_bay_occupied")
	_move(s.accounts[q.payer_id].items, s.spent, q.bill)
	q.used = true
	s.vehicles[q.vehicle_id] = {"id": q.vehicle_id, "generation": q.next_generation, "garage_id": q.garage_id, "camp_id": q.camp_id, "alive": true, "hp": q.max_hp, "max_hp": q.max_hp, "tier": 1, "cargo": {}, "last_destruction": ""}
	return {"ok": true, "operation": "purchase", "vehicle_id": q.vehicle_id, "generation": q.next_generation, "tier": 1, "consumed": q.bill.duplicate(true)}

func _rebind_quote(s: Dictionary, p: Dictionary, f: Dictionary) -> Dictionary:
	if not _keys(p, ["quote_id"]) or not s.quotes.has(p.quote_id) or not _keys(f, ["garage", "replacement_receipt_id", "acquisition_proof_id"]):
		return _fail("invalid_quote_rebind")
	var q: Dictionary = s.quotes[p.quote_id]
	if q.used or not _id(f.replacement_receipt_id) or not _id(f.acquisition_proof_id) or not _garage_valid(f.garage, q.garage_id, q.camp_id) or f.garage.generation <= q.garage_generation:
		return _fail("quote_rebind_not_authorized")
	var old: Variant = q.garage_generation
	q.garage_generation = f.garage.generation
	return {"ok": true, "operation": "rebind_quote", "quote_id": q.id, "previous_garage_generation": old, "garage_generation": q.garage_generation, "unchanged_bill": q.bill.duplicate(true)}

func _storage_destroyed(s: Dictionary, p: Dictionary, f: Dictionary) -> Dictionary:
	if not _keys(p, ["storage_id", "generation"]) or not _keys(f, ["destruction_receipt_id", "destroyed"]):
		return _fail("invalid_storage_destruction")
	if not _account(s, p.storage_id, p.generation) or s.accounts[p.storage_id].kind != "storage" or not _id(f.destruction_receipt_id) or not _true(f.destroyed):
		return _fail("storage_not_destroyable")
	var account: Dictionary = s.accounts[p.storage_id]
	var cache: String = "storage-estate:" + p.storage_id + ":" + str(int(p.generation))
	var contents: Dictionary = account.items.duplicate(true)
	s.salvage[cache] = {}
	_move(account.items, s.salvage[cache], contents)
	account.alive = false
	return {"ok": true, "operation": "storage_destroyed", "cache_id": cache, "moved": contents}

func _reopen_storage(s: Dictionary, p: Dictionary, f: Dictionary) -> Dictionary:
	if not _keys(p, ["storage_id", "previous_generation"]) or not _keys(f, ["replacement_receipt_id", "new_generation", "working"]):
		return _fail("invalid_storage_reopen")
	if not _id(p.storage_id) or not s.accounts.has(p.storage_id) or not _positive_integer(p.previous_generation) or not _positive_integer(f.new_generation):
		return _fail("invalid_storage_identity")
	var account: Dictionary = s.accounts[p.storage_id]
	if account.kind != "storage" or account.alive or account.generation != p.previous_generation or f.new_generation != p.previous_generation + 1 or not _id(f.replacement_receipt_id) or not _true(f.working):
		return _fail("storage_reopen_not_authorized")
	# Payment and actual level1 rebuilding belong to the bound lifecycle adapter.
	# This callback only reopens EMPTY custody, preserving the old ruin estate.
	account.generation = f.new_generation
	account.alive = true
	return {"ok": true, "operation": "reopen_storage", "storage_id": p.storage_id, "generation": f.new_generation}

func _rebind_payer(s: Dictionary, p: Dictionary, f: Dictionary) -> Dictionary:
	if not _keys(p, ["quote_id", "payer_id", "payer_generation"]) or not s.quotes.has(p.quote_id) or not _keys(f, ["payment_authorization_id", "payer_available"]):
		return _fail("invalid_payer_rebind")
	var q: Dictionary = s.quotes[p.quote_id]
	if q.used or not _account(s, p.payer_id, p.payer_generation) or not _id(f.payment_authorization_id) or not _true(f.payer_available):
		return _fail("payer_rebind_not_authorized")
	var old_id: String = q.payer_id
	var old_generation: Variant = q.payer_generation
	q.payer_id = p.payer_id
	q.payer_generation = p.payer_generation
	return {"ok": true, "operation": "rebind_payer", "quote_id": q.id, "previous_payer_id": old_id, "previous_payer_generation": old_generation, "payer_id": q.payer_id, "payer_generation": q.payer_generation, "unchanged_bill": q.bill.duplicate(true)}

func _load(s: Dictionary, p: Dictionary, f: Dictionary) -> Dictionary:
	if not _keys(p, ["vehicle_id", "generation", "source_id", "source_generation", "items"]) or not _keys(f, ["contact_id", "source_reachable", "source_available"]):
		return _fail("invalid_load_shape")
	if not _live_vehicle(s, p.vehicle_id, p.generation) or not _account(s, p.source_id, p.source_generation):
		return _fail("invalid_vehicle_or_source")
	if not _id(f.contact_id) or not _true(f.source_reachable) or not _true(f.source_available):
		return _fail("source_not_in_contact")
	if not _items_valid(p.items, s.resources, true) or not _has_items(s.accounts[p.source_id].items, p.items):
		return _fail("invalid_or_insufficient_load")
	_move(s.accounts[p.source_id].items, s.vehicles[p.vehicle_id].cargo, p.items)
	return {"ok": true, "operation": "load", "moved": p.items.duplicate(true)}

func _dock(s: Dictionary, p: Dictionary, f: Dictionary) -> Dictionary:
	if not _keys(p, ["vehicle_id", "generation"]) or not _keys(f, ["garage", "receiver", "hull_points", "blade_points", "parking_min", "parking_max", "speed", "blade_speed", "geometry_profile_id"]):
		return _fail("invalid_docking_shape")
	if not _live_vehicle(s, p.vehicle_id, p.generation):
		return _fail("vehicle_not_alive")
	var v: Dictionary = s.vehicles[p.vehicle_id]
	if not _garage_valid(f.garage, v.garage_id, v.camp_id):
		return _fail("garage_not_ready")
	if not _id(f.geometry_profile_id) or not _number(f.speed) or not _number(f.blade_speed) or f.speed != 0 or f.blade_speed != 0:
		return _fail("vehicle_or_blades_moving")
	if not _points_inside(f.hull_points, f.parking_min, f.parking_max) or not _points_inside(f.blade_points, f.parking_min, f.parking_max):
		return _fail("full_vehicle_not_parked")
	var r: Variant = f.receiver
	if not r is Dictionary or not _keys(r, ["id", "generation", "working", "route_connected", "accepts_all_resources", "unbounded_logical_stock"]) or not _account(s, r.id, r.generation):
		return _fail("invalid_receiver")
	if r.id != f.garage.storage_id or s.accounts[r.id].kind != "storage" or not _true(r.working) or not _true(r.route_connected) or not _true(r.accepts_all_resources) or not _true(r.unbounded_logical_stock):
		return _fail("receiver_hold_all_cargo")
	var moved: Dictionary = v.cargo.duplicate(true)
	_move(v.cargo, s.accounts[r.id].items, moved)
	return {"ok": true, "operation": "dock", "receiver_id": r.id, "receiver_generation": r.generation, "garage_generation": f.garage.generation, "moved": moved}

func _damage(s: Dictionary, p: Dictionary, f: Dictionary) -> Dictionary:
	if not _keys(p, ["vehicle_id", "generation", "contact_id"]) or not _keys(f, ["contact_id", "damage", "truck_footprint", "camp_polygon", "camp_id", "geometry_profile_id"]):
		return _fail("invalid_damage_shape")
	if not _live_vehicle(s, p.vehicle_id, p.generation) or not _id(p.contact_id) or p.contact_id != f.contact_id or not _positive_integer(f.damage) or not _id(f.geometry_profile_id):
		return _fail("invalid_damage_contact")
	if s.contacts.has(p.contact_id):
		return _fail("contact_already_applied")
	var v: Dictionary = s.vehicles[p.vehicle_id]
	if f.camp_id != v.camp_id or not _polygon_valid(f.truck_footprint) or not _polygon_valid(f.camp_polygon):
		return _fail("invalid_camp_geometry")
	s.contacts[p.contact_id] = {"vehicle_id": p.vehicle_id, "generation": p.generation}
	v.hp = maxi(0, int(v.hp) - int(f.damage))
	if v.hp > 0:
		return {"ok": true, "operation": "damage", "hp": v.hp, "destroyed": false}
	var outside: bool = _outside(f.truck_footprint, f.camp_polygon)
	var cargo: Dictionary = v.cargo.duplicate(true)
	var destination := "lost_outside_camp"
	if outside:
		_move(v.cargo, s.lost, cargo)
	else:
		destination = "vehicle-estate:" + p.vehicle_id + ":" + str(p.generation)
		s.salvage[destination] = {}
		_move(v.cargo, s.salvage[destination], cargo)
	v.alive = false
	v.last_destruction = destination
	s.tombstones[p.vehicle_id + ":" + str(p.generation)] = {"contact_id": p.contact_id, "disposition": destination, "cargo": cargo}
	return {"ok": true, "operation": "damage", "hp": 0, "destroyed": true, "outside_camp": outside, "disposition": destination, "cargo": cargo}

func _claim(s: Dictionary, p: Dictionary, f: Dictionary) -> Dictionary:
	if not _keys(p, ["cache_id", "account_id", "generation"]) or not _keys(f, ["contact_id", "cache_reachable", "recipient_available"]):
		return _fail("invalid_claim_shape")
	if not s.salvage.has(p.cache_id) or not _account(s, p.account_id, p.generation) or s.accounts[p.account_id].kind != "actor" or not _id(f.contact_id) or not _true(f.cache_reachable) or not _true(f.recipient_available):
		return _fail("cache_not_claimable")
	var moved: Dictionary = s.salvage[p.cache_id].duplicate(true)
	_move(s.salvage[p.cache_id], s.accounts[p.account_id].items, moved)
	return {"ok": true, "operation": "claim", "moved": moved}

func _initial_state(initial: Dictionary) -> Dictionary:
	if not _keys(initial, ["authority_id", "resources", "accounts"]) or not _id(initial.authority_id) or not initial.resources is Array or initial.resources.is_empty() or not initial.accounts is Dictionary:
		return _fail("invalid_bootstrap")
	var resources: Array = []
	for item in initial.resources:
		if not _id(item) or item in resources:
			return _fail("invalid_resource_catalogue")
		resources.append(item)
	resources.sort()
	var introduced: Dictionary = {}
	for owner in initial.accounts:
		var a: Variant = initial.accounts[owner]
		if not _id(owner) or not a is Dictionary or not _keys(a, ["kind", "generation", "items"]) or a.kind not in ["actor", "storage"] or not _positive_integer(a.generation) or not _items_valid(a.items, resources, false):
			return _fail("invalid_initial_account")
		_add_items(introduced, a.items)
	var accounts: Dictionary = initial.accounts.duplicate(true)
	for account in accounts.values(): account["alive"] = true
	return {"ok": true, "state": {"resources": resources, "accounts": accounts, "vehicles": {}, "quotes": {}, "salvage": {}, "lost": {}, "spent": {}, "introduced": introduced, "contacts": {}, "tombstones": {}}}

func _conserved(s: Dictionary) -> bool:
	var held: Dictionary = {}
	for a in s.accounts.values(): _add_items(held, a.items)
	for v in s.vehicles.values():
		if not v.alive and not v.cargo.is_empty(): return false
		_add_items(held, v.cargo)
	for items in s.salvage.values(): _add_items(held, items)
	_add_items(held, s.lost)
	_add_items(held, s.spent)
	return Count.canonical(held) == Count.canonical(s.introduced)

func _garage_valid(g: Variant, garage_id: Variant, camp_id: Variant) -> bool:
	return g is Dictionary and _keys(g, ["id", "generation", "camp_id", "ready", "plot_inside_camp", "construction_receipt_id", "storage_id"]) and g.id == garage_id and g.camp_id == camp_id and _positive_integer(g.generation) and _true(g.ready) and _true(g.plot_inside_camp) and _id(g.construction_receipt_id) and _id(g.storage_id)

func _account(s: Dictionary, account_id: Variant, generation: Variant) -> bool:
	return _id(account_id) and s.accounts.has(account_id) and _positive_integer(generation) and s.accounts[account_id].generation == generation and s.accounts[account_id].alive

func _live_vehicle(s: Dictionary, vehicle_id: Variant, generation: Variant) -> bool:
	return _id(vehicle_id) and s.vehicles.has(vehicle_id) and _positive_integer(generation) and s.vehicles[vehicle_id].generation == generation and s.vehicles[vehicle_id].alive

func _items_valid(items: Variant, resources: Array, nonempty: bool) -> bool:
	if not items is Dictionary or (nonempty and items.is_empty()): return false
	for item in items:
		if not _id(item) or item not in resources or not Count.valid(items[item]) or items[item] == "0": return false
	return true

func _has_items(source: Dictionary, items: Dictionary) -> bool:
	for item in items:
		if Count.compare(source.get(item, "0"), items[item]) < 0: return false
	return true

func _move(source: Dictionary, destination: Dictionary, items: Dictionary) -> void:
	for item in items:
		var amount: String = items[item]
		var left: String = Count.subtract(source[item], amount)
		if left == "0": source.erase(item)
		else: source[item] = left
		destination[item] = Count.add(destination.get(item, "0"), amount)

func _add_items(destination: Dictionary, items: Dictionary) -> void:
	for item in items:
		destination[item] = Count.add(destination.get(item, "0"), items[item])

func _points_inside(points: Variant, low: Variant, high: Variant) -> bool:
	if not _point3(low) or not _point3(high) or not points is Array or points.size() < 8: return false
	for axis in range(3):
		if low[axis] >= high[axis]: return false
	for point in points:
		if not _point3(point): return false
		for axis in range(3):
			if point[axis] < low[axis] or point[axis] > high[axis]: return false
	return true

func _point3(value: Variant) -> bool:
	return value is Array and value.size() == 3 and _number(value[0]) and _number(value[1]) and _number(value[2])

func _polygon_valid(value: Variant) -> bool:
	if not value is Array or value.size() < 3: return false
	for point in value:
		if not point is Array or point.size() != 2 or not _number(point[0]) or not _number(point[1]): return false
	var polygon := _polygon(value)
	return not Geometry2D.triangulate_polygon(polygon).is_empty() and absf(_area(polygon)) > 0.00000001

func _outside(truck: Array, camp: Array) -> bool:
	# Full footprint, including any segment through a concave boundary. Merely
	# checking vertices would misclassify some intersecting footprints as inside.
	for polygon in Geometry2D.clip_polygons(_polygon(truck), _polygon(camp)):
		if absf(_area(polygon)) > 0.00000001: return true
	return false

func _polygon(points: Array) -> PackedVector2Array:
	var result := PackedVector2Array()
	for point in points: result.append(Vector2(point[0], point[1]))
	return result

func _area(polygon: PackedVector2Array) -> float:
	var result := 0.0
	for i in range(polygon.size()):
		var next := (i + 1) % polygon.size()
		result += polygon[i].x * polygon[next].y - polygon[next].x * polygon[i].y
	return result * 0.5

func _adapter_valid(adapter: Object) -> bool:
	if adapter == null or not is_instance_valid(adapter): return false
	for method in METHODS:
		if not adapter.has_method(method): return false
	return _id(adapter.vehicle_authority_id())

func _keys(value: Dictionary, names: Array) -> bool:
	if value.size() != names.size(): return false
	for key in names:
		if not value.has(key): return false
	return true

func _json_tree(value: Variant) -> bool:
	if value is Dictionary:
		for key in value:
			if not key is String or not _json_tree(value[key]): return false
		return true
	if value is Array:
		for item in value:
			if not _json_tree(item): return false
		return true
	return value == null or value is String or value is bool or _number(value)

func _id(value: Variant) -> bool:
	return value is String and not value.is_empty() and value.strip_edges() == value

func _number(value: Variant) -> bool:
	return (value is int or value is float) and is_finite(float(value))

func _positive_integer(value: Variant) -> bool:
	return _number(value) and value >= 1 and value <= 9007199254740991 and floor(float(value)) == value

func _true(value: Variant) -> bool:
	return value is bool and value

func _payload(operation: String, parameters: Dictionary) -> String:
	return Count.canonical({"operation": operation, "parameters": parameters})

func _fail(reason: String) -> Dictionary:
	return {"ok": false, "reason": reason}
