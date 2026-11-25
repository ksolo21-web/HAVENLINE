extends "res://tests/test_integrated_opening.gd"
const CrownPath := "res://assets/studio/starter_ground_wood_lod.glb"
const CENTER_XZ := Vector2(-5.25, 8.70)
const PITCH := 0.105
func find_crown() -> Mesh:
	var doc := GLTFDocument.new()
	var state := GLTFState.new()
	if doc.append_from_buffer(FileAccess.get_file_as_bytes(CrownPath), "res://assets/studio", state) != OK:
		return null
	for n: GLTFNode in state.get_nodes():
		if String(n.original_name) == "Pickup LOD - Crown log" and n.mesh == 0:
			return state.get_meshes()[n.mesh].mesh.get_mesh()
	return null

func bounds_clear(mesh_bounds: AABB, pose: Transform3D, shapes: Array[RID]) -> Array:
	var box := BoxShape3D.new()
	box.size = mesh_bounds.size
	var q := PhysicsShapeQueryParameters3D.new()
	q.shape = box
	q.collision_mask = 1
	q.exclude = shapes
	q.transform = Transform3D(pose.basis, pose * mesh_bounds.get_center())
	return game.actor.get_world_3d().direct_space_state.intersect_shape(q,32)

func names(hits: Array) -> Array:
	var out: Array
	for row in hits:
		var body: Node = row.get("collider")
		out.append(String(body.get_path()) if is_instance_valid(body) else "<unknown>")
	return out

func arrive(mesh_bounds: AABB, xz: Vector2) -> Transform3D:
	var y := -INF
	for x in [-.5, 0., .5]:
		for z in [-.5, 0., .5]:
			var p := xz + Vector2(x * mesh_bounds.size.x,z * mesh_bounds.size.z)
			var found := Terrain.sample(p)
			check(found.valid and found.dry and not found.crossing_reserved, "exact proposed footprint sample is dry and ordinary")
			y = maxf(y, float(found.height))
	return Transform3D(Basis.IDENTITY, Vector3(xz.x-mesh_bounds.get_center().x, y + .005 - mesh_bounds.position.y, xz.y-mesh_bounds.get_center().z))

func run() -> void:
	game = GAME.instantiate()
	root.add_child(game)
	check(game.bound and not game.persist_requested, "admit exact integrated ephemeral scene")
	if failures:
		quit(3)
		return
	await tick(10)
	check(await travel(game.wood_anchors["wood-b"]) and await travel(game.wood_anchors["wood-c"]), "obtain two live loose credits through original native route")
	check(await travel(game.point([-.35, 6.0])) and await travel(game.point([-.85, 6.0])), "native approach and face tree")
	for i in range(3):
		press(KEY_F)
		await tick(21)
	check(await travel(game.point([0.0, 6.0])), "move out of original tree fall corridor")
	await tick(58)
	check(game.ledger.stock.wood == 3, "all three opening credits produced by normal rules")
	check(await travel(game.pad_anchor), "pay via original ordinary source and walk")
	await tick(3)
	check(game.camp_built.visible and not game.ledger.receipt.is_empty() and game.ledger.stock.wood == 0, "real paid state exhausts stock")
	check(game.camp_colliders.size() == 7 and not game.wood_stock_view.payload.is_visible_in_tree(), "authored six walls plus hearth, no carried bundle after payment")
	if failures:
		quit(3)
		return
	var ledger_start := var_to_bytes(game.ledger.snapshot())
	var stock = game.wood_stock_view
	var sentinel := Node3D.new()
	sentinel.name = "DetachedUntouchedRowWitness"
	stock.add_child(sentinel)
	sentinel.position = Vector3(.25,.05,0)
	var identity := sentinel.get_instance_id()
	var original := sentinel.transform
	var mesh := find_crown()
	check(mesh != null and mesh.get_surface_count() == 2, "exact original crown primitive, both material surfaces")
	if failures:
		quit(3)
		return
	var mesh_bounds := mesh.get_aabb()
	check(mesh_bounds.size.z < PITCH, "two full-size log envelope widths do not overlap at prior pitch")
	var logs: Array[MeshInstance3D] = []
	var landing: Array[Transform3D] = []
	var outside_actor_hits: Array
	var actor_excludes: Array[RID] = [game.actor.get_rid()]
	for i in range(2):
		var load_mesh := MeshInstance3D.new()
		load_mesh.name = "DetachedClearanceGauge%d" % i
		load_mesh.mesh = mesh
		game.add_child(load_mesh)
		var dest := arrive(mesh_bounds,CENTER_XZ + Vector2(0,(i-.5)*PITCH))
		load_mesh.global_transform = dest
		logs.append(load_mesh)
		landing.append(dest)
		var hits := names(bounds_clear(mesh_bounds,dest,actor_excludes))
		outside_actor_hits.append(hits)
		check(hits.is_empty(), "static candidate envelope %d clears actual paid scene layer-1 bodies" % i)
	check(not logs[0].get_aabb().intersects((landing[0].affine_inverse()*landing[1])*logs[1].get_aabb()), "individual original-scale landing envelope does not intersect its peer")
	var want_xz := [CENTER_XZ.x+3.25,CENTER_XZ.y-5.8]
	check(await travel(game.point(want_xz)), "player can walk to provisional occupied footprint in actual paid camp")
	var actor_block: Array
	for i in range(2):
		var hits := names(bounds_clear(mesh_bounds,landing[i],[]))
		actor_block.append(hits)
		check(game.actor.get_path() in hits or String(game.actor.get_path()) in hits, "same candidate envelope %d is occupied by a player at its center" % i)
	var wall: Node3D = game.camp_colliders[0]
	var hearth: Node3D = game.camp_colliders[6]
	var wall_center := Transform3D(Basis.IDENTITY,wall.global_position-mesh_bounds.get_center())
	var hearth_center := Transform3D(Basis.IDENTITY,hearth.global_position+Vector3.UP*.675-mesh_bounds.get_center())
	var wall_hits := names(bounds_clear(mesh_bounds,wall_center,actor_excludes))
	var hearth_hits := names(bounds_clear(mesh_bounds,hearth_center,actor_excludes))
	check(String(wall.get_path()) in wall_hits, "known solid paid wall rejects same log envelope")
	check(String(hearth.get_path()) in hearth_hits, "known solid paid hearth rejects same log envelope")
	check(sentinel.get_parent() == stock and sentinel.get_instance_id() == identity and sentinel.transform == original and sentinel.is_visible_in_tree(), "test-only untouched row custody and local transform unchanged")
	check(ledger_start == var_to_bytes(game.ledger.snapshot()) and not stock.payload.is_visible_in_tree(), "no garnish wood, accepted receipt and original presentation untouched")
	print("CLEARANCE ",JSON.stringify({"checks":checks,"failures":failures,"actual_stock":game.ledger.stock,"pitch_m":PITCH,"log_size_m":[mesh_bounds.size.x,mesh_bounds.size.y,mesh_bounds.size.z],"static_hits":outside_actor_hits,"occupied_hits":actor_block,"wall_control":wall_hits,"hearth_control":hearth_hits}))
	quit(0 if failures == 0 else 1)
