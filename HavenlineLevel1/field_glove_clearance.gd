extends RefCounted
## Preserve the compact explorer's original elbow flex as its mitten passes
## the coat hem. The clip's authored upper-limb scales are 1 within 3e-7.

static func usable(basis: Basis) -> bool:
	return basis.is_finite() and absf(basis.determinant())>.00001 and basis.x.length_squared()>.0001 and basis.y.length_squared()>.0001 and basis.z.length_squared()>.0001

static func set_joint_rotation(rig: Skeleton3D, joint: int, basis: Basis) -> void:
	var parent:=rig.get_bone_global_pose(rig.get_bone_parent(joint)).basis
	if not usable(parent) or not usable(basis):return
	# Preserve the local translation and unit scale from the clip. Decomposing
	# a global transform after every step slowly introduces shear in the wrist.
	var local:=parent.orthonormalized().transposed()*basis.orthonormalized()
	rig.set_bone_pose_rotation(joint,local.get_rotation_quaternion().normalized())
	rig.set_bone_pose_scale(joint,Vector3.ONE)

static func solve(rig: Skeleton3D, actor: Node3D, ids: Array, body_width := 1., forward_wrist := 0.) -> void:
	var upper:=rig.get_bone_global_pose(ids[0])
	var lower:=rig.get_bone_global_pose(ids[1])
	var hand:=rig.get_bone_global_pose(ids[2])
	if not usable(rig.global_basis) or not usable(actor.global_basis):return
	if not upper.is_finite() or not lower.is_finite() or not hand.is_finite():return
	if not usable(upper.basis) or not usable(lower.basis) or not usable(hand.basis):
		for joint: int in ids: rig.reset_bone_pose(joint)
		return
	var shoulder:=actor.to_local(rig.to_global(upper.origin))
	var wrist:=actor.to_local(rig.to_global(hand.origin))
	var sign_x:=signf(shoulder.x)
	var level:=1.-smoothstep(.29,.46,absf(wrist.z))
	var band:=1.-smoothstep(.10,.29,absf(wrist.y-.56))
	var along:=1.-smoothstep(.23,.36,absf(wrist.z))
	var envelope:=(.416+.049*band*along)*body_width
	if forward_wrist>0.:
		var front_band:=smoothstep(.015,.08,wrist.z)*(1.-smoothstep(.218,.34,wrist.z))
		var coat_band:=1.-smoothstep(.145,.26,absf(wrist.y-.73))
		envelope=maxf(envelope,forward_wrist*front_band*coat_band)
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
	if not end.is_finite() or upper.origin.distance_squared_to(end)<.0000001:return
	var axis:=upper.origin.direction_to(end)
	var a:=upper.origin.distance_to(lower.origin)
	var b:=lower.origin.distance_to(hand.origin)
	if minf(a,b)<.001:return
	var d:=maxf(.0001,upper.origin.distance_to(end))
	var advance:=(a*a-b*b+d*d)/(2.*d)
	var pole:=(lower.origin-upper.origin).slide(axis)
	if pole.length_squared()<.000001:
		pole=(rig.global_basis.inverse()*actor.global_basis.z).slide(axis)
	var elbow:=upper.origin+axis*advance+pole.normalized()*sqrt(maxf(0.,a*a-advance*advance))
	if lower.origin.distance_squared_to(hand.origin)<.0000001 or elbow.distance_squared_to(end)<.0000001:return
	upper.basis=Basis(Quaternion(upper.origin.direction_to(lower.origin),upper.origin.direction_to(elbow)))*upper.basis
	lower.basis=Basis(Quaternion(lower.origin.direction_to(hand.origin),elbow.direction_to(end)))*lower.basis
	lower.origin=elbow
	hand.origin=end
	set_joint_rotation(rig,ids[0],upper.basis)
	set_joint_rotation(rig,ids[1],lower.basis)
	set_joint_rotation(rig,ids[2],hand.basis)
