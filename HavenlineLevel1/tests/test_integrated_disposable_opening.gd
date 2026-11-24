extends "res://tests/test_integrated_opening.gd"
const FIXTURE = preload("res://tests/fixture_integrated_disposable_opening.gd")
const STORE = preload("res://opening_save.gd")
const LEDGER = preload("res://opening_ledger.gd")

func report() -> void:
	print("combined cold fixture checks=", checks, " failures=", failures)
	quit(0 if failures == 0 else 1)

func earn_wood_through_input() -> void:
	check(await travel(game.wood_anchors["wood-b"]), "walk to first actual wood")
	check(await travel(game.wood_anchors["wood-c"]), "walk to second actual wood")
	check(await travel(game.point([-.35, 6.0])), "approach east of native tree")
	check(await travel(game.point([-.85, 6.0])), "face tree normally")
	for i in range(3):
		press(KEY_F)
		await tick(21)
	check(game.resource_tree.phase == "falling" and game.resource_tree.blocked, "occupied fall stays withheld")
	check(await travel(game.point([.0, 6.0])), "leave occupied fall area normally")
	await tick(58)
	check(game.ledger.stock.wood == 3 and game.ledger.receipt.is_empty(), "three distinct grants, before pay")

func gates_earned_closed() -> bool:
	return game.gates.size() == 2 and game.gates[0].active and game.gates[1].active and not game.gates[0].target_open and not game.gates[1].target_open and is_zero_approx(game.gates[0].angle) and is_zero_approx(game.gates[1].angle)

func gates_unearned() -> bool:
	return game.gates.size() == 2 and not game.gates[0].active and not game.gates[1].active

func probe_normal_preview() -> void:
	# Even with this process's intentional fixture flags, the ordinary combined
	# PackedScene never reads the staged input or starts persistence.
	game = GAME.instantiate()
	root.add_child(game)
	check(game.bound and not game.persist_requested and not game.camp_built.visible and game.ledger.collected.is_empty(), "ordinary preview ignores test-only flags and paid primary")
	game.queue_free()
	await process_frame

