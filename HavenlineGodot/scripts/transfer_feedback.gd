class_name HavenlineTransferFeedback
extends Node3D

## T08 presentation-only resource receipts. Only committed simulation events may
## start a flight; replayed receipt IDs and malformed routes fail closed.

const KINDS := ["wood", "stone", "metal", "fuel"]
const MAX_FLIGHTS := 48
const RECEIPT_WINDOW := 256
const DURATION_SECONDS := 0.72
const FLIGHT_SCALE_MULTIPLIER := 2.3
const ARC_HEIGHT := 1.2
const TRAIL_SAMPLES := 3
const TRAIL_LAG := 0.085
const AUTHORITY_ID := "T08-transfer-feedback-v1"
const ASSETS := HavenlineCarryStack.ASSETS

var loader: Callable
var flights: Array[Dictionary] = []
var pools: Dictionary = {"wood": [], "stone": [], "metal": [], "fuel": []}
var receipts: Dictionary = {}
var receipt_order: Array[String] = []
var accepted_count := 0
var rejected_count := 0
var completed_count := 0
var gather_trail: MultiMeshInstance3D
var destination_trail: MultiMeshInstance3D

static func contract() -> Dictionary:
	return {
		"authority_id": AUTHORITY_ID,
		"resource_kinds": KINDS.duplicate(),
		"maximum_flights": MAX_FLIGHTS,
		"receipt_window": RECEIPT_WINDOW,
		"duration_seconds": DURATION_SECONDS,
		"flight_scale_multiplier": FLIGHT_SCALE_MULTIPLIER,
		"arc_height": ARC_HEIGHT,
		"trail_samples": TRAIL_SAMPLES,
		"trail_colors": {"source_to_actor":"5deaff", "actor_to_destination":"ffb548"},
		"trail_draw_calls": 2,
		"simulation_authoritative": true,
		"mutates_inventory": false,
		"directions": ["source_to_actor", "actor_to_destination"],
	}

static func valid_point(value: Vector3) -> bool:
	return is_finite(value.x) and is_finite(value.y) and is_finite(value.z)

func _make_trail(color: Color) -> MultiMeshInstance3D:
	var mesh := CapsuleMesh.new()
	mesh.radius = 0.085
	mesh.height = 0.17
	mesh.radial_segments = 8
	mesh.rings = 4
	var material := StandardMaterial3D.new()
	material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	material.albedo_color = color
	material.emission_enabled = true
	material.emission = color
	material.emission_energy_multiplier = 2.4
	material.no_depth_test = true
	mesh.material = material
	var instances := MultiMesh.new()
	instances.transform_format = MultiMesh.TRANSFORM_3D
	instances.mesh = mesh
	instances.instance_count = MAX_FLIGHTS * TRAIL_SAMPLES
	instances.visible_instance_count = 0
	var result := MultiMeshInstance3D.new()
	result.multimesh = instances
	add_child(result)
	return result

func _ensure_trails() -> void:
	if not is_instance_valid(gather_trail):
		gather_trail = _make_trail(Color("5deaff"))
	if not is_instance_valid(destination_trail):
		destination_trail = _make_trail(Color("ffb548"))

func _eased_position(item: Dictionary, normalized_time: float) -> Vector3:
	var t := clampf(normalized_time, 0.0, 1.0)
	var eased := t * t * (3.0 - 2.0 * t)
	return item.start.lerp(item.finish, eased) + Vector3.UP * sin(t * PI) * ARC_HEIGHT

func _update_trails() -> void:
	_ensure_trails()
	var gather_index := 0
	var destination_index := 0
	for item in flights:
		var normalized_time := float(item.time) / DURATION_SECONDS
		for sample in TRAIL_SAMPLES:
			var position := _eased_position(item, normalized_time - float(sample + 1) * TRAIL_LAG)
			var scale := 1.0 - float(sample) * 0.22
			var transform := Transform3D(Basis.IDENTITY.scaled(Vector3.ONE * scale), position)
			if item.direction == "source_to_actor":
				gather_trail.multimesh.set_instance_transform(gather_index, transform)
				gather_index += 1
			else:
				destination_trail.multimesh.set_instance_transform(destination_index, transform)
				destination_index += 1
	gather_trail.multimesh.visible_instance_count = gather_index
	destination_trail.multimesh.visible_instance_count = destination_index

