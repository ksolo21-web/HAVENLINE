extends "res://tests/test_integrated_opening.gd"
## Detached observer only. This does not attach mounts or add any purchase effect.
const FIXTURE = preload("res://tests/fixture_integrated_disposable_opening.gd")
const STORE = preload("res://opening_save.gd")
const OPT_IN := "--hvn-observe-purchase-mounts"
const SOURCES := ["wood-b", "wood-c", "wood-a"]
var actor_id := 0
var representative_id := 0
var observed_commit := false
var watch_commit := false
var representative_mesh_ids: Array[int] = []

func visible_meshes(view: Node3D) -> Array[MeshInstance3D]:
	var found: Array[MeshInstance3D] = []
	for n in view.find_children("*", "MeshInstance3D", true, false):
		if n.mesh != null and n.is_visible_in_tree():
			found.append(n)
	return found

func source_status(amount: int, tag: String) -> void:
	var view = game.wood_stock_view
	var payload: Node3D = view.payload
	check(game.actor.get_instance_id() == actor_id and game.actor.is_on_floor(), tag + " same grounded actor")
	check(is_instance_valid(payload) and payload.get_instance_id() == representative_id and payload.get_parent() == view and view.get_parent() == game.actor, tag + " one original representative mounted under same actor")
	var ids: Array = game.ledger.collected
	check(game.ledger.stock.wood == amount and ids == SOURCES.slice(0, amount) and game.ledger.receipt.is_empty(), tag + " authoritative typed source prefix")
	check(view.presented_units == amount and view.counter.visible == (amount > 0), tag + " original view reflects exact count")
	var visible := visible_meshes(view)
	check(visible.size() == (6 if amount > 0 else 0), tag + " native mesh occupancy")
	var branch_ids: Array[int] = []
	for n in visible:
		branch_ids.append(n.get_instance_id())
		check(payload.is_ancestor_of(n) and n.global_transform.is_finite() and absf(n.global_transform.basis.determinant()) > 0.000001, tag + " finite actual mesh transform in single bundle branch")
	if amount == 1:
		representative_mesh_ids = branch_ids.duplicate()
	elif amount > 1:
		check(branch_ids == representative_mesh_ids, tag + " same six native meshes, no new source-bound instances")
	var check_direct := 0
	for child in view.get_children():
		if child is Node3D and (child is MeshInstance3D or not visible_meshes(child).is_empty()) and child.is_visible_in_tree():
			check_direct += 1
	check(check_direct == (1 if amount > 0 else 0), tag + " one or zero visible direct mounting branches")
	print("WITNESS %s stock=%d sources=%d cover=%d branches=%d representative_finite=%s" % [tag, amount, ids.size(), visible.size(), check_direct, payload.global_transform.is_finite()])

func paid(tag: String) -> void:
	var receipt: Dictionary = game.ledger.receipt
	check(receipt == {"offer": "center-hearth", "typed_debit": {"wood": 3}, "grant": "center-hearth", "revision": 1}, tag + " exact one-time receipt")
	check(game.ledger.stock.wood == 0 and game.ledger.collected == SOURCES, tag + " paid stock and exact source order retained")
	check(game.camp_built.is_visible_in_tree() and game.camp_built.has_node("CenteredHearth_StudioTrialOnly"), tag + " furnace and camp visible in paid frame")
	check(game.camp_colliders.size() > 0, tag + " original paid collision bodies present")
	for item in game.camp_colliders:
		check(item.collision_layer == 1, tag + " original paid collision active")
	check(not game.purchase_pad_view.scene_view.is_visible_in_tree() and visible_meshes(game.wood_stock_view).is_empty(), tag + " paid marker and representative immediately hidden")
	print("WITNESS %s stock=0 receipt=exact live_marker=false mount_meshes=0" % tag)

func tick(n: int) -> void:
	for i in range(n):
		await super.tick(1)
		# SceneTree.physics_frame precedes node processing: no other physics step
		# occurs between this poll and the immediately preceding published tick.
		if watch_commit and not observed_commit and not game.ledger.receipt.is_empty():
			observed_commit = true
			paid("first-published")

