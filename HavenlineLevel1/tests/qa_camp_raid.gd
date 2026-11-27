extends SceneTree

const Guard = preload("res://tests/lifecycle_test_profile.gd")
const Clock = preload("res://field_raid_director.gd")
const Wolf = preload("res://field_enemy.gd")
const Progress = preload("res://field_progression.gd")
var field
var results := {}

func _initialize() -> void:
	if not Guard.isolated(self, "res://tests/qa_camp_raid.gd"):
		call_deferred("run")

func check(label: String, passed: bool) -> void:
	results[label] = passed
	if not passed:
		push_error("Raid check failed: " + label)

func _clock_checks() -> void:
	var state := Clock.new()
	var pick := func(): return "gate-east"
	state.advance(1500., false, true, pick)
	check("unbuilt camp doesn't advance first cooldown", state.seconds_left == 1200.)
	state.advance(1200., true, false, pick)
	check("a defender near camp prevents a due raid from starting", state.phase == "quiet")
	check("exposed camp receives its full warning", state.advance(.016, true, true, pick) == "warning" and state.seconds_left == 300.)
	check("no hit during warning", not state.damage("gate-east", 10))
	state.advance(94.25, true, false, pick)
	var in_progress: Dictionary = JSON.parse_string(JSON.stringify(state.snapshot()))
	var returned := Clock.new()
	check("warning survives JSON round trip", returned.restore(in_progress) and is_equal_approx(returned.seconds_left, 205.75))
	check("no launch a hundredth of a second early", returned.advance(205.74, true, false, pick).is_empty())
	check("launch only after all five minutes", returned.advance(.01, true, false, pick) == "launch")
	returned.begin_attack()
	returned.end_attack(false, 2800.)
	check("repelled raid starts independent cooldown", returned.seconds_left == 2800.)
	returned.end_attack(true, 2800.)
	check("failed raid grants 60 minutes between attack end and earliest start", returned.seconds_left + Clock.WARNING_SECONDS == 3600.)

func _fund(id: String) -> void:
	for kind: String in field.inventory.remaining(id):
		var units := int(field.inventory.remaining(id)[kind])
		for i in units:
			field.inventory.collect("raid-fixture-" + id + "-" + kind + "-" + str(i), kind)
		assert(field.inventory.payment(id,kind,false,units))

func _live() -> Array:
	return field.enemies.filter(func(wolf: Wolf): return wolf.raid_member and wolf.hp > 0)

func _repair_site(id: String, total_spent: Dictionary) -> void:
	var raid = field.encounters.raids
	var bill: Dictionary = raid.clock.repair_bill(id)
	for kind: String in bill:
		total_spent[kind] = int(total_spent.get(kind, 0)) + int(bill[kind])
		for i in bill[kind]:
			field.inventory.collect("raid-repair-" + id + "-" + kind + "-" + str(i), kind)
	field.actor.global_position = raid.sites.repair_position(id)
	check("paid repair of " + id, raid.sites.repair(id))

func _crew_target_order() -> void:
	var worker = field.survivor
	var ledger = field.inventory
	for i in ledger.survivor_cost:
		ledger.collect("raid-survivor-fee-" + str(i), "wood")
	ledger.carried.wood -= ledger.survivor_cost
	ledger.settlement.survivor_wood = ledger.survivor_cost
	ledger.settlement.survivor_paid = true
	field.actor.global_position = worker.actor.global_position
	check("native proximity rescues the bought survivor", field.settlement_loop.rescue())
	worker.actor.global_position = Vector3(14.0, 0., -5.1)
	var wolf_position := Vector3(13.8, 0., -3.25)
	field.encounters.serial += 1
	var wolf: Wolf = field.encounters._add(wolf_position, false, field.encounters.serial, wolf_position)
	field.actor.global_position = Vector3.ZERO
	check("resident player protects the nearby unprovoking survivor", not field.encounters._ambient_target(wolf, false) and wolf.aim_role == "player")
	worker.retaliation[wolf.get_instance_id()] = field.simulation_time + 2.0
	check("a hostile already provoked by the survivor may retaliate", field.encounters._ambient_target(wolf, false) and wolf.aim_role == "survivor")
	worker.retaliation.clear()
	field.actor.global_position = Vector3(-44.0, 0., -29.0)
	check("isolated survivor is a legal target with both defenders far away", field.encounters._ambient_target(wolf, true) and wolf.aim_role == "survivor")
	var hp: int = ledger.settlement.survivor_hp
	for tick in 160:
		field.encounters.advance(1.0 / 60.)
		if ledger.settlement.survivor_hp < hp:
			break
	check("ordinary jaw contact reduces the isolated survivor's actual HP", ledger.settlement.survivor_hp < hp)
	if is_instance_valid(wolf): field.encounters._remove(wolf)
	worker.actor.global_position = Vector3(-6.4, 0., 3.8)

