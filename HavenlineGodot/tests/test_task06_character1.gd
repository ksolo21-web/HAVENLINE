extends SceneTree

const Motion = preload("res://scripts/character1_motion.gd")
const REQUIRED_LOOPS := ["idle", "walk", "run"]
const REQUIRED_TRANSITIONS := [
	"start_walk", "start_run", "stop_walk", "stop_run", "walk_to_run", "run_to_walk",
	"turn_left_030", "turn_right_030",
	"turn_left_090", "turn_right_090", "turn_left_180", "turn_right_180"
]
const REQUIRED_ACTIONS := [
	"chop", "mine", "dismantle", "deposit", "build", "repair", "rescue",
	"service", "attack_contact"
]
const SEAM_ROTATION_EPSILON_DEGREES := 0.10

var failures: Array[String] = []
var checks: Array[Dictionary] = []
var loop_seam_metrics: Dictionary = {}

func check(label: String, passed: bool) -> void:
	checks.append({"name": label, "passed": passed})
	if not passed:
		failures.append(label)

func find_skeleton(node: Node) -> Skeleton3D:
	if node is Skeleton3D:
		return node
	for child in node.get_children():
		var found := find_skeleton(child)
		if found:
			return found
	return null

func find_player(node: Node) -> AnimationPlayer:
	if node is AnimationPlayer:
		return node
	for child in node.get_children():
		var found := find_player(child)
		if found:
			return found
	return null

func count_types(node: Node, counts: Dictionary) -> void:
	if node is MeshInstance3D:
		counts.meshes += 1
	if node is PhysicsBody3D or node is CollisionObject3D:
		counts.physics += 1
	if node is Skeleton3D:
		counts.skeletons += 1
	for child in node.get_children():
		count_types(child, counts)

func track_for_bone(animation: Animation, bone: String) -> int:
	for track in animation.get_track_count():
		if animation.track_get_type(track) == Animation.TYPE_ROTATION_3D and String(animation.track_get_path(track)).ends_with(":" + bone):
			return track
	return -1

func finite_quaternion(q: Quaternion) -> bool:
	return q.is_finite() and absf(q.length_squared() - 1.0) < 0.002

func validate_animation(id: String, animation: Animation, should_loop: bool) -> void:
	check(id + " has positive bounded duration", animation.length >= 0.28 and animation.length <= 16.0)
	check(id + " loop mode matches contract", (animation.loop_mode == Animation.LOOP_LINEAR) == should_loop)
	var has_motion := false
	var valid := true
	var has_scale_deformation := false
	for track in animation.get_track_count():
		if animation.track_get_type(track) == Animation.TYPE_SCALE_3D:
			var first_scale: Vector3 = animation.track_get_key_value(track, 0)
			for key in animation.track_get_key_count(track):
				var scale: Vector3 = animation.track_get_key_value(track, key)
				has_scale_deformation = has_scale_deformation or not scale.is_finite() or not scale.is_equal_approx(first_scale)
		if animation.track_get_type(track) == Animation.TYPE_ROTATION_3D:
			for key in animation.track_get_key_count(track):
				var q: Quaternion = animation.track_get_key_value(track, key)
				valid = valid and finite_quaternion(q)
				if key > 0 and q.angle_to(animation.track_get_key_value(track, key - 1)) > 0.001:
					has_motion = true
	check(id + " contains no animated scale deformation", not has_scale_deformation)
	check(id + " has finite normalized rotations", valid)
	check(id + " contains authored motion", has_motion or id == "idle")

func validate_locomotion_feet(library: AnimationLibrary, id: String, minimum_degrees: float) -> void:
	var animation := library.get_animation(id)
	for bone in ["L_Foot", "R_Foot", "L_ToeBase", "R_ToeBase"]:
		var track := track_for_bone(animation, bone)
		check(id + " contains " + bone + " rotation", track >= 0)
		if track < 0:
			continue
		var first: Quaternion = animation.track_get_key_value(track, 0)
		var maximum := 0.0
		for key in animation.track_get_key_count(track):
			maximum = maxf(maximum, rad_to_deg(first.angle_to(animation.track_get_key_value(track, key))))
		check(id + " articulates " + bone, maximum >= minimum_degrees)
		var last: Quaternion = animation.track_get_key_value(track, animation.track_get_key_count(track) - 1)
		check(id + " closes " + bone + " cycle", rad_to_deg(first.angle_to(last)) < 0.5)

