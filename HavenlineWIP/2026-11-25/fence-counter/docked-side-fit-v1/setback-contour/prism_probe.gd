extends "res://tests/_audit_cpu_surface.gd"
# Proposal-only: a supplemental shape, independent numeric points, no moved markers.
var shape_guard: CollisionShape3D
var q: Dictionary
var mark_orig: Dictionary
var angles := 0
var cover_rows := 0
var pose_ids := []

func install_fixture() -> bool:
	if not await super.install_fixture():
		return false
	q = JSON.parse_string(FileAccess.get_file_as_string("res://tests/_proposal_contour.json"))
	if q.is_empty():
		return false
	var originals := []
	for old in joined.get_children():
		originals.append({"shape":old.shape,"size":old.shape.size,"node":old,"transform":old.transform})
	var frame := joined.get_parent() as Node3D
	var original := joined.global_transform
	for name in ["WorkerInteriorStance","CustomerExteriorStance","StockHandling","PaymentHandling","StockRestWitness","PaymentRestWitness"]:
		var n: Node3D=frame.get_node("Markers_NotBindings/"+name)
		mark_orig[name]=n.transform
	var point_set := PackedVector3Array()
	for p in q["guard_vertices_xz"]:
		point_set.append(Vector3(p[0],0.,p[1]))
		point_set.append(Vector3(p[0],.95,p[1]))
	var hull := ConvexPolygonShape3D.new()
	hull.points=point_set
	shape_guard=CollisionShape3D.new()
	shape_guard.name="ConditionalCounterClearanceProofOnly"
	shape_guard.shape=hull
	joined.add_child(shape_guard)
	await tick(2)
	check(joined.global_transform==original and joined.get_child_count()==4 and
		PhysicsServer3D.body_get_shape_count(joined.get_rid())==4,"exact frame with one new detached proof prism")
	for i in range(originals.size()):
		var p: Dictionary=originals[i]
		var n := joined.get_child(i) as CollisionShape3D
		check(is_same(n,p.node) and n.transform==p.transform and is_same(n.shape,p.shape) and n.shape.size==p.size,
			"same original retained collider %d" % i)
	check(frame.get_node("UnmodifiedDonor").is_visible_in_tree(),"original art visibly remains instanced")
	return true

func marker_invariants() -> bool:
	var frame := joined.get_parent() as Node3D
	for name in mark_orig:
		var n: Node3D=frame.get_node("Markers_NotBindings/"+name)
		if n.transform!=mark_orig[name]:
			return false
	return true

func precise_point(target: Vector3) -> bool:
	gesture += 1
	send_touch(true)
	for i in range(180):
		var delta: Vector3=target-game.actor.position
		delta.y=0.
		if delta.length()<=.0015 or not game.bound:
			break
		var local := delta.rotated(Vector3.UP,-atan2(7.,11.))
		var ev := InputEventScreenDrag.new()
		ev.index=gesture
		ev.position=CENTER+(Vector2(local.x,local.z)*15.).limit_length()*82.
		game._input(ev)
		await tick(1)
	send_touch(false)
	await tick(3)
	var foot: Vector3=game.actor.position
	return game.bound and Vector2(foot.x-target.x,foot.z-target.z).length()<=.002

func snapshot(name: String, kind: String, expected: Vector2, desired: int=0, inside: bool=true) -> bool:
	await tick(12)
	var frame := joined.get_parent() as Node3D
	var actor := game.actor as CharacterBody3D
	var animation: AnimationPlayer=game.hero_locomotion.player
	var hero: Node3D
	if not actor.is_on_floor() or animation==null:
		return false
	for child in actor.get_children():
		if child.is_ancestor_of(animation):
			hero=child
	if hero==null:
		return false
	var ss:=hero.find_children("*","Skeleton3D",true,false)
	if ss.size()!=1:
		return false
	var skel:=ss[0] as Skeleton3D
	skel.force_update_all_bone_transforms()
	var anatomy:={}
	for bone in ["Head","L_Hand","R_Hand"]:
		var idx:=skel.find_bone(bone)
		if idx<0:
			return false
		anatomy[bone]=pt(frame.to_local(skel.to_global(skel.get_bone_global_pose(idx).origin)))
	if not written_donor:
		written_donor=output_surface(frame.get_node("UnmodifiedDonor").find_children("*","MeshInstance3D",true,false),frame,"counter",false)
	if not written_donor or not output_surface(hero.find_children("*","MeshInstance3D",true,false),frame,name,true):
		return false
	var exact_pointer:={}
	for mark in ["WorkerInteriorStance","CustomerExteriorStance","StockHandling","PaymentHandling","StockRestWitness","PaymentRestWitness"]:
		var n: Node3D=frame.get_node("Markers_NotBindings/"+mark)
		exact_pointer[mark]=pt(frame.to_local(n.global_position))
	pose_ids.append(name)
	var feet:=frame.to_local(actor.global_position)
	var error:=Vector2(feet.x,feet.z).distance_to(expected)
	var phi:=rad_to_deg(wrapf(actor.rotation.y-(PI if inside else 0.),-PI,PI))
	print("PRISM_CPU ",JSON.stringify({"id":name,"kind":kind,"foot":pt(feet),"yaw":actor.rotation.y,
		"heading_degrees_from_counter":phi,"desired_degrees":desired,"expected_xz":[expected.x,expected.y],
		"planar_error_m":error,"floor":actor.is_on_floor(),"anatomy":anatomy,"actual_unbound_markers":exact_pointer,
		"animation":str(animation.current_animation),"animation_time":animation.current_animation_position,
		"physics_shape_slides":joined_contacts,"display":DisplayServer.get_name()}))
	return kind!="temporary-stance" or (error<=.002 and absf(absf(phi)-absf(float(desired)))<5.)

