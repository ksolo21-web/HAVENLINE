extends SceneTree

func reject(message: String) -> void:
	print("OWNER_GATE_IMPORT_REJECT ", message)
	quit(2)

func _initialize() -> void:
	var files := ["GateLeaf.obj","GateLeaf_Right.obj","ThresholdPost.obj","ThresholdPost_Right.obj"]
	var base := OS.get_environment("HVN_OWNER_GATE_EVIDENCE")
	if not base.is_absolute_path() or not DirAccess.dir_exists_absolute(base):
		reject("missing private evidence output")
		return
	for file: String in files:
		var path: String = "res://donors/"+file
		var mesh := load(path) as ArrayMesh
		if mesh == null or mesh.resource_path != path:
			reject("real ArrayMesh/path "+path)
			return
		var box := mesh.get_aabb()
		var rows: Array[Dictionary] = []
		for index in range(mesh.get_surface_count()):
			var mat := mesh.surface_get_material(index) as StandardMaterial3D
			var arrays := mesh.surface_get_arrays(index)
			if mat == null or arrays.size() != Mesh.ARRAY_MAX or mesh.surface_get_primitive_type(index) != Mesh.PRIMITIVE_TRIANGLES:
				reject("primitive/material "+path)
				return
			var verts: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX]
			var ind := PackedInt32Array()
			if arrays[Mesh.ARRAY_INDEX] != null:
				ind = arrays[Mesh.ARRAY_INDEX]
			var expanded := verts.size() if ind.is_empty() else ind.size()
			if expanded == 0 or expanded % 3 != 0:
				reject("malformed triangle stream "+path)
				return
			# Record actual indexed-or-unindexed triangle positions for exact independent source-level verification.
			var basename := file.get_basename() + ".surface-" + str(index)+".xyzf32"
			var handle := FileAccess.open(base.path_join(basename), FileAccess.WRITE)
			if handle == null:
				reject("no geometry evidence file "+basename)
				return
			handle.big_endian = false
			for i in range(expanded):
				var q: Vector3 = verts[i] if ind.is_empty() else verts[ind[i]]
				handle.store_float(q.x)
				handle.store_float(q.y)
				handle.store_float(q.z)
			handle.close()
			var textures: Array[String] = []
			for property in mat.get_property_list():
				var key := String(property.name)
				# Check the descriptor and actual resource; heightmap_flip_texture is bool.
				if int(property.type) == TYPE_OBJECT and mat.get(key) is Texture:
					textures.append(key)
			rows.append({"index":index,"label":mat.resource_name.to_lower(),"primitive":mesh.surface_get_primitive_type(index),
				"material_class":mat.get_class(),"vertices":verts.size(),"indices":ind.size(),"triangles":int(expanded/3.0),
				"payload":basename,"map_slots_bound":textures,"albedo_rgba":[mat.albedo_color.r,mat.albedo_color.g,mat.albedo_color.b,mat.albedo_color.a]})
		print("OWNER_GATE_IMPORT_OBSERVED ", JSON.stringify({"file":file,"mesh_resource":mesh.resource_path,
			"surfaces":rows,"aabb":[[box.position.x,box.position.y,box.position.z],[box.end.x,box.end.y,box.end.z]]}))
	quit()
