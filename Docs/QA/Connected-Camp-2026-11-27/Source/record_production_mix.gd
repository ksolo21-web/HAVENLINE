extends SceneTree
## Capture the native stereo mix while a real, already-paid Build 9 camp resumes.
var game
var tap := AudioEffectCapture.new()
var samples := PackedByteArray()
var cues := []
var seconds := 0.0
var energy := 0.0
var peak := 0.
var observed_motor := false

func _initialize() -> void: call_deferred("run")

func collect() -> void:
	var batch := tap.get_buffer(tap.get_frames_available())
	var pcm := PackedByteArray()
	pcm.resize(batch.size() * 4)
	for i in batch.size():
		var v := batch[i]
		peak = maxf(peak,maxf(absf(v.x),absf(v.y)))
		energy += v.length_squared()
		pcm.encode_s16(i * 4, roundi(clampf(v.x,-1.,1.)*32767.))
		pcm.encode_s16(i * 4 + 2, roundi(clampf(v.y,-1.,1.)*32767.))
	samples.append_array(pcm)

func run() -> void:
	var is_muted := "--muted" in OS.get_cmdline_user_args()
	game = load("res://field_opening.tscn").instantiate()
	root.add_child(game)
	current_scene = game
	game.sound.set_muted(is_muted, false)
	# Add a known mixed load to this disposable checkpoint using normal inventory receipts.
	for batch in [["wood",17],["stone",17],["meat",18]]:
		for i in int(batch[1]):
			game.inventory.collect("production-listening-%s-%d" % [batch[0],i], batch[0])
	game.carry.sync()
	game.actor.global_position = game.depot.apron.global_position
	var landed_at_store := 0
	var peak_in_flight := 0
	var flights := {}
	var output := AudioServer.get_bus_index("Master")
	tap.buffer_length = 2.0
	AudioServer.add_bus_effect(output, tap)
	var effect_slot := AudioServer.get_bus_effect_count(output)-1
	game.sound.cue_started.connect(func(event: String, clock: float, _index: int): cues.append({"seconds":snappedf(clock,.001), "event":event}))
	var start := Time.get_ticks_usec()
	await create_timer(.12).timeout
	tap.clear_buffer()
	for i in 1080:
		await physics_frame
		collect()
		for flight in game.carry.flights:
			if flight.to == game.carry.STOCK: flights[flight.mesh.get_instance_id()] = true
		peak_in_flight = maxi(peak_in_flight,game.carry.flights.size())
		if i == 330:
			for evt in game.events:
				if evt.event in ["deposit_wood","deposit_stone","deposit_meat"]: landed_at_store+=1
			game.actor.global_position = game.counter.service_point.global_position + Vector3(.68,0,2.2)
		observed_motor = observed_motor or game.sound._conveyor_gain > .01
	seconds = (Time.get_ticks_usec() - start)/1000000.
	var stream := AudioStreamWAV.new()
	stream.format = AudioStreamWAV.FORMAT_16_BITS
	stream.mix_rate = AudioServer.get_mix_rate()
	stream.stereo = true
	stream.data = samples
	var folder := OS.get_environment("HAVENLINE_MIX_OUT")
	var label := "Muted" if is_muted else "Production"
	var err := stream.save_to_wav(folder.path_join(label+".wav"))
	var report := {"muted":is_muted,"game_seconds":18,"wall_seconds":seconds,"frames":samples.size()/4,"sample_rate":stream.mix_rate,"linear_peak":peak,"rms":sqrt(energy/maxi(1,samples.size()/2)),"discarded_frames":tap.get_discarded_frames(),"orders":game.inventory.settlement.served,"planks":game.inventory.settlement.product_store.planks,"blocks":game.inventory.settlement.product_store.blocks,"motor_from_moving_load":observed_motor,"mixed_load_staged":52,"distinct_visible_storage_flights":flights.size(),"peak_in_flight":peak_in_flight,"deposit_events_before_handoff":landed_at_store,"played":cues,"events":game.events}
	var file := FileAccess.open(folder.path_join(label+".json"),FileAccess.WRITE)
	file.store_string(JSON.stringify(report,"  ")+"\n")
	file.close()
	var ok: bool = err == OK and flights.size()>=50 and observed_motor and report.frames > 400000 and tap.get_discarded_frames()==0 and ((peak < .0001 and cues.is_empty()) if is_muted else (peak>.01 and peak<1. and not cues.is_empty()))
	print("MIX ",label," ",ok," ",report.frames," ",peak)
	AudioServer.remove_bus_effect(output,effect_slot)
	game.set_physics_process(false)
	game.carry.set_physics_process(false)
	game.sound.stop_playback()
	await create_timer(.2).timeout
	game.queue_free()
	for i in 4: await process_frame
	quit(int(not ok))
