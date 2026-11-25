extends "res://tests/_audit_cpu_surface.gd"
## Detached, nonvisual fourth shape on the unchanged north compound body.
const GUARD_X := 3.00
const GUARD_Y := 0.95
const GUARD_Z := 1.76
var guard: CollisionShape3D
var direction_rows := 0
var stance_rows := 0
var shoulder_rows := 0
var seam_rows := 0

func install_fixture() -> bool:
	if not await super.install_fixture():
		return false
	var prior_shapes := []
	for n in joined.get_children():
		prior_shapes.append({"node":n, "transform":n.transform, "shape":n.shape, "size":n.shape.size})
	var previous_body := joined.global_transform
	var frame := joined.get_parent() as Node3D
	var capsule: CapsuleShape3D
	for n in game.actor.get_children():
		if n is CollisionShape3D and n.shape is CapsuleShape3D:
			capsule = n.shape
	if capsule == null:
		return false
	check(is_equal_approx(capsule.radius,.31),"exact stock capsule; no collider change to actor")
	var shape := BoxShape3D.new()
	shape.size = Vector3(GUARD_X, GUARD_Y, GUARD_Z)
	guard = CollisionShape3D.new()
	guard.name = "DetachedCenterStopGuard"
	guard.position = Vector3(0, GUARD_Y * .5, 0)
	guard.shape = shape
	joined.add_child(guard)
	await tick(2)
	check(joined.get_child_count() == 4 and PhysicsServer3D.body_get_shape_count(joined.get_rid()) == 4,"one additional invisible center guard")
	check(joined.global_transform == previous_body and joined.collision_layer == 1 and joined.collision_mask == 0,"same native joined body frame and collision layers")
	for k in range(prior_shapes.size()):
		var p: Dictionary = prior_shapes[k]
		var n := joined.get_child(k) as CollisionShape3D
		check(is_same(n,p.node) and n.transform == p.transform and is_same(n.shape,p.shape) and n.shape.size == p.size,"exact original collider %d unmodified" % k)
	check(frame.get_node("UnmodifiedDonor").is_visible_in_tree(),"unchanged donor still visible")
	return true

func pt_gap(a: Vector3, b: Vector3) -> float:
	return Vector2(a.x-b.x,a.z-b.z).length()

func blocked_at(local_x: float, initial_z: float, opposite_z: float, label: String) -> void:
	var from_inside := initial_z > -4.0
	var sign_side := 1.0 if from_inside else -1.0
	var center := absf(local_x) < .001
	var frame := joined.get_parent() as Node3D
	var stance: Node3D = frame.get_node("Markers_NotBindings/WorkerInteriorStance" if from_inside else "Markers_NotBindings/CustomerExteriorStance")
	check(await travel(game.point([local_x, initial_z])),label + " ordinary approach")
	if center:
		check(pt_gap(game.actor.global_position,stance.global_position) < .05 and game.actor.is_on_floor(),label + " exact authored stance remains reachable")
	check(not await travel(game.point([local_x,opposite_z]),75),label + " opposite side denied")
	var feet := frame.to_local(game.actor.global_position as Vector3)
	var signed := feet.z * sign_side
	if center:
		check(signed >= 1.17 and signed <= 1.22 and game.actor.is_on_floor(),label + " expected moved center stop grounded")
		check(joined_contacts.has(guard.get_index()),label + " actual shape slide includes new center guard")
	else:
		check(signed >= .43 and signed <= .52 and game.actor.is_on_floor(),label + " old seam stop grounded and position preserved")
		check(not joined_contacts.is_empty() and not joined_contacts.has(guard.get_index()),label + " actual seam slides on old collider only")
	var start: Vector3 = game.to_global(game.point([local_x,initial_z],.475))
	var end: Vector3 = game.to_global(game.point([local_x,opposite_z],.475))
	var hit: Dictionary = game.get_world_3d().direct_space_state.intersect_ray(PhysicsRayQueryParameters3D.create(start,end,1,[game.actor.get_rid()]))
	check(hit.get("collider")==joined and (int(hit.get("shape",-1))==guard.get_index())==center,label + " ray contact exact expected body and center/seam")
	direction_rows += 1
	print("STOP_GUARD ", JSON.stringify({"side":"inboard" if from_inside else "outboard","x_requested":local_x,"center":center,"feet":pt(feet),"shape_contact_indices":joined_contacts,"ray_shape":hit.get("shape",-1)}))
	if not center:
		var side := "inboard" if from_inside else "outboard"
		var site := "left" if local_x<0.0 else "right"
		check(await shot("seam-"+side+"-"+site,Vector3.ZERO,Vector3.ZERO,0,false),"actual CPU capture of retained seam")

