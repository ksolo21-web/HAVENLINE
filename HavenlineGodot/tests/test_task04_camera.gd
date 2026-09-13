extends SceneTree

const Composition = preload("res://scripts/camera_composition.gd")

var checks: Array = []
var failures: Array = []

func check(label: String, passed: bool) -> void:
	checks.append({"name": label, "passed": passed})
	if not passed:
		failures.append(label)

func _initialize() -> void:
	call_deferred("run")

func run() -> void:
	var descriptor := Composition.descriptor()
	check("Camera authority is versioned", descriptor.authority_id == "T04-reference-camera-v1")
	check("Reference projection remains orthographic", descriptor.projection == "orthographic")
	check("Unity half-height conversion remains 14.3 full-height", is_equal_approx(descriptor.base_full_height, 14.3))
	check("Historical focus height remains 0.95", is_equal_approx(descriptor.focus_height, 0.95))
	check("Historical look-ahead remains 0.72", is_equal_approx(descriptor.look_ahead, 0.72))
	check("Historical follow sharpness remains 8.6", is_equal_approx(descriptor.follow_sharpness, 8.6))
	check("Camera adds no render content", not descriptor.adds_render_content)

	var fixtures := {
		"phone_16_9": Vector2(1920, 1080),
		"phone_20_9": Vector2(2400, 1080),
		"tablet_16_10": Vector2(2560, 1600),
		"tablet_4_3": Vector2(2732, 2048),
		"foldable_outer": Vector2(2520, 1080),
		"foldable_inner": Vector2(2208, 1768)
	}
	for id in fixtures:
		var viewport: Vector2 = fixtures[id]
		var aspect := Composition.safe_aspect(viewport)
		var height := Composition.full_height_for(viewport)
		check(id + " is landscape-finite", is_finite(aspect) and aspect >= 1.0)
		check(id + " keeps readable actor scale", height >= 14.3 and height <= 16.0)
		check(id + " preserves minimum horizontal context", height * aspect >= 19.5 - 0.001)
	check("Wide screens reveal width without shrinking actor scale", is_equal_approx(Composition.full_height_for(Vector2(2400, 1080)), 14.3))
	check("Invalid viewport safely uses reference aspect", is_equal_approx(Composition.safe_aspect(Vector2(NAN, 0)), 16.0 / 9.0))

	var player := Vector3(1.0, 0.0, 2.0)
	var east := Composition.desired_focus(player, Vector3(4, 0, 0), Vector3(0, 0, -1))
	var west := Composition.desired_focus(player, Vector3(-4, 0, 0), Vector3(0, 0, -1))
	var north := Composition.desired_focus(player, Vector3.ZERO, Vector3(0, 0, -1))
	check("Look-ahead follows eastward motion", east.x > player.x and is_equal_approx(east.z, player.z))
	check("Look-ahead follows westward motion", west.x < player.x and is_equal_approx(west.z, player.z))
	check("Facing supplies look-ahead while stationary", north.z < player.z)
	check("Selected lead retains reference focus height", is_equal_approx(north.y, player.y + 0.95))

	var target := Vector3(6.0, 0.0, 2.0)
	var with_target := Composition.desired_focus(player, Vector3.ZERO, Vector3(0, 0, -1), target)
	var without_target := Composition.desired_focus(player, Vector3.ZERO, Vector3(0, 0, -1))
	check("Nearby contextual target shifts composition toward itself", with_target.x > without_target.x)
	check("Target shift stays bounded", with_target.distance_to(without_target) <= 2.2 + 0.001)
	var far_target := Vector3(30.0, 0.0, 2.0)
	check("Distant target cannot drag the camera", Composition.desired_focus(player, Vector3.ZERO, Vector3(0, 0, -1), far_target).is_equal_approx(without_target))
	check("Target-aware zoom remains close", Composition.desired_full_height(Vector2(1920,1080), player, target) <= 15.05)

	var controller := Composition.new()
	var first := controller.compose(player, Vector3(4,0,0), Vector3(0,0,-1), null, Vector2(1920,1080), 1.0/60.0, true)
	check("Snap initializes exact desired focus", first.focus.is_equal_approx(east))
	check("Shipping camera keeps vertical scale", first.keep_aspect == Camera3D.KEEP_HEIGHT)
	check("Near-plane padding keeps camera more than 28 units from focus", first.camera_position.distance_to(first.focus) > 28.0)
	var prior: Vector3 = first.focus
	var goal := Composition.desired_focus(Vector3(8,0,2), Vector3(4,0,0), Vector3(1,0,0))
	var monotonic := true
	for _i in range(45):
		var row := controller.compose(Vector3(8,0,2), Vector3(4,0,0), Vector3(1,0,0), null, Vector2(1920,1080), 1.0/60.0)
		monotonic = monotonic and row.focus.distance_to(goal) <= prior.distance_to(goal) + 0.00001
		prior = row.focus
	check("Damped follow converges without overshoot", monotonic and prior.distance_to(goal) < 0.02)

	var wide := controller.compose(Vector3(8,0,2), Vector3.ZERO, Vector3(1,0,0), null, Vector2(2400,1080), 1.0/60.0, true)
	var narrow := controller.compose(Vector3(8,0,2), Vector3.ZERO, Vector3(1,0,0), null, Vector2(2208,1768), 1.0/60.0)
	check("Resize widens immediately before content can crop", narrow.full_height >= Composition.full_height_for(Vector2(2208,1768)))
	check("Resize does not move the selected lead discontinuously", narrow.focus.distance_to(wide.focus) < 0.001)

	var integration_source := FileAccess.get_file_as_string("res://scripts/main.gd")
	check("Runtime preloads the T04 camera authority", integration_source.contains('const CameraComposition = preload("res://scripts/camera_composition.gd")'))
	check("Runtime resolves the current contextual action target", integration_source.contains("func camera_action_target() -> Variant:"))
	check("Normal gameplay calls the bounded composition controller", integration_source.contains("camera_composition.compose("))
	check("Disclosed QA viewpoints remain explicitly separated", integration_source.contains("var qa_camera_override := qa_mode"))

	print(JSON.stringify({
		"suite": "T04_reference_camera_composition",
		"checks": checks,
		"failures": failures,
		"passed": failures.is_empty(),
		"device_fixture_count": fixtures.size(),
		"independent_critic": false,
		"physical_4k60_verified": false
	}))
	quit(0 if failures.is_empty() else 1)
