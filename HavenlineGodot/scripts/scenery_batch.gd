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
