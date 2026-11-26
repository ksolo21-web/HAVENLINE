extends "res://tests/test_paid_pine_renewal.gd"
# This is a separate test SceneTree, not the game application's entry point.
const FLAG := "--hvn-pine-rollback-candidate"

func report() -> void:
	print("PINE_ROLLBACK_CANDIDATE checks=", checks, " failures=", failures)
	quit(1 if failures else 0)

func run() -> void:
	var args := OS.get_cmdline_user_args()
	var sentry := "PINE-ROLLBACK-CANDIDATE"
	for arg in args:
		if arg.begins_with(SAVE_FLAG):
			profile = arg.trim_prefix(SAVE_FLAG)
	if args.count(FLAG) != 1 or args.size() != 2 or not profile.get_file().begins_with("havenline-l1-v3-pine-rollback-candidate-") or not FileAccess.file_exists(profile.path_join(sentry)) or FileAccess.get_file_as_string(profile.path_join(sentry)) != "PINE-ROLLBACK-CANDIDATE-V1\n":
		check(false,"strict candidate opt-in marker")
		report()
		return
	game = GAME.instantiate()
	game.set_script(AuditScene)
	root.add_child(game)
	check(game.bound and game.persist_requested and not game.persist_blocked, "exact patched integrated scene plus private save predicate")
	if failures > 0:
		report()
		return
	var primary := profile.path_join(game.save.PRIMARY)
	var capture := profile.path_join("v1-frozen.json")
	check(not FileAccess.file_exists(primary) and not FileAccess.file_exists(capture), "fresh disposable writer profile")
	await tick(10)
	for starter in ["wood-b","wood-c"]:
		check(await travel(game.wood_anchors[starter]), "ordinary pickup " + starter)
	await approach()
	await settle(2,3)
	check(game.ledger.pine_occurrences == 0 and game.ledger.collected == ["wood-b","wood-c","wood-a"], "all original collected IDs and zero paid pine count")
	check(await travel(game.point([0.,3.30])), "ordinary approach outside cost radius")
	check(game.ledger.stock.wood==3 and game.ledger.receipt.is_empty(),"outside range leaves unpaid")
	check(await travel(game.pad_anchor), "ordinary input reaches unchanged original V5 pad")
	await tick(3)
	var v1: Dictionary = game.ledger.snapshot()
	check(v1.version==1 and v1.stock=={"wood":0} and v1.receipt=={"offer":"center-hearth","grant":"center-hearth","typed_debit":{"wood":3},"revision":1} and game.camp_built.visible,"paid control exact v1 before first repeat")
	var canonical_v1 := Ledger.new()
	check(game.save.load_into(canonical_v1)==OK and canonical_v1.snapshot()==v1,"real fresh v1 primary independently decodes by candidate reader")
	var v1_bytes := FileAccess.get_file_as_bytes(primary)
	check(not v1_bytes.is_empty(), "real v1 primary bytes captured")
	var f := FileAccess.open(capture,FileAccess.WRITE)
	if f==null:
		check(false,"exact disposable v1 evidence copy")
		report()
		return
	f.store_buffer(v1_bytes)
	f.close()
	check(FileAccess.get_file_as_bytes(capture)==v1_bytes,"frozen v1 bytes are exact candidate primary copy")
	await cross_south()
	await tick(310)
	check(game.resource_tree.phase=="rooted" and game.ledger.stock.wood==0 and game.ledger.pine_occurrences==0 and FileAccess.get_file_as_bytes(primary)==v1_bytes, "regrowth alone does not write or award")
	await approach()
	await settle(0,1)
	var v2: Dictionary = game.ledger.snapshot()
	var canonical_v2 := Ledger.new()
	check(v2.version==2 and v2.pine_occurrences==1 and v2.stock=={"wood":1} and v2.collected==v1.collected and v2.receipt==v1.receipt,"first lawful completed repeat only: exact v2 and +1")
	check(game.save.load_into(canonical_v2)==OK and canonical_v2.snapshot()==v2,"candidate reads exactly its actual v2 persisted primary")
	check(FileAccess.get_file_as_bytes(capture)==v1_bytes and FileAccess.get_file_as_bytes(primary)!=v1_bytes,"v1 evidence immutable while actual primary becomes v2")
	check(not FileAccess.file_exists(profile.path_join(game.save.STAGING)),"no candidate staged-file residue")
	report()
