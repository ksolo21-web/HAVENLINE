extends RefCounted
# A continuous, gently sculpted terrain mesh, not stacked primitive scenery.
# Both actors and static placements sample this same surface for ground contact.
const HALF := 31.0
const STEP := 0.5
static func height_at(p: Vector2) -> float:
	var ripple := sin(p.x * .53 + sin(p.y * .26)) * cos(p.y * .48) * .055
	var edge := smoothstep(13.5, 24.0, maxf(absf(p.x), absf(p.y) * .86))
	var drift := edge * (0.28 + 0.32 * pow(sin(p.x * .23 + p.y * .19), 2.0))
	return -.035 + ripple + drift

static func mesh() -> ArrayMesh:
	var tool := SurfaceTool.new()
	tool.begin(Mesh.PRIMITIVE_TRIANGLES)
	var n := int(HALF * 2.0 / STEP)
	for z in range(n):
		for x in range(n):
			var a := Vector2(-HALF + x * STEP, -HALF + z * STEP)
			var b := a + Vector2(STEP, 0)
			var c := a + Vector2(0, STEP)
			var d := a + Vector2(STEP, STEP)
			for p in [a,b,c,b,d,c]:
				tool.set_uv(p * .08)
				tool.add_vertex(Vector3(p.x, height_at(p), p.y))
	tool.generate_normals()
	tool.index()
	return tool.commit()