func capture_inputs() -> void:
	source_status(0, "spawn")
	check(await travel(game.wood_anchors["wood-b"]), "ordinary input to first loose wood")
	source_status(1, "wood-b")
	await tick(6)
	check(game.ledger.collected == ["wood-b"], "hold on first position does not duplicate")
	check(await travel(game.wood_anchors["wood-c"]), "ordinary input to second loose wood")
	source_status(2, "wood-c")
	check(await travel(game.point([-.35, 6.0])), "ordinary input east of the starter pine")
	check(await travel(game.point([-.85, 6.0])), "ordinary westbound facing")
	for i in range(3):
		press(KEY_F)
		await tick(21)
	check(game.resource_tree.phase == "falling" and game.resource_tree.blocked, "occupied fall remains withheld")
	source_status(2, "occupied-pine")
	check(await travel(game.point([0.0, 6.0])), "ordinary input clears fall")
	await tick(58)
	source_status(3, "settled-pine")
	check(await travel(game.point([0.0, 3.30])), "ordinary approach stops outside pay range")
	source_status(3, "unpaid-approach")

func run() -> void:
	var args := OS.get_cmdline_user_args()
	var selected: Array[String] = []
	for item in ["default", "write", "fail", "cold", "recover"]:
		if "--phase=" + item in args:
			selected.append(item)
	if args.count(OPT_IN) != 1 or selected.size() != 1:
		check(false, "explicit opt in and one test phase required")
		report()
		return
	var phase := selected[0]
	game = GAME.instantiate() if phase == "default" else FIXTURE.new()
	game.position = Vector3(2.0, 1.1, -3.0)
	root.add_child(game)
	check(game.bound and game.persist_requested == (phase != "default") and not game.persist_blocked, "exact scene bound under expected storage policy")
	if failures > 0:
		report()
		return
	await tick(10)
	var primary: String = "" if phase == "default" else game.profile.path_join(STORE.PRIMARY)
	var actor: Node3D = game.actor
	var payload: Node3D = game.wood_stock_view.payload
	check(is_instance_valid(payload), "exact integrated representative installed")
	if failures > 0:
		report()
		return
	actor_id = actor.get_instance_id()
	representative_id = payload.get_instance_id()
	if phase == "cold":
		var old := FileAccess.get_file_as_bytes(primary)
		paid("cold-before-input")
		check(await travel(game.point([0.0, 6.0])), "cold ordinary South gate approach")
		check(game.nearest_gate == game.gates[0] and not game.gates[0].target_open, "cold South gate initially closed and reachable")
		press(KEY_E)
		await tick(70)
		check(game.gates[0].target_open and absf(game.gates[0].angle - PI * .5) < .002, "ordinary input opens earned South gate")
		check(await travel(game.pad_anchor), "cold repeat ordinary approach through South gate")
		await tick(10)
		paid("cold-after-input")
		check(not old.is_empty() and FileAccess.get_file_as_bytes(primary) == old, "cold repeat cannot rewrite receipt")
	elif phase == "recover":
		var old := FileAccess.get_file_as_bytes(primary)
		# Already earned stock has not been observed in an earlier state in this process.
		for n in visible_meshes(game.wood_stock_view):
			representative_mesh_ids.append(n.get_instance_id())
		source_status(3, "recovered-unpaid")
		check(await travel(game.point([0.0, 3.30])), "recovered unpaid input stops outside reach")
		check(not old.is_empty() and FileAccess.get_file_as_bytes(primary) == old and not game.camp_built.visible, "recovery alone cannot debit")
	else:
		await capture_inputs()
		var previous := PackedByteArray()
		if phase != "default":
			previous = FileAccess.get_file_as_bytes(primary)
			check(not previous.is_empty(), "ordinary three grants were durably published")
		if phase == "fail":
			check(DirAccess.open(game.profile).make_dir(STORE.STAGING) == OK, "contained disposable save failure injection")
		watch_commit = true
		check(await travel(game.pad_anchor), "ordinary physical approach to real pad")
		await tick(10)
		if phase == "fail":
			check(not observed_commit and game.persist_blocked and not game.camp_built.visible, "failed save never publishes camp or receipt")
			source_status(3, "failed-save")
			check(FileAccess.get_file_as_bytes(primary) == previous and game.purchase_pad_view.scene_view.is_visible_in_tree(), "failed save leaves prior bytes and marker untouched")
		else:
			check(observed_commit, "observed first real published physics frame")
			paid("holding-paid")
			if phase == "write":
				var committed := FileAccess.get_file_as_bytes(primary)
				var next := PackedByteArray()
				await tick(10)
				next = FileAccess.get_file_as_bytes(primary)
				check(not committed.is_empty() and committed != previous and committed == next, "one durable promotion and no repeat write")
	report()

func report() -> void:
	print("purchase mount admission checks=", checks, " failures=", failures)
	quit(0 if failures == 0 else 1)