func _instantiate_piece(kind: String) -> Node3D:
	var path := String(ASSETS.get(kind, ""))
	if not path.is_empty() and ResourceLoader.exists(path):
		var packed: Variant = load(path)
		if packed is PackedScene:
			var node: Variant = packed.instantiate()
			if node is Node3D:
				node.set_meta("t08_authored_asset", path)
				add_child(node)
				return node
	if loader.is_valid():
		var fallback: Variant = loader.call(kind, self)
		if fallback is Node3D:
			return fallback
	return null

func _remember_receipt(receipt_id: String) -> void:
	receipts[receipt_id] = true
	receipt_order.append(receipt_id)
	while receipt_order.size() > RECEIPT_WINDOW:
		receipts.erase(receipt_order.pop_front())

func transfer(kind: String, start: Vector3, finish: Vector3, receipt_id := "",
		direction := "source_to_actor", actor_id := -1, destination_id := "") -> bool:
	if kind not in KINDS or not valid_point(start) or not valid_point(finish):
		rejected_count += 1
		return false
	if direction not in ["source_to_actor", "actor_to_destination"]:
		rejected_count += 1
		return false
	if start.distance_squared_to(finish) <= 0.000001 or flights.size() >= MAX_FLIGHTS:
		rejected_count += 1
		return false
	if receipt_id.is_empty():
		receipt_id = "local:%d" % (accepted_count + rejected_count + completed_count)
	if receipts.has(receipt_id):
		rejected_count += 1
		return false
	var node: Node3D = pools[kind].pop_back() if not pools[kind].is_empty() else _instantiate_piece(kind)
	if node == null:
		rejected_count += 1
		return false
	_remember_receipt(receipt_id)
	node.visible = true
	node.scale = Vector3.ONE * float(HavenlineCarryStack.PIECE_SCALE[kind]) * FLIGHT_SCALE_MULTIPLIER
	node.position = start
	node.set_meta("t08_receipt_id", receipt_id)
	flights.append({
		"node": node, "kind": kind, "start": start, "finish": finish, "time": 0.0,
		"receipt_id": receipt_id, "direction": direction, "actor_id": actor_id,
		"destination_id": destination_id,
	})
	accepted_count += 1
	_update_trails()
	return true

func _process(dt: float) -> void:
	if dt <= 0.0 or not is_finite(dt):
		return
	for index in range(flights.size() - 1, -1, -1):
		var item: Dictionary = flights[index]
		item.time += dt
		var t := minf(1.0, float(item.time) / DURATION_SECONDS)
		# Smoothstep separation and a taller arc keep origin, travel direction,
		# and destination readable at the approved gameplay camera scale.
		item.node.position = _eased_position(item, t)
		item.node.rotation.y += dt * 3.2
		if t >= 1.0:
			item.node.position = item.finish
			item.node.visible = false
			pools[item.kind].append(item.node)
			flights.remove_at(index)
			completed_count += 1
	_update_trails()

func descriptor() -> Dictionary:
	return {
		"authority_id": AUTHORITY_ID,
		"active_flights": flights.size(),
		"maximum_flights": MAX_FLIGHTS,
		"accepted_receipts": accepted_count,
		"rejected_receipts": rejected_count,
		"completed_receipts": completed_count,
		"remembered_receipts": receipts.size(),
		"mutates_inventory": false,
		"trail_instances": {
			"source_to_actor": gather_trail.multimesh.visible_instance_count if is_instance_valid(gather_trail) else 0,
			"actor_to_destination": destination_trail.multimesh.visible_instance_count if is_instance_valid(destination_trail) else 0,
		},
		"flights": flights.map(func(item): return {
			"kind": item.kind, "receipt_id": item.receipt_id, "direction": item.direction,
			"actor_id": item.actor_id, "destination_id": item.destination_id,
		}),
	}
