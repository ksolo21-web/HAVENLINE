extends RefCounted
## Detached presentation-only reference marker. The original installed View
## remains the visible-in-tree authority checked by the purchase receiver.
const Ledger = preload("res://opening_ledger.gd")
const Terrain = preload("res://terrain_source.gd")
const OPT := "--hvn-l1-grounded-construction-marker-v1"
const DATA := "res://previews/grounded_plot_reference/marker.json"
const ROLES := ["gray","brackets","castle","wood_shell","wood_end","wood_pith","price"]
const HEIGHTS := [.003,.006,.006,.007,.008,.009,.006]
const PAINT_ORDER := [0,1,1,1,2,3,1]

static func stage(view: Node3D, graphic_root: Node3D, action: Label3D, cost: Label3D, pad: Node3D) -> bool:
	if not is_instance_valid(view) or view.get_parent()!=pad or not bool(view.get("installed")):
		return false
	if not is_instance_valid(graphic_root) or not is_instance_valid(action) or not is_instance_valid(cost):
		return false
	if graphic_root.get_parent()!=view or action.get_parent()!=view or cost.get_parent()!=view or view.get_child_count()!=3:
		return false
	if action.name!=&"Action" or cost.name!=&"Cost" or graphic_root.find_children("*","MeshInstance3D",true,false).size()!=6:
		return false
	if not pad.global_basis.is_equal_approx(Basis.IDENTITY) or not view.transform.is_finite():
		return false
	var d = JSON.parse_string(FileAccess.get_file_as_string(DATA))
	if not d is Dictionary or not d.get("vertices") is Dictionary or not d.get("palette") is Dictionary:
		return false
	var amount := int(Ledger.COST.wood)
	# This exact reviewed glyph atlas covers the stock numeral only; any real
	# cost change rejects the candidate. Never interpret the reference 200.
	if int(d.get("amount",-1))!=amount or Ledger.COST.size()!=1:
		return false
	var xz := Vector2(pad.global_position.x,pad.global_position.z)
	var anchor_data: Array = d.anchor_xz
	if not xz.is_equal_approx(Vector2(float(anchor_data[0]),float(anchor_data[1]))) or absf(pad.global_position.y-float(d.anchor_terrain_y))>.0001:
		return false
	if d.vertices.size()!=ROLES.size() or d.palette.size()!=ROLES.size():
		return false
	var upload := []
	for i in range(ROLES.size()):
		var role: String = ROLES[i]
		var coords = d.vertices.get(role)
		var rgb = d.palette.get(role)
		if not coords is Array or coords.is_empty() or coords.size()%3!=0 or not rgb is Array or rgb.size()!=3:
			return false
		var verts := PackedVector3Array()
		for pos in coords:
			if not pos is Array or pos.size()!=3:
				return false
			var p := Vector3(float(pos[0]),float(pos[1]),float(pos[2]))
			if not p.is_finite() or maxf(absf(p.x),absf(p.z))>.52001 or Vector2(p.x,p.z).length()>.72:
				return false
			var sample := Terrain.sample(xz+Vector2(p.x,p.z))
			if not bool(sample.get("valid",false)) or not bool(sample.get("dry",false)):
				return false
			if absf(pad.global_position.y+p.y-float(sample.height)-float(HEIGHTS[i]))>.00015:
				return false
			verts.append(p)
		var arrays := []
		arrays.resize(Mesh.ARRAY_MAX)
		arrays[Mesh.ARRAY_VERTEX]=verts
		var mesh := ArrayMesh.new()
		mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,arrays)
		var ink := StandardMaterial3D.new()
		ink.shading_mode=BaseMaterial3D.SHADING_MODE_UNSHADED
		ink.cull_mode=BaseMaterial3D.CULL_DISABLED
		ink.albedo_color=Color(float(rgb[0]),float(rgb[1]),float(rgb[2]))
		ink.render_priority=int(PAINT_ORDER[i])
		ink.roughness=1.0
		mesh.surface_set_material(0,ink)
		upload.append(mesh)
	# Only now change one presentation node. Original authority and install
	# flags, original hierarchy and both hidden label text contracts preserved.
	var marker := Node3D.new()
	marker.name=&"DetachedGroundedPlotReference"
	marker.transform=view.transform.affine_inverse()
	for i in range(upload.size()):
		var view_layer := MeshInstance3D.new()
		view_layer.name=StringName(ROLES[i])
		view_layer.mesh=upload[i]
		view_layer.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		marker.add_child(view_layer)
	view.add_child(marker)
	graphic_root.hide()
	action.hide()
	cost.hide()
	print("DETACHED_GROUNDED_CONSTRUCTION_READY data=",DATA," tiers=",ROLES.size()," canonical_cost=",amount," visual_only=true")
	return true
