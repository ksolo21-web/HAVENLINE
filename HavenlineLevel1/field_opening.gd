extends "res://orbit_opening.gd"

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
var rock_recovery := 0.0
var respawns := {}
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
var simulation_time := 0.0
var last_notice := ""
var current_music := ""

func create_opening_hud() -> OpeningHUD:
	return preload("res://field_hud.gd").new()

func _ready() -> void:
	super()
	inventory.configure({HEARTH_OFFER: layout.furnace_cost, UPGRADE_OFFER: {"stone":2, "meat":1}})
	persist_requested = field_save.requested(OS.get_cmdline_user_args())
	if persist_requested:
		if not field_save.configure(OS.get_cmdline_user_args()):
			persist_blocked = true
			persist_error = "Disposable field profile rejected."
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
	add_child(carry)
	carry.setup(inventory, actor, FieldArt.make)
	for kind: String in Inventory.KINDS:
		carry.define_storage(kind,field_env.stock_anchors[kind])
	carry.set_storage_layout(field_env.landing_position)
	carry.define_receiver(HEARTH_OFFER, field_env.buy_anchor)
	carry.define_receiver(UPGRADE_OFFER, field_env.upgrade_anchor)
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
	_configure_stem(resource_tree)
	trees.append(resource_tree)
	for pos in [Vector2(-5.0,9.3),Vector2(-8.6,8.5),Vector2(-8.4,12),Vector2(-5.4,13.5),Vector2(-11.3,6.3),Vector2(-10.8,10.4),Vector2(-8.9,15),Vector2(-12.5,13.1)]:
		_add_pine(pos)
	for pos in [Vector2(5.0,9),Vector2(8.8,11.8),Vector2(10.7,8.2),Vector2(11.8,13.9)]:
		var wolf := FieldEnemy.new()
		wolf.name = "RidgeWolf%d" % (enemies.size()+1)
		wolf.position = Vector3(pos.x,0,pos.y)
		add_child(wolf)
		wolf.configure(actor)
		wolf.player_hit.connect(_player_hit)
		wolf.defeated.connect(_wolf_defeated.bind(wolf))
		enemies.append(wolf)
		if wolf.contact_mesh():
			register_hostile(wolf,wolf.contact_mesh())
	enemy = enemies.front()
	field_ready = true
	original_auto_quit = get_tree().auto_accept_quit
	get_tree().auto_accept_quit = false
	get_window().close_requested.connect(_close_field)
	forest.install.call_deferred(self)
	_apply_hearth(inventory.complete(HEARTH_OFFER),false)
	character_kit.set_upgraded(inventory.complete(UPGRADE_OFFER))
	_refresh_field()

func _close_field() -> void:
	if closing: return
	closing = true
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

func _add_pine(at: Vector2, variant := 0) -> ResourceTreeScript:
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
	return tree

func retire_tree(tree: ResourceTreeScript, animate: bool) -> void:
	trees.erase(tree)
	surfaces.erase(tree)
	if animate and tree.visible and tree._pivot.visible:
		var thaw := tree.create_tween().set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_IN)
		thaw.tween_property(tree,"scale",Vector3.ONE*.015,.31)
		thaw.tween_callback(tree.queue_free)
	else:
		tree.queue_free()

func _configure_stem(tree: ResourceTreeScript) -> void:
	tree.regrows = true
	tree.fall_away = true
	for marker in tree._marks:
		marker.queue_free()
	tree._marks.clear()

func _input(event: InputEvent) -> void:
	if event is InputEventKey and event.physical_keycode == KEY_U:
		return
	super(event)

func reachable(body: Node3D) -> bool:
	if body in trees:
		return body.can_address(actor.global_position, body.global_position-actor.global_position)
	return super(body)

func selected_tool() -> String:
	# Inside a mixed grove, a trunk near the player's boots cannot intercept
	# the cutting head at the edge of the orbit. Give a reachable stone on
	# that sweep priority until depleted; contact still uses its real mesh.
	if reachable(resource_rock):
		var offset := resource_rock.global_position - actor.global_position
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
	var landed := false
	if body in trees and body != resource_tree:
		tree_input_sequence += 1
		landed = body.strike(ResourceTreeScript.TREE_ID,tree_input_sequence,actor.global_position,body.global_position-actor.global_position)
	else:
		landed = super(body)
	if not landed:
		return false
	if body in trees:
		_event("impact_wood",body.global_position)
	elif body == resource_rock:
		_event("impact_stone",body.global_position)
		if resource_rock.phase == "mined":
			_event("deplete_stone",body.global_position)
			_make_drops("stone",body.global_position,3)
			rock_recovery = 13.0
	else:
		_event("player_attack",body.global_position)
		_event("hit",body.global_position)
	return true

