class_name HavenlineSceneryBatch
extends RefCounted

# Lossless draw submission optimization for the authored static GLBs. Skinning,
# animation, source vertices, materials and character files are never rewritten.
static func collect(node: Node3D, transform: Transform3D, surfaces: Dictionary):
	var local := transform * node.transform
	if node is MeshInstance3D and node.mesh:
		assert(node.skin == null, "Skinned geometry must never enter static batching")
		for index in node.mesh.get_surface_count():
			var material: Material = node.get_active_material(index)
			var key: int = material.get_instance_id() if material else 0
			if not surfaces.has(key): surfaces[key] = {"material":material,"parts":[]}
			surfaces[key].parts.append({"mesh":node.mesh,"surface":index,"transform":local})
	for child in node.get_children():
		if child is Node3D: collect(child, local, surfaces)

static func compile(scene: PackedScene) -> ArrayMesh:
	var root: Node3D = scene.instantiate()
	# The authored kit contains one mesh in an identity transform. Rebuilding
	# it with SurfaceTool discards imported screen-space LODs and shadow meshes.
	# Duplicate the mesh resource (not its vertices) to keep both intact while
	# allowing instance materials to change without mutating the source scene.
	var candidates: Array = []
	collect_meshes(root, Transform3D.IDENTITY, candidates)
	if candidates.size() == 1 and candidates[0].transform.is_equal_approx(Transform3D.IDENTITY):
		var source: MeshInstance3D = candidates[0].node
		if source.mesh is ArrayMesh and source.skin == null:
			var retained: ArrayMesh = source.mesh.duplicate()
			for i in source.mesh.get_surface_count():
				retained.surface_set_material(i, source.get_active_material(i))
			root.free()
			return retained
	var surfaces: Dictionary = {}
	collect(root, Transform3D.IDENTITY, surfaces)
	var result := ArrayMesh.new()
	for group in surfaces.values():
		var tool := SurfaceTool.new()
		tool.begin(Mesh.PRIMITIVE_TRIANGLES)
		tool.set_material(group.material)
		for part in group.parts:
			tool.append_from(part.mesh, part.surface, part.transform)
		tool.commit(result)
	root.free()
	return result

static func instances(mesh: Mesh, transforms: Array[Transform3D], parent: Node3D) -> MultiMeshInstance3D:
	var batch := MultiMesh.new()
	batch.transform_format = MultiMesh.TRANSFORM_3D
	batch.mesh = mesh
	batch.instance_count = transforms.size()
	for index in transforms.size(): batch.set_instance_transform(index, transforms[index])
	var visual := MultiMeshInstance3D.new()
	visual.multimesh = batch
	parent.add_child(visual)
	return visual

static func collect_meshes(node: Node3D, parent_transform: Transform3D, result: Array):
	var combined := parent_transform * node.transform
	if node is MeshInstance3D and node.mesh:
		assert(node.skin == null, "Skinned geometry must never enter static batching")
		result.append({"node": node, "transform": combined})
	for child in node.get_children():
		if child is Node3D: collect_meshes(child, combined, result)
