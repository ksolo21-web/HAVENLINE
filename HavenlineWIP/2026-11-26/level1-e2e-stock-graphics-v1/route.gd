extends "res://tests/test_paid_pine_renewal.gd"
# This script explicitly instantiates the exact integrated PackedScene.
# The inherited ordinary input helpers are used; no actor/game methods are patched.
const MARKER := "L1-E2E-ROUTE"
const MARK := "HAVENLINE-L1-E2E-ROUTE-V1\n"
const RECEIPT := {"offer":"center-hearth","grant":"center-hearth","typed_debit":{"wood":3},"revision":1}
const STARTER := ["wood-b","wood-c","wood-a"]
var observe_paid := false
var first_paid_seen := false
var watch_restore := false
var restore_count := 0
var last_remaining: float = -1.0
var last_hidden := false

func checkpoint(phase: String) -> void:
	print("L1_COMBINED_CHECKPOINT ", JSON.stringify({"phase":phase,"tick":tick_count,"published_wood":game.ledger.stock.wood,"renewals":game.ledger.pine_occurrences,"paid":not game.ledger.receipt.is_empty()}))

func finish(phase: String) -> void:
	print("L1_COMBINED_ROUTE phase=",phase," checks=",checks," failures=",failures)
	quit(1 if failures else 0)

func camp_ok(active: bool) -> bool:
	if not is_instance_valid(game.camp_built) or game.camp_built.is_visible_in_tree() != active:
		return false
	var hearth := game.camp_built.get_node_or_null("CenteredHearth_StudioTrialOnly") as Node3D
	var floor := game.camp_built.get_node_or_null("CampOnlySurface") as MeshInstance3D
	if hearth == null or floor == null or hearth.is_visible_in_tree() != active or floor.is_visible_in_tree() != active:
		return false
	if not hearth.position.is_equal_approx(game.point([0.,0.])):
		return false
	if game.camp_colliders.size() != 7:
		return false
	for collider in game.camp_colliders:
		if collider.collision_layer != (1 if active else 0):
			return false
	return game.gates.size() == 2 and game.gates[0].gate_id == "gate-south" and game.gates[1].gate_id == "gate-east" and game.gates[0].active == active and game.gates[1].active == active

func live_pad_hidden() -> bool:
	return not game.purchase_pad_view.scene_view.is_visible_in_tree()

func check_first_paid() -> void:
	check(game.ledger.stock.wood==0 and game.ledger.snapshot().version==1 and game.ledger.receipt==RECEIPT and game.ledger.collected==STARTER, "first completed paid sample has exact original receipt and debit")
	check(camp_ok(true) and live_pad_hidden(), "centered camp/furnace visible and original solids live on first paid sample")
	check(game.ledger.pine_occurrences==0 and game.wood_stock_view.presented_units==0, "paid sample shows zero wood with no renewal or fake visible inventory")

func tick(n: int) -> void:
	for i in n:
		await super.tick(1)
		if observe_paid and not first_paid_seen and not game.ledger.receipt.is_empty():
			first_paid_seen = true
			check_first_paid()
			checkpoint("paid-first-frame")
		if watch_restore:
			var tr = game.resource_tree
			if last_hidden and tr.phase=="rooted":
				restore_count+=1
				check(absf(last_remaining - 1.0/60.0)<.00001 and tr.strikes==0 and tr.get_child(0).is_visible_in_tree(), "actual last hidden tick followed by rooted visible pine")
				checkpoint("pine-regrown")
			last_hidden=tr.phase=="credited"
			last_remaining=tr._regrow_remaining