func validate_loop_seam(library: AnimationLibrary, id: String) -> void:
	var animation := library.get_animation(id)
	var step := minf(1.0 / 120.0, animation.length * 0.02)
	var closed := true
	var velocity_matched := true
	var maximum_seam_motion := 0.0
	var maximum_rotation_error_degrees := 0.0
	var maximum_position_error_meters := 0.0
	var worst_rotation_track := ""
	var worst_position_track := ""
	for track in animation.get_track_count():
		var kind := animation.track_get_type(track)
		if kind == Animation.TYPE_ROTATION_3D:
			var start := animation.rotation_track_interpolate(track, 0.0).normalized()
			var after := animation.rotation_track_interpolate(track, step).normalized()
			var before := animation.rotation_track_interpolate(track, animation.length - step).normalized()
			var finish := animation.rotation_track_interpolate(track, animation.length).normalized()
			closed = closed and rad_to_deg(start.angle_to(finish)) < 0.1
			var incoming_delta := before.inverse() * finish
			var outgoing_delta := start.inverse() * after
			var rotation_error := rad_to_deg(incoming_delta.angle_to(outgoing_delta))
			if rotation_error > maximum_rotation_error_degrees:
				maximum_rotation_error_degrees = rotation_error
				worst_rotation_track = String(animation.track_get_path(track))
			velocity_matched = velocity_matched and rotation_error < SEAM_ROTATION_EPSILON_DEGREES
			maximum_seam_motion = maxf(maximum_seam_motion, rad_to_deg(start.angle_to(after)))
		elif kind == Animation.TYPE_POSITION_3D:
			var start := animation.position_track_interpolate(track, 0.0)
			var after := animation.position_track_interpolate(track, step)
			var before := animation.position_track_interpolate(track, animation.length - step)
			var finish := animation.position_track_interpolate(track, animation.length)
			closed = closed and start.distance_to(finish) < 0.0001
			var position_error := ((finish - before) - (after - start)).length()
			if position_error > maximum_position_error_meters:
				maximum_position_error_meters = position_error
				worst_position_track = String(animation.track_get_path(track))
			velocity_matched = velocity_matched and position_error < 0.0001
			maximum_seam_motion = maxf(maximum_seam_motion, start.distance_to(after) * 100.0)
	loop_seam_metrics[id] = {
		"rotation_epsilon_degrees": SEAM_ROTATION_EPSILON_DEGREES,
		"maximum_rotation_error_degrees": maximum_rotation_error_degrees,
		"worst_rotation_track": worst_rotation_track,
		"maximum_position_error_meters": maximum_position_error_meters,
		"worst_position_track": worst_position_track,
		"maximum_seam_motion": maximum_seam_motion,
	}
	check(id + " closes every transform track", closed)
	check(id + " matches 120 Hz seam velocity direction and magnitude", velocity_matched)
	if id in ["walk", "run"]:
		check(id + " retains non-zero motion through seam", maximum_seam_motion > 0.05)

func _initialize() -> void:
	call_deferred("run")

