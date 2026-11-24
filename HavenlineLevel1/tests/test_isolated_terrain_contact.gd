extends SceneTree
## Opt-in native physics witness. No rendered pixels, movement, river collision or camp.
const Preview = preload("res://previews/terrain_contact_preview.tscn")
const TerrainSource = preload("res://terrain_source.gd")
const River = preload("res://river_geometry.gd")
const Contact = preload("res://previews/terrain_contact_preview.gd")
const HEIGHT_EPS := 0.002
var checks := 0
var failures: Array[String] = []

func _initialize() -> void:
	call_deferred("_probe")

func _probe() -> void:
	_check(current_scene == null, "fixture did not boot the default scene")
	var fixture := Preview.instantiate() as Node3D
	root.add_child(fixture)
	var nodes := _descendants(fixture)
	_check(nodes.size() == 3, "only visual, body, and collider exist")
	var meshes := 0
	var bodies := 0
	var shapes := 0
	for node: Node in nodes:
		if node is MeshInstance3D:
			meshes += 1
		if node is PhysicsBody3D:
			bodies += 1
		if node is CollisionShape3D:
			shapes += 1
	_check(meshes == 1 and bodies == 1 and shapes == 1, "one visible mesh and one physical shape, no legacy bodies")
	var visual := fixture.get_node_or_null("GroundVisual") as MeshInstance3D
	var body := fixture.get_node_or_null("GroundBody") as StaticBody3D
	var ground := fixture.get_node_or_null("GroundBody/GroundTriangles") as CollisionShape3D
	_check(visual != null and body != null and ground != null, "all three owned nodes available")
	if visual == null or body == null or ground == null:
		_finish(fixture)
		return
	_check(fixture.get("bound") == true, "opt-in source reports bound")
	_check(is_same(visual.mesh, TerrainSource.terrain_mesh()), "reference same accepted source mesh")
	_check(visual.material_override != null and visual.material_override.resource_path ==
		"res://materials/neutral_shore_snow.tres", "neutral R-only shore material")
	_check(visual.global_transform == Transform3D.IDENTITY and ground.global_transform == Transform3D.IDENTITY,
		"mesh and physical triangles share canonical coordinates without Y offset")
	_check(body.collision_layer == Contact.GROUND_LAYER and body.collision_mask == 0, "isolated ray bit only")
	_check(ground.shape is ConcavePolygonShape3D, "physical ground uses triangles, never a height map or plane")
	if not ground.shape is ConcavePolygonShape3D:
		_finish(fixture)
		return
	var triangles := ground.shape as ConcavePolygonShape3D
	_check(not triangles.backface_collision, "downward front-face contacts only")
	_check(triangles.get_faces() == visual.mesh.get_faces(), "native collider triangle positions/order match the render mesh")
	await physics_frame
	await physics_frame
	_check(current_scene == null, "default scene still inactive")
	var state := fixture.get_world_3d().direct_space_state
	var probes: Array[Vector2] = [
		Vector2(0.061, 6.054), Vector2(0.181, 6.187), # opposite halves of one indexed cell
		Vector2(-15.38, 9.37), Vector2(12.113, 4.143), # inland relief
		Vector2(-30.88, 17.13), Vector2(30.87, -17.13), # inward edge controls
	]
	for x: float in [-9.0, 1.5, 4.8, 10.0]:
		var center := River.center_at_x(x)
		var tangent := River.tangent_at_x(x)
		var north := Vector2(-tangent.y, tangent.x)
		var half := River.width_at_x(x) * 0.5
		probes.append(center)
		probes.append(center + north * (half + 1.25))
		probes.append(center - north * (half + 1.25))
	for p: Vector2 in probes:
		var accepted := TerrainSource.sample(p)
		var hit := _down(state, p, Contact.GROUND_LAYER)
		_check(bool(accepted.valid), "source owns hit probe %s" % str(p))
		_check(not hit.is_empty(), "one ray hit %s" % str(p))
		if not hit.is_empty():
			var position: Vector3 = hit.position
			_check(hit.collider == body, "hit belongs to the only ground body")
			_check(absf(position.y - float(accepted.height)) <= HEIGHT_EPS, "ray Y matches exact sampled height")
	for outside: Vector2 in [Vector2(31.2, 0.6), Vector2(-31.2, -0.6), Vector2(0.6, 31.2), Vector2(-0.6, -31.2)]:
		_check(not bool(TerrainSource.sample(outside).valid), "outside source invalid")
		_check(_down(state, outside, Contact.GROUND_LAYER).is_empty(), "no hidden exterior ground")
	_check(_down(state, Vector2(0.061, 6.054), 1).is_empty(), "no neighbor runtime layer body")
	var from_below := PhysicsRayQueryParameters3D.create(Vector3(0.061, -8, 6.054),
		Vector3(0.061, 8, 6.054), Contact.GROUND_LAYER)
	from_below.hit_back_faces = false
	_check(state.intersect_ray(from_below).is_empty(), "backside is not a second ground plane")
	_finish(fixture)

func _descendants(node: Node) -> Array[Node]:
	var result: Array[Node] = []
	for child: Node in node.get_children():
		result.append(child)
		result.append_array(_descendants(child))
	return result

func _down(state: PhysicsDirectSpaceState3D, p: Vector2, mask: int) -> Dictionary:
	var query := PhysicsRayQueryParameters3D.create(Vector3(p.x, 8.0, p.y),
		Vector3(p.x, -8.0, p.y), mask)
	query.hit_back_faces = false
	return state.intersect_ray(query)

func _check(ok: bool, label: String) -> void:
	checks += 1
	if not ok:
		failures.append(label)

func _finish(fixture: Node3D) -> void:
	fixture.free()
	print(JSON.stringify({"suite":"opt_in_accepted_terrain_contact", "checks":checks,
		"failures":failures, "live_terrain_bound":false, "terrain_fixture_only":true,
		"pixels_reviewed":false, "river_motion_tested":false}))
	for label in failures:
		push_error(label)
	quit(0 if failures.is_empty() else 1)
