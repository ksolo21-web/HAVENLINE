extends RefCounted
## The chosen character wears its original skin. All four characters follow the
## same field controller, while each visible skeleton keeps its own bind lengths.
const CHARACTERS := {
	2: "res://assets/characters/Character2.glb",
	3: "res://assets/characters/Character3.glb",
	4: "res://assets/characters/Character4.glb"
}
const CENTER := {"Hips":"Pelvis","Spine":"Spine","Spine1":"Spine","Spine2":"Chest","Neck":"Neck","Head":"Head"}
const LIMBS := {"Shoulder":"Clavicle","Arm":"UpperArm","ForeArm":"Forearm","Hand":"Hand","UpLeg":"Thigh","Leg":"Shin","Foot":"Foot","ToeBase":"Toe"}
const DIGITS := {"Thumb":"Thumb","Index":"Index","Middle":"Middle","Ring":"Ring","Pinky":"Little"}
var world
var source: Skeleton3D
var originals: Array[Node] = []
var visual: Node3D
var target: Skeleton3D
var number := 1
var settings_path := ""
var mapping: Array = []
var fingers: Array = []
var elbows: Array[int] = []
var glove_chains: Array = []
var pelvis_source := -1
var feet: Array = []
var tread = preload("res://field_tread_samples.gd").new()
var last_actor := Vector3.INF
var grounded_ids: Array[int] = [-1,-1]
var grounded_points: Array[Vector3] = [Vector3.ZERO,Vector3.ZERO]
var plant_shift: Array[Vector3] = [Vector3.ZERO,Vector3.ZERO]

func setup(host: Node3D) -> void:
	world = host
	source = world.hero_model.find_children("*","Skeleton3D",true,false)[0]
	pelvis_source = source.find_bone("Pelvis")
	originals = world.hero_model.find_children("*","MeshInstance3D",true,false)
	settings_path = "user://field-player.cfg" if world.field_save.native_profile else world.field_save.directory.path_join("field-player.cfg")
	var prefs := ConfigFile.new()
	if prefs.load(settings_path) == OK:
		choose(int(prefs.get_value("player","character",1)),false)

func choose(id: int, persist := true) -> bool:
	if id == number: return true
	if id < 1 or id > 4: return false
	var next: Node3D
	var rig: Skeleton3D
	if id != 1:
		var body := load(CHARACTERS[id]) as PackedScene
		if not body: return false
		next = world.model(body,world.hero_model,float(world.layout.actor_height)/world.hero_model.global_basis.get_scale().y)
		var skeletons := next.find_children("*","Skeleton3D",true,false)
		if skeletons.size() != 1:
			next.queue_free()
			return false
		rig = skeletons[0]
	if persist:
		var prefs := ConfigFile.new()
		prefs.set_value("player","character",id)
		if prefs.save(settings_path) != OK:
			if next: next.queue_free()
			return false
	if visual:
		visual.hide()
		visual.queue_free()
	for piece in originals: piece.visible = id == 1
	number = id
	visual = next
	target = rig
	mapping.clear()
	fingers.clear()
	elbows.clear()
	glove_chains.clear()
	feet.clear()
	tread = preload("res://field_tread_samples.gd").new()
	grounded_ids.assign([-1,-1])
	plant_shift.assign([Vector3.ZERO,Vector3.ZERO])
	last_actor = Vector3.INF
	if not visual: return true
	visual.name = "PlayerCharacter"+str(id)
	world._disable_worn_shadow(visual)
	for bone in target.get_bone_count():
		var from := _source_id(String(target.get_bone_name(bone)).trim_prefix("mixamorig"))
		if from >= 0:
			mapping.append([from,bone,source.get_bone_global_rest(from).basis.inverse(),target.get_bone_global_rest(bone)])
	for side in ["Left","Right"]:
		elbows.append(target.find_bone("mixamorig"+side+"Arm"))
		feet.append([target.find_bone("mixamorig"+side+"UpLeg"),target.find_bone("mixamorig"+side+"Leg"),target.find_bone("mixamorig"+side+"Foot")])
		var hand_id := target.find_bone("mixamorig"+side+"Hand")
		glove_chains.append([elbows.back(),target.find_bone("mixamorig"+side+"ForeArm"),hand_id])
		var palm := target.get_bone_global_rest(hand_id)
		var index_knuckle := target.get_bone_global_rest(target.find_bone("mixamorig"+side+"HandIndex1")).origin
		var little_knuckle := target.get_bone_global_rest(target.find_bone("mixamorig"+side+"HandPinky1")).origin
		var down := (index_knuckle-palm.origin).cross(little_knuckle-palm.origin).normalized()
		if down.y>0.:down=-down
		for digit: String in DIGITS:
			for segment in range(1,4):
				var id_bone:=target.find_bone("mixamorig"+side+"Hand"+digit+str(segment))
				var bone_transform:=target.get_bone_global_rest(id_bone)
				var adjacent:=target.get_bone_parent(id_bone) if segment==3 else target.find_bone("mixamorig"+side+"Hand"+digit+str(segment+1))
				var along:=bone_transform.origin.direction_to(target.get_bone_global_rest(adjacent).origin)
				if segment==3:along=-along
				var curl_axis:=bone_transform.basis.inverse()*along.cross(down).normalized()
				var angle:=deg_to_rad(32. if segment<3 else 20.)
				if digit=="Thumb":angle*=.36
				fingers.append([id_bone,curl_axis.normalized(),angle])
	tread.bind(visual.find_children("*","MeshInstance3D",true,false)[0],target)
	update_pose(0.)
	return true

