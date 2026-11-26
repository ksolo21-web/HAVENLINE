extends SceneTree
## Import and scale contract shared by world bank batches and inventory art.
const Art := preload("res://field_art.gd")
var checks := {}
func _initialize() -> void:
	for mineral:String in ["coal","metal","slate"]:
		var direct:Node3D=load(Art.PATHS[mineral]).instantiate()
		var matches:=direct.find_children("*","MeshInstance3D",true,false)
		if direct is MeshInstance3D: matches.append(direct)
		checks[mineral+" single_mesh"]=matches.size()==1
		if matches.size()==1:
			var node:MeshInstance3D=matches[0]
			var mesh:=node.mesh
			var bounds:=mesh.get_aabb()
			checks[mineral+" unit_geometry"]=node.transform.is_equal_approx(Transform3D.IDENTITY) and is_equal_approx(maxf(bounds.size.x,bounds.size.z),1.0) and absf(bounds.position.y)<.0001 and Vector2(bounds.get_center().x,bounds.get_center().z).length()<.0001 and mesh.get_surface_count()==1
			var arrays:=mesh.surface_get_arrays(0)
			var normals:PackedVector3Array=arrays[Mesh.ARRAY_NORMAL]
			var valid:=normals.size()==(arrays[Mesh.ARRAY_VERTEX] as PackedVector3Array).size()
			for normal in normals:
				if not normal.is_finite() or absf(normal.length()-1.)>.015:valid=false
			checks[mineral+" surface_normals"]=valid
			var mat:=mesh.surface_get_material(0) as StandardMaterial3D
			checks[mineral+" painted_pbr"]=mat!=null and mat.albedo_texture!=null
		direct.free()
		for width:float in [2.0,float(Art.WIDTHS[mineral])]:
			var item:=Art.make(mineral,width)
			var boxes:Array[AABB]=[]
			Art._bounds(item,Transform3D.IDENTITY,boxes)
			checks[mineral+" configured_width "+str(width)]=boxes.size()==1 and absf(maxf(boxes.front().size.x,boxes.front().size.z)-width)<.0005
			item.free()
	print(JSON.stringify({"suite":"field_mineral_art","checks":checks}))
	quit(1 if checks.values().has(false) else 0)
