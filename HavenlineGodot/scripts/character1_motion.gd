class_name Character1Motion
extends RefCounted

# T06 owns animation/controller data only. The supplied Character1 GLB stays
# byte-identical; gameplay position, rewards and action completion stay in the
# simulation.
const SOURCE_GLTF_SHA256 := "95e4fed3a2778656cdf8b73affd2eb3feda8a32f82f4a0c3f76d90c82633c099"
const LIBRARY := "t06"
const BLEND_SECONDS := 0.16
const WALK_STRIDE_METERS := 1.72
const RUN_STRIDE_METERS := 3.62

const LOOP_CLIPS := ["idle", "walk", "run"]
const TRANSITION_CLIPS := [
	"start_walk", "start_run", "stop",
	"turn_left_030", "turn_right_030",
	"turn_left_090", "turn_right_090",
	"turn_left_180", "turn_right_180"
]
const ACTION_CLIPS := [
	"chop", "mine", "dismantle", "deposit", "build", "repair",
	"rescue", "service", "attack_contact"
]

const ACTION_SPECS := {
	"chop": {"duration": 0.92, "contact": 0.56, "profile": "human_player_chop"},
	"mine": {"duration": 1.02, "contact": 0.58, "profile": "human_player_mine"},
	"dismantle": {"duration": 1.08, "contact": 0.61, "profile": "human_player_dismantle"},
	"deposit": {"duration": 0.78, "contact": 0.63, "profile": "human_player_deposit"},
	"build": {"duration": 0.96, "contact": 0.57, "profile": "human_player_build"},
	"repair": {"duration": 0.88, "contact": 0.55, "profile": "human_player_repair"},
	"rescue": {"duration": 1.18, "contact": 0.68, "profile": "human_player_rescue"},
	"service": {"duration": 0.82, "contact": 0.61, "profile": "human_player_service"},
	"attack_contact": {"duration": 0.74, "contact": 0.49, "profile": "human_player_attack_foundation"}
}