func ordinary_route(primary: String) -> void:
	await tick(10)
	check(game.actor.basis.is_equal_approx(Basis.IDENTITY), "fresh spawn starts with exact standard actor basis")
	check(game.actor.is_on_floor() and Vector2(game.actor.position.x,game.actor.position.z).distance_to(Vector2(game.point(game.layout.start_xz).x,game.point(game.layout.start_xz).z))<.005, "exact authored fresh grounded spawn x/z")
	check(game.ledger.stock.wood==0 and game.ledger.collected.is_empty() and game.ledger.receipt.is_empty() and not FileAccess.file_exists(primary),"fresh v1 state and profile with no save")
	check(camp_ok(false) and not live_pad_hidden(), "camp/furnace/floor/gates exist only as hidden inactive prefabs before purchase")
	check(is_instance_valid(game.resource_tree) and game.resource_tree.name=="StarterResourceTree_wood_a" and game.wood_visuals.keys().size()==2 and game.wood_anchors.keys().size()==3,"only exact original wood sources under the pinned opening scope")
	checkpoint("fresh-spawn")
	var held := 0
	for source in ["wood-b","wood-c"]:
		check(await travel(game.wood_anchors[source]), "ordinary touch route to exact "+source)
		held+=1
		check(game.ledger.stock.wood==held and game.ledger.collected==STARTER.slice(0,held) and not game.wood_visuals[source].visible,"one committed distinct wood source")
	await approach()
	watch_restore=true
	await settle(2,3)
	check(game.ledger.collected==STARTER and game.ledger.receipt.is_empty() and game.ledger.pine_occurrences==0,"settled original tree is third one-time source")
	checkpoint("three-original-wood")
	check(await travel(game.point([0.,3.30])), "ordinary outside .72 purchase approach")
	check(not game.camp_built.visible and game.ledger.stock.wood==3 and game.ledger.receipt.is_empty(), "outside cannot pay or reveal")
	observe_paid=true
	check(await travel(game.pad_anchor), "ordinary touch inside exact real pad reach")
	await tick(10)
	check(first_paid_seen and game.ledger.receipt==RECEIPT and game.ledger.stock.wood==0,"actual paid tick was observed")
	observe_paid=false
	var exact_paid_bytes := FileAccess.get_file_as_bytes(primary)
	var expected_paid := Ledger.new()
	check(not exact_paid_bytes.is_empty() and game.save.load_into(expected_paid)==OK and expected_paid.snapshot()==game.ledger.snapshot(),"complete exact paid v1 authority saved")
	await tick(12)
	check(FileAccess.get_file_as_bytes(primary)==exact_paid_bytes and game.ledger.stock.wood==0,"standing during paid occupancy cannot repeat debit or write")
	await gate_cross(game.gates[0],[0.0,2.0],[0.0,6.0],"South")
	checkpoint("south-bidirectional")
	check(await travel(game.point([2.0,1.9])),"interior walk around centered hearth, not through obstruction")
	await gate_cross(game.gates[1],[3.0,0.0],[7.0,0.0],"East")
	checkpoint("east-bidirectional")
	check(await travel(game.point([2.0,1.9])) and await travel(game.point([0.0,2.0])) and await travel(game.point([0.0,6.0])), "return to original pine via open South, not a teleport")
	for _i in 310:
		if game.resource_tree.phase=="rooted":
			break
		await tick(1)
	check(restore_count==1 and game.ledger.stock.wood==0 and game.ledger.receipt==RECEIPT and FileAccess.get_file_as_bytes(primary)==exact_paid_bytes,"first regrowth gives no passive wood, acts or write")
	watch_restore=false
	await approach()
	await settle(0,1)
	check(game.ledger.snapshot().version==2 and game.ledger.pine_occurrences==1 and game.ledger.stock.wood==1 and game.ledger.receipt==RECEIPT,"first eligible completed paid repeat is exactly +1 and unchanged receipt")
	var saved_v2 := FileAccess.get_file_as_bytes(primary)
	var disk := Ledger.new()
	check(saved_v2!=exact_paid_bytes and game.save.load_into(disk)==OK and disk.snapshot()==game.ledger.snapshot(),"new genuine v2 exact durable authority")
	await tick(25)
	check(FileAccess.get_file_as_bytes(primary)==saved_v2 and game.ledger.stock.wood==1 and game.ledger.pine_occurrences==1,"settle/repeat cannot replay inside process")
	check(grounded>100,"native physical grounded route witnessed")
	checkpoint("writer-v2")

func cold_route(primary: String) -> void:
	var raw := FileAccess.get_file_as_bytes(primary)
	var expected: Dictionary = game.ledger.snapshot()
	check(not raw.is_empty() and expected.version==2 and expected.collected==STARTER and expected.stock=={"wood":1} and expected.receipt==RECEIPT and game.ledger.pine_occurrences==1, "fresh process reuses exact earned +1 and receipt")
	check(camp_ok(true) and live_pad_hidden() and not game.gates[0].target_open and not game.gates[1].target_open, "cold restores same centered paid camp, gates safely closed, pad absent")
	check(game.resource_tree.phase=="credited" and is_equal_approx(game.resource_tree._regrow_remaining,5.0), "cold sets original hidden timer without demand for a reward replay")
	watch_restore=true
	await tick(310)
	check(restore_count==1 and game.resource_tree.phase=="rooted","cold same original 5-second appearance restored")
	for id in ["wood-b","wood-c"]:
		check(await travel(game.wood_anchors[id]) and not game.wood_visuals[id].visible,"ordinary revisit sees spent source does not respawn")
	check(game.ledger.snapshot()==expected and FileAccess.get_file_as_bytes(primary)==raw and not FileAccess.file_exists(profile.path_join(game.save.STAGING)), "fresh-process replay-free restore, unchanged authority and exact bytes")
	checkpoint("cold-v2-no-replay")

func run() -> void:
	var args:=OS.get_cmdline_user_args()
	var phase:=""
	for arg in args:
		if arg.begins_with(SAVE_FLAG):
			profile=arg.trim_prefix(SAVE_FLAG)
		elif arg in ["--hvn-l1-e2e=write","--hvn-l1-e2e=cold"]:
			phase=arg.trim_prefix("--hvn-l1-e2e=")
	check(args.size()==2 and not phase.is_empty() and profile.get_file().begins_with("havenline-l1-v3-l1-e2e-") and FileAccess.get_file_as_string(profile.path_join(MARKER))==MARK,"explicit marked disposable opening only")
	if failures>0:
		finish(phase)
		return
	game=GAME.instantiate()
	root.add_child(game)
	check(game.bound and game.persist_requested and not game.persist_blocked,"exact authorized isolated scene and profile bound")
	if failures>0:
		finish(phase)
		return
	var primary:=profile.path_join(game.save.PRIMARY)
	if phase=="write":
		await ordinary_route(primary)
	else:
		await cold_route(primary)
	finish(phase)