func _source_id(label: String) -> int:
	if CENTER.has(label): return source.find_bone(CENTER[label])
	var side := ".L" if label.begins_with("Left") else ".R"
	var limb := label.trim_prefix("Left").trim_prefix("Right")
	if LIMBS.has(limb): return source.find_bone(LIMBS[limb]+side)
	for digit: String in DIGITS:
		if limb.begins_with("Hand"+digit):
			var segment := mini(int(limb.right(1)),2) if digit=="Thumb" else int(limb.right(1))
			return source.find_bone(DIGITS[digit]+str(segment)+side)
	return -1

func _place_ankle(side: int, shift: Vector3) -> void:
	var ids: Array = feet[side]
	var hip := target.get_bone_global_pose(ids[0])
	var knee := target.get_bone_global_pose(ids[1])
	var boot := target.get_bone_global_pose(ids[2])
	var to := boot.origin + target.global_basis.inverse()*shift
	var direction := hip.origin.direction_to(to)
	var upper := hip.origin.distance_to(knee.origin)
	var lower := knee.origin.distance_to(boot.origin)
	var length := clampf(hip.origin.distance_to(to),absf(upper-lower)+.0005,upper+lower-.0005)
	var along := (upper*upper-lower*lower+length*length)/(2.*length)
	var pole := (knee.origin-hip.origin).slide(direction)
	# A nearly straight leg must retain the same forward bend branch.
	var front: Vector3 = (target.global_basis.inverse()*world.actor.global_basis.z).slide(direction).normalized()
	pole=front if pole.dot(front)<.006 else pole.normalized().lerp(front,.90).normalized()
	var hinge := hip.origin + direction*along + pole.normalized()*sqrt(maxf(0.,upper*upper-along*along))
	var end := hip.origin+direction*length
	hip.basis = Basis(Quaternion(hip.origin.direction_to(knee.origin),hip.origin.direction_to(hinge)))*hip.basis
	knee.basis = Basis(Quaternion(knee.origin.direction_to(boot.origin),hinge.direction_to(end)))*knee.basis
	knee.origin=hinge
	boot.origin=end
	target.set_bone_global_pose(ids[0],hip)
	target.set_bone_global_pose(ids[1],knee)
	target.set_bone_global_pose(ids[2],boot)

