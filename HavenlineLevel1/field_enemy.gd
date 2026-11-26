extends Node3D

signal player_hit(damage: int)
signal defeated(at: Vector3)
const Art = preload("res://field_art.gd")
const MAX_HEALTH := 3
const WALK_SPEED := 1.18
const NOTICE_RADIUS := 5.3
const LEASH := 4.2
const BITE_RANGE := 1.52
const STALK_STOP := 1.66
const CONTACT_DISTANCE := 1.35
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
var flank_sign := 0.0
var configured := false
var active := true
var _tint: StandardMaterial3D

func _init() -> void:
	add_to_group("swirl_hostiles")

func _ready() -> void:
	_setup_visual()

func _setup_visual() -> void:
	if visual: return
	visual = Art.make("wolf")
	if not visual: return
	add_child(visual)
	body = AnimatableBody3D.new()
	body.name = "WolfTorso"
	body.sync_to_physics = false
	body.collision_layer = 1
	body.collision_mask = 0
	add_child(body)
	var torso := CapsuleShape3D.new()
	torso.radius = .39
	torso.height = 1.68
	var shape := CollisionShape3D.new()
	shape.shape = torso
	shape.position = Vector3(0,.76,.04)
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
		for clip in ["Walk", "Idle"]:
			if animator.has_animation(clip):
				animator.get_animation(clip).loop_mode = Animation.LOOP_LINEAR
	if surface: hit_surface = surface.mesh.generate_triangle_mesh()
	health_bar = Sprite3D.new()
	health_bar.name = "WolfHealth"
	health_bar.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	health_bar.shaded = false
	health_bar.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	health_bar.pixel_size = .0095
	health_bar.position.y = 1.78
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
		pixels.fill_rect(Rect2i(2,2,roundi(68.0 * hp / MAX_HEALTH),4),Color("#58de6c"))
	health_bar.texture = ImageTexture.create_from_image(pixels)
	health_bar.visible = hp > 0

func contact_segment(a: Vector3, b: Vector3, _radius: float = 0.0) -> bool:
	if not can_receive_swirl() or not hit_surface: return false
	return not hit_surface.intersect_segment(surface.to_local(a), surface.to_local(b)).is_empty()

func _play(clip: String) -> void:
	if animator and animator.has_animation(clip) and animator.current_animation != clip:
		animator.play(clip,.10)

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
	hp = maxi(0, hp - amount)
	_refresh_health()
	hurt_timer = .16
	if surface: surface.material_overlay = _tint
	if hp == 0:
		state = "defeated"
		if body: body.collision_layer = 0
		timer = .34
		_play("Fall")
		defeated.emit(global_position)
	else:
		state = "stagger"
		timer = .24
		if impact != Vector3.ZERO:
			_face(impact - global_position,.10)
		_play("Hurt")
	return true

func _face(direction: Vector3, dt: float) -> void:
	if direction.length_squared() > .00001:
		rotation.y = rotate_toward(rotation.y, atan2(direction.x,direction.z), 7.4 * dt)

func _move(direction: Vector3, distance: float, sweep: Callable) -> void:
	var next := global_position + direction * distance
	next.y = home.y
	if not sweep.is_valid() or sweep.call(global_position,next):
		global_position = next

func advance(delta: float, sweep_allowed: Callable = Callable()) -> void:
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
	var space := global_position - target.global_position
	space.y = 0.0
	var clearance := CONTACT_DISTANCE if state == "lunge" else STALK_STOP
	if space.length() < clearance:
		var away := space.normalized() if space.length_squared() > .0025 else -global_basis.z
		_move(away, minf(clearance-space.length(), 5.8*dt), sweep_allowed)
	for other in get_tree().get_nodes_in_group("swirl_hostiles"):
		if other == self or not other.can_receive_swirl(): continue
		var separation: Vector3 = global_position-other.global_position
		separation.y = 0.0
		var gap := separation.length()
		if gap > .01 and gap < .90:
			_move(separation/gap,minf((.90-gap)*.5,dt*2.2),sweep_allowed)
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
		"stagger", "recover":
			if timer <= 0.0: state = "guard"
		"windup":
			_face(toward,dt)
			attack_direction = toward
			if timer <= 0.0:
				state = "lunge"
				timer = .15
				_play("Bite")
		"lunge":
			_move(attack_direction, minf(2.1*dt,maxf(0.0,distance-CONTACT_DISTANCE)),sweep_allowed)
			if timer <= 0.0:
				var remaining := target.global_position-global_position
				remaining.y = 0.0
				if remaining.length() <= BITE_RANGE and (remaining.length_squared() < .01 or remaining.normalized().dot(attack_direction) > .55):
					player_hit.emit(1)
				state = "recover"
				timer = 1.08
				_play("Idle")
		_:
			var to_home := home-global_position
			to_home.y = 0.0
			if distance <= NOTICE_RADIUS and target.global_position.distance_to(home) <= LEASH+.55:
				_face(toward,dt)
				if distance <= STALK_STOP+.025:
					state = "windup"
					timer = .38
					attack_direction = toward
					_play("Brace")
				else:
					state = "stalk"
					_move(toward, minf(WALK_SPEED*dt,distance-STALK_STOP),sweep_allowed)
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
	hp = MAX_HEALTH
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
