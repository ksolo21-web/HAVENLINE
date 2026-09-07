extends "res://scripts/simulation.gd"

const Collision = preload("res://scripts/native_collision.gd")
const JOBS := ["follow", "gather", "wood", "stone", "metal", "fuel", "guard"]
var threat_presentation_ready := true
var _origin := Vector2.ZERO
var _resolving := false
var _step_seconds := 0.0
var _obstacles: Array = []
var _worker_paths: Dictionary = {}
var _nav: AStarGrid2D
var _nav_signature := ""

func step(dt: float, input_vector: Vector2, sprint := false):
	if dt <= 0 or not is_finite(dt): return
	_origin = position
	_step_seconds = minf(dt, .1)
	_obstacles = Collision.outpost(self)
	_resolving = true
	super.step(dt, input_vector, sprint)
	_resolving = false

func choose_action() -> Dictionary:
	if _resolving:
		position = Collision.solve(_origin, position - _origin, _obstacles, world_bounds())
		# Physics is resolved before choosing/performing proximity interactions.
	if not threat_presentation_ready:
		var deferred_enemies: Array = enemies
		enemies = []
		var selected: Dictionary = super.choose_action()
		enemies = deferred_enemies
		return selected
	return super.choose_action()

func world_bounds() -> Vector2:
	return Vector2(contract.world.boundX, contract.world.boundZ)

func assign_job(id: int, job: String) -> bool:
	if job not in JOBS: return false
	for c in companions:
		if c.id == id:
			c.job = job
			# In-flight cargo retains its original resource kind until delivered.
			if not c.has("cargo_kind"): c.cargo_kind = "wood"
			_worker_paths.erase(id)
			return true
	return false

func _prepare_navigation():
	var signature := str(_obstacles)
	if signature == _nav_signature and _nav != null: return
	_nav_signature = signature
	_nav = AStarGrid2D.new()
	_nav.region = Rect2i(-29, -33, 59, 67)
	_nav.cell_size = Vector2(.5, .5)
	_nav.diagonal_mode = AStarGrid2D.DIAGONAL_MODE_ONLY_IF_NO_OBSTACLES
	_nav.update()
	for y in range(-33, 34):
		for x in range(-29, 30):
			var p := Vector2(x, y) * .5
			if p.distance_squared_to(Collision.project(p, _obstacles, world_bounds())) > .0001:
				_nav.set_point_solid(Vector2i(x, y))
	_worker_paths.clear()

func _free_cell(point: Vector2) -> Vector2i:
	var center := Vector2i((point / .5).round())
	center = center.clamp(_nav.region.position, _nav.region.end - Vector2i.ONE)
	if not _nav.is_point_solid(center): return center
	var nearest := center
	var distance := INF
	for dy in range(-4, 5):
		for dx in range(-4, 5):
			var cell := center + Vector2i(dx, dy)
			if not _nav.is_in_boundsv(cell) or _nav.is_point_solid(cell): continue
			var d := (Vector2(cell) * .5).distance_squared_to(point)
			if d < distance:
				distance = d
				nearest = cell
	return nearest

func _move_worker(c: Dictionary, target: Vector2, dt: float):
	var destination := Collision.project(target, _obstacles, world_bounds())
	var entry: Dictionary = _worker_paths.get(c.id, {})
	if entry.is_empty() or destination.distance_to(entry.goal) > .7 or elapsed - entry.created > 1.2:
		entry = {"goal": destination, "created": elapsed, "points": _nav.get_point_path(_free_cell(c.position), _free_cell(destination)), "index": 0}
		_worker_paths[c.id] = entry
	var waypoint := destination
	while entry.index < entry.points.size() and c.position.distance_to(entry.points[entry.index]) < .22:
		entry.index += 1
	if entry.index < entry.points.size(): waypoint = entry.points[entry.index]
	elif c.position.distance_to(destination) > .8: return # Do not walk through a disconnected obstacle.
	var displacement: Vector2 = (waypoint - c.position).limit_length(3.7 * dt)
	c.position = Collision.solve(c.position, displacement, _obstacles, world_bounds())

