extends RefCounted
## Calibrated to the forester's compact legs. Passage is animated in place;
## the world mover advances the same distance per cycle used by the stance foot.
const STRIDE := .94
const JOG_STRIDE := 1.82
const JOG_SUPPORT := .31
# Each entry is (sole Y, sole Z, toe weight) relative to its ankle. The points
# span the actual sole's supporting hull over the heel-to-toe pitch range.
const FORESTER_SOLES := [
	[Vector3(-0.10423,-0.14002,0.00000), Vector3(-0.10423,0.11562,0.18798), Vector3(-0.10423,0.11485,0.17620), Vector3(-0.10423,0.11408,0.16470), Vector3(-0.10423,0.12409,0.33171), Vector3(-0.10423,0.14103,0.65226), Vector3(-0.10423,0.12486,0.34586), Vector3(-0.10423,0.12948,0.43263), Vector3(-0.10500,0.01398,0.00000), Vector3(-0.10423,0.12640,0.37422), Vector3(-0.10423,0.10638,0.06762), Vector3(-0.10423,0.13641,0.56542), Vector3(-0.10423,0.13256,0.49159), Vector3(-0.10423,0.13025,0.44740), Vector3(-0.10423,0.13333,0.50645), Vector3(-0.10423,0.14565,0.73477), Vector3(-0.10423,0.19802,1.00000)],
	[Vector3(-0.10423,-0.13848,0.00000), Vector3(-0.10500,-0.13463,0.00000), Vector3(-0.10500,0.05479,0.00000), Vector3(-0.10423,0.10638,0.06762), Vector3(-0.10423,0.12178,0.29011), Vector3(-0.10423,0.13641,0.56542), Vector3(-0.10423,0.14488,0.72138), Vector3(-0.10423,0.11485,0.17620), Vector3(-0.10423,0.11716,0.21231), Vector3(-0.10423,0.13179,0.47673), Vector3(-0.10423,0.14103,0.65226), Vector3(-0.10423,0.12409,0.33171), Vector3(-0.10423,0.12486,0.34586), Vector3(-0.10423,0.13333,0.50645), Vector3(-0.10423,0.19802,1.00000)],
]

# Full-stride forester knee landmarks. The slopes are single-valued at each
# key and reverse only at load, push-off and the peak of recovery.
const RUN_KNEE := [
	Vector2(0.,17.),Vector2(.10,33.),Vector2(.16,37.),Vector2(.26,25.),
	Vector2(.36,15.),Vector2(.40,19.),Vector2(.48,41.),Vector2(.57,78.),
	Vector2(.68,99.),Vector2(.77,84.),Vector2(.86,55.),Vector2(.94,23.),Vector2(.97,15.),Vector2(1.,17.)]

func _knee_at(p: float) -> float:
	var i := 0
	while i+2 < RUN_KNEE.size() and p > RUN_KNEE[i+1].x: i+=1
	var a:Vector2=RUN_KNEE[i]
	var b:Vector2=RUN_KNEE[i+1]
	var prev:Vector2=RUN_KNEE[i-1] if i>0 else Vector2(-.03,15.)
	var following:Vector2=RUN_KNEE[i+2] if i+2<RUN_KNEE.size() else Vector2(1.1,33.)
	var mid := (b.y-a.y)/(b.x-a.x)
	var left := (a.y-prev.y)/(a.x-prev.x)
	var right := (following.y-b.y)/(following.x-b.x)
	var start := 2.*left*mid/(left+mid) if left*mid>0. else 0.
	var end := 2.*right*mid/(right+mid) if right*mid>0. else 0.
	var t := (p-a.x)/(b.x-a.x)
	var t2 := t*t
	var t3 := t2*t
	return (2.*t3-3.*t2+1.)*a.y+(t3-2.*t2+t)*(b.x-a.x)*start+(-2.*t3+3.*t2)*b.y+(t3-t2)*(b.x-a.x)*end

var legs := []
var skeleton: Skeleton3D

func bind(rig: Skeleton3D) -> void:
	skeleton=rig
	for side in ["L","R"]:
		var ids := []
		for bone in ["Thigh","Shin","Foot","Toe"]:
			ids.append(rig.find_bone(bone+"."+side))
		legs.append(ids)

