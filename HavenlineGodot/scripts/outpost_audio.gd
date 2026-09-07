extends Node
var wind: AudioStreamPlayer
var fire: AudioStreamPlayer
var voices: Array[AudioStreamPlayer] = []
var streams: Dictionary = {}
var cursor := 0
var muted := false
var settings_path := "user://outpost-audio.cfg"
var emitted_events := 0

func _ready():
	var settings := ConfigFile.new()
	if settings.load(settings_path) == OK:
		var saved = settings.get_value("audio", "muted", false)
		if saved is bool: muted = saved
	for name in ["wind","fire","wood","stone","transfer","upgrade"]:
		var path: String="res://assets/audio/"+str(name)+".wav"
		if not ResourceLoader.exists(path):
			push_error("Missing baked outpost audio: run tools/havenline/bake_outpost_audio.py")
			return
		streams[name]=load(path)
	for name in ["wind","fire"]:
		var stream: AudioStreamWAV=streams[name].duplicate()
		stream.loop_mode=AudioStreamWAV.LOOP_FORWARD
		stream.loop_end=int(stream.get_length()*stream.mix_rate)
		var player:=AudioStreamPlayer.new()
		player.stream=stream; player.volume_db=-30.0
		add_child(player); player.play()
		if name == "wind": wind=player
		else: fire=player
	for index in range(8):
		var voice:=AudioStreamPlayer.new()
		add_child(voice); voices.append(voice)

func sync(sim, paused: bool, dt: float):
	if not is_instance_valid(wind): return
	wind.stream_paused=paused or muted
	fire.stream_paused=paused or muted
	for voice in voices: voice.stream_paused=paused or muted
	var distance: float=sim.position.distance_to(sim.point(sim.contract.world.furnace))
	var near:=1.0-smoothstep(1.0,sim.warmth()+3.0,distance)
	var w: Dictionary=sim.climate.weather()
	var smoothing:=1.0-exp(-dt*3.)
	wind.volume_db=lerpf(wind.volume_db,-31.0+float(w.wind)*10.,smoothing)
	fire.volume_db=lerpf(fire.volume_db,(-29.0+near*12.) if sim.durability>0 else -80.0,smoothing)

func consume(events: Array):
	if muted or voices.is_empty(): return
	var played:=0
	for event in events:
		var clip:=""
		match event.type:
			"gather": clip="wood" if event.get("resource","")=="wood" else "stone"
			"deposit","build","repair","defense_repair","customer_sale": clip="transfer"
			"upgrade","wave_clear": clip="upgrade"
		if clip.is_empty(): continue
		if played>=3: break # Bounded polyphony; crew crowds cannot flood the mixer.
		var voice: AudioStreamPlayer=voices[cursor]
		cursor=(cursor+1)%voices.size()
		voice.stream=streams[clip]
		voice.volume_db=-16.0 if clip=="upgrade" else -23.0
		voice.pitch_scale=1.0
		voice.play(); emitted_events+=1; played+=1

func set_muted(value: bool) -> Error:
	muted = value
	var settings := ConfigFile.new()
	settings.set_value("audio", "muted", muted)
	var result := settings.save(settings_path)
	if result != OK: push_warning("Could not preserve outpost sound preference: " + str(result))
	return result

func stop_all():
	for player in [wind,fire]+voices:
		if is_instance_valid(player):
			# A paused voice must be resumed before the mixer can retire it.
			player.stream_paused = false
			player.stop()
			player.stream = null
	streams.clear()

func _exit_tree():
	stop_all()
