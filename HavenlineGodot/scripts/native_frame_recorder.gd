extends RefCounted

const CAPACITY := 262144
var intervals := PackedFloat64Array()
var count := 0
var cursor := 0
var last_usec := 0
var segment_start_usec := 0
var warmup := 180
var discontinuities := 0
var min_dimensions := Vector2i(2147483647, 2147483647)
var max_dimensions := Vector2i.ZERO

func _init():
	intervals.resize(CAPACITY)

func reset_segment():
	last_usec = 0
	segment_start_usec = 0
	count = 0
	cursor = 0
	warmup = 180
	discontinuities += 1
	min_dimensions = Vector2i(2147483647, 2147483647)
	max_dimensions = Vector2i.ZERO

func sample(now: int, dimensions: Vector2i):
	if warmup > 0:
		warmup -= 1
		last_usec = now
		return
	if segment_start_usec == 0: segment_start_usec = last_usec
	if last_usec > 0:
		intervals[cursor] = float(now - last_usec) / 1000.0
		cursor = (cursor + 1) % CAPACITY
		count = mini(count + 1, CAPACITY)
		min_dimensions = Vector2i(mini(min_dimensions.x, dimensions.x), mini(min_dimensions.y, dimensions.y))
		max_dimensions = Vector2i(maxi(max_dimensions.x, dimensions.x), maxi(max_dimensions.y, dimensions.y))
	last_usec = now

func report(context: Dictionary) -> Dictionary:
	var result := context.duplicate(true)
	var sorted := intervals.slice(0, count)
	sorted.sort()
	var total := 0.0
	var over_deadline := 0
	for value in sorted:
		total += value
		if value > 1000.0 / 60.0 + .1: over_deadline += 1
	result.merge({
		"schema":1, "sample_count":count, "retained_sample_seconds":total / 1000.0,
		"average_callback_fps":1000.0 * count / total if total > 0 else 0,
		"p99_callback_ms":sorted[mini(count-1, int(ceil(count*.99))-1)] if count > 0 else 0,
		"max_callback_ms":sorted[-1] if count > 0 else 0,
		"over_60fps_deadline":over_deadline, "segment_resets":discontinuities,
		"minimum_internal_dimensions":[min_dimensions.x, min_dimensions.y] if count > 0 else [],
		"maximum_internal_dimensions":[max_dimensions.x, max_dimensions.y] if count > 0 else [],
		"measurement":"Application frame callbacks, not Android display presentation or GPU timestamps.",
		"physical_device_verified":false, "thermal_evidence_verified":false,
		"performance_certified":false, "whole_rig_approved":false,
		"release_status":"BLOCKED: outstanding production and physical-device acceptance gates."
	}, true)
	return result
