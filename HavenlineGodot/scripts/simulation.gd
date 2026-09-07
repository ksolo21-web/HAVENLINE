class_name HavenlineSimulation
extends RefCounted

# Deterministic, engine-independent gameplay state. Vector2 stores world X/Z.
# Rendering consumes events; it cannot invent inventory or progression.
const CrewWork = preload("res://scripts/crew_work.gd")
const KINDS = ["wood", "stone", "metal", "fuel"]
var contract: Dictionary
var tuning: Dictionary
var position := Vector2.ZERO
var velocity := Vector2.ZERO
var facing := Vector2.DOWN
var lead := 1
var inventory := {"wood": 0, "stone": 0, "metal": 0, "fuel": 0}
var stored := {"wood": 0, "stone": 0, "metal": 0, "fuel": 0}
var resources: Array = []
var level := 1
var durability := 260.0
var health := 100.0
var temperature := 100.0
var rescued := false
var rescue_progress := 0.0
var defenses: Dictionary = {}
var enemies: Array = []
var companions: Array = []
var wave := 0
var completed_waves := 0
var wave_timer := 48.0
var wave_active := false
var forest_unlocked := false
var elapsed := 0.0
var action: Dictionary = {}
var action_clocks: Dictionary = {}
var events: Array = []
var threat_serial := 0
# Runtime presentation capabilities are NOT saved progression and default to full
# simulation. The native review sets them before restoring any saved encounter.
var threats_enabled := true
var rescue_enabled := true
var presented_actor_ids: Array = []

func _init(data: Dictionary = {}, chosen_lead: int = 1):
	contract = data if not data.is_empty() else JSON.parse_string(FileAccess.get_file_as_string("res://data/reference-contract.json"))
	tuning = contract.openingLoopTuning
	lead = chosen_lead if chosen_lead in [1, 2] else 1
	position = point(contract.player.spawn)
	wave_timer = tuning.firstWaveDelaySeconds
	durability = tuning.furnaceMaxDurability
	for kind in ["wood", "stone"]:
		var index := 0
		for p in contract.world[kind + "Nodes"]:
			resources.append({"id": kind + str(index), "kind": kind, "position": point(p), "units": int(tuning[kind + "UnitsPerNode"]), "respawn": 0.0})
			index += 1
	for kind in ["metal", "fuel"]:
		resources.append({"id": kind + "0", "kind": kind, "position": point(contract.world[kind + "Node"]), "units": int(tuning[kind + "UnitsPerNode"]), "respawn": 0.0})
	for side in ["north", "south"]:
		defenses[side] = {"position": point(contract.world[side + "Barricade"]), "delivered": {"wood": 0, "stone": 0}, "built": false, "health": 0.0}
	var slot := 0
	for id in range(1, 5):
		if id == lead:
			continue
		companions.append({"id": id, "position": position + point(contract.characterSystem.companionFormationOffsets[slot]), "cooldown": 0.0, "job": "follow"})
		slot += 1

static func point(p: Array) -> Vector2:
	return Vector2(float(p[0]), float(p[2]))

static func meets(have: Dictionary, need: Dictionary) -> bool:
	for kind in need:
		if have.get(kind, 0) < need[kind]:
			return false
	return true

func carried() -> int:
	var total := 0
	for kind in KINDS:
		total += inventory[kind]
	return total

func warmth() -> float:
	return tuning.warmthRadiusLevel1 + (level - 1) * tuning.warmthRadiusPerAdditionalLevel

func gate_open() -> bool:
	return level >= 2 and rescued and defenses.north.built

func update_level():
	var before := level
	for value in [2, 3, 4]:
		if meets(stored, tuning["furnaceLevel" + str(value)]):
			level = maxi(level, value)
	if level != before:
		events.append({"type": "upgrade", "level": level, "position": point(contract.world.furnace)})

func first_carried(allowed: Array = KINDS) -> String:
	for kind in allowed:
		if inventory.get(kind, 0) > 0:
			return kind
	return ""

func candidate(kind: String, id: String, p: Vector2, radius: float, priority: float) -> Dictionary:
	var current: bool = action.get("id", "") == id and action.get("kind", "") == kind
	var distance := position.distance_to(p)
	if distance > radius + (float(tuning.automaticActionTargetHysteresis) if current else 0.0):
		return {}
	var alignment := facing.dot((p - position).normalized())
	return {"kind": kind, "id": id, "position": p, "score": priority + (1.0 - distance / radius) * tuning.automaticActionDistanceScoreWeight + alignment * tuning.automaticActionFacingWeight + (1.5 if current else 0.0)}

