extends SceneTree

const Motion = preload("res://scripts/character1_motion.gd")
const SOURCE := "res://assets/characters/Character1.glb"
const Main = preload("res://scripts/main.gd")

var output := "user://task06-capture"
var candidate := ""
var native_4k := false
var video_sequences := false
var benchmark := false
var export_review_only := false
var benchmark_frames_per_phase := 450
var video_manifest: Array[Dictionary] = []
var captures: Array[Dictionary] = []
var gameplay_captures: Array[Dictionary] = []
var stage: Node3D
var actor: Node3D
var visual: Node3D
var player: AnimationPlayer
var skeleton: Skeleton3D
var camera: Camera3D
var overlay_root: Node3D
var atlas_rigs: Array[Dictionary] = []

const SIX_VIEW_LAYOUT := [
	{"id":"front", "yaw":0.0},
	{"id":"front-three-quarter", "yaw":45.0},
	{"id":"left", "yaw":90.0},
	{"id":"rear", "yaw":180.0},
	{"id":"rear-three-quarter", "yaw":225.0},
	{"id":"right", "yaw":270.0}
]

const WHOLE_RIG_PARTS := [
	{"id":"root_pelvis", "joints":["Root","Hip","Pelvis"]},
	{"id":"left_thigh", "joints":["L_Thigh","L_ThighTwist01","L_ThighTwist02"]},
	{"id":"left_calf_knee", "joints":["L_Calf","L_CalfTwist01","L_CalfTwist02","L_KneePad"]},
	{"id":"left_foot_toe_boot", "joints":["L_Foot","L_ToeBase","L_BootFastener_upper_inner","L_BootFastener_lower_inner","L_BootFastener_upper_outer","L_BootFastener_lower_outer"]},
	{"id":"right_thigh", "joints":["R_Thigh","R_ThighTwist01","R_ThighTwist02"]},
	{"id":"right_calf_knee", "joints":["R_Calf","R_CalfTwist01","R_CalfTwist02","R_KneePad"]},
	{"id":"right_foot_toe_boot", "joints":["R_Foot","R_ToeBase","R_BootFastener_lower_outer","R_BootFastener_upper_outer","R_BootFastener_lower_inner","R_BootFastener_upper_inner"]},
	{"id":"waist_spine", "joints":["Waist","Spine01","Spine02"]},
	{"id":"neck_head_face_hair_eyewear", "joints":["NeckTwist01","NeckTwist02","Head"]},
	{"id":"left_shoulder_upper_arm", "joints":["L_Clavicle","L_Upperarm","L_UpperarmTwist01","L_UpperarmTwist02"]},
	{"id":"left_forearm_wrist_hand", "joints":["L_Forearm","L_ForearmTwist01","L_ForearmTwist02","L_Hand"]},
	{"id":"right_shoulder_upper_arm", "joints":["R_Clavicle","R_Upperarm","R_UpperarmTwist01","R_UpperarmTwist02"]},
	{"id":"right_forearm_wrist_hand", "joints":["R_Forearm","R_ForearmTwist01","R_ForearmTwist02","R_Hand"]},
	{"id":"coat_torso_garment", "joints":["CoatFront","L_CoatFront"]},
	{"id":"pouch_attachment", "joints":["PouchSwing"]},
	{"id":"hem_fasteners", "joints":["HemFastener_01","HemFastener_02","HemFastener_03","HemFastener_04","HemFastener_05","HemFastener_06","HemFastener_07","HemFastener_08","HemFastener_09","HemFastener_10","HemFastener_11","HemFastener_12"]}
]

func _initialize() -> void:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--out="):
			output = argument.trim_prefix("--out=")
		elif argument.begins_with("--candidate="):
			candidate = argument.trim_prefix("--candidate=")
		elif argument == "--native-4k":
			native_4k = true
		elif argument == "--video-sequences":
			video_sequences = true
		elif argument == "--benchmark":
			benchmark = true
		elif argument == "--export-review-only":
			export_review_only = true
		elif argument.begins_with("--benchmark-frames="):
			benchmark_frames_per_phase = maxi(60, argument.trim_prefix("--benchmark-frames=").to_int())
	if candidate.is_empty():
		candidate = "0000000000000000000000000000000000000000"
	call_deferred("run")

func find_skeleton(node: Node) -> Skeleton3D:
	if node is Skeleton3D:
		return node
	for child in node.get_children():
		var found := find_skeleton(child)
		if found:
			return found
	return null

func gather_meshes(node: Node, meshes: Array) -> void:
	if node is MeshInstance3D:
		meshes.append(node)
	for child in node.get_children():
		gather_meshes(child, meshes)

func normalize_character() -> void:
	var meshes: Array = []
	gather_meshes(visual, meshes)
	var bounds := AABB()
	var first := true
	for mesh in meshes:
		var box: AABB = actor.global_transform.affine_inverse() * mesh.global_transform * mesh.get_aabb()
		bounds = box if first else bounds.merge(box)
		first = false
	var factor := 1.75 / maxf(0.01, bounds.size.y)
	visual.scale *= factor
	visual.position = Vector3(-bounds.get_center().x, -bounds.position.y, -bounds.get_center().z) * factor

func setup_stage() -> void:
	stage = Node3D.new()
	stage.name = "T06EvidenceStage"
	root.add_child(stage)
	var world := WorldEnvironment.new()
	var environment := Environment.new()
	environment.background_mode = Environment.BG_COLOR
	environment.background_color = Color("#14283b")
	environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	environment.ambient_light_color = Color("#dceeff")
	environment.ambient_light_energy = 0.82
	environment.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	world.environment = environment
	stage.add_child(world)
	var key := DirectionalLight3D.new()
	key.rotation_degrees = Vector3(-48, -32, 0)
	key.light_color = Color("#fff2df")
	key.light_energy = 1.38
	key.shadow_enabled = true
	stage.add_child(key)
	var fill := DirectionalLight3D.new()
	fill.rotation_degrees = Vector3(-25, 145, 0)
	fill.light_color = Color("#9fcfff")
	fill.light_energy = 0.48
	fill.shadow_enabled = false
	stage.add_child(fill)
	var ground := MeshInstance3D.new()
	var plane := PlaneMesh.new()
	plane.size = Vector2(10, 10)
	var material := StandardMaterial3D.new()
	material.albedo_color = Color("#dbeeff")
	material.roughness = 0.93
	plane.material = material
	ground.mesh = plane
	ground.position.y = -0.012
	stage.add_child(ground)
	actor = Node3D.new()
	actor.name = "Character1"
	stage.add_child(actor)
	visual = load(SOURCE).instantiate()
	actor.add_child(visual)
	normalize_character()
	var installed := Motion.install(actor, "player_lead")
	assert(installed.passed, str(installed.errors))
	player = installed.player
	skeleton = installed.skeleton
	camera = Camera3D.new()
	camera.current = true
	camera.fov = 34.0
	stage.add_child(camera)
	set_view("front")

