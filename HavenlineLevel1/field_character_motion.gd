extends RefCounted
## Character 1 upper-body actions over the grounded field gait. Actor-local +Z
## is forward. The caller owns movement, actions, collision, and every receipt.
const MODEL_SHA256 := "639be377fe8d492370ff1e636ede6003f72b412addcdd769776f20c485b3b5e4"
const GloveClearance = preload("res://field_glove_clearance.gd")
const LEAD := &"player_lead"
const COMPANION := &"core_human_companion"
# Span, anticipation, contact, follow-through, socket. Every span is in seconds;
# the following beats are fractions of that span. Paths below share these beats.
const CLIPS := {
	&"chop": [.88, .30, .55, .72, &"two_hand"],
	&"mine": [.94, .34, .58, .74, &"two_hand"],
	&"dismantle": [1.16, .29, .60, .78, &"right_hand"],
	&"deposit": [.68, .25, .56, .69, &"carry"],
	&"build": [.78, .30, .57, .71, &"right_hand"],
	&"repair": [.76, .28, .54, .72, &"left_hand"],
	&"rescue": [1.06, .32, .62, .82, &"rescue"],
	&"service": [.72, .26, .58, .76, &"right_hand"],
	&"attack_contact": [.78, .24, .48, .64, &"forward_impact"],
}
# Each pose is [left wrist, right wrist, chest pitch/yaw/roll in degrees].
# Wrist coordinates are measured from their shoulder in arm lengths. Positive
# X is outward for either arm, positive Y raises the hand, positive Z reaches.
const PATHS := {
	&"chop": [
		[Vector3(-.13,.03,.84), Vector3(.39,.25,.76), Vector3(-6,-14,-5)],
		[Vector3(-.20,-.62,.73), Vector3(-.18,-.40,.84), Vector3(16,8,5)],
		[Vector3(-.04,-.78,.56), Vector3(-.20,-.58,.74), Vector3(19,12,7)],
	],
	&"mine": [
		[Vector3(.26,.21,.78), Vector3(.30,.29,.78), Vector3(-10,-4,-2)],
		[Vector3(-.12,-.72,.62), Vector3(-.05,-.68,.64), Vector3(24,2,2)],
		[Vector3(-.06,-.76,.60), Vector3(-.04,-.74,.60), Vector3(22,4,3)],
	],
	&"dismantle": [
		[Vector3(-.10,-.51,.70), Vector3(.28,-.64,.55), Vector3(7,-8,0)],
		[Vector3(-.08,-.48,.79), Vector3(-.28,-.44,.80), Vector3(16,8,3)],
		[Vector3(-.08,-.56,.67), Vector3(.55,-.35,.41), Vector3(2,-18,-8)],
	],
	&"deposit": [
		[Vector3(-.06,-.64,.63), Vector3(-.04,-.63,.65), Vector3(4,0,0)],
		[Vector3(-.15,-.34,.81), Vector3(-.12,-.36,.82), Vector3(12,2,0)],
		[Vector3(-.05,-.42,.76), Vector3(-.02,-.42,.74), Vector3(8,2,0)],
	],
	&"build": [
		[Vector3(.10,-.83,.38), Vector3(.21,.28,.64), Vector3(-2,-10,-4)],
		[Vector3(.08,-.77,.46), Vector3(-.30,-.54,.76), Vector3(15,7,3)],
		[Vector3(.07,-.82,.38), Vector3(.10,-.52,.66), Vector3(8,8,3)],
	],
	&"repair": [
		[Vector3(.29,-.56,.57), Vector3(.12,-.85,.30), Vector3(4,13,2)],
		[Vector3(-.17,-.26,.85), Vector3(.02,-.80,.39), Vector3(9,-10,-4)],
		[Vector3(-.11,-.33,.76), Vector3(.07,-.85,.34), Vector3(7,-4,-2)],
	],
	&"rescue": [
		[Vector3(.17,-.75,.54), Vector3(.19,-.78,.51), Vector3(20,0,0)],
		[Vector3(-.16,-.64,.71), Vector3(-.08,-.68,.71), Vector3(24,4,1)],
		[Vector3(-.15,-.27,.79), Vector3(-.08,-.30,.82), Vector3(8,4,1)],
	],
	&"service": [
		[Vector3(.07,-.79,.34), Vector3(-.17,-.56,.65), Vector3(2,-6,-3)],
		[Vector3(-.07,-.68,.51), Vector3(-.13,-.22,.91), Vector3(8,10,3)],
		[Vector3(.00,-.70,.49), Vector3(-.12,-.33,.81), Vector3(6,8,2)],
	],
	&"attack_contact": [
		[Vector3(.08,-.42,.70), Vector3(.12,-.37,.64), Vector3(-5,-21,-7)],
		[Vector3(-.04,-.54,.69), Vector3(-.18,-.30,.92), Vector3(11,20,9)],
		[Vector3(.00,-.55,.63), Vector3(-.19,-.48,.79), Vector3(10,22,10)],
	],
}
const BODY_WEIGHT := {
	&"chop": [Vector3(-.036,-.017,-.026), Vector3(.033,-.034,.029), Vector3(.048,-.046,.035)],
	&"mine": [Vector3(-.011,-.014,-.026), Vector3(.008,-.086,.030), Vector3(.012,-.069,.031)],
	&"dismantle": [Vector3(.022,-.032,.014), Vector3(.016,-.051,.033), Vector3(-.040,-.032,-.015)],
	&"deposit": [Vector3(0.,-.023,-.009), Vector3(0.,-.019,.025), Vector3(0.,-.015,.016)],
	&"build": [Vector3(-.022,-.009,-.014), Vector3(-.013,-.039,.029), Vector3(-.010,-.031,.017)],
	&"repair": [Vector3(.015,-.024,.006), Vector3(.030,-.029,.026), Vector3(.024,-.020,.012)],
	&"rescue": [Vector3(0.,-.084,-.025), Vector3(0.,-.118,.021), Vector3(0.,-.046,.012)],
	&"service": [Vector3(-.014,-.011,.008), Vector3(-.016,-.012,.025), Vector3(-.009,-.008,.012)],
	&"attack_contact": [Vector3(-.045,-.023,-.015), Vector3(-.024,-.032,.040), Vector3(.034,-.026,.029)],
}
const LIVE_GAINS := {
	&"chop": .38, &"mine": .42, &"attack_contact": .34,
	&"dismantle": .80, &"deposit": .82, &"build": .83, &"repair": .85,
	&"rescue": .88, &"service": .85,
}

