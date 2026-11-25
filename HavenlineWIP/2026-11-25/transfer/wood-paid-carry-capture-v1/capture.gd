extends "res://tests/test_integrated_opening.gd"

func pt(v: Vector3) -> Array:
	return [v.x,v.y,v.z]

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

func tf(t: Transform3D) -> Dictionary:
	return {"basis_cols":[pt(t.basis.x),pt(t.basis.y),pt(t.basis.z)],"origin":pt(t.origin)}

func local_box(b: AABB) -> Dictionary:
	return {"position":pt(b.position),"size":pt(b.size)}

func exact_paid_cut(start: int) -> bool:
	if not await travel(game.point([-.35,6.])) or not await travel(game.point([-.85,6.])):
		return false
	if not game.resource_tree.can_address(game.actor.global_position, game.tree_facing()) or game.ledger.stock.wood!=start:
		return false
	for i in range(3):
		press(KEY_F)
		await tick(21)
	if game.resource_tree.phase != "falling" or game.ledger.stock.wood!=start:
		return false
	if not await travel(game.point([0.,6.])):
		return false
	for i in range(65):
		if game.resource_tree.phase=="credited":
			break
		await tick(1)
	return game.resource_tree.phase=="credited" and game.ledger.stock.wood==start+1 and game.ledger.pine_occurrences==start+1

func capture() -> bool:
	var native_actor: CharacterBody3D = game.actor
	var anim: AnimationPlayer=game.hero_locomotion.player
	var visual: Node3D
	for child in native_actor.get_children():
		if child.is_ancestor_of(anim):
			visual=child
	var carry: Node3D = game.wood_stock_view
	var bundle: Node3D=carry.payload
	if bundle==null or not bundle.is_visible_in_tree() or not native_actor.is_on_floor() or visual==null:
		return false
	var dir:=OS.get_environment("HVN_OUT")
	if not output_surface(visual.find_children("*","MeshInstance3D",true,false),dir,"hero_world"):
		return false
	var parts:= []
	for item in bundle.find_children("*","MeshInstance3D",true,false):
		var mesh:=item as MeshInstance3D
		var ss:=[]
		for i in mesh.mesh.get_surface_count():
			var m:=mesh.get_active_material(i)
			ss.append(m.resource_name if m != null else "")
		parts.append({"name":mesh.name,"world":tf(mesh.global_transform),"aabb":local_box(mesh.get_aabb()),"surface_role_names":ss,"visible":mesh.is_visible_in_tree()})
	var leaves:=[]
	for item in game.gates:
		var leaf:=[]
		for name in ["HingeLeft","HingeRight"]:
			var h: Node3D=item.get_node(name)
			var b:=h.get_child(0) as AnimatableBody3D
			var c:=b.get_child(0) as CollisionShape3D
			var sh:=c.shape as BoxShape3D
			leaf.append({"hinge":name,"hinge_world":tf(h.global_transform),"body_world":tf(b.global_transform),"shape_world":tf(c.global_transform),"size":pt(sh.size),"layer":b.collision_layer})
		leaves.append({"gate_id":item.gate_id,"world":tf(item.global_transform),"in_player_reach":item.interaction_in_range(native_actor.global_position),"outside_freeze_box":item.sweep_clear(native_actor.global_position,float(game.layout.actor_radius)),"angle":item.angle,"target_open":item.target_open,"holding_for_occupancy":item.holding_for_occupancy,"leaf_boxes":leaf})
	var shapes:=[]
	for ch in native_actor.get_children():
		if ch is CollisionShape3D and ch.shape is CapsuleShape3D:
			shapes.append({"world":tf(ch.global_transform),"radius":ch.shape.radius,"height":ch.shape.height})
	var data={"tick":tick_count,"paid_receipt":game.ledger.receipt,"wood_stock":game.ledger.stock.wood,"pine_occurrences":game.ledger.pine_occurrences,"actors_native_grounded":native_actor.is_on_floor(),"actor_world":tf(native_actor.global_transform),"actor_collisions":shapes,"actor_velocity":pt(native_actor.velocity),"settled_animation":anim.current_animation,"settled_animation_time":anim.current_animation_position,"hero_root_world":tf(visual.global_transform),"gates":leaves,
		"carry_root_world":tf(carry.global_transform),"original_bundle_world":tf(bundle.global_transform),"original_bundle_parent_is_stock_view":bundle.get_parent()==carry,"original_bundle_visible":bundle.is_visible_in_tree(),"native_stock_readout":carry.counter.text,"native_presented_units":carry.presented_units,"original_fit":local_box(carry.fitted_bounds),"original_measured_hero":local_box(carry.measured_actor),"actual_bundle_mesh_parts":parts,"carry_node_child_names":Array(carry.get_children()).map(func(item):return str(item.name)),
		"path_label":"original South inner [0,2] sampling checkpoint only","no_persistence":not game.persist_requested,"has_receiver":false}
	print("PAID_CARRY ",JSON.stringify(data))
	return native_actor.velocity.length()<.01 and not shapes.is_empty() and carry.presented_units==2 and leaves[0]["in_player_reach"] and leaves[0]["outside_freeze_box"] and leaves[0]["target_open"] and is_equal_approx(float(leaves[0]["angle"]),PI*.5)

func run() -> void:
	root.size=Vector2i(1280,720)
	game=GAME.instantiate()
	root.add_child(game)
	if not game.bound or game.persist_requested or game.persist_blocked:
		quit(2)
		return
	await tick(25)
	check(await collect(),"three original earned materials")
	check(await travel(game.point([0.,3.30])),"approach beyond purchase reach")
	check(await travel(game.pad_anchor) and game.ledger.has_exact_paid_hearth() and game.ledger.stock.wood==0,"actual three wood paid exactly once")
	check(await travel(game.point([0.,2.])),"native South interior route point")
	check(game.gates[0].interaction_in_range(game.actor.global_position),"native gate in reach")
	press(KEY_E)
	await tick(70)
	check(is_equal_approx(game.gates[0].angle,PI*.5),"South leaves fully open")
	check(await travel(game.point([0.,6.])),"ordinary exit through South gate")
	if failures:
		quit(1)
		return
	for i in range(2):
		for k in range(320):
			if game.resource_tree.phase=="rooted":
				break
			await tick(1)
		check(game.resource_tree.phase=="rooted" and game.resource_tree.strikes==0 and game.ledger.stock.wood==i,"real regrowth with no passive award")
		check(await exact_paid_cut(i),"exact ordinary paid repeat cut yields one")
		if failures:
			quit(1)
			return
	var before := var_to_bytes(game.ledger.snapshot())
	check(await travel(game.point([0.,6.])),"return to actual outer South route waypoint")
	check(await travel(game.point([0.,2.])),"return through opened South gate to original source checkpoint")
	await tick(12)
	check(var_to_bytes(game.ledger.snapshot())==before and game.ledger.stock.wood==2 and game.ledger.pine_occurrences==2,"no transfer or mutation on returning with two real wood")
	check(capture(),"capture exact primary sight/actor, stock and gates in settled paid checkpoint")
	print("CAPTURE_COUNT ",checks," failures ",failures," grounded ",grounded)
	quit(1 if failures else 0)