# Local additive rotations in degrees. Deliberately bounded angles preserve the
# supplied rig while producing readable anticipation/contact/recovery poses.
const ACTION_POSES := {
	"chop": {
		"Hip": Vector3(-8, 0, 0), "Waist": Vector3(-10, 0, -5),
		"Spine01": Vector3(-12, 0, 0), "L_Upperarm": Vector3(-44, -7, 18),
		"R_Upperarm": Vector3(-62, 9, -16), "L_Forearm": Vector3(-34, 0, 5),
		"R_Forearm": Vector3(-48, 0, -6), "L_Hand": Vector3(-14, 0, 0),
		"R_Hand": Vector3(-18, 0, 0), "L_Thigh": Vector3(8, 0, 3),
		"R_Thigh": Vector3(11, 0, -3), "L_Calf": Vector3(-10, 0, 0),
		"R_Calf": Vector3(-13, 0, 0)
	},
	"mine": {
		"Hip": Vector3(-13, 0, 0), "Waist": Vector3(-15, 0, 0),
		"Spine01": Vector3(-17, 0, 0), "L_Upperarm": Vector3(-52, -8, 14),
		"R_Upperarm": Vector3(-68, 8, -14), "L_Forearm": Vector3(-46, 0, 4),
		"R_Forearm": Vector3(-52, 0, -4), "L_Thigh": Vector3(13, 0, 3),
		"R_Thigh": Vector3(16, 0, -3), "L_Calf": Vector3(-18, 0, 0),
		"R_Calf": Vector3(-20, 0, 0)
	},
	"dismantle": {
		"Waist": Vector3(-9, 8, 0), "Spine01": Vector3(-11, 7, 0),
		"L_Upperarm": Vector3(-34, -10, 16), "R_Upperarm": Vector3(-55, 15, -12),
		"L_Forearm": Vector3(-42, 0, 0), "R_Forearm": Vector3(-58, 0, 0),
		"L_Hand": Vector3(-19, 0, 0), "R_Hand": Vector3(22, 0, 0)
	},
	"deposit": {
		"Hip": Vector3(-8, 0, 0), "Waist": Vector3(-12, 0, 0),
		"Spine01": Vector3(-14, 0, 0), "L_Upperarm": Vector3(-38, -8, 12),
		"R_Upperarm": Vector3(-38, 8, -12), "L_Forearm": Vector3(-50, 0, 0),
		"R_Forearm": Vector3(-50, 0, 0), "L_Thigh": Vector3(10, 0, 2),
		"R_Thigh": Vector3(10, 0, -2), "L_Calf": Vector3(-15, 0, 0),
		"R_Calf": Vector3(-15, 0, 0)
	},
	"build": {
		"Waist": Vector3(-11, -7, 0), "Spine01": Vector3(-12, -6, 0),
		"L_Upperarm": Vector3(-25, -4, 14), "R_Upperarm": Vector3(-61, 8, -12),
		"L_Forearm": Vector3(-36, 0, 0), "R_Forearm": Vector3(-48, 0, 0),
		"R_Hand": Vector3(-20, 0, 0)
	},
	"repair": {
		"Waist": Vector3(-8, 8, 0), "Spine01": Vector3(-10, 9, 0),
		"L_Upperarm": Vector3(-42, -7, 12), "R_Upperarm": Vector3(-30, 12, -10),
		"L_Forearm": Vector3(-55, 0, 0), "R_Forearm": Vector3(-38, 0, 0),
		"L_Hand": Vector3(-18, 0, 0), "R_Hand": Vector3(18, 0, 0)
	},
	"rescue": {
		"Hip": Vector3(-18, 0, 0), "Waist": Vector3(-24, 0, 0),
		"Spine01": Vector3(-20, 0, 0), "L_Upperarm": Vector3(-42, -6, 18),
		"R_Upperarm": Vector3(-42, 6, -18), "L_Forearm": Vector3(-58, 0, 0),
		"R_Forearm": Vector3(-58, 0, 0), "L_Thigh": Vector3(28, 0, 3),
		"R_Thigh": Vector3(18, 0, -3), "L_Calf": Vector3(-48, 0, 0),
		"R_Calf": Vector3(-28, 0, 0)
	},
	"service": {
		"Waist": Vector3(-5, -9, 0), "Spine01": Vector3(-4, -8, 0),
		"L_Upperarm": Vector3(-26, -10, 14), "R_Upperarm": Vector3(-36, 14, -12),
		"L_Forearm": Vector3(-48, 0, 0), "R_Forearm": Vector3(-56, 0, 0),
		"R_Hand": Vector3(-12, 0, 0)
	},
	"attack_contact": {
		"Hip": Vector3(-8, 12, 0), "Waist": Vector3(-12, 18, 0),
		"Spine01": Vector3(-10, 14, 0), "L_Upperarm": Vector3(-24, -12, 18),
		"R_Upperarm": Vector3(-68, 18, -18), "L_Forearm": Vector3(-34, 0, 0),
		"R_Forearm": Vector3(-32, 0, 0), "L_Thigh": Vector3(12, 0, 4),
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
	return Basis.from_euler(Vector3(
		deg_to_rad(degrees.x), deg_to_rad(degrees.y), deg_to_rad(degrees.z)
	)).get_rotation_quaternion()

static func _curve(points: Array, phase: float) -> float:
	var p := fposmod(phase, 1.0)
	for index in range(points.size() - 1):
		var a: Vector2 = points[index]
		var b: Vector2 = points[index + 1]
		if p >= a.x and p <= b.x:
			return lerpf(a.y, b.y, inverse_lerp(a.x, b.x, p))
	return float(points[-1].y)

static func _tune_locomotion(source: Animation, running: bool) -> Animation:
	var clip: Animation = source.duplicate(true)
	clip.loop_mode = Animation.LOOP_LINEAR
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
	# A small opposing thigh correction keeps knees tracking over the feet under
	# the authored wide winter stance without changing limb length.
	for side in ["L", "R"]:
		var thigh := _track_for_bone(clip, side + "_Thigh", Animation.TYPE_ROTATION_3D)
		if thigh < 0:
			continue
		var sign := 1.0 if side == "L" else -1.0
		for key in clip.track_get_key_count(thigh):
			var phase := fposmod(clip.track_get_key_time(thigh, key) / maxf(clip.length, 0.001) + (0.0 if side == "L" else 0.5), 1.0)
			var correction := sign * _curve([Vector2(0, 2.0), Vector2(0.5, 4.0), Vector2(1, 2.0)], phase)
			var base: Quaternion = clip.track_get_key_value(thigh, key)
			clip.track_set_key_value(thigh, key, (base * Quaternion(Vector3.FORWARD, deg_to_rad(correction))).normalized())
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

static func _transition_clip(from_clip: Animation, to_clip: Animation, duration: float, turn_degrees := 0.0) -> Animation:
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
			var bone := String(path).get_slice(":", String(path).get_slice_count(":") - 1)
			var turn := Quaternion.IDENTITY
			if bone in ["Hip", "Waist", "Spine01", "Spine02"]:
				var share := {"Hip": 0.18, "Waist": 0.32, "Spine01": 0.28, "Spine02": 0.22}[bone]
				turn = Quaternion(Vector3.UP, deg_to_rad(turn_degrees * share))
			clip.rotation_track_insert_key(track, 0.0, start)
			clip.rotation_track_insert_key(track, duration * 0.52, (start.slerp(finish, 0.52) * turn).normalized())
			clip.rotation_track_insert_key(track, duration, finish)
		else:
			clip.position_track_insert_key(track, 0.0, _sample_position(from_clip, path, 0.0))
			clip.position_track_insert_key(track, duration, _sample_position(to_clip, path, minf(to_clip.length * 0.12, 0.16)))
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
		for phase in phases:
			if kind == Animation.TYPE_ROTATION_3D:
				var base := _sample_rotation(idle, path, 0.0)
				var peak: Vector3 = ACTION_POSES[id].get(bone, Vector3.ZERO)
				var pose := _euler_offset(peak * _action_factor(phase))
				clip.rotation_track_insert_key(track, phase * duration, (base * pose).normalized())
			else:
				var position := _sample_position(idle, path, 0.0)
				if bone == "Hip":
					position.y -= absf(_action_factor(phase)) * (0.018 if id != "rescue" else 0.035)
				clip.position_track_insert_key(track, phase * duration, position)
	return clip

static func _contact_contract() -> Dictionary:
	var actions := {}
	for id in ACTION_CLIPS:
		actions[id] = ACTION_SPECS[id].duplicate(true)
	return {
		"schema_version": 1,
		"source_gltf_sha256": SOURCE_GLTF_SHA256,
		"roles": ["player_lead", "core_human_companion"],
		"simulation_authoritative": true,
		"duplicate_gameplay_impacts_allowed": false,
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
	_attachment(skeleton, root, "C1TwoHandContact", "Waist", Vector3(0.0, 0.36, -0.24))
	_attachment(skeleton, root, "C1CarryContact", "Waist", Vector3(0.0, 0.30, -0.42))
	_attachment(skeleton, root, "C1RescueContact", "Waist", Vector3(0.0, 0.18, -0.48))
	_attachment(skeleton, root, "C1ForwardImpact", "", Vector3(0.0, 0.92, -0.72))

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
	var walk := _tune_locomotion(player.get_animation(source_names.walk), false)
	var run := _tune_locomotion(player.get_animation(source_names.run), true)
	var library := AnimationLibrary.new()
	library.add_animation("idle", idle)
	library.add_animation("walk", walk)
	library.add_animation("run", run)
	library.add_animation("start_walk", _transition_clip(idle, walk, 0.34))
	library.add_animation("start_run", _transition_clip(idle, run, 0.30))
	library.add_animation("stop", _transition_clip(walk, idle, 0.32))
	for degrees in [30, 90, 180]:
		var duration := 0.30 if degrees == 30 else (0.44 if degrees == 90 else 0.62)
		library.add_animation("turn_left_%03d" % degrees, _transition_clip(idle, idle, duration, -degrees))
		library.add_animation("turn_right_%03d" % degrees, _transition_clip(idle, idle, duration, degrees))
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
		player.speed_scale = 0.0
		return {"passed": true, "state": action_clip, "progress": progress, "role": role, "simulation_authoritative": true}
	if absf(turn_degrees) >= 15.0 and speed < 0.20:
		var turn := _turn_clip(turn_degrees)
		_play(player, root, turn)
		player.speed_scale = 1.0
		return {"passed": true, "state": turn, "role": role, "simulation_authoritative": true}
	var state := "run" if speed > 4.3 else ("walk" if speed > 0.15 else "idle")
	var previous := String(root.get_meta("t06_locomotion_state", "idle"))
	var remaining := maxf(0.0, float(root.get_meta("t06_transition_remaining", 0.0)) - maxf(dt, 0.0))
	if state != previous:
		var transition := ""
		if previous == "idle" and state == "walk":
			transition = "start_walk"
		elif previous == "idle" and state == "run":
			transition = "start_run"
		elif state == "idle":
			transition = "stop"
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
	_play(player, root, state)
	var animation := player.get_animation(_qualified(state))
	if state == "walk":
		player.speed_scale = clampf(speed * animation.length / WALK_STRIDE_METERS, 0.60, 1.55)
	elif state == "run":
		player.speed_scale = clampf(speed * animation.length / RUN_STRIDE_METERS, 0.78, 1.55)
	else:
		player.speed_scale = 1.0
	return {"passed": true, "state": state, "speed_scale": player.speed_scale, "role": role, "simulation_authoritative": true}