func choose_action() -> Dictionary:
	var options: Array = []
	var p: Dictionary = contract.player
	for enemy in enemies:
		if threats_enabled and enemy.health > 0:
			options.append(candidate("enemy", enemy.id, enemy.position, p.combatRadius, 200))
	var furnace := point(contract.world.furnace)
	if durability < tuning.furnaceMaxDurability and inventory.wood > 0:
		options.append(candidate("repair", "furnace", furnace, p.depositRadius, 130))
	elif carried() > 0 and durability > 0:
		options.append(candidate("deposit", "furnace", furnace, p.depositRadius, 95))
	if carried() > 0 and durability > 0:
		options.append(candidate("deposit", "storage", point(contract.world.storage), p.depositRadius, 95))
	if rescue_enabled and not rescued and level >= 2 and durability > 0:
		options.append(candidate("rescue", "survivor", point(contract.world.survivor), p.rescueRadius, 110))
	for side in defenses:
		var d: Dictionary = defenses[side]
		if not d.built:
			var need: Dictionary = tuning[side + "BarricadeBuild"]
			if (d.delivered.wood < need.wood and inventory.wood > 0) or (d.delivered.stone < need.stone and inventory.stone > 0):
				options.append(candidate("build", side, d.position, p.buildRadius, 80))
		elif d.health < 160 and inventory.wood > 0:
			options.append(candidate("defense_repair", side, d.position, p.buildRadius, 129))
	for resource in resources:
		if resource.units > 0:
			options.append(candidate("gather", resource.id, resource.position, p.interactionRadius, 30))
	var selected: Dictionary = {}
	for option in options:
		if not option.is_empty() and (selected.is_empty() or option.score > selected.score):
			selected = option
	return selected

func step(dt: float, input_vector: Vector2, sprint := false):
	if dt <= 0 or not is_finite(dt):
		return
	dt = minf(dt, 0.1) # App suspension must not fast-forward combat.
	events.clear()
	elapsed += dt
	var p: Dictionary = contract.player
	var input := input_vector.limit_length(1.0)
	var speed: float = p.runSpeed if sprint else p.walkSpeed
	var moving: bool = input.length() > tuning.automaticActionMovementCancelThreshold
	velocity = velocity.move_toward(input * speed, float(p.acceleration if moving else p.deceleration) * dt)
	position += velocity * dt
	position.x = clampf(position.x, -contract.world.boundX, contract.world.boundX)
	position.y = clampf(position.y, -contract.world.boundZ, contract.world.boundZ)
	if moving:
		facing = input.normalized()
	action = choose_action()
	if not moving and velocity.length() < 0.2 and not action.is_empty():
		perform_action(dt)
	step_companions(dt)
	step_threats(dt)
	step_climate(dt)
	prune_action_clocks()
	for resource in resources:
		if resource.units <= 0:
			resource.respawn += dt
			if resource.respawn >= 90:
				resource.units = int(tuning[resource.kind + "UnitsPerNode"])
				resource.respawn = 0.0

func perform_action(dt: float):
	var kind: String = action.kind
	var key: String = kind + ":" + action.id
	var duration := 0.5
	var resource: Dictionary = {}
	match kind:
		"gather":
			for item in resources:
				if item.id == action.id:
					resource = item
			if resource.is_empty():
				return
			duration = tuning.gatherSecondsPerUnit[resource.kind]
		"deposit": duration = tuning.furnaceDepositSecondsPerUnit
		"repair", "defense_repair": duration = tuning.furnaceRepairSecondsPerUnit
		"rescue": duration = tuning.survivorRescueSeconds
		"build": duration = tuning.playerConstructionSecondsPerUnit
		"enemy": duration = tuning.wolf.playerHitSeconds
	var progress: float = action_clocks.get(key, 0.0) + dt
	if progress + 0.00001 < duration:
		action_clocks[key] = progress
		action["progress"] = progress / duration
		return
	action_clocks[key] = maxf(0, progress - duration)
	action["progress"] = 0.0
	var event := {"type": kind, "position": action.position}
	match kind:
		"gather":
			if resource.units <= 0: return
			resource.units -= 1
			inventory[resource.kind] += 1
			event["resource"] = resource.kind
		"deposit":
			var item := first_carried()
			if item.is_empty(): return
			inventory[item] -= 1
			stored[item] += 1
			event["resource"] = item
			update_level()
		"repair":
			event["resource"] = "wood"
			inventory.wood -= 1
			durability = minf(tuning.furnaceMaxDurability, durability + tuning.furnaceRepairPerWood)
		"defense_repair":
			event["resource"] = "wood"
			inventory.wood -= 1
			defenses[action.id].health = minf(160, defenses[action.id].health + 42)
		"rescue":
			rescued = true
			rescue_progress = 1
			companions.append({"id": 5, "position": point(contract.world.survivor), "cooldown": 0.0, "job": "gather", "cargo": 0})
		"build":
			var defense: Dictionary = defenses[action.id]
			var need: Dictionary = tuning[action.id + "BarricadeBuild"]
			for item in ["wood", "stone"]:
				if defense.delivered[item] < need[item] and inventory[item] > 0:
					inventory[item] -= 1
					defense.delivered[item] += 1
					event["resource"] = item
					break
			if meets(defense.delivered, need):
				defense.built = true
				defense.health = 160.0
		"enemy":
			for enemy in enemies:
				if enemy.id == action.id:
					enemy.health -= tuning.wolf.playerDamagePerHit
	events.append(event)

