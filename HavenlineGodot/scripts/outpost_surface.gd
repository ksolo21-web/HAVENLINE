extends RefCounted
# T02 river revision remains authoritative for terrain/water. T03 adds only an
# encoded packed-lane mask to this same continuous terrain surface.
const River = preload("res://scripts/river_geometry.gd")
const Boundary = preload("res://scripts/camp_boundary.gd")
const HALF := 31.0
const STEP := 0.25
const WATER_Y := River.WATER_Y
const LAND_MARGIN := River.DEFAULT_DRY_MARGIN
const WORK_CENTER := Vector2(0.0, 2.8)
const WORK_HALF := Vector2(9.75, 4.3)
const T03_LANE_COMPRESSION_DEPTH := 0.075
const T03_LANE_RUT_DEPTH := 0.055
const T03_LANE_SHOULDER_HEIGHT := 0.075
static var _mesh: ArrayMesh
static var _water_mesh: ArrayMesh
static var _heights := PackedFloat32Array()
static var _lane_distances := PackedFloat32Array()

static func rounded_rect(p: Vector2, center: Vector2, half_size: Vector2, radius: float) -> float:
	var q := (p-center).abs()-half_size+Vector2.ONE*radius
	return q.max(Vector2.ZERO).length()+minf(maxf(q.x,q.y),0.0)-radius

static func work_distance(p: Vector2) -> float:
	return rounded_rect(p,WORK_CENTER,WORK_HALF,0.78)

static func river_distance(p: Vector2) -> float:
	return River.shore_distance(p)

# Compatibility for older diagnostic scripts only. Runtime code uses river_*.
static func lake_distance(p: Vector2) -> float:
	return river_distance(p)

static func land_position(p: Vector2, margin := LAND_MARGIN) -> Vector2:
	return River.dry_position(p,margin)

static func protected_build_position(p: Vector2) -> Vector2:
	return River.protected_build_position(p)

static func _shape_height(p: Vector2,lane_distance:=INF) -> float:
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
	var shore := river_distance(p)
	var bank_height := lerpf(WATER_Y-.82,.15,smoothstep(-.42,River.WET_EDGE+River.BANK_RUN,shore))
	bank_height += .18*exp(-pow((shore-(River.WET_EDGE+River.BANK_RUN+.14))/.34,2.0))
	result=lerpf(bank_height,result,smoothstep(River.WET_EDGE+River.BANK_RUN,River.WET_EDGE+River.BANK_RUN+River.SNOW_SHOULDER,shore))
	# T03 routes are physically compressed into this same terrain mesh. The
	# previous shader-only tint could read as a flat overlay at grouped evidence
	# scale. A shallow continuous bed plus paired traffic ruts now creates real
	# height/contact cues without adding a path plane or touching T02 water.
	var lane:=Boundary.lane_signed_distance(p) if is_inf(lane_distance) else lane_distance
	var lane_bed:=1.0-smoothstep(-.08,.22,lane)
	var centre_distance:=maxf(0.0,lane+Boundary.LANE_HALF)
	var paired_ruts:=exp(-pow((centre_distance-.62)/.17,2.0))
	var compression_variation:=.82+.18*pow(sin(p.x*.91+p.y*.57),2.0)
	result-=lane_bed*(T03_LANE_COMPRESSION_DEPTH*compression_variation+T03_LANE_RUT_DEPTH*paired_ruts)
	var swept_snow_shoulder:=exp(-pow((lane-.13)/.17,2.0))
	result+=T03_LANE_SHOULDER_HEIGHT*swept_snow_shoulder*(.82+.18*pow(sin(p.x*.47-p.y*.81),2.0))
	return result

static func _ensure_heights():
	if not _heights.is_empty(): return
	var n := int(HALF*2.0/STEP);var side := n+1
	_heights.resize(side*side)
	_lane_distances.resize(side*side)
	for z in range(side):
		for x in range(side):
			var i:=z*side+x;var p:=Vector2(-HALF+x*STEP,-HALF+z*STEP)
			_lane_distances[i]=Boundary.lane_signed_distance(p)
			_heights[i]=_shape_height(p,_lane_distances[i])