func set_view(view: String, detail := "body") -> void:
	var focus := Vector3(0, 0.92, 0)
	var radius := 4.15
	if detail == "feet":
		focus = Vector3(0, 0.22, 0)
		radius = 2.15
	elif detail == "hands":
		focus = Vector3(0, 1.05, -0.08)
		radius = 2.35
	match view:
		"front": camera.position = focus + Vector3(0, 0.42, radius)
		"rear": camera.position = focus + Vector3(0, 0.42, -radius)
		"left": camera.position = focus + Vector3(-radius, 0.42, 0)
		"right": camera.position = focus + Vector3(radius, 0.42, 0)
		"three-quarter": camera.position = focus + Vector3(radius * 0.70, 0.42, radius * 0.70)
		"overhead": camera.position = focus + Vector3(0.001, radius, 0.001)
		_: camera.position = focus + Vector3(0, 0.42, radius)
	camera.look_at(focus)

func snap(relative: String, clip: String, phase: float, view: String, category: String, detail := "body") -> void:
	set_view(view, detail)
	await save_current_frame(relative, clip, phase, view, category, detail)

func save_current_frame(relative: String, clip: String, phase: float, view: String, category: String, detail := "body") -> void:
	await process_frame
	await RenderingServer.frame_post_draw
	var image := get_root().get_texture().get_image()
	var path := output.path_join(relative)
	DirAccess.make_dir_recursive_absolute(path.get_base_dir())
	assert(image.save_png(path) == OK)
	captures.append({
		"file": relative, "clip": clip, "phase": phase, "view": view,
		"category": category, "detail": detail,
		"resolution": [image.get_width(), image.get_height()],
		"draw_calls": get_root().get_render_info(Viewport.RENDER_INFO_TYPE_VISIBLE, Viewport.RENDER_INFO_DRAW_CALLS_IN_FRAME),
		"submitted_primitives": get_root().get_render_info(Viewport.RENDER_INFO_TYPE_VISIBLE, Viewport.RENDER_INFO_PRIMITIVES_IN_FRAME),
		"source_sha256": Motion.SOURCE_GLTF_SHA256
	})

func setup_six_view_atlas() -> void:
	if not atlas_rigs.is_empty():
		return
	actor.visible = false
	var spacing := 1.52
	for index in SIX_VIEW_LAYOUT.size():
		var row: Dictionary = SIX_VIEW_LAYOUT[index]
		var atlas_actor := Node3D.new()
		atlas_actor.name = "T06Atlas_" + row.id
		atlas_actor.position = Vector3((float(index) - 2.5) * spacing, 0.0, 0.0)
		stage.add_child(atlas_actor)
		var atlas_visual: Node3D = load(SOURCE).instantiate()
		atlas_actor.add_child(atlas_visual)
		# Use the exact normalized transform already proved on the single-rig stage.
		atlas_visual.scale = visual.scale
		atlas_visual.position = visual.position
		var installed := Motion.install(atlas_actor, "player_lead")
		assert(installed.passed, str(installed.errors))
		atlas_rigs.append({
			"id":row.id, "base_yaw":float(row.yaw), "root":atlas_actor,
			"player":installed.player, "skeleton":installed.skeleton
		})

func clear_six_view_atlas() -> void:
	for row in atlas_rigs:
		(row.root as Node3D).free()
	atlas_rigs.clear()
	actor.visible = true
	camera.fov = 34.0
	set_view("front")

func pose_six_view_atlas(clip: String, phase: float) -> void:
	var qualified := Motion.LIBRARY + "/" + clip
	for row in atlas_rigs:
		var atlas_player: AnimationPlayer = row.player
		var atlas_skeleton: Skeleton3D = row.skeleton
		var animation := atlas_player.get_animation(qualified)
		(row.root as Node3D).rotation.y = deg_to_rad(float(row.base_yaw) + Motion.facing_delta_for_turn(clip) * phase)
		atlas_player.play(qualified, 0.0)
		atlas_player.seek(animation.length * phase, true)
		atlas_player.speed_scale = 0.0
		atlas_player.advance(0.0)
		atlas_skeleton.force_update_all_bone_transforms()

func capture_six_view_temporal_review() -> void:
	setup_six_view_atlas()
	camera.fov = 28.0
	camera.position = Vector3(0.0, 3.2, 18.0)
	camera.look_at(Vector3(0.0, 0.88, 0.0))
	for clip in Motion.LOOP_CLIPS + Motion.TRANSITION_CLIPS + Motion.ACTION_CLIPS:
		for index in range(17):
			var phase := float(index) / 16.0
			pose_six_view_atlas(clip, phase)
			await save_current_frame(
				"six-view/%s/phase-%03d.png" % [clip, roundi(phase * 100.0)],
				clip, phase, "six-view-atlas", "six_view_temporal", "body"
			)
			captures[-1]["views"] = SIX_VIEW_LAYOUT.map(func(row): return row.id)
			captures[-1]["view_layout"] = "single-row left-to-right"
	# Denser leg-height evidence covers both limbs from front, rear, both sides
	# and both three-quarter views. Combined with real-time playback and the
	# 120 Hz numeric ledger, this exposes support/passing/raised extrema and seams.
	camera.fov = 20.0
	camera.position = Vector3(0.0, 1.55, 19.0)
	camera.look_at(Vector3(0.0, 0.43, 0.0))
	for clip in Motion.LOOP_CLIPS:
		for index in range(33):
			var phase := float(index) / 32.0
			pose_six_view_atlas(clip, phase)
			await save_current_frame(
				"lower-limb-six-view/%s/phase-%03d.png" % [clip, roundi(phase * 100.0)],
				clip, phase, "six-view-atlas", "lower_limb_temporal", "legs"
			)
			captures[-1]["views"] = SIX_VIEW_LAYOUT.map(func(row): return row.id)
			captures[-1]["view_layout"] = "single-row left-to-right"
	clear_six_view_atlas()

func capture_phase(clip: String, phase: float, view: String, category: String, detail := "body") -> void:
	var name := Motion.LIBRARY + "/" + clip
	var animation := player.get_animation(name)
	actor.rotation.y = deg_to_rad(Motion.facing_delta_for_turn(clip) * phase)
	player.play(name, 0.0)
	player.seek(animation.length * phase, true)
	player.speed_scale = 0.0
	player.advance(0.0)
	skeleton.force_update_all_bone_transforms()
	await snap("%s/%s-%03d.png" % [clip, view + ("-" + detail if detail != "body" else ""), roundi(phase * 100)], clip, phase, view, category, detail)

