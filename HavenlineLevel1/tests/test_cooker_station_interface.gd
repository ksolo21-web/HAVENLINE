extends SceneTree
const Cooker = preload("res://resources/cooker_station_interface.gd")
var checks: int = 0
var failures: int = 0

func _check(ok: bool, label: String) -> void:
	checks += 1
	if not ok:
		failures += 1
		push_error(label)

func _records(yaw: int) -> Array:
	var origin := Vector3(3, 1, 7)
	var pinned := {"station_id":"s", "mesh_id":"m", "placement_id":"p", "revision_id":"r", "yaw_degrees":yaw}
	var station := pinned.merged({"active":true, "mesh_confirmed":true, "world_origin":origin})
	var intake := pinned.merged({"socket_id":"in", "role":"intake", "confirmed":true, "local_position":Vector3(0, 0.5, -1)})
	var output := pinned.merged({"socket_id":"out", "role":"output", "confirmed":true, "local_position":Vector3(0, 0.5, 1)})
	var axis: Vector3 = {0: Vector3.BACK, 90: Vector3.RIGHT, 180: Vector3.FORWARD, 270: Vector3.LEFT}[yaw]
	var route := pinned.merged({"confirmed":true, "gate_state_verified":true, "socket_reach_limit_m":1.0, "load_radius_m":0.625, "min_center_clearance_m":0.65625, "required_residual_m":0.03125})
	var intake_route := route.merged({"socket_id":"in", "role":"intake", "world_anchor":origin - axis * 1.75 + Vector3.UP * 0.5})
	var output_route := route.merged({"socket_id":"out", "role":"output", "world_anchor":origin + axis * 1.75 + Vector3.UP * 0.5})
	return [station, intake, output, intake_route, output_route]

func _valid(records: Array) -> bool:
	return Cooker.binding_is_valid(records[0], records[1], records[2], records[3], records[4])

func _initialize() -> void:
	for yaw: int in [0, 90, 180, 270]:
		_check(_valid(_records(yaw)), "authored end orientation %d" % yaw)
	var baseline := _records(0)
	var negative := [
		[0,"active",false,"inactive station"],
		[0,"mesh_confirmed",false,"unconfirmed mesh"],
		[0,"yaw_degrees",13,"unproven angle"],
		[0,"yaw_degrees",0.0,"noncanonical angle representation"],
		[1,"confirmed",false,"socket unconfirmed"],
		[1,"local_position",Vector3.ZERO,"socket not at authored end"],
		[1,"local_position",Vector3(0, 0.5, 1),"input physically on output end"],
		[2,"socket_id","in","duplicate input output socket"],
		[3,"socket_id","out","input points to output"],
		[3,"station_id","other","different station"],
		[3,"mesh_id","other","different exact asset"],
		[3,"placement_id","other","different seat"],
		[3,"revision_id","other","stale route record"],
		[3,"yaw_degrees",180,"wrong orientation for route"],
		[3,"world_anchor",Vector3(4, 1.5, 7),"side stance on centerline"],
		[3,"world_anchor",Vector3(3, 1.5, 8),"reversed stance"],
		[3,"world_anchor",Vector3(3, 4, 5.25),"vertical reach fails"],
		[3,"min_center_clearance_m",0.65624,"just outside exact loaded residual"],
		[3,"load_radius_m",0,"no loaded envelope"],
		[3,"min_center_clearance_m",INF,"nonfinite measured clearance"],
		[4,"gate_state_verified",false,"output route gate state unknown"],
	]
	for row: Array in negative:
		var candidate: Array = baseline.duplicate(true)
		candidate[row[0]][row[1]] = row[2]
		var before := var_to_bytes(candidate)
		_check(not _valid(candidate) and before == var_to_bytes(candidate), row[3])
	var unknown: Array = baseline.duplicate(true)
	unknown[4] = {}
	_check(not _valid(unknown), "missing output route")
	# Match intentionally across all affected records, so an equality-only guard
	# cannot mask acceptance of an unauthored, noncanonical token.
	for key: String in ["station_id", "mesh_id", "placement_id", "revision_id"]:
		for raw: String in [" \t ", " padded", "padded ", "\t padded \n"]:
			var candidate: Array = baseline.duplicate(true)
			for record: Dictionary in candidate:
				record[key] = raw
			var before := var_to_bytes(candidate)
			_check(not _valid(candidate) and before == var_to_bytes(candidate), "reject matching malformed %s: %s" % [key, var_to_str(raw)])
	for side: int in [1, 2]:
		for raw: String in [" \t ", " end", "end ", "\t end \n"]:
			var sockets: Array = baseline.duplicate(true)
			sockets[side]["socket_id"] = raw
			sockets[side + 2]["socket_id"] = raw
			var before := var_to_bytes(sockets)
			_check(not _valid(sockets) and before == var_to_bytes(sockets), "reject matching malformed socket ID at index %d" % side)
	for index: int in [1, 2, 3, 4]:
		var roles: Array = baseline.duplicate(true)
		roles[index]["role"] = StringName(roles[index]["role"])
		var before := var_to_bytes(roles)
		_check(not _valid(roles) and before == var_to_bytes(roles), "reject plausible but non-String role at index %d" % index)
	var preserved: Array = baseline.duplicate(true)
	for record: Dictionary in preserved:
		record["station_id"] = "within label"
	_check(_valid(preserved), "internal whitespace is not edge padding")
	print("Cooker station interface: %d/%d checks" % [checks - failures, checks])
	quit(1 if failures else 0)
