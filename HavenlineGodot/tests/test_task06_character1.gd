extends SceneTree

const Motion = preload("res://scripts/character1_motion.gd")
const REQUIRED_LOOPS := ["idle", "walk", "run"]
const REQUIRED_TRANSITIONS := [
	"start_walk", "start_run", "stop", "turn_left_030", "turn_right_030",
	"turn_left_090", "turn_right_090", "turn_left_180", "turn_right_180"
]
const REQUIRED_ACTIONS := [
	"chop", "mine", "dismantle", "deposit", "build", "repair", "rescue",
	"service", "attack_contact"
]

var failures: Array[String] = []
var checks: Array[Dictionary] = []

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
	validate_locomotion_feet(library, "walk", 8.0)
	validate_locomotion_feet(library, "run", 14.0)
	var contract: Dictionary = result.contract
	check("contact contract binds immutable source", contract.source_gltf_sha256 == Motion.SOURCE_GLTF_SHA256)
	check("contact contract supports both Character1 roles", contract.roles == ["player_lead", "core_human_companion"])
	check("motion never grants gameplay impacts", contract.simulation_authoritative and not contract.duplicate_gameplay_impacts_allowed)
	check("T06 does not claim finished tools or weapons", not contract.finished_tool_or_weapon_assets_included)
	check("all action beats are normalized and complete", REQUIRED_ACTIONS.all(func(id): return contract.actions.has(id) and contract.actions[id].contact > 0.0 and contract.actions[id].contact < 1.0))
	for marker in contract.contacts.values():
		check("contact marker exists: " + marker, actor.find_child(marker, true, false) != null)
	check("wood proximity maps to chop", Motion.motion_for_action({"kind":"gather","id":"wood0"}) == "chop")
	check("stone proximity maps to mine", Motion.motion_for_action({"kind":"gather","id":"stone1"}) == "mine")
	check("fuel proximity maps to dismantle foundation", Motion.motion_for_action({"kind":"gather","id":"fuel"}) == "dismantle")
	check("defense repair maps to repair", Motion.motion_for_action({"kind":"defense_repair"}) == "repair")
	check("enemy contact maps to attack foundation", Motion.motion_for_action({"kind":"enemy"}) == "attack_contact")
	var action_state := Motion.update_actor(actor, 0.0, {"kind":"gather","id":"wood0","progress":0.56}, 0.016, "player_lead")
	check("action progress selects and synchronizes the clip", action_state.state == "chop" and is_equal_approx(action_state.progress, 0.56) and player.speed_scale == 0.0)
	var helper_state := Motion.update_actor(actor, 0.0, {"kind":"deposit","progress":0.63}, 0.016, "core_human_companion")
	check("Character1 companion role uses the motion foundation", helper_state.state == "deposit" and helper_state.role == "core_human_companion")
	Motion.update_actor(actor, 2.2, {}, 0.016, "player_lead")
	var walk_state := Motion.update_actor(actor, 2.2, {}, 0.50, "player_lead")
	check("walk cadence is distance synchronized", walk_state.state == "walk" and walk_state.speed_scale >= 0.60 and walk_state.speed_scale <= 1.55)
	Motion.update_actor(actor, 5.6, {}, 0.016, "player_lead")
	var run_state := Motion.update_actor(actor, 5.6, {}, 0.50, "player_lead")
	check("run cadence is distance synchronized", run_state.state == "run" and run_state.speed_scale >= 0.78 and run_state.speed_scale <= 1.55)
	var turn_state := Motion.update_actor(actor, 0.0, {}, 0.016, "player_lead", -95.0)
	check("turn selector preserves direction and bucket", turn_state.state == "turn_left_090")
	var skeleton := find_skeleton(actor)
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
		"required_clips":expected, "critic_approval":false
	}))
	quit(0 if failures.is_empty() else 1)
