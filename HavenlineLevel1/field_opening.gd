extends "res://orbit_opening.gd"

const Progress = preload("res://field_progression.gd")
const OfferFloor = preload("res://field_offer_floor.gd")
const Inventory = preload("res://field_inventory.gd")
const Carry = preload("res://field_carry.gd")
const MiningResources = preload("res://mining_resources.gd")
const FieldArt = preload("res://field_art.gd")
const FieldEnvironment = preload("res://field_environment.gd")
const FieldEnemy = preload("res://field_enemy.gd")
const FieldAudio = preload("res://field_audio.gd")
const FieldSave = preload("res://field_save.gd")

const HEARTH_OFFER := "center_hearth"
const UPGRADE_OFFER := "orbit_upgrade"
const PICKUP_RADIUS := 1.38
const Reach = preload("res://field_reach.gd")
const RUN_STICK_DEAD_ZONE := 0.11
const MAX_HP := 10 * FieldEnemy.MAX_HEALTH
const RECOIL_SECONDS := .38
const CAMP_HEAL_INTERVAL := 1.0
const CAMP_HEAL_HP := 3
const UPGRADE_GLINT = preload("res://assets/field_ui/upgrade_glint.svg")
var lakeshore
var processors
var owl
var survivor
var counter
var settlement_loop
var previous_dry_position := Vector3.INF
var world_landscape
var tracks
var depot := preload("res://field_depot.gd").new()
var offer_floors := {}
var exit_required := {}
var inventory := Inventory.new()
var carry := Carry.new()
var field_env := FieldEnvironment.new()
var sound := FieldAudio.new()
var field_save := FieldSave.new()
var enemy: FieldEnemy
var enemies: Array[FieldEnemy] = []
var trees: Array[Node3D] = []
var forest := preload("res://field_forest.gd").new()
var trunk_cache := {}
var drops: Dictionary = {}
var drop_id := 0
var camp_heal_elapsed := 0.0
var player_hp := MAX_HP
var player_invulnerability := 0.0
var reset_time := 0.0
var lifecycle := preload("res://field_lifecycle.gd").new()
var encounters := preload("res://field_encounters.gd").new()
var defense_tower := preload("res://field_defense_tower.gd").new()
var rocks: Array[Node3D] = []
var events: Array[Dictionary] = []
var boot_raised_for_audio: Array[bool] = [false,false]
var first_physics := true
var field_ready := false
var original_auto_quit := true
var closing := false
var camp_active := false
var reveal_countdown := -1.0
var flash: ColorRect
var hero_model: Node3D
var last_good: Dictionary
var moving_gates := {}
var hurt_time := 0.0
var recoil_side := 1.0
var impact_lean := Vector2(1,0)
var rescue_time := 0.0
var simulation_time := 0.0
var last_notice := ""
var next_project := ""
var current_music := ""

func create_opening_hud() -> OpeningHUD:
	return preload("res://field_hud.gd").new()

func move_actor(input: Vector2, dt: float) -> float:
	# The drag supplies a heading. Any deliberate displacement requests a run.
	var heading := input.normalized() if input.length_squared() > RUN_STICK_DEAD_ZONE * RUN_STICK_DEAD_ZONE else Vector2.ZERO
	return gait_motor.step(self, heading, dt)

