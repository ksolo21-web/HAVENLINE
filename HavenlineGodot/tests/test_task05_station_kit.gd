extends SceneTree
# Exact-source R10H validation after R10G service-counter/defense visual materialization.
# Exact triangle assertions intentionally fail closed if authored geometry drifts.

const StationKit = preload("res://scripts/station_kit.gd")
const Boundary = preload("res://scripts/camp_boundary.gd")
const River = preload("res://scripts/river_geometry.gd")

var checks: Array = []
var failures: Array = []

func check(label: String, passed: bool) -> void:
	checks.append({"name": label, "passed": passed})
	if not passed:
		failures.append(label)

func visit(node: Node, callback: Callable) -> void:
	callback.call(node)
	for child in node.get_children():
		visit(child, callback)

func material_state(node: Node) -> Array:
	var state: Array = []
	visit(node, func(part):
		if part is MeshInstance3D and part.mesh != null:
			for surface in part.mesh.get_surface_count():
				var material = part.get_active_material(surface)
				var colors = part.mesh.surface_get_arrays(surface)[Mesh.ARRAY_COLOR]
				if material is BaseMaterial3D:
					state.append({"material": material, "color": material.albedo_color,
						"metallic": material.metallic, "roughness": material.roughness,
						"uses_colors": material.vertex_color_use_as_albedo,
						"has_colors": colors != null and colors.size() > 0})
	)
	return state

func test_material_binding(kit: Node, asset_id: String, before: Array, instance: Node) -> void:
	var active := material_state(instance)
	var consistent := before.size() == active.size() and not active.is_empty()
	for index in mini(before.size(), active.size()):
		var source: Dictionary = before[index]
		var actual: Dictionary = active[index]
		consistent = consistent and (not actual.has_colors or actual.uses_colors)
		consistent = consistent and source.color == actual.color and source.metallic == actual.metallic and source.roughness == actual.roughness
	check(asset_id + " preserves authored pigment and PBR in standalone rendering", consistent)
	# A second instance must not mutate cached imported materials. This catches
	# global-resource changes that leak into unrelated stations or future loads.
	var second: Node = kit.instantiate_asset(asset_id)
	var immutable := true
	for source: Dictionary in before:
		immutable = immutable and source.material.vertex_color_use_as_albedo == source.uses_colors
	check(asset_id + " keeps cached source material flags immutable", immutable)
	second.queue_free()

func bounds_visit(node: Node, root_node: Node3D, state: Dictionary) -> void:
	if node is MeshInstance3D:
		var mesh_node := node as MeshInstance3D
		if mesh_node.mesh != null:
			var transformed := root_node.global_transform.affine_inverse() * mesh_node.global_transform * mesh_node.get_aabb()
			state.bounds = transformed if not state.found else (state.bounds as AABB).merge(transformed)
			state.found = true
	for child in node.get_children():
		bounds_visit(child, root_node, state)

func local_bounds(root_node: Node3D) -> AABB:
	var state := {"bounds": AABB(), "found": false}
	bounds_visit(root_node, root_node, state)
	return state.bounds

func socket_count(node: Node) -> int:
	var count := 1 if node is Marker3D and node.has_meta("t05_socket") else 0
	for child in node.get_children():
		count += socket_count(child)
	return count

func forbidden_count(node: Node) -> int:
	var count := 1 if node is PhysicsBody3D or node is CollisionObject3D or node is AnimationPlayer or node is Skeleton3D else 0
	for child in node.get_children():
		count += forbidden_count(child)
	return count

func minimum_lane_clearance(placement: Dictionary, row: Dictionary) -> float:
	var centre := Vector2(float(placement.position[0]), float(placement.position[2]))
	var half := Vector2(float(row.footprint[0]), float(row.footprint[1])) * 0.5
	var angle := float(placement.rotation_y)
	var result := INF
	for x_step in range(13):
		for z_step in range(13):
			var local := Vector2(lerpf(-half.x, half.x, float(x_step) / 12.0), lerpf(-half.y, half.y, float(z_step) / 12.0))
			var rotated := Vector2(local.x * cos(angle) + local.y * sin(angle), -local.x * sin(angle) + local.y * cos(angle))
			result = minf(result, Boundary.lane_signed_distance(centre + rotated))
	return result