func center_probe(inside:bool)->bool:
	var frame:=joined.get_parent() as Node3D
	var side: String="inboard" if inside else "outboard"
	var sign_side:=1. if inside else -1.
	var dest: Array=q["conditional_targets_xz"][side]
	var z:=float(dest[1])
	var source: Node3D=frame.get_node("Markers_NotBindings/"+("WorkerInteriorStance" if inside else "CustomerExteriorStance"))
	for deg: int in [0,-90,90]:
		var t:=deg_to_rad(float(deg))
		var pre:=Vector3(.52*sin(t),0,z+.52*cos(t)*sign_side)
		var apron:=Vector3(0,0,z+.73*sign_side)
		var target: Vector3=game.to_local(frame.to_global(Vector3(0,0,z)))
		check(await precise_point(game.to_local(frame.to_global(apron))),"lawful apron at temporary target")
		check(await precise_point(game.to_local(frame.to_global(pre))),"ordinary short heading approach setup")
		check(await precise_point(target),"temporary proof target reached by ordinary steering")
		check(await snapshot("temp-%s-%+d" % [side,deg],"temporary-stance",Vector2(0,z),deg,inside),
			"unchanged original markers and actual posed temporary ground arrival")
		angles+=1
	check(not await travel(game.to_local(source.global_position),75),"original stance occupancy excluded by temporary test prism without moving original marker")
	check(joined_contacts.has(shape_guard.get_index()) and game.actor.is_on_floor(),"original center stance is now excluded by actual new shape")
	check(await snapshot("stop-"+side,"center-block",Vector2(0,z),0,inside),"actual held ground stop mesh")
	cover_rows+=1
	# Probe old seams and actual beyond-original-guard diagonal trajectories.
	for px: float in [-1.825,1.825,-1.65,1.65]:
		var seam:=absf(px)>1.8
		var start:=Vector3(px,0,z+.44*sign_side)
		var aimx:=px if seam else signf(px)*1.76
		var end:=Vector3(aimx,0,-1.90*sign_side)
		var label:=("seam-" if seam else "nudge-")+side+("-left" if px<0 else "-right")
		check(await travel(game.to_local(frame.to_global(start))),"real "+label+" approach on lawful ground")
		check(not await travel(game.to_local(frame.to_global(end)),85),"real "+label+" does not cross")
		var foot:=frame.to_local(game.actor.global_position as Vector3)
		check(foot.z*sign_side>.43 and game.actor.is_on_floor() and joined_contacts.has(shape_guard.get_index()),
			"real "+label+" touched proposal shape and ended on original side")
		check(await snapshot(label,"seam-block" if seam else "nudge-block",Vector2(px,z),0,inside),"actual "+label+" full skin capture")
		cover_rows+=1
		# Retreat in place before moving parallel to the coast; no fabricated yaw.
		check(await travel(game.to_local(frame.to_global(Vector3(foot.x,0,z+.44*sign_side)))),"clear retreat after "+label)
	check(await travel(game.to_local(frame.to_global(Vector3(2.,0,z+.38*sign_side)))),"same apron exits toward gate route")
	check(marker_invariants(),"six original service/stock/payment marker transforms unchanged")
	if not inside:
		check(angles==6 and cover_rows==10 and pose_ids.size()==16,"both proof points and all actual stop/seam/nudge poses")
	return true