func _ready() -> void:
	super()
	character_kit.locomotion.use_field_run()
	gait_motor.use_field_run()
	lifecycle.world = self
	encounters.setup(self)
	inventory.configure(Progress.offers())
	persist_requested = true
	if not field_save.configure(OS.get_cmdline_user_args()):
		persist_blocked = true
		persist_error = "Field save directory unavailable."
	else:
		var result := field_save.load_into(inventory)
		persist_blocked = result != OK and result != ERR_FILE_NOT_FOUND
		if persist_blocked:
			persist_error = "Field profile could not be read."
	for marker: Node3D in wood_visuals.values():
		marker.hide()
	wood_stock_view.hide()
	purchase_pad_view.hide()
	add_child(field_env)
	field_env.install(self)
	tracks = preload("res://field_snow_tracks.gd").new()
	add_child(tracks)
	tracks.configure(func(pos:Vector3): return not field_env.is_inside_camp(pos))
	tracks.register_actor(actor,"human",1.0,gait_motor.snow_contact_points)
	add_child(carry)
	carry.setup(inventory, actor, FieldArt.make)
	add_child(depot)
	depot.install(self)
	carry.define_receiver(HEARTH_OFFER, field_env.buy_anchor)
	for id in inventory.costs:
		if id == HEARTH_OFFER or id in Progress.STORAGE: continue
		var anchor: Vector2 = Progress.POSITIONS[id]
		var at := Vector3(anchor.x,0,anchor.y)
		var floor_mark := OfferFloor.new()
		field_env.add_child(floor_mark)
		floor_mark.install(field_env,id,at)
		offer_floors[id] = floor_mark
		carry.define_receiver(id,floor_mark)
	carry.inventory_changed.connect(_inventory_changed)
	carry.purchase_completed.connect(_finish_purchase)
	carry.unit_landed.connect(_landed)
	add_child(sound)
	flash = ColorRect.new()
	flash.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	flash.mouse_filter = Control.MOUSE_FILTER_IGNORE
	flash.color = Color(0.47,0.085,0.07,0.0)
	opening_hud.get_parent().add_child(flash)
	hero_model = character_kit.locomotion.tree.get_parent()
	_disable_worn_shadow(hero_model)
	_disable_worn_shadow(carry.rack)
	last_good = inventory.snapshot()
	lifecycle.register("starter-wood","wood",resource_tree)
	lifecycle.register("starter-stone","stone",resource_rock)
	rocks.append(resource_rock)
	_configure_stem(resource_tree)
	trees.append(resource_tree)
	# Leave a full work stance between the pines and preserve the saved harvest ID.
	_add_pine(Vector2(-6.47,9.12),0,"pine@-5000,9300")
	for pos in [Vector2(-8.6,8.5),Vector2(-8.4,12),Vector2(-5.4,13.5),Vector2(-11.3,6.3),Vector2(-10.8,10.4),Vector2(-8.9,15),Vector2(-12.5,13.1)]:
		_add_pine(pos)
	add_child(defense_tower)
	defense_tower.setup(self)
	_apply_hearth(inventory.complete(HEARTH_OFFER),false)
	if inventory.world_state.is_empty():
		encounters.launch(false)
	elif not lifecycle.restore(inventory.world_state):
		persist_blocked = true
		persist_error = "Saved world state could not be restored."
	# Restore the paid footprint before classifying a saved position on its edge.
	depot.refresh(camp_active)
	# Resume loading at the doorway, while requiring a fresh approach to buy.
	if not inventory.world_state.is_empty() and ((depot.house.tier == 0 and depot.at_apron(actor.position)) or depot.on_upgrade_side(actor.position)):
		depot.pause_purchase(actor.position)
	settlement_loop = preload("res://field_settlement_loop.gd").new()
	add_child(settlement_loop)
	settlement_loop.install(self)
	previous_dry_position = actor.position
	field_ready = true
	var home_compass := preload("res://field_navigation.gd").new()
	opening_hud.add_child(home_compass)
	home_compass.install(self,opening_hud)
	original_auto_quit = get_tree().auto_accept_quit
	get_tree().auto_accept_quit = false
	get_window().close_requested.connect(_close_field)
	get_viewport().size_changed.connect(_release_field_gestures)
	forest.install.call_deferred(self)
	character_kit.set_upgraded(inventory.complete(UPGRADE_OFFER))
	_refresh_field()
	world_landscape = load("res://world_landscape.gd").new()
	add_child(world_landscape)
	world_landscape.install.call_deferred(self)

func _notification(what: int) -> void:
	if not field_ready or closing:
		return
	if what == NOTIFICATION_APPLICATION_FOCUS_OUT or what == NOTIFICATION_APPLICATION_PAUSED:
		_release_field_gestures()
	if what == NOTIFICATION_APPLICATION_PAUSED:
		_persist_world()

func _release_field_gestures() -> void:
	# A fold, task switch or system overlay can interrupt a drag without a release.
	clear_touch()
	settlement_loop.finger = -1

func _close_field() -> void:
	if closing: return
	closing = true
	_persist_world()
	set_physics_process(false)
	sound.stop_playback()
	# Let the audio server release queued streaming voices before exiting.
	var release_at := Time.get_ticks_msec() + 240
	while Time.get_ticks_msec() < release_at:
		await get_tree().process_frame
	if is_inside_tree(): get_tree().quit()

func _exit_tree() -> void:
	if field_ready:
		get_tree().auto_accept_quit = original_auto_quit

# The base scene uses an older inventory envelope. This scene owns its own save.
func load_opening_profile(_args: PackedStringArray) -> void:
	pass

func _add_pine(at: Vector2, variant := 0, source_id := "") -> ResourceTreeScript:
	var tree := ResourceTreeScript.new()
	tree.name = "HarvestPine"
	tree.position = Vector3(at.x,0,at.y)
	add_child(tree,true)
	if source_id == "survivor-work-pine":
		tree.build(preload("res://assets/reference_forest/forester_work_pine.glb"),true)
		tree.fall_reach = 3.56
	else:
		tree.build(CONIFERS[variant],true)
	_configure_stem(tree)
	var parts := tree._pivot.find_children("*","MeshInstance3D",true,false)
	for part: MeshInstance3D in parts:
		var mesh := part.mesh
		if not mesh: continue
		if not trunk_cache.has(mesh):
			var faces := PackedVector3Array()
			for surface in mesh.get_surface_count():
				var material := mesh.surface_get_material(surface)
				if material and material.resource_name.to_lower() == "trunk":
					var arrays := mesh.surface_get_arrays(surface)
					var vertices: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX]
					for index in arrays[Mesh.ARRAY_INDEX]:
						faces.append(vertices[index])
			if faces.is_empty(): continue
			var trunk := TriangleMesh.new()
			trunk.create_from_faces(faces)
			trunk_cache[mesh] = trunk
		surfaces[tree] = [part,trunk_cache[mesh]]
		break
	trees.append(tree)
	if source_id.is_empty(): source_id="pine@%d,%d" % [roundi(at.x*1000),roundi(at.y*1000)]
	lifecycle.register(source_id,"wood",tree)
	return tree