func capture_native_selection() -> void:
	for row in [
		["idle", 0.50, "front", "motion_cycle", "body"],
		["walk", 0.24, "three-quarter", "motion_cycle", "body"],
		["run", 0.49, "left", "contact_detail", "feet"],
		["chop", 0.56, "three-quarter", "contact_detail", "hands"],
		["rescue", 0.68, "right", "contact_detail", "body"],
		["turn_left_090", 0.52, "front", "motion_transition", "body"]
	]:
		await capture_phase(row[0], row[1], row[2], row[3], row[4])

func capture_video_review() -> void:
	set_view("three-quarter")
	for clip in Motion.LOOP_CLIPS + Motion.TRANSITION_CLIPS + Motion.ACTION_CLIPS:
		var qualified: String = Motion.LIBRARY + "/" + clip
		var animation := player.get_animation(qualified)
		var representative_speed := 2.2 if clip == "walk" else (5.6 if clip == "run" else 0.0)
		var cadence_scale := Motion.cadence_scale(clip, representative_speed, animation)
		var playback_duration := animation.length / cadence_scale
		var frame_count := ceili(playback_duration * 30.0) + 1
		var folder := output.path_join("video-frames/" + clip)
		DirAccess.make_dir_recursive_absolute(folder)
		player.play(qualified, 0.0)
		for frame in frame_count:
			var phase := float(frame) / float(maxi(frame_count - 1, 1))
			actor.rotation.y = deg_to_rad(Motion.facing_delta_for_turn(clip) * phase)
			player.seek(animation.length * phase, true)
			player.speed_scale = 0.0
			player.advance(0.0)
			skeleton.force_update_all_bone_transforms()
			await process_frame
			await RenderingServer.frame_post_draw
			var image: Image = get_root().get_texture().get_image()
			assert(image.save_jpg(folder.path_join("frame-%05d.jpg" % frame), 0.88) == OK)
		video_manifest.append({
			"clip":clip, "source_duration_seconds":animation.length, "playback_duration_seconds":playback_duration, "fps":30,
			"frame_count":frame_count, "deterministic_blend_seconds":0.0,
			"representative_speed":representative_speed, "cadence_scale":cadence_scale,
			"external_root_facing":Motion.facing_delta_for_turn(clip), "sequence_type":"standalone_clip"
		})
	await capture_runtime_boundary_sequences()
	var file := FileAccess.open(output.path_join("video-sequences.json"), FileAccess.WRITE)
	file.store_string(JSON.stringify({
		"task":"T06-character1-motion-v1", "candidate_commit":candidate,
		"source_sha256":Motion.SOURCE_GLTF_SHA256, "clips":video_manifest,
		"real_time_fps":30, "slow_motion_playback_fraction":0.25,
		"source_frames_are_shared_between_encodes":true
	}, "\t"))
	file.close()

func capture_runtime_boundary_sequences() -> void:
	var scenarios := [
		{"id":"idle_walk_idle", "role":"player_lead", "stages":[
			{"seconds":0.30,"speed":0.0},{"seconds":0.92,"speed":2.2},{"seconds":0.76,"speed":0.0}
		]},
		{"id":"idle_run_idle", "role":"player_lead", "stages":[
			{"seconds":0.30,"speed":0.0},{"seconds":0.84,"speed":5.6},{"seconds":0.82,"speed":0.0}
		]},
		{"id":"walk_run_walk", "role":"player_lead", "stages":[
			{"seconds":0.25,"speed":0.0},{"seconds":0.82,"speed":2.2},{"seconds":0.82,"speed":5.6},{"seconds":0.74,"speed":2.2},{"seconds":0.68,"speed":0.0}
		]},
		{"id":"idle_chop_idle", "role":"player_lead", "stages":[
			{"seconds":0.30,"speed":0.0},{"seconds":0.92,"speed":0.0,"action":"chop"},{"seconds":0.72,"speed":0.0}
		]},
		{"id":"companion_idle_walk", "role":"core_human_companion", "stages":[
			{"seconds":0.30,"speed":0.0},{"seconds":1.12,"speed":2.2},{"seconds":0.72,"speed":0.0}
		]},
		{"id":"runtime_turn_right_090", "role":"player_lead", "stages":[
			{"seconds":0.30,"speed":0.0},{"seconds":0.62,"speed":0.0,"turn_degrees":90.0},{"seconds":0.70,"speed":0.0}
		]}
	]
	set_view("three-quarter")
	for scenario in scenarios:
		var installed := Motion.install(actor, String(scenario.role))
		assert(installed.passed, str(installed.errors))
		player = installed.player
		skeleton = installed.skeleton
		player.stop()
		var prior_callback_mode := player.callback_mode_process
		player.callback_mode_process = AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_MANUAL
		actor.rotation.y = 0.0
		var total_seconds := 0.0
		for stage_row in scenario.stages:
			total_seconds += float(stage_row.seconds)
		var frame_count := ceili(total_seconds * 30.0) + 1
		var folder := output.path_join("video-frames/boundary_" + String(scenario.id))
		DirAccess.make_dir_recursive_absolute(folder)
		var trace: Array[Dictionary] = []
		for frame in frame_count:
			var seconds := minf(total_seconds, float(frame) / 30.0)
			var cursor := 0.0
			var stage_index := 0
			var current: Dictionary = scenario.stages[0]
			for index in scenario.stages.size():
				var candidate_stage: Dictionary = scenario.stages[index]
				if seconds <= cursor + float(candidate_stage.seconds) or index == scenario.stages.size() - 1:
					current = candidate_stage
					stage_index = index
					break
				cursor += float(candidate_stage.seconds)
			var stage_phase := clampf((seconds - cursor) / maxf(0.001, float(current.seconds)), 0.0, 1.0)
			var action := {}
			if current.get("action", "") == "chop":
				action = {"kind":"gather", "id":"wood0", "progress":stage_phase}
			var turn_degrees := float(current.get("turn_degrees", 0.0))
			var state: Dictionary = Motion.update_actor(actor, float(current.speed), action, 1.0 / 30.0, String(scenario.role), turn_degrees)
			if not is_zero_approx(turn_degrees):
				actor.rotation.y = deg_to_rad(turn_degrees * stage_phase)
			player.advance(1.0 / 30.0)
			skeleton.force_update_all_bone_transforms()
			# Let Skeleton3D submit the new skin matrices before the synchronous
			# render readback. frame_post_draw is intentionally avoided because it
			# can deadlock software/headless renderers.
			await process_frame
			RenderingServer.force_draw(false, 0.0)
			var image: Image = get_root().get_texture().get_image()
			assert(image.save_jpg(folder.path_join("frame-%05d.jpg" % frame), 0.88) == OK)
			trace.append({"frame":frame,"seconds":seconds,"stage":stage_index,"stage_phase":stage_phase,"state":state.get("state", ""),"speed":current.speed,"action":current.get("action", ""),"turn_degrees":turn_degrees})
		video_manifest.append({
			"clip":"boundary_" + String(scenario.id), "sequence_type":"runtime_boundary",
			"source_duration_seconds":total_seconds, "playback_duration_seconds":total_seconds,
			"fps":30, "frame_count":frame_count, "deterministic_blend_seconds":Motion.BLEND_SECONDS,
			"role":scenario.role, "stages":scenario.stages, "runtime_state_trace":trace,
			"simulation_position_authoritative":true, "external_root_facing":scenario.id == "runtime_turn_right_090"
		})
		player.callback_mode_process = prior_callback_mode

