class_name HavenlineCampBoundary
extends RefCounted

# T03 single source of truth for visible fence panels, collision gaps and the
# packed work-lane network. River geometry remains owned by T02.
const River = preload("res://scripts/river_geometry.gd")
const SIDE_X := 12.4
const NORTH_Z := 8.8
const SIDE_GATE_Z := 2.4
const NORTH_GATE_HALF := 1.8
const SIDE_GATE_HALF := 1.7
const RIVER_GATE_HALF := 1.7
const COLLISION_RADIUS := 0.32
const PANEL_TARGET := 2.72
const PANEL_SOURCE_LENGTH := 2.95
# T03 polish revision: the prior .92-unit leaves were physically present but
# too short to read unmistakably as opened gates from normal oblique views.
# Gate openings/collision widths remain unchanged; only the authored open-leaf
# presentation becomes more legible.
const GATE_LEAF_LENGTH := 1.35
const GATE_OPEN_ANGLE := 1.18
# River-facing entrances need stronger visual hierarchy because snow/river-bank
# colors reduce contrast. These are visual open leaves only; collision openings
# and future crossing reserves remain exactly unchanged.
const RIVER_GATE_LEAF_LENGTH := 1.85
# 1.53 rad keeps the long leaves visibly authored while swinging them far enough
# open to preserve a comfortable pixel-space threshold, not merely collision.
const RIVER_GATE_OPEN_ANGLE := 1.53
const RIVER_RESERVED_CORRIDOR := 3.0
const RIVER_VISUAL_CLEARANCE_MIN := 3.20
# River approaches need a broader worn threshold than ordinary camp lanes so
# the three future-crossing entrances read as intentional gates in snow.
const RIVER_LANE_HALF := 1.55
const RIVER_APRON_INSET := 0.55
const SOUTH_FENCE_MARGIN := River.WET_EDGE+River.BANK_RUN+River.SNOW_SHOULDER+River.BUILD_SETBACK
const LANE_HALF := 1.30
const BANK_LANE_MARGIN := River.DEFAULT_DRY_MARGIN+0.55
const CAMP_CENTER := Vector2(0.0,2.8)
const SHELTER_WEST := Vector2(-6.4,-0.4)
const SHELTER_EAST := Vector2(6.4,-0.4)
const RIVER_GATES := [-9.0,1.5,10.0]
const RIVER_EVIDENCE_KINDS := ["river-side-approach","threshold-three-quarter","camp-side-outward","gameplay-scale"]
const GATE_AUTHORITY_ID := "T03-gate-geometry-v3"

static func _cross(a: Vector2,b: Vector2)->float:
	return a.x*b.y-a.y*b.x

static func _closest(p:Vector2,a:Vector2,b:Vector2)->Vector2:
	var d:=b-a
	var den:=d.length_squared()
	if den<0.0000001:return a
	return a+d*clampf((p-a).dot(d)/den,0.0,1.0)

static func _distance_to_segment(p:Vector2,a:Vector2,b:Vector2)->float:
	return p.distance_to(_closest(p,a,b))

static func _segment_intersection(a:Vector2,b:Vector2,c:Vector2,d:Vector2)->Dictionary:
	var r:=b-a;var s:=d-c;var den:=_cross(r,s)
	if absf(den)<0.0000001:return {}
	var t:=_cross(c-a,s)/den;var u:=_cross(c-a,r)/den
	if t<-0.00001 or t>1.00001 or u<-0.00001 or u>1.00001:return {}
	return {"point":a+r*clampf(t,0.0,1.0),"t":t,"u":u}

static func south_point(x:float)->Vector2:
	# Solve the exact north-bank shore-distance at a fixed world X so the visual
	# perimeter never drifts inside T02's permanent-build setback.
	var clamped:=clampf(x,-SIDE_X,SIDE_X)
	var center:=River.center_at_x(clamped)
	var z:=center.y+River.width_at_x(clamped)*.5+SOUTH_FENCE_MARGIN
	for _i in range(8):
		var p:=Vector2(clamped,z);var q:=River.query(p)
		var error:=SOUTH_FENCE_MARGIN-float(q.shore_distance)
		if absf(error)<0.0001:break
		z+=error/maxf(absf(Vector2(q.north_normal).y),0.55)
	return Vector2(clamped,z)

