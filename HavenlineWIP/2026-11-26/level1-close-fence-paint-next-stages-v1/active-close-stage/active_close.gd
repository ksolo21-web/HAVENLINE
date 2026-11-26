extends "res://tests/hvn_l1_combined_draw.gd"
## Disconnected witness only. Never assigns gates or actor position.
var close_count := 0
var close_failed := 0
var close_pending := 0
var close_seen: Array[String] = []
var closing_index := -1
var max_previous_angle := 0.0
var moves_for_current := 0
var close_begin_tick := -1

func close_check(condition: bool, note: String) -> bool:
	close_count += 1
	if not condition:
		close_failed += 1
	print("%s %s tick=%d" % ["CLOSE_ASSERT_OK" if condition else "DRAW_REJECT CLOSE_ASSERT",note,tick_count])
	return condition

func ordinary_route(primary: String) -> void:
	await super.ordinary_route(primary)
	if failures != 0:
		return
	# Wait for final original writer proof if it is armed. No new inputs until
	# original 67-route writer checkpoints and opening angles are settled.
	if armed > 0:
		await RenderingServer.frame_post_draw
		if armed>0:
			await process_frame
	if not close_check(armed==0 and draw_failures==0 and drawn==WRITER and moving_frames==[41,41],"original working opening proof frozen before close inputs"):
		return
	print("CLOSE_INHERITED_MOTION_COUNTS ",JSON.stringify(moving_frames))
	var before := FileAccess.get_file_as_bytes(primary)
	var state: Dictionary = game.ledger.snapshot()
	if not close_check(not before.is_empty() and state.version==2 and state.stock=={"wood":1} and state.receipt==RECEIPT,"exact earned state before first close"):
		return
	var passed: bool = await travel(game.point([0.,2.]))
	if not close_check(passed and await travel(game.point([2.,1.9])) and await travel(game.point([3.,0.])),"legal inner East input approach via open South"):
		return
	if not await _one_close(1,[3.,0.],[7.,0.],false):
		return
	passed = await travel(game.point([3.,0.]))
	if not close_check(passed and await travel(game.point([2.,1.9])) and await travel(game.point([0.,2.])) and await travel(game.point([0.,6.])),"legal outside South input approach after East closes"):
		return
	if not await _one_close(0,[0.,6.],[0.,2.],true):
		return
	close_check(game.ledger.snapshot()==state and FileAccess.get_file_as_bytes(primary)==before and not FileAccess.file_exists(profile.path_join(game.save.STAGING)),"closing and subsequent blocked probes leave exact v2 bytes unchanged")

func _one_close(i: int, start: Array, opposite: Array, from_outside: bool) -> bool:
	var gate = game.gates[i]
	var tag := String(gate.gate_id)
	if not close_check(gate.target_open and is_equal_approx(gate.angle,PI*.5) and game.nearest_gate==gate and gate.interaction_in_range(game.actor.global_position) and gate.sweep_clear(game.actor.global_position,float(game.layout.actor_radius)),
			tag+" real addressable safe opening-side stance"):
		return false
	closing_index=i
	max_previous_angle=float(gate.angle)
	moves_for_current=0
	close_begin_tick=tick_count
	press(KEY_E)
	await tick(52)
	closing_index=-1
	var safe_plate := gate_and_light(tag+"-settled")
	if not close_check(not gate.target_open and is_zero_approx(gate.angle) and moves_for_current==41 and not safe_plate.is_empty(),
			tag+" active closing reaches zero in 41 original moving ticks"):
		return false
	var reached: bool = await travel(game.point(opposite),110)
	var foot: Vector3 = gate.to_local(game.actor.global_position)
	var signed_z := foot.z if from_outside else -foot.z
	var anchor_foot: Vector3 = gate.to_local(game.point(start))
	if not close_check(not reached and game.actor.is_on_floor() and absf(foot.x)<.045 and signed_z>=.30 and signed_z<=.54 and absf(anchor_foot.z)>1.85,
		tag+" attempted traversal blocked by closed leaves at grounded centerline"):
		return false
	print("CLOSE_TRAVERSAL_BLOCK ",JSON.stringify({"gate":tag,"attempt_side":"outside" if from_outside else "inside",
		"foot_x_m":foot.x,"still_correct_side_distance_m":signed_z,"grounded":game.actor.is_on_floor(),"aborted":not reached,
		"active_closed":not gate.target_open and is_zero_approx(gate.angle)}))
	return true

