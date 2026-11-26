extends Node3D

signal player_hit(damage: int)
signal damaged(amount: int)
signal defeated(at: Vector3)
const Art = preload("res://field_art.gd")
const MAX_HEALTH := 3
const BOSS_HEALTH := 8
const BITE_DAMAGE := 2
const BOSS_BITE_DAMAGE := 4
var is_boss := false
var spawn_id := 0

func size_factor() -> float:
	return 1.58 if is_boss else 1.0

func sanctuary_margin() -> float:
	return 1.25 * size_factor()

func max_hp() -> int:
	return BOSS_HEALTH if is_boss else MAX_HEALTH

const WALK_SPEED := 1.35
const CHASE_SPEED := 2.65
const NOTICE_RADIUS := 14.0
const LEASH := 20.0
const STRIKE_START := 2.14
const BITE_RANGE := 1.52
const STALK_STOP := 1.66
const CONTACT_DISTANCE := 1.35
# The authored Bite closes the mouth at 0.170 s in its 0.260 s clip.
const BITE_DURATION := .26
const JAW_CONTACT := .17
const ALPHA_BITE_DURATION := .32

func _brace_duration() -> float:
	return .45 if is_boss else .30

func _bite_duration() -> float:
	return ALPHA_BITE_DURATION if is_boss else BITE_DURATION

func _recovery_duration() -> float:
	return .91 if is_boss else .76
var hp := MAX_HEALTH
var state := "guard"
var last_turn := -1
var timer := 0.0
var hurt_timer := 0.0
var body: AnimatableBody3D
var health_bar: Sprite3D
var hit_surface: TriangleMesh
var target: Node3D
var visual: Node3D
var surface: MeshInstance3D
var animator: AnimationPlayer
var home: Vector3
var attack_direction := Vector3.FORWARD
var bite_landed := false
var flank_sign := 0.0
var configured := false
var active := true
static var _surface_cache: Dictionary = {}
var _tint: StandardMaterial3D

func _init() -> void:
	add_to_group("swirl_hostiles")

func _ready() -> void:
	_setup_visual()

func _setup_visual() -> void:
	if visual: return
	hp = max_hp()
	visual = Art.make("wolf",2.4 * size_factor())
	if not visual: return
	add_child(visual)
	body = AnimatableBody3D.new()
	body.name = "WolfTorso"
	body.sync_to_physics = false
	body.collision_layer = 1
	body.collision_mask = 0
	add_child(body)
	var torso := CapsuleShape3D.new()
	torso.radius = .39 * size_factor()
	torso.height = 1.68 * size_factor()
	var shape := CollisionShape3D.new()
	shape.shape = torso
	shape.position = Vector3(0,.76,.04) * size_factor()
	shape.rotation.x = PI*.5
	body.add_child(shape)
	var meshes := visual.find_children("*", "MeshInstance3D", true, false)
	var max_volume := -1.0
	for entry in meshes:
		var part := entry as MeshInstance3D
		if part.mesh:
			var volume := part.get_aabb().get_volume()
			if volume > max_volume:
				surface = part
				max_volume = volume
	var players := visual.find_children("*", "AnimationPlayer", true, false)
	if not players.is_empty():
		animator = players[0] as AnimationPlayer
		# Missing tracks return to rest when an attack gives way to idle or hurt.
		animator.deterministic = true
		for clip in ["Walk", "Idle"]:
			if animator.has_animation(clip):
				animator.get_animation(clip).loop_mode = Animation.LOOP_LINEAR
	if surface:
		if not _surface_cache.has(surface.mesh): _surface_cache[surface.mesh]=surface.mesh.generate_triangle_mesh()
		hit_surface=_surface_cache[surface.mesh]
	health_bar = Sprite3D.new()
	health_bar.name = "WolfHealth"
	health_bar.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	health_bar.shaded = false
	health_bar.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	health_bar.pixel_size = .0095
	health_bar.position.y = 1.78 * size_factor()
	health_bar.pixel_size *= 1.32 if is_boss else 1.0
	add_child(health_bar)
	_refresh_health()
	_tint = StandardMaterial3D.new()
	_tint.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	_tint.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	_tint.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	_tint.albedo_color = Color(1.0,.36,.18,.36)
	_play("Idle")

