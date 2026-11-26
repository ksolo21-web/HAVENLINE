extends Node3D
## A successful axe contact drives one recoil, chip burst and notch.
const TREE_ID := "wood-a"
const TREE_SCALE := 0.69
const FALL_DIR := Vector3(-0.953582665, 0, -0.301131367)
const FALL_MAX := 1.41
const MIN_REACH := 0.52
const MAX_REACH := 1.65
const MIN_FACING_DOT := 0.80
const CONTACT_COOLDOWN := 0.32
const FALL_SECONDS := 0.72
const SETTLE_SECONDS := 0.12
const REGROW_SECONDS := 5.0
const RECOIL_SECONDS := .30
const RETURN_SECONDS := .45
var recoil_elapsed := RECOIL_SECONDS
var recoil_direction := Vector3.FORWARD
var burst_elapsed := .56
var chips: Array[MeshInstance3D] = []
var chip_origins: Array[Vector3] = []
var chip_velocities: Array[Vector3] = []
static var splinter: Mesh
static var powder: Mesh
var phase := "rooted"
var strikes := 0
var last_sequence := 0
var cooldown := 0.0
var falling_clock := 0.0
var settle_clock := 0.0
var fall_direction := FALL_DIR
var fall_away := false
var blocked := false
var regrows := false
var starter_credit_seen := false
var _regrow_remaining := 0.0
var _pivot: Node3D
var _marks: Array[Node3D] = []

func build(source_mesh: PackedScene, allow_regrowth := false) -> void:
	regrows = allow_regrowth
	_pivot = Node3D.new()
	add_child(_pivot)
	var tree := source_mesh.instantiate() as Node3D
	_pivot.add_child(tree)
	tree.scale = Vector3.ONE * TREE_SCALE
	for i in range(2):
		var mark := MeshInstance3D.new()
		var chip := BoxMesh.new()
		chip.size = Vector3(0.035, 0.045, 0.15 - .025 * float(i))
		mark.mesh = chip
		mark.position = Vector3(.132, .56 - .12 * float(i), .02)
		var color := StandardMaterial3D.new()
		color.albedo_color = Color("#594131")
		mark.material_override = color
		_pivot.add_child(mark)
		mark.hide()
		_marks.append(mark)

func can_address(feet: Vector3, facing: Vector3) -> bool:
	if phase != "rooted":
		return false
	var to_target := global_position - feet
	to_target.y = 0.0
	var planar := Vector3(facing.x, 0, facing.z)
	var dist := to_target.length()
	return dist >= MIN_REACH and dist <= float(get_meta("orbit_reach", MAX_REACH)) and planar.normalized().dot(to_target.normalized()) >= MIN_FACING_DOT

func strike(source: String, sequence: int, feet: Vector3, facing: Vector3, travel := Vector3.ZERO, hit_at := Vector3.INF) -> bool:
	if source != TREE_ID or sequence <= last_sequence:
		return false
	last_sequence = sequence
	if cooldown > 0.0 or not can_address(feet, facing):
		return false
	cooldown = CONTACT_COOLDOWN
	strikes += 1
	recoil_direction = travel if Vector2(travel.x,travel.z).length_squared()>.000001 else global_position-feet
	recoil_direction.y = 0.
	recoil_direction = recoil_direction.normalized()
	recoil_elapsed = 0.
	_emit_chips(hit_at)
	if strikes <= _marks.size():
		_marks[strikes - 1].show()
	if strikes == 3:
		if fall_away:
			var away := global_position - feet
			away.y = 0.0
			if away.length_squared() > .0001: fall_direction = away.normalized()
		phase = "falling"
	return true

func sweep_clear(feet: Vector3, capsule_radius: float) -> bool:
	var offset := feet - global_position
	var along := offset.dot(fall_direction)
	var across := offset.dot(Vector3(-fall_direction.z, 0, fall_direction.x))
	# Entire measured footprint: freezes proactively before any step. No push.
	var heel := .18 if fall_away else 1.0
	return along < -(heel + capsule_radius) or along > 2.4 + capsule_radius or absf(across) > 1.25 + capsule_radius