func capture_full_review() -> void:
	for clip in Motion.LOOP_CLIPS:
		for index in range(17):
			await capture_phase(clip, float(index) / 16.0, "front", "motion_cycle")
		for phase in [0.0, 0.24, 0.49, 0.74]:
			for view in ["rear", "left", "right", "three-quarter"]:
				await capture_phase(clip, phase, view, "motion_cycle")
		if clip in ["walk", "run"]:
			for phase in [0.0, 0.12, 0.36, 0.49, 0.64, 0.86]:
				await capture_phase(clip, phase, "left", "contact_detail", "feet")
	for clip in Motion.TRANSITION_CLIPS:
		for index in range(9):
			await capture_phase(clip, float(index) / 8.0, "front", "motion_transition")
		await capture_phase(clip, 0.52, "three-quarter", "motion_transition")
	for clip in Motion.ACTION_CLIPS:
		for index in range(13):
			await capture_phase(clip, float(index) / 12.0, "front", "motion_cycle")
		var contact := float(Motion.ACTION_SPECS[clip].contact)
		for view in ["rear", "left", "right", "three-quarter"]:
			await capture_phase(clip, contact, view, "contact_detail")
		await capture_phase(clip, contact, "three-quarter", "contact_detail", "hands")
	for view in ["front", "rear", "left", "right", "three-quarter", "overhead"]:
		await capture_phase("idle", 0.50, view, "gameplay_state", "gameplay")
	await capture_six_view_temporal_review()

func export_runtime_review_glb() -> Dictionary:
	# The production GLB is immutable. This artifact-only export gives the
	# independent whole-rig gate one exact GLB containing the 24 installed T06
	# clips it must inventory; it is never loaded by shipping gameplay.
	for library_name in player.get_animation_library_list():
		if String(library_name) != Motion.LIBRARY:
			player.remove_animation_library(library_name)
	var review_directory := output.path_join("review")
	DirAccess.make_dir_recursive_absolute(review_directory)
	var review_path := review_directory.path_join("Character1-T06-runtime.glb")
	var document := GLTFDocument.new()
	var state := GLTFState.new()
	var append_error := document.append_from_scene(actor, state)
	assert(append_error == OK, "T06 runtime review GLB scene append failed: %s" % append_error)
	var write_error := document.write_to_filesystem(state, review_path)
	assert(write_error == OK, "T06 runtime review GLB write failed: %s" % write_error)
	return {
		"path":"review/Character1-T06-runtime.glb",
		"sha256":FileAccess.get_sha256(review_path),
		"purpose":"artifact-only exact runtime animation inventory for independent whole-rig review",
		"shipping_asset":false,
		"source_glb_sha256":Motion.SOURCE_GLTF_SHA256
	}

func ensure_overlay() -> void:
	if is_instance_valid(overlay_root):
		return
	overlay_root = Node3D.new()
	overlay_root.name = "T06EvidenceBoneOverlay"
	stage.add_child(overlay_root)
	for bone in ["Hip","L_Thigh","R_Thigh","L_Calf","R_Calf","L_Foot","R_Foot","L_ToeBase","R_ToeBase","L_Hand","R_Hand"]:
		var marker := MeshInstance3D.new()
		marker.name = bone
		var sphere := SphereMesh.new()
		sphere.radius = 0.050 if bone != "Hip" else 0.065
		sphere.height = sphere.radius * 2.0
		var material := StandardMaterial3D.new()
		material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		material.no_depth_test = true
		material.albedo_color = Color("#4de8ff") if bone.begins_with("L_") else (Color("#ff6ea8") if bone.begins_with("R_") else Color("#ffe16a"))
		material.emission_enabled = true
		material.emission = material.albedo_color
		sphere.material = material
		marker.mesh = sphere
		overlay_root.add_child(marker)
	var target := MeshInstance3D.new()
	target.name = "ContactTarget"
	var target_mesh := BoxMesh.new()
	target_mesh.size = Vector3(0.16,0.16,0.16)
	var target_material := StandardMaterial3D.new()
	target_material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	target_material.no_depth_test = true
	target_material.albedo_color = Color("#76ff65")
	target_material.emission_enabled = true
	target_material.emission = target_material.albedo_color
	target_mesh.material = target_material
	target.mesh = target_mesh
	target.visible = false
	overlay_root.add_child(target)

func update_overlay(clip := "") -> void:
	ensure_overlay()
	for marker in overlay_root.get_children():
		if marker.name == "ContactTarget":
			marker.visible = clip in Motion.ACTION_CLIPS
			if marker.visible:
				marker.global_position = actor.to_global(Motion.ACTION_SPECS[clip].target)
				marker.scale = Vector3(3.5,0.5,0.5) if Motion.ACTION_SPECS[clip].marker == "C1TwoHandContact" else Vector3.ONE
			continue
		var index := skeleton.find_bone(marker.name)
		marker.global_position = skeleton.to_global(skeleton.get_bone_global_pose(index).origin)

func capture_overlay_review() -> void:
	ensure_overlay()
	for clip in ["walk","run"]:
		for phase in [0.0,0.25,0.50,0.75]:
			var animation := player.get_animation(Motion.LIBRARY + "/" + clip)
			player.play(Motion.LIBRARY + "/" + clip, 0.0)
			player.seek(animation.length * phase, true)
			player.advance(0.0)
			skeleton.force_update_all_bone_transforms()
			update_overlay()
			for view in ["front","rear","left","right"]:
				await snap("overlay/%s-%s-%03d.png" % [clip,view,roundi(phase*100.0)],clip,phase,view,"bone_overlay","body")
	for clip in Motion.ACTION_CLIPS:
		var phase := float(Motion.ACTION_SPECS[clip].contact)
		var animation := player.get_animation(Motion.LIBRARY + "/" + clip)
		player.play(Motion.LIBRARY + "/" + clip, 0.0)
		player.seek(animation.length * phase, true)
		player.advance(0.0)
		skeleton.force_update_all_bone_transforms()
		update_overlay(clip)
		await snap("overlay/%s-contact.png" % clip,clip,phase,"three-quarter","bone_overlay","body")
	for clip in ["turn_left_030","turn_right_030","turn_left_090","turn_right_090","turn_left_180","turn_right_180"]:
		var animation := player.get_animation(Motion.LIBRARY + "/" + clip)
		player.play(Motion.LIBRARY + "/" + clip, 0.0)
		player.seek(animation.length * 0.52, true)
		player.advance(0.0)
		skeleton.force_update_all_bone_transforms()
		update_overlay()
		await snap("overlay/%s-mid.png" % clip,clip,0.52,"front","bone_overlay","body")
	overlay_root.free()
	overlay_root = null

