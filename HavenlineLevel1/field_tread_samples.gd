extends RefCounted
## Sample real tread vertices on both feet and retain their material identities.
var target: Skeleton3D
var soles: Array = []
var bind_ids := {}

func bind(mesh: MeshInstance3D, rig: Skeleton3D) -> void:
	target=rig
	var box:=mesh.mesh.get_aabb()
	for surface in mesh.mesh.get_surface_count():
		var a:=mesh.mesh.surface_get_arrays(surface)
		var vertices: PackedVector3Array=a[Mesh.ARRAY_VERTEX]
		var weights: PackedFloat32Array=a[Mesh.ARRAY_WEIGHTS]
		var indices: PackedInt32Array=a[Mesh.ARRAY_BONES]
		var width:=weights.size()/vertices.size()
		var lowest:={}

		for i in vertices.size():
			var p := vertices[i]
			if p.y > box.position.y+.033*box.size.y: continue
			var cell := Vector2i(floori(p.x/.025),floori(p.z/.025))
			if not lowest.has(cell) or vertices[lowest[cell]].y > p.y: lowest[cell]=i
		for i: int in lowest.values():
			var contributions := []
			for k in width:
				var weight := weights[width*i+k]
				if weight <= 0.: continue
				var index := indices[width*i+k]
				var bone := target.find_bone(mesh.skin.get_bind_name(index))
				if bone < 0: bone = mesh.skin.get_bind_bone(index)
				bind_ids[bone]=true
				contributions.append([bone,mesh.skin.get_bind_pose(index)*vertices[i],weight])
			soles.append([int(vertices[i].x < box.get_center().x),contributions])


func points() -> PackedVector3Array:
	var poses := {}
	for bone: int in bind_ids: poses[bone]=target.global_transform*target.get_bone_global_pose(bone)
	var points := PackedVector3Array()
	for sample: Array in soles:
		var at := Vector3.ZERO
		for influence: Array in sample[1]:
			at += (poses[influence[0]] * influence[1]) * float(influence[2])
		points.append(at)
	return points

func lowest(points: PackedVector3Array) -> Array[int]:
	var indices: Array[int]=[-1,-1]
	for i in points.size():
		var side: int=soles[i][0]
		if indices[side]<0 or points[i].y<points[indices[side]].y:
			indices[side]=i
	return indices

func contacts() -> PackedVector3Array:
	var pts := points()
	if pts.is_empty(): return PackedVector3Array()
	var lows := Vector2(INF,INF)
	for i in pts.size():
		var side: int=soles[i][0]
		lows[side]=minf(lows[side],pts[i].y)
	var centers := PackedVector3Array([Vector3.ZERO,Vector3.ZERO])
	var counts := Vector2i.ZERO
	for i in pts.size():
		var side: int=soles[i][0]
		if pts[i].y<=lows[side]+.004:
			centers[side]+=pts[i]
			counts[side]+=1
	for side in 2:
		centers[side]/=maxi(1,counts[side])
		centers[side].y=lows[side]
	return centers