func update_pose(dt: float) -> void:
	if not target: return
	var scale_ratio := source.global_basis.get_scale().y/target.global_basis.get_scale().y
	for pair: Array in mapping:
		var current := source.get_bone_global_pose(pair[0])
		var rest: Transform3D = pair[3]
		var local := target.get_bone_global_pose(pair[1])
		local.basis=(current.basis*pair[2]).orthonormalized()*rest.basis
		if pair[0] == pelvis_source:
			local.origin=rest.origin+(current.origin-source.get_bone_global_rest(pair[0]).origin)*scale_ratio
		target.set_bone_global_pose(pair[1],local)
	# Keep the palms outside the cup and leather pouches on the belted
	# outfits. The source and target keep their individual shoulder widths.
	if number in [2,3,4]:
		for side in 2:
			var arm:=target.get_bone_global_pose(elbows[side])
			var spread:=deg_to_rad(11. if number==3 else 10.)
			var forward:Vector3=(target.global_basis.inverse()*world.actor.global_basis.z).normalized()
			var sign_x:=1. if arm.origin.x>0. else -1.
			arm.basis=Basis(forward,sign_x*spread)*arm.basis
			target.set_bone_global_pose(elbows[side],arm)
	for chain: Array in glove_chains:
		preload("res://field_glove_clearance.gd").solve(target,world.actor,chain,number)
	# Rest the selected gloves in a loose curl. Increase it slightly when
	# running; all phalanges retain the initial rig's own local bend axes.
	var squeeze := lerpf(.43,1.,smoothstep(.30,3.3,world.actor.velocity.length()))
	for finger: Array in fingers:
		var joint: int=finger[0]
		var rotation:=target.get_bone_pose_rotation(joint)
		target.set_bone_pose_rotation(joint,rotation*Quaternion(finger[1],finger[2]*squeeze))
	if not world.gait_motor.skeleton or tread.soles.is_empty(): return
	var boots: Vector2 = world.gait_motor._heights()
	var points: PackedVector3Array = tread.points()
	var low: Array[int] = tread.lowest(points)
	if low[0]<0 or low[1]<0:return
	var body: Node3D = world.actor
	var actor_at: Vector3 = body.global_position
	if actor_at.distance_squared_to(last_actor)>1.:
		grounded_ids.assign([-1,-1])
		plant_shift.assign([Vector3.ZERO,Vector3.ZERO])
	last_actor=actor_at
	var goals: Array[Vector3] = []
	var heights := Vector2.ZERO
	for side in 2:
		var src_ids: Array = world.gait_motor.leg_chains[side]
		var dst_ids: Array = feet[side]
		var hip := target.to_global(target.get_bone_global_pose(dst_ids[0]).origin)
		var knee := target.to_global(target.get_bone_global_pose(dst_ids[1]).origin)
		var ankle := target.to_global(target.get_bone_global_pose(dst_ids[2]).origin)
		var ref := source.to_global(source.get_bone_global_pose(src_ids[2]).origin)
		var ref_rest := source.to_global(source.get_bone_global_rest(src_ids[2]).origin)
		var own_rest := target.to_global(target.get_bone_global_rest(dst_ids[2]).origin)
		var goal := own_rest+(ref-ref_rest)
		goal.y=ankle.y + boots[side]-points[low[side]].y
		var prediction := (goal-ankle).slide(Vector3.UP)
		var marker := grounded_ids[side]
		if boots[side]-actor_at.y > .024:
			grounded_ids[side]=-1
			plant_shift[side]=plant_shift[side].move_toward(Vector3.ZERO,dt*1.4)
		else:
			if marker<0 or points[marker].y-points[low[side]].y>.012:
				marker=low[side]
				grounded_ids[side]=marker
				grounded_points[side]=points[marker]+prediction+plant_shift[side]
			plant_shift[side]=(grounded_points[side]-points[marker]-prediction).slide(Vector3.UP).limit_length(.20)
		goal+=plant_shift[side]
		goals.append(goal)
		# Match the compact driver's knee flex using this body's actual femur
		# and tibia. The supporting leg governs pelvis height for this step.
		var upper := hip.distance_to(knee)
		var lower := knee.distance_to(ankle)
		var ref_hip := source.get_bone_global_pose(src_ids[0]).origin
		var ref_knee := source.get_bone_global_pose(src_ids[1]).origin
		var ref_boot := source.get_bone_global_pose(src_ids[2]).origin
		var flex := clampf((ref_knee-ref_hip).angle_to(ref_boot-ref_knee),deg_to_rad(13.),deg_to_rad(120.))
		var d2 := upper*upper+lower*lower+2.*upper*lower*cos(flex)
		var horizontal := (goal-hip).slide(Vector3.UP).length_squared()
		heights[side]=goal.y+sqrt(maxf(.001,d2-horizontal))-hip.y
	var left_weight := smoothstep(-.024,.024,boots.y-boots.x)
	var lift := lerpf(heights.y,heights.x,left_weight)
	for side in 2:
		var ids: Array=feet[side]
		var hip := target.to_global(target.get_bone_global_pose(ids[0]).origin)
		var knee := target.to_global(target.get_bone_global_pose(ids[1]).origin)
		var ankle := target.to_global(target.get_bone_global_pose(ids[2]).origin)
		var reach := hip.distance_to(knee)+knee.distance_to(ankle)
		var horizontal := (goals[side]-hip).slide(Vector3.UP).length_squared()
		lift=minf(lift,goals[side].y+sqrt(maxf(.001,reach*reach*.988-horizontal))-hip.y)
	visual.global_position.y+=lift
	for side in 2:
		var ankle := target.to_global(target.get_bone_global_pose(feet[side][2]).origin)
		_place_ankle(side,goals[side]-ankle)
	# The outer leather near the sole can share a shin influence. Recheck
	# the actual material patch after IK and keep it planted through toe-off.
	points=tread.points()
	low=tread.lowest(points)
	for side in 2:
		var marker := grounded_ids[side]
		var error := (grounded_points[side]-points[marker]).slide(Vector3.UP) if marker>=0 else Vector3.ZERO
		error.y=boots[side]-points[low[side]].y
		_place_ankle(side,error)

func boot_contacts() -> PackedVector3Array:
	return tread.contacts() if target else world.gait_motor.snow_contact_points()