func _repeat_raid_fence(total_spent: Dictionary) -> void:
	var raid = field.encounters.raids
	for id: String in ["camp_cooker", "saw_bench", "quarry_drill", "watchtower"]:
		_fund(id)
	field._inventory_changed()
	for at: Vector3 in [Vector3(-45.,0.,-42.), Vector3(-42.,0.,42.), Vector3(-47.,0.,-.6), Vector3(-39.,0.,-11.)]:
		field.actor.global_position = at
		if raid._pick_entrance().begins_with("fence-"):
			break
	field.encounters.remaining = 999.
	raid.clock.seconds_left = .005
	field.encounters.advance(.016)
	var id: String = raid.clock.entrance
	check("a repeat wave warns about an actual east fence section", id.begins_with("fence-") and raid.clock.phase == "warning" and raid.clock.seconds_left == 300.)
	if not id.begins_with("fence-"):
		return
	field.encounters.advance(300.)
	var port: Node3D = raid.sites.gate(id)
	var cross: Vector3 = raid.sites.outside_normal(port) * 1.35
	var at := port.global_position
	var row: int = raid.sites.FENCE_IDS.find(id)
	check("intact fence rejects travel across its collision before the raid", not field.field_env.travel_clear(at - cross, at + cross, .18) and field.camp_colliders[row].collision_layer == 1)
	var breach_tick := -1
	for tick in 2300:
		field.encounters.advance(1.0 / 60.)
		if port.breached:
			breach_tick = tick
			break
	print("RAID_REPEAT entrance=", id, " breach=", breach_tick)
	check("authored bite eventually breaks the warned fence", breach_tick >= 0)
	check("breached fence opens both physical and analytical collision", field.field_env.travel_clear(at - cross, at + cross, .18) and field.camp_colliders[row].collision_layer == 0)
	var inside := false
	for tick in 1100:
		field.encounters.advance(1.0 / 60.)
		inside = _live().any(func(wolf: Wolf): return field.field_env.is_inside_camp(wolf.global_position))
		if inside: break
	check("repeat raiders walk through the new physical fence opening", inside)
	# Inject heavy damage through the raid's real structure event binding to
	# exercise every paid workshop without artificially steering the wolf pack.
	for id_to_break: String in ["cooker", "saw", "drill", "tower"]:
		check("paid damageable site exists for " + id_to_break, is_instance_valid(raid.sites.building(id_to_break)))
		check("raid damage can destroy " + id_to_break, raid.damage_site(id_to_break, Clock.MAX_HP[id_to_break]))
	check("destroyed cooker cannot accept manual or automated input", not field.lakeshore.available and field.lakeshore.guard.collision_layer == 0)
	check("destroyed mills stop operating and open their hulls", not field.processors.available and field.processors.guards.wood.collision_layer == 0 and field.processors.guards.stone.collision_layer == 0)
	raid.clock.seconds_left = .005
	field.encounters.advance(.016)
	for site: String in [id, "cooker", "saw", "drill", "tower"]:
		_repair_site(site, total_spent)
	check("rebuilt fence closes both physical and analytical collision", not field.field_env.travel_clear(at - cross, at + cross, .18) and field.camp_colliders[row].collision_layer == 1)
	check("rebuilding restores each paid machine", field.lakeshore.available and field.processors.available and not field.encounters.is_structure_down("tower"))

