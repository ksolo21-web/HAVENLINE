extends RefCounted
## A swept spoke is a pair of triangles between consecutive pivot/tip poses.
## Native BVH rays find intersections on its edges. The mesh-plane test covers
## a target whose entire cross section lies between the edges of a fast sweep.
const SLICES := 24
const EPS := .000002
var faces: PackedVector3Array
var bounds: AABB
var slices: Array = []

func _init(mesh: TriangleMesh) -> void:
	faces = mesh.get_faces()
	bounds = AABB(faces[0], Vector3.ZERO)
	for point in faces:
		bounds = bounds.expand(point)
	for i in SLICES:
		slices.append([])
	for i in range(0, faces.size(), 3):
		var low := minf(faces[i].y, minf(faces[i+1].y, faces[i+2].y))
		var high := maxf(faces[i].y, maxf(faces[i+1].y, faces[i+2].y))
		for layer in range(_slice(low), _slice(high) + 1):
			slices[layer].append(i)

func _slice(y: float) -> int:
	return clampi(floori((y - bounds.position.y) * SLICES / maxf(bounds.size.y, EPS)), 0, SLICES-1)

static func _outside(box: AABB, point: Vector3, inward: Vector3) -> bool:
	var farthest := box.position
	if inward.x >= 0.0: farthest.x = box.end.x
	if inward.y >= 0.0: farthest.y = box.end.y
	if inward.z >= 0.0: farthest.z = box.end.z
	return inward.dot(farthest - point) < -EPS * inward.length()

func triangle_contact(a: Vector3, b: Vector3, c: Vector3) -> Vector3:
	var n := (b-a).cross(c-a)
	if n.length_squared() < 1e-16: return Vector3.INF
	n = n.normalized()
	var ab := n.cross(b-a)
	var bc := n.cross(c-b)
	var ca := n.cross(a-c)
	if _outside(bounds,a,n) or _outside(bounds,a,-n) or _outside(bounds,a,ab) or _outside(bounds,b,bc) or _outside(bounds,c,ca):
		return Vector3.INF
	var first := _slice(minf(a.y,minf(b.y,c.y)) - EPS)
	var last := _slice(maxf(a.y,maxf(b.y,c.y)) + EPS)
	for layer in range(first,last+1):
		for i: int in slices[layer]:
			var p := faces[i]
			var q := faces[i+1]
			var r := faces[i+2]
			var dp := n.dot(p-a)
			var dq := n.dot(q-a)
			var dr := n.dot(r-a)
			if minf(dp,minf(dq,dr)) > EPS or maxf(dp,maxf(dq,dr)) < -EPS:
				continue
			var hit := _edge(p,q,dp,dq,a,b,c,ab,bc,ca)
			if not hit.is_finite(): hit = _edge(q,r,dq,dr,a,b,c,ab,bc,ca)
			if not hit.is_finite(): hit = _edge(r,p,dr,dp,a,b,c,ab,bc,ca)
			if hit.is_finite(): return hit
	return Vector3.INF

static func _edge(p: Vector3, q: Vector3, dp: float, dq: float, a: Vector3, b: Vector3, c: Vector3, ab: Vector3, bc: Vector3, ca: Vector3) -> Vector3:
	if (dp > EPS and dq > EPS) or (dp < -EPS and dq < -EPS): return Vector3.INF
	var hit := p if absf(dp) <= EPS else q
	if dp * dq < 0.0:
		hit = p.lerp(q, dp/(dp-dq))
	if ab.dot(hit-a) < -EPS or bc.dot(hit-b) < -EPS or ca.dot(hit-c) < -EPS:
		return Vector3.INF
	return hit
