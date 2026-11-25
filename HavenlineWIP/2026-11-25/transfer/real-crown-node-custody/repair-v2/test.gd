extends SceneTree

const Planner = preload("res://planner_upstream.gd")
const SPACING := 0.105
const FLIGHT_US := 285000
const START_STEP_US := 11500
const POLICY := {"fixture": {"enabled": true, "limits": {"wood": 4}}}
var errors: Array[String] = []
var checks := 0
var lab: Node3D
var actor: Node3D
var flight: Node3D
var landed: Node3D
var logs: Array[MeshInstance3D] = []
var stones: Array[MeshInstance3D] = []
var log_ids: Array[int] = []
var mesh: Mesh
var stone_snapshot: Array
var samples := 0
var fault := "clean"
var key_samples: Array[Dictionary] = []
var ledger := {"carry":{"wood":4,"stone":5}, "receivers":{"fixture":{"wood":0}}, "receipts":{}}

func _initialize() -> void:
	call_deferred("run")

func check(ok: bool, label: String) -> void:
	checks += 1
	if not ok:
		errors.append(label)

func make_mount(parent: Node, label: String) -> Node3D:
	var node := Node3D.new()
	node.name = label
	parent.add_child(node)
	return node

func make_visual(parent: Node3D, visual: Mesh, label: String, pos: Vector3) -> MeshInstance3D:
	var node := MeshInstance3D.new()
	node.name = label
	node.mesh = visual
	node.position = pos
	parent.add_child(node)
	return node

# Recursively inspect every visible MeshInstance3D under the lab, even nested
# under a helper and even when an equivalent mesh is a different Resource.
func visible_visuals(parent: Node) -> Array[MeshInstance3D]:
	var visuals: Array[MeshInstance3D] = []
	for child in parent.get_children(true):
		if child is MeshInstance3D and child.is_visible_in_tree() and child.mesh != null:
			visuals.append(child)
		visuals.append_array(visible_visuals(child))
	return visuals

func scan_others() -> Array:
	var result := []
	for child in visible_visuals(lab):
		if child.name.begins_with("Stone"):
			var override_id := 0
			var override_color := Color.TRANSPARENT
			if child.material_override != null:
				override_id = child.material_override.get_instance_id()
				if child.material_override is StandardMaterial3D:
					override_color = child.material_override.albedo_color
			result.append([String(child.name), child.get_instance_id(), child.get_parent().get_instance_id(), actor.global_transform.affine_inverse() * child.global_transform, child.mesh.get_instance_id(), override_id, override_color])
	return result

func scan_wood() -> Dictionary:
	var result := {}
	for child in visible_visuals(lab):
		if child.mesh == mesh or child.get_meta("kind", "") == "wood" or log_ids.has(child.get_instance_id()):
			var slot := str(child.get_meta("slot", "missing"))
			if not result.has(slot):
				result[slot] = []
			result[slot].append(child)
	return result

# Separate oracle in aligned-lab coordinates. Deliberately does not reuse the
# presenter interpolation or its timing constants. Check actual scene poses.
func oracle_flight(now_us: int, second_in_batch: bool, slot: int) -> Vector3:
	var age := float(now_us - (11500 if second_in_batch else 0))
	var x := -2.0 + (4.0 / 285000.0) * age
	var y := 1.0 - age / 570000.0 + (2.6 / (285000.0 * 285000.0)) * age * (285000.0 - age)
	return Vector3(x, y, (slot - 1.5) * 0.105)

