extends "res://tests/test_integrated_opening.gd"

func pt(v: Vector3) -> Array:
	return [v.x,v.y,v.z]

func sample(tag: String) -> bool:
	var pad: Node3D = game.purchase_pad_view.scene_view
	var label := pad.get_node_or_null("Cost") as Label3D
	var cam: Camera3D = game.camera
	var anim: AnimationPlayer = game.hero_locomotion.player
	var visual: Node3D
	for child in game.actor.get_children():
		if child.is_ancestor_of(anim):
			visual = child
	if visual == null or label == null or not game.actor.is_on_floor():
		return false
	var quad := []
	if label.is_visible_in_tree():
		for v in label.generate_triangle_mesh().get_faces():
			quad.append(pt(label.to_global(v)))
	var feet: Vector3 = game.actor.global_position
	var anchor: Vector3 = game.to_global(game.pad_anchor)
	var data := {"tag":tag,"tick":tick_count,"stock":game.ledger.stock.wood,"receipt":game.ledger.receipt,"camp":game.camp_built.visible,"pad_visible":pad.is_visible_in_tree(),"visible":label.is_visible_in_tree(),"text":label.text,"quad":quad,"feet":pt(feet),"anchor":pt(anchor),"distance":feet.distance_to(anchor),"yaw":game.actor.rotation.y,"animation":anim.current_animation,"animation_t":anim.current_animation_position,"cam_position":pt(cam.global_position),"camera_back":pt(cam.global_basis.z),"camera_size":cam.size,"camera_projection":cam.projection}
	var out := OS.get_environment("HVN_OUT")
	if not quad.is_empty() and not output_surface(visual.find_children("*", "MeshInstance3D", true, false), out, tag):
		return false
	print("PAD_ROUTE ", JSON.stringify(data))
	return true

func output_surface(parts: Array[Node], directory: String, tag: String) -> bool:
	var rows := []
	for child in parts:
		var mesh := child as MeshInstance3D
		if not mesh.is_visible_in_tree():
			continue
		if mesh.mesh == null or mesh.mesh.get_blend_shape_count() != 0 or mesh.skin == null:
			return false
		var skel := mesh.get_node_or_null(mesh.skeleton) as Skeleton3D
		if skel == null or mesh.skin.get_bind_count() != 66:
			return false
		var matrices: Array[Transform3D] = []
		skel.force_update_all_bone_transforms()
		for j in range(mesh.skin.get_bind_count()):
			var k := skel.find_bone(String(mesh.skin.get_bind_name(j))) if mesh.skin.get_bind_name(j) != &"" else mesh.skin.get_bind_bone(j)
			if k < 0:
				return false
			matrices.append(skel.get_bone_global_pose(k) * mesh.skin.get_bind_pose(j))
		for i in range(mesh.mesh.get_surface_count()):
			if mesh.mesh.surface_get_primitive_type(i) != Mesh.PRIMITIVE_TRIANGLES:
				return false
			var row: Array = mesh.mesh.surface_get_arrays(i)
			var v: PackedVector3Array = row[Mesh.ARRAY_VERTEX]
			var b: PackedInt32Array = row[Mesh.ARRAY_BONES]
			var w: PackedFloat32Array = row[Mesh.ARRAY_WEIGHTS]
			var ix: PackedInt32Array = row[Mesh.ARRAY_INDEX]
			var width := b.size() / float(v.size())
			if width not in [4.,8.] or w.size()!=b.size() or ix.is_empty():
				return false
			var fitted := []
			for a in range(v.size()):
				var pr := Vector3.ZERO
				var sum := 0.
				for j in range(int(width)):
					var h := a*int(width)+j
					if w[h] == 0.:
						continue
					pr += (matrices[b[h]] * v[a])*w[h]
					sum += w[h]
				if absf(sum-1.)>.0002:
					return false
				fitted.append(pt(mesh.to_global(pr)))
			rows.append({"positions":fitted,"triangles":Array(ix)})
	var f := FileAccess.open(directory.path_join(tag+".json"),FileAccess.WRITE)
	if rows.is_empty() or f == null:
		return false
	f.store_string(JSON.stringify(rows))
	return true

func collect() -> bool:
	if not await travel(game.wood_anchors["wood-b"]) or not await travel(game.wood_anchors["wood-c"]):
		return false
	if not await travel(game.point([-.35,6.])) or not await travel(game.point([-.85,6.])):
		return false
	if game.ledger.stock.wood != 2 or not game.resource_tree.can_address(game.actor.global_position,game.tree_facing()):
		return false
	for i in range(3):
		press(KEY_F)
		await tick(21)
	if not await travel(game.point([0.,6.])):
		return false
	await tick(58)
	return game.ledger.stock.wood == 3 and game.resource_tree.phase == "credited"

func station(dist: float) -> Vector3:
	var xz: Array = game.layout.pad_xz
	return game.point([xz[0],xz[1]+dist])

func run() -> void:
	root.size = Vector2i(1280,720)
	game=GAME.instantiate()
	root.add_child(game)
	if not game.bound or game.persist_requested:
		quit(2)
		return
	await tick(25)
	var funded := OS.get_environment("HVN_ROUTE")=="funded"
	if funded:
		check(await collect(),"earn all three wood only through ordinary scene-handler motion/chop")
	if failures:
		quit(1)
		return
	check(await travel(station(2.35)),"arrive outside south line")
	check(await travel(station(1.60)),"straight northbound to far control")
	check(game.ledger.stock.wood == (3 if funded else 0) and game.ledger.receipt.is_empty(),"far pre-payment")
	check(sample("far"),"capture far active exact hero and label")
	check(await travel(station(.90)),"same south line to 90 cm")
	check(game.ledger.stock.wood == (3 if funded else 0) and game.ledger.receipt.is_empty(),"near pre-payment unmodified ledger")
	check(sample("near"),"capture near active exact hero and label")
	if funded and failures==0:
		check(await travel(station(.79)),"move closer still outside live reach")
		check(game.ledger.stock.wood==3 and game.ledger.receipt.is_empty() and sample("before"),"capture last commanded funded outside stance")
		check(await travel(game.pad_anchor),"ordinary continued northbound movement enters purchase")
		check(game.ledger.stock.wood==0 and game.ledger.receipt.get("typed_debit",{})=={"wood":3} and game.camp_built.visible,"charged exactly original three wood")
		check(sample("after") and not game.purchase_pad_view.scene_view.is_visible_in_tree(),"pad and label vanish after receipt")
	quit(1 if failures else 0)
