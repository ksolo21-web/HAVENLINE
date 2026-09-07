class_name HavenlineNpcPopulation
extends RefCounted

# Serializable NPC state. This is gameplay, not proof that the art exists.
# Runtime presentation is fail-closed; headless tests opt into logical actors.
const Work = preload("res://scripts/crew_work.gd")
const CATALOG_PATH := "res://data/npc-catalog.json"
const KINDS := ["wood", "stone", "metal", "fuel"]
const PRICES := {"wood": 1, "stone": 2, "metal": 4, "fuel": 3}
const COUNTER := Vector2(5.4, 2.8)
const ENTRY := Vector2(12.5, 13.0)
const MAX_CUSTOMERS := 4
const SERVICE_SECONDS := 0.40
const RESCUE_SECONDS := 2.2
const PET_JOBS := ["follow", "scout"]
var catalog: Dictionary
var seed_value := 20260907
var next_id := 100
var credits := 0
var customer_clock := 0.0
var customers: Array = []
var encounters: Array = []
var recruits: Array = []
var pets: Array = []
var presented_ids: Array = []
var presentation_required := false
var enabled_templates: Array = []
var service_clock := 0.0
var service_id := -1
var rescue_clocks: Dictionary = {}
var arrivals := 0

func _init():
	catalog = JSON.parse_string(FileAccess.get_file_as_string(CATALOG_PATH))

func visible(id: int) -> bool:
	return not presentation_required or id in presented_ids

func template_available(key: String) -> bool:
	return catalog.templates.has(key) and (not presentation_required or key in enabled_templates)

func roll(id: int, channel: String, count: int) -> int:
	# A stable hash, rather than serialized 64-bit RNG state that JSON rounds.
	return (str(seed_value) + ":" + str(id) + ":" + channel).sha256_text().substr(0, 8).hex_to_int() % maxi(1, count)

func make_person(template: String, at: Vector2) -> Dictionary:
	if not catalog.templates.has(template): return {}
	var id := next_id
	next_id += 1
	var spec: Dictionary = catalog.templates[template]
	var names: Array = ["Milo", "Ellis", "Theo", "Rowan", "Jude", "Noah"] if spec.gender == "male" else ["Mara", "Lena", "June", "Ada", "Nora", "Iris"]
	if spec.role == "pet": names = ["Scout", "Moss", "Pip", "Ember", "Echo", "Clover"]
	return {"id": id, "template": template, "name": names[roll(id, "name", names.size())],
		"role": spec.role, "species": spec.species, "gender": spec.gender,
		"appearance": {"palette": roll(id, "palette", 6), "hair": roll(id, "hair", 4), "outfit": roll(id, "outfit", 3)},
		"position": at, "cooldown": 0.0, "job": "follow", "cargo": 0,
		"cargo_kind": "wood", "resource_kind": "wood", "delivering": false,
		"building": false, "work_clocks": {}}

func available_pool(role: String) -> Array:
	var result: Array = []
	for key in catalog[role + "_template_pool"]:
		if template_available(key): result.append(key)
	return result

func spawn_customer() -> bool:
	if customers.size() >= MAX_CUSTOMERS: return false
	var pool := available_pool("customer")
	if pool.is_empty(): return false
	# Avoid immediate exact-base repeats when more than one base is available.
	if customers.size() > 0 and pool.size() > 1:
		pool.erase(customers.back().template)
	var template: String = pool[roll(next_id, "customer_base", pool.size())]
	var c := make_person(template, ENTRY)
	var kind: String = KINDS[roll(c.id, "order", KINDS.size())]
	c.merge({"state": "arriving", "order_kind": kind, "remaining": 2 + roll(c.id, "amount", 4),
		"price": PRICES[kind], "patience": 90.0, "depart_clock": 0.0})
	customers.append(c)
	arrivals += 1
	return true

func add_encounter(template: String, at: Vector2) -> int:
	if not template_available(template): return -1
	if catalog.templates[template].role not in ["survivor", "pet"]: return -1
	if not is_finite(at.x) or not is_finite(at.y): return -1
	var c := make_person(template, at)
	encounters.append(c)
	return c.id

func actor_records() -> Array:
	return customers + encounters + recruits + pets

