extends "res://tests/test_integrated_opening.gd"
## Detached observer plus two proposed pieces and one diagnostic second row.
## No mutation of purchase, stock, authored source meshes or project authority.
const CrownPath := "res://assets/studio/starter_ground_wood_lod.glb"
const Pitch := .105
const StockFurnaceRelative := Vector2(-2.0, 2.30) # same-pin legacy crate + stock offset minus legacy furnace
const ArcSeconds := .285
const ArcHeight := .30
const Lift := .005
const Faults := ["clean", "cached-origin", "surface-override"]
var movers: Array[MeshInstance3D]
var launch_records: Array[Dictionary]
var targets: Array[Transform3D]
var material_refs: Array[Material]
var landing_mount: Node3D
var flight_mount: Node3D
var diagnostic: MeshInstance3D
var diagnostic_pose: Transform3D
var diagnostic_material: Material
var fault := "clean"
var timestamps: Array[Dictionary]
var clock_ticks := 0
var actor_departure: Transform3D
var source_views: Array[String]
var material_checks := 0
var observing := false
var terrain_sites: Array[Dictionary]
var selected_shift := Vector2.ZERO

func tick(n: int) -> void:
	for i in range(n):
		await super.tick(1)
		if observing:
			clock_ticks += 1
			advance_pieces()
			witness_inventory()

func ground_far(point: Vector2) -> Dictionary:
	return Terrain.sample(point)

func find_crown() -> Mesh:
	var doc := GLTFDocument.new()
	var state := GLTFState.new()
	if doc.append_from_buffer(FileAccess.get_file_as_bytes(CrownPath), "res://assets/studio", state) != OK:
		return null
	for n: GLTFNode in state.get_nodes():
		if String(n.original_name) == "Pickup LOD - Crown log" and n.mesh == 0:
			return state.get_meshes()[n.mesh].mesh.get_mesh()
	return null

func vec(v: Vector3) -> Array:
	return [v.x, v.y, v.z]

func materials_ok(n: MeshInstance3D) -> bool:
	if n.mesh.get_surface_count() != material_refs.size():
		return false
	for i in range(material_refs.size()):
		material_checks += 1
		if n.get_active_material(i) != material_refs[i]:
			return false
	return true

func make_target(selected: Vector2, box: AABB) -> Transform3D:
	var high := -INF
	var low := INF
	for x in [-box.size.x / 2.0, 0.0, box.size.x / 2.0]:
		for z in [-box.size.z / 2.0, 0.0, box.size.z / 2.0]:
			var sample := ground_far(selected + Vector2(x,z))
			if not bool(sample.valid) or not bool(sample.dry) or bool(sample.crossing_reserved):
				terrain_sites.append({"xz":[selected.x,selected.y],"excluded":"sample invalid, wet or reserved"})
				return Transform3D(Basis.IDENTITY, Vector3.INF)
			high = maxf(high, float(sample.height))
			low = minf(low, float(sample.height))
	terrain_sites.append({"xz":[selected.x,selected.y],"height_span_m":high-low,"accepted":high-low<=.025})
	if high - low > .025:
		return Transform3D(Basis.IDENTITY, Vector3.INF)
	return Transform3D(Basis.IDENTITY, game.to_global(Vector3(selected.x, high + Lift - box.position.y, selected.y)) - Vector3(box.get_center().x,0,box.get_center().z))

func begin_piece(i: int, request_pose: Transform3D) -> void:
	var node := movers[i]
	var live := node.global_transform
	var used := request_pose if fault == "cached-origin" and i == 1 else live
	node.reparent(flight_mount, true)
	node.global_transform = used
	var transition_error := live.origin.distance_to(node.global_position)
	var transition_basis := live.basis.is_equal_approx(node.global_basis)
	if fault == "surface-override" and i == 1:
		var bad := StandardMaterial3D.new()
		bad.albedo_color = Color.MAGENTA
		node.set_surface_override_material(1, bad)
	check(transition_error < .00001 and transition_basis, "launch %s preserves live origin and basis (not request-time)" % i)
	check(materials_ok(node), "launch %s retains both active materials/surface roles" % i)
	launch_records.append({"pose": node.global_transform, "tick": clock_ticks})
	timestamps.append({"launch":i, "tick":clock_ticks,"expected":vec(live.origin),"actual":vec(node.global_position),"origin_error_m":transition_error,"candidate_landing":vec(targets[i].origin)})