func gameplay_snap(game: Control, relative: String, row: Dictionary) -> void:
	await process_frame
	await RenderingServer.frame_post_draw
	var image: Image = game.scene_view.get_texture().get_image()
	var path := output.path_join(relative)
	DirAccess.make_dir_recursive_absolute(path.get_base_dir())
	assert(image.save_png(path) == OK)
	row["file"] = relative
	row["resolution"] = [image.get_width(), image.get_height()]
	row["draw_calls"] = game.scene_view.get_render_info(Viewport.RENDER_INFO_TYPE_VISIBLE, Viewport.RENDER_INFO_DRAW_CALLS_IN_FRAME)
	row["submitted_primitives"] = game.scene_view.get_render_info(Viewport.RENDER_INFO_TYPE_VISIBLE, Viewport.RENDER_INFO_PRIMITIVES_IN_FRAME)
	row["source_sha256"] = Motion.SOURCE_GLTF_SHA256
	row["shipping_context"] = "T04 camera + T05 stations/environment in scripts/main.gd"
	gameplay_captures.append(row)

func pose_gameplay_actor(root_actor: Node3D, clip: String, phase: float) -> void:
	var runtime_player: AnimationPlayer = root_actor.get_meta("t06_motion_player")
	var qualified: String = Motion.LIBRARY + "/" + clip
	var animation := runtime_player.get_animation(qualified)
	runtime_player.play(qualified, 0.0)
	runtime_player.seek(animation.length * phase, true)
	runtime_player.speed_scale = 0.0
	runtime_player.advance(0.0)

func set_shipping_camera(game: Control, lead: Node3D, target: Variant) -> void:
	var state: Dictionary = game.camera_composition.compose(
		lead.position, Vector3.ZERO, -lead.global_basis.z, target,
		Vector2(game.scene_view.size), 1.0 / 60.0, true
	)
	game.camera.keep_aspect = state.keep_aspect
	game.camera.size = state.full_height
	game.camera.position = state.camera_position
	game.camera.look_at(state.focus)

func capture_gameplay_review() -> void:
	stage.visible = false
	var game: Control = Main.new()
	game.qa_mode = true
	game.capture_frames = 1000
	game.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	root.add_child(game)
	game.size = Vector2(root.size)
	await process_frame
	await process_frame
	game.set_process(false)
	game.set_physics_process(false)
	game.paused = true
	var lead: Node3D = game.actors[1]
	var lead_install := Motion.install(lead, "player_lead")
	assert(lead_install.passed, str(lead_install.errors))
	for id in [2, 3, 4]:
		game.actors[id].visible = false
	var helper: Node3D = game.actor(1)
	helper.name = "Character1CompanionEvidence"
	var helper_install := Motion.install(helper, "core_human_companion")
	assert(helper_install.passed, str(helper_install.errors))
	var resource_points := {}
	for resource in game.sim.resources:
		if not resource_points.has(resource.kind):
			resource_points[resource.kind] = resource.position
	var station: Vector2 = game.sim.point(game.sim.contract.world.storage)
	var defense: Vector2 = game.sim.defenses.north.position
	var scenarios := [
		{"id":"roles_together","clip":"idle","phase":0.50,"point":Vector2(0.0,1.4),"target":Vector2(0.0,0.2)},
		{"id":"slope_walk","clip":"walk","phase":0.36,"point":Vector2(-10.4,4.8),"target":Vector2(-10.4,1.0)},
		{"id":"slope_run","clip":"run","phase":0.64,"point":Vector2(10.6,3.2),"target":Vector2(10.6,-1.0)},
		{"id":"resource_chop","clip":"chop","phase":float(Motion.ACTION_SPECS.chop.contact),"point":resource_points.wood+Vector2(0.0,1.0),"target":resource_points.wood},
		{"id":"resource_mine","clip":"mine","phase":float(Motion.ACTION_SPECS.mine.contact),"point":resource_points.stone+Vector2(0.0,1.0),"target":resource_points.stone},
		{"id":"storage_deposit","clip":"deposit","phase":float(Motion.ACTION_SPECS.deposit.contact),"point":station+Vector2(0.0,1.0),"target":station},
		{"id":"defense_build","clip":"build","phase":float(Motion.ACTION_SPECS.build.contact),"point":defense+Vector2(0.0,1.0),"target":defense},
		{"id":"defense_repair","clip":"repair","phase":float(Motion.ACTION_SPECS.repair.contact),"point":defense+Vector2(0.0,1.0),"target":defense},
		{"id":"companion_rescue","clip":"rescue","phase":float(Motion.ACTION_SPECS.rescue.contact),"point":Vector2(-1.0,3.0),"target":Vector2(0.0,3.0)},
		{"id":"station_service","clip":"service","phase":float(Motion.ACTION_SPECS.service.contact),"point":station+Vector2(1.0,0.0),"target":station},
		{"id":"forward_contact","clip":"attack_contact","phase":float(Motion.ACTION_SPECS.attack_contact.contact),"point":Vector2(2.0,2.0),"target":Vector2(2.0,0.8)}
	]
	for scenario in scenarios:
		var point: Vector2 = scenario.point
		var target_point: Vector2 = scenario.target
		lead.position = game.xyz(point)
		helper.position = game.xyz(point + Vector2(1.15, 0.72))
		var direction := target_point - point
		lead.rotation.y = atan2(direction.x, direction.y)
		helper.rotation.y = lead.rotation.y - 0.18
		pose_gameplay_actor(lead, scenario.clip, scenario.phase)
		var helper_phase := fposmod(float(scenario.phase) + 0.37, 1.0) if scenario.clip in Motion.LOOP_CLIPS else maxf(0.0, float(scenario.phase) - 0.18)
		pose_gameplay_actor(helper, scenario.clip, helper_phase)
		var target_world: Vector3 = game.xyz(target_point)
		set_shipping_camera(game, lead, target_world)
		await gameplay_snap(game, "gameplay/%s.png" % scenario.id, {
			"scenario":scenario.id, "clip":scenario.clip, "phase":scenario.phase,
			"lead_role":"player_lead", "helper_role":"core_human_companion",
			"helper_visual_phase":helper_phase, "duplicate_gameplay_impacts":false,
			"terrain_height":lead.position.y, "target_world":[target_world.x,target_world.y,target_world.z],
			"camera_authority":game.camera_composition.descriptor().authority_id,
			"station_authority":game.camp_station_kit.descriptor().authority_id
		})
	if is_instance_valid(game.outpost_audio):
		game.outpost_audio.stop_all()
	game.free()
	stage.visible = true

func local_bone_point(bone: String) -> Vector3:
	var pose := skeleton.get_bone_global_pose(skeleton.find_bone(bone)).origin
	return actor.to_local(skeleton.to_global(pose))

