extends Node3D
## Detached fixture only. In-process ownership, not a GDScript sandbox.
signal arrived(ticket: String, ordinal: int, marker_us: int, observed_us: int, local_position: Vector3)
signal completed(ticket: String, marker_us: int, observed_us: int)

const Planner = preload("res://planner_upstream.gd")
const RECEIVER := "receiver_test"
const MATERIAL := "wood"
const OTHER := "red_test_only"
const FLIGHT_US := 285000
const STEP_US := 11500
const MAX_FIXTURE_UNITS := 52
const MAX_IN_FLIGHT := 25

var _ledger := {"carry":{MATERIAL:52,OTHER:7}, "receivers":{RECEIVER:{MATERIAL:0}}, "receipts":{}}
var _policy := {RECEIVER:{"enabled":true,"limits":{MATERIAL:52}}}
var _committed_seq := 0
var _epoch := 1
var _pending: Array[Dictionary] = []
var _active := {}
var _last_elapsed_us := 0
var _dispatching := false
var _visual_mutation := false
var _ready_done := false
var _visual: Node3D
var _other_visual: Node3D
var _peak := 0

func _ready() -> void:
	_visual = Node3D.new()
	_visual.name = "FlightPoints_NoRender"
	add_child(_visual)
	_other_visual = Node3D.new()
	_other_visual.position = Vector3(-2, 1, -1)
	add_child(_other_visual)
	for i in range(7):
		var held := Node3D.new()
		_other_visual.add_child(held)
		held.position.y = i * .035
	_ready_done = true

func state_snapshot() -> Dictionary:
	return {"ledger":_ledger.duplicate(true),"sequence":_committed_seq,"epoch":_epoch}

func presentation_snapshot() -> Dictionary:
	var copies := []
	for node in _visual.get_children():
		copies.append([String(node.name), node.position])
	return {
		"active":_active.get("ticket",""),
		"points":copies,
		"other":_other_visual.get_children().map(func(node): return node.transform),
		"peak":_peak,
	}

## Intended write boundary: strict INTENT, not externally supplied proof.
## Unknown keys (including a facsimile of receipt, seq, or cue) fail closed.
func submit_intent(expected_epoch: int, intent: Dictionary) -> bool:
	if not _ready_done or _visual_mutation or _dispatching or expected_epoch != _epoch or intent.size() != 4:
		return false
	for key in ["receiver","material","ticket","units"]:
		if not intent.has(key):
			return false
	if intent.receiver != RECEIVER or intent.material != MATERIAL:
		return false
	var plan: Dictionary = Planner.plan_transfer(_ledger, [MATERIAL,OTHER], _policy, RECEIVER, intent)
	if plan.is_empty():
		return false
	# Single-threaded commit point; no callbacks or presenter invocations happen before it.
	# Accepted accounting is not contingent on any future fill or animation.
	_ledger = plan.next_state
	_committed_seq += 1
	var cue: Array = plan.cue_after_commit
	_pending.append({"ticket":cue[0], "units":cue[3], "seq":_committed_seq, "epoch":_epoch})
	_open_next_committed()
	return true

## Explicit reattach drops transient presentations, never business receipts.
## Floor/epoch are computed by the owner, not accepted from the caller.
func reattach_view(expected_epoch: int) -> bool:
	if not _ready_done or _visual_mutation or expected_epoch != _epoch:
		return false
	_epoch += 1
	_pending.clear()
	_active.clear()
	_last_elapsed_us = 0
	_peak = 0
	_visual_mutation = true
	_clear_visual()
	_visual_mutation = false
	return true

func _clear_visual() -> void:
	for node in _visual.get_children():
		_visual.remove_child(node)
		node.queue_free()

func _open_next_committed() -> void:
	if _visual_mutation or _dispatching or not _active.is_empty() or _pending.is_empty():
		return
	var entry: Dictionary = _pending.pop_front()
	assert(entry.epoch == _epoch and entry.seq <= _committed_seq)
	assert(_ledger.receipts[entry.ticket] == [RECEIVER,MATERIAL,entry.units])
	assert(0 < entry.units and entry.units <= MAX_FIXTURE_UNITS)
	_visual_mutation = true
	_clear_visual()
	var pieces := []
	for i in range(entry.units):
		var node := Node3D.new()
		node.name = "Piece_%02d" % i
		_visual.add_child(node)
		var start := Vector3(-2.0, 1.0 + (51-i)*.035, 0.0)
		var finish := Vector3(2.0 + (i%8)*.035, (i/8)*.035, 0.0)
		node.position = start
		pieces.append({"node":node, "start":start, "finish":finish, "done":false})
	_active = {"ticket":entry.ticket,"pieces":pieces}
	_last_elapsed_us = 0
	_peak = 0
	_visual_mutation = false

## Addressed clock advance. Injected time, not a frame or load benchmark.
func sample_elapsed(ticket: String, expected_epoch: int, elapsed_us: int) -> bool:
	if _visual_mutation or _dispatching or _active.is_empty() or ticket != _active.ticket or expected_epoch != _epoch or elapsed_us < _last_elapsed_us:
		return false
	_last_elapsed_us = elapsed_us
	var pieces: Array = _active.pieces
	var end_us: int = FLIGHT_US + (pieces.size()-1) * STEP_US
	var clock_us := mini(elapsed_us,end_us)
	var events := []
	var in_flight := 0
	for i in range(pieces.size()):
		var piece: Dictionary = pieces[i]
		var local_us := clock_us - i*STEP_US
		if local_us < 0 or piece.done:
			continue
		var node: Node3D = piece.node
		if local_us >= FLIGHT_US:
			node.position = piece.finish
			piece.done = true
			events.append([i,FLIGHT_US+i*STEP_US,node.position])
		else:
			var progress := float(local_us)/FLIGHT_US
			var lift: float = piece.start.distance_to(piece.finish)*.2
			node.position = piece.start.lerp(piece.finish,progress) + Vector3.UP*(4.0*lift*progress*(1.0-progress))
			in_flight += 1
	_peak = maxi(_peak,in_flight)
	_dispatching = true
	for event in events:
		if _epoch != expected_epoch:
			break
		arrived.emit(ticket,event[0],event[1],elapsed_us,event[2])
	if _epoch == expected_epoch and clock_us == end_us:
		_active.clear()
		completed.emit(ticket,end_us,elapsed_us)
	_dispatching = false
	_open_next_committed()
	return true