func retire_tree(tree: ResourceTreeScript, animate: bool) -> void:
	if tree.phase in ["falling","ready_to_credit"]:
		_credit_tree(tree)
	lifecycle.loaded.erase(tree.get_meta("field_source_id",""))
	trees.erase(tree)
	surfaces.erase(tree)
	if animate and tree.visible and tree._pivot.visible:
		var thaw := tree.create_tween().set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_IN)
		thaw.tween_property(tree,"scale",Vector3.ONE*.015,.31)
		thaw.tween_callback(tree.queue_free)
	else:
		tree.queue_free()

func is_source_available(id: String) -> bool:
	return not lifecycle.cooling.has(id)

func make_mineral_model(kind: String) -> Node3D:
	var scene: PackedScene = SNOW_STONE if kind == "stone" else load(FieldArt.PATHS[kind])
	var mount := Node3D.new()
	var model := scene.instantiate() as Node3D
	mount.add_child(model)
	mount.scale = Vector3.ONE * MiningResources.bank_scale(kind)
	var part := mount.find_children("*", "MeshInstance3D", true, false)[0] as MeshInstance3D
	part.position.y = -part.mesh.get_aabb().position.y
	return mount

func add_resource_source(id: String, kind: String, at: Vector2, variant := 0) -> Node3D:
	if is_instance_valid(lifecycle.loaded.get(id)): return lifecycle.loaded[id]
	if kind=="wood":
		return _add_pine(at,clampi(variant,0,CONIFERS.size()-1),id)
	if kind not in MiningResources.KINDS or id.is_empty(): return null
	var rock := ResourceRockScript.new()
	rock.name="Harvest" + kind.capitalize()
	rock.position=Vector3(at.x,0,at.y)
	add_child(rock,true)
	var mount := make_mineral_model(kind)
	rock.add_child(mount)
	var part := mount.find_children("*", "MeshInstance3D", true, false)[0] as MeshInstance3D
	rock._mesh = part
	if not trunk_cache.has(part.mesh): trunk_cache[part.mesh]=part.mesh.generate_triangle_mesh()
	rock.attach_bank_body()
	surfaces[rock]=[part,trunk_cache[part.mesh]]
	rocks.append(rock)
	lifecycle.register(id,kind,rock)
	return rock

func unload_resource_source(id: String) -> void:
	var node = lifecycle.loaded.get(id)
	if not is_instance_valid(node) or node==resource_tree or node==resource_rock: return
	if node in trees:
		retire_tree(node,false)
	else:
		lifecycle.loaded.erase(id)
		rocks.erase(node)
		surfaces.erase(node)
		node.queue_free()

func _configure_stem(tree: ResourceTreeScript) -> void:
	tree.regrows = false
	tree.fall_away = true
	for marker in tree._marks:
		marker.queue_free()
	tree._marks.clear()

func _input(event: InputEvent) -> void:
	if field_ready and settlement_loop.handle_input(event):
		return
	if event is InputEventKey and event.physical_keycode == KEY_U:
		return
	super(event)

func selected_tool() -> String:
	# Prefer the pick when the orbit passes a bank in a mixed grove. Inner
	# targets also participate through the usual nearest-target selection.
	for rock in rocks:
		if not reachable(rock): continue
		var offset: Vector3 = rock.global_position - actor.global_position
		var side := offset.dot(Orbit.CAMERA_RIGHT) / Orbit.RADIUS_SIDE
		var depth := offset.dot(Orbit.CAMERA_NEAR) / Orbit.RADIUS_DEPTH
		var relative := Vector2(side,depth).length() / float(character_kit.reach_scale)
		if relative >= .64 and relative <= 1.24:
			return "pickaxe"
	return super()

func accept_contact(body: Node3D) -> bool:
	if not field_ready or persist_blocked or reset_time > 0:
		return false
	if body in trees and character_kit.equipped != "axe": return false
	if body in rocks and character_kit.equipped != "pickaxe": return false
	var landed := false
	if body in trees:
		tree_input_sequence += 1
		var geometry: MeshInstance3D = surfaces[body][0]
		var matched: bool = character_kit.hit_geometry == geometry
		var travel: Vector3 = character_kit.hit_travel if matched else Vector3.ZERO
		var at: Vector3 = character_kit.hit_position if matched else Vector3.INF
		character_kit.hit_geometry = null
		landed = body.strike(ResourceTreeScript.TREE_ID,tree_input_sequence,actor.global_position,body.global_position-actor.global_position,travel,at,matched)
	elif body in rocks and body != resource_rock:
		rock_input_sequence += 1
		landed=body.strike(ResourceRockScript.ROCK_ID,rock_input_sequence,actor.position,body.position-actor.position,character_kit.hit_geometry == surfaces[body][0])
	else:
		landed = super(body)
	if not landed:
		return false
	if body in trees:
		lifecycle.record_strike(body)
		_event("impact_wood",body.global_position)
	elif body in rocks:
		var kind: String = body.get_meta("resource_kind")
		lifecycle.record_strike(body)
		_event("impact_"+kind,body.global_position)
		if body.phase == "mined":
			_event("deplete_"+kind,body.global_position)
			_make_drops(kind,body.global_position,3)
			lifecycle.deplete(body)
			_checkpoint_lifecycle()
	else:
		_event("player_attack",body.global_position)
		_event("hit",body.global_position)
	return true

