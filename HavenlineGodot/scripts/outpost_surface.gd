extends RefCounted
# A continuous, gently sculpted terrain mesh, not stacked primitive scenery.
# Both actors and static placements sample this same surface for ground contact.
const HALF := 31.0
const STEP := 0.5
static func height_at(p: Vector2) -> float:
	var ripple := sin(p.x * .53 + sin(p.y * .26)) * cos(p.y * .48) * .055
	var edge := smoothstep(13.5, 24.0, maxf(absf(p.x), absf(p.y) * .86))
	var drift := edge * (0.64 + 0.52 * pow(sin(p.x * .19 + p.y * .15), 2.0))
	var local_drifts := 0.0
	for bank in [Vector4(-8.5,8.,.34,2.4),Vector4(8.4,8.,.37,2.2),Vector4(-11.,-1.,.28,2.2),Vector4(11.,-7.,.44,2.7),Vector4(-3.,13.,.31,2.1)]:
		var d: Vector2 = (p-Vector2(bank.x,bank.y))/bank.w
		local_drifts += bank.z*exp(-d.dot(d)*.5)
	return -.035 + ripple + drift + local_drifts

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
	tool.generate_tangents()
	tool.index()
	return tool.commit()
