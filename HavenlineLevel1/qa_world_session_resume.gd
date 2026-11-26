extends SceneTree
const Session=preload("res://tests/lifecycle_test_profile.gd")
const SCRIPT="res://qa_world_session_resume.gd"
func _initialize() -> void:call_deferred("run")
func run() -> void:
	var args:=OS.get_cmdline_user_args()
	if not ("--writer" in args or "--reader" in args):
		var directory:=Session.make_directory()
		var code:=2
		if not directory.is_empty():
			code=Session.child(SCRIPT,directory,"--writer")
			if code==0:code=Session.child(SCRIPT,directory,"--reader")
			Session.remove_owned(directory)
		quit(code)
		return
	var guard:=Session.Profile.new()
	if not guard.configure(args):
		quit(2)
		return
	var f=load("res://field_opening.tscn").instantiate()
	root.add_child(f)
	await physics_frame
	var witness:String=f.field_save.directory.path_join("resume-test-witness.json")
	if "--reader" in args:
		var expected=JSON.parse_string(FileAccess.get_file_as_string(witness))
		var gap:float=f.actor.position.distance_to(Vector3(expected.x,0,expected.z))
		var cool:float=f.lifecycle.cooling.get("qa-pause-proof",0)
		var valid:bool=not f.persist_blocked and gap<.025 and f.player_hp==expected.hp and absf(float(expected.cooldown)-cool)<.08 and f.actor.position.distance_to(f.point(f.layout.start_xz))>32
		print("WORLD_SESSION_REOPEN ",JSON.stringify({"passed":valid,"x":f.actor.position.x,"z":f.actor.position.z,"restored_hp":f.player_hp,"position_error_m":gap,"saved_timer":expected.cooldown,"remaining":cool,"wave":f.encounters.wave}))
		quit(0 if valid else 1)
		return
	var touch:=InputEventScreenTouch.new()
	touch.index=2
	touch.position=Vector2(70,280)
	touch.pressed=true
	f._input(touch)
	var drag:=InputEventScreenDrag.new()
	drag.index=2
	var right:Vector3=f.camera.global_basis.x
	var near:=right.cross(Vector3.UP)
	drag.position=touch.position+82*Vector2(Vector3.LEFT.dot(right),Vector3.LEFT.dot(near))
	f._input(drag)
	for tick in 1050:
		await physics_frame
		if f.actor.position.x < -36:break
	touch.pressed=false
	f._input(touch)
	for tick in 45:await physics_frame
	if f.actor.position.x>=-34 or f.persist_blocked:
		printerr("ordinary travel did not reach west snowfield");quit(1);return
	# Position came solely from movement input. Supply a non-default health and a timer
	# here so a fresh process also detects accidental full healing or elapsed wall-clock.
	f._player_hit(1)
	f.lifecycle.cooling["qa-pause-proof"]=8.25
	var w:=FileAccess.open(witness,FileAccess.WRITE)
	w.store_string(JSON.stringify({"x":f.actor.position.x,"z":f.actor.position.z,"hp":f.player_hp,"cooldown":8.25}))
	w.close()
	print("WORLD_SESSION_CLOSE ",f.actor.position," HP ",f.player_hp)
	f._close_field()
