extends "res://tests/hvn_latch_two_cycle_route.gd"
## New detached test entry: one ordinary South occupancy episode only.
var episode_ok := false

func ordinary_route(primary: String) -> void:
	await super.ordinary_route(primary)
	if route_failed or capture_failed or failures != 0 or checks != 57 or route_checks != 23:
		return
	print("L1_LATCH_ROUTE_OK write inherited=57 extra=23") # exact completed prefix only; variant result checked separately.
	var initial := FileAccess.get_file_as_bytes(primary)
	var ledger: Dictionary = game.ledger.snapshot()
	var south = game.gates[0]
	var east = game.gates[1]
	if not await travel(game.point([0.,6.])) or game.nearest_gate!=south or south.target_open or south.angle!=0 or not south.sweep_clear(game.actor.global_position,float(game.layout.actor_radius)):
		return
	if not await _toggle_at_stance(0,true,3):
		return
	# _toggle_at_stance adds two to route_checks. Keep exact parent counters and
	# use a separate completion proof below; do not relabel the historical 23.
	if not await _hold_nudge(south,.62,.59,.65,100,"approach"):
		return
	if not _hold_pose(south,.59,.65) or game.nearest_gate!=south or not south.sweep_clear(game.actor.global_position,float(game.layout.actor_radius)):
		return
	print("SOUTH_HOLD_BEGIN ",JSON.stringify({"tick":tick_count,"physics":Engine.get_physics_frames(),"angle":south.angle},"",true,true))
	press(KEY_E)
	await tick(8)
	var pre := float(south.angle)
	if south.target_open or south.holding_for_occupancy or absf(pre-(PI*.5-8.0*2.3/60.0))>.00001:
		return
	if not await _hold_nudge(south,.44,.425,.455,18,"enter"):
		return
	if not _hold_pose(south,.425,.455) or south.sweep_clear(game.actor.global_position,float(game.layout.actor_radius)) or not south.holding_for_occupancy or south.target_open or not (south.angle>0 and south.angle<pre):
		return
	var held := float(south.angle)
	for i in range(3):
		await tick(1)
		if not _hold_pose(south,.425,.455) or not south.holding_for_occupancy or south.target_open or south.angle!=held:
			return
		_hold_print(south,"held-close")
	if game.nearest_gate!=south or not south.interaction_in_range(game.actor.global_position):
		return
	press(KEY_E)
	for i in range(3):
		await tick(1)
		if not _hold_pose(south,.425,.455) or not south.holding_for_occupancy or not south.target_open or south.angle!=held:
			return
		_hold_print(south,"held-reopen")
	if not await _hold_nudge(south,.62,.59,.65,20,"retreat"):
		return
	await tick(52)
	if not _hold_pose(south,.59,.65) or not south.target_open or south.holding_for_occupancy or not is_equal_approx(south.angle,PI*.5) or east.target_open or east.angle!=0 or not east.active or not south.active:
		return
	if ledger!=game.ledger.snapshot() or initial.is_empty() or initial!=FileAccess.get_file_as_bytes(primary) or FileAccess.file_exists(profile.path_join(game.save.STAGING)) or capture_failed:
		return
	_hold_print(south,"open-settled")
	episode_ok=true

func _hold_nudge(gate, goal: float, lo: float, hi: float, limit: int, stage: String) -> bool:
	gesture += 1
	send_touch(true)
	var accepted := false
	for i in range(limit):
		var local: Vector3 = gate.to_local(game.actor.global_position)
		if _hold_pose(gate,lo,hi):
			accepted=true
			break
		# No pose or velocity injection; use the same ordinary drag path as travel.
		var along: Vector3 = gate.global_basis.z.normalized() * signf(goal-local.z)
		var screen := along.rotated(Vector3.UP,-atan2(7.,11.))
		var ev := InputEventScreenDrag.new()
		ev.index=gesture
		ev.position=CENTER+Vector2(screen.x,screen.z)*82.*.20
		game._input(ev)
		await tick(1)
		var after: Vector3 = gate.to_local(game.actor.global_position)
		if not _hold_pose(gate,.41,2.05) or absf(after.z-local.z)>.014 or capture_failed:
			break
		_hold_print(gate,stage)
	send_touch(false)
	return accepted

func _hold_pose(gate, low: float, high: float) -> bool:
	var local: Vector3 = gate.to_local(game.actor.global_position)
	if not game.bound or not game.actor.is_on_floor() or absf(local.x)>.03 or local.z<low or local.z>high:
		return false
	for i in game.actor.get_slide_collision_count():
		var hit = game.actor.get_slide_collision(i).get_collider()
		if hit is Node and gate.is_ancestor_of(hit):
			return false
	return true

func _hold_print(gate, mode: String) -> void:
	var at: Vector3 = gate.to_local(game.actor.global_position)
	print("SOUTH_HOLD_ROW ",JSON.stringify({"mode":mode,"tick":tick_count,"physics":Engine.get_physics_frames(),"gate_id":String(gate.gate_id),"instance_id":gate.get_instance_id(),"z_m":at.z,"x_m":at.x,"angle":gate.angle,"target_open":gate.target_open,"held":gate.holding_for_occupancy,"grounded":true,"leaf_contact":false},"",true,true))

func finish(phase: String) -> void:
	if phase=="write":
		if not episode_ok or route_checks!=25:
			print("SOUTH_HOLD_REJECT incomplete safe ordinary South episode")
			quit(7)
			return
		print("SOUTH_HOLD_OK one-reopened-without-close")
		print("SOUTH_HOLD_PARENT_CHECKS writer_baseline=23 added_reopen=2 inherited=57")
		quit(0)
		return
	await super.finish(phase)
