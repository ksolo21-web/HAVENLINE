extends Node
## Original field score, surface Foley and transaction cues.
## The caller supplies successful gameplay events and current state after restore.

const BANK := "res://assets/audio/"
const OUTPUT := "Field Output"
const MUSIC := "Field Music"
const AMBIENCE := "Field Ambience"
const SFX := "Field Effects"
const NO_SOURCE := Vector3.INF
const VOICES := 8
const RESERVED := 2

# [variation count, minimum interval, playback gain in dB, importance]
# Tier 3 events can use the two reserved voices; routine Foley leaves them free.
const CUES := {
	"step_snow": [3, .095, -9, 0], "step_camp": [3, .095, -10, 0],
	"swing": [2, .14, -13, 0], "impact_wood": [2, .10, -3.8, 2],
	"impact_stone": [2, .10, -4.4, 2], "deplete_wood": [1, .35, -3, 2],
	"deplete_stone": [1, .35, -3, 2], "drop_wood": [1, .09, -6, 1],
	"drop_stone": [1, .09, -7, 1], "drop_meat": [1, .09, -7, 1],
	"pickup_partial": [1, .07, 1.0, 2], "pickup_full": [1, .17, -3.5, 2],
	"carry": [1, .38, -14.5, 0], "deposit_wood": [1, .09, -5, 2],
	"deposit_stone": [1, .09, -5.5, 2], "deposit_meat": [1, .09, -5, 2],
	"spend_wood": [1, .14, -5.5, 3], "spend_stone": [1, .14, -5.5, 3],
	"spend_meat": [1, .14, -5.5, 3], "purchase": [1, .35, .5, 3],
	"build": [1, .35, -6, 2], "rise": [1, .38, -11, 1], "reveal": [1, .40, -5, 3],
	"gate": [1, .29, -6.5, 1], "gate_latch": [1, .14, -8, 1],
	"approach": [1, 1.05, -5, 2], "enemy_attack": [1, .24, -3.8, 2],
	"player_attack": [1, .17, -5, 2], "hit": [1, .11, -4, 2],
	"player_hurt": [1, .24, -2, 3], "defeat": [1, .35, -3, 3],
	"reset": [1, .55, -7, 3], "meat": [1, .12, -4, 2], "victory": [1, .75, -4, 3],
	"equip_axe": [1,.30,-10,1], "equip_pickaxe": [1,.30,-10,1],
	"regrow_wood": [1,.35,-12,0], "regrow_stone": [1,.4,-11,0],
	"wolf_brace": [1,.26,-9,2], "wolf_return": [1,.8,-4,2], "player_fall": [1,.75,-5,3],
	"boss_arrival": [1,.65,-3.5,3], "boss_defeat": [1,.7,-4,3],
	"cook_griddle": [1, .45, -3.0, 1], "service_cash_paper": [1, .18, -2.0, 3],
	"saw_work": [1,.45,-3.5,1], "drill_work": [1,.45,-3.5,1],
	"plank_out": [1,.12,-3.2,2], "block_out": [1,.12,-3.2,2],
	"owl_dive": [1,.20,-3.2,1], "owl_hit": [1,.12,-2.5,2],
	"owl_equip": [1,.40,-2,3], "rescue_answer": [1,.4,-2,3],
	"roast_ready": [1,.22,-2.4,2], "tower_fire": [1,.25,-6.0,2], "tower_hit": [1,.16,-4.8,2]
}
const ALIASES := {"attack":"enemy_attack","wolf_attack":"enemy_attack",
	"survivor_rescued":"rescue_answer", "worker_pickup":"carry", "worker_delivery":"deposit_wood",
	"cooker_start":"cook_griddle", "meal_ready":"roast_ready", "meal_served":"service_cash_paper",
	"level_complete":"victory", "next_level":"reveal", "process_wood":"saw_work", "process_stone":"drill_work", "process_done":"plank_out"}
const ORE_PITCH := {"metal": 1.19, "coal": 0.84, "slate": 1.08}
const LOOP_NAMES := ["field_score","camp_score","threat_score","wind","fire"]
const SETTINGS_PATH := "user://field-audio.cfg"

var _bank: Dictionary = {}
var _loops: Dictionary = {}
var _voices: Array[AudioStreamPlayer2D] = []
var _starts: Array[float] = []
var _importance: Array[int] = []
var _last: Dictionary = {}
var _counts: Dictionary = {}
var _owned_buses: Array[String] = []
var _clock := 0.0
var _duck_until := 0.0
var _hearth := 0.0
var _state := "field"
var _listener := Vector3.ZERO
var _ready_to_play := false
var _focused := true
var _muted := false
var _duck_db := 0.0
var _levels := {"music":1.0, "ambience":1.0, "sfx":1.0}
var rejected_event_count := 0
signal cue_started(event_name: String, game_seconds: float, voice_index: int)