static func height_at(p: Vector2) -> float:
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
	var n := int(HALF*2.0/STEP);var side := n+1
	var vertices := PackedVector3Array();vertices.resize(side*side)
	var normals := PackedVector3Array();normals.resize(side*side)
	var uv := PackedVector2Array();uv.resize(side*side)
	var colors := PackedColorArray();colors.resize(side*side)
	var indices := PackedInt32Array();indices.resize(n*n*6)
	for z in range(side):
		for x in range(side):
			var p := Vector2(-HALF+x*STEP,-HALF+z*STEP);var i := z*side+x
			vertices[i]=Vector3(p.x,_heights[i],p.y);uv[i]=p*.08
			var shore:=clampf((river_distance(p)+4.0)/8.0,0.0,1.0)
			var work:=clampf((work_distance(p)+4.0)/8.0,0.0,1.0)
			var lane:=clampf((_lane_distances[i]+4.0)/8.0,0.0,1.0)
			colors[i]=Color(shore,work,lane,1.0)
	for z in range(side):
		for x in range(side):
			var l := maxi(0,x-1);var r := mini(n,x+1);var b := maxi(0,z-1);var t := mini(n,z+1)
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
	arrays[Mesh.ARRAY_TEX_UV]=uv;arrays[Mesh.ARRAY_COLOR]=colors;arrays[Mesh.ARRAY_INDEX]=indices
	var result := ArrayMesh.new();result.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,arrays)
	return result

static func mesh() -> ArrayMesh:
	if _mesh==null: _mesh=_indexed_grid()
	return _mesh

static func water_mesh() -> ArrayMesh:
	if _water_mesh!=null: return _water_mesh
	var rows:=13;var samples:=River.plan_samples(.25)
	var vertices:=PackedVector3Array();var normals:=PackedVector3Array()
	var uv:=PackedVector2Array();var tangents:=PackedFloat32Array();var indices:=PackedInt32Array()
	var along:=0.0;var previous:=Vector2.ZERO
	for i in range(samples.size()):
		var sample:Dictionary=samples[i];var center:Vector2=sample.center
		if i>0: along+=center.distance_to(previous)
		previous=center
		var north:Vector2=sample.north_normal;var half:=float(sample.width)*.5
		for j in range(rows):
			var lateral:=lerpf(-half,half,float(j)/float(rows-1))
			var p:=center+north*lateral
			vertices.append(Vector3(p.x,WATER_Y,p.y));normals.append(Vector3.UP)
			uv.append(Vector2(along*.12,float(j)/float(rows-1)))
			tangents.append_array(PackedFloat32Array([float(sample.tangent.x),0.,float(sample.tangent.y),1.]))
	for i in range(samples.size()-1):
		for j in range(rows-1):
			var a:=i*rows+j;var b:=(i+1)*rows+j
			for triangle in [[a,b,a+1],[b,b+1,a+1]]:
				var area:Vector3=(vertices[triangle[1]]-vertices[triangle[0]]).cross(vertices[triangle[2]]-vertices[triangle[0]])
				if area.length_squared()>.0000000001:
					for index in triangle:indices.append(index)
	var arrays:Array=[];arrays.resize(Mesh.ARRAY_MAX)
	arrays[Mesh.ARRAY_VERTEX]=vertices;arrays[Mesh.ARRAY_NORMAL]=normals
	arrays[Mesh.ARRAY_TEX_UV]=uv;arrays[Mesh.ARRAY_TANGENT]=tangents;arrays[Mesh.ARRAY_INDEX]=indices
	_water_mesh=ArrayMesh.new();_water_mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,arrays)
	return _water_mesh

static func river_evidence() -> Dictionary:
	var evidence:=River.evidence()
	evidence["water_triangles"]=water_mesh().get_faces().size()/3
	evidence["terrain_triangles"]=mesh().get_faces().size()/3
	evidence["work_center"]=[WORK_CENTER.x,WORK_CENTER.y]
	evidence["work_half"]=[WORK_HALF.x,WORK_HALF.y]
	evidence["task03_lane_network"]=Boundary.evidence()
	return evidence
