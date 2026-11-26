extends SceneTree
## Loads only the resources bundled in --main-pack. The external harness supplies
## screen touches; the field spawns enemies, drives their AI, and applies damage.
var w
var outcomes := {}
var evidence := {}
var stick := Vector2(76,590)
var failures := []

func _initialize(): start.call_deferred()
func check(key: String, result: bool) -> void:
	outcomes[key] = result
	if not result: failures.append(key)
func touch(pressed: bool) -> void:
	var e := InputEventScreenTouch.new()
	e.index=0
	e.position=stick
	e.pressed=pressed
	w._input(e)
func move(stick_offset: Vector2) -> void:
	var e := InputEventScreenDrag.new()
	e.index=0
	e.position=stick + stick_offset
	w._input(e)
func wait_ticks(n: int) -> void:
	for tick in n: await physics_frame

func start() -> void:
	var scene_path: String = ProjectSettings.get_setting("application/run/main_scene")
	check("signed_pack_entry_scene",scene_path == "res://field_opening.tscn")
	check("compiled_android_scripts",FileAccess.file_exists("res://field_opening.gdc") and not FileAccess.file_exists("res://field_opening.gd"))
	var scene = load(scene_path)
	if not scene:
		check("field_loaded",false);finish();return
	w = scene.instantiate()
	root.add_child(w)
	await wait_ticks(3)
	check("loaded_in_disposable_profile",w.field_ready and not w.persist_blocked)
	evidence.start_hp = w.player_hp
	check("thirty_hp_on_fresh_spawn",w.player_hp == 30 and w.MAX_HP == 30)
	check("hud_shows_current_hp","30" in w.opening_hud.health_text.text)
	check("first_camp_plot_costs_200_wood",int(w.inventory.costs.center_hearth.wood)*int(w.Progress.UNITS_PER_BUNDLE)==200)
	var wear: Array = w.hero_model.find_children("*","GeometryInstance3D",true,false)
	wear.append_array(w.carry.rack.find_children("*","GeometryInstance3D",true,false))
	check("worn_meshes_have_shadow_casting_off",not wear.is_empty() and wear.all(func(mesh): return mesh.cast_shadow==GeometryInstance3D.SHADOW_CASTING_SETTING_OFF))
	check("owl_shipped_with_talon_shapes_and_six_contact_points",w.owl.plumage.get_blend_shape_count()>=3 and w.owl.claw_binds.size()==6)
	check("new_effects_and_three_scores_loaded",w.sound._ready_to_play and w.sound.CUES.size()>=56 and w.sound.LOOP_NAMES.size()==5)
	check("wearable_supports_in_signed_scene",w.carry.braces.size()==4 and w.carry.braces.all(func(part): return part.mesh != null and part.cast_shadow == GeometryInstance3D.SHADOW_CASTING_SETTING_OFF))
	var start_pos: Vector3 = w.actor.position
	touch(true)
	move(Vector2(21.,0.))
	await wait_ticks(60)
	var distance := start_pos.distance_to(w.actor.position)
	evidence.short_drag_distance_m = distance
	evidence.short_drag_gait = w.character_kit.locomotion.current
	check("short_touch_drag_runs",distance > 1.5 and w.character_kit.locomotion.current == "run")
	touch(false)
	await wait_ticks(36)
	check("release_returns_to_idle",w.character_kit.locomotion.current == "idle")

	# Walk toward the live pack using the same virtual stick. Stay still after
	# entering biting range, allowing auto-attack and enemy attacks to run.
	var move_target = null
	var nearest := INF
	for wolf in w.enemies:
		var d: float = w.actor.position.distance_squared_to(wolf.position)
		if wolf.hp > 0 and d < nearest:
			nearest=d; move_target=wolf
	check("genuine_enemy_encounter",move_target != null)
	if move_target:
		var skeletons: Array = move_target.visual.find_children("*","Skeleton3D",true,false)
		check("attacker_has_weighted_jaw_rig",not skeletons.is_empty() and skeletons[0].find_bone("Jaw")>=0 and move_target.surface.skin.get_bind_count()>0)
	var released := false
	var first_contact := -1
	var lowest_hp: int = w.player_hp
	var attack_events := {}
	var event_cursor: int = w.events.size()
	touch(true)
	for tick in 1260:
		if is_instance_valid(move_target) and not released:
			var dir: Vector3 = move_target.position - w.actor.position
			if dir.length() <= 1.32:
				touch(false); released=true
			else:
				var camera_dir := dir.normalized().rotated(Vector3.UP,-atan2(7.,11.))
				move(Vector2(camera_dir.x,camera_dir.z)*76.)
		await physics_frame
		lowest_hp = mini(lowest_hp,int(w.player_hp))
		for j in range(event_cursor,w.events.size()):
			var name_: String = w.events[j].event
			if name_ in ["player_attack","wolf_brace","enemy_attack","player_hurt"]:
				attack_events[name_]=int(attack_events.get(name_,0))+1
				if first_contact == -1: first_contact=tick
		event_cursor=w.events.size()
		if attack_events.has_all(["player_attack","enemy_attack","player_hurt"]) and lowest_hp < 30:
			break
	if not released: touch(false)
	evidence.combat_events=attack_events
	evidence.first_contact_tick=first_contact
	evidence.lowest_hp=lowest_hp
	check("orbit_strikes_without_attack_input",attack_events.has("player_attack"))
	check("wolf_starts_real_attack",attack_events.has("enemy_attack"))
	check("damage_applies_to_player_and_hud",lowest_hp < 30 and attack_events.has("player_hurt") and str(w.player_hp) in w.opening_hud.health_text.text)
	w.sound.stop_playback()
	for i in 12:
		OS.delay_msec(20)
		await process_frame
	w.queue_free()
	for i in 8:
		OS.delay_msec(18)
		await process_frame
	finish()

func finish() -> void:
	print("APK_PAYLOAD_SMOKE ",JSON.stringify({"passed":failures.is_empty(),"checks":outcomes,"evidence":evidence,"failures":failures}))
	quit(int(not failures.is_empty()))
