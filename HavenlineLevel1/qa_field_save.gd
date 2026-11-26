extends SceneTree

const Store = preload("res://field_save.gd")
const Profile = preload("res://opening_save.gd")
const Ledger = preload("res://field_inventory.gd")
var failures: Array[String] = []
const OFFERS := {"hearth":{"wood":2, "stone":1}}

func check(ok: bool, label: String) -> void:
	if not ok:
		failures.append(label)
		push_error(label)

func ledger() -> Ledger:
	var inv := Ledger.new()
	inv.configure(OFFERS)
	return inv

func write(path: String, content: String) -> void:
	var f := FileAccess.open(path, FileAccess.WRITE)
	f.store_string(content)
	f.close()

func _initialize() -> void:
	var incoming := OS.get_cmdline_user_args()
	if "--verify-restart" in incoming:
		var reader := Store.new()
		var resumed := ledger()
		var valid := reader.configure(incoming) and reader.load_into(resumed) == OK
		valid = valid and resumed.paid.hearth.wood == 1 and resumed.stored.stone == 1 and not resumed.complete("hearth")
		quit(0 if valid else 1)
		return
	var path := "/tmp/havenline-l1-v3-fieldqa-" + str(OS.get_process_id()) + "-" + str(Time.get_ticks_usec())
	check(DirAccess.make_dir_absolute(path) == OK,"create isolated test directory")
	var args := PackedStringArray([Profile.FLAG + path])
	var s := Store.new()
	var inv := ledger()
	check(not s.configure(args) and s.commit(inv) == ERR_UNAUTHORIZED,"no implicit access without sentinel")
	write(path.path_join(Profile.SENTINEL),Profile.MARK)
	check(s.configure(args) and s.load_into(inv) == ERR_FILE_NOT_FOUND,"authorized empty profile")
	check(inv.collect("tree#1","wood") and inv.payment("hearth","wood",false) and s.commit(inv) == OK,"initial partial purchase committed")
	var stale := Store.new()
	var stale_state := ledger()
	check(stale.configure(args) and stale.load_into(stale_state) == OK and stale_state.snapshot() == inv.snapshot(),"resumed typed partial")
	inv.collect("stone#1","stone")
	inv.deposit("stone")
	check(s.commit(inv) == OK and stale.commit(stale_state) == ERR_BUSY, "stale writer denied")
	var dead := path.path_join(Store.LOCK)
	DirAccess.make_dir_absolute(dead)
	write(dead.path_join("owner-2099999999"),"")
	write(dead.path_join("inventory.stage"),"interrupted output")
	check(s.commit(inv) == OK and not DirAccess.dir_exists_absolute(dead), "dead writer recovered")
	check(not FileAccess.file_exists(path.path_join(Profile.PRIMARY)), "legacy opening slot untouched")
	var child: Array = []
	var status := OS.execute(OS.get_executable_path(), PackedStringArray(["--headless","--path",ProjectSettings.globalize_path("res://"),"--script","res://qa_field_save.gd","--",Profile.FLAG+path,"--verify-restart"]),child,true)
	check(status == 0, "new process reopens exact typed partial")
	DirAccess.make_dir_absolute(dead)
	var active := dead.path_join("owner-"+str(OS.get_process_id()))
	write(active,"")
	check(s.commit(inv) == ERR_BUSY, "live process lock is respected")
	DirAccess.remove_absolute(active)
	DirAccess.remove_absolute(dead)
	var expected := inv.snapshot()
	check(stale.load_into(stale_state) == OK and stale_state.snapshot() == expected, "latest authoritative material balances resume")
	var other_path := path.path_join("untouched")
	write(other_path,"protected original")
	var dir := DirAccess.open(path)
	dir.remove(Store.PRIMARY)
	check(dir.create_link(other_path, Store.PRIMARY)==OK, "create test symlink")
	check(s.commit(inv)==ERR_UNAUTHORIZED and FileAccess.get_file_as_string(other_path)=="protected original","reject redirected primary")
	dir.remove(Store.PRIMARY)
	write(path.path_join(Store.PRIMARY),"{bad-field-save")
	check(s.load_into(inv)==ERR_FILE_CORRUPT and inv.snapshot()==expected and s.commit(inv)==ERR_FILE_CORRUPT,"reject corrupt primary, preserve prior memory and saved bytes")
	for name in [Store.PRIMARY, "untouched", Profile.SENTINEL]:
		dir.remove(name)
	DirAccess.remove_absolute(path)
	print(JSON.stringify({"failures":failures,"profile":"unique temporary sentinel directory", "persisted":expected}))
	quit(0 if failures.is_empty() else 1)
