extends RefCounted
## Interaction distance is measured from the printed plot edge or the building wall.
## All distances use the player's horizontal position in world metres.
const NEAR := .72

static func distance_to_rect(point: Vector2, rect: Rect2) -> float:
	return point.distance_to(point.clamp(rect.position, rect.end))

static func plot_distance(anchor: Node3D, at: Vector3) -> float:
	var bounds: Rect2
	if anchor.has_meta(&"approach_rect"):
		bounds = anchor.get_meta(&"approach_rect")
	else:
		var edge := anchor.get_node("Brackets") as MeshInstance3D
		var aabb := edge.transform * edge.get_aabb()
		bounds = Rect2(aabb.position.x, aabb.position.z, aabb.size.x, aabb.size.z)
		anchor.set_meta(&"approach_rect", bounds)
	var local := anchor.to_local(at)
	var point := Vector2(local.x, local.z)
	var delta := point - point.clamp(bounds.position, bounds.end)
	return (anchor.global_basis * Vector3(delta.x, 0, delta.y)).length()
