extends "res://tests/test_paid_pine_renewal.gd"
# Detached native test only. No new store flag, authority or gameplay source.
func finish() -> void:
	print("PINE_FORK_CANDIDATE checks=", checks, " failures=", failures)
	quit(1 if failures else 0)

func run() -> void:
	var args := OS.get_cmdline_user_args()
	var mode := ""
	for arg in args:
		if arg.begins_with(SAVE_FLAG):
			profile = arg.trim_prefix(SAVE_FLAG)
		elif arg == "--hvn-pine-fork=earn" or arg == "--hvn-pine-fork=cold":
			mode = arg.trim_prefix("--hvn-pine-fork=")
	check(args.size() == 2 and not mode.is_empty() and profile.get_file().begins_with("havenline-l1-v3-pine-fork-new-") and FileAccess.get_file_as_string(profile.path_join("PINE-FORK-ROLE")) == "PINE-FORK-NEW-V1\n", "candidate observer admits only supported role marker")
	if failures > 0:
		finish()
		return
	game = GAME.instantiate()
	game.set_script(AuditScene)
	root.add_child(game)
	check(game.bound and game.persist_requested and not game.persist_blocked, "exact already-paid state admitted")
	if failures > 0:
		finish()
		return
	var saves := profile.path_join(game.save.PRIMARY)
	var bytes := FileAccess.get_file_as_bytes(saves)
	var original: Dictionary = game.ledger.snapshot()
	var version := 1 if mode == "earn" else 2
	check(not bytes.is_empty() and original.version == version and game.ledger.stock.wood == version - 1 and game.ledger.pine_occurrences == version - 1, "actual fork payload and stock")
	check(game.ledger.collected == ["wood-b","wood-c","wood-a"] and game.ledger.has_exact_paid_hearth() and game.camp_built.visible and not game.purchase_pad_view.scene_view.is_visible_in_tree(), "original paid receipt and camp remain exact")
	var tree = game.resource_tree
	check(tree.phase=="credited" and is_equal_approx(tree._regrow_remaining, 5.0), "native restore starts exact original five-second timer")
	var remaining: float = tree._regrow_remaining
	var casted := false
	for i in 310:
		remaining = tree._regrow_remaining
		await tick(1)
		if tree.phase=="rooted":
			casted=true
			break
	check(casted and absf(remaining - 1.0/60.0) < .00001 and tree.strikes==0 and tree.get_child(0).is_visible_in_tree(), "last hidden tick to rooted transition at the exact timer boundary")
	check(game.ledger.snapshot()==original and FileAccess.get_file_as_bytes(saves)==bytes, "countdown/restoration does not award or write")
	if mode=="earn":
		await approach()
		await settle(0,1)
		var renewed: Dictionary = game.ledger.snapshot()
		check(renewed.version==2 and renewed.pine_occurrences==1 and renewed.stock=={"wood":1} and renewed.receipt==original.receipt and renewed.collected==original.collected, "only first actual paid repeat advances cloned profile to v2 plus one")
		var cold_reader := Ledger.new()
		check(game.save.load_into(cold_reader)==OK and cold_reader.snapshot()==renewed and FileAccess.get_file_as_bytes(saves)!=bytes, "new v2 authority/disk exact on B")
	else:
		check(game.ledger.pine_occurrences==1 and game.ledger.stock.wood==1 and FileAccess.get_file_as_bytes(saves)==bytes, "fresh candidate restores earned +1 without regrowth credit or rewrites")
	check(not FileAccess.file_exists(profile.path_join(game.save.STAGING)),"no stage side effects")
	finish()