func center_probe(from_inside: bool) -> bool:
	if not await super.center_probe(from_inside):
		return false
	var initial_z := -2.65 if from_inside else -5.45
	var opposite_z := -5.45 if from_inside else -2.65
	var apron_z := -2.30 if from_inside else -5.70
	# Move back into the legal apron before trying the existing original seams.
	for x in [-1.825,1.825]:
		check(await travel(game.point([0.0,apron_z])), "center stop retreats freely before seam")
		check(await travel(game.point([x,apron_z])), "legal apron lateral approach")
		await blocked_at(x,initial_z,opposite_z,"retained seam %.3f" % x)
	check(await travel(game.point([1.825,apron_z])), "last seam retreats freely")
	for xsign in [-1.0,1.0]:
		check(await travel(game.point([xsign*1.65,apron_z])),"center edge diagonal legal start")
		check(not await travel(game.point([xsign*1.76,opposite_z]),75),"guard-end diagonal opposite side denied")
		var frame := joined.get_parent() as Node3D
		var feet := frame.to_local(game.actor.global_position as Vector3)
		check(game.actor.is_on_floor() and feet.z*(1.0 if from_inside else -1.0) >= .43 and not joined_contacts.is_empty(),"guard-end diagonal actual slide and grounded")
		check(joined_contacts.has(guard.get_index()),"guard-end diagonal genuinely nudges the new guard")
		check(absf(feet.x) >= 1.52 and absf(feet.x) <= 1.80,"actor center did reach outside the 1.50m guard-end plane")
		var side := "inboard" if from_inside else "outboard"
		var site := "left" if xsign<0 else "right"
		print("SHOULDER_ROUTE ",JSON.stringify({"side":side,"site":site,"feet":pt(feet),"shape_contact_indices":joined_contacts}))
		if not await shot("shoulder-"+side+"-"+site,Vector3.ZERO,Vector3.ZERO,0,false):
			return false
		check(await travel(game.point([xsign*1.76,apron_z])),"guard-end nudge retreat stays clear")
	check(await travel(game.point([2.0,apron_z])),"apron returns to validated continuation line")
	if not from_inside:
		check(direction_rows == 6 and found_stops == 2 and stance_rows == 2 and shoulder_rows == 4 and seam_rows == 4,"six physical directions, two skinned center stops and two stance samples")
	return true

func shot(tag: String, focus: Vector3, offset: Vector3, span: float, custom: bool) -> bool:
	if tag not in ["center-inboard-stance","center-outboard-stance"] and not tag.begins_with("shoulder-") and not (tag.begins_with("seam-") and not custom):
		return await super.shot(tag,focus,offset,span,custom)
	route_frames += 1
	# No collector or UI fabricated; this only compares the actual reachable stance.
	await tick(12)
	var frame := joined.get_parent() as Node3D
	var actor := game.actor as CharacterBody3D
	var hero: Node3D
	var animation: AnimationPlayer = game.hero_locomotion.player
	if animation == null:
		return false
	for child in actor.get_children():
		if child.is_ancestor_of(animation):
			hero = child
	if hero == null or not actor.is_on_floor():
		return false
	if not output_surface(hero.find_children("*", "MeshInstance3D", true, false),frame,tag,true):
		push_error("stance cannot be sourced from the actual rig")
		return false
	if tag.begins_with("shoulder-"):
		shoulder_rows += 1
	elif tag.begins_with("seam-"):
		seam_rows += 1
	else:
		stance_rows += 1
	print("CPU_STANCE ",JSON.stringify({"id":tag,"foot":pt(frame.to_local(actor.global_position)),"animation":str(animation.current_animation),"animation_time":animation.current_animation_position,"yaw":actor.rotation.y,"floor":actor.is_on_floor(),"actual_renderer":DisplayServer.get_name()}))
	return true
