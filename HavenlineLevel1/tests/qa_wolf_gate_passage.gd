extends "res://tests/qa_gate_corner_controls.gd"

const TEST := "res://tests/qa_wolf_gate_passage.gd"
var checks := {}
var witnessed_bites := 0
var previously_healthy := 0
var bite_cost := 0

func _initialize() -> void:
	if not Profile.isolated(self, TEST):
		run.call_deferred()

func run() -> void:
	field = load("res://field_opening.tscn").instantiate()
	root.add_child(field)
	camera = field.camera
	origin = root.get_visible_rect().size * Vector2(.3, .72)
	for tick in 4:
		await physics_frame
	pay("center_hearth")
	field._apply_hearth(true, false)
	for id in ["expansion_1", "storage_wood", "storage_stone", "storage_meat", "expansion_2"]:
		pay(id)
	for tick in 6:
		await physics_frame
	var gate = field.gates[0 if OS.get_environment("HAVENLINE_THREAT_GATE") == "south" else 1]
	var hunter_at: Vector3 = gate.to_global(Vector3(0,0,2.1))
	# Restore a valid encounter with an alpha parked at the outer lip.
	# The other live pack members start far enough outside to identify the
	# damage from this particular wolf. All hunters keep normal AI and physics.
	var encounter: Dictionary = field.encounters.snapshot()
	var other_count: int = maxi(0, encounter.live.size() - 1)
	for i in other_count:
		var row: Array = encounter.live[i]
		var territory: Vector3 = gate.to_global(Vector3(-9. + i * 4.,0,23.))
		encounter.live[i] = [row[0],row[1],row[2],territory.x,territory.z,territory.x,territory.z]
	if encounter.live.is_empty():
		encounter.serial += 1
		encounter.live.append([encounter.serial])
	var id: int = encounter.live.back()[0]
	encounter.live[-1] = [id,true,preload("res://field_enemy.gd").BOSS_HEALTH,hunter_at.x,hunter_at.z,hunter_at.x,hunter_at.z]
	checks["normal encounter restore accepts the live pack"] = field.encounters.restore(encounter)
	var hunter = field.enemies.back()
	hunter.player_hit.connect(func(_amount):
		witnessed_bites += 1
		bite_cost += maxi(0, previously_healthy - int(field.player_hp)))
	checks["hunter starts legally outside sanctuary"] = field.encounters.outside(hunter_at,hunter.sanctuary_margin())
	var start: Vector3 = gate.to_global(Vector3(0,0,-2.6))
	field.actor.global_position = start
	field.previous_dry_position = start
	field.actor.velocity = Vector3.ZERO
	field.actor.rotation.y = atan2(gate.global_basis.z.x,gate.global_basis.z.z)
	field.gait_motor.travel_speed = 0
	field.camera.position = start + field.camera_follow_offset
	field.player_hp = field.MAX_HP
	var outward: Vector3 = gate.global_basis.z
	var right: Vector3 = camera.global_basis.x
	var stick := Vector2(outward.dot(right),outward.dot(right.cross(Vector3.UP))).normalized()
	var nearest := INF
	var peak_step := 0.
	var still_ticks := 0
	var max_still := 0
	var solid_crossings := 0
	var hunter_crossed_fence := false
	var yielded := false
	var healthy_in_camp := true
	var ticks_to_far := 0
	var exception_at_exit := true
	var hp_at_first_bite: int = field.MAX_HP
	var bite_position := Vector3.INF
	var exited_well := false
	for tick in 270:
		var previous: Vector3 = field.actor.global_position
		previously_healthy = field.player_hp
		if exited_well and is_instance_valid(hunter):
			# Re-enter this hunter's bite reach in the field, even when another
			# member of the pack has reached the runner first.
			var toward: Vector3 = hunter.global_position - previous
			if toward.length() > 1.80:
				steer(Vector2(toward.dot(right),toward.dot(right.cross(Vector3.UP))).normalized())
			else:
				steer(Vector2.ZERO)
		else:
			steer(stick)
		await physics_frame
		var position: Vector3 = field.actor.global_position
		var depth: float = gate.to_local(position).z
		var distance: float = position.distance_to(previous)
		peak_step = maxf(peak_step,distance)
		if not exited_well:
			still_ticks = still_ticks+1 if distance < .0063 else 0
			max_still = maxi(max_still,still_ticks)
		if not field.field_env.travel_clear(previous,position,0.):
			solid_crossings += 1
		if field.field_env.is_inside_camp(position) and field.player_hp < field.MAX_HP:
			healthy_in_camp = false
		if is_instance_valid(hunter):
			nearest = minf(nearest,position.distance_to(hunter.global_position))
			hunter_crossed_fence = hunter_crossed_fence or field.field_env.is_inside_camp(hunter.global_position)
			yielded = yielded or field.actor.get_collision_exceptions().has(hunter.body)
			if witnessed_bites and field.player_hp < field.MAX_HP and not bite_position.is_finite():
				bite_position = position
				hp_at_first_bite = field.player_hp
		if not exited_well and depth>=5.2:
			exited_well = true
			ticks_to_far = tick+1
			exception_at_exit = is_instance_valid(hunter) and field.actor.get_collision_exceptions().has(hunter.body)
		if exited_well and witnessed_bites and field.player_hp < field.MAX_HP:
			break
	steer(Vector2.ZERO)
	checks["runner passes the parked live torso into the field"] = yielded and exited_well and ticks_to_far < 95
	checks["open gateway stays traversable at run speed"] = max_still < 12 and peak_step < .24 and nearest < 2.35
	checks["runner and wolf respect solid fence and safe camp"] = healthy_in_camp and not hunter_crossed_fence and solid_crossings == 0
	checks["open-field torso regains normal collision"] = exited_well and not exception_at_exit
	checks["same live hunter can pursue and damage the runner"] = witnessed_bites > 0 and bite_cost >= preload("res://field_enemy.gd").BOSS_BITE_DAMAGE and hp_at_first_bite < field.MAX_HP and not field.field_env.is_inside_camp(bite_position)
	print("LIVE_GATE_HUNTER ",JSON.stringify({"gate":gate.gate_id,"checks":checks,"metrics":{"ticks_to_5_2m":ticks_to_far,"maximum_still_ticks":max_still,"maximum_step_m":peak_step,"nearest_m":nearest,"solid_crossings":solid_crossings,"wolf_bites":witnessed_bites,"hp_lost_to_this_wolf":bite_cost,"hp_after_first_bite":hp_at_first_bite,"max_hp":field.MAX_HP,"wolves":field.enemies.size()}}))
	field.set_physics_process(false)
	field.carry.set_physics_process(false)
	await Profile.drain_field_audio(self,field)
	field.free()
	quit(int(checks.values().has(false)))
