extends SceneTree

const Profiles = preload("res://tests/lifecycle_test_profile.gd")
const SCRIPT_PATH := "res://tests/qa_field_hearth.gd"
var world
var checks := {}

func _initialize() -> void:
	if not Profiles.isolated(self,SCRIPT_PATH):
		run.call_deferred()

func check(criterion: String, success: bool) -> void:
	checks[criterion] = success
	if not success:
		push_error(criterion)

func run() -> void:
	world = load("res://field_opening.tscn").instantiate()
	root.add_child(world)
	for tick in 3: await physics_frame
	var fire = world.field_env.hearth_fire
	check("Unpaid furnace produces no fire, light or recovery",not world.camp_active and not fire.fired and not fire.is_visible_in_tree() and not fire.chamber_light.is_visible_in_tree() and not world.is_camp_healing())
	for i in int(world.inventory.remaining(world.HEARTH_OFFER).wood):
		world.inventory.collect("hearth-probe-"+str(i),"wood")
		world.inventory.payment(world.HEARTH_OFFER,"wood",false)
	world._apply_hearth(true,true)
	for tick in 60: await physics_frame
	check("Paid furnace keeps its fire after the brief purchase effect",fire.fired and fire.is_visible_in_tree() and fire.chamber_light.is_visible_in_tree() and world.field_env.hearth_stones[0].material_overlay==null)
	for part: String in ["CoalsUnderFlue","ArchedFirebox","FlueFlame","ChimneyDraft"]:
		var surface: MeshInstance3D = fire.get_node(part)
		check("Live "+part+" fitted to the paid furnace",surface.is_visible_in_tree() and surface.material_override is ShaderMaterial and world.field_env.hearth_shell.is_ancestor_of(surface))
	var lo := INF
	var hi := -INF
	for tick in 75:
		await physics_frame
		lo=minf(lo,fire.chamber_light.light_energy)
		hi=maxf(hi,fire.chamber_light.light_energy)
	check("Fire breathes steadily at full health",hi-lo>.10 and lo>.65 and world.player_hp==world.MAX_HP)
	var stock:Dictionary=world.inventory.carried.duplicate()
	var wallet: int=world.inventory.settlement.served
	# Take a native combat hit on outside snow, then re-enter through the south gate.
	world.player_invulnerability=0.
	var gate: Node3D=world.gates[0]
	world.actor.position=gate.global_position+Vector3.BACK*1.25
	world.actor.position.y=0.
	world.previous_dry_position=world.actor.position
	world.encounters.remaining=600.
	for wolf in world.enemies.duplicate(): world.encounters._remove(wolf)
	world._player_hit(7)
	var hurt: int=world.player_hp
	for tick in 65: await physics_frame
	check("Outdoor hits persist while the furnace burns inside",hurt==world.MAX_HP-7 and world.player_hp==hurt)
	var start := root.get_visible_rect().size * Vector2(.25,.7)
	var right: Vector3 = world.camera.global_basis.x
	var heading := Vector2(Vector3.FORWARD.dot(right),Vector3.FORWARD.dot(right.cross(Vector3.UP)))
	var touch := InputEventScreenTouch.new()
	touch.index=1; touch.position=start; touch.pressed=true
	world._input(touch)
	var drag := InputEventScreenDrag.new()
	drag.index=1; drag.position=start+heading*110.
	world._input(drag)
	for tick in 90:
		await physics_frame
		if world.actor.position.z < gate.global_position.z-.7:break
	touch.pressed=false
	world._input(touch)
	check("Crossing the gate starts camp-wide hearth recovery",world.is_camp_healing())
	var peak := 0.
	for tick in 70:
		await physics_frame
		peak=maxf(peak,fire.recovery_pulse)
	check("A successful saved heal brightens the furnace and updates HP",world.player_hp==hurt+world.CAMP_HEAL_HP and world.opening_hud.health_bar.value==world.player_hp and peak>.8)
	check("Furnace recovery leaves balances intact",world.inventory.carried==stock and world.inventory.settlement.served==wallet)
	print("HEARTH_QA ",JSON.stringify({"checks":checks,"minimum_light":lo,"maximum_light":hi,"outdoor_hp":hurt,"return_hp":world.player_hp,"recovery_flash":peak}))
	await Profiles.drain_field_audio(self,world)
	world.queue_free()
	for tick in 4:await process_frame
	quit(0 if not checks.values().has(false) else 1)
