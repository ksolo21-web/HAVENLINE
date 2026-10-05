class_name HavenlineStationKit
extends Node3D

## T05 presentation-only station and prop authority. This component owns asset
## selection, deterministic placement, socket markers, and inspectable bounds.
## It deliberately contains no production, economy, interaction, or animation.

const CATALOG_PATH := "res://assets/stations_v2/catalog.json"
const AUTHORITY_ID := "T05-station-kit-v1"

var catalog: Dictionary = {}
var entries: Dictionary = {}
var scene_cache: Dictionary = {}
var placed: Array[Node3D] = []
var batched_visual: MeshInstance3D

static func read_catalog() -> Dictionary:
	assert(FileAccess.file_exists(CATALOG_PATH), "Missing authored T05 station catalog: " + CATALOG_PATH)
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(CATALOG_PATH))
	assert(parsed is Dictionary, "T05 station catalog must be a JSON object")
	return parsed

func _ready() -> void:
	if catalog.is_empty():
		_load_authority()

func _load_authority() -> void:
	catalog = read_catalog()
	assert(catalog.get("authority_id", "") == AUTHORITY_ID, "Unexpected T05 station authority")
	entries.clear()
	for row: Dictionary in catalog.get("entries", []):
		var asset_id := str(row.get("id", ""))
		assert(not asset_id.is_empty() and not entries.has(asset_id), "Invalid or duplicate T05 asset id: " + asset_id)
		var asset_path := str(row.get("asset", ""))
		assert(ResourceLoader.exists(asset_path), "Missing authored T05 asset: " + asset_path)
		entries[asset_id] = row

func clear_arrangement() -> void:
	if is_instance_valid(batched_visual):
		batched_visual.free()
	batched_visual = null
	for node in placed:
		if is_instance_valid(node):
			node.free()
	placed.clear()

func add_socket_markers(instance: Node3D, row: Dictionary) -> void:
	for socket_name: String in row.sockets:
		var values: Array = row.sockets[socket_name]
		var socket_node := Marker3D.new()
		socket_node.name = "Socket_" + socket_name.to_pascal_case()
		socket_node.position = Vector3(float(values[0]), float(values[1]), float(values[2]))
		socket_node.set_meta("t05_socket", socket_name)
		instance.add_child(socket_node)

func configure_identity(instance: Node3D, asset_id: String, row: Dictionary) -> void:
	instance.name = asset_id.to_pascal_case()
	instance.set_meta("t05_asset_id", asset_id)
	instance.set_meta("t05_requirement", str(row.requirement))
	instance.set_meta("t05_footprint", Vector2(float(row.footprint[0]), float(row.footprint[1])))
	instance.set_meta("t05_clearance", float(row.clearance))

func instantiate_asset(asset_id: String, parent: Node = self) -> Node3D:
	if catalog.is_empty():
		_load_authority()
	assert(entries.has(asset_id), "Unknown T05 station asset: " + asset_id)
	var row: Dictionary = entries[asset_id]
	var asset_path := str(row.asset)
	if not scene_cache.has(asset_path):
		scene_cache[asset_path] = load(asset_path)
	var packed: PackedScene = scene_cache[asset_path]
	var instance: Node3D = packed.instantiate()
	configure_identity(instance, asset_id, row)
	parent.add_child(instance)
	add_socket_markers(instance, row)
	return instance

func collect_batch_parts(node: Node3D, parent_transform: Transform3D, groups: Dictionary) -> void:
	var combined := parent_transform * node.transform
	if node is MeshInstance3D and node.mesh != null:
		assert(node.skin == null, "T05 static station kit cannot batch skinned geometry")
		for surface_index in node.mesh.get_surface_count():
			var active_material: Material = node.get_active_material(surface_index)
			var material_key := active_material.resource_name if active_material != null else "unmaterialed"
			assert(not material_key.is_empty(), "Every T05 surface needs a stable named material")
			if not groups.has(material_key):
				groups[material_key] = {"material": active_material, "parts": []}
			groups[material_key].parts.append({"mesh": node.mesh, "surface": surface_index, "transform": combined})
	for child in node.get_children():
		if child is Node3D:
			collect_batch_parts(child, combined, groups)