func advance(dt: float, feet: Vector3, capsule_radius: float) -> void:
	var step := clampf(dt, 0.0, .04)
	cooldown = maxf(cooldown - step, 0.0)
	blocked = false
	if burst_elapsed < .56:
		_step_chips(step)
	if phase == "rooted" and recoil_elapsed < RECOIL_SECONDS:
		recoil_elapsed = minf(RECOIL_SECONDS,recoil_elapsed+step)
		var t := recoil_elapsed/RECOIL_SECONDS
		var lean := sin(t*TAU*1.23)*pow(1.-t,1.7)*(.15+.025*strikes)
		var local := global_basis.inverse()*recoil_direction
		_pivot.basis = Basis(Vector3.UP.cross(local).normalized(),lean)
	if regrows and phase == "credited":
		_regrow_remaining = maxf(_regrow_remaining - maxf(dt, 0.0), 0.0)
		show_return(_regrow_remaining)
		if is_zero_approx(_regrow_remaining):
			_regrow()
		return
	if phase != "falling":
		return
	if not sweep_clear(feet, capsule_radius):
		blocked = true
		return
	# Do not count the first terminal-pose step as stationary time.
	var was_terminal := falling_clock >= FALL_SECONDS
	falling_clock = minf(falling_clock + step, FALL_SECONDS)
	var f := falling_clock / FALL_SECONDS
	_pose(FALL_MAX * f * f)
	if was_terminal:
		settle_clock += step
		if settle_clock >= SETTLE_SECONDS:
			phase = "ready_to_credit"

func mark_credited() -> void:
	if phase == "ready_to_credit":
		_finish_fall()

func restore_collected() -> void:
	# Existing paid ledger remains the only durable authority; no regrant on reload.
	strikes = 3
	for mark in _marks:
		mark.show()
	_pose(FALL_MAX)
	_finish_fall()

func _finish_fall() -> void:
	starter_credit_seen = true
	phase = "credited"
	if regrows:
		_pivot.hide()
		_regrow_remaining = REGROW_SECONDS

func restore_notches(count: int) -> void:
	strikes = count
	for i in _marks.size(): _marks[i].visible = i < count

func show_return(remaining: float) -> void:
	if remaining > RETURN_SECONDS:
		_pivot.hide()
		return
	var f := 1.-clampf(remaining/RETURN_SECONDS,0.,1.)
	var radius := lerpf(.08,1.,smoothstep(.05,.94,f))
	var height := lerpf(.03,1.,smoothstep(0.,1.,f))
	_pivot.basis = Basis.IDENTITY.scaled(Vector3(radius,height,radius))
	_pivot.show()
	for mark in _marks: mark.hide()

func _regrow() -> void:
	strikes = 0
	recoil_elapsed = RECOIL_SECONDS
	cooldown = 0.0
	falling_clock = 0.0
	settle_clock = 0.0
	for mark in _marks:
		mark.hide()
	_pose(0.0)
	_pivot.show()
	phase = "rooted"

func _pose(radians: float) -> void:
	var local_direction := global_basis.inverse()*fall_direction if is_inside_tree() else fall_direction
	_pivot.basis = Basis(Vector3.UP.cross(local_direction).normalized(), radians)

func _emit_chips(hit_at: Vector3) -> void:
	if not splinter:
		var sliver := PrismMesh.new()
		sliver.size = Vector3(.055,.078,.032)
		var wood := StandardMaterial3D.new()
		wood.albedo_color = Color("d79b58")
		wood.roughness = .92
		sliver.material = wood
		splinter = sliver
		var flake := SphereMesh.new()
		flake.radius = .042
		flake.height = .058
		flake.radial_segments = 8
		flake.rings = 3
		var white := StandardMaterial3D.new()
		white.albedo_color = Color("e1f1ff")
		white.roughness = .96
		flake.material = white
		powder = flake
	var incoming := (global_basis.inverse()*recoil_direction).normalized()
	var side := Vector3.UP.cross(incoming)
	if chips.is_empty():
		for i in 7:
			var chip := MeshInstance3D.new()
			chip.mesh = splinter if i < 3 else powder
			chip.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			add_child(chip)
			chips.append(chip)
			chip_origins.append(Vector3.ZERO)
			chip_velocities.append(Vector3.ZERO)
	for i in chips.size():
		var spread := sin(float(i)*2.4+strikes*.8)
		var eject := -incoming*(.9+.28*cos(i+strikes))+side*spread
		if i < 3:
			chip_origins[i] = to_local(hit_at) if hit_at.is_finite() else -incoming*.14 + Vector3.UP*(.51+.055*i)
			chip_velocities[i] = eject*.89+Vector3.UP*(.93+.18*i)
		else:
			chip_origins[i] = side*spread*.40+Vector3.UP*(1.22+.15*(i-3))
			chip_velocities[i] = eject*.61+Vector3.UP*(.18+.10*(i-3))
		chips[i].show()
	burst_elapsed = 0.
	_step_chips(0.)

func _step_chips(dt: float) -> void:
	burst_elapsed = minf(.56,burst_elapsed+dt)
	var t := burst_elapsed
	for i in chips.size():
		var chip := chips[i]
		if t >= .56:
			chip.hide()
		else:
			chip.position = chip_origins[i]+chip_velocities[i]*t+Vector3.DOWN*(2.7*t*t)
			chip.rotation = Vector3(i*.91+t*8.,i*.7+t*3.,i*.56-t*5.)
			chip.scale = Vector3.ONE*(1.-smoothstep(.34,.56,t))
