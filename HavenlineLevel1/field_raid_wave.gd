extends RefCounted
## Binds a timed camp assault to the real wolf bodies and existing camp perimeter.

const Wolf = preload("res://field_enemy.gd")
const Clock = preload("res://field_raid_director.gd")
const Sites = preload("res://field_raid_sites.gd")
const WAVE_LIMIT := 4
const SPAWN_LANES := [
	Vector2(-2.65, 6.2), Vector2(2.6, 6.8), Vector2(-.2, 9.1),
	Vector2(3.50, 9.7), Vector2(-3.25, 10.3), Vector2(0.0, 12.2)
]
var world
var encounter_ref: WeakRef
var encounters:
	get: return encounter_ref.get_ref()
var clock := Clock.new()
var sites := Sites.new()
var checkpoint_in := 15.
var sync_paid_layout := false

func setup(host: Node3D, handler: RefCounted) -> void:
	world = host
	encounter_ref = weakref(handler)
	sites.setup(host, clock)

func hp(id: String) -> int:
	return clock.hp(id)

func _camp_unattended() -> bool:
	if world.field_env.perimeter_stage < 1:
		return false
	var court: Vector4 = world.field_env.COURTS[world.field_env.perimeter_stage - 1]
	if not _away(world.actor.global_position, court):
		return false
	var owl = world.owl
	return not is_instance_valid(owl) or owl.state in ["locked", "dead", "defeated"] or _away(owl.global_position, court)

func permits_worker_target(wolf: Wolf) -> bool:
	var worker = world.survivor
	return is_instance_valid(worker) and worker.can_defend() and (worker.provoked(wolf) or _camp_unattended())

func _away(at: Vector3, court: Vector4) -> bool:
	var closest := Vector2(clampf(at.x, court.x, court.z), clampf(at.z, court.y, court.w))
	return closest.distance_squared_to(Vector2(at.x, at.z)) >= Clock.AWAY_DISTANCE * Clock.AWAY_DISTANCE

func _spawn_points(door: Node3D) -> PackedVector3Array:
	var result := PackedVector3Array()
	var outward := sites.outside_normal(door)
	var right := door.global_basis.x.normalized()
	for lane: Vector2 in SPAWN_LANES:
		var spot := door.global_position + outward * lane.y + right * lane.x
		if spot.distance_squared_to(world.actor.global_position) < 5.2 * 5.2 or not encounters.outside(spot, 1.975):
			continue
		var occupied: bool = world.enemies.any(func(wolf: Wolf): return wolf.hp > 0 and wolf.global_position.distance_squared_to(spot) < 5.1)
		if occupied:
			continue
		result.append(spot)
		if result.size() == WAVE_LIMIT:
			break
	return result

func _pick_entrance() -> String:
	var selected := ""
	var best := -INF
	var choices: Array[Node3D] = []
	choices.assign(world.gates)
	if clock.raids_started > 0:
		choices.append(sites.gate("fence-east-north"))
		choices.append(sites.gate("fence-east-south"))
	for door: Node3D in choices:
		if not is_instance_valid(door):
			continue
		if not door.active or _spawn_points(door).size() < 2:
			continue
		var choice := door.global_position.distance_to(world.actor.global_position)
		choice += (float(Clock.MAX_HP[door.gate_id]) - clock.hp(door.gate_id)) * .18
		if door.gate_id.begins_with("fence-"):
			choice += 2.1
		if choice > best:
			best = choice
			selected = door.gate_id
	return selected

func _spawn() -> bool:
	var door := sites.gate(clock.entrance)
	if not door:
		return false
	var points := _spawn_points(door)
	if points.size() < 2:
		return false
	var count := mini(points.size(), 3 if clock.raids_started == 0 else WAVE_LIMIT)
	clock.begin_attack()
	for i in count:
		encounters.serial += 1
		encounters._add(points[i], i == 0, encounters.serial, points[i], true)
	world._event("raid_started", world.actor.position, "enemy_attack")
	world._checkpoint_lifecycle()
	return true

func advance(delta: float) -> bool:
	if sync_paid_layout and world.camp_layout:
		sync_paid_layout = false
		sites.apply_condition()
	var stage: int = world.field_env.perimeter_stage
	var has_defenses: bool = stage >= 3 and (world.inventory.offer_open("watchtower") or world.inventory.complete("watchtower"))
	var unattended := has_defenses and _camp_unattended()
	var transition := clock.advance(delta, has_defenses, unattended, _pick_entrance)
	match transition:
		"warning":
			world._event("raid_warning", world.actor.position, "boss_arrival")
			world._checkpoint_lifecycle()
		"launch":
			_spawn()
		"expired":
			_finish(clock.breaches_during_attack)
	checkpoint_in -= delta
	if checkpoint_in <= 0.:
		checkpoint_in = 15.
		if clock.phase != "quiet":
			world._checkpoint_lifecycle()
	sites.update_notice(delta)
	if clock.phase != "attack":
		return false
	var count := 0
	for wolf in world.enemies.duplicate():
		if not wolf.raid_member:
			continue
		if wolf.hp <= 0:
			wolf.advance(delta)
			if not wolf.visible:
				encounters._remove(wolf)
			continue
		count += 1
		var previous: String = wolf.state
		_advance_raider(wolf, delta)
		encounters._observe_transition(wolf, previous)
	if count == 0:
		_finish(clock.breaches_during_attack)
		return false
	return true

