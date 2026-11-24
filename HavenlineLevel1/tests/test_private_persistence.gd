extends SceneTree
const Ledger = preload("res://opening_ledger.gd")
const Save = preload("res://opening_save.gd")
var failures := 0

func check(value: bool, message: String) -> void:
	if not value:
		failures += 1
		push_error(message)

func _initialize() -> void:
	var args := OS.get_cmdline_user_args()
	var store := Save.new()
	check(not store.configure(PackedStringArray()), "default must not persist")
	check(not store.configure(PackedStringArray(["--l1-disposable-profile=/tmp/../outside"])), "outside must reject")
	if not store.configure(args):
		push_error("Supply exact disposable path; no file writes attempted")
		quit(2)
		return
	var clean := Ledger.new()
	if store.load_into(clean) != ERR_FILE_NOT_FOUND:
		push_error("The disposable directory must begin without a primary.")
		quit(2)
		return
	check(not clean.pay_center_hearth(), "fresh can't pay")
	check(store.commit(clean) == OK, "baseline commit")
	var unpaid := Ledger.new()
	check(store.load_into(unpaid) == OK and unpaid.snapshot() == clean.snapshot(), "baseline reload")
	check(unpaid.collect_wood("wood-a") and not unpaid.collect_wood("wood-a"), "single-source pickup")
	check(store.commit(unpaid) == OK, "partial commit replacement")
	var paid := Ledger.new()
	check(store.load_into(paid) == OK and paid.stock.wood == 1 and paid.receipt.is_empty(), "partial reload")
	check(not paid.pay_center_hearth(), "partial can't pay")
	check(paid.collect_wood("wood-b") and paid.collect_wood("wood-c") and paid.pay_center_hearth(), "complete paid transaction")
	check(store.commit(paid) == OK, "paid commit")
	var later := Ledger.new()
	check(store.load_into(later) == OK and later.snapshot() == paid.snapshot(), "exact paid tuple reload")
	check(not later.pay_center_hearth() and not later.collect_wood("wood-b"), "no repeated payment or gathering")
	var mixed := later.snapshot()
	mixed.stock.wood = 3
	check(not later.restore(mixed) and later.snapshot() == paid.snapshot(), "mixed tuple rejected transactionally")
	var path := ""
	for arg in args:
		if arg.begins_with(Save.FLAG):
			path = arg.trim_prefix(Save.FLAG).path_join(Save.PRIMARY)
	var file := FileAccess.open(path, FileAccess.WRITE)
	if file == null:
		push_error("Disposable corruption fixture not writable")
		quit(2)
		return
	var inconsistent := JSON.stringify(mixed)
	file.store_string(JSON.stringify({"version": 1, "payload": inconsistent, "sha256": inconsistent.sha256_text()}))
	file.close()
	check(store.load_into(later) == ERR_FILE_CORRUPT and later.snapshot() == paid.snapshot(), "checksum-valid mixed tuple rejected")
	file = FileAccess.open(path, FileAccess.WRITE)
	if file == null:
		push_error("Disposable corruption fixture not writable")
		quit(2)
		return
	file.store_string("not a save")
	file.close()
	check(store.load_into(later) == ERR_FILE_CORRUPT and later.snapshot() == paid.snapshot(), "corruption never mutates loaded authority")
	check(store.commit(clean) == ERR_FILE_CORRUPT and FileAccess.get_file_as_string(path) == "not a save", "do not overwrite corrupt primary")
	print("Private persistence fixture failures: ", failures)
	quit(0 if failures == 0 else 1)