static func bank_lane_point(x:float)->Vector2:
	var clamped:=clampf(x,-SIDE_X,SIDE_X);var center:=River.center_at_x(clamped)
	var z:=center.y+River.width_at_x(clamped)*.5+BANK_LANE_MARGIN
	for _i in range(8):
		var p:=Vector2(clamped,z);var q:=River.query(p)
		var error:=BANK_LANE_MARGIN-float(q.shore_distance)
		if absf(error)<0.0001:break
		z+=error/maxf(absf(Vector2(q.north_normal).y),0.55)
	return Vector2(clamped,z)

static func _sample_south(x0:float,x1:float)->Array[Vector2]:
	var points:Array[Vector2]=[]
	var count:=maxi(1,ceili(absf(x1-x0)/1.0))
	for i in range(count+1):points.append(south_point(lerpf(x0,x1,float(i)/float(count))))
	return points

static func _gate_intervals()->Array[Vector2]:
	var result:Array[Vector2]=[]
	for x in RIVER_GATES:result.append(Vector2(float(x)-RIVER_GATE_HALF,float(x)+RIVER_GATE_HALF))
	return result

static func boundary_polylines()->Array[Dictionary]:
	var south_left:=south_point(-SIDE_X);var south_right:=south_point(SIDE_X)
	var rows:Array[Dictionary]=[
		{"id":"north-west","points":[Vector2(-SIDE_X,NORTH_Z),Vector2(-NORTH_GATE_HALF,NORTH_Z)]},
		{"id":"north-east","points":[Vector2(NORTH_GATE_HALF,NORTH_Z),Vector2(SIDE_X,NORTH_Z)]},
		{"id":"west-south","points":[south_left,Vector2(-SIDE_X,SIDE_GATE_Z-SIDE_GATE_HALF)]},
		{"id":"west-north","points":[Vector2(-SIDE_X,SIDE_GATE_Z+SIDE_GATE_HALF),Vector2(-SIDE_X,NORTH_Z)]},
		{"id":"east-south","points":[south_right,Vector2(SIDE_X,SIDE_GATE_Z-SIDE_GATE_HALF)]},
		{"id":"east-north","points":[Vector2(SIDE_X,SIDE_GATE_Z+SIDE_GATE_HALF),Vector2(SIDE_X,NORTH_Z)]}
	]
	var cursor:float=-SIDE_X
	for interval in _gate_intervals():
		var start:=clampf(interval.x,-SIDE_X,SIDE_X);var finish:=clampf(interval.y,-SIDE_X,SIDE_X)
		if start>cursor+0.15:rows.append({"id":"south-%0.2f"%cursor,"points":_sample_south(cursor,start)})
		cursor=maxf(cursor,finish)
	if cursor<SIDE_X-0.15:rows.append({"id":"south-%0.2f"%cursor,"points":_sample_south(cursor,SIDE_X)})
	return rows

static func panel_specs()->Array[Dictionary]:
	# Collision and rendering both consume these exact subsegments.
	var result:Array[Dictionary]=[]
	for row in boundary_polylines():
		var points:Array=row.points
		for i in range(points.size()-1):
			var a:Vector2=points[i];var b:Vector2=points[i+1];var length:=a.distance_to(b)
			if length<0.15:continue
			var pieces:=maxi(1,ceili(length/PANEL_TARGET))
			for j in range(pieces):
				var p0:=a.lerp(b,float(j)/float(pieces));var p1:=a.lerp(b,float(j+1)/float(pieces))
				result.append({"boundary":row.id,"a":p0,"b":p1,"mid":(p0+p1)*.5,"length":p0.distance_to(p1),"tangent":(p1-p0).normalized()})
	return result