func run() -> void:
	_clock_checks()
	field=load("res://field_opening.tscn").instantiate()
	root.add_child(field)
	await physics_frame
	field.set_physics_process(false)
	field.world_landscape.set_physics_process(false)
	field.carry.set_physics_process(false)
	for id: String in ["center_hearth", "expansion_1", "storage_wood", "storage_stone", "storage_meat", "expansion_2"]:
		_fund(id)
	field._apply_hearth(true,false)
	for wolf: Wolf in field.enemies.duplicate():
		field.encounters._remove(wolf)
	await process_frame
	var raid = field.encounters.raids
	field.encounters.remaining = 999.
	field.actor.global_position = Vector3(-44.,0.,-19.)
	raid.clock.seconds_left = .005
	field.encounters.advance(.016)
	var id: String = raid.clock.entrance
	check("the real paid camp shows a 5:00 warning while player is far away", raid.clock.phase == "warning" and not id.is_empty() and raid.sites.raid_label.contains("5:00"))
	check("no early camp attackers", _live().is_empty())
	field.encounters.advance(298.9)
	var snapshot: Dictionary=JSON.parse_string(JSON.stringify(field.lifecycle.snapshot()))
	check("native world snapshot restores the warning without spawning", field.lifecycle.restore(snapshot) and raid.clock.phase == "warning" and _live().is_empty())
	field.encounters.advance(1.11)
	var live_count := _live().size()
	check("the raid spawns real wolves at its warned camp", raid.clock.phase == "attack" and live_count >= 2)
	check("no automatic hit on a distant player", field.player_hp == field.MAX_HP)
	var entrance: Node3D = raid.sites.gate(id)
	var start_hp: int = raid.clock.hp(id)
	var first_contact_tick := -1
	var first_breach_tick := -1
	var first_furnace_tick := -1
	var entered := false
	for tick in 2800:
		field.encounters.advance(1./60.)
		if first_contact_tick < 0 and raid.clock.hp(id) < start_hp:
			first_contact_tick = tick
		if first_breach_tick < 0 and entrance.breached:
			first_breach_tick = tick
		if not entered:
			for wolf: Wolf in _live():
				entered = entered or field.field_env.is_inside_camp(wolf.global_position)
		if first_furnace_tick < 0 and raid.clock.hp("furnace") < Clock.MAX_HP.furnace:
			first_furnace_tick = tick
		if raid.clock.is_down("furnace"):
			break
	check("raid wolf jaws physically attack the warned gate", first_contact_tick >= 0)
	check("paid gate eventually breaches and opens its collision", entrance.breached and first_breach_tick >= first_contact_tick and entrance._leaf_bodies.all(func(body: Node3D): return body.collision_layer == 0))
	check("a real raid wolf enters through the breach without the player nearby", entered)
	check("furnace is attacked inside camp after entry", first_furnace_tick >= 0)
	check("destroyed furnace extinguishes the healing fire", raid.clock.is_down("furnace") and not field.field_env.hearth_fire.fired)
	print("RAID_NATIVE first-contact=", first_contact_tick, " breach=", first_breach_tick, " furnace=", first_furnace_tick, " entrance=", id)
	var full: Dictionary=JSON.parse_string(JSON.stringify(field.lifecycle.snapshot()))
	check("live enemies and breached gate survive world snapshot", field.lifecycle.restore(full) and _live().size() > 0 and entrance.breached)
	# Resolution must be driven by the same timed attack, not a direct health reset.
	raid.clock.seconds_left = .01
	field.encounters.advance(.02)
	check("a lost attack ends and allows a repair period", raid.clock.phase == "quiet" and raid.clock.seconds_left == Clock.FAILED_WAIT)
	var total_spent := {}
	for site_id: String in [id, "furnace"]:
		_repair_site(site_id, total_spent)
	check("hearth lights and gate collides once repaired", field.field_env.hearth_fire.fired and not entrance.breached and entrance._leaf_bodies.all(func(body: Node3D): return body.collision_layer == 1))
	_crew_target_order()
	_repeat_raid_fence(total_spent)
	check("repair accounting includes every used unit", raid.clock.spend == total_spent)
	var saved: Dictionary=JSON.parse_string(JSON.stringify(field.inventory.snapshot()))
	check("actual game inventory can restore the conserved repair journal", field.inventory.restore(saved))
	print("CAMP_RAID_TESTS ", JSON.stringify(results))
	await Guard.drain_field_audio(self,field)
	quit(0 if results.values().all(func(passed: bool): return passed) else 1)
