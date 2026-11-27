extends SceneTree

const Artist = preload("res://field_snow_truck_art.gd")

func _initialize() -> void:
	call_deferred(&"run")

func _bounds(node: Node3D) -> AABB:
	var found := false
	var box := AABB()
	for m in node.find_children("*","MeshInstance3D", true, false):
		var mesh_node := m as MeshInstance3D
		var extent := mesh_node.global_transform * mesh_node.get_aabb()
		box = box.merge(extent) if found else extent
		found = true
	return box

func _stage() -> Node3D:
	var env := WorldEnvironment.new()
	var setting := Environment.new()
	setting.background_mode = Environment.BG_COLOR
	setting.background_color = Color("#243758")
	setting.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	setting.ambient_light_color = Color("#e5efff")
	setting.ambient_light_energy = 0.60
	env.environment = setting
	root.add_child(env)
	var sun := DirectionalLight3D.new()
	sun.light_color = Color("#fff6e7")
	sun.light_energy = 1.23
	sun.rotation_degrees = Vector3(-53,-30,0)
	sun.shadow_enabled = true
	root.add_child(sun)
	var fill := DirectionalLight3D.new()
	fill.light_color = Color("#dbedff")
	fill.light_energy = .33
	fill.rotation_degrees = Vector3(-30,122,0)
	root.add_child(fill)
	var plane := PlaneMesh.new()
	plane.size = Vector2(200,200)
	var material := StandardMaterial3D.new()
	material.albedo_color = Color("#768ba9")
	material.roughness = .79
	plane.material = material
	var ground := MeshInstance3D.new()
	ground.mesh = plane
	ground.position.y = -.04
	root.add_child(ground)
	var scene := Node3D.new()
	root.add_child(scene)
	return scene

func _capture(camera: Camera3D, eye: Vector3, focus: Vector3, ortho: float, name: String) -> void:
	camera.size = ortho
	camera.look_at_from_position(eye,focus)
	await RenderingServer.frame_post_draw
	await RenderingServer.frame_post_draw
	var target := OS.get_environment("HAVENLINE_TRUCK_ART_REVIEW")
	if target.is_empty():
		target = "/tmp"
	var path := target.path_join(name + ".png")
	var result := root.get_texture().get_image().save_png(path)
	if result != OK:
		push_error("Could not save " + path)

func run() -> void:
	var scene := _stage()
	var truck := Artist.truck()
	var garage := Artist.garage()
	scene.add_child(garage)
	scene.add_child(truck)
	garage.hide()
	var bounds := _bounds(truck)
	var checks := {
		"left blade": truck.find_child("BladeLeft",true,false) != null,
		"right blade": truck.find_child("BladeRight",true,false) != null,
		"envelope": bounds.position.x >= -1.19 and bounds.end.x <= 1.19 and bounds.position.z > -2.38 and bounds.end.z <= 1.49,
		"road contact": absf(bounds.position.y) < .02,
	}
	Artist.set_motion(truck,.9,1.4)
	var left := truck.find_child("BladeLeft", true, false) as Node3D
	var right := truck.find_child("BladeRight", true, false) as Node3D
	var wheel := truck.find_child("WheelFrontLeft", true, false) as Node3D
	checks["counter rotation"] = is_equal_approx(left.rotation.y,1.4) and is_equal_approx(right.rotation.y,-1.4)
	checks["wheel rotation"] = is_equal_approx(wheel.rotation.x,.9)
	Artist.set_motion(truck,0,0)
	Artist.set_damage(truck,0)
	var door := garage.find_child("RollupDoor",true,false)
	var roof := garage.find_child("Roof",true,false) as Node3D
	checks["complete separate door"] = door != null and door.get_child_count() == 12
	Artist.set_door(garage,1.)
	checks["door clears fully"] = not (door.get_child(0) as Node3D).visible
	Artist.set_door(garage,0.)
	checks["door closes again"] = (door.get_child(0) as Node3D).visible
	Artist.set_roof_visibility(garage,false)
	checks["separate roof support"] = roof != null and not roof.visible and door != null
	Artist.set_roof_visibility(garage,true)
	Artist.set_load(truck, {
		"wood": "490000000000000000000000", "stone": 2, "metal": 9,
		"planks": 8, "blocks": 4, "coal": 7, "slate": 1, "meat": 1000,
	})
	var rack := truck.get_node_or_null("CargoPreview") as Node3D
	checks["large mixed cargo uses twelve representative meshes"] = rack != null and rack.get_child_count() == 12
	checks["cargo protrudes above the bed"] = _bounds(rack).end.y > 1.57
	Artist.set_load(truck, {"wood": "1"})
	checks["one lot of wood uses one representative mesh"] = rack.get_child_count() == 1
	Artist.set_load(truck, {})
	checks["cargo empty state clears the rack"] = rack.get_child_count() == 0
	print(JSON.stringify({"bounds":str(bounds),"checks":checks}))
	if "--show" in OS.get_cmdline_user_args():
		root.size = Vector2i(740,610)
		var camera := Camera3D.new()
		camera.projection = Camera3D.PROJECTION_ORTHOGONAL
		scene.add_child(camera)
		camera.make_current()
		Artist.set_load(truck, {"wood": 100, "stone": 384, "metal": 196, "meat": 416})
		await _capture(camera,Vector3(5,4,-6),Vector3(0,.89,-.37),4.15,"Truck-angle")
		await _capture(camera,Vector3(0,2.2,-7),Vector3(0,1,-.38),3.15,"Truck-front")
		garage.show()
		truck.position.z = 2.75
		Artist.set_door(garage,1.0)
		await _capture(camera,Vector3(4.5,4.2,-7),Vector3(0,1.4,1.65),6.9,"Garage-open")
		Artist.set_door(garage,0.0)
		await _capture(camera,Vector3(4.5,4.2,-7),Vector3(0,1.4,1.65),6.9,"Garage-closed")
		Artist.set_roof_visibility(garage,false)
		await _capture(camera,Vector3(-4,8,10),Vector3(0,1,2.3),6.5,"Garage-cutaway")
		Artist.set_roof_visibility(garage,true)
		await _capture(camera,Vector3(-4,4.2,10),Vector3(0,1,2.3),7.1,"Garage-rear")
	quit(0 if checks.values().all(func(passed): return passed) else 1)