func advance_pieces() -> void:
	for i in launch_records.size():
		var node := movers[i]
		if node.get_parent() == landing_mount:
			continue
		var k := clampf((clock_ticks - int(launch_records[i].tick)) / 60.0 / ArcSeconds, 0.0, 1.0)
		var start: Transform3D = launch_records[i].pose
		var target := targets[i]
		var t := start.interpolate_with(target,k)
		t.origin.y += 4.0 * ArcHeight * k * (1.0-k)
		node.global_transform = t
		if k == 1.0:
			node.reparent(landing_mount, true)
			check(node.global_position.distance_to(target.origin) < .00001 and node.global_basis.is_equal_approx(target.basis), "candidate landing %s full transform" % i)
			check(materials_ok(node), "landing %s retains both active materials/surface roles" % i)

func witness_inventory() -> void:
	check(diagnostic.get_parent() == game.wood_stock_view and diagnostic.transform == diagnostic_pose and diagnostic.is_visible_in_tree() and diagnostic.get_active_material(0) == diagnostic_material, "other diagnostic row retains actor-local slot identity, position and material")
	var seen_ids: Dictionary
	for node in movers:
		var seen := 0
		for owner in [game.wood_stock_view, flight_mount, landing_mount]:
			if node in owner.get_children():
				seen += 1
		check(seen == 1 and node.is_visible_in_tree(), "known physical log has one visible owning mount")
		seen_ids[node.get_instance_id()] = true
	check(seen_ids.size() == 2,"two log identities remain distinct")

func finish(code: int) -> void:
	print("ANCHOR_RESULT ", JSON.stringify({"scenario":fault,"checks":checks,"failures":failures,"clock_ticks":clock_ticks,"active_material_checks":material_checks,"launches":timestamps,"surface_roles":source_views,"terrain_sites":terrain_sites,"selected_shift_m":[selected_shift.x,selected_shift.y],"scope":"exact live source scene; detached proposed anchor; no authored receiver or render"}))
	quit(code)