func select_lead(id: int) -> bool:
	if id not in [1,2]: return false
	if id == lead: return true
	for index in companions.size():
		var c: Dictionary = companions[index]
		if c.id != id: continue
		CrewWork.prepare(c)
		# Transfer the incoming lead's actual cargo into the selected-lead stack;
		# never leave a duplicate copy on the outgoing lead's companion record.
		inventory[c.cargo_kind] += c.cargo
		var new_position: Vector2 = c.position
		c.id = lead
		c.position = position
		c.cargo = 0
		c.job = "follow"
		c.delivering = false
		c["building"] = false
		c.work_clocks.clear()
		lead = id
		position = new_position
		velocity = Vector2.ZERO
		action = {}
		action_clocks.clear()
		return true
	return false

func prune_action_clocks():
	# Progress can survive movement while still in reach, but dead/depleted or
	# abandoned targets must not accumulate unbounded obsolete save entries.
	for key in action_clocks.keys():
		var parts: PackedStringArray = key.split(":",true,1)
		if parts.size() != 2:
			action_clocks.erase(key)
			continue
		var kind := parts[0]
		var id := parts[1]
		var keep := false
		var radius: float = contract.player.interactionRadius
		if kind == "gather":
			for resource in resources:
				if resource.id == id and resource.units > 0:
					keep = position.distance_to(resource.position) <= radius + tuning.automaticActionTargetHysteresis
		elif kind == "enemy":
			radius = contract.player.combatRadius
			for enemy in enemies:
				if enemy.id == id and enemy.health > 0:
					keep = position.distance_to(enemy.position) <= radius + tuning.automaticActionTargetHysteresis
		else:
			var target: Vector2
			if id in defenses:
				target = defenses[id].position
				radius = contract.player.buildRadius
			elif kind == "rescue":
				target = point(contract.world.survivor)
				radius = contract.player.rescueRadius
			else:
				target = point(contract.world.storage if id == "storage" else contract.world.furnace)
				radius = contract.player.depositRadius
			keep = position.distance_to(target) <= radius + tuning.automaticActionTargetHysteresis
		if not keep: action_clocks.erase(key)

func assign_job(id: int, job: String, resource_kind := "wood") -> bool:
	if job not in CrewWork.JOBS or resource_kind not in KINDS: return false
	for c in companions:
		if c.id != id: continue
		CrewWork.prepare(c)
		c.job = job
		c.resource_kind = resource_kind
		c["building"] = false
		# Existing cargo is delivered intact before starting a different resource.
		if c.cargo > 0: c.delivering = true
		return true
	return false

func step_companions(dt: float):
	CrewWork.step(self, dt)

