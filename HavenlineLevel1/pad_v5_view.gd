extends Node3D
## Scene-neutral presentation only. Does not listen to input, charge, grant or save.
enum Phase { UNAVAILABLE, AVAILABLE, PAYING, PENDING, ACCEPTED }
const INLAYS := ["PurchaseCorner_SW", "PurchaseCorner_SE", "PurchaseCorner_NE", "PurchaseCorner_NW"]
const EXPECTED_TRIANGLES := 84041
const ACTIVE := Color("#77eb52")
const CONFIRM_TINT := Color("#54af3b")
const PENDING_TINT_WEIGHT := 0.32
var installed := false
var _model: Node3D
var _paint: Array[BaseMaterial3D] = []
var _idle: Array[Color] = []
var _deck_paint: BaseMaterial3D
var _deck_idle: Color
var _action: Label3D
var _cost: Label3D
var _revision := -1

func _ready() -> void:
	hide()

## Producer verifies the source GLB pin when preparing the PackedScene.
## This binding also checks all six imported surfaces, including the four unique inlays.
func install(source: PackedScene) -> bool:
	if installed or source == null:
		return false
	var instance := source.instantiate()
	if not instance is Node3D:
		instance.free()
		return false
	var mesh_nodes: Array[Node] = instance.find_children("*", "MeshInstance3D", true, false)
	var tallies := {}
	var meshes := {}
	for item in mesh_nodes:
		var mesh_instance := item as MeshInstance3D
		var node_name := String(item.name)
		if meshes.has(node_name) or mesh_instance.mesh == null or mesh_instance.mesh.get_surface_count() != 1:
			instance.free()
			return false
		if not mesh_instance.mesh is ArrayMesh or (mesh_instance.mesh as ArrayMesh).surface_get_primitive_type(0) != Mesh.PRIMITIVE_TRIANGLES:
			instance.free()
			return false
		meshes[node_name] = mesh_instance
		var elements := mesh_instance.mesh.surface_get_arrays(0)
		var triangle_data: PackedInt32Array = elements[Mesh.ARRAY_INDEX]
		tallies[node_name] = triangle_data.size() / 3
	var expected := {"Mesh_0": 82105, "PurchaseDeck_Surface": 1280}
	for tag in INLAYS:
		expected[tag] = 164
	if tallies != expected:
		instance.free()
		return false
	var deck := meshes["PurchaseDeck_Surface"] as MeshInstance3D
	var deck_base := deck.mesh.surface_get_material(0) as BaseMaterial3D
	if deck_base == null:
		instance.free()
		return false
	_deck_paint = deck_base.duplicate() as BaseMaterial3D
	_deck_idle = _deck_paint.albedo_color
	deck.set_surface_override_material(0, _deck_paint)
	for tag in INLAYS:
		var inlay := meshes[tag] as MeshInstance3D
		var base := inlay.mesh.surface_get_material(0) as BaseMaterial3D
		if base == null:
			_paint.clear()
			_idle.clear()
			instance.free()
			return false
		var paint := base.duplicate() as BaseMaterial3D
		_idle.append(paint.albedo_color)
		inlay.set_surface_override_material(0, paint)
		_paint.append(paint)
	_model = instance as Node3D
	add_child(_model)
	_action = _new_label("Action", -0.17, 0.0037)
	_cost = _new_label("Cost", 0.18, 0.0032)
	installed = true
	return true

## Revision belongs to an authoritative stream; no revision may be reused across its lifetime.
## Last trusted state is retained on stale, invalid or contradictory updates.
func apply_state(revision: int, phase: int, repeatable: bool, next_offer_available: bool, commit_confirmed: bool, action_text: String, cost_text: String) -> bool:
	if not installed or revision <= _revision or phase < Phase.UNAVAILABLE or phase > Phase.ACCEPTED:
		return false
	if commit_confirmed != (phase == Phase.ACCEPTED):
		return false
	if next_offer_available and not (phase == Phase.ACCEPTED and repeatable):
		return false
	_revision = revision
	var active := phase == Phase.PAYING or phase == Phase.PENDING
	var rearmed := phase == Phase.ACCEPTED and repeatable and next_offer_available
	visible = phase == Phase.AVAILABLE or active or rearmed
	for i in range(_paint.size()):
		_paint[i].albedo_color = ACTIVE if active else _idle[i]
	var deck_color := _deck_idle
	if phase == Phase.PENDING:
		deck_color = _deck_idle.lerp(CONFIRM_TINT, PENDING_TINT_WEIGHT)
		deck_color.a = _deck_idle.a
	_deck_paint.albedo_color = deck_color
	_action.text = action_text if visible else ""
	_cost.text = cost_text if visible else ""
	return true

func _new_label(label_name: String, offset_z: float, pixel_scale: float) -> Label3D:
	var label := Label3D.new()
	label.name = label_name
	label.position = Vector3(0.0, 0.029, offset_z)
	label.rotate_x(-PI / 2.0)
	label.font_size = 30
	label.pixel_size = pixel_scale
	add_child(label)
	return label
