extends RefCounted

const PATHS := {
	"money": "res://assets/customer_counter/banded_notes.glb",
	"meal": "res://assets/customer_counter/cooked_game_meat.glb",
	"planks": "res://assets/shore_workshops/finished_planks.glb",
	"blocks": "res://assets/shore_workshops/dressed_block.glb",
	"wood": "res://assets/field/wood.glb",
	"stone": "res://assets/field/stone.glb",
	"meat": "res://assets/field/meat.glb",
	"wolf": "res://assets/field/hostile_wolf.glb",
	"coal": "res://assets/field/coal.glb",
	"metal": "res://assets/field/metal.glb",
	"slate": "res://assets/field/slate.glb",
}
const WIDTHS := {"money": .26, "meal": .36, "planks": .48, "blocks": .39, "wood": .53, "stone": .40, "meat": .39, "wolf": 2.4, "coal": .39, "metal": .42, "slate": .47}
const GROUND_WIDTHS := {"wood": .64, "stone": .54, "meat": .53, "coal": .50, "metal": .53, "slate": .59}
static var source_bounds := {}
static var source_scenes := {}

static func _bounds(node: Node, parent_xform: Transform3D, found: Array[AABB]) -> void:
	var transform := parent_xform
	if node is Node3D:
		transform *= (node as Node3D).transform
	if node is MeshInstance3D and node.mesh:
		found.append(transform * node.mesh.get_aabb())
	for child in node.get_children():
		_bounds(child, transform, found)

static func make(kind: String, width: float = 0.0) -> Node3D:
	if not PATHS.has(kind):
		push_error("Unknown field asset " + kind)
		return null
	# Instances hold the mesh, not the PackedScene: retain the source while a
	# stream of identical drops is loaded, carried or displayed on its shelf.
	if not source_scenes.has(kind):
		var scene := load(String(PATHS[kind])) as PackedScene
		if not scene:
			push_error("Cannot load field art for " + kind)
			return null
		source_scenes[kind] = scene
	var model := (source_scenes[kind] as PackedScene).instantiate() as Node3D
	if not source_bounds.has(kind):
		var boxes: Array[AABB] = []
		_bounds(model, Transform3D.IDENTITY, boxes)
		if boxes.is_empty():
			model.free()
			return null
		var combined: AABB = boxes[0]
		for box in boxes:
			combined = combined.merge(box)
		source_bounds[kind] = combined
	var bounds: AABB = source_bounds[kind]
	var scale_factor := (width if width > 0.0 else float(WIDTHS[kind])) / maxf(.0001, maxf(bounds.size.x, bounds.size.z))
	var anchor := Node3D.new()
	anchor.name = kind.capitalize()
	var normalization := Node3D.new()
	normalization.name = "GroundedModel"
	anchor.add_child(normalization)
	normalization.add_child(model)
	normalization.scale = Vector3.ONE * scale_factor
	normalization.position = -Vector3(bounds.get_center().x, bounds.position.y, bounds.get_center().z) * scale_factor
	return anchor
