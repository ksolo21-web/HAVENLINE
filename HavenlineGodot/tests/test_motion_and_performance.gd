extends SceneTree
const Metrics = preload("res://scripts/performance_record.gd")
const Main = preload("res://scripts/main.gd")
var failures: Array = []
var checks: Array = []
func check(label: String, passed: bool):
	checks.append({"name":label,"passed":passed})
	if not passed: failures.append(label)
func _initialize(): call_deferred("run")
func run():
	var metrics := Metrics.new()
	metrics.resolution(Vector2i(3840,2160))
	for i in 100: metrics.sample(10.0 if i < 95 else 40.0)
	var report := metrics.report()
	check("interval percentiles use the observed samples", report.p50_ms == 10 and report.p95_ms == 10 and report.p99_ms == 40)
	check("slow frames are counted rather than hidden by mean FPS", report.over_60hz_budget == 5 and report.over_30hz_budget == 5)
	check("internal 4K settings cannot grant device or thermal certification", report.uhd_pixel_budget_at_all_recorded_resolutions and not report.sustained_4k60_certified and not report.physical_device_validated and not report.thermal_validated)
	metrics.resolution(Vector2i(1280,720))
	check("smaller review resolution disqualifies native pixel-budget evidence", not metrics.report().uhd_pixel_budget_at_all_recorded_resolutions)
	metrics.sample(NAN); metrics.sample(-1)
	check("invalid intervals cannot corrupt performance evidence", metrics.count == 100)
	metrics = Metrics.new()
	for i in 72001: metrics.sample(16.0)
	report = metrics.report()
	check("ring retains exactly its bounded sample budget", report.samples == 72000 and report.total_samples == 72001)
	check("ring overwrites in place without losing duration accounting", is_equal_approx(report.retained_seconds,1152.0))
	var game := Main.new()
	# We use production actor normalization and motion attachment for these tests.
	game.world = Node3D.new(); root.add_child(game.world)
	for id in [2,3,4]:
		var actor: Node3D = game.actor(id)
		var animation: AnimationPlayer = actor.get_meta("animation")
		var skeleton: Skeleton3D = game.find_skeleton(actor)
		var clips := animation.get_animation_list()
		check("Character%d has three usable baked locomotion clips" % id, clips.size() == 3)
		for clip in clips:
			var resource := animation.get_animation(clip)
			var shape_safe := true
			var rotations_valid := true
			var changed := false
			for track in resource.get_track_count():
				if resource.track_get_type(track) == Animation.TYPE_SCALE_3D: shape_safe = false
				if resource.track_get_type(track) == Animation.TYPE_POSITION_3D and not str(resource.track_get_path(track)).ends_with(":mixamorigHips"): shape_safe = false
				if resource.track_get_type(track) == Animation.TYPE_ROTATION_3D:
					for key in resource.track_get_key_count(track):
						var q: Quaternion = resource.track_get_key_value(track,key)
						if not q.is_finite() or not is_equal_approx(q.length_squared(),1.0): rotations_valid = false
					if resource.track_get_key_count(track) > 1:
						if resource.track_get_key_value(track,0) != resource.track_get_key_value(track,1): changed = true
			check("Character%d %s preserves limb translations and scales" % [id,clip], shape_safe)
			check("Character%d %s has finite normalized rotations" % [id,clip], rotations_valid)
			check("Character%d %s contains actual motion rather than a relabeled rest pose" % [id,clip], changed)
			animation.play(clip)
			var valid_length := true
			for phase in range(16):
				animation.seek(resource.length * phase / 16.0,true)
				skeleton.force_update_all_bone_transforms()
				for bone in skeleton.get_bone_count():
					var parent := skeleton.get_bone_parent(bone)
					if parent < 0: continue
					var length := skeleton.get_bone_global_pose(bone).origin.distance_to(skeleton.get_bone_global_pose(parent).origin)
					if absf(length - skeleton.get_bone_rest(bone).origin.length()) > .0001: valid_length = false
			check("Character%d %s does not stretch its skeleton across sampled phases" % [id,clip], valid_length)
		actor.free()
	game.world.free(); game.free()
	print(JSON.stringify({"suite":"motion_and_performance","passed":failures.is_empty(),"checks":checks,"failures":failures,"visual_or_rig_approval":false}))
	quit(0 if failures.is_empty() else 1)
