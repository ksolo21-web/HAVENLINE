extends SceneTree

class LogBody extends RigidBody3D:
	var deck_contact_ticks := 0
	var cross_contact_ticks := 0
	var last_summary := {}
	var ticks := 0
	func _integrate_forces(state: PhysicsDirectBodyState3D) -> void:
		ticks += 1
		var got_deck := false
		var got_cross := false
		for i in range(state.get_contact_count()):
			if state.get_contact_collider_object(i) is StaticBody3D:
				got_deck = true
			elif state.get_contact_collider_object(i) is RigidBody3D:
				got_cross = true
		if got_deck:
			deck_contact_ticks += 1
		if got_cross:
			cross_contact_ticks += 1
		last_summary={"deck":got_deck,"cross":got_cross,"speed":state.linear_velocity.length(),"angular_speed":state.angular_velocity.length()}

var shape_points: Array[Vector3] = []
var deck_footprint: Array[Vector3] = []
var state: Dictionary
var failures := 0
var checks := 0
var rows := []

func v(a: Array) -> Vector3:
	return Vector3(float(a[0]),float(a[1]),float(a[2]))
func xyz(p: Vector3) -> Array:
	return [p.x,p.y,p.z]
func _initialize() -> void:
	call_deferred("run")
func attach(body: CollisionObject3D, points: Array[Vector3]) -> void:
	var c := CollisionShape3D.new()
	var cv := ConvexPolygonShape3D.new()
	cv.points=PackedVector3Array(points)
	c.shape=cv
	body.add_child(c)
func expect(b: bool, label: String) -> void:
	checks += 1
	if not b:
		failures += 1
	print("CHECK ", b, " ", label)
func body_for(location: Transform3D, mode: String) -> LogBody:
	var body := LogBody.new()
	body.mass=1.0
	body.center_of_mass_mode=RigidBody3D.CENTER_OF_MASS_MODE_CUSTOM
	body.center_of_mass=v(state.source_com)
	body.can_sleep=false
	body.max_contacts_reported=16
	body.contact_monitor=true
	body.linear_damp_mode=RigidBody3D.DAMP_MODE_REPLACE
	body.angular_damp_mode=RigidBody3D.DAMP_MODE_REPLACE
	body.linear_damp=.1
	body.angular_damp=.3
	body.continuous_cd=true
	body.physics_material_override=PhysicsMaterial.new()
	body.physics_material_override.friction=.75
	body.physics_material_override.bounce=0.
	body.transform=location
	attach(body,shape_points)
	root.add_child(body)
	return body
func inner_edge_margin(p: Vector3) -> float:
	var ans := INF
	for i in range(deck_footprint.size()):
		var a := deck_footprint[i]
		var b := deck_footprint[(i+1)%deck_footprint.size()]
		var u := Vector2(b.x-a.x,b.z-a.z)
		var q := Vector2(p.x-a.x,p.z-a.z)
		ans=minf(ans,u.cross(q)/u.length())
	return ans
func report_pose(b: LogBody, initial_basis: Basis) -> Dictionary:
	var low := Vector3(INF,INF,INF)
	var high := Vector3(-INF,-INF,-INF)
	var reserve := INF
	for p in shape_points:
		var q:=b.transform*p
		low=low.min(q); high=high.max(q)
		reserve=minf(reserve,inner_edge_margin(q))
	var diff := initial_basis.get_rotation_quaternion().angle_to(b.transform.basis.orthonormalized().get_rotation_quaternion())
	return {"lo":xyz(low),"hi":xyz(high),"inset":reserve,"deviation_deg":rad_to_deg(diff),"origin":xyz(b.position),"state":b.last_summary}
