extends RefCounted
## Separate imported owner donor census. No consumer writes.
const CENSUS := preload("res://previews/clearance_gate/owner_runtime_census.json")
const DIR := "res://previews/clearance_gate/owner_assets/"
const POST_PARENT := "Owner33035ThresholdPosts"
const POST_PREFIX := "OwnerThreshold_"
const POST_BACKSET := .19616
const POST_SEAT_X := .18816
const POST_SEAT_Z := .19309
const EPS := .00001

static func file_for(left: bool, post: bool) -> String:
	if post:
		return "ThresholdPost.obj" if left else "ThresholdPost_Right.obj"
	return "GateLeaf.obj" if left else "GateLeaf_Right.obj"

static func receipt(source: Mesh, file: String) -> Dictionary:
	var contracted: Dictionary = CENSUS.data.meshes.get(file,{})
	var mesh := source as ArrayMesh
	if contracted.is_empty() or mesh == null or mesh.resource_path != DIR+file:
		return {}
	var expected: Array = contracted.surfaces
	if mesh.get_surface_count() != expected.size():
		return {}
	var box := mesh.get_aabb()
	if not box.position.is_finite() or not box.end.is_finite():
		return {}
	for k in range(3):
		if absf(box.position[k]-float(contracted.aabb[0][k])) > .000001 or absf(box.end[k]-float(contracted.aabb[1][k])) > .000001:
			return {}
	var rows: Array[Dictionary] = []
	var totals := {}
	var tris := 0
	for i in range(mesh.get_surface_count()):
		var mat := mesh.surface_get_material(i) as StandardMaterial3D
		var exp: Dictionary = expected[i]
		if mat == null or mesh.surface_get_primitive_type(i) != Mesh.PRIMITIVE_TRIANGLES:
			return {}
		for prop in mat.get_property_list():
			if int(prop.type)==TYPE_OBJECT and mat.get(prop.name) is Texture:
				return {}
		var key := mat.resource_name.to_lower()
		var ni := mesh.surface_get_array_index_len(i)
		var nv := mesh.surface_get_array_len(i)
		var count := int((ni if ni>0 else nv)/3.0)
		if key!=String(exp.label) or i!=int(exp.index) or ni!=int(exp.indices) or nv!=int(exp.vertices) or count!=int(exp.triangles) or mat.get_class()!=String(exp.material_class):
			return {}
		var color := mat.albedo_color
		var rgba := [color.r,color.g,color.b,color.a]
		for k in range(4):
			if absf(float(rgba[k])-float(exp.albedo_rgba[k]))>.00001:
				return {}
		rows.append({"index":i,"material":key,"class":mat.get_class(),"primitive":mesh.surface_get_primitive_type(i),
			"triangles":count,"indices":ni,"vertices":nv,"albedo_map":false,"albedo_rgba":rgba})
		totals[key]=int(totals.get(key,0))+count
		tris+=count
	if tris!=int(contracted.triangles):
		return {}
	return {"source":mesh.resource_path,"surface_count":rows.size(),"ordered_surfaces":rows,"material_triangles":totals,
		"aabb_low":[box.position.x,box.position.y,box.position.z],"aabb_high":[box.end.x,box.end.y,box.end.z],
		"render_triangles":tris}

static func post_name(gate_index: int, left: bool) -> String:
	return POST_PREFIX+str(gate_index)+("_L" if left else "_R")