func step_tree(dt: float) -> void:
	tree_button.hide()
	if persist_blocked or not field_ready: return
	for tree in trees:
		tree.set_meta("orbit_reach",SURFACE_REACH * character_kit.reach_scale)
		var previous_phase: String = tree.phase
		tree.advance(dt,actor.position,float(layout.actor_radius))
		if previous_phase == "credited" and tree.phase == "rooted":
			_event("regrow_wood",tree.global_position)
		if tree.phase == "ready_to_credit":
			_event("deplete_wood", tree.global_position)
			_make_drops("wood",tree.global_position,3)
			tree.mark_credited()

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
		var item := FieldArt.make(kind)
		if not item: continue
		add_child(item)
		var angle := float(i) * TAU / amount + 0.7
		var end := origin + Vector3(cos(angle),0,sin(angle))*(.48+.15*float(i%2))
		item.position = origin+Vector3.UP*.29
		item.rotation.y = angle*.75
		drops[token] = {"mesh":item,"kind":kind,"at":end,"from":item.position,"age":0.0}
	_event("drop_"+kind,origin)

func _step_drops(dt: float) -> void:
	for token: String in drops.keys():
		var drop: Dictionary = drops[token]
		drop.age += dt
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
	_make_drops("meat",at,2)
	respawns[wolf] = 27.0

func _player_hit(amount: int) -> void:
	if player_invulnerability > 0.0 or reset_time > 0 or persist_blocked: return
	player_hp = maxi(0,player_hp-amount)
	hurt_time = .32
	player_invulnerability = 1.0
	flash.color.a = .26
	_event("player_hurt",actor.position)
	if player_hp == 0:
		_event("player_fall",actor.position)
		reset_time = 1.05
		character_kit.rest()
	_refresh_field()

func _wolf_sweep(_from: Vector3, to: Vector3) -> bool:
	var r: Array = layout.camp_rect_xz
	return not camp_active or to.x < r[0]-.4 or to.x > r[2]+.4 or to.z < r[1]-.4 or to.z > r[3]+.4

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
		hero_model.rotation.z = -.88*smoothstep(0.0,.42,1.05-reset_time)
		reset_time = maxf(0.0,reset_time-dt)
		actor.velocity = Vector3.ZERO
		clear_touch()
		if reset_time <= 0:
			actor.position = point(layout.start_xz)
			hero_model.rotation.z = 0.0
			camera.position = actor.position + Vector3(7,11,11)
			player_hp = MAX_HP
			player_invulnerability = 2.0
			for wolf in enemies:
				if wolf.hp > 0: wolf.reset_encounter()
			_event("reset",actor.position)
			_refresh_field()
		return
	var previous_tool: String = character_kit.equipped
	super(dt)
	if persist_blocked: return
	if not previous_tool.is_empty() and previous_tool != character_kit.equipped and character_kit.equipped in ["axe","pickaxe"]:
		_event("equip_"+character_kit.equipped,actor.position)
	hurt_time = maxf(0.0,hurt_time-dt)
	hero_model.rotation.z = .14*sin(PI*hurt_time/.32)
	sound.set_listener_position(actor.position)
	if character_kit.turn_id != last_turn and not first_physics:
		_event("swing",actor.position)
	first_physics = false
	var inside := camp_active and absf(actor.position.x)<5.0 and absf(actor.position.z)<4.0
	_step_foot_audio(inside)
	player_invulnerability = maxf(0.0,player_invulnerability-dt)
	flash.color.a = maxf(0.0,flash.color.a-dt*.6)
	if rock_recovery > 0:
		rock_recovery = maxf(0.0,rock_recovery-dt)
		if rock_recovery <= 0:
			resource_rock.phase = "seated"
			resource_rock.strikes = 0
			resource_rock._mesh.scale = Vector3.ONE
			resource_rock._mesh.position.y = -resource_rock._mesh.mesh.get_aabb().position.y
			resource_rock._mesh.show()
			_event("regrow_stone",resource_rock.position)
	var danger := false
	for wolf in enemies:
		if respawns.has(wolf):
			respawns[wolf] -= dt
			if respawns[wolf] <= 0.0 and actor.position.distance_to(wolf.home)>6.0:
				respawns.erase(wolf)
				wolf.reset_encounter()
				_event("wolf_return",wolf.position)
		var before := wolf.state
		wolf.advance(dt,_wolf_sweep)
		if before != wolf.state:
			if wolf.state == "stalk" and before in ["guard","return"]:
				_event("approach",wolf.position)
			elif wolf.state == "windup":
				_event("wolf_brace",wolf.position)
			elif wolf.state == "lunge":
				_event("enemy_attack",wolf.position)
		danger = danger or wolf.state in ["stalk","windup","lunge","recover","stagger"]
	_step_drops(dt)
	if reveal_countdown >= 0:
		reveal_countdown -= dt
		if reveal_countdown <= 0:
			reveal_countdown = -1.0
			_apply_hearth(true,true)
			_event("reveal", Vector3.ZERO)
	if camp_active:
		for kind: String in Inventory.KINDS:
			var anchor: Node3D = field_env.stock_anchors[kind]
			if actor.position.distance_to(anchor.global_position)<PAD_RADIUS:
				carry.deposit_storage(kind)
		if actor.position.distance_to(field_env.upgrade_anchor.global_position)<PAD_RADIUS:
			carry.contribute(UPGRADE_OFFER)
	elif actor.position.distance_to(field_env.buy_anchor.global_position)<PAD_RADIUS:
		carry.contribute(HEARTH_OFFER)
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
			_event("deposit_"+kind,field_env.stock_anchors[kind].global_position)
		_:
			_event("spend_"+kind,carry.receivers[dest].global_position)

