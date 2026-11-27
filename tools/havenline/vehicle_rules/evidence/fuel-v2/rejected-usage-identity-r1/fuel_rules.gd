extends RefCounted
## Same custody ledger as vehicle_rules, not an independent wallet.
## Prototype tuning only. No driving, harvesting, elapsed-time or receipt truth
## is established by this standalone reducer; the bound world owns those facts.
const Count = preload("res://exact_count.gd")
const POLICY := "fuel-v2-prototype-60-drive-120-blade"
const SUBUNITS := 120000
const TANK_UNITS := 60
const CAPACITY := 7200000
const MAX_SLICE_MS := 1000

static func enabled(s: Dictionary) -> bool: return s.has("fuel")

static func activate(s: Dictionary, p: Dictionary, f: Dictionary) -> Dictionary:
	if not _keys(p, []) or not _keys(f, ["policy_id", "timeline_id", "active_tick", "migration_receipt_id"]): return _fail("invalid_fuel_activation")
	if enabled(s) or "fuel" not in s.resources or f.policy_id != POLICY or not _id(f.timeline_id) or not Count.valid(f.active_tick) or not _id(f.migration_receipt_id): return _fail("fuel_policy_not_activatable")
	s["fuel"] = {"policy_id": POLICY, "timeline_id": f.timeline_id, "activation_tick": f.active_tick, "tanks": {}, "burned_subunits": "0", "lost_subunits": "0", "estates": {}, "usage_ids": {}}
	for vehicle in s.vehicles.values():
		s.fuel.tanks[_instance(vehicle.id, vehicle.generation)] = {"amount": "0", "cursor": f.active_tick}
	return {"ok": true, "operation": "activate_fuel_policy", "policy_id": POLICY, "legacy_free_fuel": "0"}

static func quote_allocation_valid(s: Dictionary, q: Dictionary) -> bool:
	if not q.has("initial_tank_fuel_units"): return true
	return enabled(s) and q.initial_tank_fuel_units is String and q.initial_tank_fuel_units == "60" and q.bill.has("fuel") and Count.valid(q.bill.fuel) and Count.compare(q.bill.fuel, "60") >= 0

static func purchase(s: Dictionary, q: Dictionary, f: Dictionary) -> Dictionary:
	if not enabled(s): return {"ok": true, "enabled": false}
	if not f.has("fuel_clock") or not f.fuel_clock is Dictionary or not _keys(f.fuel_clock, ["timeline_id", "active_tick"]): return _fail("purchase_missing_fuel_clock")
	var clock: Dictionary = f.fuel_clock
	if clock.timeline_id != s.fuel.timeline_id or not Count.valid(clock.active_tick) or Count.compare(clock.active_tick, s.fuel.activation_tick) < 0: return _fail("invalid_purchase_fuel_clock")
	for tank in s.fuel.tanks.values():
		if Count.compare(clock.active_tick, tank.cursor) < 0: return _fail("purchase_clock_rollback")
	var key := _instance(q.vehicle_id, q.next_generation)
	if s.fuel.tanks.has(key): return _fail("tank_generation_already_exists")
	var units: String = q.get("initial_tank_fuel_units", "0")
	if not quote_allocation_valid(s,q): return _fail("invalid_funded_tank")
	# The bill has just been transferred to spending by the parent reducer. Move
	# its funded tank portion OUT of spending into this same ledger's tank owner.
	if units != "0":
		if Count.compare(s.spent.get("fuel","0"),units) < 0: return _fail("tank_allocation_unfunded")
		_debit(s.spent, "fuel", units)
	s.fuel.tanks[key] = {"amount": Count.multiply_small(units,SUBUNITS), "cursor": clock.active_tick}
	return {"ok": true, "enabled": true, "initial_tank_fuel_units": units, "tank_subunits": s.fuel.tanks[key].amount}