# A worker changes direction by moving one boot and then the other. Keep each
# supporting ankle in world space while the hips turn around the grounded boot.
var pivot_elapsed := -1.0
var pivot_heading := 0.0
var pivot_angle := 0.0
var pivot_first := 0
var pivot_start: Array[Transform3D] = []
var pivot_finish: Array[Transform3D] = []
var pivot_toes: Array[Quaternion] = []
var pivot_frame := false
var move_phase := 0.
var move_pace := 0.
const PIVOT_STEP := .125

# An ankle can start a turn a full stride behind its hip. Select the first
# stepping boot and heading together, keeping both winter boots in separate
# lanes throughout the turn instead of crossing the fixed supporting calf.
func _turn_width(actor: Node3D, angle: float, first: int) -> float:
	var end_body:=Transform3D(Basis(Vector3.UP,pivot_heading+angle),actor.global_position)
	var ends: Array[Vector3]=[]
	for side in 2:
		ends.append(end_body*skeleton.get_bone_global_rest(legs[side][2]).origin)
	var clearance:=INF
	for frame in range(1,15):
		var t:=float(frame)/15.
		var right:=Basis(Vector3.UP,pivot_heading+angle*smoothstep(0.,1.,t)).x
		var points: Array[Vector3]=[]
		for side in 2:
			var step:=clampf(2.*t-(0. if side==first else 1.),0.,1.)
			points.append(pivot_start[side].origin.lerp(ends[side],smoothstep(0.,1.,step)))
		clearance=minf(clearance,right.dot(points[0]-points[1]))
	return clearance

func turn_towards(actor: Node3D, desired: float, dt: float, starting := false) -> bool:
	if pivot_elapsed < 0.0:
		var angle := angle_difference(actor.rotation.y,desired)
		if absf(angle) < deg_to_rad(18. if starting else 48.): return false
		pivot_heading = actor.rotation.y
		pivot_angle = clampf(angle, -deg_to_rad(75.), deg_to_rad(75.))
		pivot_first = 0 if pivot_angle > 0. else 1
		pivot_start.clear()
		pivot_finish.clear()
		pivot_toes.clear()
		for side in 2:
			var foot: int = legs[side][2]
			var source := skeleton.global_transform * skeleton.get_bone_global_pose(foot)
			pivot_start.append(source)
			pivot_toes.append(skeleton.get_bone_pose_rotation(legs[side][3]))
		var requested:=pivot_angle
		var best_width:=-INF
		var best_angle:=requested
		var best_first:=pivot_first
		for fraction: float in [1.,.78,.58,.40]:
			for first in 2:
				var width:=_turn_width(actor,requested*fraction,first)
				# Prefer to leave the lower boot in contact when both turns fit.
				var height_bonus:=clampf(pivot_start[first].origin.y-pivot_start[1-first].origin.y,-.08,.08)*.12
				if width+height_bonus>best_width:
					best_width=width+height_bonus
					best_angle=requested*fraction
					best_first=first
			if best_width>=.285:break
		pivot_angle=best_angle
		pivot_first=best_first
		var finish_body:=Transform3D(Basis(Vector3.UP,pivot_heading+pivot_angle),actor.global_position)
		for side in 2:
			var end_foot:int=legs[side][2]
			var rest:=skeleton.get_bone_global_rest(end_foot).origin
			rest.y=_sole_drop(side,0.,0.)+.003
			pivot_finish.append(finish_body*Transform3D(Basis.IDENTITY,rest))
		pivot_elapsed = 0.
		actor.pose("idle",0.)
	pivot_frame = true
	pivot_elapsed = minf(2.*PIVOT_STEP,pivot_elapsed+dt)
	var whole := pivot_elapsed/(2.*PIVOT_STEP)
	actor.rotation.y = pivot_heading + pivot_angle*smoothstep(0.,1.,whole)
	for side in 2:
		var step := clampf(pivot_elapsed/PIVOT_STEP-(0. if side==pivot_first else 1.),0.,1.)
		var blend := smoothstep(0.,1.,step)
		var pose := pivot_start[side].interpolate_with(pivot_finish[side],blend)
		pose.origin.y += .065*sin(PI*blend)
		var local := skeleton.global_transform.affine_inverse() * pose
		_seat_leg(legs[side],local.origin,0.,0.)
		var foot: int = legs[side][2]
		skeleton.set_bone_global_pose(foot,local)
		skeleton.set_bone_pose_rotation(legs[side][3],pivot_toes[side].slerp(Quaternion.IDENTITY,blend))
	if pivot_elapsed >= 2.*PIVOT_STEP: pivot_elapsed = -1.
	return true

