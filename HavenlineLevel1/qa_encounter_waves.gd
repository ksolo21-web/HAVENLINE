extends SceneTree
## Retires and replenishes 200 entire native enemy packs across an expanded camp and the four map corners.
func _initialize() -> void:
	if not preload("res://tests/lifecycle_test_profile.gd").isolated(self,"res://qa_encounter_waves.gd"): call_deferred("run")
func run() -> void:
	var field=load("res://field_opening.tscn").instantiate()
	root.add_child(field)
	await physics_frame
	field.set_physics_process(false)
	field.world_landscape.set_physics_process(false)
	field.field_env.set_perimeter(3,false)
	field.camp_active=true
	var e=field.encounters
	e.rng.seed=600286
	e.boss_chance=.18
	for wolf in field.enemies.duplicate(): e._remove(wolf)
	await process_frame
	# The southern stag is a persistent, tracked prey actor. Only the wolves
	# belong to the wave and should disappear at the end of each encounter.
	var permanent := {field.actor:"human",field.survivor.actor:"human",field.survivor.wildlife:"stag"}
	var persistent_surfaces: Array = field.surfaces.keys()
	var correct_actors := _preserves_trackers(field,permanent)
	var cleanup_failures := 0
	var corners: Array[Vector3]=[Vector3.ZERO,Vector3(510,0,510),Vector3(-510,0,510),Vector3(510,0,-510),Vector3(-510,0,-510)]
	var total:=0
	var alphas:=0
	var deaths:=0
	var peak:=0
	var ok:=correct_actors
	var duplicate_loot:=0
	var starting_wave: int=e.wave
	var previous_id:=0
	for wave in 200:
		field.actor.position=corners[wave%corners.size()]
		e.remaining=.11
		e.advance(.10)
		if not field.enemies.is_empty(): ok=false
		e.advance(.02)
		peak=maxi(peak,field.enemies.size())
		if field.enemies.is_empty() or field.enemies.size()>4: ok=false
		for wolf in field.enemies.duplicate():
			total+=1
			if wolf.is_boss: alphas+=1
			if wolf.spawn_id<=previous_id or not e.outside(wolf.position,wolf.sanctuary_margin()) or not field.tracks.living.has(wolf) or not field.surfaces.has(wolf):ok=false
			previous_id=wolf.spawn_id
			var before: int=field.drops.size()
			if wolf.receive_hit(wolf.hp): deaths+=1
			if not field.drops.size()==before+(5 if wolf.is_boss else 2): ok=false
			if wolf.receive_hit(1): duplicate_loot+=1
		for tick in 10: e.advance(.08)
		if not field.enemies.is_empty():ok=false
		field._step_drops(101)
		await process_frame
		await process_frame
		correct_actors = _preserves_trackers(field,permanent) and correct_actors
		if field.enemy != null or not field.get_tree().get_nodes_in_group("swirl_hostiles").is_empty() or not field.drops.is_empty():
			cleanup_failures += 1
		elif field.surfaces.size()!=persistent_surfaces.size() or not persistent_surfaces.all(func(body):return field.surfaces.has(body)):
			cleanup_failures += 1
	var summary={"passed":ok and correct_actors and cleanup_failures==0 and total==deaths and duplicate_loot==0 and peak<=4 and alphas>0 and alphas<200 and e.wave==starting_wave+200,"native_waves":e.wave-starting_wave,"actual_wolves":total,"actual_deaths":deaths,"actual_alphas":alphas,"peak_live":peak,"duplicate_loot":duplicate_loot,"orphan_wolves":field.get_tree().get_nodes_in_group("swirl_hostiles").size(),"remaining_trackers":field.tracks.living.size(),"preserved_player_and_survivor":correct_actors,"preserved_prey_tracker":correct_actors,"failed_cleanup_cycles":cleanup_failures}
	print("ENCOUNTER_STRESS ",JSON.stringify(summary))
	await preload("res://tests/lifecycle_test_profile.gd").drain_field_audio(self, field)
	quit(0 if summary.passed else 1)

func _preserves_trackers(field: Node3D, expected: Dictionary) -> bool:
	var living: Dictionary = field.tracks.living
	return living.size()==expected.size() and expected.keys().all(func(actor):
		return is_instance_valid(actor) and actor.is_inside_tree() and living.has(actor) and living[actor].species==expected[actor])
