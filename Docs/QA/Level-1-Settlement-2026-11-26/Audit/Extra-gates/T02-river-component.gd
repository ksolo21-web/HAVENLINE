extends SceneTree
const River=preload("res://assets/lakeshore/river_geometry.gd")
var checks:Array=[]
var failures:Array=[]
func check(name:String,passed:bool):
	checks.append({"name":name,"passed":passed})
	if not passed:failures.append(name)
func _initialize():call_deferred("run")
func run():
	var expected:Array=[Vector2(-31,-8.6),Vector2(-24,-7.2),Vector2(-17,-9),Vector2(-10,-6.8),Vector2(-3,-8.7),Vector2(4,-6.9),Vector2(11,-8.5),Vector2(19,-6.7),Vector2(25,-8.1),Vector2(31,-7.3)]
	check("Locked ten river anchors retained exactly",River.ANCHORS==expected)
	check("River version is persistent map-span v1",River.LAYOUT_VERSION=="river_v1_mapspan")
	var anchor_exact:=true;var c1:=true
	for i in range(expected.size()):
		var anchor:Vector2=expected[i];anchor_exact=anchor_exact and River.center_at_x(anchor.x).distance_to(anchor)<.00001
		if i>0 and i<expected.size()-1:c1=c1 and River.tangent_at_x(anchor.x-.001).dot(River.tangent_at_x(anchor.x+.001))>.9999
	check("Spline passes through every locked anchor",anchor_exact);check("Spline is C1-continuous through interior anchors",c1)
	var min_width:=999.0;var max_width:=0.0;var finite:=true;var current_crosses:=true
	for i in range(1241):
		var x:float=-31.0+float(i)*.05;var c:Vector2=River.center_at_x(x);var w:float=River.width_at_x(x)
		min_width=minf(min_width,w);max_width=maxf(max_width,w);finite=finite and c.is_finite() and is_finite(w)
	check("Full terrain river samples are finite",finite);check("Open-water width remains inside locked 3.2 to 4.6 range",min_width>=3.2 and max_width<=4.6)
	for side_value in [-14.2,14.2]:
		var side:float=float(side_value);var c:Vector2=River.center_at_x(side);var q:Dictionary=River.query(c);current_crosses=current_crosses and float(q.shore_distance)<-1.5
	check("Water continuously crosses both current east-west movement edges",current_crosses)
	var south_min:=999.0;var north_min:=999.0;var lane_dry:=true
	for i in range(285):
		var x:float=-14.2+float(i)*.1;var q:Dictionary=River.query(River.center_at_x(x));var center:Vector2=q.center;var n:Vector2=q.north_normal;var half_width:float=float(q.half_width)
		var south_crest:Vector2=center-n*(half_width+River.WET_EDGE+River.BANK_RUN);var north_build:Vector2=center+n*(half_width+River.WET_EDGE+River.BANK_RUN+River.SNOW_SHOULDER+River.BUILD_SETBACK)
		south_min=minf(south_min,south_crest.y-(-16.2));north_min=minf(north_min,16.2-north_build.y)
		var north_lane:Vector2=center+n*(half_width+River.WET_EDGE+River.BANK_RUN+River.SNOW_SHOULDER+.7);var south_lane:Vector2=center-n*(half_width+River.WET_EDGE+River.BANK_RUN+River.SNOW_SHOULDER+.7)
		lane_dry=lane_dry and River.shore_distance(north_lane)>1.4 and River.shore_distance(south_lane)>1.4
	check("Current south-bank traversable depth never below 4.5",south_min>=4.5);check("Current north unrestricted gross span never below 16.5",north_min>=16.5);check("Both bank route centerlines remain continuously dry",lane_dry)
	print(JSON.stringify({"checks":checks,"failures":failures,"passed":failures.is_empty(),"min_width":min_width,"max_width":max_width,"south_min":south_min,"north_min":north_min}))
	quit(0 if failures.is_empty() else 1)
