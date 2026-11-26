extends RefCounted
## Source-only test helper; return {} on unknown render state. Not installed or parsed.
static func v(a: Vector3) -> Array:
	return [a.x,a.y,a.z]

static func tf(t: Transform3D) -> Array:
	return [v(t.basis.x),v(t.basis.y),v(t.basis.z),v(t.origin)]

static func acquire(actor: Node3D, player: AnimationPlayer, cam: Camera3D, tick: int) -> Dictionary:
	if not is_instance_valid(actor) or not is_instance_valid(player) or not is_instance_valid(cam):
		return {}
	if cam.projection!=Camera3D.PROJECTION_ORTHOGONAL or not is_equal_approx(cam.size,13.0):
		return {}
	var surfaces := []
	var skinned := 0
	for node in actor.find_children("*","MeshInstance3D",true,false):
		var mesh := node as MeshInstance3D
		if not mesh.is_visible_in_tree():
			continue
		if not mesh.mesh is ArrayMesh or mesh.mesh.get_blend_shape_count()!=0:
			return {}
		var binds := []
		var skel_world := []
		if mesh.skin:
			var skel := mesh.get_node_or_null(mesh.skeleton) as Skeleton3D
			if skel==null or skel.get_bone_count()!=66:
				return {}
			# No force_update, seek, movement, visibility or skeleton change.
			for i in mesh.skin.get_bind_count():
				var n := mesh.skin.get_bind_name(i)
				var idx := skel.find_bone(String(n)) if n!=&"" else mesh.skin.get_bind_bone(i)
				if idx<0 or idx>=skel.get_bone_count():
					return {}
				binds.append({"bind":i,"bone":idx,"pose":tf(skel.get_bone_global_pose(idx)),"inverse":tf(mesh.skin.get_bind_pose(i))})
			skel_world=tf(skel.global_transform)
			skinned+=1
		var entries := []
		for i in mesh.mesh.get_surface_count():
			if (mesh.mesh as ArrayMesh).surface_get_primitive_type(i)!=Mesh.PRIMITIVE_TRIANGLES:
				return {}
			var a := mesh.mesh.surface_get_arrays(i)
			var em := mesh.get_active_material(i) as BaseMaterial3D
			if em==null or em.transparency!=BaseMaterial3D.TRANSPARENCY_DISABLED:
				return {}
			var vtx: PackedVector3Array = a[Mesh.ARRAY_VERTEX]
			var indices: PackedInt32Array = [] if a[Mesh.ARRAY_INDEX]==null else a[Mesh.ARRAY_INDEX]
			var w: PackedFloat32Array = [] if a[Mesh.ARRAY_WEIGHTS]==null else a[Mesh.ARRAY_WEIGHTS]
			var j: PackedInt32Array = [] if a[Mesh.ARRAY_BONES]==null else a[Mesh.ARRAY_BONES]
			if vtx.is_empty() or not w.size()==j.size() or (not binds.is_empty() and j.size() not in [4*vtx.size(),8*vtx.size()]):
				return {}
			entries.append({"surface":i,"vertices":vtx.size(),"indices":indices.size(),"weights":w.size(),"cull":em.cull_mode,
				"albedo_path":em.albedo_texture.resource_path if em.albedo_texture else ""})
		surfaces.append({"relative":String(actor.get_path_to(mesh)),"world":tf(mesh.global_transform),"skeleton_world":skel_world,
			"palette":binds,"surfaces":entries})
	if skinned!=1 or surfaces.is_empty():
		return {}
	return {"tick":tick,"physics":Engine.get_physics_frames(),"phase":String(player.current_animation),
		"phase_seconds":player.current_animation_position,"actor":tf(actor.global_transform),"camera":tf(cam.global_transform),
		"projection":cam.projection,"size":cam.size,"keep_aspect":cam.keep_aspect,"viewport":[cam.get_viewport().size.x,cam.get_viewport().size.y],
		"offset":[cam.h_offset,cam.v_offset],"near":cam.near,"far":cam.far,"surfaces":surfaces}
