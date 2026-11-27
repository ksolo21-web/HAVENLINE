extends SceneTree

const Profiles = preload("res://tests/lifecycle_test_profile.gd")
const SCRIPT_PATH := "res://qa_camp_healing.gd"
var world
var checks := {}
var gates_crossed := {}

func _initialize() -> void:
	if not Profiles.isolated(self,SCRIPT_PATH): run.call_deferred()

func check(label: String, success: bool) -> void:
	checks[label] = success
	if not success: printerr("Camp recovery check failed: ",label)

func aim(direction: Vector3) -> void:
	var start := root.get_visible_rect().size * Vector2(.3,.7)
	var right: Vector3 = world.camera.global_basis.x
	var screen := Vector2(direction.dot(right),direction.dot(right.cross(Vector3.UP)))
	var touch := InputEventScreenTouch.new()
	touch.pressed = true
	touch.index = 3
	touch.position = start
	world._input(touch)
	var drag := InputEventScreenDrag.new()
	drag.index = 3
	drag.position = start + screen*90.
	world._input(drag)

func release() -> void:
	var touch := InputEventScreenTouch.new()
	touch.index = 3
	touch.pressed = false
	world._input(touch)

func gate_return(index: int, outward: Vector3) -> void:
	var gate: Node3D = world.gates[index]
	var center := gate.global_position
	center.y = 0.
	world.actor.position = center + outward*2.
	world.previous_dry_position = world.actor.position
	world.actor.velocity = Vector3.ZERO
	world.actor.rotation.y = atan2(-outward.x,-outward.z)
	world.player_invulnerability = 0.
	world._player_hit(5)
	var hurt: int = world.player_hp
	for frame in 65: await physics_frame
	check("gate_%d_snow_does_not_heal"%index,world.player_hp == hurt)
	aim(-outward)
	var entered := false
	for frame in 180:
		await physics_frame
		if (world.actor.position-center).dot(outward) < -.75:
			entered = true
			break
	release()
	var feet: Vector3 = world.actor.position
	gates_crossed[str(index)] = [feet.x,feet.z]
	check("gate_%d_normal_input_crosses"%index,entered and world.field_env.is_inside_camp(feet))
	for frame in 65: await physics_frame
	check("gate_%d_automatic_visible_recovery"%index,world.player_hp > hurt and int(world.opening_hud.health_bar.value)==world.player_hp)
	check("gate_%d_world_feedback"%index,world.events.any(func(row):return row.event=="camp_heal"))

func read_player_save() -> Dictionary:
	var saved = world.Inventory.new()
	saved.configure(world.Progress.offers())
	if world.field_save.load_into(saved) != OK: return {}
	return saved.world_state

func run() -> void:
	world=load("res://field_opening.tscn").instantiate()
	root.add_child(world)
	for frame in 5: await physics_frame
	for wolf in world.enemies.duplicate(): world.encounters._remove(wolf)
	world.encounters.remaining=600.
	world.player_invulnerability=0.
	world._player_hit(7)
	var initial: int=world.player_hp
	world.actor.position=Vector3(1.72,0,1.8)
	for frame in 75: await physics_frame
	check("unbuilt_footprint_does_not_heal",world.player_hp==initial and not world.is_camp_healing())
	for i in int(world.inventory.remaining(world.HEARTH_OFFER).wood):
		world.inventory.collect("healing-fixture-"+str(i),"wood")
		world.inventory.payment(world.HEARTH_OFFER,"wood",false)
	world._apply_hearth(true,false)
	await gate_return(0,Vector3.BACK)
	await gate_return(1,Vector3.RIGHT)
	world.set_physics_process(false)
	world.actor.position=Vector3(1.72,0,1.8)
	world.camp_heal_elapsed=0.
	world.player_hp=16
	world._advance_camp_heal(.45)
	world._persist_world()
	var disk:Dictionary=read_player_save()
	check("save_keeps_partial_hp_and_elapsed",disk.get("player",{}).get("hp")==16 and is_equal_approx(float(disk.player.get("camp_heal_elapsed",-1)),.45))
	world.camp_heal_elapsed=0.
	world.player_hp=1
	check("paid_profile_restored",world.lifecycle.restore(disk))
	world._advance_camp_heal(.54)
	check("reload_does_not_grant_early_hp",world.player_hp==16)
	world._advance_camp_heal(.01)
	check("partial_second_completes_after_reload",world.player_hp==19 and read_player_save().player.hp==19)
	world._advance_camp_heal(.8)
	world.actor.position=Vector3(9,0,0)
	world._advance_camp_heal(.4)
	world.actor.position=Vector3(1.72,0,1.8)
	world._advance_camp_heal(.2)
	check("leaving_cancels_partial_pulse",world.player_hp==19 and is_equal_approx(world.camp_heal_elapsed,.2))
	var snow_save: Dictionary = disk.player.duplicate()
	var east: float = world.layout.camp_rect_xz[2]
	snow_save.x = east+.05
	snow_save.z = 0.0
	world.lifecycle._restore_actor(snow_save)
	world._advance_camp_heal(2.)
	check("just_outside_closed_gate_restore_stays_on_snow",world.actor.position.x>east+world.layout.actor_radius and world.player_hp==16 and world.camp_heal_elapsed==0.)
	var legacy:Dictionary=disk.player.duplicate()
	legacy.erase("camp_heal_elapsed")
	legacy.hp=2
	world.lifecycle._restore_actor(legacy,1)
	check("v1_low_hp_loads_without_a_free_pulse",world.player_hp==15 and world.camp_heal_elapsed==0.)
	world._advance_camp_heal(1.)
	check("legacy_profile_can_heal",world.player_hp==18)
	world.player_hp=world.MAX_HP-1
	world._advance_camp_heal(2.5)
	check("last_actual_hp_only",world.player_hp==world.MAX_HP and world.camp_heal_elapsed==0. and world.get_children().any(func(node):return node is Label3D and node.text=="Hearth  +1 HP"))
	var event_count:int=world.events.size()
	world._advance_camp_heal(10.)
	check("full_hp_has_no_award_or_repeat",world.events.size()==event_count)
	world.actor.position=Vector3(12,0,0)
	world.player_invulnerability=0.
	world._player_hit(world.MAX_HP)
	var fall:Dictionary=read_player_save()
	world.lifecycle.restore(fall)
	world.actor.position=Vector3(1.72,0,1.8)
	world._advance_camp_heal(2.)
	check("downed_save_waits_for_respawn",world.player_hp==0 and world.reset_time>0)
	world._physics_process(1.06)
	check("existing_respawn_remains_full_hp",world.player_hp==world.MAX_HP and world.player_invulnerability>1.9 and world.camp_heal_elapsed==0.)
	world.field_env.set_perimeter(3,false)
	world.actor.position=Vector3(8.1,0,2.1)
	world.player_hp=22
	world._advance_camp_heal(1.)
	check("expanded_paid_grounds_heal",world.player_hp==25)
	world.field_save.revision="stale-writer-fixture"
	var before_failure:int=world.events.size()
	world._advance_camp_heal(1.)
	check("failed_checkpoint_grants_no_hp_or_feedback",world.persist_blocked and world.player_hp==25 and world.events.size()==before_failure and read_player_save().player.hp==25)
	print(JSON.stringify({"suite":"camp_healing","checks":checks,"gate_crossings":gates_crossed}))
	await Profiles.drain_field_audio(self,world)
	quit(1 if checks.values().has(false) else 0)
