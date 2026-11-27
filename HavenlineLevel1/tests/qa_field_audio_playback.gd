extends SceneTree
## Run at realtime with --headless --audio-driver Dummy. This examines the mix
## produced by Godot, including imported WAV decoding, each voice and its send.
const FieldAudio = preload("res://field_audio.gd")
var bank: FieldAudio
var tap := AudioEffectCapture.new()
var errors: Array[String] = []
var report := {"cues":{}, "music":{}, "aliases":{}}
var last_cue := ""
var tap_slot := -1

func _initialize() -> void:
	call_deferred("run")

func check(condition: bool, description: String) -> void:
	if not condition:
		errors.append(description)
		push_error(description)

func stop_voices() -> void:
	for voice: AudioStreamPlayer2D in bank._voices:
		voice.stop()

func measure(seconds: float) -> Dictionary:
	tap.clear_buffer()
	await create_timer(seconds).timeout
	var samples := tap.get_buffer(tap.get_frames_available())
	var squared := 0.0
	var peak := 0.0
	for sample in samples:
		squared += sample.length_squared()
		peak = maxf(peak, maxf(absf(sample.x), absf(sample.y)))
	return {"frames":samples.size(),"rms_dbfs":snappedf(linear_to_db(maxf(.0000001,sqrt(squared/maxi(1,samples.size()*2)))),.01),
		"peak_dbfs":snappedf(linear_to_db(maxf(.0000001,peak)),.01)}

func run() -> void:
	bank = FieldAudio.new()
	root.add_child(bank)
	bank.set_muted(false,false)
	bank.set_mix_levels(0,0,1,false)
	bank.cue_started.connect(func(cue:String, _time:float, _slot:int): last_cue=cue)
	tap.buffer_length = 3.
	tap_slot = AudioServer.get_bus_effect_count(0)
	AudioServer.add_bus_effect(0,tap)
	await create_timer(.18).timeout
	check(bank._ready_to_play,"all streams imported")
	for id: String in FieldAudio.CUES:
		stop_voices()
		await create_timer(.075).timeout
		check(bank.emit_event(id),id+" accepted")
		var sample: Dictionary = await measure(.29)
		report.cues[id]=sample
		check(sample.frames>2000 and sample.peak_dbfs > -65.0, id+" reaches Master")
	stop_voices()
	bank.set_mix_levels(1,0,0,false)
	for state in ["field","camp","threat"]:
		bank.set_music_state(state)
		await create_timer(1.5).timeout
		var sample: Dictionary = await measure(.65)
		report.music[state]=sample
		check(sample.frames>2000 and sample.rms_dbfs > -55.,state+" music reaches Master")
	# Monitor the actual conveyor stem on its own while the other ambience is muted.
	bank.set_mix_levels(0,0,0,false)
	AudioServer.add_bus()
	var monitor := AudioServer.bus_count-1
	AudioServer.set_bus_name(monitor,"QA Conveyor Monitor")
	AudioServer.set_bus_send(monitor,FieldAudio.OUTPUT)
	var motor: AudioStreamPlayer = bank._loops.conveyor_motor
	motor.bus = "QA Conveyor Monitor"
	bank.set_conveyor_proximity(1.)
	await create_timer(.9).timeout
	var running := await measure(.30)
	bank.set_conveyor_proximity(0.)
	await create_timer(1.8).timeout
	var stopped := await measure(.30)
	check(running.rms_dbfs > -42 and stopped.rms_dbfs < running.rms_dbfs - 35.,"moving conveyor is audible and idle conveyor fades")
	report["conveyor_motor"] = {"working":running, "idle":stopped}
	motor.bus = FieldAudio.AMBIENCE
	AudioServer.remove_bus(monitor)
	bank.set_mix_levels(0,0,1,false)
	var routing: Dictionary = FieldAudio.ALIASES.duplicate()
	for kind: String in FieldAudio.ORE_PITCH:
		for action in ["impact","deplete","drop","deposit","spend","regrow"]:
			routing[action+"_"+kind] = action+"_stone"
	for key: String in routing:
		stop_voices()
		bank._last.clear()
		check(bank.emit_event(key) and last_cue==routing[key],key+" routes")
		report.aliases[key]=last_cue
	bank.set_muted(true,false)
	await create_timer(.22).timeout
	var muted: Dictionary = await measure(.25)
	check(muted.peak_dbfs < -100. and not bank.emit_event("owl_equip"), "muted field is silent")
	check(bank.rejected_event_count==0 and tap.get_discarded_frames()==0, "complete cue routing with no discarded frames")
	report["mute"]=muted
	report["failures"]=errors
	report["mix_rate"]=AudioServer.get_mix_rate()
	print("FIELD_AUDIO_PLAYBACK ",JSON.stringify(report))
	AudioServer.remove_bus_effect(0,tap_slot)
	root.remove_child(bank)
	bank.free()
	await create_timer(.32).timeout
	quit(0 if errors.is_empty() else 1)
