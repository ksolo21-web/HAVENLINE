extends SceneTree
## Deterministic contact fixtures exercise the normal pack, HUD, hit and recovery handlers.
const Session = preload("res://tests/lifecycle_test_profile.gd")
var results := {}
var observations := {}
var scene
func _initialize() -> void:
	if not Session.isolated(self,"res://qa_world_combat.gd"): call_deferred("run")
func check(key: String, ok: bool) -> void:
	results[key]=ok
	if not ok: printerr("Combat check failed ",key)
func run() -> void:
	scene=load("res://field_opening.tscn").instantiate()
	root.add_child(scene)
	await physics_frame
	scene.set_physics_process(false)
	scene.world_landscape.set_physics_process(false)
	for wolf in scene.enemies.duplicate(): scene.encounters._remove(wolf)
	await physics_frame
	var hud=scene.opening_hud
	check("continuous_full_hp_even_without_threat",hud.health_bar.is_visible_in_tree() and hud.health_text.text.contains("30 / 30") and hud.health_bar.max_value==10*scene.FieldEnemy.MAX_HEALTH)
	for paid: bool in [false,true]:
		var phase := "paid" if paid else "unpaid"
		if paid:
			for kind in scene.inventory.costs[scene.HEARTH_OFFER]:
				for unit in scene.inventory.costs[scene.HEARTH_OFFER][kind]:
					scene.inventory.collect("combat-hearth-%d" % unit,kind)
					scene.inventory.payment(scene.HEARTH_OFFER,kind,false)
			scene._apply_hearth(true,false)
		scene.actor.position=Vector3(16,0,4)
		scene.player_invulnerability=0
		var home: Vector3=scene.actor.position+Vector3(10.5,0,1.3)
		scene.encounters.remaining = 90.0
		scene.encounters.serial += 1
		var wolf=scene.encounters._add(home,paid,scene.encounters.serial,home)
		var phases := {}
		var closing_ticks := 0
		for tick in 430:
			closing_ticks += 1
			scene.encounters.advance(1.0/60)
			phases[wolf.state]=true
			if scene.player_hp<scene.MAX_HP: break
		check(phase+"_pursuit_windup_lunge_and_hp_loss",phases.has("stalk") and phases.has("windup") and phases.has("lunge") and scene.player_hp==scene.MAX_HP-(wolf.BOSS_BITE_DAMAGE if paid else wolf.BITE_DAMAGE))
		observations[phase]={"start_range_m":home.distance_to(scene.actor.position),"first_hit_seconds":closing_ticks/60.0,"health_after_first_bite":scene.player_hp,"state_at_contact":wolf.state}
		check(phase+"_bite_contact_within_five_seconds_from_ten_metres",closing_ticks<300 and wolf.state=="lunge")
		check(phase+"_instant_health_and_trailing_bar",hud.health_bar.value==scene.player_hp and hud.health_trail.value>scene.player_hp)
		var hp_before:int=scene.player_hp
		scene._player_hit(2,wolf)
		check(phase+"_invulnerability_blocks_repeat",scene.player_hp==hp_before)
		check(phase+"_committed_lunge_retains_authored_bite",wolf.take_swirl_hit(100) and wolf.state=="lunge" and wolf.animator.current_animation=="Bite" and wolf.hurt_timer>0)
		scene._physics_process(3.0/60)
		check(phase+"_directional_hero_recoil_and_hit_flash",Vector2(scene.hero_model.rotation.x,scene.hero_model.rotation.z).length()>.12 and scene.flash.color.a>.12)
		while wolf.state=="lunge": scene.encounters.advance(1.0/60)
		check(phase+"_uncommitted_wolf_has_animated_damage",wolf.take_swirl_hit(101) and wolf.state=="stagger" and wolf.animator.current_animation=="Hurt")
		for tick in 2400:
			scene.player_invulnerability=maxf(0.0,scene.player_invulnerability-1.0/60)
			scene.encounters.advance(1.0/60)
			if scene.reset_time>0: break
		check(phase+"_zero_hp_disarms_and_changes_hud",scene.player_hp==0 and not scene.character_kit.active and hud.health_bar.value==0)
		for tick in 33: scene._physics_process(1.0/60)
		check(phase+"_visible_fall_before_reset",absf(scene.hero_model.rotation.z)>1.2 and scene.player_hp==0)
		for tick in 35:
			if scene.reset_time>0: scene._physics_process(1.0/60)
		var at: Vector3=scene.actor.position
		var target: Vector3=Vector3(1.72,0,1.8) if paid else scene.point(scene.layout.pad_xz)
		check(phase+"_returns_to_correct_floor",at.distance_to(target)<.01 and bool(scene.field_env.is_inside_camp(at))==paid)
		check(phase+"_restores_hud_and_grace",scene.player_hp==scene.MAX_HP and hud.health_bar.value==scene.MAX_HP and scene.player_invulnerability>1.9)
		var recovered: Dictionary = scene.lifecycle.snapshot()
		scene.player_invulnerability = 0.0
		scene.lifecycle._restore_actor(recovered.player)
		check(phase+"_remaining_protection_survives_restore",is_equal_approx(scene.player_invulnerability,2.0))
		scene.player_invulnerability = .27
		var partial: Dictionary = scene.lifecycle.snapshot().player
		scene.lifecycle._restore_actor(partial)
		check(phase+"_reload_does_not_refill_partial_protection",is_equal_approx(scene.player_invulnerability,.27))
		partial.erase("protection_left")
		partial.erase("fall_left")
		scene.lifecycle._restore_actor(partial)
		check(phase+"_old_player_records_restore_without_grace",scene.player_invulnerability==0 and scene.player_hp==scene.MAX_HP)
		var overlap=scene.actor.test_move(scene.actor.global_transform,Vector3.ZERO,null,.001,true)
		check(phase+"_recovery_clear_of_obstacles",not overlap)
		if paid:
			scene.player_invulnerability=0
			scene._player_hit(2,wolf)
			check("camp_safe_even_after_grace",scene.player_hp==scene.MAX_HP)
		scene.encounters._remove(wolf)
		await physics_frame
	# Normal field physics drives both the orbit and a deterministic ordinary
	# wave. Never call a damage method or move a wolf after its spawn.
	scene.actor.position=Vector3(42,0,18)
	scene.actor.velocity=Vector3.ZERO
	scene.encounters.rng.seed=80721
	scene.encounters.boss_chance=0.0
	scene.player_invulnerability=0.0
	scene.encounters.launch()
	var spawned: int=scene.enemies.size()
	var closest:=INF
	for wolf in scene.enemies:
		closest=minf(closest,wolf.position.distance_to(scene.actor.position))
	var active_orbit:=false
	var time_to_bite:=0.0
	for tick in 720:
		scene._physics_process(1.0/60)
		active_orbit=active_orbit or scene.character_kit.active
		if scene.player_hp<scene.MAX_HP:
			time_to_bite=(tick+1)/60.
			break
	check("ordinary_spawn_bites_while_player_orbit_is_enabled",spawned>=2 and closest>=scene.encounters.MIN_PLAYER_GAP and active_orbit and time_to_bite>0 and not scene.persist_blocked)
	observations["normal_wave"]={"wolves":spawned,"closest_spawn_m":closest,"seconds_to_player_bite":time_to_bite,"orbit_enabled":active_orbit,"remaining_hp":scene.player_hp}
	check("damaging_and_receiving_sound_bank",scene.sound.CUES.has("player_hurt") and scene.sound.CUES.has("enemy_attack") and scene.sound.CUES.has("hit") and scene.sound.CUES.has("reset") and scene.sound.CUES.has("player_fall"))
	var ok:=not results.values().has(false)
	print("WORLD_COMBAT ",JSON.stringify({"passed":ok,"checks":results,"observed":observations}))
	scene.sound.stop_playback()
	# The mixer releases stopped voices on its real-time audio thread even during a fixed-FPS test.
	var release_deadline := Time.get_ticks_msec()+300
	while Time.get_ticks_msec()<release_deadline:
		OS.delay_msec(5)
		await process_frame
	scene.queue_free()
	for i in 3: await process_frame
	quit(0 if ok else 1)
