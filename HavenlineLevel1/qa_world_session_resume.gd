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
		await Session.drain_field_audio(self, f)
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
	# Walk around the north end of the new inlet to reach the same west snowfield.
	var north := Vector3.FORWARD
	drag.position=touch.position+82*Vector2(north.dot(right),north.dot(near))
	f._input(drag)
	for tick in 420:
		await physics_frame
		if f.actor.position.z < -6: break
	var checkpoint: Vector3=f.actor.position
	var sidestep:=0
	var trace: Array=[]
	for tick in 2000:
		if tick%35==0:
			trace.append(str(f.actor.position))
			if tick>0 and f.actor.position.distance_squared_to(checkpoint)<.6:
				sidestep=33
			checkpoint=f.actor.position
		var move:=Vector3.LEFT
		if sidestep>0:
			move=Vector3.FORWARD
			sidestep-=1
		drag.position=touch.position+82*Vector2(move.dot(right),move.dot(near))
		f._input(drag)
		await physics_frame
		if f.actor.position.x < -36:break
	touch.pressed=false
	f._input(touch)
	for tick in 45:await physics_frame
	if f.actor.position.x>=-34 or f.persist_blocked:
		printerr("ordinary travel did not reach west snowfield at ",f.actor.position," route ",trace);await Session.drain_field_audio(self, f);quit(1);return
	# Position came solely from movement input. Supply a non-default health and a timer
	# here so a fresh process also detects accidental full healing or elapsed wall-clock.
	f._player_hit(1)
	f.lifecycle.cooling["qa-pause-proof"]=8.25
	var w:=FileAccess.open(witness,FileAccess.WRITE)
	w.store_string(JSON.stringify({"x":f.actor.position.x,"z":f.actor.position.z,"hp":f.player_hp,"cooldown":8.25}))
	w.close()
	print("WORLD_SESSION_CLOSE ",f.actor.position," HP ",f.player_hp)
	f._close_field()
