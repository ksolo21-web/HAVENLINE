extends SceneTree

func _initialize() -> void:
	call_deferred("run")

func run() -> void:
	var expected_root := OS.get_environment("HAVENLINE_QA_PRIVATE_XDG")
	var app_folder: String = ProjectSettings.get_setting("application/config/custom_user_dir_name")
	if not expected_root.begins_with("/tmp/havenline-l1-native-dir-") or expected_root!=OS.get_environment("XDG_DATA_HOME"):
		quit(2)
		return
	var directory: String = expected_root.path_join(app_folder).path_join("world-one")
	var token := "native-directory-" + app_folder
	var write := "--directory-write" in OS.get_cmdline_user_args()
	var old := "--old-store" in OS.get_cmdline_user_args()
	var field
	var inventory
	var store
	var ok := true
	if old:
		inventory = preload("res://field_inventory.gd").new()
		inventory.configure(preload("res://field_progression.gd").offers({"wood":3}))
		store = preload("res://field_save.gd").new()
		ok = store.configure(OS.get_cmdline_user_args())
		var load_error: int = store.load_into(inventory)
		ok = ok and load_error==(ERR_FILE_NOT_FOUND if write else OK)
	else:
		change_scene_to_file(ProjectSettings.get_setting("application/run/main_scene"))
		await scene_changed
		for tick in 12: await physics_frame
		field = current_scene
		store = field.field_save
		inventory = field.inventory
		ok = not field.persist_blocked
	ok = ok and store.native_profile and store.directory==directory
	if write and ok:
		ok = inventory.collected.is_empty() and inventory.collect(token,"wood") and store.commit(inventory)==OK
	elif ok:
		ok = inventory.collected.size()==1 and inventory.collected.get(token)=="wood" and inventory.carried.wood==1
	print("NATIVE_DIRECTORY ",JSON.stringify({"app_folder":app_folder,"expected_native_directory":store.directory==directory,"normal_gameplay_scene":not old,"write":write,"credits":inventory.collected,"passed":ok}))
	if old: quit(0 if ok else 1)
	elif ok: field._close_field()
	else:
		await preload("res://tests/lifecycle_test_profile.gd").drain_field_audio(self,field)
		quit(1)
