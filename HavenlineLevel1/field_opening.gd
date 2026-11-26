extends "res://orbit_opening.gd"

const Progress = preload("res://field_progression.gd")
const OfferFloor = preload("res://field_offer_floor.gd")
const Inventory = preload("res://field_inventory.gd")
const Carry = preload("res://field_carry.gd")
const FieldArt = preload("res://field_art.gd")
const FieldEnvironment = preload("res://field_environment.gd")
const FieldEnemy = preload("res://field_enemy.gd")
const FieldAudio = preload("res://field_audio.gd")
const FieldSave = preload("res://field_save.gd")

const HEARTH_OFFER := "center_hearth"
const UPGRADE_OFFER := "orbit_upgrade"
const PICKUP_RADIUS := 1.38
const PAD_RADIUS := 1.0
const MAX_HP := 4
const UPGRADE_GLINT = preload("res://assets/field_ui/upgrade_glint.svg")
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
var player_hp := MAX_HP
var player_invulnerability := 0.0
var reset_time := 0.0
var lifecycle := preload("res://field_lifecycle.gd").new()
var encounters := preload("res://field_encounters.gd").new()
var defense_tower := preload("res://field_defense_tower.gd").new()
var rocks: Array[Node3D] = []
var events: Array[Dictionary] = []
var last_half_stride := -1
var last_support_step := 0
var procedural_step_last := false
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
var rescue_time := 0.0
var simulation_time := 0.0
var last_notice := ""
var current_music := ""

func create_opening_hud() -> OpeningHUD:
	return preload("res://field_hud.gd").new()

func _ready() -> void:
	super()
	lifecycle.world = self
	encounters.setup(self)
	inventory.configure(Progress.offers(layout.furnace_cost))
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
	tracks.register_actor(actor,"human")
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
	last_good = inventory.snapshot()
	lifecycle.register("starter-wood","wood",resource_tree)
	lifecycle.register("starter-stone","stone",resource_rock)
	rocks.append(resource_rock)
	_configure_stem(resource_tree)
	trees.append(resource_tree)
	for pos in [Vector2(-5.0,9.3),Vector2(-8.6,8.5),Vector2(-8.4,12),Vector2(-5.4,13.5),Vector2(-11.3,6.3),Vector2(-10.8,10.4),Vector2(-8.9,15),Vector2(-12.5,13.1)]:
		_add_pine(pos)
	add_child(defense_tower)
	defense_tower.setup(self)
	_apply_hearth(inventory.complete(HEARTH_OFFER),false)
	if inventory.world_state.is_empty():
		encounters.launch(false)
	elif not lifecycle.restore(inventory.world_state):
		persist_blocked = true
		persist_error = "Saved world state could not be restored."
	# A saved position on the apron begins a new visit only after stepping out.
	if not inventory.world_state.is_empty() and depot.at_apron(actor.position): depot.visit = "done"
	field_ready = true
	original_auto_quit = get_tree().auto_accept_quit
	get_tree().auto_accept_quit = false
	get_window().close_requested.connect(_close_field)
	forest.install.call_deferred(self)
	character_kit.set_upgraded(inventory.complete(UPGRADE_OFFER))
	_refresh_field()
	world_landscape = load("res://world_landscape.gd").new()
	add_child(world_landscape)
	world_landscape.install.call_deferred(self)

func _notification(what: int) -> void:
	if what == NOTIFICATION_APPLICATION_PAUSED and field_ready and not closing:
		_persist_world()

func _close_field() -> void:
	if closing: return
	closing = true
	_persist_world()
	set_physics_process(false)
	sound.stop_playback()
	# Let the audio server release queued streaming voices before exiting.
	await get_tree().create_timer(.24,true,false,true).timeout
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

func add_resource_source(id: String, kind: String, at: Vector2, variant := 0) -> Node3D:
	if is_instance_valid(lifecycle.loaded.get(id)): return lifecycle.loaded[id]
	if kind=="wood":
		return _add_pine(at,clampi(variant,0,CONIFERS.size()-1),id)
	if kind!="stone" or id.is_empty(): return null
	var rock := ResourceRockScript.new()
	rock.name="HarvestStone"
	rock.position=Vector3(at.x,0,at.y)
	add_child(rock,true)
	var mount := Node3D.new()
	rock.add_child(mount)
	mount.scale=Vector3.ONE*ResourceRockScript.BANK_SCALE
	var model := SNOW_STONE.instantiate() as Node3D
	mount.add_child(model)
	var part := model as MeshInstance3D
	if not part: part=model.find_children("*","MeshInstance3D",true,false)[0]
	rock._mesh=part
	part.position.y=-part.mesh.get_aabb().position.y
	if not trunk_cache.has(part.mesh): trunk_cache[part.mesh]=part.mesh.generate_triangle_mesh()
	rock.attach_bank_body()
	surfaces[rock]=[part,trunk_cache[part.mesh]]
	rocks.append(rock)
	lifecycle.register(id,"stone",rock)
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
	if event is InputEventKey and event.physical_keycode == KEY_U:
		return
	super(event)