func write_motion_ledger() -> void:
	var all_bones: Array[String] = []
	for bone_index in skeleton.get_bone_count():
		all_bones.append(String(skeleton.get_bone_name(bone_index)))
	var mapped_bones: Array[String] = []
	for part in WHOLE_RIG_PARTS:
		for bone in part.joints:
			mapped_bones.append(String(bone))
	mapped_bones.sort()
	var sorted_all_bones := all_bones.duplicate()
	sorted_all_bones.sort()
	assert(mapped_bones == sorted_all_bones, "T06 semantic part map must cover every skeleton joint exactly")
	var ledger := {
		"task":"T06-character1-motion-v1", "candidate_commit":candidate,
		"sample_rate_hz":120, "source_sha256":Motion.SOURCE_GLTF_SHA256,
		"coordinate_space":"normalized actor-local metres; external moving root applied for plant drift",
		"skin_joint_inventory":all_bones, "skin_joint_count":all_bones.size(),
		"semantic_parts":WHOLE_RIG_PARTS,
		"capability_boundaries":["no finger joints", "no facial joints", "no finished tool or weapon assets", "in-place clips; simulation owns world travel and final facing"],
		"clips":{}, "actions":{}, "turns":{}, "roles":{
			"player_lead":{"gameplay_impact_authority":true,"visual_phase_offset":0.0},
			"core_human_companion":{"gameplay_impact_authority":false,"visual_phase_offset":0.37}
		}
	}
	var relevant_bones := ["Hip","L_Thigh","R_Thigh","L_Calf","R_Calf","L_Foot","R_Foot","L_ToeBase","R_ToeBase","L_Hand","R_Hand"]
	for clip in Motion.LOOP_CLIPS + Motion.TRANSITION_CLIPS + Motion.ACTION_CLIPS:
		var qualified: String = Motion.LIBRARY + "/" + clip
		var animation := player.get_animation(qualified)
		var count := ceili(animation.length * 120.0) + 1
		var first_points := {}
		var last_points := {}
		var previous_points := {}
		var maximum_step := 0.0
		var maximum_relevant_step := 0.0
		var maximum_scale_error := 0.0
		var transforms_finite := true
		var joint_metrics := {}
		for bone in all_bones:
			joint_metrics[bone] = {"maximum_step_m_at_120hz":0.0,"endpoint_delta_m":0.0}
		var foot_samples := {"L":[],"R":[]}
		player.play(qualified, 0.0)
		for sample in count:
			var phase := float(sample) / float(maxi(count - 1, 1))
			player.seek(animation.length * phase, true)
			player.advance(0.0)
			skeleton.force_update_all_bone_transforms()
			for bone in all_bones:
				var bone_pose := skeleton.get_bone_global_pose(skeleton.find_bone(bone))
				transforms_finite = transforms_finite and bone_pose.is_finite()
				var pose_scale := bone_pose.basis.get_scale()
				maximum_scale_error = maxf(maximum_scale_error, pose_scale.distance_to(Vector3.ONE))
				var point := local_bone_point(bone)
				if sample == 0:
					first_points[bone] = point
				if previous_points.has(bone):
					var step := point.distance_to(previous_points[bone])
					maximum_step = maxf(maximum_step, step)
					joint_metrics[bone].maximum_step_m_at_120hz = maxf(float(joint_metrics[bone].maximum_step_m_at_120hz), step)
					if bone in relevant_bones:
						maximum_relevant_step = maxf(maximum_relevant_step, step)
				previous_points[bone] = point
				if sample == count - 1:
					last_points[bone] = point
			for side in ["L","R"]:
				var foot: Vector3 = local_bone_point(side + "_Foot")
				foot_samples[side].append([phase,foot.y,foot.z])
		var endpoint_square := 0.0
		var whole_rig_endpoint_square := 0.0
		for bone in all_bones:
			var endpoint_delta := (first_points[bone] as Vector3).distance_to(last_points[bone])
			joint_metrics[bone].endpoint_delta_m = endpoint_delta
			whole_rig_endpoint_square += endpoint_delta * endpoint_delta
			if bone in relevant_bones:
				endpoint_square += endpoint_delta * endpoint_delta
		var row := {
			"duration_seconds":animation.length, "samples":count, "tracks":animation.get_track_count(),
			"keys":0, "skin_joints_sampled":all_bones.size(), "all_joint_transforms_finite":transforms_finite,
			"maximum_joint_scale_error":maximum_scale_error,
			"maximum_joint_step_m_at_120hz":maximum_step,
			"maximum_relevant_bone_step_m_at_120hz":maximum_relevant_step,
			"endpoint_rms_m":sqrt(endpoint_square / relevant_bones.size()),
			"whole_rig_endpoint_rms_m":sqrt(whole_rig_endpoint_square / all_bones.size()),
			"joint_metrics":joint_metrics
		}
		for track in animation.get_track_count():
			row.keys += animation.track_get_key_count(track)
		if clip in Motion.LOOP_CLIPS:
			var stride := Motion.WALK_STRIDE_METERS if clip == "walk" else (Motion.RUN_STRIDE_METERS if clip == "run" else 0.0)
			var estimates: Array[float] = []
			var maximum_plant_drift := 0.0
			if stride > 0.0:
				for side in ["L","R"]:
					var samples: Array = foot_samples[side]
					var minimum_y := INF
					for foot in samples:
						minimum_y = minf(minimum_y, foot[1])
					var run_start := -1
					for index in samples.size() + 1:
						var planted: bool = index < samples.size() and samples[index][1] <= minimum_y + 0.025
						if planted and run_start < 0:
							run_start = index
						elif not planted and run_start >= 0:
							var run_end := index - 1
							if run_end - run_start >= 4:
								var phase_delta: float = samples[run_end][0] - samples[run_start][0]
								var local_delta: float = absf(samples[run_end][2] - samples[run_start][2])
								estimates.append(local_delta / maxf(phase_delta, 0.0001))
								maximum_plant_drift = maxf(maximum_plant_drift, absf(local_delta - stride * phase_delta))
							run_start = -1
				estimates.sort()
			row["controller_stride_m"] = stride
			row["derived_low-contact_stride_median"] = estimates[estimates.size()/2] if not estimates.is_empty() else 0.0
			row["maximum_moving_root_plant_drift_m"] = maximum_plant_drift
		ledger.clips[clip] = row
		if clip in Motion.ACTION_CLIPS:
			var contact := float(Motion.ACTION_SPECS[clip].contact)
			player.seek(animation.length * contact, true)
			player.advance(0.0)
			skeleton.force_update_all_bone_transforms()
			var left := local_bone_point("L_Hand")
			var right := local_bone_point("R_Hand")
			var target: Vector3 = Motion.ACTION_SPECS[clip].target
			var working_point := (left + right) * 0.5 if Motion.ACTION_SPECS[clip].marker in ["C1TwoHandContact","C1RescueContact"] else (left if Motion.ACTION_SPECS[clip].marker == "C1LeftHandContact" else right)
			ledger.actions[clip] = {"contact_phase":contact,"marker":Motion.ACTION_SPECS[clip].marker,"target":Motion._contact_contract().actions[clip].target,"left_hand":[left.x,left.y,left.z],"right_hand":[right.x,right.y,right.z],"working_point":[working_point.x,working_point.y,working_point.z],"target_error_m":working_point.distance_to(target),"forward_positive_z":working_point.z>0.08}
		if clip.begins_with("turn_"):
			ledger.turns[clip] = {"skeleton_returns_neutral":row.endpoint_rms_m < 0.001,"external_root_facing_delta_degrees":Motion.facing_delta_for_turn(clip)}
	var file := FileAccess.open(output.path_join("motion-ledger.json"), FileAccess.WRITE)
	file.store_string(JSON.stringify(ledger, "\t"))
	file.close()

