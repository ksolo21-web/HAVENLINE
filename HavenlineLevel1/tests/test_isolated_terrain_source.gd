extends SceneTree
## Opt-in geometry checks only; no rendering, physics contacts or Level 1 progression.
const Source = preload("res://terrain_source.gd")
const River = preload("res://river_geometry.gd")
const EPS := 0.00002
var checks := 0
var failures: Array[String] = []

func _initialize() -> void:
	_check(current_scene == null, "probe does not boot the default scene")
	_check(not bool(Source.sample(Vector2(INF, 0.0)).valid), "nonfinite query rejected")
	_check(not bool(Source.sample(Vector2(0.0, 31.01)).valid), "out-of-grid query rejected")
	_check(bool(Source.sample(Vector2(-31.0, 31.0)).valid), "exact finite grid edge admitted")
	var terrain := Source.terrain_mesh()
	var water := Source.water_mesh()
	_check(is_same(terrain, Source.terrain_mesh()), "one cached terrain mesh source")
	_check(is_same(water, Source.water_mesh()), "one cached water mesh source")
	var arrays := terrain.surface_get_arrays(0)
	var v: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX]
	var indices: PackedInt32Array = arrays[Mesh.ARRAY_INDEX]
	var normals: PackedVector3Array = arrays[Mesh.ARRAY_NORMAL]
	_check(v.size() == 249 * 249, "62m grid at quarter-meter resolution")
	_check(indices.size() == 248 * 248 * 6, "two indexed triangles per terrain cell")
	_check(normals.size() == v.size(), "same-grid normal cardinality")
	var water_arrays := water.surface_get_arrays(0)
	var w: PackedVector3Array = water_arrays[Mesh.ARRAY_VERTEX]
	var wi: PackedInt32Array = water_arrays[Mesh.ARRAY_INDEX]
	_check(w.size() == 249 * 13, "exact accepted water cross-section and span")
	_check(wi.size() > 0 and wi.size() % 3 == 0, "nonempty indexed water triangles")
	var all_y := true
	for p: Vector3 in w:
		all_y = all_y and p.is_finite() and absf(p.y - River.WATER_Y) <= EPS
	_check(all_y, "every water vertex shares accepted Y")
	if w.size() == 249 * 13:
		_check(w[6].is_equal_approx(Vector3(-31.0, River.WATER_Y, -8.6)), "west centerline edge")
		_check(w[(249 - 1) * 13 + 6].is_equal_approx(Vector3(31.0, River.WATER_Y, -7.3)), "east centerline edge")
	if v.size() == 249 * 249 and indices.size() == 248 * 248 * 6:
		for x: float in [-9.0, 1.5, 4.8, 10.0]:
			var center := River.center_at_x(x)
			var dir := River.tangent_at_x(x)
			var north := Vector2(-dir.y, dir.x)
			var half := River.width_at_x(x) * 0.5
			var wet := Source.sample(center)
			_check(bool(wet.valid) and not bool(wet.dry) and float(wet.height) < River.WATER_Y,
				"center submerged at %s" % str(x))
			_check(bool(wet.crossing_reserved) == (x != 4.8), "exact reserve classification")
			for side: float in [-1.0, 1.0]:
				var dry_at := center + north * (half + 1.25) * side
				var dry := Source.sample(dry_at)
				_check(bool(dry.valid) and bool(dry.dry) and float(dry.bank_side) == side,
					"both sides dry with sign retained")
				_check(float(dry.height) > River.WATER_Y, "dry crest above water")
				_check(absf(float(dry.shore_distance) - River.shore_distance(dry_at)) <= EPS,
					"no parallel shore formula")
				_check_near_triangle(dry_at, v, indices)
	print(JSON.stringify({"suite":"T02_terrain_source_only", "checks":checks, "failures":failures,
		"active_world_changed":false, "native_contacts_tested":false, "live_terrain_bound":false}))
	for label in failures:
		push_error(label)
	quit(0 if failures.is_empty() else 1)

func _check_near_triangle(p: Vector2, v: PackedVector3Array, indices: PackedInt32Array) -> void:
	var grid_at := (p + Vector2.ONE * 31.0) / .25
	var x := clampi(floori(grid_at.x), 0, 247)
	var z := clampi(floori(grid_at.y), 0, 247)
	var first := (z * 248 + x) * 6
	for cell_triangle: int in [0, 3]:
		var a := v[indices[first + cell_triangle]]
		var b := v[indices[first + cell_triangle + 1]]
		var c := v[indices[first + cell_triangle + 2]]
		var point := (a + b * 2.0 + c * 3.0) / 6.0
		var sampled := Source.sample(Vector2(point.x, point.z))
		_check((b - a).cross(c - a).y < 0.0, "accepted triangle winding")
		_check(bool(sampled.valid) and absf(float(sampled.height) - point.y) <= EPS,
			"both triangle halves agree with rendered indexed Y")

func _check(ok: bool, label: String) -> void:
	checks += 1
	if not ok:
		failures.append(label)
