extends RefCounted
## Calibrated to the forester's compact legs. Passage is animated in place;
## the world mover advances the same distance per cycle used by the stance foot.
const STRIDE := .94
# Each entry is (sole Y, sole Z, toe weight) relative to its ankle. The points
# span the actual sole's supporting hull over the heel-to-toe pitch range.
const FORESTER_SOLES := [
	[Vector3(-0.10423,-0.14002,0.00000), Vector3(-0.10423,0.11562,0.18798), Vector3(-0.10423,0.11485,0.17620), Vector3(-0.10423,0.11408,0.16470), Vector3(-0.10423,0.12409,0.33171), Vector3(-0.10423,0.14103,0.65226), Vector3(-0.10423,0.12486,0.34586), Vector3(-0.10423,0.12948,0.43263), Vector3(-0.10500,0.01398,0.00000), Vector3(-0.10423,0.12640,0.37422), Vector3(-0.10423,0.10638,0.06762), Vector3(-0.10423,0.13641,0.56542), Vector3(-0.10423,0.13256,0.49159), Vector3(-0.10423,0.13025,0.44740), Vector3(-0.10423,0.13333,0.50645), Vector3(-0.10423,0.14565,0.73477), Vector3(-0.10423,0.19802,1.00000)],
	[Vector3(-0.10423,-0.13848,0.00000), Vector3(-0.10500,-0.13463,0.00000), Vector3(-0.10500,0.05479,0.00000), Vector3(-0.10423,0.10638,0.06762), Vector3(-0.10423,0.12178,0.29011), Vector3(-0.10423,0.13641,0.56542), Vector3(-0.10423,0.14488,0.72138), Vector3(-0.10423,0.11485,0.17620), Vector3(-0.10423,0.11716,0.21231), Vector3(-0.10423,0.13179,0.47673), Vector3(-0.10423,0.14103,0.65226), Vector3(-0.10423,0.12409,0.33171), Vector3(-0.10423,0.12486,0.34586), Vector3(-0.10423,0.13333,0.50645), Vector3(-0.10423,0.19802,1.00000)],
]

var legs := []
var skeleton: Skeleton3D

func bind(rig: Skeleton3D) -> void:
	skeleton=rig
	for side in ["L","R"]:
		var ids := []
		for bone in ["Thigh","Shin","Foot","Toe"]:
			ids.append(rig.find_bone(bone+"."+side))
		legs.append(ids)

func _pitches(phase: float) -> Vector4:
	# z offset, clearance, foot pitch, forefoot pitch.
	if phase < .50:
		var t := phase*2.
		return Vector4(STRIDE*(.25-phase),0.,-.21*(1.-smoothstep(0.,.33,t))+.29*smoothstep(.61,1.,t),-.24*smoothstep(.61,1.,t))
	var t := (phase-.50)*2.
	var step := t*t*(3.-2.*t)
	return Vector4(STRIDE*(-.25+.5*(2.*step-t)),.095*pow(sin(t*PI),1.65),lerpf(.29,-.21,step),-.24*(1.-smoothstep(0.,.52,t)))

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

func update(phase: float, moving: bool) -> void:
	var targets := []
	var angles := []
	var position := Vector3.ZERO
	if moving: position.x=.009*cos(phase*TAU)
	var lowest := -0.009 if moving else 0.
	for side in 2:
		var ids: Array = legs[side]
		var p := _pitches(fposmod(phase+side*.5,1.)) if moving else Vector4.ZERO
		var ankle := skeleton.get_bone_global_rest(ids[2]).origin
		ankle.z+=p.x
		ankle.y=_sole_drop(side,p.z,p.w)+p.y
		var hip := skeleton.get_bone_global_pose(ids[0]).origin+position
		var span := skeleton.get_bone_rest(ids[1]).origin.length()+skeleton.get_bone_rest(ids[2]).origin.length()-.004
		var horizontal := Vector2(ankle.x-hip.x,ankle.z-hip.z).length_squared()
		lowest=minf(lowest,ankle.y+sqrt(maxf(.001,span*span-horizontal))-hip.y)
		targets.append(ankle)
		angles.append(Vector2(p.z,p.w))
	position.y=lowest
	skeleton.position=position
	for side in 2:
		_seat_leg(legs[side],targets[side]-position,angles[side].x,angles[side].y)
