extends RefCounted
# Task 2 authoritative river definition. Terrain carving, water mesh, collision,
# save recovery and expansion masks must sample this same source.
const TERRAIN_HALF := 31.0
const WATER_Y := -0.34
const WET_EDGE := 0.30
const BANK_RUN := 0.70
const SNOW_SHOULDER := 0.45
const BUILD_SETBACK := 1.60
const DEFAULT_DRY_MARGIN := 0.32
const LAYOUT_VERSION := "river_v1_mapspan"
const ANCHORS := [
	Vector2(-31.0,-8.6), Vector2(-24.0,-7.2), Vector2(-17.0,-9.0),
	Vector2(-10.0,-6.8), Vector2(-3.0,-8.7), Vector2(4.0,-6.9),
	Vector2(11.0,-8.5), Vector2(19.0,-6.7), Vector2(25.0,-8.1),
	Vector2(31.0,-7.3)
]
# Bend apices widen, straight inlet/outlet reaches narrow. Changes are smooth
# over each 6-8 unit anchor interval, satisfying the >=4 unit transition rule.
const WIDTHS := [3.6,4.05,4.20,4.25,4.00,4.25,4.00,4.25,3.80,3.60]
const CROSSING_X := [-9.0,1.5,10.0]
const CROSSING_HALF_WIDTH := 1.5

static func _segment_index(x: float) -> int:
	if x<=ANCHORS[0].x: return 0
	for i in range(ANCHORS.size()-1):
		if x<=ANCHORS[i+1].x: return i
	return ANCHORS.size()-2

static func _slope(index: int) -> float:
	if index<=0:
		return (ANCHORS[1].y-ANCHORS[0].y)/(ANCHORS[1].x-ANCHORS[0].x)
	if index>=ANCHORS.size()-1:
		var n:=ANCHORS.size()-1
		return (ANCHORS[n].y-ANCHORS[n-1].y)/(ANCHORS[n].x-ANCHORS[n-1].x)
	return (ANCHORS[index+1].y-ANCHORS[index-1].y)/(ANCHORS[index+1].x-ANCHORS[index-1].x)

static func _hermite_value(y0: float,y1: float,m0: float,m1: float,h: float,t: float) -> float:
	var t2:=t*t;var t3:=t2*t
	return (2.0*t3-3.0*t2+1.0)*y0+(t3-2.0*t2+t)*h*m0+(-2.0*t3+3.0*t2)*y1+(t3-t2)*h*m1

static func _hermite_derivative(y0: float,y1: float,m0: float,m1: float,h: float,t: float) -> float:
	var t2:=t*t
	return ((6.0*t2-6.0*t)*y0+(3.0*t2-4.0*t+1.0)*h*m0+(-6.0*t2+6.0*t)*y1+(3.0*t2-2.0*t)*h*m1)/h

static func center_at_x(x: float) -> Vector2:
	var clamped:=clampf(x,-TERRAIN_HALF,TERRAIN_HALF)
	var i:=_segment_index(clamped)
	var a:Vector2=ANCHORS[i];var b:Vector2=ANCHORS[i+1]
	var h:=b.x-a.x;var t:=clampf((clamped-a.x)/h,0.0,1.0)
	return Vector2(clamped,_hermite_value(a.y,b.y,_slope(i),_slope(i+1),h,t))

static func tangent_at_x(x: float) -> Vector2:
	var clamped:=clampf(x,-TERRAIN_HALF,TERRAIN_HALF)
	var i:=_segment_index(clamped)
	var a:Vector2=ANCHORS[i];var b:Vector2=ANCHORS[i+1]
	var h:=b.x-a.x;var t:=clampf((clamped-a.x)/h,0.0,1.0)
	var dzdx:=_hermite_derivative(a.y,b.y,_slope(i),_slope(i+1),h,t)
	return Vector2(1.0,dzdx).normalized()

static func width_at_x(x: float) -> float:
	var clamped:=clampf(x,-TERRAIN_HALF,TERRAIN_HALF)
	var i:=_segment_index(clamped)
	var a:Vector2=ANCHORS[i];var b:Vector2=ANCHORS[i+1]
	var t:=clampf((clamped-a.x)/(b.x-a.x),0.0,1.0)
	var smooth:=t*t*(3.0-2.0*t)
	return lerpf(float(WIDTHS[i]),float(WIDTHS[i+1]),smooth)

