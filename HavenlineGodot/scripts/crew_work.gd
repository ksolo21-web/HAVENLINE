class_name HavenlineCrewWork
extends RefCounted

# Tasks commit one unit only when their clock reaches the work beat. Movement,
# threats and reassignment cannot duplicate, discard or instantly unload cargo.
const JOBS = ["follow", "gather", "build", "repair", "guard"]
const MOVE_SPEED := 3.7
const GATHER_SECONDS := 1.2
const DELIVERY_BATCH := 4 # Routing threshold, NOT an inventory capacity.

static func prepare(c: Dictionary):
	for key in {"cargo": 0, "cargo_kind": "wood", "resource_kind": "wood", "delivering": false, "work_clocks": {}}:
		if not c.has(key):
			c[key] = {"cargo": 0, "cargo_kind": "wood", "resource_kind": "wood", "delivering": false, "work_clocks": {}}[key]
	c["activity"] = {"kind": "follow", "progress": 0.0}

static func travel(c: Dictionary, target: Vector2, dt: float) -> bool:
	c.position = c.position.move_toward(target, MOVE_SPEED * dt)
	return c.position.distance_to(target) <= 0.08

static func beat(c: Dictionary, key: String, seconds: float, dt: float) -> bool:
	var elapsed: float = c.work_clocks.get(key, 0.0) + dt
	c.activity["progress"] = minf(1.0, elapsed / seconds)
	if elapsed + 0.000001 < seconds:
		c.work_clocks[key] = elapsed
		return false
	c.work_clocks[key] = maxf(0.0, elapsed - seconds)
	return true

static func emit(sim, c: Dictionary, kind: String, target: Vector2, resource := ""):
	sim.events.append({"type": "worker_" + kind, "actor_id": c.id,
		"position": c.position, "target": target, "resource": resource})

static func nearest_resource(sim, c: Dictionary, kind: String) -> Dictionary:
	var nearest: Dictionary = {}
	var distance := INF
	for resource in sim.resources:
		if resource.kind != kind or resource.units <= 0: continue
		var d: float = c.position.distance_squared_to(resource.position)
		if d < distance:
			nearest = resource
			distance = d
	return nearest

static func collect(sim, c: Dictionary, kind: String, dt: float) -> bool:
	var resource := nearest_resource(sim, c, kind)
	if resource.is_empty(): return false
	c.activity = {"kind": "gather", "target_id": resource.id, "progress": 0.0}
	if not travel(c, resource.position + Vector2(0, 1.1), dt): return true
	if beat(c, "gather:" + resource.id, GATHER_SECONDS, dt) and resource.units > 0:
		resource.units -= 1
		c.cargo += 1
		c.cargo_kind = kind
		emit(sim, c, "gather", resource.position, kind)
	return true

static func deliver(sim, c: Dictionary, dt: float):
	if c.cargo <= 0:
		c.delivering = false
		return
	c.delivering = true
	var target: Vector2 = sim.point(sim.contract.world.furnace)
	c.activity = {"kind": "deposit", "target_id": "furnace", "progress": 0.0}
	if not travel(c, target + Vector2(1.4, 0), dt): return
	if beat(c, "deposit:furnace", float(sim.tuning.furnaceDepositSecondsPerUnit), dt):
		c.cargo -= 1
		sim.stored[c.cargo_kind] += 1
		sim.update_level()
		emit(sim, c, "deposit", target, c.cargo_kind)
		if c.cargo == 0: c.delivering = false

static func threat_interrupt(sim, c: Dictionary, dt: float) -> bool:
	if not sim.threats_enabled: return false
	var nearest: Dictionary = {}
	var distance := INF
	for enemy in sim.enemies:
		if enemy.health <= 0: continue
		var d: float = c.position.distance_to(enemy.position)
		if d < distance:
			distance = d
			nearest = enemy
	if nearest.is_empty(): return false
	if distance <= 2.2:
		c.activity = {"kind": "enemy", "target_id": nearest.id, "progress": 0.0}
		if c.cooldown <= 0:
			nearest.health = maxf(0.0, nearest.health - 9.0)
			c.cooldown = 0.95
			emit(sim, c, "enemy", nearest.position)
		return true
	if c.job == "guard" and distance <= 8.0:
		c.activity = {"kind": "intercept", "target_id": nearest.id, "progress": 0.0}
		travel(c, nearest.position, dt)
		return true
	if c.job in ["gather", "build", "repair"] and distance < 4.4:
		c.activity = {"kind": "retreat", "progress": 0.0}
		travel(c, sim.point(sim.contract.world.furnace) + Vector2(1.4, 0), dt)
		return true
	return false

