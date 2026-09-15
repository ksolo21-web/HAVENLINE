class_name HavenlineTransferFeedback
extends Node3D

## T08 presentation-only resource receipts. Only committed simulation events may
## start a flight; replayed receipt IDs and malformed routes fail closed.

const KINDS := ["wood", "stone", "metal", "fuel"]
const MAX_FLIGHTS := 48
const RECEIPT_WINDOW := 256
const DURATION_SECONDS := 0.72
const FLIGHT_SCALE_MULTIPLIER := 1.75
const ARC_HEIGHT := 1.05
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

static func contract() -> Dictionary:
	return {
		"authority_id": AUTHORITY_ID,
		"resource_kinds": KINDS.duplicate(),
		"maximum_flights": MAX_FLIGHTS,
		"receipt_window": RECEIPT_WINDOW,
		"duration_seconds": DURATION_SECONDS,
		"flight_scale_multiplier": FLIGHT_SCALE_MULTIPLIER,
		"arc_height": ARC_HEIGHT,
		"simulation_authoritative": true,
		"mutates_inventory": false,
		"directions": ["source_to_actor", "actor_to_destination"],
	}

static func valid_point(value: Vector3) -> bool:
	return is_finite(value.x) and is_finite(value.y) and is_finite(value.z)

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
		var eased := t * t * (3.0 - 2.0 * t)
		item.node.position = item.start.lerp(item.finish, eased) + Vector3.UP * sin(t * PI) * ARC_HEIGHT
		item.node.rotation.y += dt * 3.2
		if t >= 1.0:
			item.node.position = item.finish
			item.node.visible = false
			pools[item.kind].append(item.node)
			flights.remove_at(index)
			completed_count += 1

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
		"flights": flights.map(func(item): return {
			"kind": item.kind, "receipt_id": item.receipt_id, "direction": item.direction,
			"actor_id": item.actor_id, "destination_id": item.destination_id,
		}),
	}