func stride_for_speed(speed: float) -> float:
	return lerpf(STRIDE,JOG_STRIDE,smoothstep(.70,3.60,speed))

func _pitches(phase: float, pace: float) -> Vector4:
	# While loaded the ankle moves backwards at exactly the actor's advance.
	# After toe-off the short lower leg folds under the coat, then reaches again.
	var run := smoothstep(.70,2.65,pace)
	var stride := stride_for_speed(pace)
	var support := lerpf(.53,JOG_SUPPORT,run)
	var half_sweep := .5*stride*support
	var heel := lerpf(-.22,-.35,run)
	var push := lerpf(.35,.66,run)
	if phase < support:
		var t := phase/support
		var pitch := heel*(1.-smoothstep(0.,.28,t)) + push*smoothstep(.51,1.,t)
		# Countertranslate the ankle as the contact migrates across the real
		# leather sole. Otherwise a planted toe slides when the boot pitches.
		var heel_roll := lerpf(.028,.0441,run)
		var toe_roll := lerpf(.040,.0685,run)
		var roll := -heel_roll*(1.-smoothstep(0.,.28,t))+toe_roll*smoothstep(.51,1.,t)
		return Vector4(half_sweep-stride*phase+roll,.003,pitch,-push*.79*smoothstep(.52,1.,t))
	var t := (phase-support)/(1.-support)
	var swing := t-.072*run*sin(PI*t)
	var reach := smoothstep(0.,1.,swing)
	var clearance := lerpf(.09,.100,run)*pow(sin(PI*swing),1.5)
	# The heel follows through behind the body after the toe leaves the snow.
	var trail := lerpf(.028,.030,run)*sin(PI*clampf(t/.43,0.,1.))
	var toe_offset := lerpf(.040,.0685,run)
	var heel_offset := lerpf(.028,.0441,run)
	var roll := lerpf(toe_offset,-heel_offset,reach)
	# The just-unloaded toe finishes moving backward as it clears the snow.
	var release := minf(phase-support,.025)*(1.-smoothstep(.025,.12,phase-support))
	var z := lerpf(-half_sweep,half_sweep,reach)-trail+roll-stride*release
	var foot_pitch := lerpf(push+.11*sin(PI*t),heel,lerpf(reach,smoothstep(0.,.88,t),run))
	return Vector4(z,clearance+.003,foot_pitch,-push*.79*(1.-smoothstep(0.,.43,t)))

func _sole_drop(side: int, pitch: float, toe_pitch: float) -> float:
	var toe_rest := skeleton.get_bone_rest(legs[side][3]).origin
	var pivot := Vector2(toe_rest.y,toe_rest.z)
	var low := INF
	for hint: Vector3 in FORESTER_SOLES[side]:
		var point := Vector2(hint.x,hint.y)
		var turned := pivot+(point-pivot).rotated(toe_pitch)
		low=minf(low,point.lerp(turned,hint.z).rotated(pitch).x)
	return -low

func _seat_leg(ids: Array, ankle: Vector3, pitch: float, toe_pitch: float) -> void:
	var hip := skeleton.get_bone_global_pose(ids[0]).origin
	var upper := skeleton.get_bone_rest(ids[1]).origin
	var lower := skeleton.get_bone_rest(ids[2]).origin
	var line := ankle-hip
	var distance := clampf(line.length(),.001,upper.length()+lower.length()-.0001)
	var axis := line.normalized()
	var along := (upper.length_squared()-lower.length_squared()+distance*distance)/(2.*distance)
	var forward := Vector3.BACK.slide(axis).normalized()
	var knee := hip+axis*along+forward*sqrt(maxf(0.,upper.length_squared()-along*along))
	skeleton.set_bone_global_pose(ids[0],Transform3D(Basis(Quaternion(upper.normalized(),(knee-hip).normalized())),hip))
	skeleton.set_bone_global_pose(ids[1],Transform3D(Basis(Quaternion(lower.normalized(),(ankle-knee).normalized())),knee))
	skeleton.set_bone_global_pose(ids[2],Transform3D(Basis(Vector3.RIGHT,pitch),ankle))
	skeleton.set_bone_pose_rotation(ids[3],Quaternion(Vector3.RIGHT,toe_pitch))