var actor: Node3D
var rig: Skeleton3D
var support_motor: RefCounted
var support_base: Dictionary = {}
var spine := -1
var neck := -1
var arms: Array = []
var original_rotations: Dictionary = {}
var action: StringName = &""
var seconds := 0.0
var visual_weight := 0.0
var has_contact := false
var target := Vector3.INF
var transfer := false
var previous_action := {}

func bind(body: Node3D, model: Node3D, motor: RefCounted) -> bool:
	var found := model.find_children("*", "Skeleton3D", true, false)
	if found.size() != 1:
		return false
	actor = body
	rig = found[0]
	support_motor = motor
	spine = rig.find_bone("Spine")
	neck = rig.find_bone("Neck")
	for side in [".L", ".R"]:
		arms.append([rig.find_bone("UpperArm" + side), rig.find_bone("Forearm" + side), rig.find_bone("Hand" + side)])
	return mini(spine, neck) >= 0 and -1 not in arms[0] and -1 not in arms[1]

static func select(speed: float, facing: float, requested_facing: float, context: StringName, progress: float, role: StringName) -> Dictionary:
	if role != LEAD and role != COMPANION:
		return {}
	if not is_finite(speed) or not is_finite(facing) or not is_finite(requested_facing) or not is_finite(progress):
		return {}
	if CLIPS.has(context):
		var clip: Array = CLIPS[context]
		return {"action": context, "phase": clampf(progress, 0., 1.), "contact": clip[2], "socket": clip[4], "speed": speed}
	var rotation := angle_difference(facing, requested_facing)
	var degrees := absf(rad_to_deg(rotation))
	var gait := &"idle" if speed < .08 else (&"walk" if speed < 1.85 else &"run")
	return {"action": gait, "turn": 0 if degrees < 12. else (30 if degrees < 60. else (90 if degrees < 135. else 180)), "side": signf(rotation)}