func validate(expected: Array, label: String, now_us := -1, first := 0) -> void:
	var seen := scan_wood()
	check(visible_visuals(lab).size() == 9, label + ": recursive all-mesh census")
	check(seen.size() == 4, label + ": slot count")
	var census := [0,0,0]
	for i in range(4):
		var copies: Array = seen.get(str(i), [])
		check(copies.size() == 1, label + ": unique visible instance")
		if copies.size() != 1:
			continue
		var node: MeshInstance3D = copies[0]
		var owner: Node3D = expected[i]
		var owner_by_oracle := owner
		if now_us >= 0:
			if i < first:
				owner_by_oracle = landed
			elif i >= first + 2:
				owner_by_oracle = actor
			else:
				var start_us := 11500 if i == first + 1 else 0
				owner_by_oracle = actor if now_us < start_us else (flight if now_us < 285000 + start_us else landed)
		check(node.get_parent() == owner_by_oracle, label + ": independent phase")
		check(node.mesh == mesh and node.material_override == null and node.get_meta("kind", "") == "wood", label + ": original crown and material")
		check(node.get_parent() == owner and node.get_instance_id() == log_ids[i], label + ": owner and identity")
		check(node.basis.is_equal_approx(Basis.IDENTITY) and is_equal_approx(node.position.z, (i - 1.5) * SPACING), label + ": orientation and separate corridor")
		check(owner == flight or node.position.is_equal_approx(Vector3(-2 if owner == actor else 2,1 if owner == actor else 0.5,(i - 1.5) * SPACING)), label + ": terminal anchor")
		var lab_pos := lab.to_local(node.global_position)
		if owner == flight:
			check(lab_pos.distance_to(oracle_flight(now_us, i == first + 1, i)) <= 0.000005, label + ": XY arc oracle")
		else:
			check(lab_pos.distance_to(Vector3(-2 if owner == actor else 2, 1 if owner == actor else 0.5, (i - 1.5) * 0.105)) <= 0.000005, label + ": lab terminal")
		var actual_owner := [actor,flight,landed].find(node.get_parent())
		if actual_owner >= 0:
			census[actual_owner] += 1
	check(census[0]+census[1]+census[2] == 4, label + ": four pieces")
	check(scan_others() == stone_snapshot, label + ": untouched row")
	if not label.contains(":") or label.ends_with(":idle") or label.ends_with(":0") or label.ends_with(":285000") or label.ends_with(":296500"):
		key_samples.append({"state":label,"held_flight_landed":census,"stone":scan_others().size()})
	samples += 1

func submit(material: String, ticket: String, units: int) -> bool:
	var plan := Planner.plan_transfer(ledger, ["wood", "stone"], POLICY, "fixture", {"receiver":"fixture","material":material,"ticket":ticket,"units":units})
	if plan.is_empty():
		return false
	ledger = plan.next_state
	return true

func simulate(first: int, ticket: String, batch: int) -> void:
	var before := ledger.duplicate(true)
	check(submit("wood",ticket,2), ticket + ": commit")
	check(ledger.carry.wood == 4 - batch*2 and ledger.receivers.fixture.wood == batch*2 and ledger.carry.stone == 5, ticket + ": typed accounting")
	check(before.carry.wood - ledger.carry.wood == 2 and ledger.receipts[ticket] == ["fixture","wood",2], ticket + ": exact once")
	var committed := ledger.duplicate(true)
	check(not submit("wood",ticket,2) and not submit("stone",ticket+"-wrong",1) and ledger == committed, ticket + ": replay and wrong typed row denied")
	var timeline := [0,START_STEP_US-1,START_STEP_US,FLIGHT_US-1,FLIGHT_US,FLIGHT_US+START_STEP_US-1,FLIGHT_US+START_STEP_US]
	for n in range(1,20):
		timeline.append(n*16667)
	timeline.sort()
	for t: int in timeline:
		var expected: Array = []
		for i in range(4):
			var node := logs[i]
			var d := t-(i-first)*START_STEP_US
			if i < first or (i < first+2 and d >= FLIGHT_US):
				expected.append(landed)
				if node.get_parent() != landed:
					node.reparent(landed,true)
				node.position = Vector3(2,.5,(i-1.5)*SPACING)
			elif i >= first+2 or d < 0:
				expected.append(actor)
			else:
				expected.append(flight)
				if node.get_parent() != flight:
					node.reparent(flight,true)
				var u := float(d)/float(FLIGHT_US)
				node.position = Vector3(lerpf(-2,2,u),lerpf(1,.5,u)+.65*4*u*(1-u),(i-1.5)*SPACING)
		if fault == "wild-xy" and ticket == "partial" and t == 16667:
			logs[first].position += Vector3(34, -91, 0)
		await process_frame
		validate(expected, "%s:%d" % [ticket,t], t, first)
		check(ledger == committed, ticket + ": animation does not mutate ledger")
	var expected_final := [landed,landed,actor,actor] if batch == 1 else [landed,landed,landed,landed]
	validate(expected_final, ticket + ":idle")

func legacy_visible(w: int, s: int) -> Array:
	if w+s <= 48:
		return [w,s]
	var result := [1,1]
	for i in range(46):
		var want := [48.0*w/(w+s)-result[0],48.0*s/(w+s)-result[1]]
		result[1 if want[1]>want[0] else 0] += 1
	return result

