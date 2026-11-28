extends Node3D
## Fixture logic: not production inventory, timing, or spatial policy.
signal arrived(ticket: String, ordinal: int, marker_us: int, observed_us: int, local_position: Vector3)
signal completed(ticket: String, marker_us: int, observed_us: int)

const FLIGHT_US := 285000
const STEP_US := 11500
const MAX_FIXTURE_UNITS := 52
const MAX_IN_FLIGHT := 25
var _epoch := 0
var _watermark := 0
var _seen := {}
var _receiver := ""
var _binding_material := ""
var _ticket := ""
var _clock_us := 0
var _dispatching := false
var _pieces: Array[Dictionary] = []
var active_peak := 0

func _cancel() -> void:
	for piece in _pieces:
		remove_child(piece.node)
		piece.node.queue_free()
	_pieces.clear()
	_ticket = ""

## Only a strictly newer trusted binding can replace the previous visual route.
## Its watermark must cover known commits, including on scene/view reattach.
func bind(epoch: int, committed_floor: int, receiver: String, material: String) -> bool:
	if epoch <= _epoch or committed_floor < _watermark or receiver.is_empty() or material.is_empty():
		return false
	_cancel()
	_epoch = epoch
	_watermark = committed_floor
	_receiver = receiver
	_binding_material = material
	return true

## Evidence payload represents a trusted, already committed caller (fixture only).
## Exact matcher cannot authenticate publication or authorize a transaction.
func admit(cue: Array, committed_receipts: Dictionary, epoch: int, commit_seq: int, sources: Array[Vector3], targets: Array[Vector3]) -> bool:
	if _dispatching or not _ticket.is_empty() or epoch != _epoch or commit_seq <= _watermark or cue.size() != 4:
		return false
	if typeof(cue[0]) != TYPE_STRING or cue[0].is_empty() or _seen.has(cue[0]):
		return false
	if typeof(cue[1]) != TYPE_STRING or typeof(cue[2]) != TYPE_STRING or cue[1] != _receiver or cue[2] != _binding_material:
		return false
	if typeof(cue[3]) != TYPE_INT or cue[3] <= 0 or cue[3] > MAX_FIXTURE_UNITS or sources.size() != cue[3] or targets.size() != cue[3]:
		return false
	var receipt: Variant = committed_receipts.get(cue[0])
	if typeof(receipt) != TYPE_ARRAY or receipt.size() != 3 or typeof(receipt[0]) != TYPE_STRING or typeof(receipt[1]) != TYPE_STRING or typeof(receipt[2]) != TYPE_INT or receipt != cue.slice(1):
		return false
	for i in range(cue[3]):
		if not sources[i].is_finite() or not targets[i].is_finite() or sources[i].is_equal_approx(targets[i]):
			return false
	_cancel()
	_ticket = cue[0]
	_seen[_ticket] = true
	_watermark = commit_seq
	_clock_us = 0
	active_peak = 0
	for i in range(cue[3]):
		var start: Vector3 = sources[i]
		var finish: Vector3 = targets[i]
		var node := Node3D.new()
		node.name = "Piece_%02d" % i
		add_child(node)
		node.position = start
		_pieces.append({"node": node, "start": start, "finish": finish, "done": false})
	return true

## Receives absolute elapsed microseconds for the admitted ticket. No delta drift.
## Completion follows a snapped endpoint, not an inventory write or a UI counter.
func sample_elapsed(for_ticket: String, epoch_id: int, elapsed_us: int) -> bool:
	if _dispatching or _ticket.is_empty() or for_ticket != _ticket or epoch_id != _epoch or elapsed_us < _clock_us:
		return false
	var end_us := FLIGHT_US + (_pieces.size() - 1) * STEP_US
	_clock_us = mini(elapsed_us, end_us)
	var airborne := 0
	var ticket := _ticket
	var epoch := _epoch
	# Stage state first. Signal callbacks may replace this epoch during dispatch.
	var events: Array[Dictionary] = []
	for i in range(_pieces.size()):
		var p := _pieces[i]
		var local_us := _clock_us - i * STEP_US
		if local_us < 0 or p.done:
			continue
		var node: Node3D = p.node
		if local_us >= FLIGHT_US:
			node.position = p.finish
			p.done = true
			events.append({"i": i, "due": i * STEP_US + FLIGHT_US, "observed": elapsed_us, "position": node.position})
		else:
			var alpha := float(local_us) / FLIGHT_US
			# The arch height is dimensionless relative to each segment. No asset geometry.
			var lift: float = p.start.distance_to(p.finish) * 0.2
			node.position = p.start.lerp(p.finish, alpha) + Vector3.UP * (4.0 * lift * alpha * (1.0 - alpha))
			airborne += 1
	active_peak = maxi(active_peak, airborne)
	if _clock_us == end_us:
		_ticket = ""
	_dispatching = true
	for event in events:
		if _epoch != epoch:
			_dispatching = false
			return true
		arrived.emit(ticket, event.i, event.due, event.observed, event.position)
	if _epoch == epoch and _ticket.is_empty() and _clock_us == end_us:
		completed.emit(ticket, end_us, elapsed_us)
	_dispatching = false
	return true
