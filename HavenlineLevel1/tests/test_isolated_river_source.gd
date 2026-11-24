extends SceneTree
## Opt-in source-contract test only. No default scene, gameplay, terrain binding or saves.
const River = preload("res://river_geometry.gd")
const EPS := 0.002
var checks := 0
var failures: Array[String] = []

func _initialize() -> void:
	_check(current_scene == null, "fixture must not open the default scene")
	_check(River.ANCHORS.size() == 10, "ten canonical anchors")
	_check(River.LAYOUT_VERSION == "river_v1_mapspan", "accepted layout identity")
	_check(is_equal_approx(River.WATER_Y, -0.34), "accepted water datum")
	_check(is_equal_approx(River.DEFAULT_DRY_MARGIN, 1.05), "accepted dry margin")
	_check(River.CROSSING_X == [-9.0, 1.5, 10.0], "three retained reserve centers")
	_check(River.plan_samples(0.25).size() == 249, "62m span with both edge samples")
	_check(River.plan_samples(0.25).front().x == -31.0, "west world edge")
	_check(River.plan_samples(0.25).back().x == 31.0, "east world edge")
	for anchor: Vector2 in River.ANCHORS:
		_check(River.center_at_x(anchor.x).is_equal_approx(anchor), "exact anchor %s" % str(anchor))
	for x: float in [-9.0, 1.5, 10.0]:
		var center := River.center_at_x(x)
		var tangent := River.tangent_at_x(x)
		var north := Vector2(-tangent.y, tangent.x)
		_check(River.crossing_reserved(center), "reserved crossing at %s" % str(x))
		for side: float in [-1.0, 1.0]:
			var wet := center + north * (River.width_at_x(x) * 0.45) * side
			var dry := River.dry_position(wet)
			var wet_query := River.query(wet)
			var dry_query := River.query(dry)
			_check(River.is_water(wet), "wet control inside water")
			_check(float(wet_query.side) == side, "wet control side")
			_check(float(dry_query.side) == side, "recovery cannot change bank")
			_check(float(dry_query.shore_distance) >= River.DEFAULT_DRY_MARGIN - EPS,
				"recovery at dry edge")
			_check(River.dry_position(dry).distance_to(dry) <= EPS, "recovery idempotent")
	_check(not River.crossing_reserved(River.center_at_x(4.8)), "off-reserve wet control")
	_check(not River.crossing_reserved(Vector2(1.5, 5.8)), "inland inside reserve X, not in crossing mask")
	print(JSON.stringify({"suite":"T02_source_only_not_live_terrain", "checks":checks,
		"failures":failures, "live_terrain_bound":false, "native_playtest":false}))
	for label in failures:
		push_error(label)
	quit(0 if failures.is_empty() else 1)

func _check(ok: bool, label: String) -> void:
	checks += 1
	if not ok:
		failures.append(label)