func _finish(failed: bool) -> void:
	var left: bool = world.enemies.any(func(wolf: Wolf): return wolf.raid_member and wolf.hp > 0)
	for wolf in world.enemies.duplicate():
		if wolf.raid_member and wolf.hp > 0:
			encounters._remove(wolf)
	clock.end_attack(failed, encounters.rng.randf_range(Clock.REPEAT_MIN_WAIT, Clock.REPEAT_MAX_WAIT))
	var message := "Raid ended · repair the camp" if failed else "Raid repelled"
	if left and not failed:
		message = "Raiders withdrew"
	sites.flash_status(message)
	world._event("raid_ended" if failed else "raid_repelled", world.actor.position, "wolf_return" if failed else "victory")
	world._checkpoint_lifecycle()

func _near_attack(wolf: Wolf, at: Vector3, reach: float) -> bool:
	var delta := at - wolf.global_position
	return absf(delta.y) <= 1.65 and Vector2(delta.x, delta.z).length() <= reach

func _choose_target(wolf: Wolf) -> void:
	# Committed windups retain their original target. An invalid contact misses
	# instead of redirecting a queued hit to a different person.
	if wolf.state in ["windup", "lunge"] and is_instance_valid(wolf.target):
		return
	var door := sites.gate(clock.entrance)
	var is_in_camp: bool = world.field_env.is_inside_camp(wolf.global_position)
	var can_cross: bool = is_instance_valid(door) and door.breached
	var actor: Node3D = world.actor
	var exposed: bool = is_in_camp or not world.field_env.is_inside_camp(actor.global_position)
	if exposed and world.player_hp > 0 and _near_attack(wolf, actor.global_position, 9.0):
		wolf.retarget(actor, "player")
		return
	var owl = world.owl
	if is_instance_valid(owl) and owl.has_method("can_be_targeted") and owl.can_be_targeted() and _near_attack(wolf, owl.global_position, 7.2):
		if is_in_camp or not world.field_env.is_inside_camp(owl.global_position):
			wolf.retarget(owl, "owl")
			return
	var worker = world.survivor
	if permits_worker_target(wolf) and _near_attack(wolf, worker.actor.global_position, 8.5):
		if is_in_camp or not world.field_env.is_inside_camp(worker.actor.global_position):
			wolf.retarget(worker.actor, "survivor")
			return
	if not can_cross:
		var lane := posmod(wolf.spawn_id, 3)
		var marker_name := "RaidContactLane%d" % lane
		var aim := door.get_node_or_null(marker_name) as Node3D
		if not is_instance_valid(aim):
			aim = Node3D.new()
			aim.name = marker_name
			door.add_child(aim)
			aim.position.x = (lane - 1) * .66
		wolf.retarget(aim, clock.entrance)
		return
	var building := _nearest_objective(wolf)
	if not building.is_empty():
		wolf.retarget(sites.building(building), building)
		return
	# Guards within the breached interior are targetable. An adventurer far
	# from camp does not draw the raid pack out into ordinary wolf territory.
	var near_camp: bool = actor.global_position.distance_squared_to(door.global_position) < 17.0 * 17.0
	wolf.retarget(actor if near_camp and world.player_hp > 0 else door, "player" if near_camp and world.player_hp > 0 else "withdraw")

func _nearest_objective(wolf: Wolf) -> String:
	var target := ""
	var best := INF
	for id: String in Sites.BUILDINGS:
		var node := sites.building(id)
		if not is_instance_valid(node) or clock.is_down(id):
			continue
		var distance := wolf.global_position.distance_squared_to(node.global_position)
		if distance < best:
			target = id
			best = distance
	return target

func _advance_raider(wolf: Wolf, delta: float) -> void:
	_choose_target(wolf)
	if wolf.aim_role == "withdraw":
		var door := sites.gate(clock.entrance)
		var exit := door.global_position + sites.outside_normal(door) * 10.
		wolf._walk_to(exit, delta, _can_walk.bind(wolf), _steer)
		if wolf.global_position.distance_squared_to(exit) < .60:
			encounters._remove(wolf)
		return
	wolf.advance(delta, _can_walk.bind(wolf), _can_contact(wolf, false), _steer)

