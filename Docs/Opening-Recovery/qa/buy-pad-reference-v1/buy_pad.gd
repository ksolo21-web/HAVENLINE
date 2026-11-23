extends Node3D
## Presentation only. Reads the state from a trusted owner; never charges or grants.
enum OfferPhase { UNAVAILABLE, AVAILABLE, PAYING, PENDING, ACCEPTED }
const IDLE_CORNER := Color("#e8edf4")
const ACTIVE_CORNER := Color("#77eb52")
const SLATE := Color("#5e636c")
const CONFIRM_TINT := Color("#54af3b")
const SIGNAL := Color("#f5f5ef")

var _deck: MeshInstance3D
var _corner_root: Node3D
var _corner_material: StandardMaterial3D
var _deck_material: StandardMaterial3D
var _action: Label3D
var _cost: Label3D

func _ready() -> void:
	_deck_material = _material()
	_corner_material = _material()
	_deck = _box(self, "SlateSurface", Vector3(0, 0.016, 0), Vector3(0.96, 0.032, 0.86), _deck_material)
	_corner_root = Node3D.new()
	_corner_root.name = "SeparatedBrackets"
	add_child(_corner_root)
	for sx: int in [-1, 1]:
		for sz: int in [-1, 1]:
			var corner := Node3D.new()
			_corner_root.add_child(corner)
			corner.position = Vector3(sx * 0.465, 0.039, sz * 0.414)
			_box(corner, "Across", Vector3(-sx * 0.059, 0, 0), Vector3(0.135, 0.007, 0.019), _corner_material)
			_box(corner, "Along", Vector3(0, 0, -sz * 0.059), Vector3(0.019, 0.007, 0.135), _corner_material)
	_action = _label("Action", -0.11, 0.011)
	_cost = _label("Cost", 0.15, 0.0085)
	show_offer(OfferPhase.UNAVAILABLE, false, false, "", "")

func show_offer(phase: int, repeatable: bool, next_offer_available: bool, action_text: String, cost_text: String) -> void:
	var is_active := phase == OfferPhase.PAYING or phase == OfferPhase.PENDING
	var is_rearmed := phase == OfferPhase.ACCEPTED and repeatable and next_offer_available
	visible = phase == OfferPhase.AVAILABLE or is_active or is_rearmed
	_corner_material.albedo_color = ACTIVE_CORNER if is_active else IDLE_CORNER
	_deck_material.albedo_color = CONFIRM_TINT if phase == OfferPhase.PENDING else SLATE
	_action.text = action_text if visible else ""
	_cost.text = cost_text if visible else ""

func _material() -> StandardMaterial3D:
	var mat := StandardMaterial3D.new()
	mat.roughness = 1.0
	mat.metallic = 0.0
	return mat

func _box(parent: Node3D, node_name: String, at: Vector3, dims: Vector3, material: StandardMaterial3D) -> MeshInstance3D:
	var shape := BoxMesh.new()
	shape.size = dims
	var node := MeshInstance3D.new()
	node.name = node_name
	node.mesh = shape
	node.material_override = material
	node.position = at
	node.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	parent.add_child(node)
	return node

func _label(node_name: String, z: float, scale_per_px: float) -> Label3D:
	var label3 := Label3D.new()
	label3.name = node_name
	label3.position = Vector3(0, 0.049, z)
	label3.rotation.x = -PI / 2.0
	label3.font_size = 30
	label3.outline_size = 0
	label3.pixel_size = scale_per_px / 5.0
	label3.modulate = SIGNAL
	add_child(label3)
	return label3
