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
const TRAIL_SAMPLES := 6
const TRAIL_LAG := 0.062
const ARRIVAL_PULSE_SECONDS := 0.42
const MAX_PULSES := 48
const AUTHORITY_ID := "T08-transfer-feedback-v1"
const ASSETS := HavenlineCarryStack.ASSETS
const FEEDBACK_MESHES := {
	"trail": "res://assets/transfer_feedback_v2/transfer_trail_ribbon.obj",
	"arrow": "res://assets/transfer_feedback_v2/transfer_arrow_sigil.obj",
	"pulse": "res://assets/transfer_feedback_v2/transfer_arrival_burst.obj",
}
const FEEDBACK_SHADER := "res://assets/transfer_feedback_v2/transfer_feedback_v2.gdshader"

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
var gather_arrows: MultiMeshInstance3D
var destination_arrows: MultiMeshInstance3D
var gather_pulses: MultiMeshInstance3D
var destination_pulses: MultiMeshInstance3D
var pulses: Array[Dictionary] = []

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
		"trail_geometry": "tangent_oriented_tapered_continuous_segments",
		"arrowheads": true,
		"arrival_pulse_seconds": ARRIVAL_PULSE_SECONDS,
		"trail_colors": {"source_to_actor":"5deaff", "actor_to_destination":"ffb548"},
		"authored_feedback_assets": FEEDBACK_MESHES.duplicate(),
		"feedback_shader": FEEDBACK_SHADER,
		"primitive_feedback_allowed": false,
		"feedback_draw_calls": 6,
		"simulation_authoritative": true,
		"mutates_inventory": false,
		"directions": ["source_to_actor", "actor_to_destination"],
	}

static func valid_point(value: Vector3) -> bool:
	return is_finite(value.x) and is_finite(value.y) and is_finite(value.z)

func _load_feedback_mesh(kind: String) -> Mesh:
	var path := String(FEEDBACK_MESHES.get(kind, ""))
	if path.is_empty() or not ResourceLoader.exists(path):
		push_error("Missing authored T08 feedback mesh: %s" % path)
		return null
	var resource: Variant = load(path)
	if resource is Mesh:
		return resource
	push_error("Authored T08 feedback resource is not a Mesh: %s" % path)
	return null

func _feedback_material(color: Color, role: float) -> ShaderMaterial:
	if not ResourceLoader.exists(FEEDBACK_SHADER):
		push_error("Missing authored T08 feedback shader: %s" % FEEDBACK_SHADER)
		return null
	var shader_resource: Variant = load(FEEDBACK_SHADER)
	if not shader_resource is Shader:
		push_error("T08 feedback shader resource is invalid")
		return null
	var material := ShaderMaterial.new()
	material.shader = shader_resource
	material.set_shader_parameter("tint", color)
	material.set_shader_parameter("role", role)
	material.set_shader_parameter("emission_strength", 2.7)
	return material

func _make_feedback_instances(kind: String, color: Color, capacity: int, role: float) -> MultiMeshInstance3D:
	var mesh := _load_feedback_mesh(kind)
	var material := _feedback_material(color, role)
	if mesh == null or material == null:
		return null
	var instances := MultiMesh.new()
	instances.transform_format = MultiMesh.TRANSFORM_3D
	instances.mesh = mesh
	instances.instance_count = capacity
	instances.visible_instance_count = 0
	var result := MultiMeshInstance3D.new()
	result.multimesh = instances
	result.material_override = material
	result.set_meta("t08_authored_feedback_asset", FEEDBACK_MESHES[kind])
	result.set_meta("t08_custom_feedback_shader", FEEDBACK_SHADER)
	add_child(result)
	return result

func _make_trail(color: Color) -> MultiMeshInstance3D:
	return _make_feedback_instances("trail", color, MAX_FLIGHTS * TRAIL_SAMPLES, 0.0)

func _make_arrows(color: Color) -> MultiMeshInstance3D:
	return _make_feedback_instances("arrow", color, MAX_FLIGHTS, 1.0)

func _make_pulses(color: Color) -> MultiMeshInstance3D:
	return _make_feedback_instances("pulse", color, MAX_PULSES, 2.0)

func _ensure_trails() -> void:
	if not is_instance_valid(gather_trail):
		gather_trail = _make_trail(Color("5deaff"))
	if not is_instance_valid(destination_trail):
		destination_trail = _make_trail(Color("ffb548"))
	if not is_instance_valid(gather_arrows):
		gather_arrows = _make_arrows(Color("5deaff"))
	if not is_instance_valid(destination_arrows):
		destination_arrows = _make_arrows(Color("ffb548"))
	if not is_instance_valid(gather_pulses):
		gather_pulses = _make_pulses(Color("5deaff"))
	if not is_instance_valid(destination_pulses):
		destination_pulses = _make_pulses(Color("ffb548"))

func _eased_position(item: Dictionary, normalized_time: float) -> Vector3:
	var t := clampf(normalized_time, 0.0, 1.0)
	var eased := t * t * (3.0 - 2.0 * t)
	return item.start.lerp(item.finish, eased) + Vector3.UP * sin(t * PI) * ARC_HEIGHT

func _tangent_basis(tangent: Vector3) -> Basis:
	var up := tangent.normalized()
	if up.length_squared() < 0.000001:
		up = Vector3.UP
	var side := Vector3.UP.cross(up)
	if side.length_squared() < 0.000001:
		side = Vector3.RIGHT
	side = side.normalized()
	var forward := side.cross(up).normalized()
	return Basis(side, up, forward)