func _near_opening(wolf: Wolf, door: Node3D) -> bool:
	var at := door.to_local(wolf.global_position)
	return absf(at.x) <= door.HALF_SPAN + .65 and absf(at.z) < 4.3

func _steer(wolf: Wolf, goal: Vector3) -> Vector3:
	var door := sites.gate(clock.entrance)
	var here := wolf.global_position
	var from_inside: bool = world.field_env.is_inside_camp(here)
	var to_inside: bool = world.field_env.is_inside_camp(goal)
	var outward := sites.outside_normal(door)
	if door.breached and from_inside != to_inside:
		var pass_point := door.global_position + outward * (1.2 if from_inside else -1.2)
		if not from_inside and not _near_opening(wolf, door):
			return encounters._steer(wolf, door.global_position + outward * 2.45)
		return pass_point - here
	if from_inside:
		return goal - here
	if _near_opening(wolf, door) and wolf.aim_role == clock.entrance:
		return goal - here
	return encounters._steer(wolf, goal)

func _can_walk(from: Vector3, to: Vector3, wolf: Wolf) -> bool:
	var door := sites.gate(clock.entrance)
	var inside: bool = world.field_env.is_inside_camp(from) or world.field_env.is_inside_camp(to)
	var near_gate := _near_opening(wolf, door)
	var radius := .395 * wolf.size_factor()
	if inside or near_gate:
		if not world.field_env.travel_clear(from, to, radius):
			return false
		for other in world.enemies:
			if other == wolf or other.hp <= 0:
				continue
			var clearance: float = radius + .395 * other.size_factor()
			var gap: float = to.distance_squared_to(other.global_position)
			if gap < clearance * clearance and gap < from.distance_squared_to(other.global_position):
				return false
		return true
	return encounters.can_walk(from, to, wolf)

func _can_contact(wolf: Wolf, committed: bool) -> bool:
	if clock.phase != "attack" or not is_instance_valid(wolf.target):
		return false
	match wolf.aim_role:
		"player":
			if world.player_hp <= 0 or (world.field_env.is_inside_camp(world.actor.global_position) and not allows_inside_contact(wolf, world.actor.global_position)):
				return false
		"owl":
			if not is_instance_valid(world.owl) or not world.owl.can_be_targeted():
				return false
		"survivor":
			if not permits_worker_target(wolf):
				return false
		_:
			if clock.is_down(wolf.aim_role):
				return false
	# A gate is the solid object we intend to strike. The other targets must
	# have the unobstructed real-world contact the jaw pose reports.
	if not committed or wolf.aim_role == clock.entrance:
		return true
	return world.field_env.travel_clear(wolf.global_position, wolf._target_point(), .02)

func allows_inside_contact(wolf: Node3D, at: Vector3) -> bool:
	if clock.phase != "attack" or not is_instance_valid(wolf) or not ("raid_member" in wolf and wolf.raid_member):
		return false
	if not world.field_env.is_inside_camp(wolf.global_position):
		return false
	return world.field_env.travel_clear(wolf.global_position, at, .02)

func contact(amount: int, wolf: Wolf) -> void:
	if not _can_contact(wolf, true):
		return
	match wolf.aim_role:
		"player":
			world._player_hit(amount, wolf)
		"owl":
			world.owl.apply_enemy_contact(wolf, amount)
		"survivor":
			world.survivor.apply_enemy_contact(wolf, amount)
		_:
			damage_site(wolf.aim_role, amount * 2)

func damage_site(id: String, amount: int) -> bool:
	if not sites.site_position(id).is_finite() or not clock.damage(id, amount):
		return false
	var at := sites.site_position(id)
	world._event("raid_site_broken" if clock.is_down(id) else "raid_site_hit", at, "deplete_wood" if clock.is_down(id) else "impact_wood")
	if world.has_method("_combat_number"):
		world._combat_number(at + Vector3.UP * 1.75, "−%d" % amount, Color("#ffbc7c"))
	sites.apply_condition()
	world._checkpoint_lifecycle()
	return true

func reconcile_perimeter() -> void:
	if world.camp_active and not clock.condition.is_empty():
		sites.apply_condition()
	# The authored gate may move on camp expansion. A raised fence cannot
	# strand or erase a live raid actor associated with the same siege.
	if clock.phase != "attack":
		return
	var door := sites.gate(clock.entrance)
	if not door:
		return
	var outward := sites.outside_normal(door)
	var row := 0
	for wolf: Wolf in world.enemies:
		if wolf.raid_member and wolf.hp > 0 and world.field_env.is_inside_camp(wolf.global_position) and not door.breached:
			var right := door.global_basis.x.normalized()
			wolf.global_position = door.global_position + outward * (3.6 + row * 1.8) + right * (1.45 if row % 2 == 0 else -1.45)
			wolf.route_destination = Vector2.INF
			row += 1