func clear_pose() -> void:
	for joint: int in original_rotations:
		rig.set_bone_pose_rotation(joint, original_rotations[joint])
	original_rotations.clear()
	for joint: int in support_base:
		var base: Transform3D = support_base[joint]
		rig.set_bone_pose_position(joint, base.origin)
		rig.set_bone_pose_rotation(joint, base.basis.get_rotation_quaternion())
	support_base.clear()

func cancel() -> void:
	clear_pose()
	action = &""
	seconds = 0.
	visual_weight = 0.
	has_contact = false
	transfer = false
	previous_action.clear()

func _begin_action(next: StringName) -> void:
	if next == action: return
	if not action.is_empty():
		previous_action = {"action": action, "phase": seconds / float(CLIPS[action][0]),
			"weight": visual_weight, "elapsed": 0., "target": target}
	action = next
	visual_weight = 0.

func aim(new_action: StringName, at: Vector3, continuous_transfer := false) -> void:
	if not LIVE_GAINS.has(new_action) or not at.is_finite(): return
	if new_action == action and has_contact and seconds < float(CLIPS[action][0]) * float(CLIPS[action][3]): return
	if new_action != action:
		_begin_action(new_action)
		seconds = 0.
		has_contact = false
	target = at
	transfer = continuous_transfer

# Gameplay acknowledges the beat. This function never dispatches a gameplay event.
func contact(new_action: StringName, at: Vector3) -> void:
	if not LIVE_GAINS.has(new_action) or not at.is_finite(): return
	if action == new_action and has_contact and seconds < float(CLIPS[action][0]) * float(CLIPS[action][3]): return
	if action == &"rescue" and new_action == &"deposit" and has_contact: return
	var clip: Array = CLIPS[new_action]
	_begin_action(new_action)
	target = at
	seconds = float(clip[0]) * float(clip[2])
	has_contact = true
	transfer = false

func advance(dt: float, speed: float, transferring: bool) -> void:
	if action.is_empty() or rig == null: return
	var clip: Array = CLIPS[action]
	var duration: float = clip[0]
	var gain: float = LIVE_GAINS[action] * lerpf(1., .44, smoothstep(.2, 5.5, speed))
	if transfer and not transferring and not has_contact:
		gain = 0.
		if visual_weight < .005:
			cancel()
			return
	var limit: float = duration if has_contact else duration * maxf(float(clip[1]), float(clip[2]) - .025)
	var phase := seconds / duration
	visual_weight = lerpf(visual_weight, gain, 1. - exp(-18. * dt))
	pose(select(speed, actor.rotation.y, actor.rotation.y, action, phase, LEAD), visual_weight, target, previous_action)
	if not previous_action.is_empty():
		previous_action.elapsed += dt
		if previous_action.elapsed > .105: previous_action.clear()
	seconds = minf(seconds + dt, limit)
	if phase >= 1.:
		action = &""
		visual_weight = 0.

func _sample(key: StringName, phase: float, at: Vector3) -> Array:
	var path: Array = PATHS[key]
	var spec: Array = CLIPS[key]
	var lo := int(phase >= float(spec[2]))
	var hi := lo + 1
	var t := smoothstep(float(spec[lo + 1]), float(spec[hi + 1]), phase)
	var chest: Vector3 = path[lo][2].lerp(path[hi][2], t)
	if at.is_finite():
		var towards := actor.to_local(at)
		if Vector2(towards.x, towards.z).length_squared() > .04:
			chest.y += clampf(rad_to_deg(atan2(towards.x, towards.z)), -23., 23.) * .62
	var shift: Array = BODY_WEIGHT[key]
	return [path[lo][0].lerp(path[hi][0],t), path[lo][1].lerp(path[hi][1],t), chest,
		shift[lo].lerp(shift[hi],t), smoothstep(0., float(spec[1]), phase) * (1. - smoothstep(float(spec[3]), 1., phase))]