static func gate_specs()->Array[Dictionary]:
	var result:Array[Dictionary]=[]
	result.append({"id":"north-main","a":Vector2(-NORTH_GATE_HALF,NORTH_Z),"b":Vector2(NORTH_GATE_HALF,NORTH_Z),"kind":"main"})
	result.append({"id":"west-work","a":Vector2(-SIDE_X,SIDE_GATE_Z-SIDE_GATE_HALF),"b":Vector2(-SIDE_X,SIDE_GATE_Z+SIDE_GATE_HALF),"kind":"work"})
	result.append({"id":"east-work","a":Vector2(SIDE_X,SIDE_GATE_Z-SIDE_GATE_HALF),"b":Vector2(SIDE_X,SIDE_GATE_Z+SIDE_GATE_HALF),"kind":"work"})
	for x in RIVER_GATES:
		var a:=south_point(float(x)-RIVER_GATE_HALF);var b:=south_point(float(x)+RIVER_GATE_HALF)
		result.append({"id":"river-%s"%str(x),"a":a,"b":b,"kind":"river","reserve_x":float(x)})
	for gate in result:
		gate["center"]=(Vector2(gate.a)+Vector2(gate.b))*.5
		gate["width"]=Vector2(gate.a).distance_to(Vector2(gate.b))
		gate["tangent"]=(Vector2(gate.b)-Vector2(gate.a)).normalized()
		gate["authority_id"]=GATE_AUTHORITY_ID
	return result

static func gate_leaf_specs()->Array[Dictionary]:
	var result:Array[Dictionary]=[]
	for gate in gate_specs():
		var a:Vector2=gate.a;var b:Vector2=gate.b;var tangent:Vector2=gate.tangent;var mid:Vector2=gate.center
		var inward:=(CAMP_CENTER-mid).normalized()
		var leaf_length:=RIVER_GATE_LEAF_LENGTH if gate.kind=="river" else GATE_LEAF_LENGTH
		var open_angle:=RIVER_GATE_OPEN_ANGLE if gate.kind=="river" else GATE_OPEN_ANGLE
		var left_dir:=tangent.rotated(open_angle)
		if left_dir.dot(inward)<0:left_dir=tangent.rotated(-open_angle)
		var right_dir:=(-tangent).rotated(open_angle)
		if right_dir.dot(inward)<0:right_dir=(-tangent).rotated(-open_angle)
		result.append({"gate":gate.id,"hinge":a,"a":a,"b":a+left_dir*leaf_length,"length":leaf_length,"open_angle":open_angle,"authority_id":GATE_AUTHORITY_ID})
		result.append({"gate":gate.id,"hinge":b,"a":b,"b":b+right_dir*leaf_length,"length":leaf_length,"open_angle":open_angle,"authority_id":GATE_AUTHORITY_ID})
	return result

static func _river_apron(gate:Dictionary)->Array[Vector2]:
	# Cross the gate perpendicular to the fence, from the dry bank lane through
	# the threshold and visibly into camp. The old apron ran ALONG the opening,
	# which did not visually communicate an approach/entrance.
	var center:Vector2=gate.center
	var inward:=(CAMP_CENTER-center).normalized()
	var outside:=bank_lane_point(float(gate.reserve_x))
	return [outside,center,center+inward*2.20]

static func _river_slug(x:float)->String:
	if is_equal_approx(x,-9.0):return "west"
	if is_equal_approx(x,1.5):return "centre"
	if is_equal_approx(x,10.0):return "east"
	assert(false,"Unknown river gate reserve: "+str(x))
	return "unknown"