func step_threats(dt: float):
	if not threats_enabled: return
	if not wave_active and gate_open():
		wave_timer = maxf(0, wave_timer - dt)
		if wave_timer <= 0:
			wave += 1
			wave_active = true
			for i in range(2 + wave):
				threat_serial += 1
				enemies.append({"id": "wolf" + str(threat_serial), "position": Vector2((i - (wave + 1) * 0.5) * 1.8, -tuning.wolf.spawnZ if i % 2 == 0 else tuning.wolf.spawnZ), "health": float(tuning.wolf.health), "cooldown": 0.0})
			events.append({"type": "wave", "wave": wave})
	var alive := 0
	for enemy in enemies:
		if enemy.health <= 0:
			continue
		alive += 1
		enemy.cooldown -= dt
		var side := "north" if enemy.position.y < 0 else "south"
		var defense: Dictionary = defenses[side]
		var target := point(contract.world.furnace)
		if defense.built and defense.health > 0:
			target = defense.position
		var player_targeted: bool = enemy.position.distance_to(position) < 4.0
		if player_targeted:
			target = position
		if enemy.position.distance_to(target) > 1.2:
			enemy.position = enemy.position.move_toward(target, float(tuning.wolf.moveSpeed) * dt)
		elif enemy.cooldown <= 0:
			enemy.cooldown = tuning.wolf.attackSeconds
			if player_targeted:
				health = maxf(0, health - 8)
			elif defense.built and defense.health > 0:
				defense.health = maxf(0, defense.health - tuning.wolf.damageToBarricade)
			else:
				durability = maxf(0, durability - tuning.wolf.damageToFurnace)
	if wave_active and alive == 0:
		wave_active = false
		completed_waves += 1
		forest_unlocked = true
		wave_timer = maxf(tuning.minimumWaveDelaySeconds, tuning.firstWaveDelaySeconds - completed_waves * tuning.waveDelayReductionPerCompletedWave)
		enemies.clear()
		events.append({"type": "wave_clear"})

func step_climate(dt: float):
	var safe := position.distance_to(point(contract.world.furnace)) < warmth() and durability > 0
	temperature = clampf(temperature + (8.0 if safe else -0.65) * dt, 0, 100)
	if safe:
		health = minf(100, health + 4 * dt)
	elif temperature <= 0:
		health = maxf(0, health - 3 * dt)
	if health <= 0:
		position = point(contract.player.spawn)
		velocity = Vector2.ZERO
		health = 100
		temperature = 65
		events.append({"type": "recovery"})

func snapshot() -> Dictionary:
	var resource_state: Array = []
	for r in resources:
		resource_state.append({"id": r.id, "units": r.units, "respawn": r.respawn})
	var defense_state := {}
	for side in defenses:
		var d: Dictionary = defenses[side]
		defense_state[side] = {"delivered": d.delivered.duplicate(), "built": d.built, "health": d.health}
	var enemy_state: Array = []
	for e in enemies:
		enemy_state.append({"id": e.id, "position": [e.position.x, e.position.y], "health": maxf(0, e.health), "cooldown": e.cooldown})
	var crew: Array = []
	for c in companions:
		crew.append({"id": c.id, "position": [c.position.x, c.position.y], "cooldown": c.cooldown, "job": c.job, "cargo": c.get("cargo", 0), "cargo_kind": c.get("cargo_kind", "wood"), "resource_kind": c.get("resource_kind", "wood"), "delivering": c.get("delivering", false), "building": c.get("building", false), "work_clocks": c.get("work_clocks", {}).duplicate()})
	return {"schema": 1, "action_clocks": action_clocks.duplicate(), "facing": [facing.x, facing.y], "lead": lead, "position": [position.x, position.y], "inventory": inventory.duplicate(), "stored": stored.duplicate(), "level": level, "durability": durability, "health": health, "temperature": temperature, "rescued": rescued, "resources": resource_state, "defenses": defense_state, "wave": wave, "completed_waves": completed_waves, "wave_timer": wave_timer, "wave_active": wave_active, "enemies": enemy_state, "threat_serial": threat_serial, "forest_unlocked": forest_unlocked, "elapsed": elapsed, "companions": crew}

