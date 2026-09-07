class_name HavenlinePerformanceRecord
extends RefCounted

# Engine interval evidence, not GPU presentation timing or physical-device proof.
# O(1) ring insertion avoids moving 72,000 samples on every frame after 20 minutes.
const CAPACITY := 72000
var intervals := PackedFloat64Array()
var count := 0
var cursor := 0
var sum_ms := 0.0
var total_samples := 0
var resolutions: Array = []

func _init(): intervals.resize(CAPACITY)

func resolution(size: Vector2i):
	var value := [size.x, size.y]
	if resolutions.is_empty() or resolutions[-1] != value: resolutions.append(value)

func sample(milliseconds: float):
	if not is_finite(milliseconds) or milliseconds <= 0: return
	if count == CAPACITY: sum_ms -= intervals[cursor]
	else: count += 1
	intervals[cursor] = milliseconds
	sum_ms += milliseconds
	cursor = (cursor + 1) % CAPACITY
	total_samples += 1

func report() -> Dictionary:
	var ordered := intervals.slice(0, count)
	ordered.sort()
	var over_60 := 0
	var over_30 := 0
	for value in ordered:
		if value > 1000.0 / 60.0 + 0.1: over_60 += 1
		if value > 1000.0 / 30.0 + 0.1: over_30 += 1
	var native_budget := not resolutions.is_empty()
	for size in resolutions:
		if size[0] * size[1] < 3840 * 2160: native_budget = false
	return {"measurement":"engine_frame_intervals_not_display_presentations", "samples":count,
		"total_samples":total_samples,"retained_seconds":sum_ms / 1000.0,
		"average_engine_fps":1000.0 * count / sum_ms if sum_ms > 0 else 0.0,
		"p50_ms":percentile(ordered,0.5),"p95_ms":percentile(ordered,0.95),"p99_ms":percentile(ordered,0.99),
		"maximum_ms":ordered[-1] if count > 0 else 0.0,"over_60hz_budget":over_60,"over_30hz_budget":over_30,
		"internal_resolutions":resolutions.duplicate(true),"uhd_pixel_budget_at_all_recorded_resolutions":native_budget,
		"physical_device_validated":false,"thermal_validated":false,"sustained_4k60_certified":false}

static func percentile(sorted_values: PackedFloat64Array, fraction: float) -> float:
	if sorted_values.is_empty(): return 0.0
	return sorted_values[clampi(int(ceil(fraction * sorted_values.size())) - 1, 0, sorted_values.size() - 1)]

func write(path: String, metadata: Dictionary = {}) -> Error:
	var result := report()
	result["session"] = metadata
	var file := FileAccess.open(path, FileAccess.WRITE)
	if file == null: return FileAccess.get_open_error()
	file.store_string(JSON.stringify(result,"\t")); file.close()
	return OK