static func refuel(s: Dictionary, p: Dictionary, f: Dictionary) -> Dictionary:
	if not _keys(p,["vehicle_id","generation","source_kind","source_id","source_generation","units"]) or not _service(f): return _fail("invalid_refuel_service")
	if not _live(s,p.vehicle_id,p.generation) or not _bounded_integer(p.source_generation,1,9007199254740991) or not Count.valid(p.units) or p.units == "0" or Count.compare(p.units,str(TANK_UNITS)) > 0: return _fail("invalid_refuel_quantity_or_vehicle")
	var source: Dictionary
	if p.source_kind == "truck":
		if p.source_id != p.vehicle_id or p.source_generation != p.generation: return _fail("wrong_cargo_source")
		source = s.vehicles[p.vehicle_id].cargo
	elif p.source_kind == "account":
		if not _id(p.source_id) or not s.accounts.has(p.source_id) or not s.accounts[p.source_id].alive or s.accounts[p.source_id].generation != p.source_generation: return _fail("unavailable_refuel_account")
		source = s.accounts[p.source_id].items
	else: return _fail("invalid_refuel_source_kind")
	var tank: Dictionary = s.fuel.tanks[_instance(p.vehicle_id,p.generation)]
	var addition := int(p.units) * SUBUNITS
	if int(tank.amount) + addition > CAPACITY: return _fail("tank_has_insufficient_whole_unit_room")
	if Count.compare(source.get("fuel","0"),p.units) < 0: return _fail("insufficient_carried_fuel")
	_debit(source,"fuel",p.units)
	tank.amount = Count.add(tank.amount,str(addition))
	return {"ok":true,"operation":"refuel","moved_units":p.units,"tank_subunits":tank.amount}

static func use(s: Dictionary, p: Dictionary, f: Dictionary) -> Dictionary:
	if not _keys(p,["vehicle_id","generation","usage_id"]) or not _keys(f,["timeline_id","from_tick","elapsed_ms","active_play","driving","blades"]): return _fail("invalid_power_grant_shape")
	if not _live(s,p.vehicle_id,p.generation) or not _id(p.usage_id) or not Count.valid(f.from_tick) or f.timeline_id != s.fuel.timeline_id or not _bounded_integer(f.elapsed_ms,0,MAX_SLICE_MS): return _fail("invalid_power_grant_window")
	if not f.active_play is bool or not f.driving is bool or not f.blades is bool: return _fail("invalid_power_modes")
	var key := _instance(p.vehicle_id,p.generation)
	var usage_key: String = key + "/" + p.usage_id
	var tank: Dictionary = s.fuel.tanks[key]
	if s.fuel.usage_ids.has(usage_key) or Count.compare(f.from_tick,tank.cursor) < 0: return _fail("replayed_or_overlapping_power_window")
	if not f.active_play and (f.elapsed_ms != 0 or f.driving or f.blades or f.from_tick != tank.cursor): return _fail("offline_catchup_forbidden")
	if f.active_play and f.elapsed_ms == 0: return _fail("empty_active_window")
	var rate := (2 if f.driving else 0) + (1 if f.blades else 0)
	var granted_ms := 0
	if rate > 0:
		granted_ms = mini(int(f.elapsed_ms), int(tank.amount) / rate)
	var burned := granted_ms * rate
	tank.amount = Count.subtract(tank.amount,str(burned))
	tank.cursor = Count.add(f.from_tick,str(int(f.elapsed_ms)))
	s.fuel.burned_subunits = Count.add(s.fuel.burned_subunits,str(burned))
	s.fuel.usage_ids[usage_key] = true
	# A processed request with powered_ms=0 is a durable denial of powered use,
	# not approval to move/harvest. Persisting its window prevents late reuse.
	return {"ok":true,"operation":"grant_powered_use","powered_ms":granted_ms,"requested_active_ms":int(f.elapsed_ms),"powered_use_allowed":granted_ms > 0,"depleted":rate > 0 and granted_ms < int(f.elapsed_ms),"burned_subunits":str(burned),"tank_subunits":tank.amount,"cursor":tank.cursor}