func _update_trails() -> void:
	_ensure_trails()
	var gather_index := 0
	var destination_index := 0
	var gather_arrow_index := 0
	var destination_arrow_index := 0
	for item in flights:
		var normalized_time := float(item.time) / DURATION_SECONDS
		for sample in TRAIL_SAMPLES:
			var head_t := normalized_time - float(sample) * TRAIL_LAG
			var tail_t := head_t - TRAIL_LAG * 1.12
			var head := _eased_position(item, head_t)
			var tail := _eased_position(item, tail_t)
			var tangent := head - tail
			var length_scale := maxf(0.38, tangent.length() / 0.28)
			var taper := 1.0 - float(sample) * 0.095
			var basis := _tangent_basis(tangent).scaled(Vector3(taper, length_scale, taper))
			var transform := Transform3D(basis, tail.lerp(head, 0.5))
			if item.direction == "source_to_actor":
				gather_trail.multimesh.set_instance_transform(gather_index, transform)
				gather_index += 1
			else:
				destination_trail.multimesh.set_instance_transform(destination_index, transform)
				destination_index += 1
		var arrow_head := _eased_position(item, normalized_time)
		var arrow_tail := _eased_position(item, normalized_time - 0.025)
		var arrow_transform := Transform3D(_tangent_basis(arrow_head - arrow_tail), arrow_head)
		if item.direction == "source_to_actor":
			gather_arrows.multimesh.set_instance_transform(gather_arrow_index, arrow_transform)
			gather_arrow_index += 1
		else:
			destination_arrows.multimesh.set_instance_transform(destination_arrow_index, arrow_transform)
			destination_arrow_index += 1
	gather_trail.multimesh.visible_instance_count = gather_index
	destination_trail.multimesh.visible_instance_count = destination_index
	gather_arrows.multimesh.visible_instance_count = gather_arrow_index
	destination_arrows.multimesh.visible_instance_count = destination_arrow_index

func _update_pulses() -> void:
	_ensure_trails()
	var gather_index := 0
	var destination_index := 0
	for pulse in pulses:
		var progress := clampf(float(pulse.time) / ARRIVAL_PULSE_SECONDS, 0.0, 1.0)
		var scale := 0.75 + progress * 2.35
		var transform := Transform3D(Basis.IDENTITY.scaled(Vector3.ONE * scale), pulse.position)
		if pulse.direction == "source_to_actor":
			gather_pulses.multimesh.set_instance_transform(gather_index, transform)
			gather_index += 1
		else:
			destination_pulses.multimesh.set_instance_transform(destination_index, transform)
			destination_index += 1
	gather_pulses.multimesh.visible_instance_count = gather_index
	destination_pulses.multimesh.visible_instance_count = destination_index

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
	# Age pulses that existed at frame start. A pulse created by a large test or
	# catch-up step must still receive one rendered frame at its destination.
	for index in range(pulses.size() - 1, -1, -1):
		var pulse: Dictionary = pulses[index]
		pulse.time = float(pulse.time) + dt
		if float(pulse.time) >= ARRIVAL_PULSE_SECONDS:
			pulses.remove_at(index)
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
			if pulses.size() >= MAX_PULSES:
				pulses.pop_front()
			pulses.append({"position":item.finish, "time":0.0, "direction":item.direction,
				"destination_id":item.destination_id})
			item.node.visible = false
			pools[item.kind].append(item.node)
			flights.remove_at(index)
			completed_count += 1
	_update_trails()
	_update_pulses()

func descriptor() -> Dictionary:
	return {
		"authority_id": AUTHORITY_ID,
		"active_flights": flights.size(),
		"maximum_flights": MAX_FLIGHTS,
		"accepted_receipts": accepted_count,
		"rejected_receipts": rejected_count,
		"completed_receipts": completed_count,
		"active_arrival_pulses": pulses.size(),
		"remembered_receipts": receipts.size(),
		"mutates_inventory": false,
		"trail_instances": {
			"source_to_actor": gather_trail.multimesh.visible_instance_count if is_instance_valid(gather_trail) else 0,
			"actor_to_destination": destination_trail.multimesh.visible_instance_count if is_instance_valid(destination_trail) else 0,
		},
		"arrow_instances": {
			"source_to_actor": gather_arrows.multimesh.visible_instance_count if is_instance_valid(gather_arrows) else 0,
			"actor_to_destination": destination_arrows.multimesh.visible_instance_count if is_instance_valid(destination_arrows) else 0,
		},
		"arrival_pulse_instances": {
			"source_to_actor": gather_pulses.multimesh.visible_instance_count if is_instance_valid(gather_pulses) else 0,
			"actor_to_destination": destination_pulses.multimesh.visible_instance_count if is_instance_valid(destination_pulses) else 0,
		},
		"arrival_pulses": pulses.map(func(pulse): return {
			"destination_id": pulse.destination_id,
			"direction": pulse.direction,
			"normalized_age": clampf(float(pulse.time) / ARRIVAL_PULSE_SECONDS, 0.0, 1.0),
		}),
		"flights": flights.map(func(item): return {
			"kind": item.kind, "receipt_id": item.receipt_id, "direction": item.direction,
			"actor_id": item.actor_id, "destination_id": item.destination_id,
		}),
	}