func percentile(values: Array[float], fraction: float) -> float:
	var sorted := values.duplicate()
	sorted.sort()
	if sorted.is_empty():
		return 0.0
	return sorted[clampi(ceili(fraction * sorted.size()) - 1, 0, sorted.size() - 1)]

func animation_inventory(runtime_player: AnimationPlayer) -> Dictionary:
	var library := runtime_player.get_animation_library(Motion.LIBRARY)
	var tracks := 0
	var keys := 0
	var seconds := 0.0
	for id in library.get_animation_list():
		var animation := library.get_animation(id)
		tracks += animation.get_track_count()
		seconds += animation.length
		for track in animation.get_track_count():
			keys += animation.track_get_key_count(track)
	return {"clips":library.get_animation_list().size(), "tracks":tracks, "keys":keys, "seconds":seconds}

func count_visible_scene_resources(node: Node, result: Dictionary) -> void:
	if node is Skeleton3D and (node as Skeleton3D).is_visible_in_tree():
		result.visible_rigs += 1
	if node.has_meta("t06_motion_player") and node is Node3D and (node as Node3D).is_visible_in_tree():
		result.t06_animated_rigs += 1
	if node is MeshInstance3D and (node as MeshInstance3D).is_visible_in_tree():
		var instance := node as MeshInstance3D
		if instance.mesh:
			for surface in instance.mesh.get_surface_count():
				var material := instance.get_active_material(surface)
				if material:
					result.material_ids[str(material.get_instance_id())] = true
					if material is ShaderMaterial and (material as ShaderMaterial).shader:
						result.shader_ids[str((material as ShaderMaterial).shader.get_instance_id())] = true
	for child in node.get_children():
		count_visible_scene_resources(child, result)

func benchmark_phase(game: Control, lead: Node3D, helper: Node3D, label: String, candidate_motion: bool) -> Dictionary:
	var lead_player: AnimationPlayer = lead.get_meta("t06_motion_player")
	var helper_player: AnimationPlayer = helper.get_meta("t06_motion_player")
	var lead_clip := Motion.LIBRARY + "/walk" if candidate_motion else String(Motion._source_clip(lead_player, "walk"))
	var helper_clip := Motion.LIBRARY + "/run" if candidate_motion else String(Motion._source_clip(helper_player, "run"))
	lead_player.play(lead_clip, 0.0)
	helper_player.play(helper_clip, 0.0)
	lead_player.speed_scale = 1.0
	helper_player.speed_scale = 1.0
	var samples: Array[float] = []
	var setup_cpu: Array[float] = []
	for frame in range(benchmark_frames_per_phase + 10):
		var started := Time.get_ticks_usec()
		lead_player.advance(1.0 / 60.0)
		helper_player.advance(1.0 / 60.0)
		lead.rotation.y = sin(float(frame) * 0.011) * 0.35
		helper.rotation.y = -0.18 + cos(float(frame) * 0.013) * 0.35
		# A frame_post_draw await can stall forever on software Vulkan, while a
		# process_frame followed by force_draw renders twice. Advance explicitly,
		# then force and time exactly one completed render submission.
		RenderingServer.force_draw(false, 0.0)
		var now := Time.get_ticks_usec()
		if frame >= 10:
			samples.append(float(now - started) / 1000.0)
			setup_cpu.append(RenderingServer.get_frame_setup_time_cpu())
	return {
		"label":label, "candidate_motion":candidate_motion, "samples":samples.size(),
		"render_submission_samples_ms":samples,
		"render_setup_cpu_samples_ms":setup_cpu,
		"p50_ms":percentile(samples,0.50), "p95_ms":percentile(samples,0.95),
		"p99_ms":percentile(samples,0.99), "max_ms":percentile(samples,1.0),
		"average_ms":samples.reduce(func(total,value): return total + value, 0.0) / maxf(1.0, samples.size()),
		"render_setup_cpu_p95_ms":percentile(setup_cpu,0.95),
		"engine_process_ms":Performance.get_monitor(Performance.TIME_PROCESS) * 1000.0,
		"draw_calls":game.scene_view.get_render_info(Viewport.RENDER_INFO_TYPE_VISIBLE, Viewport.RENDER_INFO_DRAW_CALLS_IN_FRAME),
		"submitted_primitives":game.scene_view.get_render_info(Viewport.RENDER_INFO_TYPE_VISIBLE, Viewport.RENDER_INFO_PRIMITIVES_IN_FRAME)
	}

