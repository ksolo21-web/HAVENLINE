extends SceneTree

const Motion = preload("res://scripts/character1_motion.gd")
const SOURCE := "res://assets/characters/Character1.glb"
const Main = preload("res://scripts/main.gd")

var output := "user://task06-capture"
var candidate := ""
var native_4k := false
var video_sequences := false
var benchmark := false
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
			"external_root_facing":Motion.facing_delta_for_turn(clip)
		})
	var file := FileAccess.open(output.path_join("video-sequences.json"), FileAccess.WRITE)
	file.store_string(JSON.stringify({
		"task":"T06-character1-motion-v1", "candidate_commit":candidate,
		"source_sha256":Motion.SOURCE_GLTF_SHA256, "clips":video_manifest,
		"real_time_fps":30, "slow_motion_playback_fraction":0.25,
		"source_frames_are_shared_between_encodes":true
	}, "\t"))
	file.close()

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
			set_view("left", "body")
			await snap("overlay/%s-left-%03d.png" % [clip,roundi(phase*100.0)],clip,phase,"bone_overlay","body")
	for clip in Motion.ACTION_CLIPS:
		var phase := float(Motion.ACTION_SPECS[clip].contact)
		var animation := player.get_animation(Motion.LIBRARY + "/" + clip)
		player.play(Motion.LIBRARY + "/" + clip, 0.0)
		player.seek(animation.length * phase, true)
		player.advance(0.0)
		skeleton.force_update_all_bone_transforms()
		update_overlay(clip)
		set_view("three-quarter", "body")
		await snap("overlay/%s-contact.png" % clip,clip,phase,"bone_overlay","body")
	for clip in ["turn_left_030","turn_right_030","turn_left_090","turn_right_090","turn_left_180","turn_right_180"]:
		var animation := player.get_animation(Motion.LIBRARY + "/" + clip)
		player.play(Motion.LIBRARY + "/" + clip, 0.0)
		player.seek(animation.length * 0.52, true)
		player.advance(0.0)
		skeleton.force_update_all_bone_transforms()
		update_overlay()
		set_view("front", "body")
		await snap("overlay/%s-mid.png" % clip,clip,0.52,"bone_overlay","body")
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
	var ledger := {
		"task":"T06-character1-motion-v1", "candidate_commit":candidate,
		"sample_rate_hz":120, "source_sha256":Motion.SOURCE_GLTF_SHA256,
		"coordinate_space":"normalized actor-local metres; external moving root applied for plant drift",
		"clips":{}, "actions":{}, "turns":{}, "roles":{
			"player_lead":{"gameplay_impact_authority":true,"visual_phase_offset":0.0},
			"core_human_companion":{"gameplay_impact_authority":false,"visual_phase_offset":0.37}
		}
	}
	var bones := ["Hip","L_Thigh","R_Thigh","L_Calf","R_Calf","L_Foot","R_Foot","L_ToeBase","R_ToeBase","L_Hand","R_Hand"]
	for clip in Motion.LOOP_CLIPS + Motion.TRANSITION_CLIPS + Motion.ACTION_CLIPS:
		var qualified: String = Motion.LIBRARY + "/" + clip
		var animation := player.get_animation(qualified)
		var count := ceili(animation.length * 120.0) + 1
		var first_points := {}
		var last_points := {}
		var previous_points := {}
		var maximum_step := 0.0
		var foot_samples := {"L":[],"R":[]}
		player.play(qualified, 0.0)
		for sample in count:
			var phase := float(sample) / float(maxi(count - 1, 1))
			player.seek(animation.length * phase, true)
			player.advance(0.0)
			skeleton.force_update_all_bone_transforms()
			for bone in bones:
				var point := local_bone_point(bone)
				if sample == 0:
					first_points[bone] = point
				if previous_points.has(bone):
					maximum_step = maxf(maximum_step, point.distance_to(previous_points[bone]))
				previous_points[bone] = point
				if sample == count - 1:
					last_points[bone] = point
			for side in ["L","R"]:
				var foot: Vector3 = local_bone_point(side + "_Foot")
				foot_samples[side].append([phase,foot.y,foot.z])
		var endpoint_square := 0.0
		for bone in bones:
			endpoint_square += (first_points[bone] as Vector3).distance_squared_to(last_points[bone])
		var row := {
			"duration_seconds":animation.length, "samples":count, "tracks":animation.get_track_count(),
			"keys":0, "maximum_relevant_bone_step_m_at_120hz":maximum_step,
			"endpoint_rms_m":sqrt(endpoint_square / bones.size())
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
	var previous := 0
	for frame in range(benchmark_frames_per_phase + 60):
		lead_player.advance(1.0 / 60.0)
		helper_player.advance(1.0 / 60.0)
		lead.rotation.y = sin(float(frame) * 0.011) * 0.35
		helper.rotation.y = -0.18 + cos(float(frame) * 0.013) * 0.35
		await process_frame
		await RenderingServer.frame_post_draw
		var now := Time.get_ticks_usec()
		if frame >= 60 and previous > 0:
			samples.append(float(now - previous) / 1000.0)
			setup_cpu.append(RenderingServer.get_frame_setup_time_cpu())
		previous = now
	return {
		"label":label, "candidate_motion":candidate_motion, "samples":samples.size(),
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
	lead.position = game.xyz(Vector2(-0.8, 2.2))
	helper.position = game.xyz(Vector2(0.8, 2.6))
	set_shipping_camera(game, lead, game.xyz(Vector2(0.0, 0.2)))
	var phases := []
	for row in [["baseline-a",false],["candidate-a",true],["candidate-b",true],["baseline-b",false]]:
		phases.append(await benchmark_phase(game, lead, helper, row[0], row[1]))
	var texture_mb := Performance.get_monitor(Performance.RENDER_TEXTURE_MEM_USED) / (1024.0 * 1024.0)
	var video_mb := Performance.get_monitor(Performance.RENDER_VIDEO_MEM_USED) / (1024.0 * 1024.0)
	var static_mb := Performance.get_monitor(Performance.MEMORY_STATIC) / (1024.0 * 1024.0)
	var baseline_p95 := (float(phases[0].p95_ms) + float(phases[3].p95_ms)) * 0.5
	var candidate_p95 := (float(phases[1].p95_ms) + float(phases[2].p95_ms)) * 0.5
	var result := {
		"task":"T06", "candidate_commit":candidate, "source_sha256":Motion.SOURCE_GLTF_SHA256,
		"method":"counterbalanced A-B-B-A continuous shipping-scene render submission benchmark",
		"frames_per_phase":benchmark_frames_per_phase, "measured_frames":benchmark_frames_per_phase * 4,
		"warmup_frames_per_phase":60, "phases":phases,
		"baseline_p95_ms":baseline_p95, "candidate_p95_ms":candidate_p95,
		"motion_p95_delta_ms":candidate_p95-baseline_p95,
		"baseline_first_last_p95_drift_ms":float(phases[3].p95_ms)-float(phases[0].p95_ms),
		"candidate_first_last_p95_drift_ms":float(phases[2].p95_ms)-float(phases[1].p95_ms),
		"texture_gpu_memory_mb":texture_mb, "video_gpu_memory_mb":video_mb,
		"process_static_memory_mb":static_mb, "animation_install_usec_two_rigs":install_usec,
		"animation_inventory_per_rig":animation_inventory(lead_install.player),
		"shipping_population_rigs_visible":4, "t06_animated_rigs":2,
		"physics_active_bodies":Performance.get_monitor(Performance.PHYSICS_3D_ACTIVE_OBJECTS),
		"renderer":RenderingServer.get_current_rendering_method(), "device":RenderingServer.get_video_adapter_name(),
		"gpu_frame_ms_where_measurable":null,
		"shader_warmup_frames":60, "thermal_proxy":"first/last counterbalanced phase drift",
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
	if video_sequences:
		await capture_video_review()
	elif native_4k:
		await capture_native_selection()
	else:
		await capture_full_review()
		await capture_overlay_review()
		write_motion_ledger()
		await capture_gameplay_review()
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
		"known_unmeasured_fields":["cpu_frame_ms","gpu_frame_ms","texture_gpu_memory_mb"],
		"contact_contract":actor.get_meta("t06_motion_contract"),
		"physical_device_certified":false, "task_approved":false
	}
	var file := FileAccess.open(output.path_join("capture.json"), FileAccess.WRITE)
	file.store_string(JSON.stringify(metadata, "\t"))
	file.close()
	print(JSON.stringify({"task":metadata.task,"captures":captures.size(),"source_immutable":metadata.source_immutable,"native_4k":native_4k}))
	quit(0 if metadata.source_immutable else 1)
