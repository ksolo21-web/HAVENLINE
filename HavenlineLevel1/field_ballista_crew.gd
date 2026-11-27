extends Node3D
## A fixed emplacement crew member operates in the turning deck's space.
const DEFENDER = preload("res://assets/settlement_people/survivor_male_01.glb")
var rig: Skeleton3D
var bones := {}

func _ready() -> void:
	var body := DEFENDER.instantiate() as Node3D
	add_child(body)
	rig = body.find_children("*", "Skeleton3D", true, false)[0]
	for index in rig.get_bone_count():
		bones[String(rig.get_bone_name(index))] = index

func operate(bow: Node3D, draw: float, kick: float, breath: float) -> void:
	if not rig:
		return
	rig.set_bone_pose_rotation(bones.Pelvis, Quaternion.from_euler(Vector3(.06,0.,-.035)))
	rig.set_bone_pose_rotation(bones.Chest, Quaternion.from_euler(Vector3(.07*breath-.19*kick,.11,-.06)))
	rig.set_bone_pose_rotation(bones.Head, Quaternion.from_euler(Vector3(-.03-.08*kick,-.20,.035)))
	# The right glove works the near winding drum; the other holds the stock.
	_place_palm("R", bow.to_global(Vector3(-.18,.14+.065*draw,-.39+.10*draw)))
	_place_palm("L", bow.to_global(Vector3(-.095,.16,-.29-.075*kick)))

func _place_palm(side: String, grip: Vector3) -> void:
	var arm: int = bones["UpperArm."+side]
	var forearm: int = bones["Forearm."+side]
	var hand: int = bones["Palm."+side]
	var shoulder := rig.get_bone_global_pose(arm).origin
	var upper := rig.get_bone_rest(forearm).origin
	var lower := rig.get_bone_rest(hand).origin
	var delta := rig.to_local(grip)-shoulder
	var axis := delta.normalized()
	var reach := clampf(delta.length(),.01,upper.length()+lower.length()-.001)
	var along := (upper.length_squared()-lower.length_squared()+reach*reach)/(2.*reach)
	var side_sign := 1. if side=="L" else -1.
	var bend := Vector3(side_sign*.72,-.7,-.6).slide(axis).normalized()
	var elbow := shoulder+axis*along+bend*sqrt(maxf(0.,upper.length_squared()-along*along))
	var palm := shoulder+axis*reach
	var upper_basis := Basis(Quaternion(upper.normalized(),(elbow-shoulder).normalized()))
	var lower_basis := Basis(Quaternion(lower.normalized(),(palm-elbow).normalized()))
	rig.set_bone_global_pose(arm, Transform3D(upper_basis,shoulder))
	rig.set_bone_global_pose(forearm, Transform3D(lower_basis,elbow))
	rig.set_bone_global_pose(hand, Transform3D(lower_basis,palm))
