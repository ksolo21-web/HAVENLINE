extends RefCounted
# T02: one continuous indexed surface shared by scenery, actors and shoreline.
# The approved T01 trees are NOT regenerated. No camera, fence or station changes.
const HALF := 31.0
const STEP := 0.25
const LAKE_CENTER := Vector2(0.0, -13.85)
const LAKE_HALF := Vector2(15.2, 1.85)
const WATER_Y := -0.34
const LAND_MARGIN := 0.32
const WORK_CENTER := Vector2(0.0, 0.3)
const WORK_HALF := Vector2(9.75, 6.7)
const BAY_CENTER := Vector2(-6.5, -9.4)
const BAY_HALF := Vector2(6.6, 1.95)
static var _mesh: ArrayMesh
static var _water_mesh: ArrayMesh
static var _heights := PackedFloat32Array()

static func rounded_rect(p: Vector2, center: Vector2, half_size: Vector2, radius: float) -> float:
	var q := (p-center).abs()-half_size+Vector2.ONE*radius
	return q.max(Vector2.ZERO).length()+minf(maxf(q.x,q.y),0.0)-radius

static func work_distance(p: Vector2) -> float:
	var main := rounded_rect(p,WORK_CENTER,WORK_HALF,0.72)
	var bay := rounded_rect(p,BAY_CENTER,BAY_HALF,0.65)
	var connector := rounded_rect(p,Vector2(-4.3,-6.8),Vector2(4.45,1.25),0.5)
	return minf(main,minf(bay,connector))

static func lake_distance(p: Vector2) -> float:
	# World-unit capsule distance: consistent bank width along the full east-west
	# lake, including both rounded ends. Water continues beyond x=+/-14.2.
	var q := (p-LAKE_CENTER).abs()
	var straight_half := LAKE_HALF.x-LAKE_HALF.y
	return Vector2(maxf(q.x-straight_half,0.0),q.y).length()-LAKE_HALF.y

static func southern_shore_y(x: float, margin := LAND_MARGIN) -> float:
	var radius := LAKE_HALF.y+maxf(margin,0.0)+0.00005
	var dx := maxf(absf(x-LAKE_CENTER.x)-(LAKE_HALF.x-LAKE_HALF.y),0.0)
	return LAKE_CENTER.y+sqrt(maxf(radius*radius-dx*dx,0.0))

static func land_position(p: Vector2, margin := LAND_MARGIN) -> Vector2:
	if not p.is_finite(): return Vector2.ZERO
	# End-to-end water separates the former north strip from the active camp.
	# Recover old actors to the connected south bank, preserving X instead of
	# radially flinging them beyond the playable east/west bounds.
	var radius := LAKE_HALF.y+maxf(margin,0.0)
	var in_span := absf(p.x-LAKE_CENTER.x)<=LAKE_HALF.x+maxf(margin,0.0)
	if not in_span: return p
	var shore := southern_shore_y(p.x,margin)
	if p.y>=shore: return p
	# Only the existing playable north strip and lake need recovery; decorative
	# far-north forest geometry is not an actor destination or a terrain clamp.
	if p.y>=-16.2001 or lake_distance(p)<radius-LAKE_HALF.y:
		return Vector2(p.x,shore)
	return p

static func _shape_height(p: Vector2) -> float:
	# Preserve the accepted outer woodland terrain exactly, including seated roots.
	var ripple := sin(p.x*.53+sin(p.y*.26))*cos(p.y*.48)*.055
	var edge := smoothstep(13.5,24.0,maxf(absf(p.x),absf(p.y)*.86))
	var drift := edge*(.64+.52*pow(sin(p.x*.19+p.y*.15),2.0))
	var local_drifts := 0.0
	for bank in [Vector4(-8.5,8.,.34,2.4),Vector4(8.4,8.,.37,2.2),Vector4(-11.,-1.,.28,2.2),Vector4(11.,-7.,.44,2.7),Vector4(-3.,13.,.31,2.1),Vector4(-4.8,8.5,.38,1.9),Vector4(10.7,2.0,.43,2.0),Vector4(4.8,-8.4,.38,2.1),Vector4(-10.,4.5,.40,2.2)]:
		var d: Vector2 = (p-Vector2(bank.x,bank.y))/bank.w
		local_drifts += bank.z*exp(-d.dot(d)*.5)
	var path := 100.0
	for endpoint in [Vector2(0,12.2),Vector2(-6.6,-3.65),Vector2(6.6,-3.65),Vector2(0,-10.7),Vector2(-2.8,2.25)]:
		var origin := Vector2(0,.2)
		var direction: Vector2 = endpoint-origin
		var near: Vector2 = origin+direction*clampf((p-origin).dot(direction)/direction.length_squared(),0,1)
		path=minf(path,p.distance_to(near))
	var shoulders := (.052*exp(-pow((path-.85)/.30,2.0))-.055*exp(-pow(path/.48,2.0)))*smoothstep(2.0,5.0,p.length())
	var original := -.035+ripple+drift+local_drifts+shoulders
	var wd := work_distance(p)
	var floor_height := 0.008*sin(p.x*.22)*sin(p.y*.26)
	var snow_rim := .12*exp(-pow((wd-.36)/.62,2.0))
	var result := lerpf(floor_height,original,smoothstep(-.12,1.80,wd))+snow_rim
	var shore := lake_distance(p)
	# A submerged basin and rounded snow-covered lip, connected without overlays.
	var bank_height := lerpf(WATER_Y-.85,.16,smoothstep(-.46,.30,shore))
	bank_height += .19*exp(-pow((shore-.38)/.37,2.0))
	result=lerpf(bank_height,result,smoothstep(.54,1.32,shore))
	return result

