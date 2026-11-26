extends RefCounted
const Profile=preload("res://opening_save.gd")

static func make_directory() -> String:
	var directory := "/tmp/havenline-l1-v3-lifecycle-%d-%d"%[OS.get_process_id(),Time.get_ticks_usec()]
	if DirAccess.make_dir_absolute(directory)!=OK:return ""
	var marker := FileAccess.open(directory.path_join(Profile.SENTINEL),FileAccess.WRITE)
	if not marker:return ""
	marker.store_string(Profile.MARK)
	marker.close()
	return directory

static func child(script:String,directory:String,step:String) -> int:
	var out: Array=[]
	var args:=PackedStringArray(["--headless","--fixed-fps","60","--path",ProjectSettings.globalize_path("res://"),"--script",script,"--",Profile.FLAG+directory,step])
	var code:=OS.execute(OS.get_executable_path(),args,out,true)
	for message in out: print(String(message).strip_edges())
	return code

static func remove_owned(directory:String) -> void:
	var guard:=Profile.new()
	if not guard.configure(PackedStringArray([Profile.FLAG+directory])):return
	for filename in DirAccess.get_files_at(directory):
		DirAccess.remove_absolute(directory.path_join(filename))
	DirAccess.remove_absolute(directory)

static func isolated(tree: SceneTree, script:String) -> bool:
	if "--lifecycle-fixture" in OS.get_cmdline_user_args():
		var guard:=Profile.new()
		if guard.configure(OS.get_cmdline_user_args()):return false
		tree.quit(2)
		return true
	var directory:=make_directory()
	if directory.is_empty():
		tree.quit(2)
		return true
	var code:=child(script,directory,"--lifecycle-fixture")
	remove_owned(directory)
	tree.quit(code)
	return true

## Fixed-FPS test frames can outrun the audio driver, which releases queued WAV
## playback on its own thread. Let the mixer finish before freeing the scene.
static func drain_field_audio(tree: SceneTree, field: Node) -> void:
	field.sound.stop_playback()
	for tick in 12:
		OS.delay_msec(20)
		await tree.process_frame