func footprint_samples(placement: Dictionary, row: Dictionary) -> Array[Vector2]:
	var centre := Vector2(float(placement.position[0]), float(placement.position[2]))
	var half := Vector2(float(row.footprint[0]), float(row.footprint[1])) * 0.5
	var angle := float(placement.rotation_y)
	var result: Array[Vector2] = []
	for x_step in range(5):
		for z_step in range(5):
			var local := Vector2(lerpf(-half.x, half.x, float(x_step) / 4.0), lerpf(-half.y, half.y, float(z_step) / 4.0))
			result.append(centre + Vector2(local.x * cos(angle) + local.y * sin(angle), -local.x * sin(angle) + local.y * cos(angle)))
	return result

func minimum_shore_clearance(placement: Dictionary, row: Dictionary) -> float:
	var result := INF
	for point in footprint_samples(placement, row):
		result = minf(result, River.shore_distance(point))
	return result

func inside_current_movement_bounds(placement: Dictionary, row: Dictionary) -> bool:
	for point in footprint_samples(placement, row):
		if absf(point.x) > 14.2 or absf(point.y) > 16.2:
			return false
	return true

func leaves_crossing_reserves_open(placement: Dictionary, row: Dictionary) -> bool:
	for point in footprint_samples(placement, row):
		if River.crossing_reserved(point):
			return false
	return true

func placement_inside_fence(placement: Dictionary, row: Dictionary) -> bool:
	var centre := Vector2(float(placement.position[0]), float(placement.position[2]))
	var half := Vector2(float(row.footprint[0]), float(row.footprint[1])) * 0.5
	var angle := float(placement.rotation_y)
	var extent_x := absf(cos(angle)) * half.x + absf(sin(angle)) * half.y
	var extent_z := absf(sin(angle)) * half.x + absf(cos(angle)) * half.y
	if absf(centre.x) + extent_x > Boundary.SIDE_X - 0.30 or centre.y + extent_z > Boundary.NORTH_Z - 0.30:
		return false
	for local in [Vector2(-half.x,-half.y), Vector2(half.x,-half.y), Vector2(-half.x,half.y), Vector2(half.x,half.y)]:
		var rotated := Vector2(local.x * cos(angle) + local.y * sin(angle), -local.x * sin(angle) + local.y * cos(angle))
		var corner := centre + rotated
		if Boundary.push_off_fence(corner, 0.32).distance_to(corner) > 0.001:
			return false
	return true

func color_fixture_mesh(colored: bool) -> ArrayMesh:
	var arrays: Array = []
	arrays.resize(Mesh.ARRAY_MAX)
	arrays[Mesh.ARRAY_VERTEX] = PackedVector3Array([Vector3.ZERO, Vector3.RIGHT, Vector3.FORWARD])
	arrays[Mesh.ARRAY_NORMAL] = PackedVector3Array([Vector3.UP, Vector3.UP, Vector3.UP])
	arrays[Mesh.ARRAY_INDEX] = PackedInt32Array([0, 1, 2])
	if colored:
		arrays[Mesh.ARRAY_COLOR] = PackedColorArray([Color.RED, Color.GREEN, Color.BLUE])
	var result := ArrayMesh.new()
	result.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arrays)
	return result

func test_mixed_vertex_color_batch(kit: Node3D) -> void:
	var colored := color_fixture_mesh(true)
	var plain := color_fixture_mesh(false)
	var material := ShaderMaterial.new()
	var shader := Shader.new()
	shader.code = "shader_type spatial; void fragment(){ALBEDO=COLOR.rgb;}"
	material.shader = shader
	for reverse_order in [false, true]:
		var first := plain if reverse_order else colored
		var second := colored if reverse_order else plain
		var groups := {"fixture": {"material": material, "parts": [
			{"mesh": first, "surface": 0, "transform": Transform3D.IDENTITY},
			{"mesh": second, "surface": 0, "transform": Transform3D(Basis.IDENTITY, Vector3(2, 0, 0))}
		]}}
		var merged: ArrayMesh = kit.compile_batch(groups)
		var arrays := merged.surface_get_arrays(0)
		var colors: PackedColorArray = arrays[Mesh.ARRAY_COLOR]
		var vertices: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX]
		var uncolored_white := true
		var authored_color_preserved := true
		for i in colors.size():
			var is_plain := (vertices[i].x < 1.5) if reverse_order else (vertices[i].x > 1.5)
			if is_plain:
				uncolored_white = uncolored_white and colors[i].is_equal_approx(Color.WHITE)
			else:
				authored_color_preserved = authored_color_preserved and colors[i] in [Color.RED, Color.GREEN, Color.BLUE]
		var suffix := " (reverse=" + str(reverse_order) + ")"
		check("Mixed-color batch retains both triangle payloads" + suffix, colors.size() == 6)
		check("Missing source colors normalize to white, never black" + suffix, uncolored_white)
		check("Authored vertex colors survive batching" + suffix, authored_color_preserved)
		check("Batching never mutates the original uncolored mesh" + suffix, plain.surface_get_arrays(0)[Mesh.ARRAY_COLOR] == null)
		check("Batching clones rather than mutates shared material" + suffix, merged.surface_get_material(0) != material)

