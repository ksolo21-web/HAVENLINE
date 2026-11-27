extends RefCounted
## Two rigged palms follow the same physical shaft from wind-up through recoil.
const ApprovedTools := preload("res://weapon_orbit.gd")
const AXE_EDGE := ApprovedTools.AXE_EDGE
const PICK_TIP := ApprovedTools.PICK_TIP
const AXE_GRIPS := [Vector3(.397,-.18,0),Vector3(.484,-.54,0)]
const PICK_GRIPS := [Vector3(.208,.075,0),Vector3(.177,-.31,0)]
const TIMES := [0.0,.16,.35,.48,.61,.73,.86,1.0]
const AXE_SHAFT := [Vector3(.59,.77,.23),Vector3(.71,.62,.29),Vector3(.78,.55,.30),Vector3(.63,.73,.24),Vector3(.47,.86,.20),Vector3(.42,.88,.22),Vector3(.61,.76,.22),Vector3(.59,.77,.23)]
const AXE_CUT := [Vector3(.23,.13,.96),Vector3(.44,.15,.88),Vector3(.47,.10,.87),Vector3(.22,-.22,.95),Vector3(.10,-.32,.94),Vector3(-.26,-.35,.89),Vector3(.17,-.12,.97),Vector3(.23,.13,.96)]
const PICK_SHAFT := [Vector3(-.25,.92,.33),Vector3(-.38,.82,.43),Vector3(-.44,.76,.48),Vector3(-.22,.71,.67),Vector3(-.17,.745,.646),Vector3(-.21,.73,.64),Vector3(-.26,.85,.45),Vector3(-.25,.92,.33)]
const PICK_CUT := [Vector3(.55,-.21,.79),Vector3(.61,-.22,.76),Vector3(.65,-.32,.70),Vector3(.67,-.44,.60),Vector3(.65,-.41,.64),Vector3(.66,-.44,.61),Vector3(.54,-.35,.77),Vector3(.55,-.21,.79)]
const AXE_HOME := Vector3(-.035,.58,.32)
const PICK_HOME := Vector3(-.10,.68,.29)

static func _basis(shaft: Vector3, direction: Vector3) -> Basis:
	var y := shaft.normalized()
	var x := -direction.slide(y).normalized()
	return Basis(x,y,x.cross(y))

