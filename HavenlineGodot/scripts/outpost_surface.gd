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
	for bank in [Vector4(-8.5,8.,.34,2.4),Vector4(8.4,8.,.37,2.2),Vector4(-11.,-1.,.28,2.2),Vector4(11.,-7.,.44,2.7),Vector4(-3.,13.,.31,2.1),Vector4(-4.8,8.5,.38,1.9),Vector4(10.7,2.0,.43,2.0),Vector4(4.8,-8.4,.38,2.1),Vector4(-10.,4.5,.40,2.2)]:
		var d: Vector2 = (p-Vector2(bank.x,bank.y))/bank.w
		local_drifts += bank.z*exp(-d.dot(d)*.5)
	# Shallow compacted walkways have real shoulders; all actors sample this
	# identical height function, rather than standing on a separate flat plane.
	var path := 100.0
	for endpoint in [Vector2(0,12.2),Vector2(-6.6,-3.65),Vector2(6.6,-3.65),Vector2(0,-10.7),Vector2(-2.8,2.25)]:
		var origin := Vector2(0,.2)
		var direction: Vector2 = endpoint-origin
		var near: Vector2 = origin+direction*clampf((p-origin).dot(direction)/direction.length_squared(),0,1)
		path=minf(path,p.distance_to(near))
	var shoulders := .052*exp(-pow((path-.85)/.30,2.0))-.055*exp(-pow(path/.48,2.0))
	shoulders *= smoothstep(2.0,5.0,p.length())
	return -.035 + ripple + drift + local_drifts + shoulders

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
				var dx := (height_at(p+Vector2(.02,0))-height_at(p-Vector2(.02,0)))/.04
				var dz := (height_at(p+Vector2(0,.02))-height_at(p-Vector2(0,.02)))/.04
				tool.set_normal(Vector3(-dx,1,-dz).normalized())
				tool.add_vertex(Vector3(p.x, height_at(p), p.y))
	tool.generate_tangents()
	tool.index()
	return tool.commit()
