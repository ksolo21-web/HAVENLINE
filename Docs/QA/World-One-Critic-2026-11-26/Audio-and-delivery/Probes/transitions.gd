extends SceneTree
var a
func _initialize(): call_deferred("run")
func run():
	a=load("res://field_audio.gd").new(); root.add_child(a)
	var samples=[]
	for tick in 480:
		await process_frame
		if tick==60:a.set_music_state("camp"); a.set_hearth_proximity(1.)
		if tick==180:a.set_music_state("threat");a.set_hearth_proximity(0.)
		if tick==300:a.set_music_state("field")
		if tick==390:a.set_muted(true,false)
		if tick==420:a.set_muted(false,false)
		if tick%12==0:
			samples.append({"frame":Engine.get_process_frames(),"tick":tick,"state":a._state,"field_db":a._loops.field_score.volume_db,"camp_db":a._loops.camp_score.volume_db,"threat_db":a._loops.threat_score.volume_db,"wind_db":a._loops.wind.volume_db,"fire_db":a._loops.fire.volume_db,"mute":AudioServer.is_bus_mute(AudioServer.get_bus_index(a.OUTPUT))})
	var f=FileAccess.open(OS.get_environment("MINING_MOVIE_METADATA"),FileAccess.WRITE);f.store_string(JSON.stringify(samples));f.close()
	a.stop_playback();a.queue_free()
	for i in 5:await process_frame
	quit()