static func destroy(s: Dictionary, vehicle: Dictionary, outside: bool, estate_id: String) -> Dictionary:
	if not enabled(s): return {}
	var tank: Dictionary = s.fuel.tanks[_instance(vehicle.id,vehicle.generation)]
	var amount: String = tank.amount
	if outside: s.fuel.lost_subunits = Count.add(s.fuel.lost_subunits,amount)
	else: s.fuel.estates[estate_id] = Count.add(s.fuel.estates.get(estate_id,"0"),amount)
	tank.amount = "0"
	return {"tank_fuel_subunits":amount,"tank_fuel_disposition":"lost_outside_camp" if outside else estate_id}

static func recover(s: Dictionary, p: Dictionary, f: Dictionary) -> Dictionary:
	if not _keys(p,["vehicle_id","generation","cache_id"]) or not _service(f): return _fail("invalid_fuel_estate_service")
	if not _live(s,p.vehicle_id,p.generation) or not _id(p.cache_id) or not s.fuel.estates.has(p.cache_id): return _fail("fuel_estate_unavailable")
	var tank: Dictionary = s.fuel.tanks[_instance(p.vehicle_id,p.generation)]
	var free := str(CAPACITY - int(tank.amount))
	var available: String = s.fuel.estates[p.cache_id]
	var moved: String = free if Count.compare(free,available) < 0 else available
	tank.amount = Count.add(tank.amount,moved)
	s.fuel.estates[p.cache_id] = Count.subtract(available,moved)
	return {"ok":true,"operation":"recover_tank_fuel","moved_subunits":moved,"remaining_estate_subunits":s.fuel.estates[p.cache_id],"tank_subunits":tank.amount}

static func conserved(s: Dictionary, whole_held: Dictionary) -> bool:
	if not enabled(s): return Count.canonical(whole_held) == Count.canonical(s.introduced)
	var fuel: Dictionary = s.fuel
	if fuel.policy_id != POLICY or not Count.valid(fuel.burned_subunits) or not Count.valid(fuel.lost_subunits): return false
	var held: String = Count.multiply_small(whole_held.get("fuel","0"),SUBUNITS)
	for tank in fuel.tanks.values():
		if not Count.valid(tank.amount) or Count.compare(tank.amount,str(CAPACITY)) > 0 or not Count.valid(tank.cursor): return false
		held = Count.add(held,tank.amount)
	for amount in fuel.estates.values():
		if not Count.valid(amount): return false
		held = Count.add(held,amount)
	held = Count.add(Count.add(held,fuel.burned_subunits),fuel.lost_subunits)
	if held != Count.multiply_small(s.introduced.get("fuel","0"),SUBUNITS): return false
	var rest: Dictionary = whole_held.duplicate(true)
	var initial: Dictionary = s.introduced.duplicate(true)
	rest.erase("fuel")
	initial.erase("fuel")
	return Count.canonical(rest) == Count.canonical(initial)

static func _service(f: Dictionary) -> bool:
	return _keys(f,["contact_id","source_available","speed","blade_speed","engine_running"]) and _id(f.contact_id) and f.source_available is bool and f.source_available and _bounded_integer(f.speed,0,0) and _bounded_integer(f.blade_speed,0,0) and f.engine_running is bool and not f.engine_running

static func _live(s: Dictionary, id: Variant, generation: Variant) -> bool:
	return enabled(s) and _id(id) and s.vehicles.has(id) and _bounded_integer(generation,1,9007199254740991) and s.vehicles[id].generation == generation and s.vehicles[id].alive and s.fuel.tanks.has(_instance(id,generation))

static func _debit(owner: Dictionary, item: String, amount: String) -> void:
	var left: String = Count.subtract(owner[item],amount)
	if left == "0": owner.erase(item)
	else: owner[item] = left

static func _instance(id: String, generation: Variant) -> String: return id + ":" + str(int(generation))
static func _keys(value: Dictionary, names: Array) -> bool:
	if value.size() != names.size(): return false
	for name in names:
		if not value.has(name): return false
	return true
static func _id(value: Variant) -> bool: return value is String and not value.is_empty() and value.strip_edges() == value
static func _bounded_integer(value: Variant, low: int, high: int) -> bool:
	return (value is int or value is float) and is_finite(float(value)) and floor(float(value)) == value and value >= low and value <= high
static func _fail(reason: String) -> Dictionary: return {"ok":false,"reason":reason}
