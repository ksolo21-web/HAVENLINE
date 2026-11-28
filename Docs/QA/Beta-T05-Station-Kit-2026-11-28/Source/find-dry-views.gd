extends SceneTree
const Session = preload("res://tests/lifecycle_test_profile.gd")
const Cam = preload("res://field_camera.gd")
var field

func _initialize() -> void:
	run.call_deferred()

func _sets(fixture: Node3D) -> PackedVector3Array:
	var points := PackedVector3Array()
	for mesh: MeshInstance3D in fixture.find_children("*","MeshInstance3D",true,false):
		for surface in mesh.mesh.get_surface_count():
			for vertex in mesh.mesh.surface_get_arrays(surface)[Mesh.ARRAY_VERTEX]:
				points.append(mesh.to_global(vertex))
	return points

func run() -> void:
	field = load("res://field_opening.tscn").instantiate()
	root.add_child(field)
	for i in 8: await physics_frame
	field.set_physics_process(false)
	for choice in [["FishingRackFixture",Vector2i(492,546)],["FishCrateFixture",Vector2i(960,540)]]:
		root.size = choice[1]
		for i in 3: await process_frame
		field.graphics.refresh_window()
		field.set_zoom_ratio(2.)
		await process_frame
		var item: Node3D = field.lakeshore.inlet_fixtures.get_node(choice[0])
		var base := item.global_position
		var cam: Camera3D = field.camera
		cam.global_position = base+field.camera_follow_offset
		var outline := PackedVector2Array()
		for p in _sets(item):
			outline.append(cam.unproject_position(p))
		var hull := Geometry2D.convex_hull(outline)
		var h = field.opening_hud
		var taken: Array[Rect2] = [h.counts_area.grow(9),Cam.quality_plate(h.quality)]
		for ctl in [h.plate,h.objective,h.camp_dock.nav,h.camp_dock.build,h.get_node_or_null("HomeCompass")]:
			if ctl and ctl.visible: taken.append(ctl.get_global_rect().grow(8))
		var safe := root.get_visible_rect().grow(-12)
		var best := INF
		var selected := Vector3.INF
		var margin := 0.
		var approach: Node3D = item.get_node("DryApproach")
		for ix in range(-12,13):
			for iz in range(-12,13):
				var at := approach.global_position + Vector3(ix*.24,-.025,iz*.24)
				if field.lakeshore.constrain_motion(at,at,field.layout.actor_radius).distance_to(at)>.02:
					continue
				cam.global_position = at+field.camera_follow_offset
				var shift := cam.unproject_position(base)-hull[0]
				var raw_ref := cam.unproject_position(base)
				var delta := raw_ref - root.get_visible_rect().get_center()
				var box := Rect2(hull[0]+delta,Vector2.ZERO)
				for p in hull: box=box.expand(p+delta)
				var overlapped := 0.
				for region in taken:
					overlapped+=box.intersection(region).get_area()
				var outside := box.get_area()-box.intersection(safe).get_area()
				var cost := outside*.10+overlapped*.12+at.distance_squared_to(approach.global_position)
				if cost>=best: continue
				best=cost
				selected=at
				margin=outside+overlapped
		print("SHORE_POSE ",choice[0]," ",selected," overlap ",margin)
	await Session.drain_field_audio(self,field)
	field.free()
	quit()