func step_tree(dt: float) -> void:
	tree_button.hide()
	if persist_blocked or not field_ready: return
	for rock in rocks:
		rock.set_meta("orbit_reach",character_kit.maximum_radius())
		if rock != resource_rock: rock.advance(dt)
	for tree in trees:
		tree.set_meta("orbit_reach",character_kit.maximum_radius())
		tree.advance(dt,actor.position,float(layout.actor_radius))
		if tree.phase == "ready_to_credit":
			_credit_tree(tree)

func _credit_tree(tree: ResourceTreeScript) -> void:
	if not tree.phase in ["falling","ready_to_credit"]: return
	_event("deplete_wood",tree.global_position)
	_make_drops("wood",tree.global_position,3)
	lifecycle.deplete(tree)
	_checkpoint_lifecycle()

func _checkpoint_lifecycle() -> void:
	if field_ready and persist_requested and not persist_blocked and has_method("_persist_world"):
		call("_persist_world")

func _collect_wood_source(_source: String) -> bool:
	return false

func fund_opening_receiver(_receiver_id: Variant = null, _material_id: Variant = null) -> bool:
	return false

func _make_drops(kind: String, origin: Vector3, amount: int) -> void:
	for i in amount:
		drop_id += 1
		var token := "%s-%d" % [kind,drop_id]
		while inventory.collected.has(token) or drops.has(token):
			drop_id += 1
			token = "%s-%d" % [kind,drop_id]
		var angle := float(i) * TAU / amount + .7
		var end := origin+Vector3(cos(angle),0,sin(angle))*(.48+.15*float(i%2))
		_place_drop(token,kind,origin+Vector3.UP*.29,end,angle*.75,0)
	_event("drop_"+kind,origin)

func _place_drop(token: String, kind: String, start: Vector3, end: Vector3, yaw: float, age: float) -> void:
	if drops.has(token) or inventory.collected.has(token): return
	if drops.size()>=lifecycle.DROP_CAP: _remove_drop(drops.keys()[0])
	var item := FieldArt.make(kind)
	if not item: return
	add_child(item)
	item.position=start
	item.rotation.y=yaw
	drops[token]={"mesh":item,"kind":kind,"at":end,"from":start,"age":age}

func _remove_drop(token: String) -> void:
	if not drops.has(token): return
	var item: Node3D=drops[token].mesh
	if is_instance_valid(item): item.queue_free()
	drops.erase(token)

func _step_drops(dt: float) -> void:
	for token: String in drops.keys():
		var drop: Dictionary = drops[token]
		drop.age += dt
		if drop.age >= lifecycle.DROP_LIFETIME_SECONDS:
			_remove_drop(token)
			continue
		var t := clampf(float(drop.age)/.3,0.0,1.0)
		var unit: Node3D = drop.mesh
		unit.position = (drop.from as Vector3).lerp(drop.at,t)+Vector3.UP*.30*sin(t*PI)
		if t == 1.0 and reset_time <= 0.0 and actor.position.distance_to(unit.position) <= PICKUP_RADIUS:
			if carry.pickup(token,drop.kind,unit.position,unit.global_rotation.y):
				unit.queue_free()
				drops.erase(token)

func _wolf_defeated(at: Vector3, wolf: FieldEnemy) -> void:
	_event("defeat",at)
	_event("meat",at)
	if wolf.is_boss: _event("boss_defeat",at)
	_make_drops("meat",at,5 if wolf.is_boss else 2)
	_checkpoint_lifecycle()

func _combat_number(at: Vector3, message: String, color: Color, target: Node3D = null) -> void:
	var number := Label3D.new()
	number.name = "CombatFeedback"
	number.text = message
	number.font_size = 47
	number.pixel_size = .009
	number.outline_size = 10
	number.modulate = color
	number.outline_modulate = Color("#19232e")
	number.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	number.no_depth_test = true
	add_child(number)
	if target:
		# A tool, tower and owl can hit one wolf within the same few frames.
		# Compare live billboards on the camera's horizontal axis as the wolf moves.
		var group := StringName("wolf_feedback_%d" % target.get_instance_id())
		var peers := get_tree().get_nodes_in_group(group)
		var right := camera.global_basis.x.normalized()
		var width := maxf(.85, number.get_aabb().size.x + .14)
		var lane := 0
		var offset := 0.0
		var occupied: Array[float] = []
		for peer: Label3D in peers:
			occupied.append((peer.global_position-at).dot(right))
		while _feedback_lane_occupied(occupied,offset,width):
			lane += 1
			offset = ceilf(lane*.5)*width*(1.0 if lane%2 else -1.0)
		at += right*offset
		number.add_to_group(group)
	number.position = at
	var tween := number.create_tween().set_parallel(true)
	tween.tween_property(number,"position",at+Vector3.UP*.60,.56).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
	tween.tween_property(number,"modulate:a",0.0,.27).set_delay(.29)
	tween.tween_property(number,"outline_modulate:a",0.0,.27).set_delay(.29)
	tween.chain().tween_callback(number.queue_free)