func active_customer() -> Dictionary:
	for c in customers:
		if c.state == "waiting" and c.position.distance_to(COUNTER) < 0.12 and visible(c.id): return c
	return {}

func action_for(sim) -> Dictionary:
	if sim.level < 2 or sim.durability <= 0: return {}
	var selected: Dictionary = {}
	for c in encounters:
		if not visible(c.id): continue
		var option: Dictionary = sim.candidate("npc_rescue", str(c.id), c.position, sim.contract.player.rescueRadius, 111.0)
		if not option.is_empty() and (selected.is_empty() or option.score > selected.score): selected = option
	var c := active_customer()
	if not c.is_empty() and sim.inventory[c.order_kind] > 0:
		var option: Dictionary = sim.candidate("customer_service", str(c.id), COUNTER, 1.8, 100.0)
		if not option.is_empty() and (selected.is_empty() or option.score > selected.score): selected = option
	return selected

func perform(sim, dt: float) -> bool:
	if sim.action.kind == "npc_rescue":
		var id: int = int(sim.action.id)
		for c in encounters:
			if c.id != id or not visible(id): continue
			var key := str(id)
			var progress: float = rescue_clocks.get(key, 0.0) + dt
			sim.action["progress"] = minf(1.0, progress / RESCUE_SECONDS)
			rescue_clocks[key] = progress
			if progress + 0.000001 >= RESCUE_SECONDS:
				if c.role == "pet": pets.append(c)
				else: recruits.append(c)
				encounters.erase(c)
				rescue_clocks.erase(key)
				sim.events.append({"type": "npc_recruited", "actor_id": id, "position": c.position, "role": c.role})
			return true
		return true
	if sim.action.kind != "customer_service": return false
	var c := active_customer()
	if c.is_empty() or str(c.id) != sim.action.id: return true
	if service_id != c.id:
		service_id = c.id
		service_clock = 0.0
	if sim.inventory[c.order_kind] <= 0: return true
	service_clock += dt
	sim.action["progress"] = minf(1.0, service_clock / SERVICE_SECONDS)
	if service_clock + 0.000001 >= SERVICE_SECONDS:
		service_clock = maxf(0.0, service_clock - SERVICE_SECONDS)
		# One atomic, conserved transfer per visible service beat. Never spend the
		# furnace/construction ledger or award a whole order more than once.
		sim.inventory[c.order_kind] -= 1
		c.remaining -= 1
		credits += c.price
		sim.events.append({"type": "customer_sale", "position": COUNTER, "resource": c.order_kind, "customer_id": c.id, "credits": c.price})
		if c.remaining <= 0:
			c.state = "leaving"
			service_id = -1
			service_clock = 0.0
	return true

func assign_job(id: int, job: String, resource: String = "wood") -> bool:
	if resource not in KINDS: return false
	for c in recruits:
		if c.id == id and job in Work.JOBS:
			c.job = job
			c.resource_kind = resource
			c.building = false
			if c.cargo > 0: c.delivering = true
			return true
	for p in pets:
		if p.id == id and job in PET_JOBS:
			p.job = job
			return true
	return false

func step(sim, dt: float):
	if dt <= 0 or not is_finite(dt): return
	# Customers are an expansion of the outpost, not a bypass of its rescue gate.
	if sim.level >= 2 and sim.rescued and sim.durability > 0:
		customer_clock = minf(12.0, customer_clock + dt)
		if customer_clock >= 12.0 and spawn_customer(): customer_clock = 0.0
	var slot := 0
	var leaving: Array = []
	for c in customers:
		if not visible(c.id): continue
		if c.state == "leaving":
			c.position = c.position.move_toward(ENTRY, 2.4 * dt)
			if c.position.distance_to(ENTRY) < 0.1: leaving.append(c)
			continue
		var target := COUNTER + Vector2(0, float(slot) * 1.15)
		slot += 1
		c.position = c.position.move_toward(target, 2.4 * dt)
		c.state = "waiting" if c.position.distance_to(target) < 0.1 else "arriving"
		var serving: bool = sim.action.get("kind") == "customer_service" and sim.action.get("id") == str(c.id) and sim.velocity.length() < 0.2
		if c.state == "waiting" and not serving:
			c.patience = maxf(0.0, c.patience - dt)
			if c.patience <= 0: c.state = "leaving"
	for c in leaving: customers.erase(c)
	var current := active_customer()
	if current.is_empty() or current.id != service_id:
		service_id = -1
		service_clock = 0.0
	for key in rescue_clocks.keys():
		var nearby := false
		for c in encounters:
			if str(c.id) == key and visible(c.id):
				nearby = sim.position.distance_to(c.position) <= sim.contract.player.rescueRadius + sim.tuning.automaticActionTargetHysteresis
		if not nearby: rescue_clocks.erase(key)
	for i in recruits.size(): step_recruit(sim, recruits[i], i, dt)
	for i in pets.size(): step_pet(sim, pets[i], i, dt)