func compile_batch(groups: Dictionary) -> ArrayMesh:
	var result := ArrayMesh.new()
	var material_keys: Array = groups.keys()
	material_keys.sort()
	for material_key: String in material_keys:
		var group: Dictionary = groups[material_key]
		var tool := SurfaceTool.new()
		tool.begin(Mesh.PRIMITIVE_TRIANGLES)
		tool.set_material(group.material)
		for part: Dictionary in group.parts:
			tool.append_from(part.mesh, int(part.surface), part.transform)
		tool.commit(result)
	return result

func arrangement_transform(
	arrangement_id: String,
	asset_id: String,
	origin := Vector3.ZERO,
	ground_height: Callable = Callable()
) -> Transform3D:
	if catalog.is_empty():
		_load_authority()
	assert(catalog.arrangements.has(arrangement_id), "Unknown T05 arrangement: " + arrangement_id)
	for placement: Dictionary in catalog.arrangements[arrangement_id]:
		if str(placement.id) != asset_id:
			continue
		var p: Array = placement.position
		var world_x := origin.x + float(p[0])
		var world_z := origin.z + float(p[2])
		var world_y := origin.y + float(p[1])
		if ground_height.is_valid():
			world_y = float(ground_height.call(Vector2(world_x, world_z)))
		return Transform3D(Basis(Vector3.UP, float(placement.rotation_y)), Vector3(world_x, world_y, world_z))
	assert(false, "T05 arrangement %s does not contain %s" % [arrangement_id, asset_id])
	return Transform3D.IDENTITY

func build_arrangement(
	arrangement_id: String,
	origin := Vector3.ZERO,
	ground_height: Callable = Callable(),
	excluded_asset_ids: Array[String] = []
) -> Array[Node3D]:
	if catalog.is_empty():
		_load_authority()
	assert(catalog.arrangements.has(arrangement_id), "Unknown T05 arrangement: " + arrangement_id)
	clear_arrangement()
	var batch_groups := {}
	for placement: Dictionary in catalog.arrangements[arrangement_id]:
		var asset_id := str(placement.id)
		if excluded_asset_ids.has(asset_id):
			continue
		var row: Dictionary = entries[asset_id]
		var placement_transform := arrangement_transform(arrangement_id, asset_id, origin, ground_height)
		var packed: PackedScene = load(str(row.asset))
		var visual_source: Node3D = packed.instantiate()
		collect_batch_parts(visual_source, placement_transform, batch_groups)
		visual_source.free()
		var marker_root := Node3D.new()
		configure_identity(marker_root, asset_id, row)
		marker_root.transform = placement_transform
		marker_root.set_meta("t05_arrangement", arrangement_id)
		add_socket_markers(marker_root, row)
		add_child(marker_root)
		placed.append(marker_root)
	batched_visual = MeshInstance3D.new()
	batched_visual.name = "Batched" + arrangement_id.to_pascal_case() + "StationKitVisual"
	batched_visual.mesh = compile_batch(batch_groups)
	batched_visual.set_meta("t05_static_batch", true)
	batched_visual.set_meta("t05_material_surface_count", batched_visual.mesh.get_surface_count())
	add_child(batched_visual)
	return placed

func socket(asset: Node3D, socket_name: String) -> Marker3D:
	var result := asset.get_node_or_null("Socket_" + socket_name.to_pascal_case()) as Marker3D
	assert(result != null, "Missing T05 socket %s on %s" % [socket_name, str(asset.get_meta("t05_asset_id", asset.name))])
	return result

func descriptor() -> Dictionary:
	if catalog.is_empty():
		_load_authority()
	var total_triangles := 0
	var material_ids := {}
	var socket_count := 0
	for row: Dictionary in catalog.entries:
		total_triangles += int(row.triangles)
		for material_id: String in row.materials:
			material_ids[material_id] = true
		socket_count += row.sockets.size()
	return {
		"authority_id": AUTHORITY_ID,
		"asset_count": entries.size(),
		"arrangement_count": catalog.arrangements.size(),
		"total_catalog_triangles": total_triangles,
		"visible_material_palette_count": material_ids.size(),
		"socket_count": socket_count,
		"placed_count": placed.size(),
		"batched_surface_count": batched_visual.mesh.get_surface_count() if is_instance_valid(batched_visual) else 0,
		"runtime_logic_included": bool(catalog.runtime_logic_included),
		"visual_approval_claimed": bool(catalog.visual_approval_claimed),
		"physical_4k60_certified": bool(catalog.physical_4k60_certified),
		"performance_contract": catalog.performance_contract.duplicate(true)
	}