static func query(p: Vector2) -> Dictionary:
	# Project against the C1 curve. Because x is strictly monotonic, a few
	# tangent-projection iterations find the nearest cross-section cheaply.
	var x:=clampf(p.x,-TERRAIN_HALF,TERRAIN_HALF)
	for _iteration in range(4):
		var center:=center_at_x(x)
		var tangent:=tangent_at_x(x)
		var delta:=p-center
		x=clampf(x+delta.dot(tangent)*tangent.x,-TERRAIN_HALF,TERRAIN_HALF)
	var center:=center_at_x(x)
	var tangent:=tangent_at_x(x)
	# Tangent always points west->east, so this left normal points north.
	var north_normal:=Vector2(-tangent.y,tangent.x).normalized()
	var lateral:=(p-center).dot(north_normal)
	var width:=width_at_x(x)
	return {"x":x,"center":center,"tangent":tangent,"north_normal":north_normal,
		"lateral":lateral,"side":1.0 if lateral>=0.0 else -1.0,
		"width":width,"half_width":width*0.5,"shore_distance":absf(lateral)-width*0.5}

static func shore_distance(p: Vector2) -> float:
	return float(query(p).shore_distance)

static func is_water(p: Vector2, extra_margin:=0.0) -> bool:
	return shore_distance(p)<extra_margin

static func dry_position(p: Vector2, margin:=DEFAULT_DRY_MARGIN) -> Vector2:
	if not p.is_finite(): return Vector2.ZERO
	var q:=query(p);var target:=float(q.half_width)+maxf(margin,0.0)
	if absf(float(q.lateral))>=target: return p
	var side:=float(q.side)
	return Vector2(q.center)+Vector2(q.north_normal)*target*side

static func protected_build_position(p: Vector2) -> Vector2:
	return dry_position(p,WET_EDGE+BANK_RUN+SNOW_SHOULDER+BUILD_SETBACK)

static func bank_crest_distance(p: Vector2) -> float:
	# Positive means beyond the sloped bank crest and therefore traversable dry
	# bank. The soft shoulder/build setback remain dry and may form travel lanes.
	return shore_distance(p)-(WET_EDGE+BANK_RUN)

static func unrestricted_build_distance(p: Vector2) -> float:
	return shore_distance(p)-(WET_EDGE+BANK_RUN+SNOW_SHOULDER+BUILD_SETBACK)

static func crossing_reserved(p: Vector2) -> bool:
	for x in CROSSING_X:
		if absf(p.x-float(x))<=CROSSING_HALF_WIDTH:
			var q:=query(p)
			if absf(float(q.lateral))<=float(q.half_width)+WET_EDGE+BANK_RUN+SNOW_SHOULDER+BUILD_SETBACK:
				return true
	return false

static func plan_samples(step:=0.25) -> Array[Dictionary]:
	var rows:Array[Dictionary]=[]
	var x:=-TERRAIN_HALF
	while x<TERRAIN_HALF-0.0001:
		var c:=center_at_x(x);var t:=tangent_at_x(x);var n:=Vector2(-t.y,t.x).normalized()
		rows.append({"x":x,"center":c,"tangent":t,"north_normal":n,"width":width_at_x(x)})
		x+=step
	var c:=center_at_x(TERRAIN_HALF);var t:=tangent_at_x(TERRAIN_HALF);var n:=Vector2(-t.y,t.x).normalized()
	rows.append({"x":TERRAIN_HALF,"center":c,"tangent":t,"north_normal":n,"width":width_at_x(TERRAIN_HALF)})
	return rows

static func evidence() -> Dictionary:
	var min_width:=999.0;var max_width:=0.0
	for row in plan_samples(.10):
		min_width=minf(min_width,float(row.width));max_width=maxf(max_width,float(row.width))
	return {"layout_version":LAYOUT_VERSION,"terrain_extent_x":[-TERRAIN_HALF,TERRAIN_HALF],
		"anchors":ANCHORS,"anchor_widths":WIDTHS,"crossing_reserves_x":CROSSING_X,
		"minimum_width":min_width,"maximum_width":max_width,"water_y":WATER_Y}