func reachable(body: Node3D) -> bool:
	if (body in trees or body in rocks) and is_instance_valid(body):
		return body.can_address(actor.global_position, body.global_position-actor.global_position)
	return super(body)

func selected_tool() -> String:
	# Inside a mixed grove, a trunk near the player's boots cannot intercept
	# the cutting head at the edge of the orbit. Give a reachable stone on
	# that sweep priority until depleted; contact still uses its real mesh.
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
		landed = body.strike(ResourceTreeScript.TREE_ID,tree_input_sequence,actor.global_position,body.global_position-actor.global_position,travel,at)
	elif body in rocks and body != resource_rock:
		rock_input_sequence += 1
		landed=body.strike(ResourceRockScript.ROCK_ID,rock_input_sequence,actor.position,body.position-actor.position)
		if landed: body._mesh.position.y=-body._mesh.mesh.get_aabb().position.y*body._mesh.scale.y
	else:
		landed = super(body)
	if not landed:
		return false
	if body in trees:
		lifecycle.record_strike(body)
		_event("impact_wood",body.global_position)
	elif body in rocks:
		lifecycle.record_strike(body)
		_event("impact_stone",body.global_position)
		if body.phase == "mined":
			_event("deplete_stone",body.global_position)
			_make_drops("stone",body.global_position,3)
			lifecycle.deplete(body)
			_checkpoint_lifecycle()
	else:
		_event("player_attack",body.global_position)
		_event("hit",body.global_position)
	return true

func step_tree(dt: float) -> void:
	tree_button.hide()
	if persist_blocked or not field_ready: return
	lifecycle.advance(dt)
	for rock in rocks:
		rock.set_meta("orbit_reach",SURFACE_REACH*character_kit.reach_scale)
		if rock != resource_rock: rock.advance(dt)
	for tree in trees:
		tree.set_meta("orbit_reach",SURFACE_REACH * character_kit.reach_scale)
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
			if carry.pickup(token,drop.kind,unit.position):
				unit.queue_free()
				drops.erase(token)

func _wolf_defeated(at: Vector3, wolf: FieldEnemy) -> void:
	_event("defeat",at)
	_event("meat",at)
	if wolf.is_boss: _event("boss_defeat",at)
	_make_drops("meat",at,5 if wolf.is_boss else 2)
	_checkpoint_lifecycle()

func _combat_number(at: Vector3, message: String, color: Color) -> void:
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
	number.position = at
	var tween := number.create_tween().set_parallel(true)
	tween.tween_property(number,"position",at+Vector3.UP*.60,.56).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
	tween.tween_property(number,"modulate:a",0.0,.27).set_delay(.29)
	tween.tween_property(number,"outline_modulate:a",0.0,.27).set_delay(.29)
	tween.chain().tween_callback(number.queue_free)

func _wolf_damage_feedback(amount: int, wolf: FieldEnemy) -> void:
	_combat_number(wolf.global_position+Vector3.UP*(2.04*wolf.size_factor()),"−%d" % amount,Color("#ffebaf"))

func _player_hit(amount: int, attacker: Node3D = null) -> void:
	if amount <= 0 or player_invulnerability > 0.0 or reset_time > 0 or persist_blocked or field_env.is_inside_camp(actor.position): return
	var loss := mini(player_hp, amount)
	player_hp -= loss
	if is_instance_valid(attacker):
		var away := hero_model.global_basis.x.dot(actor.global_position-attacker.global_position)
		recoil_side = signf(away) if absf(away)>.01 else 1.0
	_combat_number(actor.position+Vector3.UP*2.16,"−%d" % loss,Color("#ff8469"))
	opening_hud.set_health(player_hp,MAX_HP)
	hurt_time = .32
	player_invulnerability = 1.0
	flash.color.a = .26
	_event("player_hurt",actor.position)
	if player_hp == 0:
		_event("player_fall",actor.position)
		reset_time = 1.05
		character_kit.rest()
	_checkpoint_lifecycle()
	_refresh_field()

func step_technical_gates(dt: float) -> void:
	var previous := {}
	for gate in gates: previous[gate] = gate.angle
	super(dt)
	if not field_ready: return
	for gate in gates:
		if not is_equal_approx(gate.angle,previous[gate]):
			if not moving_gates.has(gate):
				moving_gates[gate] = true
				_event("gate",gate.position)
			if is_equal_approx(gate.angle,PI/2 if gate.target_open else 0.0):
				moving_gates.erase(gate)
				_event("gate_latch",gate.position)