func step_recruit(sim, c: Dictionary, slot: int, dt: float):
	if not visible(c.id): return
	Work.prepare(c)
	c.cooldown = maxf(0.0, c.cooldown - dt)
	if Work.threat_interrupt(sim, c, dt): return
	if c.delivering: Work.deliver(sim, c, dt); return
	if c.job == "build" and Work.work_build(sim, c, dt): return
	if c.job == "repair" and Work.work_repair(sim, c, dt): return
	if c.job == "gather":
		if c.cargo > 0 and (c.cargo_kind != c.resource_kind or c.cargo >= Work.DELIVERY_BATCH or Work.nearest_resource(sim, c, c.resource_kind).is_empty()):
			Work.deliver(sim, c, dt)
			return
		if Work.collect(sim, c, c.resource_kind, dt): return
	if c.cargo > 0: Work.deliver(sim, c, dt); return
	var a := TAU * float(slot % 8) / 8.0 + 0.35
	var target: Vector2 = sim.position + Vector2(cos(a), sin(a)) * (3.8 + floorf(slot / 8.0) * 1.3)
	if c.job == "guard": target = sim.defenses.north.position + Vector2(float(slot % 5) - 2.0, 2.0)
	Work.travel(c, target, dt)

func step_pet(sim, p: Dictionary, slot: int, dt: float):
	if not visible(p.id): return
	p.cooldown = maxf(0.0, p.cooldown - dt)
	var a := TAU * float(slot % 6) / 6.0 + 1.1
	var distance := 3.0 if p.job == "scout" else 1.7
	var target: Vector2 = sim.position + Vector2(cos(a), sin(a)) * distance
	if sim.threats_enabled:
		for e in sim.enemies:
			if e.health > 0 and p.position.distance_to(e.position) < 6.0:
				target = sim.point(sim.contract.world.furnace) + Vector2(1.8, 1.8)
				if p.job == "scout" and p.cooldown <= 0:
					p.cooldown = 3.0
					sim.events.append({"type": "pet_alert", "actor_id": p.id, "position": p.position})
				break
	p.position = p.position.move_toward(target, 4.2 * dt)
	# Pets are not human workers: no axes, mining, construction or ghost cargo.

func snapshot() -> Dictionary:
	var data := {"schema": 2, "seed": seed_value, "next_id": next_id, "credits": credits,
		"customer_clock": customer_clock, "service_clock": service_clock, "service_id": service_id,
		"rescue_clocks": rescue_clocks.duplicate(), "arrivals": arrivals}
	for group in ["customers", "encounters", "recruits", "pets"]:
		var saved: Array = []
		for person in get(group):
			var c: Dictionary = person.duplicate(true)
			c.position = [person.position.x, person.position.y]
			c.erase("activity")
			saved.append(c)
		data[group] = saved
	return data

static func number(value, maximum: float = 1e12) -> bool:
	return (value is int or value is float) and is_finite(float(value)) and value >= 0 and value <= maximum

static func count(value, maximum: float = 1e12) -> bool:
	return number(value, maximum) and fmod(float(value), 1.0) == 0.0

static func clocks(value) -> bool:
	if not value is Dictionary or value.size() > 256: return false
	for key in value:
		if not key is String or key.length() > 96 or not number(value[key], 60.0): return false
	return true

