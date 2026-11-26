extends SceneTree

func _initialize() -> void:
	call_deferred("check_restart")

func check_restart() -> void:
	var w=load("res://field_opening.tscn").instantiate()
	root.add_child(w)
	w.set_physics_process(false)
	var mode=OS.get_cmdline_user_args()[0]
	if mode=="write":
		w._player_hit(4)
		for tick in 20: w._physics_process(1./60.)
		w._persist_world()
	var hp_before=int(w.player_hp)
	var grace=float(w.player_invulnerability)
	var at:Vector3=w.actor.position
	var was_safe:bool=w.field_env.is_inside_camp(at)
	w._player_hit(1)
	print(JSON.stringify({"mode":mode,"position":str(at),"inside":was_safe,"hp_before_immediate_hit":hp_before,"remaining_fall":w.reset_time,"remaining_grace":grace,"hp_after_immediate_hit":w.player_hp,"save_error":w.persist_error}))
	w.sound.stop_playback()
	w.queue_free()
	for i in 8: await process_frame
	quit()
