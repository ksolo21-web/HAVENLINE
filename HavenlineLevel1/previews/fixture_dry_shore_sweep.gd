extends RefCounted
## Test-only bounded horizontal sweep. Never instantiates or moves an actor.
const Terrain = preload("res://terrain_source.gd")
const River = preload("res://river_geometry.gd")
const STEP := 0.025
const POSITION_PAD := 0.025
const SWEEP_PAD := 0.050
const MAX_SWEEP := 9.0
const MAX_RADIUS := 1.0

static func dry_footprint(p: Vector2, radius: float, bank_side: float, extra := 0.0) -> bool:
	if not p.is_finite() or not is_finite(radius) or radius <= 0.0 or radius > MAX_RADIUS or (bank_side != -1.0 and bank_side != 1.0):
		return false
	if not is_finite(extra) or extra < 0.0:
		return false
	var center := Terrain.sample(p)
	var guard_margin := River.DEFAULT_DRY_MARGIN + POSITION_PAD + extra
	# Conservative center bound plus eight direct samples of the true capsule rim.
	# All shore classification comes from the same active geometry source.
	if not bool(center.valid) or float(center.bank_side) != bank_side or float(center.shore_distance) < guard_margin + radius:
		return false
	for i: int in range(8):
		var rim := Terrain.sample(p + Vector2.from_angle(TAU * float(i) / 8.0) * radius)
		if not bool(rim.valid) or float(rim.bank_side) != bank_side or float(rim.shore_distance) < guard_margin:
			return false
	return true

static func allowed_delta(start: Vector2, requested: Vector2, radius: float, bank_side: float) -> Vector2:
	if not requested.is_finite() or requested.length() > MAX_SWEEP or not dry_footprint(start, radius, bank_side, SWEEP_PAD):
		return Vector2.ZERO
	if requested.is_zero_approx():
		return Vector2.ZERO
	var count := ceili(requested.length() / STEP)
	var last := Vector2.ZERO
	for i: int in range(1, count + 1):
		var offset := requested * float(i) / float(count)
		if not dry_footprint(start + offset, radius, bank_side, SWEEP_PAD):
			break
		last = offset
	return last
