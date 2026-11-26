from pathlib import Path
import sys
p=Path(sys.argv[1])/'previews/reference_panel/reference_panel.gd'
obs=Path(sys.argv[1])/'tests/hvn_l1_combined_draw.gd'
def replacement(path,pairs):
    s=path.read_text()
    for a,b in pairs:
        assert s.count(a)==1,a
        s=s.replace(a,b)
    path.write_text(s)
replacement(p,[
 ('const CUT_INDEX := 0','''const CUT_INDEX := 0
const PAINT = preload("res://previews/reference_panel/assets/material_reference_paint.gdshader")
const PAINT_MAP = preload("res://previews/reference_panel/assets/material-map.json")
const PAINT_STRENGTH := 1.0'''),
 ('\tview.mesh = detail','''	view.mesh = detail
	var roles: Dictionary = PAINT_MAP.data.bindings
	if roles.size()!=4:
		return "local-paint-binding-cardinality"
	for i in range(4):
		var expected := String(MATERIAL_ORDER[i])
		if not roles.has(expected) or int(roles[expected])!=i:
			return "local-paint-binding-order"
		var local := ShaderMaterial.new()
		local.shader = PAINT
		local.set_shader_parameter("style_role",i)
		local.set_shader_parameter("paint_strength",PAINT_STRENGTH)
		view.set_surface_override_material(i,local)
	print("V3_LOCAL_PAINT_MOUNT exact 4 per-instance overrides; no source or world material changes")''')
])
replacement(obs,[
 ('or view.get_surface_override_material(i)!=null',''),
 ('\treturn true\n\n','\treturn true\n\n') if False else
 ('''		if mat.resource_name.to_lower()!=labels[i] or int((ni if ni>0 else nv)/3.0)!=counts[i] or not mat.albedo_color.is_equal_approx(colors[i]):
			return false
	return true''','''		if mat.resource_name.to_lower()!=labels[i] or int((ni if ni>0 else nv)/3.0)!=counts[i] or not mat.albedo_color.is_equal_approx(colors[i]):
			return false
		var applied := view.get_surface_override_material(i) as ShaderMaterial
		if not applied or applied.shader.resource_path!="res://previews/reference_panel/assets/material_reference_paint.gdshader" or int(applied.get_shader_parameter("style_role"))!=i or not is_equal_approx(float(applied.get_shader_parameter("paint_strength")),1.0):
			return false
	return true''')
])
