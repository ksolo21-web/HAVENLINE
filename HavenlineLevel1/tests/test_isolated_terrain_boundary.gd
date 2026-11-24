extends SceneTree
# All unmodified rendered edge segments at five fractions; a near-inside row
# independently reconstructs the adjacent indexed triangle in each direction.
const Source = preload("res://terrain_source.gd")
const EPS := 0.00002
const SEGMENTS := 248
const SIDE := 249

func edge_index(edge: int, i: int) -> int:
	var positions: Array[int] = [i, SIDE * SEGMENTS + i, SIDE * i, SIDE * i + SEGMENTS]
	return positions[edge]

func ordered_edge_matches(points: PackedVector3Array) -> int:
	var mismatches := 0
	for edge in range(4):
		for i in range(SEGMENTS):
			var a := points[edge_index(edge, i)]
			var b := points[edge_index(edge, i + 1)]
			for fraction in [0.0, 0.25, 0.5, 0.75, 1.0]:
				var expected := a.lerp(b, float(fraction))
				var actual := Source.sample(Vector2(expected.x, expected.z))
				if not bool(actual.valid) or absf(float(actual.height) - expected.y) > EPS:
					mismatches += 1
	return mismatches

func _initialize() -> void:
	var arrays := Source.terrain_mesh().surface_get_arrays(0)
	var points: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX]
	var indices: PackedInt32Array = arrays[Mesh.ARRAY_INDEX]
	var edge_fail := ordered_edge_matches(points)
	var near_checks := 0
	var near_fail := 0
	var above_strict_boundary_fail := 0
	for n in range(0, indices.size(), 3):
		var a := points[indices[n]]
		var b := points[indices[n + 1]]
		var c := points[indices[n + 2]]
		var min_x := minf(a.x, minf(b.x, c.x))
		var max_x := maxf(a.x, maxf(b.x, c.x))
		var min_z := minf(a.z, minf(b.z, c.z))
		var max_z := maxf(a.z, maxf(b.z, c.z))
		if min_x != -31.0 and max_x != 31.0 and min_z != -31.0 and max_z != 31.0:
			continue
		var expected := a * 0.25 + b * 0.375 + c * 0.375
		var actual := Source.sample(Vector2(expected.x, expected.z))
		near_checks += 1
		if not bool(actual.valid) or absf(float(actual.height) - expected.y) > EPS:
			near_fail += 1
	for p in [Vector2(NAN, 0), Vector2(0, INF), Vector2(31.0001, 0),
		Vector2(-31.0001, 0), Vector2(0, 31.0001), Vector2(0, -31.0001)]:
		if Source.sample(p) != {"valid": false}:
			above_strict_boundary_fail += 1
	print("TERRAIN_EDGE_REPAIR edge=4960 failures=", edge_fail, " near=", near_checks,
		" near_failures=", near_fail, " strict_outside=6 outside_failures=", above_strict_boundary_fail)
	quit(0 if edge_fail == 0 and near_checks == 1976 and near_fail == 0 and above_strict_boundary_fail == 0 else 1)