static func river_gate_contracts()->Array[Dictionary]:
	# One authoritative river-gate contract feeds route metadata, capture IDs and
	# visual-clearance assertions. Collision gaps and rendered leaves are already
	# derived from the same gate constants/specs above.
	var result:Array[Dictionary]=[]
	var leaf_intrusion:=maxf(0.0,RIVER_GATE_LEAF_LENGTH*cos(RIVER_GATE_OPEN_ANGLE))
	for gate in gate_specs():
		if gate.kind!="river":continue
		var route:=_river_apron(gate)
		var slug:=_river_slug(float(gate.reserve_x))
		var evidence_ids:Dictionary={}
		for kind in RIVER_EVIDENCE_KINDS:evidence_ids[kind]="river-gate/%s/%s"%[slug,kind]
		result.append({
			"id":gate.id,"slug":slug,"reserve_x":float(gate.reserve_x),"a":gate.a,"b":gate.b,
			"center":gate.center,"tangent":gate.tangent,"inward":(CAMP_CENTER-Vector2(gate.center)).normalized(),
			"outside":route[0],"inside":route[-1],"route_points":route,"width":float(gate.width),
			"collision_reserved_width":RIVER_RESERVED_CORRIDOR,
			"visual_leaf_intrusion_each":leaf_intrusion,
			"visual_clear_width":float(gate.width)-leaf_intrusion*2.0,
			"visual_clearance_min":RIVER_VISUAL_CLEARANCE_MIN,
			"evidence_ids":evidence_ids,"authority_id":GATE_AUTHORITY_ID
		})
	return result

static func lane_polylines()->Array[Dictionary]:
	var gates:=gate_specs();var by_id:Dictionary={}
	for gate in gates:by_id[gate.id]=gate
	var bank:Array[Vector2]=[]
	for x in [-10.5,-9.0,-5.0,0.0,1.5,5.0,10.0,10.5]:bank.append(bank_lane_point(float(x)))
	return [
		{"id":"central-spine","points":[bank_lane_point(1.5),Vector2(by_id["river-1.5"].center),Vector2(1.5,0.3),Vector2(0.0,2.25),Vector2(by_id["north-main"].center)]},
		{"id":"cross-camp","points":[Vector2(by_id["west-work"].center),Vector2(-2.8,2.25),Vector2(0.0,2.25),Vector2(by_id["east-work"].center)]},
		{"id":"west-shelter","points":[Vector2(-4.7,2.25),Vector2(-5.5,0.9),SHELTER_WEST]},
		{"id":"east-shelter","points":[Vector2(4.7,2.25),Vector2(5.5,0.9),SHELTER_EAST]},
		{"id":"north-bank","points":bank},
		{"id":"west-river-connector","points":[bank_lane_point(-9.0),Vector2(by_id["river--9.0"].center),Vector2(-8.3,0.9),Vector2(-6.8,2.25)]},
		{"id":"east-river-connector","points":[bank_lane_point(10.0),Vector2(by_id["river-10.0"].center),Vector2(8.7,0.9),Vector2(6.8,2.25)]},
		# Worn threshold aprons make each river opening legible as a used gate,
		# while staying entirely inside the already-open collision interval.
		{"id":"river-apron-west","points":_river_apron(by_id["river--9.0"]),"half_width":RIVER_LANE_HALF},
		{"id":"river-apron-centre","points":_river_apron(by_id["river-1.5"]),"half_width":RIVER_LANE_HALF},
		{"id":"river-apron-east","points":_river_apron(by_id["river-10.0"]),"half_width":RIVER_LANE_HALF}
	]

static func lane_signed_distance(p:Vector2)->float:
	var result:=999.0
	for lane in lane_polylines():
		var points:Array=lane.points
		var half_width:=float(lane.get("half_width",LANE_HALF))
		for i in range(points.size()-1):result=minf(result,_distance_to_segment(p,points[i],points[i+1])-half_width)
	return result

static func constrain_motion(previous:Vector2,candidate:Vector2,radius:=COLLISION_RADIUS)->Vector2:
	if not previous.is_finite() or not candidate.is_finite():return previous if previous.is_finite() else CAMP_CENTER
	var result:=candidate;var segments:=panel_specs()
	for _iteration in range(4):
		var changed:=false
		for panel in segments:
			var a:Vector2=panel.a;var b:Vector2=panel.b;var d:Vector2=(b-a).normalized();var n:=Vector2(-d.y,d.x)
			var side:=signf((previous-a).dot(n));if side==0.0:side=signf((CAMP_CENTER-a).dot(n));if side==0.0:side=1.0
			var hit:=_segment_intersection(previous,result,a,b)
			if not hit.is_empty():
				var point:Vector2=hit.point;var remaining:=result-point
				result=point+d*remaining.dot(d)+n*side*(radius+.002);changed=true
			var closest:=_closest(result,a,b);var delta:=result-closest;var distance:=delta.length()
			if distance<radius:
				var push_dir:=delta/distance if distance>0.00001 else n*side
				if push_dir.dot(n)*side<0:push_dir=n*side
				result=closest+push_dir*(radius+.002);changed=true
		if not changed:break
	return result

