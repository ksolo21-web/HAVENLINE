extends SceneTree
## Discrete checks use scaled simulation time and seeded encounter decisions in an isolated field scene.
var f
var rows := {}
var fail := []
func check(key:String, result:bool) -> void:
	rows[key]=result
	if not result: fail.append(key)
func _initialize() -> void:
	if not preload("res://tests/lifecycle_test_profile.gd").isolated(self,"res://qa_world_lifecycle.gd"): call_deferred("run")
func run() -> void:
	f=load("res://field_opening.tscn").instantiate()
	root.add_child(f)
	await physics_frame
	await process_frame
	f.set_physics_process(false)
	var e=f.encounters
	e.rng.seed=94721
	var all_initial_registered:=true
	for wolf in f.enemies: all_initial_registered=all_initial_registered and f.tracks.living.has(wolf)
	check("initial_wolves_have_track_registration",not f.enemies.is_empty() and all_initial_registered)
	f.field_env.set_perimeter(2,false)
	var boundary_wolf=e._add(Vector3(9.8,0,.3),false,100000,Vector3(11,0,.3))
	f.field_env.set_perimeter(3,false)
	check("perimeter_expansion_synchronously_retires_encroaching_wolf",not f.enemies.has(boundary_wolf) and not boundary_wolf.visible and not f.surfaces.has(boundary_wolf))
	f.camp_active=true
	var boss_count:=0
	var blocked:=0
	var bad:=0
	e.boss_chance=.18
	var corners: Array[Vector3]=[Vector3.ZERO,Vector3(511,0,511),Vector3(-511,0,511),Vector3(511,0,-511),Vector3(-511,0,-511)]
	var rolls_before: int=e.boss_rolls
	for i in 500:
		var player:Vector3=corners[i%corners.size()]
		var plans:Array=e._plan(e.anchor_for(player),player,[],4)
		if plans.is_empty():
			blocked+=1
			continue
		if e.last_roll: boss_count+=1
		for a in plans.size():
			if not e.outside(plans[a],2.0) or plans[a].distance_to(player)<5.2: bad+=1
			for b in a:
				if plans[a].distance_to(plans[b])<3.89: bad+=1
	check("500_waves_camp_and_four_borders_have_room_and_clearance",bad==0 and blocked==0)
	check("each_formed_wave_rolls_its_own_boss",e.boss_rolls-rolls_before==500 and boss_count>45 and boss_count<140)
	check("full_cap_retries_without_boss_roll",e._plan(Vector3.ZERO,Vector3.ZERO,[],0).is_empty() and e.boss_rolls-rolls_before==500)
	for wolf in f.enemies.duplicate(): e._remove(wolf)
	e.boss_chance=0.0
	check("forced_regular_wave",e.launch(false) and not f.enemies.any(func(w): return w.is_boss))
	for wolf in f.enemies.duplicate(): e._remove(wolf)
	e.boss_chance=1.0
	check("forced_boss_wave",e.launch() and f.enemies.filter(func(w): return w.is_boss).size()==1 and f.enemies.size()<=4)
	var boss = f.enemies[0]
	check("boss_model_health_hit_surface_and_real_paws",boss.hp==8 and boss.size_factor()>1.5 and boss.contact_mesh()!=null and f.tracks.living[boss].feet.size()==4)
	for wolf in f.enemies.duplicate():
		if wolf!=boss: e._remove(wolf)
	# Actual skeleton animation, ordinary stalk motion, then native snow renderer.
	boss.position=Vector3(18,0,6)
	boss.home=boss.position
	f.actor.position=boss.position+Vector3(3,0,0)
	var old_marks:int=f.tracks.total
	for i in 150:
		boss.advance(1.0/60,e.can_walk.bind(boss),true)
		if boss.animator: boss.animator.advance(1.0/60)
		f.tracks._physics_process(1.0/60)
	check("boss_left_real_paw_imprints",f.tracks.total>old_marks)
	var safe_from:=Vector3(13.5,0,0)
	var safe_to:=Vector3(8.0,0,0)
	check("boss_cannot_cross_third_perimeter",not e.sweep(safe_from,safe_to,boss.sanctuary_margin()))
	boss.position=Vector3(14,0,-2)
	boss.home=boss.position
	f.actor.position=Vector3(8.5,0,-2)
	boss.state="lunge"
	boss.timer=0
	var hp_before:int=f.player_hp
	e.advance(.03)
	check("sanctuary_cancels_windup_and_bite",f.player_hp==hp_before and boss.state!="lunge")
	var tower=f.defense_tower
	var same:int=boss.hp
	for i in 360: tower.advance(1.0/60,false)
	check("unpaid_tower_never_deals_damage",boss.hp==same and tower.flights.is_empty())
	tower.advance(.03,true)
	var previous_bolt:=Vector3.INF
	var traveled:=false
	for i in 160:
		tower.advance(1.0/60,true)
		if not tower.flights.is_empty() and boss.hp==same:
			var bolt:Node3D=tower.flights[0].mesh
			if previous_bolt.is_finite():
				traveled=bolt.global_position.distance_to(previous_bolt)>.05 and bolt.find_children("*","MeshInstance3D",true,false).size()>0
				break
			previous_bolt=bolt.global_position
	check("paid_tower_launches_authored_bolt_before_damage",traveled and boss.hp==same)
	for i in 1200:
		tower.advance(1.0/60,true)
		if boss.hp==0:break
	check("tower_defeats_actual_alpha_and_credits_typed_meat_once",boss.hp==0 and f.drops.size()==5 and not boss.receive_hit(1))
	check("tower_events_mark_launch_and_hit",f.events.any(func(r):return r.event=="tower_fire") and f.events.any(func(r):return r.event=="tower_hit"))
	for i in 30:e.advance(.02)
	check("corpse_retained_for_fall",boss in f.enemies)
	for i in 20:e.advance(.02)
	check("dead_actor_removed_from_orbit_and_pack",not boss in f.enemies and not f.surfaces.has(boss))
	var p:=Vector2(31,20)
	var rock=f.add_resource_source("qa-rock","stone",p)
	f.actor.position=rock.position+Vector3.RIGHT*1.4
	f.character_kit.equipped="pickaxe"
	for i in 2:
		rock.cooldown=0
		check("stone_hit_"+str(i),f.accept_contact(rock))
	f.unload_resource_source("qa-rock")
	rock=f.add_resource_source("qa-rock","stone",p)
	check("partial_source_survives_stream",rock.strikes==2 and rock.phase=="seated")
	var drops_before:int=f.drops.size()
	check("third_hit_visual_depletion",f.accept_contact(rock) and rock.phase=="mined" and not f.is_source_available("qa-rock"))
	check("one_source_three_fresh_drops",f.drops.size()==drops_before+3)
	f.unload_resource_source("qa-rock")
	f.lifecycle.advance(31.9)
	var cooldown_save:Dictionary=f.lifecycle.snapshot()
	check("timer_while_unloaded",not f.is_source_available("qa-rock"))
	rock=f.add_resource_source("qa-rock","stone",p)
	check("unloaded_source_stays_hidden_until_due",not rock._mesh.visible)
	f.lifecycle.advance(.11)
	check("exact_stone_timer_returns_actual_mesh",rock.phase=="seated" and rock._mesh.visible and rock.strikes==0)
	var png=JSON.parse_string(JSON.stringify(cooldown_save))
	check("json_lifecycle_resume",f.lifecycle.restore(png) and not f.is_source_available("qa-rock") and f.drops.size()==drops_before+3)
	f.lifecycle.advance(.11)
	for i in 3:
		rock.cooldown=0
		f.accept_contact(rock)
	check("regrown_round_new_loot",f.drops.size()==drops_before+6)
	var pine=f.add_resource_source("qa-pine","wood",Vector2(34,20))
	f.actor.position=pine.position+Vector3.RIGHT*1.4
	f.character_kit.equipped="axe"
	for i in 3:
		pine.cooldown=0
		f.accept_contact(pine)
	f.unload_resource_source("qa-pine")
	var count:int=f.drops.size()
	pine=f.add_resource_source("qa-pine","wood",Vector2(34,20))
	check("travel_while_pine_falling_resolves_once",not f.is_source_available("qa-pine") and pine.phase=="credited")
	f.unload_resource_source("qa-pine")
	f.lifecycle.advance(4.9)
	check("wood_timer_distinct",not f.is_source_available("qa-pine"))
	f.lifecycle.advance(.11)
	pine=f.add_resource_source("qa-pine","wood",Vector2(34,20))
	check("pine_regrown_no_duplicate_loot",f.is_source_available("qa-pine") and pine.phase=="rooted" and pine._pivot.visible and f.drops.size()==count)
	var snap:Dictionary=f.lifecycle.snapshot()
	var corrupt=snap.duplicate(true)
	corrupt.cooling={"bad":-5}
	check("invalid_state_rejected_atomically",not f.lifecycle.restore(corrupt) and f.lifecycle.snapshot()==snap)
	f._step_drops(101)
	check("old_ground_loot_retired",f.drops.is_empty())
	var legacy:Dictionary=f.lifecycle.snapshot()
	legacy.erase("player")
	var prior:Vector3=f.actor.position
	check("older_snapshot_no_position_keeps_start_state",f.lifecycle.restore(legacy) and f.actor.position==prior)
	f.lifecycle._restore_actor({"x":1.0e9,"z":0,"hp":99,"yaw":0.0})
	check("invalid_saved_position_and_health_recover",f.actor.position==f.lifecycle.safe_start() and f.player_hp==f.MAX_HP)
	f.lifecycle._restore_actor({"x":10.0,"z":0.0,"hp":2,"yaw":0.0})
	check("restored_actor_avoids_paid_closed_gate",f.actor.position==f.lifecycle.safe_start() and f.player_hp==2)
	f.lifecycle._restore_actor({"x":-35.0,"z":5.0,"hp":0,"yaw":0.0})
	check("dead_player_resumes_existing_recovery",f.reset_time>0.0 and f.player_hp==0)
	for _i in 75: f._physics_process(1.0/60)
	check("restored_fall_returns_home_alive",f.player_hp==f.MAX_HP and f.actor.position.distance_to(f.lifecycle.safe_start())<.1)
	check("dedicated_boss_and_tower_cues_loaded",["boss_arrival","boss_defeat","tower_fire","tower_hit"].all(func(id):return f.sound._bank.has(id) and f.sound._bank[id].size()==1))
	check("all_four_semantic_cues_started_on_actions",["boss_arrival","boss_defeat","tower_fire","tower_hit"].all(func(id):return f.sound._counts.get(id,0)>0))
	print(JSON.stringify({"checks":rows,"failed":fail,"waves":500,"bosses":boss_count,"paw_marks_before":old_marks,"paw_marks_after":f.tracks.total,"audible_boss_tower_cue_starts":{"boss_arrival":f.sound._counts.get("boss_arrival",0),"boss_defeat":f.sound._counts.get("boss_defeat",0),"tower_fire":f.sound._counts.get("tower_fire",0),"tower_hit":f.sound._counts.get("tower_hit",0)}}))
	quit(0 if fail.is_empty() else 1)