func tick(n: int) -> void:
	for t in range(n):
		await super.tick(1)
		if closing_index<0:
			continue
		var gate = game.gates[closing_index]
		var angle := float(gate.angle)
		if gate.target_open or angle > max_previous_angle + .000001 or max_previous_angle-angle > 2.3/60.0+.0001:
			draw_failures+=1
			print("DRAW_REJECT active close angle or direction")
			return
		if angle < max_previous_angle - .000001:
			moves_for_current += 1
		var trig := ""
		if rad_to_deg(max_previous_angle) > 45.0 and rad_to_deg(angle) <= 45.0:
			trig="mid"
		elif max_previous_angle > .000001 and is_zero_approx(angle):
			trig="closed"
		if not trig.is_empty():
			close_pending+=1
			RenderingServer.frame_post_draw.connect(_closing_frame.bind(closing_index,trig,angle,Engine.get_physics_frames(),tick_count,close_begin_tick),CONNECT_ONE_SHOT)
		max_previous_angle=angle

func _closing_frame(i: int, kind: String, queued: float, physics: int, tick_at: int, e_tick: int) -> void:
	close_pending-=1
	var gate := game.gates[i] as Node3D
	var tag := String(gate.get("gate_id"))+"-"+kind
	var angle := float(gate.get("angle"))
	var elapsed := Engine.get_physics_frames()-physics
	var camera := game.camera as Camera3D
	var imported_gate_witness := gate_and_light(tag)
	if tag in close_seen or gate.get("target_open") or elapsed<0 or elapsed>1 or angle>queued+.000001 or imported_gate_witness.is_empty():
		draw_failures+=1
		print("DRAW_REJECT active-close captured invalid state ",tag)
		return
	if root.get_camera_3d()!=camera or camera.projection!=Camera3D.PROJECTION_ORTHOGONAL or not is_equal_approx(camera.size,13.0) or camera.global_basis.z.normalized().dot(Vector3(7,11,11).normalized())<.999999:
		draw_failures+=1
		print("DRAW_REJECT active-close camera custody")
		return
	var image := root.get_texture().get_image()
	if not image or image.is_empty() or image.get_size()!=Vector2i(1280,720):
		draw_failures+=1
		print("DRAW_REJECT active-close frame preparation")
		return
	var file := capture_dir.path_join("close-"+tag+".png")
	if FileAccess.file_exists(file) or image.save_png(file)!=OK:
		draw_failures+=1
		print("DRAW_REJECT active-close output ownership")
		return
	var digest := HashingContext.new()
	digest.start(HashingContext.HASH_SHA256)
	digest.update(image.get_data())
	close_seen.append(tag)
	print("ACTIVE_CLOSE_FRAME ",JSON.stringify({"tag":tag,"queued_deg":rad_to_deg(queued),"drawn_deg":rad_to_deg(angle),
		"e_tick":e_tick,"tick":tick_at,"draw_physics_delta":elapsed,"native_sha256":digest.finish().hex_encode(),
		"camera_zoom_m":camera.size,"target_open":gate.get("target_open"),"gate_mount_witness":imported_gate_witness}))

func finish(phase: String) -> void:
	if phase=="write" and (close_pending>0 or close_count!=11 or close_failed!=0 or close_seen!=["gate-east-mid","gate-east-closed","gate-south-mid","gate-south-closed"]):
		print("DRAW_REJECT incomplete active closing ",close_count," ",close_failed," ",close_seen)
		quit(6)
		return
	if phase=="write" and (moving_frames!=[82,82] or not is_zero_approx(game.gates[0].angle) or not is_zero_approx(game.gates[1].angle)):
		print("DRAW_REJECT closing teardown totals or angle ",moving_frames)
		quit(6)
		return
	if phase=="write":
		print("ACTIVE_CLOSE_RESULT checks=",close_count," failures=",close_failed)
	await super.finish(phase)
