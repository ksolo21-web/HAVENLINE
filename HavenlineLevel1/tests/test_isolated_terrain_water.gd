extends SceneTree
## Nondefault structure and collision-exclusion probe only; no captured pixels.
const Preview = preload("res://previews/terrain_water_preview.tscn")
const TerrainSource = preload("res://terrain_source.gd")
const River = preload("res://river_geometry.gd")
const GroundContact = preload("res://previews/terrain_contact_preview.gd")
const AcceptedWaterShader = preload("res://materials/accepted_t02_river_water.gdshader")
const EPS := 0.00002
var checks := 0
var failures: Array[String] = []

func _initialize() -> void:
	call_deferred("_probe")

func _probe() -> void:
	_check(current_scene == null, "opt-in probe does not launch default")
	var fixture := Preview.instantiate() as Node3D
	root.add_child(fixture)
	var ground := fixture.get_node_or_null("AcceptedGround") as Node3D
	var water := fixture.get_node_or_null("MapSpanningRiver") as MeshInstance3D
	_check(fixture.get_child_count() == 2 and ground != null and water != null,
		"one proven ground scene and one visible river node")
	if ground == null or water == null:
		_finish(fixture)
		return
	_check(ground.get("bound") == true and fixture.get("water_bound") == true, "both opt-in sources bound")
	_check(fixture.find_children("*", "MeshInstance3D", true, false).size() == 2,
		"one ground mesh plus exactly one water mesh")
	_check(fixture.find_children("*", "PhysicsBody3D", true, false).size() == 1 and
		fixture.find_children("*", "CollisionShape3D", true, false).size() == 1,
		"only known ground body; no water collision shape or concealed camp")
	_check(fixture.find_children("*", "Area3D", true, false).is_empty(),
		"no hidden water detection or gameplay/runtime areas")
	_check(water.global_transform == Transform3D.IDENTITY, "no water position/rotation/scale override")
	_check(water.cast_shadow == GeometryInstance3D.SHADOW_CASTING_SETTING_OFF, "accepted shadow policy")
	_check(is_same(water.mesh, TerrainSource.water_mesh()), "exact accepted shared water mesh object")
	var material := water.material_override as ShaderMaterial
	_check(material != null and is_same(material.shader, AcceptedWaterShader), "exact donor water shader resource")
	if water.mesh == null or material == null:
		_finish(fixture)
		return
	_check(is_equal_approx(float(material.get_shader_parameter("sim_time")), 0.0), "deterministic neutral phase, no inherited clock")
	var arrays := water.mesh.surface_get_arrays(0)
	var vertices: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX]
	var indices: PackedInt32Array = arrays[Mesh.ARRAY_INDEX]
	_check(vertices.size() == 249 * 13, "one accepted 62m span and 13 cross-channel rows")
	_check(indices.size() > 0 and indices.size() % 3 == 0, "indexed accepted triangle mesh")
	var exact_y := true
	for vertex: Vector3 in vertices:
		exact_y = exact_y and vertex.is_finite() and absf(vertex.y - River.WATER_Y) <= EPS
	_check(exact_y, "entire visible water mesh on accepted -0.34m plane")
	var samples := River.plan_samples(0.25)
	_check(samples.size() == 249, "immutable T02 river sample count")
	if vertices.size() == 249 * 13 and samples.size() == 249:
		for i: int in [0, 60, 124, 185, 248]:
			var offset := i * 13
			var expected := samples[i]
			var center: Vector2 = expected.center
			var normal: Vector2 = expected.north_normal
			var half := float(expected.width) * 0.5
			var expected_a := center - normal * half
			var expected_b := center + normal * half
			var left := vertices[offset]
			var mid := vertices[offset + 6]
			var right := vertices[offset + 12]
			_check(absf(left.distance_to(right) - float(expected.width)) <= EPS,
				"local width from exact River slice %d" % i)
			_check(Vector2(mid.x, mid.z).distance_to(center) <= EPS,
				"center preserves accepted west/east/bend pose %d" % i)
			_check(Vector2(left.x, left.z).distance_to(expected_a) <= EPS and
				Vector2(right.x, right.z).distance_to(expected_b) <= EPS,
				"both outer edges match River normal and width %d" % i)
	await physics_frame
	await physics_frame
	var bed_center := River.center_at_x(1.5)
	var ray := PhysicsRayQueryParameters3D.create(Vector3(bed_center.x, 8.0, bed_center.y),
		Vector3(bed_center.x, -8.0, bed_center.y), GroundContact.GROUND_LAYER)
	ray.hit_back_faces = false
	var hit := fixture.get_world_3d().direct_space_state.intersect_ray(ray)
	_check(not hit.is_empty(), "one proven terrain bed contact beneath visible river")
	if not hit.is_empty():
		var point: Vector3 = hit.position
		_check(hit.collider == ground.get_node("GroundBody") and point.y < River.WATER_Y,
			"ray reaches submerged bed, not a water collider")
	_check(current_scene == null, "default still not active")
	_finish(fixture)

func _check(ok: bool, label: String) -> void:
	checks += 1
	if not ok:
		failures.append(label)

func _finish(fixture: Node3D) -> void:
	fixture.free()
	print(JSON.stringify({"suite":"opt_in_accepted_terrain_water", "checks":checks,
		"failures":failures, "pixels_reviewed":false, "has_water_body":false,
		"runtime_bound":false, "native_actor_routes":false}))
	for label in failures:
		push_error(label)
	quit(0 if failures.is_empty() else 1)