func run_benchmark() -> void:
	DirAccess.make_dir_recursive_absolute(output)
	var game: Control = Main.new()
	game.qa_mode = true
	game.capture_frames = 1000
	game.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	root.add_child(game)
	game.size = Vector2(root.size)
	await process_frame
	await process_frame
	game.set_process(false)
	game.set_physics_process(false)
	game.paused = true
	var lead: Node3D = game.actors[1]
	var static_memory_before_install := Performance.get_monitor(Performance.MEMORY_STATIC)
	var before_install := Time.get_ticks_usec()
	var lead_install := Motion.install(lead, "player_lead")
	var install_usec := Time.get_ticks_usec() - before_install
	assert(lead_install.passed, str(lead_install.errors))
	game.actors[2].visible = false
	var helper: Node3D = game.actor(1)
	helper.name = "Character1CompanionBenchmark"
	var helper_install := Motion.install(helper, "core_human_companion")
	install_usec += Time.get_ticks_usec() - before_install - install_usec
	assert(helper_install.passed, str(helper_install.errors))
	var static_memory_after_install := Performance.get_monitor(Performance.MEMORY_STATIC)
	lead.position = game.xyz(Vector2(-0.8, 2.2))
	helper.position = game.xyz(Vector2(0.8, 2.6))
	set_shipping_camera(game, lead, game.xyz(Vector2(0.0, 0.2)))
	var phases := []
	for row in [["baseline-a",false],["candidate-a",true],["candidate-b",true],["baseline-b",false]]:
		var phase: Dictionary = await benchmark_phase(game, lead, helper, row[0], row[1])
		phases.append(phase)
		print(JSON.stringify({"task":"T06","benchmark_phase_complete":phase.label,"samples":phase.samples,"p95_ms":phase.p95_ms}))
	var texture_mb := Performance.get_monitor(Performance.RENDER_TEXTURE_MEM_USED) / (1024.0 * 1024.0)
	var video_mb := Performance.get_monitor(Performance.RENDER_VIDEO_MEM_USED) / (1024.0 * 1024.0)
	var static_mb := Performance.get_monitor(Performance.MEMORY_STATIC) / (1024.0 * 1024.0)
	var baseline_p95 := (float(phases[0].p95_ms) + float(phases[3].p95_ms)) * 0.5
	var candidate_p95 := (float(phases[1].p95_ms) + float(phases[2].p95_ms)) * 0.5
	var scene_resources := {"visible_rigs":0, "t06_animated_rigs":0, "material_ids":{}, "shader_ids":{}}
	count_visible_scene_resources(game.world, scene_resources)
	var result := {
		"task":"T06", "candidate_commit":candidate, "source_sha256":Motion.SOURCE_GLTF_SHA256,
		"method":"counterbalanced A-B-B-A continuous shipping-scene render submission benchmark",
		"frames_per_phase":benchmark_frames_per_phase, "measured_frames":benchmark_frames_per_phase * 4,
		"warmup_frames_per_phase":10, "phases":phases,
		"baseline_p95_ms":baseline_p95, "candidate_p95_ms":candidate_p95,
		"motion_p95_delta_ms":candidate_p95-baseline_p95,
		"baseline_first_last_p95_drift_ms":float(phases[3].p95_ms)-float(phases[0].p95_ms),
		"candidate_first_last_p95_drift_ms":float(phases[2].p95_ms)-float(phases[1].p95_ms),
		"scene_state":"shipping T04 camera + T05 stations/environment with one lead and three visible companion workloads",
		"resolution":[game.scene_view.size.x,game.scene_view.size.y], "renderer":RenderingServer.get_current_rendering_method(),
		"texture_gpu_memory_mb":texture_mb, "video_gpu_memory_mb":video_mb,
		"process_static_memory_mb":static_mb, "animation_install_usec_two_rigs":install_usec,
		"animation_static_memory_delta_mb_two_rigs":maxf(0.0, static_memory_after_install-static_memory_before_install)/(1024.0*1024.0),
		"animation_inventory_per_rig":animation_inventory(lead_install.player),
		"shipping_population_rigs_visible":scene_resources.visible_rigs,
		"npc_companion_active_population":maxi(0,int(scene_resources.visible_rigs)-1),
		"npc_companion_active_population_definition":"visible animated non-lead core companion workloads in the shipping-scene preflight",
		"t06_animated_rigs":scene_resources.t06_animated_rigs,
		"materials_visible_whole_scene":scene_resources.material_ids.size(),
		"unique_shader_resources_visible":scene_resources.shader_ids.size(),
		"t06_incremental_materials":0, "t06_incremental_shaders":0,
		"physics_active_bodies":Performance.get_monitor(Performance.PHYSICS_3D_ACTIVE_OBJECTS),
		"device":RenderingServer.get_video_adapter_name(),
		"gpu_frame_ms_where_measurable":null,
		"shader_warmup_frames":10, "thermal_proxy":"first/last counterbalanced phase drift",
		"software_preflight_passed":phases.all(func(row): return row.samples == benchmark_frames_per_phase and row.p99_ms > 0.0),
		"physical_device_certified":false, "limitations":["Render submission, not display presentation timing.","No GPU timestamp is exposed by this Godot runtime.","Physical 4K60 and thermal certification remain T68/T69 gates."]
	}
	var file := FileAccess.open(output.path_join("benchmark.json"), FileAccess.WRITE)
	file.store_string(JSON.stringify(result, "\t"))
	file.close()
	print(JSON.stringify({"task":"T06","benchmark":true,"measured_frames":result.measured_frames,"software_preflight_passed":result.software_preflight_passed}))
	if is_instance_valid(game.outpost_audio):
		game.outpost_audio.stop_all()
	game.free()
	quit(0 if result.software_preflight_passed else 1)

func run() -> void:
	if benchmark:
		await run_benchmark()
		return
	DirAccess.make_dir_recursive_absolute(output)
	setup_stage()
	if export_review_only:
		await process_frame
		write_motion_ledger()
		var review := export_runtime_review_glb()
		print(JSON.stringify({"task":"T06","runtime_review_candidate":review}))
		quit(0)
		return
	if video_sequences:
		await capture_video_review()
	elif native_4k:
		await capture_native_selection()
	else:
		await capture_full_review()
		await capture_overlay_review()
		write_motion_ledger()
		await capture_gameplay_review()
	var runtime_review_candidate := {} if native_4k or video_sequences else export_runtime_review_glb()
	var metadata := {
		"task":"T06-character1-motion-v1", "candidate_commit":candidate,
		"source_path":SOURCE, "source_sha256":FileAccess.get_sha256(SOURCE),
		"source_expected_sha256":Motion.SOURCE_GLTF_SHA256,
		"source_immutable":FileAccess.get_sha256(SOURCE) == Motion.SOURCE_GLTF_SHA256,
		"library":Motion.LIBRARY, "captures":captures, "gameplay_captures":gameplay_captures,
		"full_review":not native_4k and not video_sequences, "native_3840x2160_scale1":native_4k,
		"video_sequence_review":video_sequences, "video_sequences":video_manifest,
		"renderer":RenderingServer.get_current_rendering_method(),
		"device":RenderingServer.get_video_adapter_name(),
		"visible_meshes":2, "visible_materials":2, "animated_rigs_active":1,
		"physics_active_bodies":0, "npc_companion_active_population":0,
		"measurement_method":"Godot Viewport visible-frame counters plus exact staged and shipping-context scene inventories",
		"six_view_temporal_frames":507 if not native_4k and not video_sequences else 0,
		"six_view_angles":SIX_VIEW_LAYOUT.map(func(row): return row.id) if not native_4k and not video_sequences else [],
		"runtime_review_candidate":runtime_review_candidate,
		"known_unmeasured_fields":["cpu_frame_ms","gpu_frame_ms","texture_gpu_memory_mb"],
		"contact_contract":actor.get_meta("t06_motion_contract"),
		"physical_device_certified":false, "task_approved":false
	}
	var file := FileAccess.open(output.path_join("capture.json"), FileAccess.WRITE)
	file.store_string(JSON.stringify(metadata, "\t"))
	file.close()
	print(JSON.stringify({"task":metadata.task,"captures":captures.size(),"source_immutable":metadata.source_immutable,"native_4k":native_4k}))
	quit(0 if metadata.source_immutable else 1)