static func drive(actor: Node3D, tool: Node3D, phase: float, mining: bool, impact: Vector3) -> void:
	var p := clampf(phase,0.0,1.0)
	var pressure := smoothstep(.35,.63,p)*(1.0-smoothstep(.67,.94,p))
	var coil := smoothstep(.01,.31,p)*(1.0-smoothstep(.36,.56,p))
	var released_weight := smoothstep(.45,.59,p)*(1.0-smoothstep(.75,.91,p))
	var rig: Skeleton3D=actor.skeleton
	var pelvis: int=actor.bones.Pelvis
	# Give the working shaft space by shifting weight onto the rear heel.
	# The leg solver seats both soles after this small hip translation.
	rig.set_bone_pose_position(pelvis,rig.get_bone_rest(pelvis).origin+Vector3(0.,-.016*released_weight,-.11*released_weight))
	actor._bend("Pelvis",.017+.065*pressure,-.09*coil+.07*pressure)
	actor._bend("Chest",.035+(.25 if mining else .07)*pressure-.107*coil,-.24*coil+.13*pressure,-.05*coil)
	actor._bend("Head",.06-.15*pressure+.04*coil,.17*coil-.14*pressure)
	actor.forester_gait.update(phase,false)
	var shafts := PICK_SHAFT if mining else AXE_SHAFT
	var cuts := PICK_CUT if mining else AXE_CUT
	var grips := PICK_GRIPS if mining else AXE_GRIPS
	var grip_mid: Vector3 = (grips[0]+grips[1])*.5
	var size := .54 if mining else .48
	var striking_tip := PICK_TIP if mining else AXE_EDGE
	var at_impact := impact-_basis(shafts[4],cuts[4])*((striking_tip-grip_mid)*size)
	var home := PICK_HOME if mining else AXE_HOME
	var raised := Vector3(-.060,.93,.36) if mining else Vector3(.132,.748,.34)
	var positions := [home,home.lerp(raised,.50),raised,raised.lerp(at_impact,.44),at_impact,at_impact+Vector3(-.025,-.042,-.031),home.lerp(at_impact,.27),home]
	var i := 0
	while i+2<TIMES.size() and p>TIMES[i+1]: i+=1
	var t := (p-float(TIMES[i]))/float(TIMES[i+1]-TIMES[i])
	var left: Vector3 = positions[maxi(i-1,0)]
	var right: Vector3 = positions[mini(i+2,positions.size()-1)]
	var middle: Vector3 = (positions[i] as Vector3).cubic_interpolate(positions[i+1],left,right,t)
	if mining:
		# Keep the lower hand in front of its shoulder while bringing the
		# shaft back up. A folded arm has no stable elbow side at that point.
		middle.z+=.07*smoothstep(.66,.79,p)*(1.0-smoothstep(.82,.99,p))
		middle.x-=.10*smoothstep(.54,.65,p)*(1.0-smoothstep(.90,1.0,p))
	else:
		middle.z+=.135*smoothstep(.44,.57,p)*(1.0-smoothstep(.75,.87,p))
		# Open to the side as the blade comes out, keeping the rear half of the
		# axe head outside the forester's face during the return stroke.
		var withdraw := smoothstep(.57,.64,p)*(1.0-smoothstep(.76,.90,p))
		middle+=Vector3(.145,-.044,.028)*withdraw
	var spin := _basis(shafts[i],cuts[i]).slerp(_basis(shafts[i+1],cuts[i+1]),t)
	var tool_basis := spin.scaled(Vector3.ONE*size)
	# Keep both hands within bone reach by moving the whole held tool, so one
	# glove cannot silently slip away from the shaft when the other is extended.
	for pass_ in 4:
		for side_index in 2:
			var side := "L" if side_index==0 else "R"
			var wrist: Vector3 = middle+tool_basis*(grips[side_index]-grip_mid)
			var shoulder := rig.get_bone_global_pose(actor.bones["UpperArm."+side]).origin+rig.position
			var separation := wrist-shoulder
			var side_clearance := Vector2(separation.x,separation.y).length()
			var front_limit := lerpf(.13,-.23,smoothstep(.045,.21,side_clearance))
			var front_offset := maxf(0.,front_limit-separation.z)
			middle.z+=front_offset
			separation.z+=front_offset
			var maximum := rig.get_bone_rest(actor.bones["Forearm."+side]).origin.length()+rig.get_bone_rest(actor.bones["Palm."+side]).origin.length()-.018
			middle-=separation-separation.limit_length(maximum)
	tool.transform=Transform3D(tool_basis,middle-tool_basis*grip_mid)
	var elbow_hint := Vector3(.87,-.21,.41) if mining else Vector3(.56,-.86,-.21)
	for side_index in 2:
		var side := "L" if side_index==0 else "R"
		var palm: Vector3 = tool.transform*grips[side_index]-rig.position
		_fit_arm(actor,side,palm,spin,elbow_hint)

static func _fit_arm(actor: Node3D, side: String, palm: Vector3, held_basis: Basis, elbow_hint: Vector3) -> void:
	var rig: Skeleton3D = actor.skeleton
	var arm: int = actor.bones["UpperArm."+side]
	var forearm: int = actor.bones["Forearm."+side]
	var hand: int = actor.bones["Palm."+side]
	var shoulder := rig.get_bone_global_pose(arm).origin
	var upper := rig.get_bone_rest(forearm).origin
	var lower := rig.get_bone_rest(hand).origin
	var reach := palm-shoulder
	var distance := clampf(reach.length(),.03,upper.length()+lower.length()-.001)
	var axis := reach.normalized()
	var along := (upper.length_squared()-lower.length_squared()+distance*distance)/(2.0*distance)
	var sign_ := 1.0 if side=="L" else -1.0
	var pole := (elbow_hint*Vector3(sign_,1,1)).slide(axis).normalized()
	var elbow := shoulder+axis*along+pole*sqrt(maxf(0.0,upper.length_squared()-along*along))
	var plane := axis.cross(pole).normalized()*sign_
	var arm_basis := _frame((elbow-shoulder).normalized(),plane)*_frame(upper.normalized(),Vector3.FORWARD).transposed()
	var fore_basis := _frame((palm-elbow).normalized(),plane)*_frame(lower.normalized(),Vector3.FORWARD).transposed()
	var hand_basis := Basis(-sign_*held_basis.y,sign_*held_basis.z,-held_basis.x)
	rig.set_bone_global_pose(arm,Transform3D(arm_basis,shoulder))
	rig.set_bone_global_pose(forearm,Transform3D(fore_basis,elbow))
	rig.set_bone_global_pose(hand,Transform3D(hand_basis,palm))

static func _frame(axis: Vector3, hint: Vector3) -> Basis:
	var across := hint.slide(axis).normalized()
	return Basis(across,axis,across.cross(axis))