func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	_make_bus(OUTPUT, "Master")
	_make_bus(MUSIC, OUTPUT)
	_make_bus(AMBIENCE, OUTPUT)
	_make_bus(SFX, OUTPUT)
	if AudioServer.get_bus_effect_count(AudioServer.get_bus_index(OUTPUT)) == 0:
		var limiter := AudioEffectHardLimiter.new()
		limiter.ceiling_db = -2.2
		AudioServer.add_bus_effect(AudioServer.get_bus_index(OUTPUT), limiter)
	var settings := ConfigFile.new()
	if settings.load(SETTINGS_PATH) == OK:
		_muted = settings.get_value("field_audio", "muted", false) == true
		for channel in _levels:
			_levels[channel] = clampf(float(settings.get_value("field_audio", channel, 1.0)), 0, 1)
	_apply_levels()
	for cue: String in CUES:
		var variants: Array[AudioStream] = []
		var count := int(CUES[cue][0])
		for n in range(count):
			var suffix := "_%d" % (n+1) if count > 1 else ""
			var clip := load(BANK + cue + suffix + ".wav") as AudioStream
			if not clip:
				push_error("Missing field audio cue " + cue + suffix)
				return
			variants.append(clip)
		_bank[cue] = variants
	for i in VOICES:
		var voice := AudioStreamPlayer2D.new()
		voice.bus = SFX
		voice.max_distance = 6000
		voice.attenuation = .01
		voice.panning_strength = .72
		add_child(voice)
		_voices.append(voice)
		_starts.append(-100.0)
		_importance.append(-1)
	for key: String in LOOP_NAMES:
		var track := load(BANK + key + ".wav") as AudioStreamWAV
		if not track:
			push_error("Missing field audio loop " + key)
			return
		var loop := track.duplicate() as AudioStreamWAV
		loop.loop_mode = AudioStreamWAV.LOOP_FORWARD
		loop.loop_end = roundi(track.get_length()*track.mix_rate)
		var player := AudioStreamPlayer.new()
		player.stream = loop
		player.bus = AMBIENCE if key == "wind" or key == "fire" else MUSIC
		player.volume_db = -80.0
		add_child(player)
		_loops[key] = player
	# One transport start keeps every arranged stem on the same 96-BPM beat grid.
	for player: AudioStreamPlayer in _loops.values():
		player.play()
	_ready_to_play = true
	_sync_silence()

func _make_bus(bus_name: String, send_to: String) -> void:
	if AudioServer.get_bus_index(bus_name) >= 0:
		return
	AudioServer.add_bus()
	var index := AudioServer.bus_count-1
	AudioServer.set_bus_name(index,bus_name)
	AudioServer.set_bus_send(index,send_to)
	_owned_buses.append(bus_name)

func _apply_levels() -> void:
	for pair in [["music",MUSIC],["ambience",AMBIENCE],["sfx",SFX]]:
		var index := AudioServer.get_bus_index(pair[1])
		if index >= 0:
			var value: float = _levels[pair[0]]
			AudioServer.set_bus_mute(index,value <= 0.0)
			AudioServer.set_bus_volume_db(index,linear_to_db(maxf(.0001,value)))

func set_mix_levels(music: float, ambience: float, effects: float, save := true) -> void:
	_levels = {"music":clampf(music,0,1),"ambience":clampf(ambience,0,1),"sfx":clampf(effects,0,1)}
	_apply_levels()
	if save: _save_controls()

func set_muted(value: bool, save := true) -> void:
	_muted = value
	_sync_silence()
	if save: _save_controls()

func _save_controls() -> void:
	var settings := ConfigFile.new()
	settings.set_value("field_audio","muted",_muted)
	for channel in _levels:
		settings.set_value("field_audio",channel,_levels[channel])
	if settings.save(SETTINGS_PATH) != OK: push_warning("Field audio settings could not be saved.")

func _notification(what: int) -> void:
	if what == NOTIFICATION_APPLICATION_FOCUS_OUT or what == NOTIFICATION_APPLICATION_PAUSED:
		_focused = false
		_sync_silence()
	elif what == NOTIFICATION_APPLICATION_FOCUS_IN or what == NOTIFICATION_APPLICATION_RESUMED:
		_focused = true
		_sync_silence()