func _feedback_lane_occupied(centers: Array[float], offset: float, width: float) -> bool:
	for center: float in centers:
		if absf(center-offset)<width-.001:
			return true
	return false

func _wolf_damage_feedback(amount: int, wolf: FieldEnemy) -> void:
	_combat_number(wolf.global_position+Vector3.UP*(2.04*wolf.size_factor()),"−%d" % amount,Color("#ffebaf"),wolf)

func _player_hit(amount: int, attacker: Node3D = null) -> void:
	if amount <= 0 or player_invulnerability > 0.0 or reset_time > 0 or persist_blocked or field_env.is_inside_camp(actor.position): return
	var loss := mini(player_hp, amount)
	player_hp -= loss
	camp_heal_elapsed = 0.0
	impact_lean = Vector2(1,0)
	if is_instance_valid(attacker):
		var away := actor.global_position - attacker.global_position
		var local_away := actor.global_basis.inverse() * away
		if local_away.length_squared() > .0001:
			impact_lean = Vector2(local_away.x,local_away.z).normalized()
	recoil_side = signf(impact_lean.x) if absf(impact_lean.x)>.01 else 1.0
	_combat_number(actor.position+Vector3.UP*2.16,"−%d" % loss,Color("#ff8469"))
	opening_hud.set_health(player_hp,MAX_HP)
	hurt_time = RECOIL_SECONDS
	player_invulnerability = 1.0
	flash.color.a = .33
	_event("player_hurt",actor.position)
	if player_hp == 0:
		settlement_loop.cancel_cooking()
		_event("player_fall",actor.position)
		reset_time = 1.05
		character_kit.rest()
	_checkpoint_lifecycle()
	_refresh_field()

func step_technical_gates(dt: float) -> void:
	var helper := Vector3.INF
	if survivor and is_instance_valid(survivor.actor):
		helper = survivor.actor.global_position
	var bystanders: Array[Vector4] = []
	for wolf in enemies:
		if wolf.active and wolf.hp>0:
			var feet:Vector3=wolf.global_position
			bystanders.append(Vector4(feet.x,feet.y,feet.z,.39*wolf.size_factor()))
	nearest_gate = null
	# Level 1 gates open directly on approach from either side.
	gate_button.hide()
	for gate in gates:
		var previous := gate.angle
		gate.advance_automatic(dt,actor.global_position,float(layout.actor_radius),helper,bystanders)
		if gate.interaction_in_range(actor.global_position):
			nearest_gate = gate
		if not field_ready or is_equal_approx(gate.angle,previous): continue
		if not moving_gates.has(gate):
			moving_gates[gate] = true
			_event("gate",gate.position)
		if is_equal_approx(gate.angle,PI/2 if gate.target_open else 0.0):
			moving_gates.erase(gate)
			_event("gate_latch",gate.position)

func toggle_nearest_gate() -> void:
	# Older opening scenes have a manual gate control. This scene's motion
	# and latch use the approach sensor irrespective of keyboard or touch.
	pass

