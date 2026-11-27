extends RefCounted
## Horizontal wrist sweep at the outer edge of each outfit's hip gear (metres).
## Measurements include the real mitten and bent finger surfaces.
const SWEEP := [0., .416, .393, .454, .401]
const HIP_GEAR := [0., .049, .111, .053, .073]

static func solve(rig: Skeleton3D, actor: Node3D, ids: Array, role: int) -> void:
	var upper:=rig.get_bone_global_pose(ids[0])
	var lower:=rig.get_bone_global_pose(ids[1])
	var hand:=rig.get_bone_global_pose(ids[2])
	var shoulder:=actor.to_local(rig.to_global(upper.origin))
	var wrist:=actor.to_local(rig.to_global(hand.origin))
	var sign_x:=signf(shoulder.x)
	var level:=1.-smoothstep(.29,.46,absf(wrist.z))
	# The winter gear occupies a local band at belt height. The mitten
	# passes behind the short parka hem; the other rigs have a rigid cup.
	var band:=1.-smoothstep(.10,.29,absf(wrist.y-(.56 if role==1 else .91)))
	var along:=1.-smoothstep(.23,.36,absf(wrist.z-(0. if role==1 else .015)))
	var envelope:=float(SWEEP[role])+float(HIP_GEAR[role])*band*along
	# The hanging steel mug reaches below the main belt on these two
	# coats. The left thumb passes its rim as the braking arm comes down.
	if sign_x>0. and role in [2,4]:
		var lower_band:=1.-smoothstep(.044,.115,absf(wrist.y-(.70 if role==2 else .59)))
		var aft:=1.-smoothstep(.05,.14,absf(wrist.z+.15))
		var slow:=1.-smoothstep(1.8,3.4,(actor as CharacterBody3D).velocity.length())
		envelope+=.026*lower_band*aft*slow
	var missing:=maxf(0.,envelope-sign_x*wrist.x)*level
	if missing<.00005:return
	var goal:=wrist+Vector3.RIGHT*sign_x*missing
	# Preserve the incoming elbow bend while redirecting the arm through
	# the clear lateral arc. Straightening here loses the running pump.
	var reach:=shoulder.distance_to(wrist)
	var span:=goal-shoulder
	var plane:=Vector2(span.y,span.z).limit_length(sqrt(maxf(0.,reach*reach-span.x*span.x)))
	goal=shoulder+Vector3(span.x,plane.x,plane.y)
	var end:=rig.to_local(actor.to_global(goal))
	var axis:=upper.origin.direction_to(end)
	var a:=upper.origin.distance_to(lower.origin)
	var b:=lower.origin.distance_to(hand.origin)
	var d:=maxf(.0001,upper.origin.distance_to(end))
	var advance:=(a*a-b*b+d*d)/(2.*d)
	var pole:=(lower.origin-upper.origin).slide(axis)
	if pole.length_squared()<.000001:
		pole=(rig.global_basis.inverse()*actor.global_basis.z).slide(axis)
	var elbow:=upper.origin+axis*advance+pole.normalized()*sqrt(maxf(0.,a*a-advance*advance))
	upper.basis=Basis(Quaternion(upper.origin.direction_to(lower.origin),upper.origin.direction_to(elbow)))*upper.basis
	lower.basis=Basis(Quaternion(lower.origin.direction_to(hand.origin),elbow.direction_to(end)))*lower.basis
	lower.origin=elbow
	hand.origin=end
	rig.set_bone_global_pose(ids[0],upper)
	rig.set_bone_global_pose(ids[1],lower)
	rig.set_bone_global_pose(ids[2],hand)