func update(phase: float, moving: bool, pace := 1.8) -> void:
	move_phase=phase
	move_pace=pace if moving else 0.
	var targets := []
	var angles := []
	var position := Vector3.ZERO
	if moving: position.x=.009*cos(phase*TAU)
	var u := fposmod(phase*2.,1.)
	var run := smoothstep(.70,2.65,pace) if moving else 0.
	# Compress at weight acceptance and extend through push-off.
	var lowest := lerpf(-.012,-.023,run)*pow(sin(PI*clampf(u/.53,0.,1.)),2.) if moving else 0.
	lowest+=.065*run
	for side in 2:
		var ids: Array = legs[side]
		var p := _pitches(fposmod(phase+side*.5,1.),pace) if moving else Vector4.ZERO
		var ankle := skeleton.get_bone_global_rest(ids[2]).origin
		ankle.z+=p.x
		ankle.y=_sole_drop(side,p.z,p.w)+p.y
		var hip := skeleton.get_bone_global_pose(ids[0]).origin+position
		var upper := skeleton.get_bone_rest(ids[1]).origin.length()
		var lower := skeleton.get_bone_rest(ids[2]).origin.length()
		var k := deg_to_rad(_knee_at(fposmod(phase+side*.5,1.)))
		var span := lerpf(upper+lower-.004,sqrt(upper*upper+lower*lower+2.*upper*lower*cos(k)),run)
		var horizontal := Vector2(ankle.x-hip.x,ankle.z-hip.z).length_squared()
		var foot_phase := fposmod(phase+side*.5,1.)
		var support := lerpf(.53,JOG_SUPPORT,run)
		# The paired hips share one height. Blend away from the support-length
		# constraint only after toe-off and rejoin it before the next heel strike.
		var release := smoothstep(support,support+.095,foot_phase)*(1.-smoothstep(.89,1.,foot_phase))
		var ceiling_span := lerpf(span,upper+lower-.0015,release*run)
		lowest=minf(lowest,ankle.y+sqrt(maxf(.001,ceiling_span*ceiling_span-horizontal))-hip.y)
		targets.append(ankle)
		angles.append(Vector2(p.z,p.w))
	position.y=lowest
	skeleton.position=position
	for side in 2:
		var ankle:Vector3=targets[side]-position
		var f := fposmod(phase+side*.5,1.)
		var support := lerpf(.53,JOG_SUPPORT,run)
		if moving and run > .001 and f > support:
			var ids:Array=legs[side]
			var hip := skeleton.get_bone_global_pose(ids[0]).origin
			var upper := skeleton.get_bone_rest(ids[1]).origin.length()
			var lower := skeleton.get_bone_rest(ids[2]).origin.length()
			var d2 := upper*upper+lower*lower+2.*upper*lower*cos(deg_to_rad(_knee_at(f)))
			var horizontal := Vector2(ankle.x-hip.x,ankle.z-hip.z).length_squared()
			var weight := run*smoothstep(support,support+.032,f)*(1.-smoothstep(.975,1.,f))
			var sole_floor := _sole_drop(side,angles[side].x,angles[side].y)+.003-position.y
			var ideal_y := hip.y-sqrt(maxf(.001,d2-horizontal))
			var clearance := .065*pow(maxf(0.,sin(PI*(f-support)/(1.-support))),1.4)*(1.-smoothstep(.56,.65,f))
			# Keep the recovering heel clear until the final approach to contact.
			var heel_swing := smoothstep(.70,.81,f)*(1.-smoothstep(.865,.98,f))
			clearance += .032*heel_swing
			var airborne_y := maxf(sole_floor+clearance,ideal_y)
			# Recover behind the body before swinging through. Preserve limb
			# length as the heel rises, so swing clearance cannot lock the knee.
			if airborne_y > ideal_y and (f < .65 or f > .72):
				var dz := sqrt(maxf(0.,d2-pow(ankle.x-hip.x,2.)-pow(airborne_y-hip.y,2.)))
				ankle.z=lerpf(ankle.z,hip.z+dz*(-1. if f<.65 else 1.),weight)
			ankle.y=lerpf(ankle.y,airborne_y,weight)
		_seat_leg(legs[side],ankle,angles[side].x,angles[side].y)

var tread = preload("res://field_tread_samples.gd").new()
var marker: Array[int] = [-1,-1]
var planted: Array[Vector3] = [Vector3.ZERO,Vector3.ZERO]
var correction: Array[Vector3] = [Vector3.ZERO,Vector3.ZERO]
var previous_feet := Vector3.INF
var foot_heading: Array[float] = [0.,0.]
var previous_points := PackedVector3Array()

