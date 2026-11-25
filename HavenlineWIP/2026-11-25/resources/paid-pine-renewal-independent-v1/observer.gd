extends "res://previews/integrated_opening.gd"
var pine_commit_records: Array = []
var denied : bool = false
var extra_attempt_rejected := false

func _commit_opening_progress(next: Ledger) -> bool:
	if int(next.pine_occurrences) <= int(ledger.pine_occurrences):
		return super._commit_opening_progress(next)
	var prev: Dictionary = ledger.snapshot()
	var phase: String = resource_tree.phase
	var shown: bool = resource_tree.get_child(0).is_visible_in_tree()
	var primary: String = __profile().path_join(save.PRIMARY)
	var before := FileAccess.get_file_as_bytes(primary)
	# Exact live ticket cannot reenter successful publication. Does not mutate fixture authority.
	extra_attempt_rejected = not _collect_paid_pine(ResourceTreeScript.TREE_ID, _pine_ticket)
	var ok := super._commit_opening_progress(next)
	var loaded := Ledger.new()
	var on_disk := save.load_into(loaded) == OK and loaded.snapshot() == ledger.snapshot()
	pine_commit_records.append({"visible_before":shown,"visible_at_return":resource_tree.get_child(0).is_visible_in_tree(),
		"phase_before":phase,"phase_at_return":resource_tree.phase,"commit":ok,
		"wood_before":prev.stock.wood,"wood_return":ledger.stock.wood,"stable_receipt":prev.receipt==ledger.receipt,
		"disk_matches_live_at_return":on_disk,"disk_unchanged":before==FileAccess.get_file_as_bytes(primary)})
	return ok

func __profile() -> String:
	for arg: String in OS.get_cmdline_user_args():
		if arg.begins_with("--l1-disposable-profile="):
			return arg.trim_prefix("--l1-disposable-profile=")
	return ""