func pose(state: Dictionary, weight := 1., at := Vector3.INF, prior := {}) -> void:
	if not state.has("phase") or rig == null or weight <= .001: return
	var keys := _sample(state.action, state.phase, at)
	var window := weight * float(keys[4])
	if not prior.is_empty():
		var fade := smoothstep(0., .105, float(prior.elapsed))
		var after: float = float(prior.phase) + float(prior.elapsed) / float(CLIPS[prior.action][0])
		var old := _sample(prior.action, minf(after, 1.), prior.target)
		var old_weight := float(old[4]) * float(prior.weight) * (1. - fade)
		window *= fade
		if old_weight + window > .001:
			for i in 4: keys[i] = old[i].lerp(keys[i], window / (old_weight + window))
		window += old_weight
	if window < .001: return
	var crouch := window * (1. - smoothstep(.15, 1.65, float(state.speed)))
	if crouch > .001 and support_motor and support_motor.skeleton == rig and not support_motor.procedural_steps_active:
		support_base = support_motor.support_action(actor.global_basis * Vector3(keys[3]) * crouch)
	var chest: Vector3 = keys[2]
	var axes := (rig.global_basis.inverse() * actor.global_basis).orthonormalized()
	var turn := Basis(axes.z, deg_to_rad(chest.z) * window)
	turn *= Basis(axes.y, deg_to_rad(chest.y) * window)
	turn *= Basis(axes.x, deg_to_rad(chest.x) * window)
	_rotate(spine, turn * rig.get_bone_global_pose(spine).basis)
	var glance := Basis(axes.x, -deg_to_rad(chest.x) * window * .52)
	_rotate(neck, glance * rig.get_bone_global_pose(neck).basis)
	for side in 2:
		var wrist: Vector3 = keys[side]
		_pose_arm(arms[side], axes, wrist, 1. if side == 0 else -1., window)

func _rotate(joint: int, basis: Basis) -> void:
	if not original_rotations.has(joint):
		original_rotations[joint] = rig.get_bone_pose_rotation(joint)
	var parent := rig.get_bone_global_pose(rig.get_bone_parent(joint)).basis.orthonormalized()
	rig.set_bone_pose_rotation(joint, (parent.transposed() * basis.orthonormalized()).get_rotation_quaternion())

func _pose_arm(chain: Array, axes: Basis, wrist: Vector3, side: float, weight: float) -> void:
	var upper := rig.get_bone_global_pose(chain[0])
	var lower := rig.get_bone_global_pose(chain[1])
	var hand := rig.get_bone_global_pose(chain[2])
	var a := upper.origin.distance_to(lower.origin)
	var b := lower.origin.distance_to(hand.origin)
	if minf(a, b) < .001: return
	var span := a + b
	var desired := upper.origin + axes * Vector3(wrist.x * side, wrist.y, wrist.z) * span
	var travel := hand.origin.lerp(desired, weight) - upper.origin
	var direction := travel.normalized()
	if direction.is_zero_approx(): return
	var reach := clampf(travel.length(), absf(a - b) + .0001, span - .0001)
	var along := (a * a - b * b + reach * reach) / (2. * reach)
	var original_pole := (lower.origin - upper.origin).slide(direction).normalized()
	var outside := (axes * Vector3(side, -.63, -.27)).slide(direction).normalized()
	# A linear pole blend can cross zero and flip the mitten through the coat.
	# Keep the authored elbow on the same side of its bend plane through entry.
	var blend := weight * smoothstep(-.95, -.30, original_pole.dot(outside))
	var pole := original_pole.lerp(outside, blend).normalized()
	if pole.length_squared() < .001: pole = outside
	var elbow := upper.origin + direction * along + pole * sqrt(maxf(0., a * a - along * along))
	var endpoint := upper.origin + direction * reach
	var shoulder_turn := Quaternion(upper.origin.direction_to(lower.origin), upper.origin.direction_to(elbow))
	var elbow_turn := Quaternion(lower.origin.direction_to(hand.origin), elbow.direction_to(endpoint))
	_rotate(chain[0], Basis(shoulder_turn) * upper.basis)
	_rotate(chain[1], Basis(elbow_turn) * lower.basis)
	_rotate(chain[2], Basis(elbow_turn) * hand.basis)
	GloveClearance.solve(rig, actor, chain)

func sockets() -> Dictionary:
	var left := _palm(0)
	var right := _palm(1)
	var center := (left + right) * .5
	return {"left_hand": left, "right_hand": right, "two_hand": center, "carry": center,
		"rescue": center, "forward_impact": right}

func _palm(side: int) -> Vector3:
	var wrist := rig.get_bone_global_pose(arms[side][2])
	return rig.to_global(wrist * Vector3(0., .050, 0.))