func _physics_process(dt: float) -> void:
	if not field_ready: return
	simulation_time += dt
	forest.advance(dt)
	var last_turn: int = character_kit.turn_id
	if reset_time > 0:
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
			camera.position = actor.position + Vector3(7,11,11)
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
	var previous_tool: String = character_kit.equipped
	super(dt)
	if persist_blocked: return
	if not previous_tool.is_empty() and previous_tool != character_kit.equipped and character_kit.equipped in ["axe","pickaxe"]:
		_event("equip_"+character_kit.equipped,actor.position)
	hurt_time = maxf(0.0,hurt_time-dt)
	rescue_time = maxf(0.0,rescue_time-dt)
	var recoil := sin(PI*hurt_time/.32)
	hero_model.rotation.z = -recoil_side*.23*recoil
	hero_model.rotation.x = -.14*recoil+.18*smoothstep(0,.32,rescue_time)
	sound.set_listener_position(actor.position)
	if character_kit.active and character_kit.turn_id != last_turn and not first_physics:
		_event("swing",actor.position)
	first_physics = false
	var inside: bool = field_env.is_inside_camp(actor.global_position)
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
	sound.set_hearth_proximity(clampf(1.0-actor.position.length()/7.0,0.0,1.0) if camp_active else 0.0)
	var music := "threat" if danger else ("camp" if inside else "field")
	if current_music != music:
		current_music = music
		sound.set_music_state(music)
	_refresh_hud_field(danger)

func _step_foot_audio(inside: bool) -> void:
	var gait = character_kit.locomotion
	var procedural: bool = gait_motor.procedural_steps_active
	var serial: int = gait_motor.support_step_serial
	var landed := serial != last_support_step
	var authored_half := floori(2.0 * fposmod(float(gait.tree.get("parameters/walk/current_position")) / gait.walk_length, 1.0))
	# A procedural boot can touch down on the same tick that the gait takes over.
	# Re-seed its phase here so one physical step triggers one surface sound.
	if not procedural and not procedural_step_last and last_half_stride >= 0:
		landed = landed or (gait.stride_hz > .05 and authored_half != last_half_stride)
	last_support_step = serial
	last_half_stride = authored_half
	procedural_step_last = procedural
	if landed:
		_event("step_camp" if inside else "step_snow",actor.position)

func _event(id: String, at: Vector3) -> void:
	events.append({"event":id,"t":snappedf(simulation_time,.001),"x":snappedf(at.x,.01),"z":snappedf(at.z,.01)})
	if events.size()>1024: events.pop_front()
	sound.emit_event(id,at)

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
		reveal_countdown = .30
		_event("build",anchor.global_position)
		_event("rise",anchor.global_position)
	else:
		if id not in Progress.STORAGE: exit_required[id] = true
		if id in [Progress.FIRST,Progress.SECOND]:
			field_env.set_perimeter(Progress.stage(inventory),true)
			if not orbit_permitted_at(actor.global_position): character_kit.rest()
			if tracks: tracks.refresh_surface()
		elif id.begins_with("storage_"):
			depot.visit = "done"
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
	field_env.set_built(built,animate)
	field_env.set_perimeter(Progress.stage(inventory) if built else 0,animate)
	if tracks: tracks.refresh_surface()
	if built and not orbit_permitted_at(actor.global_position): character_kit.rest()
	if field_ready: _refresh_field()

func orbit_permitted_at(world_position: Vector3) -> bool:
	return not field_env.is_inside_camp(world_position)

func _step_receivers() -> void:
	if reveal_countdown >= 0.: return
	depot.step(actor.position)
	for id in inventory.costs:
		if id in Progress.STORAGE: continue
		var anchor: Node3D = carry.receivers[id]
		var close := actor.position.distance_squared_to(anchor.global_position) <= PAD_RADIUS * PAD_RADIUS
		if not close:
			exit_required.erase(id)
			continue
		if exit_required.has(id): continue
		if inventory.offer_open(id):
			carry.contribute(id)

func _refresh_field() -> void:
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
	elif danger: hint = "Wolves nearby"
	else:
		if not camp_active: hint = "Fell pines to build the hearth."
		elif not inventory.complete(Progress.FIRST): hint = "Bring wood and stone to expand camp."
		elif not inventory.complete(Progress.SECOND):
			hint = "Fund the east expansion." if depot.offer.is_empty() else Progress.TITLES[depot.offer] + " in the northwest."
		elif not inventory.complete(Progress.TOWER) or not inventory.complete(UPGRADE_OFFER):
			hint = "Fund the marked battlefield upgrades."
		else: hint = "Watchtower built  ·  Extra axes equipped"
		for id in inventory.costs:
			if id in Progress.STORAGE: continue
			var anchor: Node3D = carry.receivers[id]
			if actor.position.distance_squared_to(anchor.global_position) > 1.6: continue
			if inventory.offer_open(id) and (camp_active or id == HEARTH_OFFER):
				hint = "%s  ·  %s" % [Progress.TITLES[id], Progress.price_text(inventory.remaining(id))]
		if depot.apron.visible and depot.at_apron(actor.position): hint = depot.hint()
	var notice := str(inventory.carried.values()) + hint
	if notice == last_notice: return
	last_notice = notice
	opening_hud.field_status(inventory.carried,hint)