func run() -> void:
	state=JSON.parse_string(FileAccess.get_file_as_string("res://fixture_data.json"))
	var deck_points: Array[Vector3]=[]
	for p in state.plate_hull_points:
		deck_points.append(v(p))
	for p in state.ordered_top_xz:
		deck_footprint.append(Vector3(float(p[0]),0,float(p[1])))
	for p in state.hull_points:
		shape_points.append(v(p))
	var deck:=StaticBody3D.new()
	deck.name="ExactPlateSupportHull"
	deck.physics_material_override=PhysicsMaterial.new()
	deck.physics_material_override.friction=.75
	deck.physics_material_override.bounce=0
	attach(deck,deck_points)
	root.add_child(deck)
	var baseline:=OS.get_environment("HVN_MODE")=="baseline"
	var cols:Array=state.basis_columns
	var axes:=Basis(v(cols[0]),v(cols[1]),v(cols[2])) if not baseline else Basis.IDENTITY
	var bodies:Array[LogBody]=[]
	if baseline:
		bodies.append(body_for(Transform3D(axes,v(state.source_center_lift)+Vector3.UP*.002),"negative"))
	else:
		for p in state.source_to_rest_t:
			bodies.append(body_for(Transform3D(axes,v(p)+Vector3.UP*.002),"trial"))
	var tail_min_gap:=INF
	var start: Array=[]
	var endpoint: Array=[]
	var tail_linear:=0.
	var tail_angular:=0.
	var tail_penetration:=INF
	var tail_plate_margin:=INF
	var tail_contact_ticks:=0
	for tick in range(300):
		await physics_frame
		if tick not in [0,29,59,119,179,239,299] and tick<240:
			continue
		var now:Array=[]
		for b in bodies:
			now.append(report_pose(b,axes))
		if tick in [0,29,59,119,179,239,299]:
			rows.append({"tick":tick,"bodies":now})
		if tick>=240:
			var all_contact := true
			for b in now:
				tail_linear=maxf(tail_linear,float(b.state.get("speed",INF)))
				tail_angular=maxf(tail_angular,float(b.state.get("angular_speed",INF)))
				tail_penetration=minf(tail_penetration,float(b.lo[1]))
				tail_plate_margin=minf(tail_plate_margin,float(b.inset))
				all_contact=all_contact and bool(b.state.get("deck",false))
			if all_contact:
				tail_contact_ticks+=1
			if not baseline:
				tail_min_gap=minf(tail_min_gap,float(now[1].lo[2])-float(now[0].hi[2]))
			if tick==240:
				start=now
			endpoint=now
	var max_drift:=0.
	for i in range(bodies.size()):
		max_drift=maxf(max_drift,v(start[i].origin).distance_to(v(endpoint[i].origin)))
		expect(bodies[i].deck_contact_ticks>80,"native deck contacts reported")
		expect(bodies[i].cross_contact_ticks==0,"no log-to-log contact reported")
	expect(tail_penetration > -.001,"last-second exact geometry plane penetration below 1mm")
	expect(tail_plate_margin>.10,"whole exact hull remains inside finite top")
	if not baseline:
		expect(tail_min_gap>0,"positive exact pair separation throughout final second")
		expect(tail_linear<.012 and tail_angular<.20 and max_drift<.003,"last-second velocities and pose drift bounded")
		expect(endpoint.all(func(b):return b.deviation_deg<3.0),"settles within 3deg of certified three-point pose")
		expect(tail_contact_ticks>=45,"both report deck contact in at least 45 of final 60 ticks")
	print("NATIVE ",JSON.stringify({"mode":"baseline" if baseline else "trial","backend":ProjectSettings.get_setting("physics/3d/physics_engine"),"contact_counts":bodies.map(func(b):return [b.deck_contact_ticks,b.cross_contact_ticks]),"checks":checks,"failures":failures,"tail_max_drift":max_drift,"tail_max_linear":tail_linear,"tail_max_angular":tail_angular,"tail_min_geom_y":tail_penetration,"tail_min_plate_margin":tail_plate_margin,"tail_min_gap":null if baseline else tail_min_gap,"tail_contact_ticks":tail_contact_ticks,"frames":rows}))
	quit(1 if failures else 0)
