extends SceneTree
# Only old 11c Save/Ledger in a script-only harness, no game scene or old app.
const OLD_SAVE = preload("res://opening_save.gd")
const OLD_LEDGER = preload("res://opening_ledger.gd")
var checks := 0
var failures := 0
func _initialize() -> void:
	call_deferred("run")
func check(ok: bool, msg: String) -> void:
	checks+=1
	failures+=0 if ok else 1
	print("PASS " if ok else "FAIL ",msg)
func report(mode: String) -> void:
	print("PINE_ROLLBACK_LEGACY mode=", mode, " checks=", checks," failures=",failures)
	quit(1 if failures else 0)
func run() -> void:
	var args := OS.get_cmdline_user_args()
	var mode := ""
	var profile := ""
	for arg in args:
		if arg=="--hvn-pine-rollback-old=v1":
			mode="v1"
		elif arg=="--hvn-pine-rollback-old=v2":
			mode="v2"
		elif arg.begins_with(OLD_SAVE.FLAG):
			profile=arg.trim_prefix(OLD_SAVE.FLAG)
	var good := args.size()==2 and not mode.is_empty() and profile.get_file().begins_with("havenline-l1-v3-pine-rollback-old"+mode+"-")
	good=good and FileAccess.get_file_as_string(profile.path_join("PINE-ROLLBACK-LEGACY"))=="PINE-ROLLBACK-LEGACY-"+mode+"\n"
	check(good,"strict legacy script and disposable version marker")
	if not good:
		report(mode)
		return
	var store := OLD_SAVE.new()
	check(store.configure(args),"same exact 11c save configure gate accepted scratch directory")
	if failures>0:
		report(mode)
		return
	var primary := profile.path_join(OLD_SAVE.PRIMARY)
	var staging := profile.path_join(OLD_SAVE.STAGING)
	var before := FileAccess.get_file_as_bytes(primary)
	check(not before.is_empty() and not FileAccess.file_exists(staging) and not DirAccess.dir_exists_absolute(staging), "real candidate-produced bytes present, no prior staging path")
	var input := OLD_LEDGER.new()
	var input_default: Dictionary = input.snapshot()
	var proposed := OLD_LEDGER.new()
	for k in ["wood-b","wood-c","wood-a"]:
		check(proposed.collect_wood(k),"create valid old proposal source "+k)
	check(proposed.pay_center_hearth(),"valid exact original paid v1 write proposal")
	var validation := OLD_LEDGER.new()
	check(validation.restore(proposed.snapshot()) and validation.snapshot()==proposed.snapshot(),"old proposal passes exact old ledger validator")
	var load_status: Error=store.load_into(input)
	if mode=="v1":
		check(load_status==OK and input.snapshot()==proposed.snapshot(),"older reader actually accepts candidate-produced paid v1")
	else:
		check(load_status==ERR_FILE_CORRUPT and input.snapshot()==input_default,"older reader refuses genuine v2 without mutating target ledger")
		var proposed_before: Dictionary=proposed.snapshot()
		var commit_status: Error=store.commit(proposed)
		check(commit_status==ERR_FILE_CORRUPT and proposed.snapshot()==proposed_before,"older valid commit refuses to replace undecodable primary")
		print("PINE_ROLLBACK_CODES load=", int(load_status)," commit=",int(commit_status)," expected=",int(ERR_FILE_CORRUPT))
	check(FileAccess.get_file_as_bytes(primary)==before and not FileAccess.file_exists(staging) and not DirAccess.dir_exists_absolute(staging),"exact primary bytes unchanged, no staging side effect")
	report(mode)