static func push_off_fence(p:Vector2,radius:=COLLISION_RADIUS)->Vector2:
	if not p.is_finite():return CAMP_CENTER
	var result:=p
	for _iteration in range(4):
		var changed:=false
		for panel in panel_specs():
			var a:Vector2=panel.a;var b:Vector2=panel.b;var closest:=_closest(result,a,b);var delta:=result-closest;var distance:=delta.length()
			if distance<radius:
				var d:Vector2=(b-a).normalized();var n:=Vector2(-d.y,d.x);var side:=signf(delta.dot(n))
				if side==0.0:side=signf((CAMP_CENTER-a).dot(n));if side==0.0:side=1.0
				result=closest+n*side*(radius+.002);changed=true
		if not changed:break
	return result

static func evidence()->Dictionary:
	var gates:=gate_specs();var minimum_gate:=999.0
	for gate in gates:minimum_gate=minf(minimum_gate,float(gate.width))
	var min_south_margin:=999.0
	for x in range(-124,125):min_south_margin=minf(min_south_margin,River.shore_distance(south_point(float(x)*.1)))
	var contract_evidence:Array=[]
	var evidence_ids:Array=[]
	var visual_clearance_pass:=true
	for contract in river_gate_contracts():
		var route:Array=[]
		for p in contract.route_points:route.append([Vector2(p).x,Vector2(p).y])
		var ids:Dictionary=contract.evidence_ids
		for kind in RIVER_EVIDENCE_KINDS:evidence_ids.append(String(ids[kind]))
		visual_clearance_pass=visual_clearance_pass and float(contract.visual_clear_width)>=RIVER_VISUAL_CLEARANCE_MIN
		contract_evidence.append({
			"id":contract.id,"slug":contract.slug,"reserve_x":contract.reserve_x,
			"center":[Vector2(contract.center).x,Vector2(contract.center).y],"width":contract.width,
			"collision_reserved_width":contract.collision_reserved_width,
			"visual_leaf_intrusion_each":contract.visual_leaf_intrusion_each,
			"visual_clear_width":contract.visual_clear_width,"visual_clearance_min":contract.visual_clearance_min,
			"route_points":route,"evidence_ids":ids,"authority_id":GATE_AUTHORITY_ID
		})
	return {"task":"T03","side_x":SIDE_X,"north_z":NORTH_Z,"panel_count":panel_specs().size(),"gate_count":gates.size(),
		"minimum_gate_width":minimum_gate,"south_fence_minimum_shore_distance":min_south_margin,
		"south_fence_required_margin":SOUTH_FENCE_MARGIN,"collision_radius":COLLISION_RADIUS,"lane_half_width":LANE_HALF,
		"gate_leaf_length":GATE_LEAF_LENGTH,"gate_open_angle":GATE_OPEN_ANGLE,
		"river_gate_leaf_length":RIVER_GATE_LEAF_LENGTH,"river_gate_open_angle":RIVER_GATE_OPEN_ANGLE,
		"river_lane_half_width":RIVER_LANE_HALF,"river_apron_inset":RIVER_APRON_INSET,
		"river_visual_clearance_min":RIVER_VISUAL_CLEARANCE_MIN,"all_river_visual_clearance_pass":visual_clearance_pass,
		"river_gate_contracts":contract_evidence,"required_river_gate_evidence_ids":evidence_ids,
		"gate_authority_id":GATE_AUTHORITY_ID,"lane_ids":lane_polylines().map(func(row):return row.id),
		"river_gate_reserves":RIVER_GATES,"task_approved":false}