func _physics_process(dt: float) -> void:
	if not field_ready: return
	simulation_time += dt
	if not persist_blocked: lifecycle.advance(dt)
	forest.advance(dt)
	var last_turn: int = character_kit.turn_id
	if reset_time > 0:
		if not persist_blocked: settlement_loop.advance_unattended(dt)
		var fall := smoothstep(0.0,.44,1.05-reset_time)
		hero_model.rotation.z = -recoil_side*1.43*fall
		hero_model.rotation.x = -.20*fall
		flash.color.a = move_toward(flash.color.a,.09,dt*.52)
		reset_time = maxf(0.0,reset_time-dt)
		actor.velocity = Vector3.ZERO
		clear_touch()
		if reset_time <= 0:
			actor.position = lifecycle.safe_start()
			hero_model.rotation = Vector3(0,hero_model.rotation.y,0)
			rescue_time = .32
			hurt_time = 0
			if tracks: tracks.reset_actor(actor)
			camera.position = actor.position + camera_follow_offset
			player_hp = MAX_HP
			player_invulnerability = 2.0
			for wolf in enemies:
				if wolf.hp > 0:
					var hp_before: int = wolf.hp
					wolf.reset_encounter()
					wolf.hp=hp_before
					wolf._refresh_health()
					if tracks: tracks.reset_actor(wolf)
			_event("reset",actor.position)
			_combat_number(actor.position+Vector3.UP*2.16,"+%d HP" % MAX_HP,Color("#83f4b1"))
			_refresh_field()
			_checkpoint_lifecycle()
		return
	previous_dry_position = actor.global_position
	var previous_tool: String = character_kit.equipped
	super(dt)
	if persist_blocked: return
	if not previous_tool.is_empty() and previous_tool != character_kit.equipped and character_kit.equipped in ["axe","pickaxe"]:
		_event("equip_"+character_kit.equipped,actor.position)
	hurt_time = maxf(0.0,hurt_time-dt)
	rescue_time = maxf(0.0,rescue_time-dt)
	var hit_fraction := hurt_time / RECOIL_SECONDS
	var recoil := smoothstep(0, .15, 1.0-hit_fraction) * smoothstep(0, .88, hit_fraction)
	hero_model.rotation.z = -impact_lean.x*.33*recoil
	hero_model.rotation.x = impact_lean.y*.30*recoil+.18*smoothstep(0,.32,rescue_time)
	sound.set_listener_position(actor.position)
	if character_kit.active and character_kit.turn_id != last_turn and not first_physics:
		_event("swing",actor.position)
	first_physics = false
	var inside: bool = field_env.is_inside_camp(actor.global_position)
	_advance_camp_heal(dt)
	if persist_blocked: return
	_step_foot_audio(inside)
	player_invulnerability = maxf(0.0,player_invulnerability-dt)
	flash.color.a = maxf(0.0,flash.color.a-dt*.6)
	var danger := encounters.advance(dt)
	if reset_time > 0.0: return
	defense_tower.advance(dt,inventory.complete("watchtower"))
	_step_drops(dt)
	if reveal_countdown >= 0:
		reveal_countdown -= dt
		if reveal_countdown <= 0:
			reveal_countdown = -1.0
			_apply_hearth(true,true)
			_event("reveal", Vector3.ZERO)
	_step_receivers()
	settlement_loop.advance(dt)
	sound.set_hearth_proximity(clampf(1.0-actor.position.length()/7.0,0.0,1.0) if camp_active else 0.0)
	var music := "camp" if inside else ("threat" if danger else "field")
	if current_music != music:
		current_music = music
		sound.set_music_state(music)
	_refresh_hud_field(danger)

func is_camp_healing() -> bool:
	return player_hp > 0 and player_hp < MAX_HP and reset_time <= 0.0 and not persist_blocked and not closing and field_env.is_inside_camp(actor.global_position)

func _advance_camp_heal(dt: float) -> void:
	if not is_camp_healing():
		camp_heal_elapsed = 0.0
		return
	camp_heal_elapsed += dt
	var intervals := floori((camp_heal_elapsed + .0000001) / CAMP_HEAL_INTERVAL)
	if intervals == 0: return
	var award := mini(intervals * CAMP_HEAL_HP, MAX_HP - player_hp)
	player_hp += award
	camp_heal_elapsed = 0.0 if player_hp == MAX_HP else maxf(0.0,camp_heal_elapsed - intervals * CAMP_HEAL_INTERVAL)
	_checkpoint_lifecycle()
	if persist_blocked:
		player_hp -= award
		camp_heal_elapsed = 0.0
		opening_hud.set_health(player_hp,MAX_HP)
		return
	opening_hud.set_health(player_hp,MAX_HP)
	_combat_number(actor.position+Vector3.UP*2.16,"+%d HP" % award,Color("#83f4b1"))
	_record_field_event("camp_heal",actor.position)

func _step_foot_audio(inside: bool) -> void:
	# Cropped mobile views make a late step especially noticeable. Trigger
	# each surface cue at the physical tread, including the final braking step.
	if actor.velocity.slide(Vector3.UP).length() < .025 and gait_motor.special not in ["brake","pivot"]:
		boot_raised_for_audio.fill(false)
		return
	var soles: PackedVector3Array = gait_motor.snow_contact_points()
	for side in soles.size():
		var clearance := soles[side].y - actor.global_position.y
		if clearance > .045:
			boot_raised_for_audio[side] = true
		elif boot_raised_for_audio[side] and clearance <= .006:
			boot_raised_for_audio[side] = false
			_event("step_camp" if inside else "step_snow",soles[side])

# Only the player and worn stock suppress the moving ground silhouette.
# These surfaces still receive light and shadows from their surroundings.
func _disable_worn_shadow(part: Node) -> void:
	if part is GeometryInstance3D:
		part.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	if not part.child_entered_tree.is_connected(_disable_worn_shadow):
		part.child_entered_tree.connect(_disable_worn_shadow)
	for child in part.get_children():
		_disable_worn_shadow(child)

func _event(id: String, at: Vector3, audio_id := "") -> void:
	_record_field_event(id,at)
	sound.emit_event(id if audio_id.is_empty() else audio_id,at)

func _record_field_event(id: String, at: Vector3) -> void:
	events.append({"event":id,"t":snappedf(simulation_time,.001),"x":snappedf(at.x,.01),"z":snappedf(at.z,.01)})
	if events.size()>1024: events.pop_front()

func _landed(kind: String, dest: String) -> void:
	if persist_blocked: return
	match dest:
		"carry":
			var pending := false
			for flight in carry.flights:
				if flight.to == "carry": pending = true
			_event("pickup_partial" if pending else "pickup_full",actor.position)
			if not pending: _event("carry",actor.position)
		"storage":
			_event("deposit_"+kind,depot.bins[kind].global_position)
		_:
			_event("spend_"+kind,carry.receivers[dest].global_position)

