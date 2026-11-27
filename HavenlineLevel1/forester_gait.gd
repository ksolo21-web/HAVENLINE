extends RefCounted
## Calibrated to the forester's compact legs. Passage is animated in place;
## the world mover advances the same distance per cycle used by the stance foot.
const STRIDE := .94
const SPRINT_STRIDE := 2.22
# Each entry is (sole Y, sole Z, toe weight) relative to its ankle. The points
# span the actual sole's supporting hull over the heel-to-toe pitch range.
const FORESTER_SOLES := [
	[Vector3(-0.10423,-0.14002,0.00000), Vector3(-0.10423,0.11562,0.18798), Vector3(-0.10423,0.11485,0.17620), Vector3(-0.10423,0.11408,0.16470), Vector3(-0.10423,0.12409,0.33171), Vector3(-0.10423,0.14103,0.65226), Vector3(-0.10423,0.12486,0.34586), Vector3(-0.10423,0.12948,0.43263), Vector3(-0.10500,0.01398,0.00000), Vector3(-0.10423,0.12640,0.37422), Vector3(-0.10423,0.10638,0.06762), Vector3(-0.10423,0.13641,0.56542), Vector3(-0.10423,0.13256,0.49159), Vector3(-0.10423,0.13025,0.44740), Vector3(-0.10423,0.13333,0.50645), Vector3(-0.10423,0.14565,0.73477), Vector3(-0.10423,0.19802,1.00000)],
	[Vector3(-0.10423,-0.13848,0.00000), Vector3(-0.10500,-0.13463,0.00000), Vector3(-0.10500,0.05479,0.00000), Vector3(-0.10423,0.10638,0.06762), Vector3(-0.10423,0.12178,0.29011), Vector3(-0.10423,0.13641,0.56542), Vector3(-0.10423,0.14488,0.72138), Vector3(-0.10423,0.11485,0.17620), Vector3(-0.10423,0.11716,0.21231), Vector3(-0.10423,0.13179,0.47673), Vector3(-0.10423,0.14103,0.65226), Vector3(-0.10423,0.12409,0.33171), Vector3(-0.10423,0.12486,0.34586), Vector3(-0.10423,0.13333,0.50645), Vector3(-0.10423,0.19802,1.00000)],
]

# Full-stride forester knee landmarks. The slopes are single-valued at each
# key and reverse only at load, push-off and the peak of recovery.
const RUN_KNEE := [
	Vector2(0.,18.),Vector2(.10,39.),Vector2(.15,43.5),Vector2(.235,27.),
	Vector2(.325,14.),Vector2(.36,15.),Vector2(.45,41.),Vector2(.55,90.),
	Vector2(.65,119.),Vector2(.75,100.),Vector2(.85,65.),Vector2(.94,22.),Vector2(.97,15.),Vector2(1.,18.)]

func _knee_at(p: float) -> float:
	var i := 0
	while i+2 < RUN_KNEE.size() and p > RUN_KNEE[i+1].x: i+=1
	var a:Vector2=RUN_KNEE[i]
	var b:Vector2=RUN_KNEE[i+1]
	var prev:Vector2=RUN_KNEE[i-1] if i>0 else Vector2(-.03,15.)
	var following:Vector2=RUN_KNEE[i+2] if i+2<RUN_KNEE.size() else Vector2(1.1,39.)
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

func stride_for_speed(speed: float) -> float:
	return lerpf(STRIDE,SPRINT_STRIDE,smoothstep(.85,5.8,speed))

func _pitches(phase: float, pace: float) -> Vector4:
	# While loaded the ankle moves backwards at exactly the actor's advance.
	# After toe-off the short lower leg folds under the coat, then reaches again.
	var run := smoothstep(.85,5.8,pace)
	var stride := stride_for_speed(pace)
	var support := lerpf(.53,.235,run)
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
	var targets := []
	var angles := []
	var position := Vector3.ZERO
	if moving: position.x=.009*cos(phase*TAU)
	var u := fposmod(phase*2.,1.)
	var run := smoothstep(.85,5.8,pace) if moving else 0.
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
		var support := lerpf(.53,.235,run)
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
		var support := lerpf(.53,.235,run)
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
			var airborne_y := maxf(sole_floor+clearance,ideal_y)
			# Recover behind the body before swinging through. Preserve limb
			# length as the heel rises, so swing clearance cannot lock the knee.
			if f < .65 and airborne_y > ideal_y:
				var dz := sqrt(maxf(0.,d2-pow(ankle.x-hip.x,2.)-pow(airborne_y-hip.y,2.)))
				ankle.z=lerpf(ankle.z,hip.z-dz,weight)
			ankle.y=lerpf(ankle.y,airborne_y,weight)
		_seat_leg(legs[side],ankle,angles[side].x,angles[side].y)
