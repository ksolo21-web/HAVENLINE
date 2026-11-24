extends SceneTree
const Base = preload("res://opening.tscn")
const Combined = preload("res://previews/integrated_opening.tscn")
const Review = preload("res://previews/gate_pair_study/gate_art_review.gd")
const Mount = preload("res://previews/gate_pair_study/gate_pair_mount.gd")
const Gate = preload("res://technical_gate.gd")
var passed := 0
var failed := 0

func _initialize() -> void:
	call_deferred("run")

func check(c: bool, label: String) -> void:
	passed += int(c)
	failed += int(not c)
	print(("PASS " if c else "FAIL ") + label)

func _count(game, want_art: bool) -> bool:
	if game.gates.size() != 2:
		return false
	for gate: Gate in game.gates:
		for path in ["HingeLeft", "HingeRight"]:
			var pivot := gate.get_node(path) as Node3D
			var body := pivot.get_child(0) as AnimatableBody3D
			var placeholder := body.get_child(1) as MeshInstance3D
			var art := pivot.get_node_or_null(NodePath(String(Mount.NAME))) as MeshInstance3D
			if (art != null) != want_art or placeholder.visible == want_art:
				return false
			if art != null and (art.get_parent() != pivot or art.transform != Transform3D.IDENTITY):
				return false
	return true

func _mechanics(game) -> Array:
	var out: Array = []
	for gate: Gate in game.gates:
		var row: Array = [gate.gate_id,str(gate.transform),gate.active,gate.visible,gate.target_open,gate.angle,gate.holding_for_occupancy]
		for path in ["HingeLeft", "HingeRight"]:
			var pivot := gate.get_node(path) as Node3D
			var body := pivot.get_child(0) as AnimatableBody3D
			var collider := body.get_child(0) as CollisionShape3D
			row.append([str(pivot.transform),str(body.transform),str(collider.transform),str((collider.shape as BoxShape3D).size),body.collision_layer,body.collision_mask])
		out.append(row)
	return out

