extends Node3D
## Technical single-tree mechanics. No axe rig or authored contact animation yet.
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
var phase := "rooted"
var strikes := 0
var last_sequence := 0
var cooldown := 0.0
var falling_clock := 0.0
var settle_clock := 0.0
var blocked := false
var _pivot: Node3D
var _marks: Array[Node3D] = []

func build(source_mesh: PackedScene) -> void:
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
	return dist >= MIN_REACH and dist <= MAX_REACH and planar.normalized().dot(to_target.normalized()) >= MIN_FACING_DOT

func strike(source: String, sequence: int, feet: Vector3, facing: Vector3) -> bool:
	if source != TREE_ID or sequence <= last_sequence:
		return false
	last_sequence = sequence
	if cooldown > 0.0 or not can_address(feet, facing):
		return false
	cooldown = CONTACT_COOLDOWN
	strikes += 1
	if strikes <= _marks.size():
		_marks[strikes - 1].show()
	if strikes == 3:
		phase = "falling"
	return true

func sweep_clear(feet: Vector3, capsule_radius: float) -> bool:
	var offset := feet - global_position
	var along := offset.dot(FALL_DIR)
	var across := offset.dot(Vector3(-FALL_DIR.z, 0, FALL_DIR.x))
	# Entire measured footprint: freezes proactively before any step. No push.
	return along < -(1.0 + capsule_radius) or along > 2.4 + capsule_radius or absf(across) > 1.25 + capsule_radius

func advance(dt: float, feet: Vector3, capsule_radius: float) -> void:
	var step := clampf(dt, 0.0, .04)
	cooldown = maxf(cooldown - step, 0.0)
	blocked = false
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
		phase = "credited"

func restore_collected() -> void:
	# Existing paid ledger remains the only durable authority; no regrant on reload.
	strikes = 3
	for mark in _marks:
		mark.show()
	_pose(FALL_MAX)
	phase = "credited"

func _pose(radians: float) -> void:
	_pivot.basis = Basis(Vector3.UP.cross(FALL_DIR).normalized(), radians)