func run() -> void:
	var source_path := "res://assets/characters/Character1.glb"
	check("Character1 source hash is immutable", FileAccess.get_sha256(source_path) == Motion.SOURCE_GLTF_SHA256)
	var actor := Node3D.new()
	actor.name = "Character1T06Test"
	root.add_child(actor)
	var visual: Node3D = load(source_path).instantiate()
	actor.add_child(visual)
	var source_player := find_player(actor)
	var source_clips := Array(source_player.get_animation_list()) if source_player else []
	check("supplied Character1 has exactly three source clips", source_clips.size() == 3)
	for suffix in ["idle", "walk", "run"]:
		check("supplied source contains " + suffix, source_clips.any(func(clip): return String(clip).ends_with(suffix)))
	var before := {"meshes": 0, "physics": 0, "skeletons": 0}
	count_types(actor, before)
	var result := Motion.install(actor, "player_lead")
	check("T06 installation succeeds", result.get("passed", false))
	if not result.get("passed", false):
		print(JSON.stringify({"suite":"task06_character1","passed":false,"checks":checks,"failures":failures,"install_errors":result.get("errors",[])}))
		quit(1)
		return
	var after := {"meshes": 0, "physics": 0, "skeletons": 0}
	count_types(actor, after)
	check("T06 adds no mesh", after.meshes == before.meshes)
	check("T06 adds no physics body", after.physics == before.physics)
	check("T06 preserves one supplied skeleton", before.skeletons == 1 and after.skeletons == 1)
	var player: AnimationPlayer = result.player
	check("T06 library is installed", player.has_animation_library(Motion.LIBRARY))
	var library := player.get_animation_library(Motion.LIBRARY)
	var expected := REQUIRED_LOOPS + REQUIRED_TRANSITIONS + REQUIRED_ACTIONS
	check("T06 exposes the exact required clip inventory", Array(library.get_animation_list()).size() == expected.size() and expected.all(func(id): return library.has_animation(id)))
	for id in expected:
		validate_animation(id, library.get_animation(id), id in REQUIRED_LOOPS)
	for id in REQUIRED_LOOPS:
		validate_loop_seam(library, id)
	validate_locomotion_feet(library, "walk", 8.0)
	validate_locomotion_feet(library, "run", 14.0)
	var contract: Dictionary = result.contract
	check("contact contract binds immutable source", contract.source_gltf_sha256 == Motion.SOURCE_GLTF_SHA256)
	check("contact contract supports both Character1 roles", contract.roles == ["player_lead", "core_human_companion"])
	check("motion never grants gameplay impacts", contract.simulation_authoritative and not contract.duplicate_gameplay_impacts_allowed)
	check("simulation exclusively owns final root facing", contract.root_facing_authority == "simulation_external")
	check("companion has disclosed visual-only phase offset", is_equal_approx(contract.companion_visual_phase_offset, 0.37))
	check("T06 does not claim finished tools or weapons", not contract.finished_tool_or_weapon_assets_included)
	check("all action beats are normalized and complete", REQUIRED_ACTIONS.all(func(id): return contract.actions.has(id) and contract.actions[id].contact > 0.0 and contract.actions[id].contact < 1.0))
	check("all actions declare a spatial target and contact marker", REQUIRED_ACTIONS.all(func(id): return contract.actions[id].target.size() == 3 and not String(contract.actions[id].marker).is_empty()))
	for marker in contract.contacts.values():
		check("contact marker exists: " + marker, actor.find_child(marker, true, false) != null)
	var two_hand_tip: Node3D = actor.find_child("C1TwoHandContact", true, false).find_child("Contact", true, false)
	var rescue_tip: Node3D = actor.find_child("C1RescueContact", true, false).find_child("Contact", true, false)
	var forward_impact: Node3D = actor.find_child("C1ForwardImpact", true, false)
	check("two-hand proxy is on Character 1 forward side", two_hand_tip.position.z > 0.20)
	check("rescue proxy is on Character 1 forward side", rescue_tip.position.z > 0.20)
	check("impact proxy matches the declared forward target", forward_impact.position.is_equal_approx(Motion.ACTION_SPECS.attack_contact.target))
	check("wood proximity maps to chop", Motion.motion_for_action({"kind":"gather","id":"wood0"}) == "chop")
	check("stone proximity maps to mine", Motion.motion_for_action({"kind":"gather","id":"stone1"}) == "mine")
	check("fuel proximity maps to dismantle foundation", Motion.motion_for_action({"kind":"gather","id":"fuel"}) == "dismantle")
	check("defense repair maps to repair", Motion.motion_for_action({"kind":"defense_repair"}) == "repair")
	check("enemy contact maps to attack foundation", Motion.motion_for_action({"kind":"enemy"}) == "attack_contact")
	var action_state := Motion.update_actor(actor, 0.0, {"kind":"gather","id":"wood0","progress":0.56}, 0.016, "player_lead")
	check("action progress selects and synchronizes the clip", action_state.state == "chop" and is_equal_approx(action_state.progress, 0.56) and player.speed_scale == 1.0)
	var runtime_skeleton := find_skeleton(actor)
	player.play(Motion.LIBRARY + "/idle", 0.0)
	player.seek(library.get_animation("idle").length * 0.5, true)
	runtime_skeleton.force_update_all_bone_transforms()
	var idle_right_hand := runtime_skeleton.get_bone_global_pose(runtime_skeleton.find_bone("R_Hand")).origin
	actor.set_meta("t06_active_clip", "idle")
	var prior_callback_mode := player.callback_mode_process
	player.callback_mode_process = AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_MANUAL
	for frame in 12:
		Motion.update_actor(actor, 0.0, {"kind":"gather","id":"wood0","progress":0.56 * float(frame + 1) / 12.0}, 1.0 / 60.0, "player_lead")
		player.advance(1.0 / 60.0)
	runtime_skeleton.force_update_all_bone_transforms()
	var blended_right_hand := runtime_skeleton.get_bone_global_pose(runtime_skeleton.find_bone("R_Hand")).origin
	check("runtime action blend reaches authored motion", idle_right_hand.distance_to(blended_right_hand) > 0.08)
	player.callback_mode_process = prior_callback_mode
	var helper_state := Motion.update_actor(actor, 0.0, {"kind":"deposit","progress":0.63}, 0.016, "core_human_companion")
	check("Character1 companion role uses the motion foundation", helper_state.state == "deposit" and helper_state.role == "core_human_companion")
	Motion.update_actor(actor, 2.2, {}, 0.016, "player_lead")
	var walk_state := Motion.update_actor(actor, 2.2, {}, 0.50, "player_lead")
	check("walk cadence is distance synchronized", walk_state.state == "walk" and walk_state.speed_scale >= 0.60 and walk_state.speed_scale <= 1.55)
	Motion.update_actor(actor, 5.6, {}, 0.016, "player_lead")
	var run_state := Motion.update_actor(actor, 5.6, {}, 0.50, "player_lead")
	check("run cadence is distance synchronized", run_state.state == "run" and run_state.speed_scale >= 0.78 and run_state.speed_scale <= 1.55)
	var turn_state := Motion.update_actor(actor, 0.0, {}, 0.016, "player_lead", -95.0)
	check("turn selector preserves direction and bucket", turn_state.state == "turn_left_090" and turn_state.facing_delta_degrees == -90.0)
	check("turn reports external facing authority", turn_state.root_facing_authority == "simulation_external")
	var skeleton := find_skeleton(actor)
	for turn_id in ["turn_left_030", "turn_right_030", "turn_left_090", "turn_right_090", "turn_left_180", "turn_right_180"]:
		var turn_animation := library.get_animation(turn_id)
		var side := "L" if turn_id.contains("left") else "R"
		var foot_track := track_for_bone(turn_animation, side + "_Foot")
		var first: Quaternion = turn_animation.rotation_track_interpolate(foot_track, 0.0)
		var middle: Quaternion = turn_animation.rotation_track_interpolate(foot_track, turn_animation.length * 0.52)
		var last: Quaternion = turn_animation.rotation_track_interpolate(foot_track, turn_animation.length)
		check(turn_id + " uses a free-foot pivot", rad_to_deg(first.angle_to(middle)) >= 5.0)
		check(turn_id + " returns the skeleton neutral", rad_to_deg(first.angle_to(last)) < 0.1)
	var action_signatures: Array[Vector3] = []
	for id in REQUIRED_ACTIONS:
		var action_animation := library.get_animation(id)
		player.play(Motion.LIBRARY + "/" + id, 0.0)
		player.seek(action_animation.length * float(Motion.ACTION_SPECS[id].contact), true)
		skeleton.force_update_all_bone_transforms()
		var left := skeleton.get_bone_global_pose(skeleton.find_bone("L_Hand")).origin
		var right := skeleton.get_bone_global_pose(skeleton.find_bone("R_Hand")).origin
		var closest := left if absf(left.x) < absf(right.x) else right
		check(id + " reaches in front of the torso", maxf(left.z, right.z) > 0.08)
		check(id + " brings a working hand toward center", absf(closest.x) < 0.23)
		action_signatures.append((left + right) * 0.5)
	var distinct_pairs := 0
	for left_index in action_signatures.size():
		for right_index in range(left_index + 1, action_signatures.size()):
			if action_signatures[left_index].distance_to(action_signatures[right_index]) > 0.018:
				distinct_pairs += 1
	check("action contact poses are spatially distinct", distinct_pairs >= 30)
	var pose_valid := true
	for id in REQUIRED_LOOPS + REQUIRED_ACTIONS:
		var animation := library.get_animation(id)
		player.play(Motion.LIBRARY + "/" + id)
		for phase in range(25):
			player.seek(animation.length * float(phase) / 24.0, true)
			skeleton.force_update_all_bone_transforms()
			for bone in skeleton.get_bone_count():
				var pose := skeleton.get_bone_global_pose(bone)
				pose_valid = pose_valid and pose.is_finite()
	check("every sampled full-cycle bone pose is finite", pose_valid)
	check("Character1 source hash remains unchanged after installation", FileAccess.get_sha256(source_path) == Motion.SOURCE_GLTF_SHA256)
	actor.free()
	print(JSON.stringify({
		"suite":"task06_character1", "passed":failures.is_empty(), "checks":checks,
		"failures":failures, "check_count":checks.size(), "source_sha256":Motion.SOURCE_GLTF_SHA256,
		"required_clips":expected, "loop_seam_metrics":loop_seam_metrics, "critic_approval":false
	}))
	quit(0 if failures.is_empty() else 1)