func _refresh_health() -> void:
	if not health_bar: return
	var pixels := Image.create_empty(72, 8, false, Image.FORMAT_RGBA8)
	pixels.fill(Color("#17222b"))
	pixels.fill_rect(Rect2i(2,2,68,4),Color("#25333b"))
	if hp > 0:
		pixels.fill_rect(Rect2i(2,2,roundi(68.0 * hp / max_hp()),4),Color("#ffb953") if is_boss else Color("#58de6c"))
	health_bar.texture = ImageTexture.create_from_image(pixels)
	health_bar.visible = hp > 0

func contact_segment(a: Vector3, b: Vector3, _radius: float = 0.0) -> bool:
	if not can_receive_swirl() or not hit_surface: return false
	return not hit_surface.intersect_segment(surface.to_local(a), surface.to_local(b)).is_empty()

func _play(clip: String) -> void:
	if animator and animator.has_animation(clip):
		animator.speed_scale = CHASE_SPEED / WALK_SPEED if clip == "Walk" and state == "stalk" else 1.0
		if animator.current_animation != clip:
			animator.play(clip,.10)

# Drive the authored attack pose from the same physics clock as contact. A slow
# render frame can skip over closed jaws without delaying or repeating damage.
func _attack_pose(clip: String, elapsed_fraction: float) -> void:
	if not animator or not animator.has_animation(clip): return
	if animator.current_animation != clip:
		animator.play(clip, 0.0)
	animator.speed_scale = 0.0
	animator.seek(animator.get_animation(clip).length * clampf(elapsed_fraction, 0.0, 1.0), true)

func configure(player: Node3D) -> void:
	target = player
	home = global_position
	configured = true
	_setup_visual()

func contact_mesh() -> MeshInstance3D:
	return surface

func can_receive_swirl() -> bool:
	return active and configured and hp > 0 and is_visible_in_tree() and is_instance_valid(surface)

func take_swirl_hit(turn: int) -> bool:
	if turn <= last_turn or not can_receive_swirl(): return false
	last_turn = turn
	return receive_hit()

func receive_hit(amount: int = 1, impact: Vector3 = Vector3.ZERO) -> bool:
	if amount <= 0 or not can_receive_swirl(): return false
	var loss := mini(hp,amount)
	hp -= loss
	damaged.emit(loss)
	_refresh_health()
	hurt_timer = .16
	if surface: surface.material_overlay = _tint
	if hp == 0:
		state = "defeated"
		if body: body.collision_layer = 0
		timer = .72
		_play("Fall")
		defeated.emit(global_position)
	elif state not in ["windup","lunge"]:
		state = "stagger"
		timer = .18
		if impact != Vector3.ZERO:
			_face(impact - global_position,.10)
		_play("Hurt")
	return true

func _face(direction: Vector3, dt: float) -> void:
	if direction.length_squared() > .00001:
		rotation.y = rotate_toward(rotation.y, atan2(direction.x,direction.z), 7.4 * dt)

func _move(direction: Vector3, distance: float, sweep: Callable) -> bool:
	var next := global_position + direction * distance
	next.y = home.y
	if not sweep.is_valid() or sweep.call(global_position,next):
		global_position = next
		return true
	return false

func _pursue(toward: Vector3, step: float, sweep: Callable) -> void:
	if _move(toward,step,sweep): return
	# A blocked wolf skirts its packmate or sanctuary rather than running in place.
	var side := 1.0 if spawn_id % 2 == 0 else -1.0
	for angle: float in [.76,-.76,1.48,-1.48]:
		if _move(toward.rotated(Vector3.UP,angle*side),step,sweep): return