func _sync_silence() -> void:
	if not _ready_to_play: return
	var silent := _muted or not _focused or get_tree().paused
	AudioServer.set_bus_mute(AudioServer.get_bus_index(OUTPUT), silent)
	for player: AudioStreamPlayer in _loops.values():
		player.stream_paused = silent
	if silent:
		for voice in _voices:
			voice.stop()

func set_listener_position(world_position: Vector3) -> void:
	_listener = world_position

func set_hearth_proximity(gain: float) -> void:
	_hearth = clampf(gain,0,1)

func set_music_state(value: String) -> void:
	if value in ["field","camp","threat"]: _state = value

func _process(dt: float) -> void:
	if not _ready_to_play: return
	_sync_silence()
	if _muted or not _focused or get_tree().paused: return
	_clock += dt
	var target_duck := -3.4 if _clock < _duck_until else 0.0
	_duck_db = move_toward(_duck_db,target_duck,dt*(55.0 if target_duck < _duck_db else 9.0))
	var target := {
		"field_score":(-1.8 if _state=="field" else -4.2)+_duck_db,
		"camp_score":-.8+_duck_db if _state=="camp" else -80.0,
		"threat_score":-1.3+_duck_db if _state=="threat" else -80.0,
		"wind":-.7,
		"fire":linear_to_db(maxf(.0001,_hearth))-.4
	}
	for key: String in LOOP_NAMES:
		var player: AudioStreamPlayer = _loops[key]
		var gain := lerpf(db_to_linear(player.volume_db),db_to_linear(target[key]),1.0-exp(-dt*3.4))
		player.volume_db = linear_to_db(maxf(.0001,gain))

func _available_voice(priority: int) -> int:
	var slots := VOICES if priority >= 3 else VOICES-RESERVED
	var best := -1
	for i in range(slots):
		if not _voices[i].playing: return i
		if _importance[i] > priority: continue
		if best == -1 or _importance[i] < _importance[best] or (_importance[i] == _importance[best] and _starts[i] < _starts[best]):
			best = i
	return best

func emit_event(requested: String, world_position := NO_SOURCE) -> bool:
	var cue: String = ALIASES.get(requested,requested)
	var kind := requested.get_slice("_", 1)
	if ORE_PITCH.has(kind):
		cue = requested.trim_suffix(kind) + "stone"
	if not CUES.has(cue):
		push_warning("Unknown field audio event: "+requested)
		rejected_event_count += 1
		return false
	if not _ready_to_play or _muted or not _focused or get_tree().paused or float(_levels.sfx)<=0:
		return false
	var params: Array = CUES[cue]
	if _clock-float(_last.get(cue,-100.0)) < float(params[1]): return false
	var slot := _available_voice(int(params[3]))
	if slot < 0: return false
	var voice := _voices[slot]
	var serial := int(_counts.get(cue,0))
	var variants: Array = _bank[cue]
	voice.stream = variants[serial % variants.size()]
	var ore_pitch: float = ORE_PITCH.get(kind, 1.0)
	voice.pitch_scale = ore_pitch * ([1.0,.968,1.026][serial%3] if int(params[3]) < 3 else 1.0)
	var delta := world_position-_listener if world_position.is_finite() else Vector3.ZERO
	var screen := get_viewport().get_visible_rect().size
	var camera := get_viewport().get_camera_3d()
	var lateral := delta.dot(camera.global_basis.x) if camera else delta.x
	voice.position = screen*.5 + Vector2(clampf(lateral/12.0,-.75,.75)*screen.x*.5,0)
	voice.volume_db = float(params[2])-minf(28.0,maxf(0,delta.length()-5.0)*.65)
	voice.play()
	_last[cue] = _clock
	_counts[cue] = serial+1
	_starts[slot] = _clock
	_importance[slot] = int(params[3])
	if int(params[3]) >= 2:
		_duck_until = maxf(_duck_until,_clock+(.24 if int(params[3])>=3 else .11))
	cue_started.emit(cue,_clock,slot)
	return true

func stop_playback() -> void:
	_ready_to_play = false
	for voice in _voices:
		voice.stop()
		voice.stream = null
	for player: AudioStreamPlayer in _loops.values():
		player.stop()
		player.stream = null

func _exit_tree() -> void:
	stop_playback()
	# Remove the child sends before their common mix bus.
	_owned_buses.reverse()
	for bus_name in _owned_buses:
		var index := AudioServer.get_bus_index(bus_name)
		if index >= 0: AudioServer.remove_bus(index)
