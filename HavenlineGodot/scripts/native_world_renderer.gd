extends RefCounted

static func meshes(node: Node, output: Array):
	if node is MeshInstance3D: output.append(node)
	for child in node.get_children(): meshes(child, output)

static func batch_static_forest(world: Node3D, resource_visuals: Dictionary) -> Dictionary:
	var groups := {}
	var roots: Array = []
	var before := 0
	for node in world.get_children():
		if not str(node.get_meta("source_asset", "")).begins_with("world/pine_"): continue
		if node in resource_visuals.values(): continue # Harvest visibility remains independent.
		roots.append(node)
		var parts: Array = []
		meshes(node, parts)
		for part in parts:
			var mesh: Mesh = part.mesh
			if mesh == null: continue
			var key := str(mesh.get_instance_id()) + ":" + str(part.material_override)
			if not groups.has(key): groups[key] = {"mesh":mesh, "material":part.material_override, "transforms":[]}
			groups[key].transforms.append(world.global_transform.affine_inverse() * part.global_transform)
			before += 1
	for group in groups.values():
		var multi := MultiMesh.new()
		multi.transform_format = MultiMesh.TRANSFORM_3D
		multi.mesh = group.mesh
		multi.instance_count = group.transforms.size()
		var bounds := AABB()
		for index in range(group.transforms.size()):
			var transform: Transform3D = group.transforms[index]
			multi.set_instance_transform(index,transform)
			var box: AABB = transform * group.mesh.get_aabb()
			bounds = box if index == 0 else bounds.merge(box)
		multi.custom_aabb = bounds.grow(.05)
		var instance := MultiMeshInstance3D.new()
		instance.name = "StaticForestBatch"
		instance.multimesh = multi
		instance.material_override = group.material
		world.add_child(instance)
	for node in roots:
		world.remove_child(node)
		node.queue_free()
	return {"static_tree_roots":roots.size(),"mesh_submissions_before":before,"instanced_mesh_groups":groups.size(),"source_geometry_modified":false,"physical_fps_certified":false}