static func work_build(sim, c: Dictionary, dt: float) -> bool:
	# North is first in the opening contract; no early wave without its materials.
	for side in ["north", "south"]:
		var defense: Dictionary = sim.defenses[side]
		if defense.built: continue
		var need: Dictionary = sim.tuning[side + "BarricadeBuild"]
		var kind := "wood" if defense.delivered.wood < need.wood else "stone"
		var missing: int = int(need[kind] - defense.delivered[kind])
		if c.cargo > 0 and c.cargo_kind != kind:
			deliver(sim, c, dt)
			return true
		var available := nearest_resource(sim, c, kind)
		if c.cargo == 0 or (c.cargo < mini(DELIVERY_BATCH, missing) and not available.is_empty() and not c.get("building", false)):
			return collect(sim, c, kind, dt)
		c["building"] = true
		c.activity = {"kind": "build", "target_id": side, "progress": 0.0}
		if travel(c, defense.position + Vector2(0, 1.1), dt) and beat(c, "build:" + side, float(sim.tuning.helperConstructionSecondsPerUnit), dt):
			if defense.delivered[kind] < need[kind] and c.cargo > 0:
				c.cargo -= 1
				defense.delivered[kind] += 1
				emit(sim, c, "build", defense.position, kind)
			if sim.meets(defense.delivered, need):
				defense.built = true
				defense.health = 160.0
			if c.cargo == 0 or defense.built: c.building = false
		return true
	return false

static func work_repair(sim, c: Dictionary, dt: float) -> bool:
	var target: Vector2 = sim.point(sim.contract.world.furnace)
	var id := "furnace"
	if sim.durability >= sim.tuning.furnaceMaxDurability:
		id = ""
		for side in ["north", "south"]:
			if sim.defenses[side].built and sim.defenses[side].health < 160:
				id = side
				target = sim.defenses[side].position
				break
	if id.is_empty(): return false
	if c.cargo > 0 and c.cargo_kind != "wood":
		deliver(sim, c, dt)
		return true
	if c.cargo == 0: return collect(sim, c, "wood", dt)
	c.activity = {"kind": "repair", "target_id": id, "progress": 0.0}
	if travel(c, target + Vector2(1.4, 0), dt) and beat(c, "repair:" + id, float(sim.tuning.furnaceRepairSecondsPerUnit), dt):
		c.cargo -= 1
		if id == "furnace":
			sim.durability = minf(float(sim.tuning.furnaceMaxDurability), sim.durability + sim.tuning.furnaceRepairPerWood)
		else:
			sim.defenses[id].health = minf(160.0, sim.defenses[id].health + sim.tuning.furnaceRepairPerWood)
		emit(sim, c, "repair", target, "wood")
	return true

static func step(sim, dt: float):
	for index in range(sim.companions.size()):
		var c: Dictionary = sim.companions[index]
		prepare(c)
		# A review scene may not simulate unrendered actors behind the player's back.
		if not sim.presented_actor_ids.is_empty() and c.id not in sim.presented_actor_ids: continue
		c.cooldown = maxf(0.0, c.cooldown - dt)
		if threat_interrupt(sim, c, dt): continue
		if c.delivering:
			deliver(sim, c, dt)
			continue
		if c.job == "build" and work_build(sim, c, dt): continue
		if c.job == "repair" and work_repair(sim, c, dt): continue
		if c.job == "gather":
			if c.cargo > 0 and (c.cargo_kind != c.resource_kind or c.cargo >= DELIVERY_BATCH or nearest_resource(sim, c, c.resource_kind).is_empty()):
				deliver(sim, c, dt)
				continue
			if collect(sim, c, c.resource_kind, dt): continue
		if c.cargo > 0:
			deliver(sim, c, dt)
			continue
		var target: Vector2 = sim.position + sim.point(sim.contract.characterSystem.companionFormationOffsets[index % 3])
		if c.job == "guard":
			target = sim.defenses.north.position + Vector2(0, 2.0)
			c.activity.kind = "guard"
		travel(c, target, dt)
