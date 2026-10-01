extends "res://tests/capture_task05_station_kit.gd"

## Evidence-only supplement. The authored R01 front faces negative Z.
## Do not rotate the asset or alter its materials to compensate for a camera label.
## Inherits the existing test-stage lighting; no shipping camera/runtime changes.
var candidate_source := ""
var inspection_records: Array = []

func _initialize() -> void:
	native = true
	candidate_source = OS.get_environment("GITHUB_SHA")
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--out="):
			output = argument.trim_prefix("--out=")
		if argument.begins_with("--source="):
			candidate_source = argument.trim_prefix("--source=")
	call_deferred("run")

func vec(value: Vector3) -> Array:
	return [value.x, value.y, value.z]

func aim(target: Vector3, offset: Vector3, height: float) -> void:
	camera.position = target + offset
	camera.look_at(target, Vector3.UP)
	camera.size = height

func record_frame(frame_id: String, condition: String, waits: int = 4) -> void:
	for index in range(waits):
		await process_frame
	await RenderingServer.frame_post_draw
	var image := viewport.get_texture().get_image()
	assert(image.get_width() == 3840 and image.get_height() == 2160)
	assert(image.save_png(output.path_join(frame_id + ".png")) == OK)
	inspection_records.append({
		"id": frame_id, "path": frame_id + ".png", "condition": condition,
		"size": [image.get_width(), image.get_height()],
		"render_scale": viewport.scaling_3d_scale,
		"camera_position": vec(camera.position),
		"camera_basis_x": vec(camera.basis.x),
		"camera_basis_y": vec(camera.basis.y),
		"camera_basis_z": vec(camera.basis.z),
		"camera_full_height": camera.size,
		"draw_calls": viewport.get_render_info(Viewport.RENDER_INFO_TYPE_VISIBLE, Viewport.RENDER_INFO_DRAW_CALLS_IN_FRAME)
	})

func run() -> void:
	assert(candidate_source.length() == 40, "Exact source SHA is required")
	assert(DirAccess.make_dir_recursive_absolute(output) == OK)
	assert(DirAccess.make_dir_recursive_absolute(output.path_join("orbit")) == OK)
	setup_world()
	clear_stage_accents()
	var asset := place_single("hearth_vessel")
	scale_actor.visible = false
	assert(asset.transform.is_equal_approx(Transform3D.IDENTITY))
	var centre := Vector3(0.0, 1.25, 0.0)
	var frames := [
		{"id":"r01-front-day", "offset":Vector3(0,6,-14), "target":centre, "height":4.4, "condition":"day"},
		{"id":"r01-front-left-day", "offset":Vector3(-9,8,-13), "target":centre, "height":4.4, "condition":"day"},
		{"id":"r01-front-right-day", "offset":Vector3(9,8,-13), "target":centre, "height":4.4, "condition":"day"},
		{"id":"r01-rear-day", "offset":Vector3(0,6,14), "target":centre, "height":4.4, "condition":"day"},
		{"id":"r01-rear-oblique-day", "offset":Vector3(9,8,13), "target":centre, "height":4.4, "condition":"day"},
		{"id":"r01-left-day", "offset":Vector3(-14,6,0), "target":centre, "height":4.4, "condition":"day"},
		{"id":"r01-right-day", "offset":Vector3(14,6,0), "target":centre, "height":4.4, "condition":"day"},
		{"id":"r01-overhead-day", "offset":Vector3(0,14,0.1), "target":centre, "height":4.4, "condition":"day"},
		{"id":"r01-firebox-detail-day", "offset":Vector3(0,1.7,-8), "target":Vector3(0,0.85,-0.7), "height":2.3, "condition":"day"},
		{"id":"r01-chimney-detail-day", "offset":Vector3(4,5,-8), "target":Vector3(0,2.1,0.1), "height":2.4, "condition":"day"},
		{"id":"r01-front-night", "offset":Vector3(-9,8,-13), "target":centre, "height":4.4, "condition":"night"},
		{"id":"r01-front-blizzard", "offset":Vector3(-9,8,-13), "target":centre, "height":4.4, "condition":"blizzard"}
	]
	for row: Dictionary in frames:
		set_condition(str(row.condition))
		aim(row.target, row.offset, float(row.height))
		await record_frame(str(row.id), str(row.condition))
	set_condition("day")
	for index in range(180):
		var angle := TAU * float(index) / 180.0
		aim(centre, Vector3(14.0 * sin(angle), 8.0, -14.0 * cos(angle)), 4.4)
		await record_frame("orbit/frame-%04d" % index, "day", 2)
	var report := {
		"schema_version":1, "task":"T05", "subtask":"R01-front-detail-inspection",
		"candidate_source":candidate_source,
		"capture_kind":"isolated-component-inspection-and-camera-orbit",
		"shipping_main_call_site_exercised":false,
		"test_stage_not_shipping_content":true,
		"source_bound":true, "asset_transform_unchanged":true,
		"front_axis":"negative-Z", "test_stage_lighting":"inherited-unchanged",
		"asset_sha256":FileAccess.get_sha256("res://assets/stations_v2/hearth_vessel.glb"),
		"catalog_sha256":FileAccess.get_sha256(StationKit.CATALOG_PATH),
		"renderer":RenderingServer.get_current_rendering_method(),
		"device":RenderingServer.get_video_adapter_name(),
		"stills_count":12, "orbit_frames":180,
		"orbit_playback_fps":60, "orbit_playback_seconds":3,
		"offline_camera_orbit_is_not_measured_gameplay_fps":true,
		"captures":inspection_records,
		"critics_executed":false, "task_approved":false,
		"physical_4k60_verified":false
	}
	var file := FileAccess.open(output.path_join("capture.json"), FileAccess.WRITE)
	assert(file != null)
	file.store_string(JSON.stringify(report, "\t"))
	file.close()
	await process_frame
	quit()
