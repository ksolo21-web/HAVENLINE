extends RefCounted
## Callable, inactive sources for the later replacement composition.
## Mesh resources are shared source data; consumers must not mutate their arrays.
## This seam does not create actors, physics bodies, materials, saves or scene nodes.
const Surface = preload("res://accepted_t02_surface.gd")
const River = preload("res://river_geometry.gd")
static var _edge_source_vertices := PackedVector3Array()

static func terrain_mesh() -> ArrayMesh:
	return Surface.mesh()

static func water_mesh() -> ArrayMesh:
	return Surface.water_mesh()

static func _indexed_height(p: Vector2) -> float:
	# The accepted interior uses its triangle interpolant. On the closed perimeter
	# it falls back to analytic height, so use the actual rendered edge vertices.
	if absf(p.x) != Surface.HALF and absf(p.y) != Surface.HALF:
		return Surface.height_at(p)
	if _edge_source_vertices.is_empty():
		_edge_source_vertices = terrain_mesh().surface_get_arrays(0)[Mesh.ARRAY_VERTEX]
	var segments := int(2.0 * Surface.HALF / Surface.STEP)
	var side := segments + 1
	var fixed_x := absf(p.x) == Surface.HALF
	var along := p.y if fixed_x else p.x
	var t := (along + Surface.HALF) / Surface.STEP
	# At the high corner use the final segment endpoint (t - segment == 1).
	var segment := mini(floori(t), segments - 1)
	var fixed := 0 if (p.x if fixed_x else p.y) < 0.0 else segments
	var a := segment * side + fixed if fixed_x else fixed * side + segment
	var b := a + (side if fixed_x else 1)
	return lerpf(_edge_source_vertices[a].y, _edge_source_vertices[b].y, t - float(segment))

static func sample(p: Vector2) -> Dictionary:
	# The source math has out-of-grid fallbacks for internal evidence callers.
	# This ownership boundary does not offer ground beyond the visible indexed terrain.
	if not p.is_finite() or absf(p.x) > Surface.HALF or absf(p.y) > Surface.HALF:
		return {"valid":false}
	var q := River.query(p)
	var shore_distance := float(q.shore_distance)
	return {
		"valid":true,
		"height":_indexed_height(p),
		"shore_distance":shore_distance,
		"bank_side":float(q.side),
		"dry":shore_distance >= River.DEFAULT_DRY_MARGIN,
		"crossing_reserved":River.crossing_reserved(p),
	}
