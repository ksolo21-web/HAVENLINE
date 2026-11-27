extends "res://tests/field_route.gd"

const SessionProof=preload("res://tests/lifecycle_test_profile.gd")

const CASES := {
	"west": [[-1.0,5.8],[-3.7,6.7],[-7.2,8.4],[-9.8,10.2],[-12.6,12.0],[-14.2,14.0],[-10.7,13.4],[-7.2,9.5]],
	"south": [[.3,5.8],[.7,8.3],[1.8,11.7],[.4,14.6],[-1.5,17.5],[1.9,19.5],[2.7,14.5],[1.3,10.8]],
	"east": [[2.2,6.3],[5.8,8.3],[8.8,10.2],[11.1,11.9],[13.9,10.5],[16.0,8.5],[15.0,6.0],[12.3,5.4]],
}
var witness := []
var failures := PackedStringArray()
var report := {}
var asset_appearances := {}
var sim_steps:=0
var previous := Vector3.INF
var high_live := 0
var high_open := 0
var high_proxies := 0
var longest_camera_gap := 0.
var capture := false
var route_name := ""
var forest_out := ""
var timings := {}
var forest_started := false

func _walk(point: Vector3, tol := .26, max_frames:=440) -> bool:
	for index in max_frames:
		var close := move_to([point.x,point.z],tol)
		if close:
			steer(Vector2.ZERO)
			return true
		if field.persist_blocked or field.reset_time > 0.0:
			steer(Vector2.ZERO)
			return false
		await _step()
	steer(Vector2.ZERO)
	return false

func _step() -> void:
	await physics_frame
	sim_steps+=1
	if not forest_started:
		return
	var live := 0
	var proxies := 0
	for entry: Dictionary in field.forest.records:
		if is_instance_valid(entry.live): live+=1
		elif entry.proxy_visible: proxies+=1
		var id: String=entry.id
		if not timings.has(id) and field.lifecycle.cooling.has(id):
			timings[id]={"start":field.simulation_time,"start_delay":field.lifecycle.cooling[id],"position":pt(entry.transform.origin),"first_type":"record"}
		elif timings.has(id) and not field.lifecycle.cooling.has(id) and not timings[id].has("renewed"):
			timings[id].renewed=field.simulation_time
			timings[id].returned_to_proxy=entry.proxy_visible and not is_instance_valid(entry.live)
	high_live=maxi(high_live,live)
	high_proxies=maxi(high_proxies,proxies)
	high_open=maxi(high_open,field.field_env.resource_sightline.opened.size())
	var actor_at: Vector3=field.actor.global_position
	var center: Vector3=camera.global_position-field.camera_follow_offset
	longest_camera_gap=maxf(longest_camera_gap,Vector2(center.x-actor_at.x,center.z-actor_at.z).length())
	if previous.is_finite():
		var step:=previous.distance_to(actor_at)
		if step>1.0 and not field.reset_time>0.0:
			failures.append("unexpected discontinuous actor movement " + str(step))
	previous=actor_at

func _coast(frames: int) -> void:
	steer(Vector2.ZERO)
	for i in frames: await _step()

func _check(ok: bool, label: String) -> void:
	if not ok: failures.append(label)

func _record(label: String, expected: Vector3, arrived: bool) -> void:
	var actual: Vector3=field.actor.global_position
	var next := {"label": label,"arrived":arrived,"target":pt(expected),"position":pt(actual),"seconds":field.simulation_time,"hp":field.player_hp,"wood":field.inventory.carried.wood,"camera_matches":camera==root.get_camera_3d(),"same_view":camera.global_basis.is_equal_approx(report.camera_basis) if report.has("camera_basis") else false,"roots_inside_radius_4":0,"cutaway_shapes":field.field_env.resource_sightline.opened.size()}
	for row: Dictionary in field.forest.records:
		if actual.distance_squared_to(row.transform.origin)<16. and not row.get("occupied",false):
			next.roots_inside_radius_4+=1
	witness.append(next)

func _view(key: String) -> void:
	if not capture: return
	await process_frame
	RenderingServer.force_draw(false,1.0/60.0)
	root.get_texture().get_image().save_jpg(forest_out.path_join(key+".jpg"),.90)

func _pinch() -> void:
	var c:=Vector2(root.get_visible_rect().size)*Vector2(.48,.45)
	field.clear_touch()
	touch(6,c-Vector2(18,0),true)
	touch(7,c+Vector2(18,0),true)
	await _step()
	for i in 12:
		var gap:=18.+float(i+1)*5.
		for j in 2:
			var drag:=InputEventScreenDrag.new()
			drag.index=6+j
			drag.position=c+Vector2(gap*(-1. if j==0 else 1.),0)
			root.push_input(drag,true)
		await _step()
	touch(6,c-Vector2(78,0),false)
	touch(7,c+Vector2(78,0),false)
	await _coast(5)