func restore(data: Dictionary) -> bool:
	# Validate every nested object before mutating live state.
	# JSON numbers decode as floats; validate integral value, not Variant type membership.
	if not count(data.get("schema"), 2) or int(data.schema) < 1: return false
	for key in ["seed", "next_id", "credits", "arrivals"]:
		if not count(data.get(key)): return false
	if data.next_id < 100: return false
	if not number(data.get("customer_clock"), 12.0) or not number(data.get("service_clock"), SERVICE_SECONDS): return false
	var service = data.get("service_id")
	if service != -1 and (not count(service) or service < 100): return false
	if not clocks(data.get("rescue_clocks")): return false
	var ids: Array = []
	var decoded := {}
	for group in ["customers", "encounters", "recruits", "pets"]:
		if not data.get(group) is Array or data[group].size() > 2048: return false
		if group == "customers" and data[group].size() > MAX_CUSTOMERS: return false
		decoded[group] = []
		for person in data[group]:
			if not person is Dictionary: return false
			var c: Dictionary = person.duplicate(true)
			# Only the retired schema-1 cat is migrated. Never repair tampered
			# role/species data or mutate the caller's save while validating.
			if c.get("template") == "pet_cat_01":
				if data.schema != 1 or c.get("role") != "pet" or c.get("species") != "cat" or c.get("gender") != "unspecified": return false
				c.template = "pet_fox_01"
				c.species = "fox"
			if not count(c.get("id")) or c.id < 100 or c.id >= data.next_id or int(c.id) in ids: return false
			ids.append(int(c.id))
			if not c.get("template") is String or not catalog.templates.has(c.template): return false
			var spec: Dictionary = catalog.templates[c.template]
			for key in ["role", "species", "gender"]:
				if c.get(key) != spec[key]: return false
			if group == "customers" and spec.role != "customer": return false
			if group == "recruits" and spec.role != "survivor": return false
			if group == "pets" and spec.role != "pet": return false
			if group == "encounters" and spec.role not in ["survivor", "pet"]: return false
			if not c.get("name") is String or c.name.is_empty() or c.name.length() > 48: return false
			if not c.get("position") is Array or c.position.size() != 2: return false
			for axis in c.position:
				if not (axis is int or axis is float) or not is_finite(float(axis)) or absf(axis) > 1000: return false
			if not c.get("appearance") is Dictionary: return false
			for key in {"palette": 5, "hair": 3, "outfit": 2}:
				if not count(c.appearance.get(key), {"palette": 5, "hair": 3, "outfit": 2}[key]): return false
			if c.get("job") not in (PET_JOBS if spec.role == "pet" else Work.JOBS): return false
			if not count(c.get("cargo")) or not number(c.get("cooldown"), 60.0): return false
			if c.get("cargo_kind") not in KINDS or c.get("resource_kind") not in KINDS: return false
			if not c.get("delivering") is bool or not c.get("building") is bool or not clocks(c.get("work_clocks")): return false
			if spec.role in ["pet", "customer"] and c.cargo != 0: return false
			if group == "customers":
				if c.get("state") not in ["arriving", "waiting", "leaving"] or c.get("order_kind") not in KINDS: return false
				if not count(c.get("remaining"), 5) or not count(c.get("price"), 4) or c.price != PRICES[c.order_kind]: return false
				if c.remaining == 0 and c.state != "leaving": return false
				if not number(c.get("patience"), 90.0) or not number(c.get("depart_clock"), 60.0): return false
			var saved: Dictionary = c.duplicate(true)
			saved.id = int(c.id)
			saved.position = Vector2(c.position[0], c.position[1])
			decoded[group].append(saved)
	if service != -1:
		var found := false
		for c in decoded.customers:
			if c.id == service and c.state == "waiting" and c.remaining > 0: found = true
		if not found: return false
	elif data.service_clock != 0: return false
	for key in data.rescue_clocks:
		var found := false
		for c in decoded.encounters:
			if str(c.id) == key: found = true
		if not found or data.rescue_clocks[key] > RESCUE_SECONDS: return false
	seed_value = int(data.seed)
	next_id = int(data.next_id)
	credits = int(data.credits)
	arrivals = int(data.arrivals)
	customer_clock = float(data.customer_clock)
	service_clock = float(data.service_clock)
	service_id = int(service)
	rescue_clocks = data.rescue_clocks.duplicate()
	for group in decoded: set(group, decoded[group])
	return true
