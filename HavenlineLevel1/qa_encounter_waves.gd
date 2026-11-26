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
	var permanent: Array = field.tracks.living.keys()
	var expected: Array = [field.actor,field.survivor.actor]
	var correct_actors: bool = permanent.size() == expected.size() and expected.all(func(a):return permanent.has(a))
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
		if field.get_tree().get_nodes_in_group("swirl_hostiles").size()>0 or field.tracks.living.size()!=permanent.size() or not permanent.all(func(a):return field.tracks.living.has(a)):ok=false
	var summary={"passed":ok and total==deaths and duplicate_loot==0 and peak<=4 and alphas>0 and alphas<200 and e.wave==starting_wave+200,"native_waves":e.wave-starting_wave,"actual_wolves":total,"actual_deaths":deaths,"actual_alphas":alphas,"peak_live":peak,"duplicate_loot":duplicate_loot,"orphan_wolves":field.get_tree().get_nodes_in_group("swirl_hostiles").size(),"remaining_trackers":field.tracks.living.size(),"preserved_player_and_survivor":correct_actors}
	print("ENCOUNTER_STRESS ",JSON.stringify(summary))
	await preload("res://tests/lifecycle_test_profile.gd").drain_field_audio(self, field)
	quit(0 if summary.passed else 1)