func run() -> void:
	var args := OS.get_cmdline_user_args()
	if args.size() != 1 or args[0] not in ["clean", "nested-equivalent", "wild-xy", "nested-foreign"]:
		printerr("Supply clean or a supported rejection control")
		quit(2)
		return
	fault = args[0]
	var path := "res://source.input"
	var doc := GLTFDocument.new()
	var state := GLTFState.new()
	var status := doc.append_from_buffer(FileAccess.get_file_as_bytes(path), "res://", state)
	if status != OK:
		printerr("GLTF load failed: ", status)
		quit(2)
		return
	var crown: GLTFNode
	for gnode: GLTFNode in state.get_nodes():
		if str(gnode.original_name) == "Pickup LOD - Crown log":
			crown = gnode
	if crown == null:
		printerr("Exact crown GLTFNode unavailable")
		quit(2)
		return
	mesh = state.get_meshes()[crown.mesh].mesh.get_mesh()
	var tris := 0
	for i in range(mesh.get_surface_count()):
		tris += mesh.surface_get_array_index_len(i) / 3
		check(mesh.surface_get_arrays(i)[Mesh.ARRAY_COLOR].size() > 0, "source vertex colors present")
	var box := mesh.get_aabb()
	check(not state.json.nodes[0].has("matrix") and not state.json.nodes[0].has("translation") and not state.json.nodes[0].has("rotation") and not state.json.nodes[0].has("scale") and crown.mesh == 0 and mesh.get_surface_count() == 2 and tris == 1300, "unaltered source crown identity")
	check(box.size.is_equal_approx(Vector3(.283673,.102560,.103834)) and SPACING-box.size.z > .001, "unaltered bounds and corridors")
	lab = make_mount(root, "SyntheticLab")
	lab.position = Vector3(3,2,-6)
	lab.rotation.y = .71
	actor = make_mount(lab, "SyntheticCarry")
	flight = make_mount(lab, "SyntheticFlight")
	landed = make_mount(lab, "SyntheticLanding")
	for i in range(4):
		var node := make_visual(actor,mesh,"Crown%d" % i, Vector3(-2,1,(i-1.5)*SPACING))
		node.set_meta("slot",i)
		node.set_meta("kind","wood")
		log_ids.append(node.get_instance_id())
		logs.append(node)
	var other_mesh := SphereMesh.new()
	other_mesh.radius = .038
	other_mesh.height = .076
	var other_material := StandardMaterial3D.new()
	other_material.albedo_color = Color(.25,.46,.62,1)
	for i in range(5):
		var node := make_visual(actor,other_mesh,"Stone%d" % i,Vector3(-2,1+i*.095,-.5))
		node.material_override = other_material
		stones.append(node)
	stone_snapshot = scan_others()
	check(stone_snapshot.size() == 5,"second row starts visible")
	check(legacy_visible(63,5)==[44,4] and legacy_visible(11,5)==[11,5], "legacy untouched stone visible count instability")
	var legacy_delta := (.374+.09)*.5
	check(is_equal_approx(legacy_delta,.232) and legacy_visible(52,5)==[44,4] and legacy_visible(0,5)==[0,5], "legacy full depletion: stone X .232 -> 0")
	if fault in ["nested-equivalent", "nested-foreign"]:
		var helper := make_mount(flight, "Nested")
		var descendant := make_mount(helper, "MoreNested")
		var duplicate_equivalent := make_visual(descendant, mesh.duplicate(), "UnexpectedVisible", Vector3.ZERO)
		if fault == "nested-equivalent":
			duplicate_equivalent.set_meta("slot", 0)
			duplicate_equivalent.set_meta("kind", "wood")
	validate([actor,actor,actor,actor],"initial")
	# Mutations: prove the snapshots flag an extra draw, a slipped row, and visibility/material drift.
	var duplicate := make_visual(flight,mesh,"InjectedDouble",Vector3.ZERO)
	duplicate.set_meta("slot",0)
	check(scan_wood()["0"].size()==2,"duplicate negative observable")
	duplicate.free()
	var original_stone := stones[0].transform
	stones[0].position.x += .02
	check(scan_others()!=stone_snapshot,"shifted second row negative observable")
	stones[0].transform = original_stone
	stones[0].hide()
	check(scan_others()!=stone_snapshot,"hidden second-row prop negative observable")
	stones[0].show()
	var substitute := StandardMaterial3D.new()
	substitute.albedo_color = Color.MAGENTA
	stones[0].material_override = substitute
	check(scan_others()!=stone_snapshot,"wrong second-row material negative observable")
	stones[0].material_override = other_material
	await simulate(0,"partial",1)
	await simulate(2,"remaining",2)
	var packet := {"fault":fault,"checks":checks,"failures":errors,"samples":samples,"final_wood_carried":ledger.carry.wood,"final_wood_received":ledger.receivers.fixture.wood,"final_stone_carried":ledger.carry.stone,"triangles":tris,"mesh_bounds_m":[box.size.x,box.size.y,box.size.z],"key_samples":key_samples,"pitch_z_m":SPACING,"place":"synthetic-only","renderer":"headless not image evidence"}
	print(JSON.stringify(packet))
	lab.free()
	quit(0 if errors.is_empty() else 1)