func _initialize() -> void:
	call_deferred("run")

func run() -> void:
	var kit := StationKit.new()
	root.add_child(kit)
	test_mixed_vertex_color_batch(kit)
	var catalog := StationKit.read_catalog()
	var descriptor := kit.descriptor()
	var lakeshore_lane_clearances := {}
	check("Station authority is versioned", descriptor.authority_id == "T05-station-kit-v1")
	check("Catalog contains the frozen 22-asset kit", descriptor.asset_count == 22)
	check("Camp and lakeshore arrangements are both declared", descriptor.arrangement_count == 2)
	check("Catalog triangle total has broad headroom", descriptor.total_catalog_triangles == 176924 and descriptor.total_catalog_triangles <= 180000)
	check("Shared palette stays within 12 visible materials", descriptor.visible_material_palette_count == 12 and descriptor.visible_material_palette_count <= 12)
	check("Catalog exposes future-task sockets", descriptor.socket_count >= 35)
	check("No gameplay logic is claimed", not descriptor.runtime_logic_included)
	check("No visual approval is self-claimed", not descriptor.visual_approval_claimed)
	check("No physical 4K60 certification is self-claimed", not descriptor.physical_4k60_certified)
	check("Physics population budget remains zero", int(descriptor.performance_contract.active_physics) == 0)
	check("Skeleton budget remains zero", int(descriptor.performance_contract.skeletons) == 0)
	check("Animation budget remains zero", int(descriptor.performance_contract.animations) == 0)

	var expected_ids := [
		"cargo_crate", "conveyor_straight", "cooked_food_stack", "cooker_processor",
		"defense_platform", "fish_crate", "fishing_rack", "fuel_canister", "hearth_vessel",
		"intake_machine", "metal_stack", "money_stack", "pad_build", "pad_input",
		"pad_output", "pad_payment", "pad_stock", "pad_upgrade", "processing_counter",
		"service_counter", "stone_stack", "wood_stack"
	]
	var ids: Array = []
	var requirements := {}
	var total_bytes := 0
	for row: Dictionary in catalog.entries:
		var asset_id := str(row.id)
		ids.append(asset_id)
		requirements[str(row.requirement)] = true
		var path := str(row.asset)
		check(asset_id + " resource exists", ResourceLoader.exists(path))
		var bytes := FileAccess.get_file_as_bytes(path)
		total_bytes += bytes.size()
		check(asset_id + " hash is source-bound", FileAccess.get_sha256(path) == str(row.sha256))
		var raw: Node = (load(path) as PackedScene).instantiate()
		var source_materials := material_state(raw)
		var instance := kit.instantiate_asset(asset_id)
		test_material_binding(kit, asset_id, source_materials, instance)
		raw.free()
		var bounds := local_bounds(instance)
		var footprint := Vector2(float(row.footprint[0]), float(row.footprint[1]))
		check(asset_id + " has stable nonzero bounds", bounds.size.x > 0.1 and bounds.size.y > 0.1 and bounds.size.z > 0.1)
		check(asset_id + " respects catalog footprint X", bounds.size.x <= footprint.x + 0.03)
		check(asset_id + " respects catalog footprint Z", bounds.size.z <= footprint.y + 0.03)
		check(asset_id + " has a shallow terrain-seating overlap", bounds.position.y >= -0.09 and bounds.position.y <= 0.01)
		var forbidden_nodes := forbidden_count(instance)
		var socket_nodes := socket_count(instance)
		check(asset_id + " contains no physics, skeleton, or animation", forbidden_nodes == 0)
		check(asset_id + " exposes every declared socket", socket_nodes == row.sockets.size())
		instance.free()
	ids.sort()
	check("Asset IDs are deterministic and complete", ids == expected_ids)
	var pad_silhouettes := {}
	var pad_icons := {}
	for pad_id: String in ["pad_build", "pad_upgrade", "pad_input", "pad_output", "pad_stock", "pad_payment"]:
		var visual_variant: Dictionary = kit.entries[pad_id].visual_variant
		pad_silhouettes[str(visual_variant.silhouette)] = true
		pad_icons[str(visual_variant.icon)] = true
	check("Ground-pad purposes have six distinct silhouettes", pad_silhouettes.size() == 6)
	check("Ground-pad purposes have six distinct in-world icons", pad_icons.size() == 6)
	check("Frozen asset-family requirements R01-R07 are covered", requirements.keys().size() == 7 and requirements.has("T05-R01") and requirements.has("T05-R02") and requirements.has("T05-R03") and requirements.has("T05-R04") and requirements.has("T05-R05") and requirements.has("T05-R06") and requirements.has("T05-R07"))
	check("Generated source kit is under 15 MiB", total_bytes <= 15 * 1024 * 1024)
	for placement: Dictionary in catalog.arrangements.camp:
		var row: Dictionary = kit.entries[str(placement.id)]
		check(str(placement.id) + " remains inside the T03 camp boundary", placement_inside_fence(placement, row))
		if str(placement.id) != "hearth_vessel":
			check(str(placement.id) + " leaves the T03 travel lanes visibly open", minimum_lane_clearance(placement, row) >= 0.05)
	check("Heated vessel remains the intended central-lane destination", minimum_lane_clearance(catalog.arrangements.camp[0], kit.entries.hearth_vessel) < 0.0)
	for placement: Dictionary in catalog.arrangements.lakeshore:
		var asset_id := str(placement.id)
		var row: Dictionary = kit.entries[asset_id]
		var lane_clearance := minimum_lane_clearance(placement, row)
		lakeshore_lane_clearances[asset_id] = lane_clearance
		check(asset_id + " lakeshore placement leaves T03 routes open", lane_clearance >= 0.05)
		check(asset_id + " lakeshore placement leaves all T02 crossing reserves open", leaves_crossing_reserves_open(placement, row))
		check(asset_id + " lakeshore placement remains on traversable dry bank", minimum_shore_clearance(placement, row) >= River.DEFAULT_DRY_MARGIN - 0.001)
		check(asset_id + " lakeshore placement remains inside current movement bounds", inside_current_movement_bounds(placement, row))

	var camp := kit.build_arrangement("camp")
	check("Camp arrangement deterministically places 11 assets", camp.size() == 11)
	check("Camp arrangement includes the heated vessel", camp.any(func(node): return node.get_meta("t05_asset_id", "") == "hearth_vessel"))
	check("Camp visual batches to the shared 12-material palette", kit.batched_visual.mesh.get_surface_count() == 12)
	check("Camp batch remains below the 48 draw-call ceiling", kit.batched_visual.mesh.get_surface_count() <= 48)
	check("Camp batch retains its full triangle payload", kit.batched_visual.mesh.get_faces().size() / 3 == 105428)
	var hearth_transform := kit.arrangement_transform("camp", "hearth_vessel", Vector3.ZERO)
	check("Interactive hearth placement resolves from the same catalog", hearth_transform.origin.is_equal_approx(Vector3(0.0, 0.0, 0.2)))
	var camp_without_hearth := kit.build_arrangement("camp", Vector3.ZERO, Callable(), ["hearth_vessel"])
	check("Integration can reserve the animated gameplay hearth without duplicate geometry", camp_without_hearth.size() == 10 and kit.batched_visual.mesh.get_faces().size() / 3 == 79460)
	var lakeshore := kit.build_arrangement("lakeshore")
	check("Lakeshore arrangement deterministically places 10 assets", lakeshore.size() == 10)
	check("Lakeshore arrangement includes fishing and processing fixtures", lakeshore.any(func(node): return node.get_meta("t05_asset_id", "") == "fishing_rack") and lakeshore.any(func(node): return node.get_meta("t05_asset_id", "") == "cooker_processor"))
	check("Lakeshore visual batches to 10 material surfaces", kit.batched_visual.mesh.get_surface_count() == 10)
	check("Lakeshore batch remains below the 48 draw-call ceiling", kit.batched_visual.mesh.get_surface_count() <= 48)
	check("Lakeshore batch retains its full triangle payload", kit.batched_visual.mesh.get_faces().size() / 3 == 67648)

	print(JSON.stringify({
		"suite": "T05_station_and_prop_kit",
		"checks": checks,
		"failures": failures,
		"passed": failures.is_empty(),
		"asset_count": descriptor.asset_count,
		"catalog_triangles": descriptor.total_catalog_triangles,
		"catalog_bytes": total_bytes,
		"lakeshore_lane_clearances": lakeshore_lane_clearances,
		"independent_critic": false,
		"physical_4k60_verified": false
	}))
	kit.free()
	quit(0 if failures.is_empty() else 1)
