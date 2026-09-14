class_name Character1Motion
extends RefCounted

# T06 owns animation/controller data only. The supplied Character1 GLB stays
# byte-identical; gameplay position, rewards and action completion stay in the
# simulation.
const SOURCE_GLTF_SHA256 := "95e4fed3a2778656cdf8b73affd2eb3feda8a32f82f4a0c3f76d90c82633c099"
const LIBRARY := "t06"
const BLEND_SECONDS := 0.16
const WALK_STRIDE_METERS := 1.55
const RUN_STRIDE_METERS := 2.15
const WALK_CYCLE_SECONDS := 0.82
const RUN_CYCLE_SECONDS := 0.56
const NORMALIZED_SOURCE_SCALE := 1.78630495

const LOOP_CLIPS := ["idle", "walk", "run"]
const TRANSITION_CLIPS := [
	"start_walk", "start_run", "stop_walk", "stop_run",
	"walk_to_run", "run_to_walk",
	"turn_left_030", "turn_right_030",
	"turn_left_090", "turn_right_090",
	"turn_left_180", "turn_right_180"
]
const ACTION_CLIPS := [
	"chop", "mine", "dismantle", "deposit", "build", "repair",
	"rescue", "service", "attack_contact"
]

# Per-foot vertical clearance sampled from the immutable textured surface at
# the same 61 authored gait phases. The larger bilateral requirement becomes a
# small skeleton-local lift, keeping both winter boot soles above the terrain
# without changing simulation-owned root travel.
const GAIT_FOOT_CLEARANCE := {
	"walk": {
		"L": [0.03802,0.02016,0.00208,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.00098,0.00977,0.00874,0.00287,0,0,0,0,0,0,0,0,0,0,0.01038,0.02990,0.04367,0.05087,0.04883,0.04201,0.03301,0.02755,0.02423,0.02492,0.02774,0.03245,0.03758,0.04361,0.04630,0.04868,0.05079,0.05361,0.05713,0.06056,0.06327,0.06458,0.06337,0.05885,0.05047,0.03802],
		"R": [0,0,0,0,0,0,0.01159,0.02607,0.03397,0.03294,0.02636,0.01790,0.00998,0.00720,0.00677,0.00957,0.01401,0.01974,0.02508,0.03125,0.03618,0.04208,0.04859,0.05504,0.06035,0.06390,0.06518,0.06362,0.05923,0.05160,0.04044,0.02479,0.00845,0,0.00237,0.00444,0.00498,0.00197,0,0,0,0,0,0,0,0,0,0,0,0,0.00655,0.01153,0.01083,0.00529,0,0,0,0,0,0,0]
	},
	"run": {
		"L": [0.00877,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.00572,0.01157,0.01387,0.01283,0.00877],
		"R": [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.00458,0.01088,0.01312,0.01171,0.00076,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
	}
}

const ACTION_FLOOR_CLEARANCE := {
	"chop":[0.00248,0.01368,0.01698,0.01028,0.00248],
	"mine":[0.00248,0.02110,0.01543,0.01238,0.00248],
	"dismantle":[0.00248,0.00248,0.00248,0.00248,0.00248],
	"deposit":[0.00248,0.01283,0.01240,0.00896,0.00248],
	"build":[0.00248,0.00248,0.00248,0.00248,0.00248],
	"repair":[0.00248,0.00248,0.00248,0.00248,0.00248],
	"rescue":[0.00248,0.02651,0.01179,0.01303,0.00248],
	"service":[0.00248,0.00248,0.00248,0.00248,0.00248],
	"attack_contact":[0.00248,0.03300,0.06000,0.03200,0.00248]
}

const TURN_FLOOR_CLEARANCE := {
	"turn_left_030":[0.00248,0.03363,0.04356,0.03214,0.00248],
	"turn_left_090":[0.00248,0.06901,0.05689,0.06862,0.00248],
	"turn_left_180":[0.00248,0.08933,0.06722,0.09238,0.00248],
	"turn_right_030":[0.00248,0.02131,0.02639,0.02050,0.00248],
	"turn_right_090":[0.00248,0.04168,0.03974,0.04298,0.00248],
	"turn_right_180":[0.00248,0.05781,0.06831,0.05615,0.00248]
}

const TRANSITION_FLOOR_CLEARANCE := {
	"start_walk":[0.00261,0.01939,0.02883,0.01585,0.0],
	"start_run":[0.00261,0.03151,0.04385,0.00849,0.0],
	"stop_walk":[0.0,0.0,0.00048,0.00354,0.00265],
	"stop_run":[0.00007,0.01042,0.01812,0.01285,0.00265],
	"walk_to_run":[0.0,0.0,0.0,0.0,0.0],
	"run_to_walk":[0.00007,0.0,0.0,0.0,0.0]
}

const ACTION_SPECS := {
	"chop": {"duration": 0.92, "contact": 0.56, "profile": "human_player_chop", "marker": "C1TwoHandContact", "target": Vector3(-0.01, 0.87698, 0.40)},
	"mine": {"duration": 1.02, "contact": 0.58, "profile": "human_player_mine", "marker": "C1TwoHandContact", "target": Vector3(-0.02, 0.89543, 0.43)},
	"dismantle": {"duration": 1.08, "contact": 0.61, "profile": "human_player_dismantle", "marker": "C1RightHandContact", "target": Vector3(-0.30, 0.81248, 0.45)},
	"deposit": {"duration": 0.78, "contact": 0.63, "profile": "human_player_deposit", "marker": "C1TwoHandContact", "target": Vector3(0.0, 0.73240, 0.30)},
	"build": {"duration": 0.96, "contact": 0.57, "profile": "human_player_build", "marker": "C1RightHandContact", "target": Vector3(-0.43, 0.88248, 0.36)},
	"repair": {"duration": 0.88, "contact": 0.55, "profile": "human_player_repair", "marker": "C1LeftHandContact", "target": Vector3(0.43, 0.94248, 0.32)},
	"rescue": {"duration": 1.18, "contact": 0.68, "profile": "human_player_rescue", "marker": "C1RescueContact", "target": Vector3(0.0, 0.70179, 0.30)},
	"service": {"duration": 0.82, "contact": 0.61, "profile": "human_player_service", "marker": "C1RightHandContact", "target": Vector3(-0.37, 0.84248, 0.25)},
	"attack_contact": {"duration": 0.74, "contact": 0.49, "profile": "human_player_attack_foundation", "marker": "C1ForwardImpact", "target": Vector3(-0.12, 0.92000, 0.59)}
}

# Local additive rotations in degrees. Deliberately bounded angles preserve the
# supplied rig while producing readable anticipation/contact/recovery poses.
const ACTION_POSES := {
	"chop": {
		"Hip": Vector3(-8, 0, 0), "Waist": Vector3(-10, 0, -5),
		"Spine01": Vector3(-12, 0, 0), "L_Upperarm": Vector3(58, -7, 55),
		"R_Upperarm": Vector3(68, 9, -55), "L_Forearm": Vector3(32, 0, 28),
		"R_Forearm": Vector3(42, 0, -28), "L_Hand": Vector3(14, 0, 0),
		"R_Hand": Vector3(18, 0, 0), "L_Thigh": Vector3(8, 0, 3),
		"R_Thigh": Vector3(11, 0, -3), "L_Calf": Vector3(-10, 0, 0),
		"R_Calf": Vector3(-13, 0, 0)
	},
	"mine": {
		"Hip": Vector3(-13, 0, 0), "Waist": Vector3(-15, 0, 0),
		"Spine01": Vector3(-17, 0, 0), "L_Upperarm": Vector3(72, -8, 52),
		"R_Upperarm": Vector3(78, 8, -52), "L_Forearm": Vector3(50, 0, 24),
		"R_Forearm": Vector3(54, 0, -24), "L_Thigh": Vector3(13, 0, 3),
		"R_Thigh": Vector3(16, 0, -3), "L_Calf": Vector3(-18, 0, 0),
		"R_Calf": Vector3(-20, 0, 0)
	},
	"dismantle": {
		"Waist": Vector3(-9, 8, 0), "Spine01": Vector3(-11, 7, 0),
		"L_Upperarm": Vector3(18, -10, 24), "R_Upperarm": Vector3(62, 15, -56),
		"L_Forearm": Vector3(28, 0, 12), "R_Forearm": Vector3(58, 0, -22),
		"L_Hand": Vector3(19, 0, 0), "R_Hand": Vector3(-22, 0, 0)
	},
	"deposit": {
		"Hip": Vector3(-8, 0, 0), "Waist": Vector3(-12, 0, 0),
		"Spine01": Vector3(-14, 0, 0), "L_Upperarm": Vector3(42, -8, 58),
		"R_Upperarm": Vector3(42, 8, -58), "L_Forearm": Vector3(48, 0, 26),
		"R_Forearm": Vector3(48, 0, -26), "L_Thigh": Vector3(10, 0, 2),
		"R_Thigh": Vector3(10, 0, -2), "L_Calf": Vector3(-15, 0, 0),
		"R_Calf": Vector3(-15, 0, 0)
	},
	"build": {
		"Waist": Vector3(-11, -7, 0), "Spine01": Vector3(-12, -6, 0),
		"L_Upperarm": Vector3(18, -4, 18), "R_Upperarm": Vector3(70, 8, -52),
		"L_Forearm": Vector3(26, 0, 10), "R_Forearm": Vector3(48, 0, -24),
		"R_Hand": Vector3(20, 0, 0)
	},
	"repair": {
		"Waist": Vector3(-8, 8, 0), "Spine01": Vector3(-10, 9, 0),
		"L_Upperarm": Vector3(66, -7, 54), "R_Upperarm": Vector3(24, 12, -22),
		"L_Forearm": Vector3(55, 0, 24), "R_Forearm": Vector3(30, 0, -10),
		"L_Hand": Vector3(18, 0, 0), "R_Hand": Vector3(-18, 0, 0)
	},
	"rescue": {
		"Hip": Vector3(-18, 0, 0), "Waist": Vector3(-24, 0, 0),
		"Spine01": Vector3(-20, 0, 0), "L_Upperarm": Vector3(52, -6, 58),
		"R_Upperarm": Vector3(52, 6, -58), "L_Forearm": Vector3(58, 0, 26),
		"R_Forearm": Vector3(58, 0, -26), "L_Thigh": Vector3(28, 0, 3),
		"R_Thigh": Vector3(18, 0, -3), "L_Calf": Vector3(-48, 0, 0),
		"R_Calf": Vector3(-28, 0, 0)
	},
	"service": {
		"Waist": Vector3(-5, -9, 0), "Spine01": Vector3(-4, -8, 0),
		"L_Upperarm": Vector3(18, -10, 22), "R_Upperarm": Vector3(52, 14, -58),
		"L_Forearm": Vector3(32, 0, 12), "R_Forearm": Vector3(56, 0, -28),
		"R_Hand": Vector3(12, 0, 0)
	},
	"attack_contact": {
		"Hip": Vector3(-8, 12, 0), "Waist": Vector3(-12, 18, 0),
		"Spine01": Vector3(-10, 14, 0), "L_Upperarm": Vector3(24, -12, 38),
		"R_Upperarm": Vector3(72, 18, -56), "L_Forearm": Vector3(34, 0, 18),
		"R_Forearm": Vector3(30, 0, -24), "L_Thigh": Vector3(12, 0, 4),
		"R_Thigh": Vector3(18, 0, -4), "L_Calf": Vector3(-18, 0, 0),
		"R_Calf": Vector3(-22, 0, 0)
	}
}

static func _find_animation_player(node: Node) -> AnimationPlayer:
	if node is AnimationPlayer:
		return node
	for child in node.get_children():
		var found := _find_animation_player(child)
		if found:
			return found
	return null

static func _find_skeleton(node: Node) -> Skeleton3D:
	if node is Skeleton3D:
		return node
	for child in node.get_children():
		var found := _find_skeleton(child)
		if found:
			return found
	return null

static func _source_clip(player: AnimationPlayer, suffix: String) -> StringName:
	for clip in player.get_animation_list():
		if String(clip).to_lower().ends_with(suffix):
			return clip
	return StringName()

static func _track_for_bone(animation: Animation, bone: String, kind: int) -> int:
	for track in animation.get_track_count():
		if animation.track_get_type(track) == kind and String(animation.track_get_path(track)).ends_with(":" + bone):
			return track
	return -1

static func _euler_offset(degrees: Vector3) -> Quaternion:
	# Apply reach and bend before the centering swing. The source arm bases are
	# strongly abducted; making local Z the final operation keeps hands in front
	# of the chest instead of letting X/Y composition splay them back outward.
	return (
		Quaternion(Vector3.FORWARD, deg_to_rad(degrees.z))
		* Quaternion(Vector3.RIGHT, deg_to_rad(degrees.x))
		* Quaternion(Vector3.UP, deg_to_rad(degrees.y))
	).normalized()

static func _curve(points: Array, phase: float) -> float:
	var p := fposmod(phase, 1.0)
	for index in range(points.size() - 1):
		var a: Vector2 = points[index]
		var b: Vector2 = points[index + 1]
		if p >= a.x and p <= b.x:
			return lerpf(a.y, b.y, inverse_lerp(a.x, b.x, p))
	return float(points[-1].y)

static func _remove_scale_tracks(animation: Animation) -> void:
	# The imported source carries redundant animated scale channels on its root.
	# Runtime motion uses the scene's authored rest scale and never deforms it.
	for track in range(animation.get_track_count() - 1, -1, -1):
		if animation.track_get_type(track) == Animation.TYPE_SCALE_3D:
			animation.remove_track(track)

static func _insert_transform_key(animation: Animation, track: int, time: float, value: Variant) -> void:
	var kind := animation.track_get_type(track)
	for key in animation.track_get_key_count(track):
		if absf(animation.track_get_key_time(track, key) - time) < 0.0001:
			animation.track_set_key_value(track, key, value)
			return
	if kind == Animation.TYPE_ROTATION_3D:
		animation.rotation_track_insert_key(track, time, value)
	elif kind == Animation.TYPE_POSITION_3D:
		animation.position_track_insert_key(track, time, value)

static func _close_loop(animation: Animation) -> void:
	# Every transform channel gets an explicit neutral seam. Matching the first,
	# 1/120 s, penultimate and terminal samples also makes seam velocity zero on
	# both sides under cubic interpolation; no hidden root or limb snap remains.
	var seam := minf(1.0 / 120.0, animation.length * 0.02)
	for track in animation.get_track_count():
		var kind := animation.track_get_type(track)
		if kind not in [Animation.TYPE_ROTATION_3D, Animation.TYPE_POSITION_3D]:
			continue
		animation.track_set_interpolation_type(track, Animation.INTERPOLATION_LINEAR)
		var first: Variant
		if kind == Animation.TYPE_ROTATION_3D:
			first = animation.rotation_track_interpolate(track, 0.0).normalized()
		else:
			first = animation.position_track_interpolate(track, 0.0)
		_insert_transform_key(animation, track, 0.0, first)
		_insert_transform_key(animation, track, seam, first)
		_insert_transform_key(animation, track, animation.length - seam, first)
		_insert_transform_key(animation, track, animation.length, first)

static func _extract_gait_cycle(source: Animation, duration: float) -> Animation:
	# Both supplied locomotion takes contain two repeated gait cycles. Extracting
	# one source-authored cycle avoids the original slow four-step shuffle while
	# retaining the supplied full-body performance and exact rig.
	var clip := Animation.new()
	clip.length = duration
	clip.loop_mode = Animation.LOOP_LINEAR
	for source_track in source.get_track_count():
		var kind := source.track_get_type(source_track)
		if kind not in [Animation.TYPE_ROTATION_3D, Animation.TYPE_POSITION_3D]:
			continue
		var track := clip.add_track(kind)
		clip.track_set_path(track, source.track_get_path(source_track))
		clip.track_set_interpolation_type(track, Animation.INTERPOLATION_LINEAR)
		for sample in range(61):
			var phase := float(sample) / 60.0
			var source_time := source.length * phase * 0.5
			var time := duration * phase
			if kind == Animation.TYPE_ROTATION_3D:
				var value := source.rotation_track_interpolate(source_track, source_time).normalized()
				if phase > 0.80:
					var first := source.rotation_track_interpolate(source_track, 0.0).normalized()
					value = value.slerp(first, smoothstep(0.80, 1.0, phase)).normalized()
				clip.rotation_track_insert_key(track, time, value)
			else:
				var value := source.position_track_interpolate(source_track, source_time)
				if phase > 0.80:
					value = value.lerp(source.position_track_interpolate(source_track, 0.0), smoothstep(0.80, 1.0, phase))
				clip.position_track_insert_key(track, time, value)
	return clip

static func _tune_locomotion(source: Animation, running: bool) -> Animation:
	var clip := _extract_gait_cycle(source, RUN_CYCLE_SECONDS if running else WALK_CYCLE_SECONDS)
	var foot_curve := [
		Vector2(0.00, -8.0), Vector2(0.10, 0.0), Vector2(0.34, 7.0),
		Vector2(0.49, 16.0), Vector2(0.64, -13.0), Vector2(0.86, -7.0),
		Vector2(1.00, -8.0)
	]
	var toe_curve := [
		Vector2(0.00, 0.0), Vector2(0.29, 0.0), Vector2(0.43, 15.0),
		Vector2(0.51, 31.0), Vector2(0.63, 9.0), Vector2(0.78, 0.0),
		Vector2(1.00, 0.0)
	]
	var multiplier := 1.16 if running else 0.82
	for side in ["L", "R"]:
		var offset := 0.0 if side == "L" else 0.5
		for bone in [side + "_Foot", side + "_ToeBase"]:
			var track := _track_for_bone(clip, bone, Animation.TYPE_ROTATION_3D)
			if track < 0:
				continue
			for key in clip.track_get_key_count(track):
				var phase := fposmod(clip.track_get_key_time(track, key) / maxf(clip.length, 0.001) + offset, 1.0)
				var angle := _curve(toe_curve if bone.ends_with("ToeBase") else foot_curve, phase) * multiplier
				var base: Quaternion = clip.track_get_key_value(track, key)
				clip.track_set_key_value(track, key, (base * Quaternion(Vector3.RIGHT, deg_to_rad(angle))).normalized())
	# Phase-aware hip/calf shaping gives the shortened cycle a readable step
	# length while the lateral correction keeps knees over the winter boots.
	for side in ["L", "R"]:
		var thigh := _track_for_bone(clip, side + "_Thigh", Animation.TYPE_ROTATION_3D)
		var calf := _track_for_bone(clip, side + "_Calf", Animation.TYPE_ROTATION_3D)
		if thigh < 0:
			continue
		var sign := 1.0 if side == "L" else -1.0
		for key in clip.track_get_key_count(thigh):
			var phase := fposmod(clip.track_get_key_time(thigh, key) / maxf(clip.length, 0.001) + (0.0 if side == "L" else 0.5), 1.0)
			var correction := sign * _curve([Vector2(0, 2.0), Vector2(0.5, 4.0), Vector2(1, 2.0)], phase)
			var base: Quaternion = clip.track_get_key_value(thigh, key)
			var stride_swing := sin(phase * TAU) * (36.0 if running else 42.0)
			clip.track_set_key_value(thigh, key, (base * _euler_offset(Vector3(stride_swing, 0.0, correction))).normalized())
		if calf >= 0:
			for key in clip.track_get_key_count(calf):
				var phase := fposmod(clip.track_get_key_time(calf, key) / maxf(clip.length, 0.001) + (0.0 if side == "L" else 0.5), 1.0)
				var flex := _curve([Vector2(0.0, 4.0), Vector2(0.18, 8.0), Vector2(0.52, 34.0 if running else 24.0), Vector2(0.76, 12.0), Vector2(1.0, 4.0)], phase)
				var base: Quaternion = clip.track_get_key_value(calf, key)
				clip.track_set_key_value(calf, key, (base * Quaternion(Vector3.RIGHT, deg_to_rad(-flex))).normalized())
	var gait_id := "run" if running else "walk"
	var position_track := _track_for_bone(clip, "Hip", Animation.TYPE_POSITION_3D)
	var left_lifts: Array = GAIT_FOOT_CLEARANCE[gait_id].L
	var right_lifts: Array = GAIT_FOOT_CLEARANCE[gait_id].R
	assert(position_track >= 0 and clip.track_get_key_count(position_track) == left_lifts.size() and left_lifts.size() == right_lifts.size())
	for key in clip.track_get_key_count(position_track):
		var position: Vector3 = clip.track_get_key_value(position_track, key)
		# Hip's imported local +Z maps to character-global +Y.
		position.z += maxf(float(left_lifts[key]), float(right_lifts[key])) / NORMALIZED_SOURCE_SCALE
		clip.track_set_key_value(position_track, key, position)
	_close_loop(clip)
	return clip

static func _sample_rotation(animation: Animation, path: NodePath, time: float) -> Quaternion:
	var track := animation.find_track(path, Animation.TYPE_ROTATION_3D)
	if track < 0:
		return Quaternion.IDENTITY
	return animation.rotation_track_interpolate(track, clampf(time, 0.0, animation.length)).normalized()

static func _sample_position(animation: Animation, path: NodePath, time: float) -> Vector3:
	var track := animation.find_track(path, Animation.TYPE_POSITION_3D)
	if track < 0:
		return Vector3.ZERO
	return animation.position_track_interpolate(track, clampf(time, 0.0, animation.length))

static func _transition_clip(from_clip: Animation, to_clip: Animation, duration: float, id: String) -> Animation:
	var clip := Animation.new()
	clip.length = duration
	clip.loop_mode = Animation.LOOP_NONE
	for source_track in from_clip.get_track_count():
		var kind := from_clip.track_get_type(source_track)
		if kind not in [Animation.TYPE_ROTATION_3D, Animation.TYPE_POSITION_3D]:
			continue
		var path := from_clip.track_get_path(source_track)
		var track := clip.add_track(kind)
		clip.track_set_path(track, path)
		clip.track_set_interpolation_type(track, Animation.INTERPOLATION_CUBIC)
		if kind == Animation.TYPE_ROTATION_3D:
			var start := _sample_rotation(from_clip, path, 0.0)
			var finish := _sample_rotation(to_clip, path, minf(to_clip.length * 0.12, 0.16))
			clip.rotation_track_insert_key(track, 0.0, start)
			clip.rotation_track_insert_key(track, duration * 0.52, start.slerp(finish, 0.52).normalized())
			clip.rotation_track_insert_key(track, duration, finish)
		else:
			var start_position := _sample_position(from_clip, path, 0.0)
			var end_position := _sample_position(to_clip, path, minf(to_clip.length * 0.12, 0.16))
			var bone := String(path).get_slice(":", String(path).get_slice_count(":") - 1)
			for phase_index in 5:
				var phase := float(phase_index) / 4.0
				var position := start_position.lerp(end_position, phase)
				if bone == "Hip":
					position.z += float(TRANSITION_FLOOR_CLEARANCE[id][phase_index]) / NORMALIZED_SOURCE_SCALE
				clip.position_track_insert_key(track, duration * phase, position)
	return clip

static func _turn_transition(idle: Animation, duration: float, degrees: int, direction: float) -> Animation:
	# The animation provides a planted support leg and a free-foot step/pivot.
	# It deliberately returns to a neutral skeleton: the simulation applies the
	# declared facing delta to the actor root and remains the sole authority.
	var clip := Animation.new()
	clip.length = duration
	clip.loop_mode = Animation.LOOP_NONE
	var magnitude := clampf(float(degrees) / 90.0, 0.34, 1.35)
	var free_side := "L" if direction < 0.0 else "R"
	var turn_id := "turn_%s_%03d" % ["left" if direction < 0.0 else "right", degrees]
	var phases := [0.0, 0.24, 0.52, 0.78, 1.0]
	for source_track in idle.get_track_count():
		var kind := idle.track_get_type(source_track)
		if kind not in [Animation.TYPE_ROTATION_3D, Animation.TYPE_POSITION_3D]:
			continue
		var path := idle.track_get_path(source_track)
		var track := clip.add_track(kind)
		clip.track_set_path(track, path)
		clip.track_set_interpolation_type(track, Animation.INTERPOLATION_CUBIC)
		var bone := String(path).get_slice(":", String(path).get_slice_count(":") - 1)
		if kind == Animation.TYPE_POSITION_3D:
			var base_position := _sample_position(idle, path, 0.0)
			for phase_index in phases.size():
				var phase: float = phases[phase_index]
				var position := base_position
				if bone == "Hip":
					position.y += sin(phase * PI) * 0.014 * magnitude
					position.x += direction * sin(phase * PI) * 0.010 * magnitude
					position.z += float(TURN_FLOOR_CLEARANCE[turn_id][phase_index]) / NORMALIZED_SOURCE_SCALE
				clip.position_track_insert_key(track, phase * duration, position)
		else:
			var base_rotation := _sample_rotation(idle, path, 0.0)
			for phase in phases:
				var envelope := sin(phase * PI)
				var offset := Vector3.ZERO
				if bone == free_side + "_Thigh":
					offset = Vector3(-13.0 * magnitude, direction * 5.0, direction * 4.0)
				elif bone == free_side + "_Calf":
					offset = Vector3(-22.0 * magnitude, 0.0, 0.0)
				elif bone == free_side + "_Foot":
					offset = Vector3(-15.0 * magnitude, -direction * 24.0 * magnitude, 0.0)
				elif bone == free_side + "_ToeBase":
					offset = Vector3(18.0 * magnitude, 0.0, 0.0)
				elif bone.ends_with("_Thigh"):
					offset = Vector3(4.0 * magnitude, 0.0, -direction * 3.0)
				elif bone in ["Hip", "Waist"]:
					offset = Vector3(-2.0 * magnitude, direction * 4.0 * magnitude, 0.0)
				clip.rotation_track_insert_key(track, phase * duration, (base_rotation * _euler_offset(offset * envelope)).normalized())
	return clip

static func _action_factor(phase: float) -> float:
	return _curve([
		Vector2(0.00, 0.0), Vector2(0.22, -0.30), Vector2(0.52, 1.0),
		Vector2(0.73, 0.34), Vector2(1.00, 0.0)
	], clampf(phase, 0.0, 1.0))

static func _action_clip(id: String, idle: Animation) -> Animation:
	var duration := float(ACTION_SPECS[id].duration)
	var clip := Animation.new()
	clip.length = duration
	clip.loop_mode = Animation.LOOP_NONE
	var phases := [0.0, 0.22, float(ACTION_SPECS[id].contact), 0.73, 1.0]
	for source_track in idle.get_track_count():
		var kind := idle.track_get_type(source_track)
		if kind not in [Animation.TYPE_ROTATION_3D, Animation.TYPE_POSITION_3D]:
			continue
		var path := idle.track_get_path(source_track)
		var track := clip.add_track(kind)
		clip.track_set_path(track, path)
		clip.track_set_interpolation_type(track, Animation.INTERPOLATION_CUBIC)
		var bone := String(path).get_slice(":", String(path).get_slice_count(":") - 1)
		for phase_index in phases.size():
			var phase: float = phases[phase_index]
			if kind == Animation.TYPE_ROTATION_3D:
				var base := _sample_rotation(idle, path, 0.0)
				var peak: Vector3 = ACTION_POSES[id].get(bone, Vector3.ZERO)
				var pose := _euler_offset(peak * _action_factor(phase))
				clip.rotation_track_insert_key(track, phase * duration, (base * pose).normalized())
			else:
				var position := _sample_position(idle, path, 0.0)
				if bone == "Hip":
					# Preserve the authored local forward/back shift, then add the
					# measured global-up clearance through imported local +Z.
					position.y -= absf(_action_factor(phase)) * (0.018 if id != "rescue" else 0.035)
					position.z += float(ACTION_FLOOR_CLEARANCE[id][phase_index]) / NORMALIZED_SOURCE_SCALE
				clip.position_track_insert_key(track, phase * duration, position)
	return clip

static func _contact_contract() -> Dictionary:
	var actions := {}
	for id in ACTION_CLIPS:
		var spec: Dictionary = ACTION_SPECS[id].duplicate(true)
		var target: Vector3 = spec.target
		spec.target = [target.x, target.y, target.z]
		actions[id] = spec
	return {
		"schema_version": 2,
		"source_gltf_sha256": SOURCE_GLTF_SHA256,
		"roles": ["player_lead", "core_human_companion"],
		"simulation_authoritative": true,
		"root_facing_authority": "simulation_external",
		"duplicate_gameplay_impacts_allowed": false,
		"companion_visual_phase_offset": 0.37,
		"finished_tool_or_weapon_assets_included": false,
		"contacts": {
			"right_hand": "C1RightHandContact", "left_hand": "C1LeftHandContact",
			"two_hand": "C1TwoHandContact", "carry": "C1CarryContact",
			"rescue": "C1RescueContact", "forward_impact": "C1ForwardImpact"
		},
		"actions": actions
	}

static func _attachment(skeleton: Skeleton3D, root: Node3D, name: String, bone: String, offset: Vector3) -> void:
	if root.find_child(name, true, false):
		return
	var marker: Node3D
	if bone.is_empty():
		marker = Marker3D.new()
		marker.name = name
		marker.position = offset
		root.add_child(marker)
	else:
		var attachment := BoneAttachment3D.new()
		attachment.name = name
		attachment.bone_name = bone
		skeleton.add_child(attachment)
		var tip := Marker3D.new()
		tip.name = "Contact"
		tip.position = offset
		attachment.add_child(tip)

static func _install_contacts(root: Node3D, skeleton: Skeleton3D) -> void:
	_attachment(skeleton, root, "C1RightHandContact", "R_Hand", Vector3(0.0, 0.085, 0.0))
	_attachment(skeleton, root, "C1LeftHandContact", "L_Hand", Vector3(0.0, 0.085, 0.0))
	# Character 1 faces local +Z. Keep the abstract multi-hand/rescue/impact
	# proxies on that same side of the body as the measured hand targets.
	_attachment(skeleton, root, "C1TwoHandContact", "Waist", Vector3(0.0, 0.36, 0.40))
	_attachment(skeleton, root, "C1CarryContact", "Waist", Vector3(0.0, 0.30, -0.42))
	_attachment(skeleton, root, "C1RescueContact", "Waist", Vector3(0.0, 0.18, 0.30))
	_attachment(skeleton, root, "C1ForwardImpact", "", ACTION_SPECS.attack_contact.target)

static func install(root: Node3D, role := "player_lead") -> Dictionary:
	var player := _find_animation_player(root)
	var skeleton := _find_skeleton(root)
	var errors: Array[String] = []
	if not player:
		errors.append("Character 1 AnimationPlayer missing")
	if not skeleton:
		errors.append("Character 1 Skeleton3D missing")
	if not errors.is_empty():
		return {"passed": false, "errors": errors}
	var source_names := {
		"idle": _source_clip(player, "idle"),
		"walk": _source_clip(player, "walk"),
		"run": _source_clip(player, "run")
	}
	for id in source_names:
		if String(source_names[id]).is_empty():
			errors.append("Source clip missing: " + id)
	if not errors.is_empty():
		return {"passed": false, "errors": errors}
	if player.has_animation_library(LIBRARY):
		player.remove_animation_library(LIBRARY)
	var idle: Animation = player.get_animation(source_names.idle).duplicate(true)
	idle.loop_mode = Animation.LOOP_LINEAR
	_remove_scale_tracks(idle)
	_close_loop(idle)
	var walk := _tune_locomotion(player.get_animation(source_names.walk), false)
	var run := _tune_locomotion(player.get_animation(source_names.run), true)
	var library := AnimationLibrary.new()
	library.add_animation("idle", idle)
	library.add_animation("walk", walk)
	library.add_animation("run", run)
	library.add_animation("start_walk", _transition_clip(idle, walk, 0.34, "start_walk"))
	library.add_animation("start_run", _transition_clip(idle, run, 0.30, "start_run"))
	library.add_animation("stop_walk", _transition_clip(walk, idle, 0.32, "stop_walk"))
	library.add_animation("stop_run", _transition_clip(run, idle, 0.38, "stop_run"))
	library.add_animation("walk_to_run", _transition_clip(walk, run, 0.28, "walk_to_run"))
	library.add_animation("run_to_walk", _transition_clip(run, walk, 0.30, "run_to_walk"))
	for degrees in [30, 90, 180]:
		var duration := 0.30 if degrees == 30 else (0.44 if degrees == 90 else 0.62)
		library.add_animation("turn_left_%03d" % degrees, _turn_transition(idle, duration, degrees, -1.0))
		library.add_animation("turn_right_%03d" % degrees, _turn_transition(idle, duration, degrees, 1.0))
	for id in ACTION_CLIPS:
		library.add_animation(id, _action_clip(id, idle))
	player.add_animation_library(LIBRARY, library)
	for from_clip in library.get_animation_list():
		for to_clip in library.get_animation_list():
			if from_clip != to_clip:
				player.set_blend_time(LIBRARY + "/" + from_clip, LIBRARY + "/" + to_clip, BLEND_SECONDS)
	_install_contacts(root, skeleton)
	var contract := _contact_contract()
	root.set_meta("t06_motion_player", player)
	root.set_meta("t06_motion_skeleton", skeleton)
	root.set_meta("t06_motion_contract", contract)
	root.set_meta("t06_motion_role", role)
	root.set_meta("t06_locomotion_state", "idle")
	root.set_meta("t06_transition_remaining", 0.0)
	root.set_meta("t06_active_clip", "")
	return {
		"passed": true, "errors": [], "player": player, "skeleton": skeleton,
		"contract": contract, "clips": Array(library.get_animation_list())
	}

static func motion_for_action(action: Dictionary) -> String:
	var kind := String(action.get("kind", ""))
	if kind == "gather":
		var id := String(action.get("id", action.get("resource", ""))).to_lower()
		if id.begins_with("wood"):
			return "chop"
		if id.begins_with("stone") or id.begins_with("metal"):
			return "mine"
		return "dismantle"
	return {
		"deposit": "deposit", "build": "build", "repair": "repair",
		"defense_repair": "repair", "rescue": "rescue", "npc_rescue": "rescue",
		"customer_service": "service", "enemy": "attack_contact"
	}.get(kind, "")

static func _qualified(id: String) -> StringName:
	return StringName(LIBRARY + "/" + id)

static func cadence_scale(id: String, speed: float, animation: Animation) -> float:
	if id == "walk":
		return clampf(speed * animation.length / WALK_STRIDE_METERS, 0.60, 2.20)
	if id == "run":
		return clampf(speed * animation.length / RUN_STRIDE_METERS, 0.78, 2.20)
	return 1.0

static func _play(player: AnimationPlayer, root: Node3D, id: String, blend := BLEND_SECONDS) -> void:
	var qualified := _qualified(id)
	if not player.has_animation(qualified):
		return
	if String(root.get_meta("t06_active_clip", "")) != id:
		player.play(qualified, blend)
		root.set_meta("t06_active_clip", id)

static func _turn_clip(turn_degrees: float) -> String:
	var amount := absf(turn_degrees)
	var bucket := 30 if amount < 60 else (90 if amount < 135 else 180)
	return "turn_%s_%03d" % ["left" if turn_degrees < 0 else "right", bucket]

static func facing_delta_for_turn(id: String) -> float:
	if not id.begins_with("turn_"):
		return 0.0
	var parts := id.split("_")
	if parts.size() != 3:
		return 0.0
	var amount := float(parts[2].to_int())
	return -amount if parts[1] == "left" else amount

static func update_actor(root: Node3D, speed: float, action: Dictionary, dt: float, role := "player_lead", turn_degrees := 0.0) -> Dictionary:
	if not root.has_meta("t06_motion_player"):
		var installed := install(root, role)
		if not installed.passed:
			return installed
	var player: AnimationPlayer = root.get_meta("t06_motion_player")
	root.set_meta("t06_motion_role", role)
	var action_clip := motion_for_action(action)
	if not action_clip.is_empty() and speed < 0.20:
		_play(player, root, action_clip)
		var clip := player.get_animation(_qualified(action_clip))
		var progress := clampf(float(action.get("progress", 0.0)), 0.0, 1.0)
		player.seek(clip.length * progress, true)
		# A zero speed scale also freezes AnimationPlayer's blend clock, leaving
		# the actor visually stuck in the previous state. Re-seeking every update
		# keeps simulation progress authoritative while a live clock completes the
		# configured 0.16 s boundary blend.
		player.speed_scale = 1.0
		return {"passed": true, "state": action_clip, "progress": progress, "role": role, "simulation_authoritative": true}
	if absf(turn_degrees) >= 15.0 and speed < 0.20:
		var turn := _turn_clip(turn_degrees)
		_play(player, root, turn)
		player.speed_scale = 1.0
		return {"passed": true, "state": turn, "role": role, "simulation_authoritative": true, "root_facing_authority": "simulation_external", "facing_delta_degrees": facing_delta_for_turn(turn)}
	var state := "run" if speed > 4.3 else ("walk" if speed > 0.15 else "idle")
	var previous := String(root.get_meta("t06_locomotion_state", "idle"))
	var remaining := maxf(0.0, float(root.get_meta("t06_transition_remaining", 0.0)) - maxf(dt, 0.0))
	if state != previous:
		var transition := ""
		if previous == "idle" and state == "walk":
			transition = "start_walk"
		elif previous == "idle" and state == "run":
			transition = "start_run"
		elif previous == "walk" and state == "run":
			transition = "walk_to_run"
		elif previous == "run" and state == "walk":
			transition = "run_to_walk"
		elif state == "idle" and previous == "walk":
			transition = "stop_walk"
		elif state == "idle" and previous == "run":
			transition = "stop_run"
		root.set_meta("t06_locomotion_state", state)
		if not transition.is_empty():
			remaining = player.get_animation(_qualified(transition)).length
			root.set_meta("t06_transition_target", state)
			_play(player, root, transition)
	if remaining > 0.0:
		root.set_meta("t06_transition_remaining", remaining)
		player.speed_scale = 1.0
		return {"passed": true, "state": String(root.get_meta("t06_active_clip", "")), "transition_target": state, "role": role, "simulation_authoritative": true}
	root.set_meta("t06_transition_remaining", 0.0)
	var clip_changed := String(root.get_meta("t06_active_clip", "")) != state
	_play(player, root, state)
	var animation := player.get_animation(_qualified(state))
	if clip_changed and role == "core_human_companion" and state in LOOP_CLIPS:
		player.seek(animation.length * float(root.get_meta("t06_motion_contract").companion_visual_phase_offset), true)
	player.speed_scale = cadence_scale(state, speed, animation)
	return {"passed": true, "state": state, "speed_scale": player.speed_scale, "role": role, "simulation_authoritative": true}