func _inventory_changed() -> void:
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
	elif id == UPGRADE_OFFER:
		character_kit.set_upgraded(true)
		_upgrade_sparks()
		_event("victory",actor.position)
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
	for gate in gates: gate.set_earned(built)
	camp_built.visible = built
	field_env.set_built(built,animate)

func _refresh_field() -> void:
	field_env.sync_stock(inventory.stored)
	field_env.set_payment(inventory.remaining(HEARTH_OFFER))
	field_env.set_upgrade_payment(inventory.remaining(UPGRADE_OFFER))
	for offer in [HEARTH_OFFER,UPGRADE_OFFER]:
		var total := 0
		var paid := 0
		for kind in inventory.costs[offer]:
			total += int(inventory.costs[offer][kind])
			paid += int(inventory.paid[offer][kind])
		field_env.set_payment_progress(float(paid)/maxi(total,1),"buy" if offer == HEARTH_OFFER else "upgrade")
	last_notice = ""
	_refresh_hud_field(current_music == "threat")

func _refresh_hud_field(danger: bool) -> void:
	var hint: String
	if persist_blocked: hint = persist_error
	elif danger: hint = "Wolf nearby  ·  Health %d/%d" % [player_hp,MAX_HP]
	elif not inventory.complete(HEARTH_OFFER):
		hint = "Fell pines and carry wood to the hearth."
		if actor.position.distance_to(field_env.buy_anchor.position)<1.6:
			hint = "Build hearth  ·  %d wood remaining" % inventory.remaining(HEARTH_OFFER).wood
	elif not inventory.complete(UPGRADE_OFFER):
		hint = "Bring stone and meat to the axe plot."
	else:
		hint = "Three axes equipped"
	if camp_active and not danger and not persist_blocked:
		for kind: String in Inventory.KINDS:
			var store: Node3D = field_env.stock_anchors[kind]
			if actor.position.distance_squared_to(store.global_position)<1.7:
				hint = "%s storage  ·  %d" % [kind.capitalize(),inventory.stored[kind]]
		if not inventory.complete(UPGRADE_OFFER) and actor.position.distance_squared_to(field_env.upgrade_anchor.global_position)<2.0:
			var remaining := inventory.remaining(UPGRADE_OFFER)
			hint = "Upgrade  ·  %d stone, %d meat remaining" % [remaining.stone,remaining.meat]
	var tally := "Wood %d   Stone %d   Meat %d" % [inventory.carried.wood,inventory.carried.stone,inventory.carried.meat]
	if tally+hint == last_notice: return
	last_notice = tally+hint
	opening_hud.field_status(inventory.carried,hint)