func _persist_world() -> void:
	if not field_ready or persist_blocked: return
	_inventory_changed()

func _inventory_changed() -> void:
	if field_ready and not persist_blocked:
		_clear_paid_machine_site()
		inventory.world_state = lifecycle.snapshot()
	if persist_requested and not persist_blocked:
		var result := field_save.commit(inventory)
		if result != OK:
			persist_blocked = true
			inventory.restore(last_good)
			carry.set_physics_process(false)
			carry.cancel_transfers()
			persist_error = "Field progress paused. Save error %d." % result
		else:
			last_good = inventory.snapshot()
	_refresh_field()

func _finish_purchase(id: String) -> void:
	if persist_blocked: return
	var anchor: Node3D = carry.receivers[id]
	_event("purchase",anchor.global_position)
	if id == HEARTH_OFFER:
		reveal_countdown = .10
		_event("build",anchor.global_position)
		_event("rise",anchor.global_position)
	else:
		if id not in Progress.STORAGE: exit_required[id] = true
		if id in [Progress.FIRST,Progress.SECOND]:
			field_env.set_perimeter(Progress.stage(inventory),true)
			if not orbit_permitted_at(actor.global_position): character_kit.rest()
			if tracks: tracks.refresh_surface()
		elif id.begins_with("storage_"):
			depot.pause_purchase(actor.position,anchor)
		elif id == UPGRADE_OFFER:
			character_kit.set_upgraded(true)
			_upgrade_sparks()
		_event("build",anchor.global_position)
		_event("rise",anchor.global_position)
		_event("victory" if id == UPGRADE_OFFER else "reveal",anchor.global_position)
	_refresh_field()

func _upgrade_sparks() -> void:
	for i in 7:
		var angle := float(i)*TAU/7.0
		var ray := Vector3(cos(angle),.4+float(i%3)*.28,sin(angle))
		var glint := Sprite3D.new()
		glint.texture = UPGRADE_GLINT
		glint.billboard = BaseMaterial3D.BILLBOARD_ENABLED
		glint.pixel_size = .005
		glint.shaded = false
		glint.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		actor.add_child(glint)
		glint.position = Vector3.UP*.85+ray*.32
		glint.scale = Vector3.ONE*.68
		var tween := glint.create_tween().set_parallel(true)
		tween.tween_property(glint,"position",Vector3.UP*.9+ray*1.7,.30).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
		tween.tween_property(glint,"modulate:a",0.0,.21).set_delay(.09)
		tween.chain().tween_callback(glint.queue_free)

func _apply_hearth(built: bool, animate: bool) -> void:
	camp_active = built
	camp_built.process_mode = Node.PROCESS_MODE_INHERIT if built else Node.PROCESS_MODE_DISABLED
	for body in camp_colliders:
		body.collision_layer = 1 if built else 0
	camp_built.visible = built
	if built and animate:
		actor.global_position = field_env.clear_hearth_footprint(actor.global_position)
	field_env.set_built(built,animate)
	field_env.set_perimeter(Progress.stage(inventory) if built else 0,animate)
	if tracks: tracks.refresh_surface()
	if built and not orbit_permitted_at(actor.global_position): character_kit.rest()
	if field_ready: _refresh_field()

func constrain_private_snow_travel() -> void:
	super()
	if lakeshore and previous_dry_position.is_finite():
		actor.global_position = lakeshore.constrain_motion(previous_dry_position, actor.global_position, float(layout.actor_radius))
		if processors:
			actor.global_position = processors.constrain_motion(previous_dry_position,actor.global_position,float(layout.actor_radius))

func orbit_permitted_at(world_position: Vector3) -> bool:
	return not field_env.is_inside_camp(world_position)

func _step_receivers() -> void:
	if reveal_countdown >= 0.: return
	var at := actor.global_position
	var depot_target: String = depot.target_at(at) if camp_active and field_env.is_inside_camp(at) else ""
	var selected := depot_target
	var best := INF
	if not selected.is_empty():
		best = Reach.plot_distance(depot.upgrade_mark,at) if depot.on_upgrade_side(at) else depot.loading_distance(at)
	for id: String in inventory.costs:
		if id in Progress.STORAGE or (not exit_required.has(id) and not inventory.offer_open(id)): continue
		var anchor: Node3D = carry.receivers[id]
		var distance := Reach.plot_distance(anchor,at)
		if distance > Reach.NEAR:
			exit_required.erase(id)
			continue
		if exit_required.has(id) or not inventory.offer_open(id): continue
		if camp_active and not field_env.is_inside_camp(at): continue
		if distance < best:
			best = distance
			selected = id
	if settlement_loop and settlement_loop.works:
		var machines = settlement_loop.works
		var working_distance: float = machines.handoff_distance(at) if not selected.is_empty() else INF
		machines.nearer_plot = not selected.is_empty() and best <= working_distance
		if working_distance < best:
			selected = ""
	if selected != carry.visit_target and not carry.visit_target.begins_with("work:"):
		carry.stop_visit(carry.visit_target)
	depot.step(at,selected if selected == depot_target else "")
	if not selected.is_empty() and selected != depot_target:
		carry.visit(selected)

