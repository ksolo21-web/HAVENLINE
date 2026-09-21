extends SceneTree

const Transform = preload("res://scripts/world_transform.gd")
const CampView = preload("res://scripts/camp_construction_view.gd")

const WARMUP_FRAMES := 60
const SAMPLE_FRAMES := 180

var candidate := "local-working-tree"
var samples: Array[float] = []

func _initialize() -> void:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--candidate="):
			candidate = argument.trim_prefix("--candidate=")
	call_deferred("run")

func simulation_ack(intent: Dictionary) -> Dictionary:
	var receipt := intent.duplicate(true)
	receipt["authority_source"] = "simulation"
	receipt["authority_applied"] = true
	return receipt

func fail(reason: String) -> void:
	print(JSON.stringify({
		"schema_version": 1,
		"task_id": "T11",
		"candidate": candidate,
		"passed": false,
		"reason": reason,
		"sample_count": samples.size()
	}))
	quit(1)

func run() -> void:
	var engine = Transform.new()
	if not engine.configure_from_file():
		fail("T10 catalog failed to configure")
		return
	if not engine.register_target("perf-camp", "seed"):
		fail("performance target registration failed")
		return

	var inventory := {"wood": 100, "stone": 100, "metal": 20, "fuel": 10}
	var foundation_intent: Dictionary = engine.commit_transform(
		"perf-foundation",
		"framework_anchor_seed_to_foundation",
		"perf-camp",
		inventory
	)
	if not bool(foundation_intent.get("passed", false)):
		fail("foundation intent failed")
		return
	var foundation_receipt: Dictionary = engine.accept_authoritative_receipt(simulation_ack(foundation_intent))
	if not bool(foundation_receipt.get("passed", false)) or not bool(foundation_receipt.get("applied", false)):
		fail("foundation bootstrap receipt failed")
		return

	var view = CampView.new()
	root.add_child(view)
	await process_frame
	if not view.configure("perf-camp", "camp_shelter_reinforced"):
		fail("reinforced camp view failed to configure")
		return
	if not view.set_placement_context(Vector3.ZERO, []):
		fail("valid performance placement blocked")
		return

	var reinforced_intent: Dictionary = engine.commit_transform(
		"perf-reinforced",
		"framework_anchor_foundation_to_reinforced",
		"perf-camp",
		inventory,
		["harvesting_online"]
	)
	if not bool(reinforced_intent.get("passed", false)) or not view.show_commit(reinforced_intent):
		fail("reinforced committing state failed")
		return

	for _i in WARMUP_FRAMES:
		await process_frame

	for _i in SAMPLE_FRAMES:
		await process_frame
		var value_ms := float(Performance.get_monitor(Performance.TIME_PROCESS)) * 1000.0
		if is_finite(value_ms) and value_ms >= 0.0:
			samples.append(value_ms)

	if samples.size() != SAMPLE_FRAMES:
		fail("incomplete CPU frame sample set")
		return

	samples.sort()
	var p95_index := int(floor(float(samples.size() - 1) * 0.95))
	var cpu_p95 := samples[p95_index]
	var cpu_max := samples[-1]
	var total := 0.0
	for value in samples:
		total += value
	var cpu_mean := total / float(samples.size())

	var report := {
		"schema_version": 1,
		"task_id": "T11",
		"candidate": candidate,
		"passed": true,
		"state": "reinforced_committing",
		"warmup_frames": WARMUP_FRAMES,
		"sample_count": samples.size(),
		"fixed_fps": 60,
		"cpu_frame_statistic": "p95_after_warmup",
		"cpu_frame_ms_p95": cpu_p95,
		"cpu_frame_ms_max": cpu_max,
		"cpu_frame_ms_mean": cpu_mean,
		"measurement_method": "Godot headless fixed-fps 60 process-time probe; no PNG encoding or software raster timing in CPU sample",
		"physical_4k60_certified": false
	}
	print(JSON.stringify(report))
	quit(0)
