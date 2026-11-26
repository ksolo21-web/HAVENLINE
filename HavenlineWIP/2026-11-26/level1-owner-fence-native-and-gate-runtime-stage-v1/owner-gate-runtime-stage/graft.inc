const Owner = preload("res://previews/clearance_gate/owner_mesh.gd")
const LEFT_LEAF: Mesh = preload("res://previews/clearance_gate/owner_assets/GateLeaf.obj")
const RIGHT_LEAF: Mesh = preload("res://previews/clearance_gate/owner_assets/GateLeaf_Right.obj")
const LEFT_POST: Mesh = preload("res://previews/clearance_gate/owner_assets/ThresholdPost.obj")
const RIGHT_POST: Mesh = preload("res://previews/clearance_gate/owner_assets/ThresholdPost_Right.obj")
const GRAFT_IDS := ["gate-south", "gate-east"]

func setup_camp() -> void:
	super.setup_camp()
	var reason := _graft_owner_four()
	if not reason.is_empty():
		# A bad binding is not an accepted visual fallback. No route or frames are emitted.
		printerr("OWNER33035_GATE_REJECT ",reason)
		if camp_built:
			camp_built.hide()
		get_tree().quit(2)
		return
	print("OWNER33035_GATE_GRAFT mounted-four-leaves-four-posts")

func _graft_owner_four() -> String:
	if scene_file_path!="res://previews/clearance_gate/clearance_gate_view.tscn" or OS.get_cmdline_user_args().has(StockReview.REVIEW_FLAG):
		return "unadmitted-scene"
	if not StockReview._translation_only(transform) or not StockReview._translation_only(global_transform):
		return "root-frame"
	if not camp_built or camp_built.get_parent()!=self or camp_built.top_level or not Mount._frame_matches(camp_built.transform,Transform3D.IDENTITY):
		return "camp-frame"
	var shell := camp_built.get_node_or_null("R17FenceViewOnly") as Node3D
	if not shell or shell.get_child_count()!=2 or not Mount._frame_matches(shell.transform,Transform3D.IDENTITY):
		return "old-wall-shell"
	var old_posts := shell.get_node_or_null("R17ThresholdPosts") as MultiMeshInstance3D
	if not old_posts or not old_posts.multimesh or old_posts.multimesh.instance_count!=4 or not Mount._frame_matches(old_posts.transform,Transform3D.IDENTITY):
		return "old-post-custody"
	if gates.size()!=2 or not _terrain_custody():
		return "terrain-and-gate-count"
	var staged: Array[Dictionary] = []
	for index in range(2):
		var gate := gates[index] as Gate
		if gate==null or gate.get_parent()!=camp_built or gate.top_level or gate.gate_id!=GRAFT_IDS[index] or not Mount._gate_frame_valid(gate):
			return "gate-frame"
		var seats := StockReview._seats_for(gate)
		if seats.is_empty():
			return "terrain-seats"
		var offsets: Vector2 = seats.offsets
		var axis := gate.basis.x.normalized()
		var cross := gate.basis.z.normalized()
		if not axis.is_equal_approx(gate.basis.x) or not cross.is_equal_approx(axis.cross(Vector3.UP)) or not gate.basis.y.is_equal_approx(Vector3.UP):
			return "gate-outward-or-scale"
		for left: bool in [true,false]:
			var side := -1.0 if left else 1.0
			var row := Mount._prepare_side(gate,left,offsets.x if left else offsets.y)
			if row.is_empty() or not row.placeholder.visible:
				return "original-pivot-body-collider"
			var leaf_mesh: Mesh = LEFT_LEAF if left else RIGHT_LEAF
			var post_mesh: Mesh = LEFT_POST if left else RIGHT_POST
			if Owner.receipt(leaf_mesh,Owner.file_for(left,false)).is_empty() or Owner.receipt(post_mesh,Owner.file_for(left,true)).is_empty():
				return "exact-native-census"
			var hinge: Node3D = row.pivot
			var at := gate.position+axis*(1.20+Owner.POST_BACKSET)*side
			at.y = _r17_seat(at-axis*Owner.POST_SEAT_X,at+axis*Owner.POST_SEAT_X,cross,Owner.POST_SEAT_Z)
			var before := old_posts.multimesh.get_instance_transform(index*2+(0 if left else 1))
			if before.origin.distance_to(at)>Owner.EPS:
				return "existing-post-seat-drift"
			var seat_key := ("south" if index==0 else "east")+("-left" if left else "-right")
			if absf((at.y-hinge.global_position.y)-float(Owner.CENSUS.data.post_minus_hinge_y_m[seat_key]))>Owner.EPS:
				return "static-post-proof-seat-drift"
			row.owner_leaf=leaf_mesh
			row.owner_post=post_mesh
			row.owner_post_frame=Transform3D(gate.basis,at)
			row.owner_post_name=Owner.post_name(index,left)
			staged.append(row)
	if staged.size()!=4:
		return "mount-count"
	# Replacements are render-only; the original old threshold mesh is not in the resulting tree.
	shell.remove_child(old_posts)
	old_posts.free()
	var thresholds := Node3D.new()
	thresholds.name=Owner.POST_PARENT
	shell.add_child(thresholds)
	for row in staged:
		var post := MeshInstance3D.new()
		post.name=row.owner_post_name
		post.mesh=row.owner_post
		post.transform=row.owner_post_frame
		thresholds.add_child(post)
		var leaf := MeshInstance3D.new()
		leaf.name=Mount.NAME
		leaf.mesh=row.owner_leaf
		row.pivot.add_child(leaf)
	for row in staged:
		row.placeholder.hide()
	return ""
