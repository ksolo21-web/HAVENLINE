from pathlib import Path
import sys
p=Path(sys.argv[1]); t=p.read_text()
assert t.count('"panels":12,"posts":4,"tris":15784')==1
t=t.replace('"panels":12,"posts":4,"tris":15784','"panels":12,"posts":4,"tris":16584')
cut=t.index('\tvar detail := view.mesh as ArrayMesh',t.index('func _one_reference_panel'))
assert t.endswith('\treturn true\n')
t=t[:cut]+'''	var detail := view.mesh as ArrayMesh
	var immutable := load("res://previews/reference_panel/assets/Fence18595V2.obj") as ArrayMesh
	if not detail or detail!=immutable or view.material_override!=null or detail.get_surface_count()!=4:
		return false
	var labels := ["amber_timber","draped_snow","warm_hemp","cream_hemp"]
	var counts := [1800,1920,2560,2560]
	var colors := [Color(.79,.43,.225,1),Color(.88,.935,.995,1),Color(.77,.55,.32,1),Color(.91,.72,.45,1)]
	for i in range(4):
		var mat := detail.surface_get_material(i) as StandardMaterial3D
		if not mat or mat.emission_enabled or view.get_surface_override_material(i)!=null or detail.surface_get_primitive_type(i)!=Mesh.PRIMITIVE_TRIANGLES:
			return false
		for prop in mat.get_property_list():
			if int(prop.type)==TYPE_OBJECT and mat.get(prop.name) is Texture:
				return false
		var ni := detail.surface_get_array_index_len(i)
		var nv := detail.surface_get_array_len(i)
		if mat.resource_name.to_lower()!=labels[i] or int((ni if ni>0 else nv)/3.0)!=counts[i] or not mat.albedo_color.is_equal_approx(colors[i]):
			return false
	return true
'''
p.write_text(t)