func run() -> void:
	var args := OS.get_cmdline_user_args()
	var modes := ["write", "cold", "fail", "recover_unpaid", "reject"]
	var selected: Array = []
	for mode in modes:
		if "--phase=" + mode in args:
			selected.append(mode)
	if selected.size() != 1:
		check(false, "one explicit test mode required")
		report()
		return
	var phase: String = selected[0]
	if phase == "cold":
		await probe_normal_preview()
	game = FIXTURE.new()
	game.position = Vector3(2, 1.1, -3)
	root.add_child(game)
	if phase == "reject":
		check(not game.bound and not game.persist_requested and game.get_child_count() == 0 and game.ledger.receipt.is_empty(), "fixture refuses unmarked invocation before composing any scene")
		report()
		return
	check(game.bound and game.persist_requested and not game.persist_blocked and not game.profile.is_empty(), "exact dual-marked disposable profile admitted")
	if failures:
		report()
		return
	var primary: String = game.profile.path_join(STORE.PRIMARY)
	var staging: String = game.profile.path_join(STORE.STAGING)
	await tick(5)
	if phase == "write" or phase == "fail":
		check(game.ledger.stock.wood == 0 and not FileAccess.file_exists(primary), "fresh test starts with no durable primary")
		await earn_wood_through_input()
		check(FileAccess.file_exists(primary), "ordinary wood grants produce same V8 durable format")
		var prepay := FileAccess.get_file_as_bytes(primary)
		if phase == "fail":
			var folder := DirAccess.open(game.profile)
			check(folder != null and folder.make_dir(STORE.STAGING) == OK, "force same-profile stage write failure after three grants")
		check(await travel(game.pad_anchor), "ordinary movement reaches authorized physical pad")
		await tick(3)
		if phase == "fail":
			check(game.persist_blocked and not game.camp_built.visible and gates_unearned() and game.ledger.stock.wood == 3 and game.ledger.receipt.is_empty(), "failed durable promotion never debits in memory or changes camp")
			check(FileAccess.get_file_as_bytes(primary) == prepay, "failed durable promotion leaves primary exact bytes")
			check(DirAccess.open(game.profile).dir_exists(STORE.STAGING), "obstruction remains contained inside test profile")
		else:
			check(not game.persist_blocked and game.camp_built.visible and gates_earned_closed() and game.ledger.stock.wood == 0, "durable paid tuple publishes one camp and two initially closed earned gates")
			check(not game.ledger.receipt.is_empty() and FileAccess.get_file_as_bytes(primary) != prepay and not FileAccess.file_exists(staging), "one promoted V8 receipt, no stage pending")
			var committed := FileAccess.get_file_as_bytes(primary)
			await tick(8)
			check(committed == FileAccess.get_file_as_bytes(primary), "holding original paid position cannot rewrite or debit again")
			check(await travel(game.point([0.0, 2.0])), "ordinary walk to South hinge control")
			press(KEY_E)
			await tick(70)
			check(game.gates[0].target_open and absf(game.gates[0].angle - PI * .5) < .002 and not game.gates[1].target_open, "writer switches only South gate prior to exit")
			check(committed == FileAccess.get_file_as_bytes(primary), "technical gate angles are not part of durable payment")
	elif phase == "cold":
		var committed := FileAccess.get_file_as_bytes(primary)
		var stale := FileAccess.get_file_as_bytes(staging)
		var expected := LEDGER.new()
		check(game.save.load_into(expected) == OK and var_to_bytes(expected.snapshot()) == var_to_bytes(game.ledger.snapshot()), "separate process restores identical durable ledger")
		check(game.camp_built.visible and gates_earned_closed() and game.ledger.stock.wood == 0 and game.ledger.collected.size() == 3, "restored one camp, spent wood and two earned gates reset safely closed")
		check(not game.wood_visuals["wood-b"].visible and not game.wood_visuals["wood-c"].visible and game.resource_tree.phase == "credited", "three sources not restored as new grants")
		check(not game.purchase_pad_view.scene_view.is_visible_in_tree(), "paid target remains hidden across cold load")
		check(await travel(game.wood_anchors["wood-b"]), "ordinary walk across previous pickup")
		check(await travel(game.point([0.0, 6.0])), "ordinary walk to cold-closed South gate")
		check(game.nearest_gate == game.gates[0] and not game.gates[0].target_open, "restored gate remains usable through normal interaction")
		press(KEY_E)
		await tick(70)
		check(game.gates[0].target_open and absf(game.gates[0].angle - PI * .5) < .002 and not game.gates[1].target_open, "ordinary input reopens only South after cold reset")
		check(await travel(game.pad_anchor), "ordinary walk through reopened gate across previous pad")
		await tick(4)
		check(game.camp_built.visible and game.ledger.stock.wood == 0 and game.ledger.collected.size() == 3 and not game.ledger.receipt.is_empty(), "no second grant or spend across paid positions")
		check(not stale.is_empty() and stale == FileAccess.get_file_as_bytes(staging) and committed == FileAccess.get_file_as_bytes(primary), "stale staged artifact ignored and primary bytes unchanged on reload")
	elif phase == "recover_unpaid":
		var primary_before := FileAccess.get_file_as_bytes(primary)
		check(game.ledger.stock.wood == 3 and game.ledger.receipt.is_empty() and not game.camp_built.visible and gates_unearned(), "cold process kept full unpaid stock after failed promotion")
		check(await travel(game.point([0.0, 3.30])), "ordinary movement keeps player outside pay radius")
		check(game.ledger.stock.wood == 3 and FileAccess.get_file_as_bytes(primary) == primary_before, "no speculative recovery grant or debit")
	report()