static func _ensure_heights():
	if not _heights.is_empty(): return
	var n := int(HALF*2.0/STEP);var side := n+1
	_heights.resize(side*side)
	for z in range(side):
		for x in range(side):
			_heights[z*side+x]=_shape_height(Vector2(-HALF+x*STEP,-HALF+z*STEP))

static func height_at(p: Vector2) -> float:
	# Barycentric sampling of the actual indexed triangles, not an approximate
	# second collision plane. Actors and approved tree roots use these same faces.
	_ensure_heights()
	if absf(p.x)>=HALF or absf(p.y)>=HALF: return _shape_height(p)
	var n := int(HALF*2.0/STEP);var side := n+1
	var q := (p+Vector2.ONE*HALF)/STEP
	var x := clampi(floori(q.x),0,n-1);var z := clampi(floori(q.y),0,n-1)
	var u := q.x-x;var v := q.y-z;var i := z*side+x
	var a := _heights[i];var b := _heights[i+1];var c := _heights[i+side];var d := _heights[i+side+1]
	if u+v<=1.0: return a+(b-a)*u+(c-a)*v
	return d+(b-d)*(1.0-v)+(c-d)*(1.0-u)

static func _indexed_grid() -> ArrayMesh:
	_ensure_heights()
	var n := int(HALF*2.0/STEP)
	var side := n+1
	var vertices := PackedVector3Array();vertices.resize(side*side)
	var normals := PackedVector3Array();normals.resize(side*side)
	var uv := PackedVector2Array();uv.resize(side*side)
	var indices := PackedInt32Array();indices.resize(n*n*6)
	for z in range(side):
		for x in range(side):
			var p := Vector2(-HALF+x*STEP,-HALF+z*STEP)
			var i := z*side+x
			vertices[i]=Vector3(p.x,_heights[i],p.y);uv[i]=p*.08
	for z in range(side):
		for x in range(side):
			var l := maxi(0,x-1);var r := mini(n,x+1)
			var b := maxi(0,z-1);var t := mini(n,z+1)
			var dx := (vertices[z*side+r].y-vertices[z*side+l].y)/(float(r-l)*STEP)
			var dz := (vertices[t*side+x].y-vertices[b*side+x].y)/(float(t-b)*STEP)
			normals[z*side+x]=Vector3(-dx,1,-dz).normalized()
	for z in range(n):
		for x in range(n):
			var a := z*side+x;var i := (z*n+x)*6
			indices[i]=a;indices[i+1]=a+1;indices[i+2]=a+side
			indices[i+3]=a+1;indices[i+4]=a+side+1;indices[i+5]=a+side
	var arrays: Array=[];arrays.resize(Mesh.ARRAY_MAX)
	arrays[Mesh.ARRAY_VERTEX]=vertices;arrays[Mesh.ARRAY_NORMAL]=normals
	arrays[Mesh.ARRAY_TEX_UV]=uv;arrays[Mesh.ARRAY_INDEX]=indices
	var result := ArrayMesh.new();result.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,arrays)
	return result

static func mesh() -> ArrayMesh:
	if _mesh==null: _mesh=_indexed_grid()
	return _mesh

static func water_mesh() -> ArrayMesh:
	if _water_mesh!=null: return _water_mesh
	var tool := SurfaceTool.new();tool.begin(Mesh.PRIMITIVE_TRIANGLES)
	var contour := PackedVector2Array()
	# Keep the contour buried 0.20 world units inside the physical snow bank.
	# Ninety-six samples per semicircle retain the 192-triangle water budget.
	var radius := LAKE_HALF.y+0.20
	var straight_half := LAKE_HALF.x-LAKE_HALF.y
	for side in [1.0,-1.0]:
		for i in range(96):
			var a := -PI*.5+PI*float(i)/95.0+(PI if side<0.0 else 0.0)
			contour.append(LAKE_CENTER+Vector2(side*straight_half+radius*cos(a),radius*sin(a)))
	for i in range(contour.size()):
		for p in [LAKE_CENTER,contour[i],contour[(i+1)%contour.size()]]:
			tool.set_normal(Vector3.UP);tool.set_uv(p*.1);tool.add_vertex(Vector3(p.x,WATER_Y,p.y))
	tool.generate_tangents();tool.index();_water_mesh=tool.commit();return _water_mesh