func advance(delta: float, sweep_allowed: Callable = Callable(), player_exposed := true) -> void:
	if not configured or not active or not is_instance_valid(target): return
	var dt := clampf(delta,0.0,.08)
	hurt_timer = maxf(0.0, hurt_timer - dt)
	if hurt_timer <= 0.0 and surface and surface.material_overlay: surface.material_overlay = null
	timer = maxf(0.0, timer - dt)
	if state == "defeated":
		if visual: visual.rotation.z = lerp_angle(visual.rotation.z, .94, minf(dt*13,1.0))
		if timer <= 0.0: hide()
		return
	# Give the player a visible shoulder and preserve space for the pack as it closes.
	if not player_exposed and state in ["windup","lunge","stalk"]:
		state="return"
		timer=0.0
	var reach_bonus := .54 if is_boss else 0.0
	var space := global_position - target.global_position
	space.y = 0.0
	var clearance := (CONTACT_DISTANCE if state == "lunge" else STALK_STOP) + reach_bonus
	if space.length() < clearance:
		var away := space.normalized() if space.length_squared() > .0025 else -global_basis.z
		_move(away, minf(clearance-space.length(), 5.8*dt), sweep_allowed)
	for other in get_tree().get_nodes_in_group("swirl_hostiles"):
		if other == self or not other.can_receive_swirl(): continue
		var separation: Vector3 = global_position-other.global_position
		separation.y = 0.0
		var gap := separation.length()
		var neighbor_gap: float = sanctuary_margin()+other.sanctuary_margin()
		if gap > .01 and gap < neighbor_gap:
			_move(separation/gap,minf((neighbor_gap-gap)*.5,dt*2.2),sweep_allowed)
	# A wolf closing straight down the camera's sightline circles to a shoulder.
	# Keep that side through the telegraph so the bite has a readable silhouette.
	var sight := get_viewport().get_camera_3d()
	if sight and state in ["guard", "stalk", "windup", "stagger"] and space.length() < 2.50:
		var right := sight.global_basis.x
		right.y = 0.0
		right = right.normalized()
		var lateral := space.dot(right)
		if absf(flank_sign) < .1:
			flank_sign = signf(lateral) if absf(lateral) > .06 else (1.0 if get_index()%2==0 else -1.0)
		if lateral*flank_sign < .85:
			_move(right*flank_sign,minf(2.2*dt,.85-lateral*flank_sign),sweep_allowed)
	elif space.length() > 3.0:
		flank_sign = 0.0
	var offset := target.global_position - global_position
	offset.y = 0.0
	var distance := offset.length()
	var toward := offset.normalized()
	match state:
		"stagger":
			if timer <= 0.0: state = "guard"
		"recover":
			_attack_pose("Recover", 1.0 - timer / _recovery_duration())
			if timer <= 0.0: state = "guard"
		"windup":
			_attack_pose("Brace", 1.0 - timer / _brace_duration())
			_face(toward,dt)
			attack_direction = toward
			if timer <= 0.0:
				state = "lunge"
				timer = _bite_duration()
				bite_landed = false
				_attack_pose("Bite", 0.0)
		"lunge":
			var duration := _bite_duration()
			var elapsed := duration - timer
			_attack_pose("Bite", elapsed / duration)
			_move(attack_direction, minf(4.6*dt,maxf(0.0,distance-CONTACT_DISTANCE-reach_bonus)),sweep_allowed)
			var remaining := target.global_position-global_position
			remaining.y = 0.0
			var contact_at := duration * JAW_CONTACT / BITE_DURATION
			var crosses_contact := elapsed >= contact_at and elapsed - dt < contact_at
			if crosses_contact and not bite_landed and player_exposed and remaining.length() <= BITE_RANGE+reach_bonus and (remaining.length_squared() < .01 or remaining.normalized().dot(attack_direction) > .55):
				bite_landed = true
				player_hit.emit(BOSS_BITE_DAMAGE if is_boss else BITE_DAMAGE)
			if timer <= 0.0:
				state = "recover"
				timer = _recovery_duration()
				_attack_pose("Recover", 0.0)
		_:
			var to_home := home-global_position
			to_home.y = 0.0
			if player_exposed and distance <= NOTICE_RADIUS and target.global_position.distance_to(home) <= LEASH+.55:
				_face(toward,dt)
				if distance <= STRIKE_START+reach_bonus+.025:
					state = "windup"
					timer = _brace_duration()
					attack_direction = toward
					_attack_pose("Brace", 0.0)
				else:
					state = "stalk"
					_pursue(toward, minf(CHASE_SPEED*dt,distance-STRIKE_START-reach_bonus),sweep_allowed)
					_play("Walk")
			elif to_home.length() > .04:
				state = "return"
				_face(to_home,dt)
				_move(to_home.normalized(),minf(to_home.length(),dt*WALK_SPEED),sweep_allowed)
				_play("Walk")
			else:
				state = "guard"
				_play("Idle")

func reset_encounter() -> void:
	hp = max_hp()
	_refresh_health()
	state = "guard"
	last_turn = -1
	timer = 0.0
	hurt_timer = 0.0
	flank_sign = 0.0
	active = true
	if body: body.collision_layer = 1
	if configured: global_position = home
	if visual: visual.rotation.z = 0.0
	if surface: surface.material_overlay = null
	show()
	_play("Idle")
