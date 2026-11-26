extends RefCounted
## Detached helper, not loaded by the game. Observe the last completed physics step.
var _epoch := ""
var _phase := ""
var _instances := {}
var _offset := 0
var _previous := {}
var _seeded := false
var _broken := false

func read_after_inherited_tick(game, route_tick: int, phase: String) -> bool:
	if _broken or phase not in ["writer","cold"] or not is_instance_valid(game) or game.gates.size() != 2 or Engine.physics_ticks_per_second != 60:
		return _reject("scope or fixed physics rate")
	var raw_engine := Engine.get_physics_frames()
	if not _seeded:
		_phase = phase
		_offset = raw_engine - route_tick
		# Local process and scene identity, not an owner/profile/save identifier.
		_epoch = "%d:%d:%s" % [OS.get_process_id(),game.get_instance_id(),phase]
		for gate in game.gates:
			if not is_instance_valid(gate) or String(gate.gate_id) not in ["gate-east","gate-south"] or _instances.has(String(gate.gate_id)):
				return _reject("invalid original gate nodes")
			_instances[String(gate.gate_id)] = gate.get_instance_id()
		if _instances.size()!=2 or _instances["gate-east"]==_instances["gate-south"]:
			return _reject("gate identity collision")
		print("L1_LATCH_BIND ",JSON.stringify({"scene_epoch":_epoch,"phase":_phase,"instances":_instances,"phase_offset":_offset}))
	elif phase!=_phase or _epoch!="%d:%d:%s" % [OS.get_process_id(),game.get_instance_id(),phase] or raw_engine-route_tick!=_offset:
		return _reject("epoch or clock phase changed")
	var now := {}
	var receipt: Variant = null
	if not game.ledger.receipt.is_empty():
		receipt = game.ledger.receipt.duplicate(true)
	for gate in game.gates:
		if not is_instance_valid(gate):
			return _reject("missing gate")
		var id := String(gate.gate_id)
		if not _instances.has(id) or now.has(id) or _instances[id]!=gate.get_instance_id():
			return _reject("gate replaced or relabeled")
		var frame := {"route_tick":route_tick,"engine_physics_counter":raw_engine,"scene_epoch":_epoch,"gate_id":id,
			"instance_id":gate.get_instance_id(),"active":bool(gate.active),"target_open":bool(gate.target_open),
			"held":bool(gate.holding_for_occupancy),"angle_rad":float(gate.angle),"receipt":receipt,"restored":phase=="cold"}
		if not _seeded:
			if frame.angle_rad!=0 or frame.target_open or frame.held or (phase=="writer" and (frame.active or receipt!=null)) or (phase=="cold" and (not frame.active or receipt==null)):
				return _reject("wrong initial writer or cold seed")
		else:
			var before: Dictionary = _previous[id]
			if route_tick!=before.route_tick+1 or raw_engine!=before.engine_physics_counter+1:
				return _reject("non-adjacent source clocks")
		now[id] = frame
	for id in ["gate-east","gate-south"]:
		if _seeded:
			print("L1_LATCH_PAIR ",JSON.stringify({"schema":"havenline.l1.gate-latch-adjacent-witness/v2","phase":phase,
				"readback_hook":"last-completed-physics-before-next","scene_epoch":_epoch,"gate_id":id,
				"instance_id":_instances[id],"previous":_previous[id],"current":now[id]}, "", true, true))
		else:
			print("L1_LATCH_SEED ",JSON.stringify(now[id]))
	_previous = now
	_seeded = true
	return true

func _reject(reason: String) -> bool:
	_broken = true
	print("L1_LATCH_OBSERVER_REJECT ",reason)
	return false
