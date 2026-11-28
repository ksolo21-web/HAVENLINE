extends RefCounted
## Explicit opt-in bridge for the already-detached combined preview.
## No actor, progress, hinge, collision, material of other scenery or save authority.
const Gate = preload("res://technical_gate.gd")
const Mount = preload("res://previews/gate_pair_study/gate_pair_mount.gd")
const Terrain = preload("res://terrain_source.gd")
const FreshT02 = preload("res://accepted_t02_surface.gd")
const REVIEW_FLAG := "--l1-review-gate-art"
const EXPECTED_IDS := ["gate-south", "gate-east"]
const ACCEPTED_FACE_VERTICES := 369024
const ACCEPTED_GROUND_LAYER := 1 << 11
static var _accepted_face_bytes := PackedByteArray()

static func _canonical_faces() -> PackedByteArray:
	# Compile from the pinned accepted generator independently of Terrain's
	# shared mutable ArrayMesh. Reuse only the private packed proof, not the mesh.
	if _accepted_face_bytes.is_empty():
		var source_mesh := FreshT02._indexed_grid()
		if source_mesh != null and source_mesh.get_surface_count() == 1:
			var authored := source_mesh.get_faces()
			if authored.size() == ACCEPTED_FACE_VERTICES:
				_accepted_face_bytes = authored.to_byte_array()
	return _accepted_face_bytes

static func _seats_for(gate: Gate) -> Dictionary:
	# Exact T02 seat formula independently re-evaluated from each mechanism
	# center + its unchanged signed X axis, never from the existing hinge Y.
	var at := gate.position
	var axis := gate.basis.x
	var values := Vector2.ZERO
	for i: int in range(2):
		var side := -1.0 if i == 0 else 1.0
		var target := Vector2(at.x + axis.x * Gate.HALF_SPAN * side, at.z + axis.z * Gate.HALF_SPAN * side)
		var sample := Terrain.sample(target)
		var y: Variant = sample.get("height")
		if sample.get("valid") != true or (typeof(y) != TYPE_INT and typeof(y) != TYPE_FLOAT) or not is_finite(float(y)):
			return {}
		values[i] = float(y) - at.y
	return {"offsets":values} if values.is_finite() else {}

static func _translation_only(frame: Transform3D) -> bool:
	if not frame.is_finite():
		return false
	return Mount._frame_matches(Transform3D(frame.basis, Vector3.ZERO), Transform3D.IDENTITY)

static func _exact_terrain_contact(ground: StaticBody3D, collider: CollisionShape3D, visual: MeshInstance3D) -> bool:
	# Exact TerrainContactPreview source builds one collision shape from the
	# ordered TriangleMesh faces of this same authoritative accepted mesh.
	if ground.collision_layer != ACCEPTED_GROUND_LAYER or ground.collision_mask != 0:
		return false
	if ground.process_mode != Node.PROCESS_MODE_INHERIT or collider.process_mode != Node.PROCESS_MODE_INHERIT:
		return false
	# A disabled ancestor removes an otherwise canonical PhysicsServer body.
	# Verify the effective state and the contact compiler's default removal mode.
	if not ground.is_inside_tree() or not collider.is_inside_tree() or not ground.can_process() or not collider.can_process():
		return false
	if ground.disable_mode != CollisionObject3D.DISABLE_MODE_REMOVE:
		return false
	var mesh := Terrain.terrain_mesh()
	if mesh == null or visual.mesh != mesh or mesh.get_surface_count() != 1:
		return false
	var shape := collider.shape as ConcavePolygonShape3D
	if shape == null or shape.backface_collision:
		return false
	var actual_faces := shape.get_faces()
	if actual_faces.size() != ACCEPTED_FACE_VERTICES:
		return false
	var visible_faces := mesh.get_faces()
	if visible_faces.size() != ACCEPTED_FACE_VERTICES:
		return false
	# At explicit mount only; compare both against independently compiled donor
	# content, so a shared cache and live shape altered together cannot agree.
	var expected := _canonical_faces()
	return not expected.is_empty() and actual_faces.to_byte_array() == expected and visible_faces.to_byte_array() == expected

static func _trusted_camp(preview: Node3D, ground: StaticBody3D) -> Node3D:
	if not is_instance_valid(preview) or not preview.is_inside_tree() or not is_instance_valid(ground):
		return null
	var script := preview.get_script() as Script
	if script == null or script.resource_path != "res://previews/integrated_opening.gd":
		return null
	# The exact combined solver and seat setup are evaluated in the preview's
	# unrotated local T02 axes. A shared rigid translation is source-supported;
	# scene-root yaw is not assumed (native South/East mechanism headings stay).
	if not _translation_only(preview.transform) or not _translation_only(preview.global_transform):
		return null
	var ground_root := ground.get_parent() as Node3D
	var surface := ground_root.get_parent() as Node3D if ground_root != null else null
	var camp := preview.get_node_or_null("GrantOnlyCamp") as Node3D
	if ground_root == null or surface == null or camp == null:
		return null
	if surface.get_parent() != preview or camp.get_parent() != preview or ground_root.name != &"AcceptedGround":
		return null
	if surface.scene_file_path != "res://previews/terrain_water_preview.tscn" or surface.get_node_or_null("AcceptedGround/GroundBody") != ground:
		return null
	if surface.get("water_bound") != true or ground_root.get("bound") != true:
		return null
	var collider := ground.get_node_or_null("GroundTriangles") as CollisionShape3D
	var visual := ground_root.get_node_or_null("GroundVisual") as MeshInstance3D
	if collider == null or not collider.shape is ConcavePolygonShape3D or collider.disabled or collider.get_parent() != ground:
		return null
	if visual == null or visual.get_parent() != ground_root:
		return null
	for item: Node3D in [camp, surface, ground_root, ground, collider, visual]:
		if item.top_level or not Mount._frame_matches(item.transform, Transform3D.IDENTITY) or not Mount._frame_matches(item.global_transform, preview.global_transform):
			return null
	return camp if _exact_terrain_contact(ground, collider, visual) else null

static func apply_all(gates: Array, preview: Node3D, ground: StaticBody3D) -> bool:
	if gates.size() != EXPECTED_IDS.size():
		return false
	var camp := _trusted_camp(preview, ground)
	if camp == null:
		return false
	var prepared: Array[Dictionary] = []
	var seen: Array[String] = []
	for any_gate in gates:
		if not any_gate is Gate:
			return false
		var gate := any_gate as Gate
		if not is_instance_valid(gate) or not gate.is_inside_tree() or not Mount._gate_frame_valid(gate):
			return false
		if not EXPECTED_IDS.has(gate.gate_id) or seen.has(gate.gate_id):
			return false
		seen.append(gate.gate_id)
		if gate.top_level or gate.get_parent() != camp:
			return false
		var seats := _seats_for(gate)
		if seats.is_empty():
			return false
		var offsets: Vector2 = seats.offsets
		var left := Mount._prepare_side(gate, true, offsets.x)
		var right := Mount._prepare_side(gate, false, offsets.y)
		if left.is_empty() or right.is_empty():
			return false
		prepared.append(left)
		prepared.append(right)
	# Exactly the approved V4 visual operations, in one synchronous batch.
	# No return/failure after installing the first node and no partial hide.
	for row in prepared:
		var art := MeshInstance3D.new()
		art.name = Mount.NAME
		art.mesh = row.visual
		row.pivot.add_child(art)
	for row in prepared:
		row.placeholder.hide()
	return true