func _regrowth_trial() -> void:
	# Rest nearby on live input. Choose one of the nearby rendered batched pines.
	var candidates:Array=[]
	for row: Dictionary in field.forest.records:
		if row.get("occupied",false) or not field.is_source_available(row.id) or row.index<0: continue
		var p:Vector3=row.transform.origin
		var distance:float=p.distance_to(field.actor.global_position)
		if distance>13.:continue
		candidates.append({"row":row,"distance":distance})
	candidates.sort_custom(func(a,b): return a.distance<b.distance)
	for entry in candidates.slice(0,5):
		var row: Dictionary=entry.row
		var at: Vector3=row.transform.origin
		var toward: Vector3=at.direction_to(field.actor.global_position)
		var stance:=at+toward*2.52
		if not await _walk(stance,.16,155):continue
		await _coast(205)
		if not timings.has(row.id):
			continue
		_record("depleted source",at,true)
		await _view("West-source-depleted")
		var before:=int(field.inventory.carried.wood)
		await _walk(at,.33,120)
		await _coast(22)
		var after:=int(field.inventory.carried.wood)
		var leave:=at+toward*7.30
		var left:=await _walk(leave,.36,155)
		await _coast(305)
		var state: Dictionary=timings[row.id]
		state.leave_path=left
		state.carried_before_pickup=before
		state.carried_after_pickup=after
		state.proxy_after_away=row.proxy_visible and not is_instance_valid(row.live)
		state.regrowth_elapsed=state.get("renewed",0.0)-state.start
		await _view("West-source-recovered-away")
		var returned:=await _walk(stance,.16,178)
		await _coast(20)
		state.returned=returned
		state.returned_live=is_instance_valid(row.live)
		state.returned_available=field.is_source_available(row.id)
		state.returned_phase=row.live.phase if is_instance_valid(row.live) else ""
		_record("returned to same tree ID",at,returned)
		await _view("West-source-return")
		report.regrowth_id=row.id
		report.regrowth=state.duplicate()
		_check(state.regrowth_elapsed>=4.96 and state.regrowth_elapsed<=5.07,"renewal is five seconds")
		_check(state.proxy_after_away,"renews as distant batch while player away")
		_check(state.returned_live and state.returned_available,"same renewable tree activates on touch return")
		_check(after>before,"material picked up on the real player back")
		return
	_check(false,"no attempted west forest harvest was observed depleting")

func run() -> void:
	route_name=OS.get_environment("T01_ROUTE")
	capture=OS.get_environment("T01_IMAGES")=="1"
	forest_out=OS.get_environment("T01_OUT")
	root.size=Vector2i(460,760)
	field=load("res://field_opening.tscn").instantiate()
	root.add_child(field)
	current_scene=field
	camera=field.camera
	origin=Vector2(root.get_visible_rect().size)*Vector2(.22,.82)
	await _coast(18)
	report.camera_basis=camera.global_basis
	_check(not field.persist_blocked,"archived returning camp opens")
	var start:Vector3=field.actor.global_position
	report.start=pt(start)
	forest_started=true
	for i in CASES[route_name].size():
		var target:=Vector3(CASES[route_name][i][0],0,CASES[route_name][i][1])
		var success:=await _walk(target)
		_record("waypoint " + str(i+1),target,success)
		_check(success,"touch route reaches point " + str(i+1))
		if i==4:
			await _coast(8)
			await _view(route_name+"-1x")
			if capture:
				await _pinch()
				report.pinch_factor=field.get_zoom_ratio()
				await _view(route_name+"-2x")
				field.set_zoom_ratio(1.0)
	if route_name=="west" and OS.get_environment("T01_REGROW")=="1": await _regrowth_trial()
	report.erase("camera_basis")
	report.route=route_name
	report.failures=failures
	report.checkpoints=witness
	report.harvested_records=timings
	report.total_local_records=field.forest.records.size()
	report.high_live=high_live
	report.high_proxies=high_proxies
	report.high_open=high_open
	report.max_camera_follow_gap_m=longest_camera_gap
	report.window=[root.size.x,root.size.y]
	report.renderer=RenderingServer.get_video_adapter_name()
	report.steps=sim_steps
	report.persistence=not field.persist_blocked
	var out:=FileAccess.open(forest_out.path_join("witness.json"),FileAccess.WRITE)
	out.store_string(JSON.stringify(report,"\t"))
	out.close()
	print("FOREST_ROUTE ",JSON.stringify({"route":route_name,"steps":sim_steps,"failures":failures,"regrowth":report.get("regrowth",{}),"high_live":high_live,"records":report.total_local_records,"cutaway":high_open}))
	await SessionProof.drain_field_audio(self,field)
	field.queue_free()
	for i in 8: await process_frame
	quit(1 if not failures.is_empty() else 0)
