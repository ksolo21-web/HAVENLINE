extends RefCounted
## Temporary exact-geometry presentation only. No caller is wired to live or default scenes.
const Gate = preload("res://technical_gate.gd")
const LeftMesh = preload("res://previews/gate_pair_study/GateLeaf.obj")
const RightMesh = preload("res://previews/gate_pair_study/GateLeaf_Right.obj")
const NAME := &"DetachedArtLeafStudy"
const EPS := 0.00001

static func _frame_matches(actual: Transform3D, expected: Transform3D) -> bool:
	return (
		actual.is_finite()
		and expected.is_finite()
		and actual.origin.distance_to(expected.origin) <= EPS
		and actual.basis.x.distance_to(expected.basis.x) <= EPS
		and actual.basis.y.distance_to(expected.basis.y) <= EPS
		and actual.basis.z.distance_to(expected.basis.z) <= EPS
	)

static func _rigid_yaw_frame(frame: Transform3D) -> bool:
	if not frame.is_finite():
		return false
	var b := frame.basis
	# Unit horizontal X and +Y with Z=X cross Y give a positive rigid frame.
	# Translation and yaw are unrestricted; pitch, reflection and shear are not.
	return b.y.distance_to(Vector3.UP) <= EPS and (
		absf(b.x.dot(Vector3.UP)) <= EPS
		and b.x.length_squared() >= 1.0 - EPS and b.x.length_squared() <= 1.0 + EPS
		and b.z.distance_to(b.x.cross(Vector3.UP)) <= EPS
		and absf(b.determinant() - 1.0) <= EPS * 3.0
	)

static func _gate_frame_valid(gate: Gate) -> bool:
	if not is_finite(gate.angle) or gate.angle < 0.0 or gate.angle > PI * 0.5:
		return false
	# Child frames may be canonical while an ancestor distorts the actual world.
	# Validate the effective world frame before selecting either visual.
	return _rigid_yaw_frame(gate.transform) and _rigid_yaw_frame(gate.global_transform)

static func _prepare_side(gate: Gate, left: bool, seat_y: float) -> Dictionary:
	var pivot := gate.get_node_or_null("HingeLeft" if left else "HingeRight") as Node3D
	var side := -1.0 if left else 1.0
	var pivot_frame := Transform3D(Basis(Vector3.UP, -side * gate.angle), Vector3(side * Gate.HALF_SPAN, seat_y, 0.0))
	if pivot == null or pivot.get_parent() != gate or not _frame_matches(pivot.transform, pivot_frame) or pivot.get_child_count() != 1:
		return {}
	var body := pivot.get_child(0) as AnimatableBody3D
	var expected := Vector3(-side * Gate.LEAF_LENGTH * 0.5, Gate.LEAF_HEIGHT * 0.5, 0.0)
	if body == null or body.get_parent() != pivot or not _frame_matches(body.transform, Transform3D(Basis.IDENTITY, expected)) or body.get_child_count() != 2:
		return {}
	var collision: CollisionShape3D
	var placeholder: MeshInstance3D
	for child in body.get_children():
		if child is CollisionShape3D:
			collision = child as CollisionShape3D
		elif child is MeshInstance3D:
			placeholder = child as MeshInstance3D
	if collision == null or placeholder == null or not collision.shape is BoxShape3D or not placeholder.mesh is BoxMesh:
		return {}
	if collision.get_parent() != body or placeholder.get_parent() != body:
		return {}
	# Match actual runtime ownership and local transforms, not just box extents.
	if not _frame_matches(collision.transform, Transform3D.IDENTITY) or not _frame_matches(placeholder.transform, Transform3D.IDENTITY):
		return {}
	if collision.top_level or placeholder.top_level or pivot.top_level or body.top_level:
		return {}
	var box := collision.shape as BoxShape3D
	if not box.size.is_equal_approx(Vector3(Gate.LEAF_LENGTH, Gate.LEAF_HEIGHT, Gate.LEAF_DEPTH)):
		return {}
	if not (placeholder.mesh as BoxMesh).size.is_equal_approx(box.size):
		return {}
	var visual: Mesh = LeftMesh if left else RightMesh
	if visual == null or visual.get_surface_count() <= 0:
		return {}
	var bounds := visual.get_aabb()
	var low := Vector3(0.0 if left else -Gate.LEAF_LENGTH, 0.0, -Gate.LEAF_DEPTH * 0.5)
	var high := Vector3(Gate.LEAF_LENGTH if left else 0.0, Gate.LEAF_HEIGHT, Gate.LEAF_DEPTH * 0.5)
	if not bounds.position.is_finite() or not bounds.end.is_finite():
		return {}
	if not (bounds.position.x >= low.x - EPS and bounds.position.y >= low.y - EPS and bounds.position.z >= low.z - EPS and
		bounds.end.x <= high.x + EPS and bounds.end.y <= high.y + EPS and bounds.end.z <= high.z + EPS):
		return {}
	return {"pivot":pivot, "placeholder":placeholder, "visual":visual}

# An explicit trusted seat pair is required from the caller, not inferred from
# whatever child poses happen to be present. In the integrated scene, independently
# recompute each Terrain.sample(gate_center + aligned hinge X).height - gate_center.y.
# Only a new flat technical fixture passes Vector2.ZERO.
static func apply(gate: Gate, trusted_seats: Vector2) -> bool:
	if not is_instance_valid(gate) or not gate.is_inside_tree() or not trusted_seats.is_finite() or not _gate_frame_valid(gate):
		return false
	var a := _prepare_side(gate, true, trusted_seats.x)
	var b := _prepare_side(gate, false, trusted_seats.y)
	if a.is_empty() or b.is_empty():
		return false
	# Attach unscaled at the exact pivots (not at their offset collision bodies).
	# Hide only validated visual placeholders after both sides prove compatible.
	for row in [a, b]:
		var node := MeshInstance3D.new()
		node.name = NAME
		node.mesh = row.visual
		row.pivot.add_child(node)
	for row in [a, b]:
		row.placeholder.hide()
	return true
