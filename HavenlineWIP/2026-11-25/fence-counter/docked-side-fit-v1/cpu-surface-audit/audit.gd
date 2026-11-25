extends "res://tests/_observe_docked.gd"
var found_stops: int = 0
var written_donor: bool = false

func pt(v: Vector3) -> Array:
	return [v.x, v.y, v.z]

func output_surface(parts: Array[Node], frame: Node3D, id: String, hero: bool) -> bool:
	if parts.is_empty():
		return false
	var surfaces := []
	for item in parts:
		var mesh := item as MeshInstance3D
		if not mesh.is_visible_in_tree():
			continue
		if mesh.mesh == null or mesh.mesh.get_blend_shape_count() != 0:
			return false
		var relative := frame.global_transform.affine_inverse() * mesh.global_transform
		var bind := mesh.skin
		var bone_matrices: Array[Transform3D] = []
		if bind != null:
			var skel := mesh.get_node_or_null(mesh.skeleton) as Skeleton3D
			if skel == null or bind.get_bind_count() == 0:
				return false
			skel.force_update_all_bone_transforms()
			for j in range(bind.get_bind_count()):
				var bone := skel.find_bone(String(bind.get_bind_name(j))) if bind.get_bind_name(j) != &"" else bind.get_bind_bone(j)
				if bone < 0 or bone >= skel.get_bone_count():
					return false
				bone_matrices.append(skel.get_bone_global_pose(bone) * bind.get_bind_pose(j))
		for si in range(mesh.mesh.get_surface_count()):
			if not mesh.mesh is ArrayMesh or (mesh.mesh as ArrayMesh).surface_get_primitive_type(si) != Mesh.PRIMITIVE_TRIANGLES:
				return false
			var arr := mesh.mesh.surface_get_arrays(si)
			var vertices: PackedVector3Array = arr[Mesh.ARRAY_VERTEX]
			var indices: PackedInt32Array = arr[Mesh.ARRAY_INDEX] if arr[Mesh.ARRAY_INDEX] != null else PackedInt32Array()
			if indices.is_empty():
				indices.resize(vertices.size())
				for j in range(vertices.size()):
					indices[j] = j
			var coeffs: PackedFloat32Array = arr[Mesh.ARRAY_WEIGHTS] if arr[Mesh.ARRAY_WEIGHTS] != null else PackedFloat32Array()
			var bones: PackedInt32Array = arr[Mesh.ARRAY_BONES] if arr[Mesh.ARRAY_BONES] != null else PackedInt32Array()
			var fitted := []
			var altered: int = 0
			var largest_sum_delta: float = 0.0
			if hero and (bones.is_empty() or bone_matrices.is_empty()):
				return false
			var width: int = int(float(bones.size()) / vertices.size())
			if width not in [0, 4, 8] or coeffs.size() != bones.size() or width * vertices.size() != bones.size():
				return false
			for j in range(vertices.size()):
				var point := vertices[j]
				if width > 0:
					var deformed := Vector3.ZERO
					var coeff_sum: float = 0.0
					for k in range(width):
						var packed := width*j+k
						if coeffs[packed] == 0.0:
							continue
						if bones[packed] < 0 or bones[packed] >= bone_matrices.size():
							return false
						deformed += (bone_matrices[bones[packed]] * point) * coeffs[packed]
						coeff_sum += coeffs[packed]
					largest_sum_delta = maxf(largest_sum_delta, absf(coeff_sum-1.0))
					if absf(coeff_sum-1.0) > .0002:
						return false
					if deformed.distance_to(point) > .0001:
						altered += 1
					point = deformed
				fitted.append(pt(relative*point))
			if hero and altered == 0:
				return false
			surfaces.append({"name":mesh.name,"surface":si,"positions":fitted,"triangles":Array(indices),"matrixes":bone_matrices.size(),"weights":width,"vertices_with_pose_delta":altered,"max_weight_sum_delta":largest_sum_delta})
	if surfaces.is_empty():
		return false
	var file := FileAccess.open(output_dir.path_join(id + ".json"), FileAccess.WRITE)
	if file == null:
		return false
	file.store_string(JSON.stringify(surfaces))
	return true

func shot(tag: String, _focus: Vector3, _offset: Vector3, _span: float, _custom: bool) -> bool:
	route_frames += 1
	if tag not in ["center-inboard-hard-stop","center-outboard-hard-stop"]:
		print("ROUTE_ONLY_NO_IMAGE ",tag)
		return true
	# Native observer waits these same 12 ticks after initiating the shot.
	await tick(12)
	var frame := joined.get_parent() as Node3D
	var actor := game.actor as CharacterBody3D
	var hero: Node3D
	var animation: AnimationPlayer = game.hero_locomotion.player
	if animation == null:
		return false
	for child in actor.get_children():
		if child.is_ancestor_of(animation):
			hero = child
	if hero == null or not actor.is_on_floor():
		return false
	var exact_donor := frame.get_node("UnmodifiedDonor")
	if not written_donor:
		written_donor = output_surface(exact_donor.find_children("*", "MeshInstance3D", true, false), frame, "counter", false)
	if not written_donor or not output_surface(hero.find_children("*", "MeshInstance3D", true, false), frame, tag, true):
		push_error("CPU pose/surface source could not be admitted")
		return false
	found_stops += 1
	print("CPU_SURFACE ",JSON.stringify({"id":tag,"foot":pt(frame.to_local(actor.global_position)),"animation":str(animation.current_animation),"animation_time":animation.current_animation_position,"yaw":actor.rotation.y, "floor":actor.is_on_floor(),"actual_renderer":DisplayServer.get_name()}))
	return true