func run() -> void:
	var args := OS.get_cmdline_user_args()
	fault = args[0] if args.size() > 0 else "clean"
	if fault not in Faults:
		quit(2)
		return
	game = GAME.instantiate()
	root.add_child(game)
	check(game.bound and not game.persist_requested, "exact integrated preview normal entry without saves")
	if failures:
		finish(1)
		return
	await tick(10)
	check(await travel(game.wood_anchors["wood-b"]), "ordinary movement into actual first pickup")
	check(await travel(game.wood_anchors["wood-c"]), "ordinary movement into actual second pickup")
	check(game.ledger.stock.wood == 2 and game.ledger.receipt.is_empty() and not game.camp_built.visible, "two native stock before paying the separate pad")
	check(await travel(game.point([0.0, 2.0])), "native pre-camp approach near proposed stock area")
	var ledger_before := var_to_bytes(game.ledger.snapshot())
	var carry: Node3D = game.wood_stock_view
	var original: Node3D = carry.payload
	check(original != null and original.is_visible_in_tree(), "real live TechnicalWoodBundleRepresentative is present")
	var mesh := find_crown()
	check(mesh != null and mesh.get_surface_count() == 2, "exact independent crown primitive has both surfaces")
	if failures:
		finish(1)
		return
	var box := mesh.get_aabb()
	var center: Vector3 = carry.fitted_bounds.get_center()
	check(box.size.z < Pitch and box.size.x <= carry.fitted_bounds.size.x, "two unscaled crowns fit the measured carry envelope by depth")
	var inside: Vector3 = game.point([StockFurnaceRelative.x, StockFurnaceRelative.y])
	# Fixed tiny sequence keeps the historical screen as a result, never promotes a
	# farther or better sample silently. Nearest alternative from the bounded set only.
	for delta: Vector2 in [Vector2.ZERO,Vector2(.2,0),Vector2(-.2,0),Vector2(0,.2),Vector2(0,-.2),Vector2(.4,0),Vector2(-.4,0),Vector2(0,.4),Vector2(0,-.4),Vector2(.6,0),Vector2(-.6,0),Vector2(0,.6),Vector2(0,-.6)]:
		var trial: Array[Transform3D]
		for i in range(2):
			var shifted := Vector2(inside.x, inside.z) + delta + Vector2(0,(i-.5)*Pitch)
			trial.append(make_target(shifted,box))
		if trial[0].is_finite() and trial[1].is_finite():
			selected_shift = delta
			targets = trial
			break
	check(targets.size() == 2, "both independent candidate landings on existing dry terrain; 9 support samples per footprint")
	if failures:
		finish(1)
		return
	var source_names: Array[String]
	for j in range(mesh.get_surface_count()):
		var m := mesh.surface_get_material(j)
		material_refs.append(m)
		source_names.append(m.resource_name if m != null else "")
	source_views = source_names
	check(source_views[0] != source_views[1] and not source_views.has(""), "crown bark and end material role names are distinct and recorded")
	# Show visual candidate separately without changing the published count or moving the original bundle.
	original.hide()
	for i in range(2):
		var node := MeshInstance3D.new()
		node.name = "ProposedFullScaleCrown%d" % i
		node.mesh = mesh
		carry.add_child(node)
		node.position = center - box.get_center() + Vector3(0,0,(i-.5)*Pitch)
		movers.append(node)
		check(materials_ok(node), "source crown %s preserves active bark/end roles" % i)

	diagnostic = MeshInstance3D.new()
	diagnostic.mesh = SphereMesh.new()
	diagnostic_material = StandardMaterial3D.new()
	diagnostic.material_override = diagnostic_material
	carry.add_child(diagnostic)
	diagnostic.position = center + Vector3(.25,0,0)
	diagnostic_pose = diagnostic.transform
	flight_mount = Node3D.new()
	flight_mount.name = "DetachedProposedFlight"
	game.add_child(flight_mount)
	landing_mount = Node3D.new()
	landing_mount.name = "DetachedLegacyDerivedGroundCandidate"
	game.add_child(landing_mount)
	actor_departure = game.actor.global_transform
	var request_late := movers[1].global_transform
	begin_piece(0,movers[0].global_transform)
	witness_inventory()

	# Real ordinary touch motion using the same handler and native physics.
	observing = true
	check(await travel(game.point([-.40, 1.72]), 10), "ordinary grounded step and turn while one piece is already flying")
	check(game.actor.is_on_floor() and actor_departure.origin.distance_to(game.actor.global_position) > .30 and not actor_departure.basis.is_equal_approx(game.actor.global_basis), "actual actor moved and turned between the departures")
	timestamps.append({"late_live_displacement_m": request_late.origin.distance_to(movers[1].global_position), "actor_displacement_m":actor_departure.origin.distance_to(game.actor.global_position)})
	begin_piece(1,request_late)
	witness_inventory()
	await tick(20)
	observing = false
	check(movers[0].get_parent() == landing_mount and movers[1].get_parent() == landing_mount, "both pieces finish inside the proposed ground mount")
	check(var_to_bytes(game.ledger.snapshot()) == ledger_before, "witness did not touch inventory/payment/receipt")
	check(game.camera.current and game.camera.projection == Camera3D.PROJECTION_ORTHOGONAL, "authored scene camera exists, headless only")
	finish(1 if failures else 0)
