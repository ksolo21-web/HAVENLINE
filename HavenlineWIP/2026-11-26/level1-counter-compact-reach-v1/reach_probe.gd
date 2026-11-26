extends "res://tests/_stop_guard.gd"
# Observation only: no queues, service state, hand animation or ray authority.
var reach_rows: int = 0

func donor_triangles(frame: Node3D) -> Array[PackedVector3Array]:
	var surfaces: Array[PackedVector3Array] = []
	for child in frame.get_node("UnmodifiedDonor").find_children("*", "MeshInstance3D", true, false):
		var view := child as MeshInstance3D
		if view.mesh == null or not view.is_visible_in_tree():
			continue
		if not view.mesh is ArrayMesh:
			return []
		var rel := frame.global_transform.affine_inverse() * view.global_transform
		for i in range(view.mesh.get_surface_count()):
			if (view.mesh as ArrayMesh).surface_get_primitive_type(i) != Mesh.PRIMITIVE_TRIANGLES:
				return []
			var arr := view.mesh.surface_get_arrays(i)
			var vs: PackedVector3Array = arr[Mesh.ARRAY_VERTEX]
			var ix: PackedInt32Array = arr[Mesh.ARRAY_INDEX] if arr[Mesh.ARRAY_INDEX] != null else PackedInt32Array()
			var vertices := PackedVector3Array()
			if ix.is_empty():
				for p in vs:
					vertices.append(rel * p)
			else:
				for j in ix:
					vertices.append(rel * vs[j])
			if vertices.is_empty() or vertices.size() % 3 != 0:
				return []
			surfaces.append(vertices)
	return surfaces

func surface_probe(origin: Vector3, destination: Vector3, donor: Array[PackedVector3Array]) -> Dictionary:
	var span := origin.distance_to(destination)
	var first := span
	var triangle_count := 0
	for surface in donor:
		for j in range(0, surface.size(), 3):
			triangle_count += 1
			var hit: Variant = Geometry3D.segment_intersects_triangle(origin,destination,surface[j],surface[j+1],surface[j+2])
			if hit is Vector3:
				first = minf(first,origin.distance_to(hit))
	return {"straight_pivot_distance_m":span,"first_donor_distance_m": first if first < span else null,
			"earlier_than_endpoint_by_1cm": first < span - .010, "tested_triangles": triangle_count}

func center_probe(from_inside: bool) -> bool:
	var frame := joined.get_parent() as Node3D
	var marks := frame.get_node("Markers_NotBindings") as Node3D
	var mark := marks.get_node("WorkerInteriorStance" if from_inside else "CustomerExteriorStance") as Node3D
	var side: float = 1.0 if from_inside else -1.0
	var local_mark := frame.to_local(mark.global_position)
	var actor := game.actor as CharacterBody3D
	check(await travel(game.to_local(frame.to_global(local_mark + Vector3(0,0,.52*side)))),"compact reach lawful axial apron by ordinary input")
	check(await travel(game.to_local(mark.global_position)),"compact reach unchanged stance by ordinary input")
	await tick(12)
	var foot := frame.to_local(actor.global_position)
	var aim: float = absf(wrapf(actor.rotation.y - (PI if from_inside else 0.0), -PI, PI))
	if not actor.is_on_floor() or Vector2(foot.x-local_mark.x,foot.z-local_mark.z).length() >= .05 or aim > deg_to_rad(5.0):
		return false
	var skeletons := actor.find_children("*", "Skeleton3D", true, false)
	if skeletons.size() != 1:
		return false
	var rig := skeletons[0] as Skeleton3D
	rig.force_update_all_bone_transforms()
	var donor := donor_triangles(frame)
	if donor.is_empty():
		return false
	var measurements := {}
	for bone: String in ["Head", "L_Hand", "R_Hand"]:
		var idx := rig.find_bone(bone)
		if idx < 0:
			return false
		var position := frame.to_local(rig.to_global(rig.get_bone_global_pose(idx).origin))
		for marker_name: String in ["StockHandling", "PaymentHandling", "StockRestWitness", "PaymentRestWitness"]:
			var site := marks.get_node(marker_name) as Node3D
			var probe := surface_probe(position,frame.to_local(site.global_position),donor)
			measurements[bone + ":" + marker_name] = probe
			check(float(probe["straight_pivot_distance_m"]) > 0.0 and int(probe["tested_triangles"]) > 0,"native pivot and real imported donor measurement")
			reach_rows += 1
	print("COMPACT_COUNTER_REACH ", JSON.stringify({"side":"inside" if from_inside else "outside", "actor_foot":pt(foot),
		"unchanged_marker":pt(local_mark), "heading_error_deg":rad_to_deg(aim), "measurements":measurements}))
	check(reach_rows == (12 if from_inside else 24),"exact scoped compact reach rows")
	return await super.center_probe(from_inside)
