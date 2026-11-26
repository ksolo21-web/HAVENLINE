extends SceneTree
func _initialize() -> void:
	var files := ["res://old/GateLeaf.obj","res://old/GateLeaf_Right.obj","res://new/GateLeaf.obj","res://new/GateLeaf_Right.obj"]
	for path in files:
		var mesh := load(path) as ArrayMesh
		if mesh == null:
			print("OBJ_IMPORT_REJECT ",path)
			quit(2)
			return
		var box := mesh.get_aabb()
		var rows := []
		var combined := {}
		for k in range(mesh.get_surface_count()):
			var mat := mesh.surface_get_material(k)
			var ni := mesh.surface_get_array_index_len(k)
			var nv := mesh.surface_get_array_len(k)
			var triangles := int((ni if ni > 0 else nv) / 3.0)
			var name := mat.resource_name.to_lower() if mat else "<NONE>"
			combined[name]=int(combined.get(name,0))+triangles
			rows.append({"index":k,"material":name,"vertices":nv,"indices":ni,"triangles":triangles,
				"primitive":mesh.surface_get_primitive_type(k),"class":mat.get_class() if mat else "<NONE>","albedo_map":mat.get("albedo_texture")!=null if mat else false})
		print("OBJ_IMPORT_OBSERVED ",JSON.stringify({"path":path,"surface_count":rows.size(),"surfaces":rows,"triangles_combined":combined,
			"aabb":[[box.position.x,box.position.y,box.position.z],[box.end.x,box.end.y,box.end.z]],"mesh_resource":mesh.resource_path}))
	quit()
