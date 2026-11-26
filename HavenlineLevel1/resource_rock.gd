extends Node3D
## Stone node for the two-handed pickaxe. Stock stays off the wood ledger.
const BANK_SCALE := 1.156
const ROCK_ID := "stone-a"
const MIN_REACH := 0.52
const MAX_REACH := 1.65
const MIN_FACING_DOT := 0.80
const CONTACT_COOLDOWN := 0.32
var phase := "seated"
var strikes := 0
var last_sequence := 0
var cooldown := 0.0
var _mesh: MeshInstance3D

var bank_body: StaticBody3D

func attach_bank_body() -> void:
	bank_body = StaticBody3D.new()
	bank_body.name = "MineableBankBody"
	var collision := CollisionShape3D.new()
	collision.shape = _mesh.mesh.create_trimesh_shape()
	bank_body.add_child(collision)
	_mesh.add_child(bank_body)

func set_bank_active(available: bool) -> void:
	if bank_body:
		bank_body.collision_layer = 1 if available else 0

func build() -> void:
	_mesh = MeshInstance3D.new()
	var rock := SphereMesh.new()
	rock.radius = 0.34
	rock.height = 0.52
	rock.radial_segments = 18
	rock.rings = 10
	_mesh.mesh = rock
	_mesh.position = Vector3(0.0, 0.28, 0.0)
	var shade := StandardMaterial3D.new()
	shade.albedo_color = Color("#6e675f")
	shade.roughness = 0.92
	_mesh.material_override = shade
	add_child(_mesh)

func can_address(feet: Vector3, facing: Vector3) -> bool:
	if phase != "seated":
		return false
	var to_target := global_position - feet
	to_target.y = 0.0
	var planar := Vector3(facing.x, 0, facing.z)
	if to_target.length() < 0.001 or planar.length() < 0.001:
		return false
	var dist := to_target.length()
	return dist >= MIN_REACH and dist <= float(get_meta("orbit_reach", MAX_REACH)) and planar.normalized().dot(to_target.normalized()) >= MIN_FACING_DOT

func strike(source: String, sequence: int, feet: Vector3, facing: Vector3) -> bool:
	if source != ROCK_ID or sequence <= last_sequence:
		return false
	last_sequence = sequence
	if cooldown > 0.0 or not can_address(feet, facing):
		return false
	cooldown = CONTACT_COOLDOWN
	strikes += 1
	if _mesh:
		_mesh.scale = Vector3.ONE * (1.0 - 0.18 * float(strikes))
	if strikes >= 3:
		phase = "mined"
		if _mesh:
			_mesh.hide()
		set_bank_active(false)
	return true

func advance(dt: float) -> void:
	cooldown = maxf(cooldown - clampf(dt, 0.0, 0.04), 0.0)
