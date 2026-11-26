func admitted_post(gate: Node3D, hinge: Node3D, gate_index: int, left: bool) -> Dictionary:
	var wall := game.camp_built.get_node_or_null("R17FenceViewOnly") as Node3D
	if wall==null or wall.get_node_or_null("R17ThresholdPosts")!=null:
		return {}
	var holder := wall.get_node_or_null(Owner.POST_PARENT) as Node3D
	if not holder or holder.get_child_count()!=4 or holder.top_level or not holder.transform.is_equal_approx(Transform3D.IDENTITY):
		return {}
	var post := holder.get_node_or_null(Owner.post_name(gate_index,left)) as MeshInstance3D
	if not post or post.top_level or post.get_parent()!=holder or not post.visible or post.is_visible_in_tree()!=hinge.is_visible_in_tree():
		return {}
	if not post.basis.is_equal_approx(gate.basis) or not post.global_basis.is_equal_approx(gate.global_basis) or not post.basis.z.is_equal_approx(gate.basis.x.cross(Vector3.UP)):
		return {}
	var side := -1. if left else 1.
	var exp := hinge.global_position+gate.global_basis.x*(Owner.POST_BACKSET*side)
	var seat := ("south" if gate_index==0 else "east")+("-left" if left else "-right")
	exp.y += float(Owner.CENSUS.data.post_minus_hinge_y_m[seat])
	if exp.distance_to(post.global_position)>Owner.EPS or post.material_override!=null or post.material_overlay!=null:
		return {}
	var file := Owner.file_for(left,true)
	var report := Owner.receipt(post.mesh,file)
	if report.is_empty() or post.mesh!=load(Owner.DIR+file):
		return {}
	report.merge({"name":String(post.name),"fixed_shell_owner":true,"basis_z":[post.global_basis.z.x,post.global_basis.z.y,post.global_basis.z.z],
		"world_origin":[post.global_position.x,post.global_position.y,post.global_position.z],
		"expected_world_origin":[exp.x,exp.y,exp.z]})
	return report
