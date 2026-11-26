extends SceneTree
const OldSave = preload("res://opening_save.gd")
const OldLedger = preload("res://opening_ledger.gd")
func _initialize() -> void:
	call_deferred("run")
func run() -> void:
	var args := OS.get_cmdline_user_args()
	var profile := ""
	for arg in args:
		if arg.begins_with(OldSave.FLAG):
			profile=arg.trim_prefix(OldSave.FLAG)
	if args.size()!=2 or args.count("--hvn-pine-fork-old-read")!=1 or not profile.get_file().begins_with("havenline-l1-v3-combined-pine-fork-old-") or FileAccess.get_file_as_string(profile.path_join("PINE-FORK-ROLE"))!="PINE-FORK-OLD-V1\n":
		print("FAIL old read role guard")
		quit(2)
		return
	var loader := OldSave.new()
	var ledger := OldLedger.new()
	var good := loader.configure(args) and loader.load_into(ledger)==OK
	var q:=ledger.snapshot()
	good=good and q == {"version":1,"stock":{"wood":0},"collected":["wood-b","wood-c","wood-a"],"receipt":{"offer":"center-hearth","grant":"center-hearth","typed_debit":{"wood":3},"revision":1}}
	print("PINE_FORK_OLD_READ preserved_paid_v1=", good)
	quit(0 if good else 1)