func step_companions(dt: float):
	_prepare_navigation()
	for index in range(companions.size()):
		var c: Dictionary = companions[index]
		c.cooldown = maxf(0, c.cooldown - dt)
		if not c.has("cargo"): c.cargo = 0
		if not c.has("cargo_kind"): c.cargo_kind = "wood"
		var target: Vector2 = position + point(contract.characterSystem.companionFormationOffsets[index % 3])
		var job: String = c.job
		var gathering := job in ["gather", "wood", "stone", "metal", "fuel"]
		var kind := "wood" if job == "gather" else job
		# Changing a job cannot turn wood into metal or destroy carried resources.
		if c.cargo > 0 and (not gathering or c.cargo_kind != kind or c.cargo >= 4):
			target = point(contract.world.furnace) + Vector2(0, 1.55)
			if c.position.distance_to(target) < .38:
				stored[c.cargo_kind] += int(c.cargo)
				events.append({"type": "worker_deposit", "id": c.id, "resource": c.cargo_kind, "amount": c.cargo})
				c.cargo = 0
				update_level()
		elif gathering:
			var chosen: Dictionary = {}
			var nearest := INF
			for resource in resources:
				if resource.kind == kind and resource.units > 0:
					var distance: float = c.position.distance_squared_to(resource.position)
					if distance < nearest:
						nearest = distance
						chosen = resource
			if not chosen.is_empty():
				target = chosen.position + Vector2(0, 1.12)
				if c.position.distance_to(target) < .42 and c.cooldown <= 0:
					chosen.units -= 1
					c.cargo += 1
					c.cargo_kind = kind
					c.cooldown = maxf(.5, tuning.gatherSecondsPerUnit[kind] * 1.4)
			elif c.cargo > 0:
				target = point(contract.world.furnace) + Vector2(0, 1.55)
				if c.position.distance_to(target) < .38:
					stored[c.cargo_kind] += int(c.cargo)
					c.cargo = 0
					update_level()
		elif job == "guard":
			target = point(contract.world.northBarricade) + Vector2(-2.0 + index * .55, 1.35)
			for enemy in enemies:
				if threat_presentation_ready and enemy.health > 0 and enemy.position.distance_to(target) < 6:
					target = enemy.position
					break
		_move_worker(c, target, dt)
		for enemy in enemies:
			if threat_presentation_ready and enemy.health > 0 and c.position.distance_to(enemy.position) < 2.2 and c.cooldown <= 0:
				enemy.health -= 9
				c.cooldown = .95
				break

func snapshot() -> Dictionary:
	var data: Dictionary = super.snapshot()
	var workers := {}
	for c in data.companions:
		var original: Dictionary = companions.filter(func(item): return item.id == c.id)[0]
		workers[str(c.id)] = {"job": original.job, "cargo_kind": original.get("cargo_kind", "wood")}
		c.job = "gather" if original.job == "gather" else "follow"
	data["native_runtime"] = {"schema": 1, "workers": workers}
	return data

func restore(data: Dictionary) -> bool:
	var extension = data.get("native_runtime", {})
	if not extension is Dictionary: return false
	if not extension.is_empty():
		if extension.get("schema") != 1 or not extension.get("workers") is Dictionary: return false
		if not data.get("companions") is Array: return false
		if extension.workers.size() != data.companions.size(): return false
		for c in data.companions:
			if not c is Dictionary: return false
			var worker = extension.workers.get(str(int(c.get("id", -1))))
			if not worker is Dictionary or worker.get("job") not in JOBS or worker.get("cargo_kind") not in KINDS: return false
	if not super.restore(data): return false
	for c in companions:
		if extension.is_empty(): c.cargo_kind = "wood"
		else:
			var worker: Dictionary = extension.workers[str(c.id)]
			c.job = worker.job
			c.cargo_kind = worker.cargo_kind
	_nav_signature = ""
	_worker_paths.clear()
	return true

func step_threats(dt: float):
	if threat_presentation_ready: super.step_threats(dt)
