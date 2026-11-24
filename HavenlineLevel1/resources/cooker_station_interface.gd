extends RefCounted
## Opt-in station binding check, not a recipe, collision query, or approval system.
## The station, socket, and route records must come from pinned authoritative evidence.

static func _id(value: Variant) -> bool:
	if typeof(value) != TYPE_STRING:
		return false
	var raw: String = value
	return not raw.is_empty() and raw == raw.strip_edges()

static func _role(record: Dictionary, expected: String) -> bool:
	var value: Variant = record.get("role")
	return typeof(value) == TYPE_STRING and value == expected

static func _positive(value: Variant) -> bool:
	return (typeof(value) == TYPE_INT or typeof(value) == TYPE_FLOAT) and is_finite(float(value)) and value > 0

static func _flag(record: Dictionary, key: String) -> bool:
	var value: Variant = record.get(key)
	return typeof(value) == TYPE_BOOL and value

static func _point(value: Variant) -> bool:
	return typeof(value) == TYPE_VECTOR3 and value.is_finite()

static func _matches(record: Dictionary, station: Dictionary, yaw: int) -> bool:
	for key in ["station_id", "mesh_id", "placement_id", "revision_id"]:
		if not _id(record.get(key)) or record[key] != station[key]:
			return false
	var other_yaw: Variant = record.get("yaw_degrees")
	return typeof(other_yaw) == TYPE_INT and other_yaw == yaw

static func _socket(station: Dictionary, socket: Dictionary, route: Dictionary, kind: String, end_sign: int, yaw: int) -> bool:
	var socket_id: Variant = socket.get("socket_id")
	if not _id(socket_id) or not _role(socket, kind) or not _flag(socket, "confirmed"):
		return false
	if not _matches(socket, station, yaw) or not _matches(route, station, yaw):
		return false
	if not _id(route.get("socket_id")) or route.get("socket_id") != socket_id or not _role(route, kind) or not _flag(route, "confirmed"):
		return false
	if not _flag(route, "gate_state_verified"):
		return false
	var local_socket: Variant = socket.get("local_position")
	var world_anchor: Variant = route.get("world_anchor")
	var reach: Variant = route.get("socket_reach_limit_m")
	var load_radius: Variant = route.get("load_radius_m")
	var center_clearance: Variant = route.get("min_center_clearance_m")
	var required_margin: Variant = route.get("required_residual_m")
	if not _point(local_socket) or not _point(world_anchor):
		return false
	for scalar in [reach, load_radius, center_clearance, required_margin]:
		if not _positive(scalar):
			return false
	if center_clearance - load_radius < required_margin:
		return false
	var origin: Vector3 = station["world_origin"]
	var anchor_delta: Vector3 = world_anchor - origin
	if not anchor_delta.is_finite():
		return false
	# Map station forward (+Z) by exact cardinal axis to avoid trigonometric
	# tolerances at the zero end boundary.
	var axis: Vector3 = {0: Vector3.BACK, 90: Vector3.RIGHT, 180: Vector3.FORWARD, 270: Vector3.LEFT}[yaw]
	if local_socket.z * end_sign <= 0.0 or anchor_delta.dot(axis) * end_sign <= 0.0:
		return false
	var p: Vector3 = local_socket
	var rotated: Vector3 = {0: p, 90: Vector3(p.z, p.y, -p.x), 180: Vector3(-p.x, p.y, -p.z), 270: Vector3(-p.z, p.y, p.x)}[yaw]
	var world_socket: Vector3 = origin + rotated
	return world_socket.is_finite() and world_anchor.distance_to(world_socket) <= reach

static func binding_is_valid(station: Dictionary, intake: Dictionary, output: Dictionary, intake_route: Dictionary, output_route: Dictionary) -> bool:
	if not _flag(station, "active") or not _flag(station, "mesh_confirmed"):
		return false
	if not _point(station.get("world_origin")):
		return false
	for key in ["station_id", "mesh_id", "placement_id", "revision_id"]:
		if not _id(station.get(key)):
			return false
	var degrees: Variant = station.get("yaw_degrees")
	if typeof(degrees) != TYPE_INT or not [0, 90, 180, 270].has(degrees):
		return false
	if intake.get("socket_id") == output.get("socket_id"):
		return false
	return (
		_socket(station, intake, intake_route, "intake", -1, degrees)
		and _socket(station, output, output_route, "output", 1, degrees)
	)
