extends "res://tests/qa_snow_truck.gd"

var traces: Array = []
var test_base := OS.get_environment("T07_VEHICLE_REVIEW")

func _initialize() -> void:
	run.call_deferred()

func local_point(x: float,z: float) -> Vector3:
	return truck.garage.to_global(Vector3(x,0.,z))

func characterize(label: String, x: float, z: float, yaw: float, pause_at_door: bool) -> void:
	# Stage the same body and yard at a known approach. The steering fixture
	# then uses ordinary touch only, with no animation or collision overrides.
	truck.body.global_position = local_point(x,z)
	truck.body.rotation.y = yaw
	truck.drive_speed = 0.
	if "bay_approach" in truck: truck.bay_approach = ""
	if "bay_reverse" in truck: truck.bay_reverse = false
	field.actor.global_position = truck.body.global_position
	steer(Vector2.ZERO)
	for i in 20: await physics_frame
	var start: Vector3 = truck.garage.to_local(truck.body.global_position)
	var touched := false
	var closest := INF
	var stalled := 0
	var max_stalled := 0
	var went_inside := false
	var events := []
	var ticks := 0
	for n in 245:
		ticks=n
		var at: Vector3 = truck.garage.to_local(truck.body.global_position)
		closest = minf(closest,at.distance_to(Vector3(0.,0.,2.72)))
		if at.z>2.60 and absf(at.x)<.30:
			went_inside=true
			break
		if pause_at_door and not touched and at.z>-.94:
			touched=true
			steer(Vector2.ZERO)
			for i in 23:await physics_frame
		var previous: Vector3 = truck.body.global_position
		steer(_heading(local_point(0.,2.72)-previous)*.85)
		await physics_frame
		var shift: float = truck.body.global_position.distance_to(previous)
		stalled = stalled + 1 if shift<.004 else 0
		max_stalled=maxi(max_stalled,stalled)
		if n%5==0 or stalled==1:
			var colliders: Array[String] = []
			for j in truck.body.get_slide_collision_count():
				var object = truck.body.get_slide_collision(j).get_collider()
				if object:colliders.append(object.name)
			events.append({"n":n,"x":at.x,"z":at.z,"yaw":truck.body.rotation.y,"door":truck.opening,"shift":shift,"contacts":colliders})
	steer(Vector2.ZERO)
	for n in 45:await physics_frame
	var result: Dictionary = {"label":label,"start":str(start),"initial_yaw":yaw,"parked":truck.parked(),"reached":went_inside,
		"entered_then_paused":touched,"end":str(truck.garage.to_local(truck.body.global_position)),"max_stall_ticks":max_stalled,"distance":closest,"ticks":ticks,"events":events,"end_yaw":truck.body.rotation.y,"end_door":truck.opening}
	traces.append(result)
	var summary := result.duplicate()
	summary.erase("events")
	print("OBLIQUE_ROUTE ",JSON.stringify(summary))

func run() -> void:
	field=load("res://field_opening.tscn").instantiate()
	root.add_child(field)
	camera=field.camera
	truck=field.snow_truck
	origin=root.get_visible_rect().size*Vector2(.28,.70)
	for n in 7:await physics_frame
	for id in ["center_hearth","expansion_1","storage_wood","storage_stone","storage_meat","expansion_2","snow_garage","snow_truck"]:
		if not _fund(id):
			printerr("Fixture failed at ",id)
			quit(1)
			return
		if id=="center_hearth":
			for count in 14:await physics_frame
	for wolf in field.enemies.duplicate():field.encounters._remove(wolf)
	field.encounters.remaining=999.
	field.actor.global_position = truck.body.position + Vector3(0,0,-1.9)
	await physics_frame
	await _key()
	if not truck.mounted:
		printerr("Could not mount")
		quit(1)
		return
	for options in [
		["straight nose-in",0.,-5.,0.,false],
		["straight reverse",0.,-5.,PI,false],
		["outside left pointed in",-2.0,-4.4,.38,true],
		["outside right pointed in",2.0,-4.4,-.38,true],
		["left lip sharp heading",-1.58,-2.90,.55,false],
		["right lip sharp heading",1.58,-2.90,-.55,false],
		["left lip reverse",-1.58,-2.90,PI+.55,true],
		["right lip reverse",1.58,-2.90,PI-.55,true],
	]:
		await characterize(options[0],options[1],options[2],options[3],options[4])
	var file := FileAccess.open(test_base.path_join("Approach.json"),FileAccess.WRITE)
	file.store_string(JSON.stringify({"source":FileAccess.get_sha256("res://field_snow_truck.gd"),"routes":traces}, "  "))
	file.close()
	await _close_field()
	quit()