func run() -> void:
	var mode := Review.REVIEW_FLAG in OS.get_cmdline_user_args()
	var base := Base.instantiate()
	root.add_child(base)
	base.set_physics_process(false)
	check(_count(base, false), "default uses technical art even with review flag")
	base.free()
	var game = Combined.instantiate()
	if "--l1-test-gate-art-translated" in OS.get_cmdline_user_args():
		game.position = Vector3(2, 1.1, -3)
	root.add_child(game)
	game.set_physics_process(false)
	check(game.bound and _count(game, mode), "flag switches both combined gates and both leaves only")
	for gate: Gate in game.gates:
		check(not gate.active and not gate.visible, "pregrant hidden and collision locked " + gate.gate_id)
		if mode:
			for path in ["HingeLeft", "HingeRight"]:
				var p := gate.get_node(path) as Node3D
				var n := p.get_node(NodePath(String(Mount.NAME))) as MeshInstance3D
				check(not n.is_visible_in_tree(), "pregrant inherited art invisible " + gate.gate_id + path)

	# Cross-process flag-off/on comparison purposely excludes presentation state.
	print("GATE_ART_MECHANICS " + JSON.stringify(_mechanics(game)))
	var second := game.gates[1] as Gate
	var second_right := second.get_node("HingeRight") as Node3D
	if not mode:
		var normal := second_right.position
		second_right.position.y += .009
		var before := _mechanics(game)
		check(not Review.apply_all(game.gates, game, game.ground) and _count(game, false) and before == _mechanics(game), "second gate late rejection leaves both completely technical")
		second_right.position = normal
		check(_count(game, false), "diagnostic restore left preview baseline art unchanged")
		var foreign = Combined.instantiate()
		root.add_child(foreign)
		foreign.set_physics_process(false)
		var reference := _mechanics(game)
		check(not Review.apply_all(game.gates, game, foreign.ground) and _count(game, false) and reference == _mechanics(game),
			"independent other world's terrain may not admit either gate")
		foreign.free()
		var nodes: Array[Node3D] = [game.camp_built, game.ground.get_parent(), game.ground.get_node("GroundTriangles"), game, game]
		var labels := ["camp offset", "terrain local drift", "collider local drift", "unsupported scene yaw", "nonunit inherited frame"]
		for i in range(nodes.size()):
			var n := nodes[i]
			var original := n.transform
			n.transform = Transform3D(Basis(Vector3.UP, .15), original.origin) if i == 3 else (
				Transform3D(Basis.from_scale(Vector3(1.02, 1.0, 1.0)), original.origin) if i == 4 else
				Transform3D(original.basis, original.origin + Vector3(.02, .03, 0)))
			var changed := n.transform
			var old_mechanics := _mechanics(game)
			check(not Review.apply_all(game.gates, game, game.ground) and _count(game, false) and changed == n.transform and old_mechanics == _mechanics(game),
				"no partial art/pose change for " + labels[i])
			n.transform = original
		# Same class/name and configured frames are insufficient for exact authority.
		var terrain_body: StaticBody3D = game.ground
		var hit := terrain_body.get_node("GroundTriangles") as CollisionShape3D
		var genuine := hit.shape as ConcavePolygonShape3D
		var terrain_visual := terrain_body.get_parent().get_node("GroundVisual") as MeshInstance3D
		var expected_mesh := terrain_visual.mesh
		var shape_before := _mechanics(game)
		var fake_floor := ConcavePolygonShape3D.new()
		fake_floor.set_faces(PackedVector3Array([Vector3(0,40,0),Vector3(0,40,1),Vector3(1,40,0)]))
		hit.shape = fake_floor
		check(not Review.apply_all(game.gates, game, terrain_body) and _count(game, false) and
			hit.shape == fake_floor and shape_before == _mechanics(game), "exact elevated concave triangle is rejected without art changes")
		var reordered := genuine.get_faces().duplicate()
		var prior := reordered[0]
		reordered[0] = reordered[1]
		reordered[1] = prior
		var wrong_order := ConcavePolygonShape3D.new()
		wrong_order.set_faces(reordered)
		hit.shape = wrong_order
		check(not Review.apply_all(game.gates, game, terrain_body) and _count(game, false) and
			hit.shape == wrong_order and shape_before == _mechanics(game), "same face count with reordered vertices is rejected")
		var alternate := expected_mesh.duplicate() as ArrayMesh
		terrain_visual.mesh = alternate
		hit.shape = alternate.create_trimesh_shape()
		var duplicate_shape := hit.shape
		check(not Review.apply_all(game.gates, game, terrain_body) and _count(game, false) and terrain_visual.mesh == alternate and
			hit.shape == duplicate_shape and shape_before == _mechanics(game), "paired visual resource alias and shape cannot replace accepted authority")
		terrain_visual.mesh = expected_mesh
		hit.shape = genuine
		var correct_layer := terrain_body.collision_layer
		terrain_body.collision_layer = 1
		check(not Review.apply_all(game.gates, game, terrain_body) and _count(game, false) and terrain_body.collision_layer == 1 and
			shape_before == _mechanics(game), "wrong collision layer denies all four unchanged")
		terrain_body.collision_layer = correct_layer
		check(_count(game, false) and shape_before == _mechanics(game), "restored genuine terrain leaves original art and gate mechanics unchanged")
		var terrain_stage := terrain_body.get_parent()
		var saved_process := terrain_stage.process_mode
		var sample_ray := PhysicsRayQueryParameters3D.create(game.to_global(Vector3(0,30,0)), game.to_global(Vector3(0,-20,0)), 1 << 11)
		await physics_frame
		await physics_frame
		var active_hit := terrain_body.get_world_3d().direct_space_state.intersect_ray(sample_ray)
		terrain_stage.process_mode = Node.PROCESS_MODE_DISABLED
		await physics_frame
		await physics_frame
		var absent_hit := terrain_body.get_world_3d().direct_space_state.intersect_ray(sample_ray)
		check(not active_hit.is_empty() and absent_hit.is_empty() and not terrain_body.can_process() and
			terrain_body.process_mode == Node.PROCESS_MODE_INHERIT, "effective disabled ancestor removes genuine known ray, local body properties unchanged")
		check(not Review.apply_all(game.gates, game, terrain_body) and _count(game, false) and shape_before == _mechanics(game) and
			terrain_stage.process_mode == Node.PROCESS_MODE_DISABLED and hit.shape == genuine,
			"disabled known ancestor cannot admit either gate")
		terrain_stage.process_mode = saved_process
		await physics_frame
		await physics_frame
		check(not terrain_body.get_world_3d().direct_space_state.intersect_ray(sample_ray).is_empty(), "restored effective participation restores native ray")
		var stored_disable_mode := terrain_body.disable_mode
		terrain_body.disable_mode = CollisionObject3D.DISABLE_MODE_KEEP_ACTIVE
		check(not Review.apply_all(game.gates, game, terrain_body) and _count(game, false), "unexpected collision disable policy cannot admit art")
		terrain_body.disable_mode = stored_disable_mode

		# Deliberately alter the same shared cached ArrayMesh, not merely the
		# renderer's pointer, and derive its matching false live collider.
		var shared := expected_mesh as ArrayMesh
		var original_arrays := shared.surface_get_arrays(0)
		var touched_arrays := original_arrays.duplicate()
		var vertices: PackedVector3Array = original_arrays[Mesh.ARRAY_VERTEX].duplicate()
		vertices[0] = vertices[0] + Vector3(0.0, 0.25, 0.0)
		touched_arrays[Mesh.ARRAY_VERTEX] = vertices
		shared.clear_surfaces()
		shared.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, touched_arrays)
		hit.shape = shared.create_trimesh_shape()
		var modified_pair := hit.shape as ConcavePolygonShape3D
		check(shared == terrain_visual.mesh and modified_pair != null and modified_pair.get_faces() == shared.get_faces() and
			not Review.apply_all(game.gates, game, terrain_body) and _count(game, false) and hit.shape == modified_pair and
			shape_before == _mechanics(game), "same shared visual and matching mutated live collider bytes both fail independent donor")
		shared.clear_surfaces()
		shared.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, original_arrays)
		hit.shape = genuine
		check(_count(game, false) and shape_before == _mechanics(game), "exact shared terrain and collision restored without altering gate state")
		var reparent_from := second.get_parent()
		var alien := Node3D.new()
		game.add_child(alien)
		second.reparent(alien, true)
		var moved := _mechanics(game)
		check(not Review.apply_all(game.gates, game, game.ground) and _count(game, false) and moved == _mechanics(game),
			"gate branch reparent denies whole preview mount")
		second.reparent(reparent_from, true)
		alien.free()
	var expected_ids := ["gate-south", "gate-east"]
	var ids: Array = []
	for gate: Gate in game.gates:
		ids.append(gate.gate_id)
		# Detached native technical witness; ordinary paid/input is existing suite.
		gate.set_earned(true)
		var safe := gate.to_global(Vector3(0,0,2.4))
		check(gate.request_toggle(safe), "existing touch-range decision " + gate.gate_id)
		gate.advance(.02, gate.global_position, .31)
		check(gate.holding_for_occupancy and is_zero_approx(gate.angle), "locked occupied sweep unchanged " + gate.gate_id)
		for i in range(100):
			gate.advance(.02,safe,.31)
		check(is_equal_approx(gate.angle,PI*.5) and not gate.holding_for_occupancy, "existing paired motion open " + gate.gate_id)
	check(ids == expected_ids and _count(game, mode), "routes distinct; art flag remains presentation only")
	print("GATE_ART_EARNED_OPEN_MECHANICS " + JSON.stringify(_mechanics(game)))
	game.free()
	print("GATE_ART_OPTIN %d/%d" % [passed,passed+failed])
	quit(0 if failed == 0 else 1)
