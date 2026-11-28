extends SceneTree
const Kit = preload("res://field_station_kit.gd")
const Pads = preload("res://field_station_pad.gd")
const Art = preload("res://field_art.gd")
const Session = preload("res://tests/lifecycle_test_profile.gd")
var checks := {}

func _initialize() -> void:
	if not Session.isolated(self,"res://tests/qa_field_station_kit.gd"):
		run.call_deferred()

func run() -> void:
	var field = load("res://field_opening.tscn").instantiate()
	root.add_child(field)
	current_scene = field
	await physics_frame
	var inlet: Node3D = field.lakeshore.inlet_fixtures
	checks["four adapted fixtures use the actual Level 1 inlet"] = inlet.get_child_count() == Kit.INLET_LAYOUT.size()
	checks["no new physics bodies, active skeletons or animation players"] = 		inlet.find_children("*","PhysicsBody3D",true,false).is_empty() and 		inlet.find_children("*","Skeleton3D",true,false).is_empty() and 		inlet.find_children("*","AnimationPlayer",true,false).is_empty()
	var radius := float(field.layout.actor_radius)
	for fixture: Node3D in inlet.get_children():
		var prefix := String(fixture.name)
		var spot: Node3D = fixture.get_node("DryApproach")
		var approach := Vector2(spot.global_position.x,spot.global_position.z)
		var deck: Rect2 = fixture.get_meta(&"station_footprint")
		checks[prefix+" has a dry approach past the capsule margin"] = 			not deck.grow(radius).has_point(Vector2(spot.position.x,spot.position.z)) and 			not Geometry2D.is_point_in_polygon(approach,field.lakeshore.shore)
		var center := fixture.to_global(Vector3(deck.get_center().x,0,deck.get_center().y))
		var stopped: Vector3 = field.lakeshore.constrain_motion(spot.global_position,center,radius)
		var local := fixture.to_local(stopped)
		checks[prefix+" stops a capsule before solid structure"] = not deck.grow(radius-.006).has_point(Vector2(local.x,local.z))
		checks[prefix+" small valid approach stays available"] = 			field.lakeshore.constrain_motion(spot.global_position,spot.global_position,radius).distance_to(spot.global_position)<.012
		var boxes: Array[AABB] = []
		var fitted: Node3D = fixture.get_child(0)
		Art._bounds(fitted,Transform3D.IDENTITY,boxes)
		checks[prefix+" grounded model geometry"] = not boxes.is_empty() and absf(boxes[0].position.y)<.005
	var rack: Node3D = inlet.get_node("FishingRackFixture")
	var cast: Vector3 = rack.get_node("Cast").global_position
	checks["rack rod tips project high above the water"] = cast.y>1.6 and 		Geometry2D.is_point_in_polygon(Vector2(cast.x,cast.z),field.lakeshore.shore)
	var full: Node3D = Kit.instantiate("fish_crate")
	var empty: Node3D = Kit.instantiate("fish_crate_empty")
	checks["stocked crate and empty landing surface have separate assets and sockets"] = 		full.has_node("StockTop") and empty.has_node("CatchPile") and 		full.get_child(0).scene_file_path != empty.get_child(0).scene_file_path
	var fish_paint: Material = (full.find_children("*","MeshInstance3D",true,false)[0] as MeshInstance3D).get_active_material(0)
	checks["Godot uses the authored linear paint instead of a white default"] = fish_paint.vertex_color_use_as_albedo and not fish_paint.vertex_color_is_srgb
	full.free()
	empty.free()
	var net := {}
	for role: String in Pads.COLORS:
		var deck := Pads.create(role)
		net[deck.mesh.resource_name+str(Pads.SILHOUETTES[role])+Pads.COLORS[role].to_html()] = true
		checks[role+" deck retains a positive shallow side wall"] = 			deck.get_aabb().size.y>.03 and deck.get_aabb().size.y<Pads.FACE_Y
		deck.free()
	checks["six distinguishable pad silhouettes and finishes"] = net.size()==6
	var anchor: Node3D = field.field_env.buy_anchor
	checks["visible founding plot keeps existing payment and reach surfaces"] = 		anchor.has_node("Gray") and anchor.has_node("Brackets") and anchor.has_node("Platform") and anchor.has_node("IconSocket")
	var active_border: MeshInstance3D = anchor.get_node("Brackets")
	var expected_height := Pads.FACE_Y+.002
	checks["interactive outline is raised above visual deck without changing its flat extent"] = 		is_equal_approx(active_border.get_aabb().position.y,expected_height) and 		active_border.get_aabb().size.x>2.85 and active_border.get_aabb().size.z>2.30
	checks["existing oven raw and hot trays retain their geometry-aligned placement"] = 		field.lakeshore.cooker_input.position.x<-.8 and field.lakeshore.cooker_output.position.x>.8
	print(JSON.stringify({"suite":"field_station_kit","checks":checks}))
	await Session.drain_field_audio(self,field)
	field.free()
	quit(int(false in checks.values()))