func restore(data: Dictionary) -> bool:
	# Validate the whole envelope before changing live gameplay state.
	if data.get("schema") != 1 or not valid_count(data.get("lead")): return false
	if int(data.lead) not in [1, 2] or float(data.lead) != float(int(data.lead)): return false
	for name in ["inventory", "stored", "defenses"]:
		if not data.get(name) is Dictionary: return false
	for name in ["resources", "enemies", "companions"]:
		if not data.get(name) is Array: return false
	if not valid_point(data.get("position")): return false
	for name in ["level", "durability", "health", "temperature", "wave", "completed_waves", "wave_timer", "threat_serial", "elapsed"]:
		if not valid_number(data.get(name)): return false
	for name in ["rescued", "wave_active", "forest_unlocked"]:
		if not data.get(name) is bool: return false
	for name in ["inventory", "stored"]:
		for kind in KINDS:
			if not valid_count(data[name].get(kind)): return false
	for side in defenses:
		var d = data.defenses.get(side)
		if not d is Dictionary or not d.get("delivered") is Dictionary or not d.get("built") is bool or not valid_number(d.get("health")): return false
		for kind in ["wood", "stone"]:
			if not valid_count(d.delivered.get(kind)): return false
			if d.delivered[kind] > tuning[side + "BarricadeBuild"][kind]: return false
	if data.resources.size() != resources.size(): return false
	for i in range(resources.size()):
		var r = data.resources[i]
		if not r is Dictionary or r.get("id") != resources[i].id or not valid_count(r.get("units")) or not valid_number(r.get("respawn")): return false
	var enemy_ids: Array = []
	for e in data.enemies:
		if not e is Dictionary or not e.get("id") is String or not valid_point(e.get("position")) or not valid_number(e.get("health")) or not valid_number(e.get("cooldown"), true): return false
		if e.id.is_empty() or e.id in enemy_ids: return false
		enemy_ids.append(e.id)
	for key in ["level", "wave", "completed_waves", "threat_serial"]:
		if not valid_count(data[key]): return false
	if not valid_clocks(data.get("action_clocks", {})): return false
	if not valid_point(data.get("facing", [0, 1])): return false
	var expected: Array = [1, 2, 3, 4]
	expected.erase(int(data.lead))
	if data.rescued: expected.append(5)
	var actual: Array = []
	for c in data.companions:
		if not c is Dictionary or not valid_point(c.get("position")) or c.get("job") not in CrewWork.JOBS or not valid_count(c.get("cargo")) or not valid_number(c.get("cooldown")): return false
		if not valid_count(c.get("id")): return false
		if c.get("cargo_kind", "wood") not in KINDS or c.get("resource_kind", "wood") not in KINDS: return false
		if not c.get("delivering", false) is bool or not c.get("building", false) is bool: return false
		if not valid_clocks(c.get("work_clocks", {})): return false
		actual.append(int(c.id))
	actual.sort()
	if actual != expected: return false
	lead = int(data.lead)
	position = Vector2(data.position[0], data.position[1])
	position.x = clampf(position.x, -contract.world.boundX, contract.world.boundX)
	position.y = clampf(position.y, -contract.world.boundZ, contract.world.boundZ)
	velocity = Vector2.ZERO
	for kind in KINDS:
		inventory[kind] = int(data.inventory[kind])
		stored[kind] = int(data.stored[kind])
	level = 1
	update_level()
	durability = clampf(data.durability, 0, tuning.furnaceMaxDurability)
	health = clampf(data.health, 0, 100)
	temperature = clampf(data.temperature, 0, 100)
	rescued = data.rescued
	for side in defenses:
		var d: Dictionary = data.defenses[side]
		defenses[side].delivered = {"wood": int(d.delivered.wood), "stone": int(d.delivered.stone)}
		defenses[side].built = meets(defenses[side].delivered, tuning[side + "BarricadeBuild"])
		defenses[side].health = clampf(d.health, 0, 160)
	for i in range(resources.size()):
		resources[i].units = int(data.resources[i].units)
		resources[i].respawn = data.resources[i].respawn
	companions.clear()
	for c in data.companions:
		companions.append({"id": int(c.id), "position": Vector2(c.position[0], c.position[1]), "cooldown": float(c.cooldown), "job": c.job, "cargo": int(c.cargo), "cargo_kind": c.get("cargo_kind", "wood"), "resource_kind": c.get("resource_kind", "wood"), "delivering": c.get("delivering", false), "building": c.get("building", false), "work_clocks": c.get("work_clocks", {}).duplicate()})
	enemies.clear()
	for e in data.enemies:
		enemies.append({"id": e.id, "position": Vector2(e.position[0], e.position[1]), "health": float(e.health), "cooldown": float(e.cooldown)})
	wave = int(data.wave)
	completed_waves = int(data.completed_waves)
	wave_timer = float(data.wave_timer)
	wave_active = data.wave_active
	forest_unlocked = data.forest_unlocked
	threat_serial = int(data.threat_serial)
	elapsed = float(data.elapsed)
	action = {}
	action_clocks = data.get("action_clocks", {}).duplicate()
	facing = Vector2(data.get("facing", [0, 1])[0], data.get("facing", [0, 1])[1]).normalized()
	events.clear()
	return true

static func valid_number(value, allow_negative := false) -> bool:
	return (value is float or value is int) and is_finite(float(value)) and (allow_negative or value >= 0)

static func valid_point(value) -> bool:
	return value is Array and value.size() == 2 and valid_number(value[0], true) and valid_number(value[1], true)

static func valid_count(value) -> bool:
	return valid_number(value) and float(value) < 9223372036854775807.0 and fmod(float(value), 1.0) == 0.0

static func valid_clocks(value) -> bool:
	if not value is Dictionary or value.size() > 256: return false
	for key in value:
		if not key is String or key.length() > 96 or not valid_number(value[key]) or value[key] > 60.0: return false
	return true
