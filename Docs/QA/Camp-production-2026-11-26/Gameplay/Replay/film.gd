extends "res://tests/field_route.gd"

var encoder := StreamPeerTCP.new()
var bus_capture := AudioEffectCapture.new()
var recording := false
var following_supply := false
var total_frames := 0
var total_samples := 0
var hz := 24.0
var chapter := ""
var plate_mode := OS.get_environment("HL_PLATES") == "1"
var plate_labels := {"Cross the production aisle": "01-camp", "Watch the outfeed without standing on the saw apron":"02-sawmill", "Inspect the saw from the operating apron at default zoom":"06-sawmill-at-feed-1x",
	"Inspect the operating apron at an actual pinch zoom":"07-sawmill-at-feed-2x",
	"Inspect the drill passage at an actual pinch zoom":"08-stoneworks-at-2x",
	"Watch stone finish after leaving the drill":"03-stoneworks", "Let both portions cook in the machine":"04-cooker",
	"A waiting customer pays at the north fence":"05-counter"}
var plate_seen := {}


func _initialize() -> void:
	recording = OS.get_environment("HL_RECORD") == "1"
	if recording:
		hz = float(OS.get_environment("HL_OUTPUT_FPS"))
		if encoder.connect_to_host("127.0.0.1", int(OS.get_environment("HL_STREAM_PORT"))) != OK:
			quit(11)
			return
		while encoder.get_status() == StreamPeerTCP.STATUS_CONNECTING:
			encoder.poll()
			OS.delay_usec(100)
		if encoder.get_status() != StreamPeerTCP.STATUS_CONNECTED:
			quit(12)
			return
		bus_capture.buffer_length = 3.0
		AudioServer.add_bus_effect(AudioServer.get_bus_index("Master"),bus_capture)
		process_frame.connect(capture_frame)
	if plate_mode: process_frame.connect(capture_plate)
	super._initialize()

func packet(header: Dictionary, data := PackedByteArray()) -> void:
	var encoded := JSON.stringify(header).to_utf8_buffer()
	encoder.big_endian = true
	encoder.put_u32(encoded.size())
	encoder.put_u32(data.size())
	encoder.put_data(encoded)
	if not data.is_empty():
		encoder.put_data(data)

func capture_frame() -> void:
	var available := bus_capture.get_frames_available()
	if available:
		packet({"type":"audio","offset":total_samples,"samples":available},bus_capture.get_buffer(available).to_byte_array())
		total_samples += available
	if chapter.is_empty() or finished or not is_instance_valid(field): return
	RenderingServer.force_draw(false, 1.0 / hz)
	var img := root.get_texture().get_image()
	packet({"type":"picture", "chapter":chapter, "engine_frame":Engine.get_process_frames(),
		"physics_tick":tick, "audio_start":total_samples, "image_size":[img.get_width(), img.get_height()],
		"render_scale":root.scaling_3d_scale, "camera":str(root.get_camera_3d().get_path())},img.save_jpg_to_buffer(.93))
	total_frames += 1

func snapshot() -> Dictionary:
	var actor_at: Vector3 = field.actor.global_position
	var data: Dictionary = field.inventory.settlement.duplicate(true)
	return {"scene":field.scene_file_path,"physics_tick":tick,"engine_frame":Engine.get_process_frames(),
		"pos":pt(actor_at), "phase":phases[index].label, "inside":field.field_env.is_inside_camp(actor_at),
		"loading_timber_or_stone":field.processors.at_station(actor_at),"loading_cooker":field.lakeshore.at_cooker(actor_at),
		"kitchen_active":field.lakeshore.working,"worker_phase":field.survivor.phase,"worker_xyz":pt(field.survivor.actor.global_position), "carried":field.inventory.carried.duplicate(),
		"settlement":data, "same_camera":root.get_camera_3d()==camera or dry,
		"zoom":field.get_zoom_ratio(),"hud":field.opening_hud.prompt.text}

func begin_phase() -> void:
	super.begin_phase()
	chapter=String(phases[index].get("film",""))

func advance() -> void:
	if index==phases.size()-1 and recording:
		packet({"type":"finish","frames":total_frames,"samples_before_tail":total_samples,"lost":bus_capture.get_discarded_frames(),"mix_hz":AudioServer.get_mix_rate()})
	super.advance()

func capture_plate() -> void:
	if finished or index >= phases.size() or not is_instance_valid(field) or tick-stage_tick < 15: return
	var label: String = phases[index].label
	if not plate_labels.has(label) or plate_seen.has(label): return
	RenderingServer.force_draw(false, 1.0 / 24.0)
	var picture := root.get_texture().get_image()
	if picture.get_size() != Vector2i(3840,2160) or root.scaling_3d_scale != 1.0:
		push_error("4K capture size or scale mismatch")
		quit(7)
		return
	plate_seen[label] = true
	var name: String = plate_labels[label]
	picture.save_jpg(out_dir.path_join(name+".jpg"), .94)
	event("native_4k", {"name":name,"state":snapshot()})

func execute(row: Dictionary) -> void:
	if row.action != "watch_feeder":
		var local_time := (tick-stage_tick)/60.0
		chapter = String(row.get("film","")) if local_time >= row.get("record_from",0.0) and local_time < row.get("record_until",INF) else ""
		super.execute(row)
		return
	steer(Vector2.ZERO)
	if tick-stage_tick > int(row.timeout)*60:
		event("timed_out_waiting_for_feeder",snapshot())
		finished=true
		quit(4)
		return
	var worker=field.survivor
	if worker.phase=="supply_out" and worker.actor.global_position.z < -3.70 or worker.phase=="supply_unload":
		following_supply=true
		chapter="A survivor carries stored material to a machine"
	if following_supply and worker.phase=="supply_back":
		chapter=""
		advance()