func settle_contact(dt: float, actor: Node3D) -> void:
	if tread.soles.is_empty(): return
	var feet := actor.global_position
	if previous_feet.distance_squared_to(feet)>1.:
		marker.assign([-1,-1])
		correction.assign([Vector3.ZERO,Vector3.ZERO])
		previous_points.clear()
	previous_feet=feet
	var support:=lerpf(.53,JOG_SUPPORT,smoothstep(.70,2.65,move_pace))
	for side in 2:
		var foot: int=legs[side][2]
		var rot:=skeleton.get_bone_global_pose(foot)
		var phase:=fposmod(move_phase+side*.5,1.)
		if marker[side]<0:
			foot_heading[side]=actor.rotation.y if previous_points.is_empty() else rotate_toward(foot_heading[side],actor.rotation.y,dt*10.)
		var yaw:=angle_difference(actor.rotation.y,foot_heading[side])
		var axis:Vector3=(skeleton.global_basis.inverse()*Vector3.UP).normalized()
		rot.basis=Basis(axis,yaw)*rot.basis
		skeleton.set_bone_global_pose(foot,rot)
	var points: PackedVector3Array=tread.points()
	var low: Array[int]=tread.lowest(points)
	var goals: Array[Vector3]=[]
	var boot_bases: Array[Basis]=[]
	var spare_height:=0.
	for side in 2:
		var ids: Array=legs[side]
		var boot:=skeleton.get_bone_global_pose(ids[2])
		var at:=skeleton.to_global(boot.origin)
		var hip:=skeleton.to_global(skeleton.get_bone_global_pose(ids[0]).origin)
		var knee:=skeleton.to_global(skeleton.get_bone_global_pose(ids[1]).origin)
		var idx:=marker[side]
		var phase:=fposmod(move_phase+side*.5,1.)
		var rising:=phase>support+.010 and phase<.94
		var lift:=.021*smoothstep(support+.005,support+.045,phase)*(1.-smoothstep(.87,.95,phase)) if rising else 0.
		# The ankle starts lifting before the toe has left the snow. Keep
		# the toe fixed across that final frame of push-off.
		if maxf(lift,points[low[side]].y-feet.y)>.009:
			marker[side]=-1
			correction[side]=correction[side].move_toward(Vector3.ZERO,dt*2.2)
		else:
			if idx<0 or points[idx].y-points[low[side]].y>.009:
				var rolling:=idx>=0 and not previous_points.is_empty()
				idx=low[side]
				marker[side]=idx
				planted[side]=previous_points[idx] if rolling else points[idx]+correction[side]
			correction[side]=(planted[side]-points[idx]).slide(Vector3.UP).limit_length(.18)
		var goal:=at+correction[side]
		if rising:
			# Release the sole visibly as body speed changes into the next step.
			goal.y+=maxf(0.,feet.y+lift-points[low[side]].y)
		goals.append(goal)
		boot_bases.append(boot.basis)
		var length:=hip.distance_to(knee)+knee.distance_to(at)
		var runout:=(goal-hip).slide(Vector3.UP).length_squared()
		spare_height=minf(spare_height,goal.y+sqrt(maxf(.001,length*length-runout-.00015))-hip.y)
	# Preserve the occupied supporting shoe on directional starts. Steer the
	# recovering boot into its own lane before it comes back to the ground.
	var local_l:=actor.to_local(goals[0])
	var local_r:=actor.to_local(goals[1])
	var needed:=.297-.06*smoothstep(.18,.40,absf(local_l.z-local_r.z))-(local_l.x-local_r.x)
	if needed>0. and (marker[0]<0 or marker[1]<0):
		var swing:=0 if marker[0]<0 and (marker[1]>=0 or goals[0].y>goals[1].y) else 1
		var spread:=actor.global_basis.x.normalized()*needed*(1. if swing==0 else -1.)
		goals[swing]+=spread
	# A sideways or braking step must release its toe before it can drag
	# the hips down towards the floor.
	skeleton.global_position.y+=maxf(-.014,spare_height)
	for side in 2:
		var ids: Array=legs[side]
		var toe:=skeleton.get_bone_pose_rotation(ids[3])
		_seat_leg(ids,skeleton.to_local(goals[side]),0.,0.)
		var ankle:=skeleton.get_bone_global_pose(ids[2])
		ankle.basis=boot_bases[side]
		skeleton.set_bone_global_pose(ids[2],ankle)
		skeleton.set_bone_pose_rotation(ids[3],toe)
	previous_points=tread.points()
