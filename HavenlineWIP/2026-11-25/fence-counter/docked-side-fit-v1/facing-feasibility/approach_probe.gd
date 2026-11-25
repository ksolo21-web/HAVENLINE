extends "res://tests/_stop_guard.gd"
# Actual native motion only. Guard and its route/negative cases remain exact.
var angle_rows := 0

func precise_point(target: Vector3) -> bool:
	gesture += 1
	send_touch(true)
	for i in range(180):
		var delta: Vector3 = target - game.actor.position
		delta.y = 0.0
		if delta.length() <= .0015 or not game.bound:
			break
		var local := delta.rotated(Vector3.UP,-atan2(7.0,11.0))
		var ev := InputEventScreenDrag.new()
		ev.index=gesture
		ev.position=CENTER+(Vector2(local.x,local.z)*15.0).limit_length()*82.0
		game._input(ev)
		await tick(1)
	send_touch(false)
	await tick(3)
	var foot: Vector3 = game.actor.position
	return game.bound and Vector2(foot.x-target.x,foot.z-target.z).length() <= .002

func write_pose(name: String, desired_deg: int, mark: Node3D, inside: bool) -> bool:
	await tick(12)
	var frame := joined.get_parent() as Node3D
	var actor := game.actor as CharacterBody3D
	var animation: AnimationPlayer = game.hero_locomotion.player
	var hero: Node3D
	if animation == null:
		return false
	for child in actor.get_children():
		if child.is_ancestor_of(animation):
			hero=child
	if hero==null or not actor.is_on_floor():
		return false
	var target: Vector3=frame.to_local(mark.global_position)
	var foot: Vector3=frame.to_local(actor.global_position)
	var yaw: float=actor.rotation.y
	var axis_angle: float=rad_to_deg(wrapf(yaw-(PI if inside else 0.0),-PI,PI))
	var mark_error: float=Vector2(foot.x-target.x,foot.z-target.z).length()
	if not output_surface(hero.find_children("*","MeshInstance3D",true,false),frame,name,true):
		return false
	if not written_donor:
		written_donor=output_surface(frame.get_node("UnmodifiedDonor").find_children("*","MeshInstance3D",true,false),frame,"counter",false)
	angle_rows+=1
	print("ACTUAL_ANGLE ",JSON.stringify({"id":name,"desired_degrees":desired_deg,"retained_physics_yaw":yaw,
		"native_axis_degrees":axis_angle,"actor_foot":pt(foot),"original_marker":pt(target),
		"planar_marker_error":mark_error,"floor":actor.is_on_floor(),"display":DisplayServer.get_name(),
		"animation":str(animation.current_animation),"animation_time":animation.current_animation_position}))
	return written_donor and actor.is_on_floor() and mark_error<=.002 and absf(absf(axis_angle)-absf(float(desired_deg)))<=5.0

func center_probe(inside: bool) -> bool:
	var frame := joined.get_parent() as Node3D
	var mark: Node3D = frame.get_node("Markers_NotBindings/WorkerInteriorStance" if inside else "Markers_NotBindings/CustomerExteriorStance")
	var side := 1.0 if inside else -1.0
	var marker := frame.to_local(mark.global_position)
	for deg: int in [0,-30,30,-60,60,-90,90]:
		var theta := deg_to_rad(float(deg))
		var sector := Vector3(sin(theta)*.52,0.0,cos(theta)*.52*side)
		var retreat: Vector3 = game.to_local(frame.to_global(marker + Vector3(0,0,.73*side)))
		var approach: Vector3 = game.to_local(frame.to_global(marker + sector))
		var destination: Vector3 = game.to_local(mark.global_position)
		check(await precise_point(retreat),"ordinary retreat from earlier angle to lawful apron")
		check(await precise_point(approach),"ordinary exact optional angle setup")
		check(await precise_point(destination),"ordinary final short approach to unchanged service marker")
		var id := "facing-%s-%+d" % ["inboard" if inside else "outboard",deg]
		check(await write_pose(id,deg,mark,inside),"pose and original marker authenticated at sampled angle %s" % id)
	check(angle_rows == (7 if inside else 14),"all authored test directions captured without setting yaw or changing marker")
	return await super.center_probe(inside)