func _clear_paid_machine_site() -> void:
	if not processors or not lakeshore: return
	var radius := float(layout.actor_radius) + .035
	var at := actor.global_position
	var point := Vector2(at.x,at.z)
	for kind: String in Progress.MACHINES:
		if not inventory.is_machine_owned(kind): continue
		var rect: Rect2 = lakeshore._footprint(radius) if kind == "meat" else processors._rect(kind,radius)
		if not rect.has_point(point): continue
		# The north side backs up to the fence. The two ends and the front
		# aisle have continuous free floor on every paid expansion.
		var exits := [Vector2(rect.position.x-.01,point.y),Vector2(rect.end.x+.01,point.y),Vector2(point.x,rect.end.y+.01)]
		var closest: Vector2=exits[2]
		for edge: Vector2 in exits:
			if point.distance_squared_to(edge)<point.distance_squared_to(closest):closest=edge
		actor.global_position = Vector3(closest.x,at.y,closest.y)
		previous_dry_position = actor.global_position
		return

func _refresh_field() -> void:
	if processors: processors.refresh_ownership()
	if lakeshore: lakeshore.refresh_ownership()
	next_project = Progress.next_build(inventory)
	depot.refresh(camp_active)
	field_env.set_payment(inventory.remaining(HEARTH_OFFER))
	field_env.upgrade_anchor.hide()
	var left: int = inventory.remaining(HEARTH_OFFER).wood
	field_env.set_payment_progress(1.0 - float(left) / inventory.costs[HEARTH_OFFER].wood)
	for id in offer_floors:
		offer_floors[id].set_due(inventory,id,camp_active and inventory.offer_open(id))
	last_notice = ""
	_refresh_hud_field(current_music == "threat")

func _refresh_hud_field(danger: bool) -> void:
	opening_hud.set_health(player_hp,MAX_HP)
	var hint := ""
	if persist_blocked: hint = persist_error
	elif reset_time > 0: hint = "Returning to camp…" if camp_active else "Returning to the hearth plot…"
	else:
		if not next_project.is_empty():
			hint = build_hint(next_project)
		else:
			hint = "All camp purchases complete."
		for id in inventory.costs:
			if id in Progress.STORAGE or not inventory.offer_open(id): continue
			var anchor: Node3D = carry.receivers[id]
			if anchor.is_visible_in_tree() and Reach.plot_distance(anchor,actor.position) <= Reach.NEAR:
				hint = build_hint(id)
		if depot.apron.visible and (depot.at_apron(actor.position) or depot.at_loading_area(actor.position) or (depot.upgrade_mark.visible and depot.on_upgrade_side(actor.position))): hint = depot.hint()
	if settlement_loop and not persist_blocked and reset_time <= 0:
		hint = settlement_loop.hint(hint,false)
	opening_hud.set_threat(danger and not persist_blocked and reset_time <= 0)
	var notice := str(inventory.carried.values()) + hint
	if notice == last_notice: return
	last_notice = notice
	opening_hud.field_status(inventory.carried,hint)

func build_hint(id: String) -> String:
	var title: String = Progress.TITLES[id]
	var price := Progress.price_text(inventory.remaining(id))
	var target: Node3D = carry.receivers[id]
	var range_m := actor.global_position.distance_to(target.global_position)
	if range_m < 1.5: return "%s · %s" % [title,price]
	var screen := camera.unproject_position(target.global_position) - camera.unproject_position(actor.global_position)
	var directions := ["→","↘","↓","↙","←","↖","↑","↗"]
	var direction: String = directions[posmod(roundi(screen.angle()/(PI/4.)),8)]
	return "%s · %s  %s %d m" % [title,price,direction,roundi(range_m)]

# Scene callbacks conclude a physical transfer and save its receipt before celebrating it.
func rescue_survivor() -> bool:
	return settlement_loop.rescue()

func claim_worker_wood(token: String) -> bool:
	return settlement_loop.claim_worker_wood(token)

func receive_worker_wood() -> bool:
	return settlement_loop.deliver_worker_wood()

func cook_meal() -> bool:
	return settlement_loop.cook()

func serve_meal(order: int) -> bool:
	return settlement_loop.serve(order)

func enter_next_level() -> bool:
	return settlement_loop.enter_next_level()

func owl_contact(wolf, at: Vector3) -> bool:
	if not settlement_loop.can_transact() or not inventory.settlement.survivor_paid or not enemies.has(wolf): return false
	if not is_instance_valid(wolf) or not wolf.can_receive_swirl() or field_env.is_inside_camp(wolf.global_position) or not at.is_finite(): return false
	if not owl.permits_contact(wolf,at): return false
	# A fatal hit synchronously persists the loot. Include the owl receipt in that same checkpoint.
	inventory.settlement.owl_hits += 1
	if not wolf.receive_hit(1,at):
		inventory.settlement.owl_hits -= 1
		return false
	return settlement_loop.commit_receipt("owl_hit",at)
