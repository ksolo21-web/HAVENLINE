extends SceneTree
## The only actor is an invisible, disposable CharacterBody3D contact fixture.
## No visual skin, route design, default hooks, saves, fishing or live weather.
const Preview = preload("res://previews/terrain_water_preview.tscn")
const Terrain = preload("res://terrain_source.gd")
const River = preload("res://river_geometry.gd")
const GroundContact = preload("res://previews/terrain_contact_preview.gd")
const Sweep = preload("res://previews/fixture_dry_shore_sweep.gd")
const RADIUS := 0.31
const HEIGHT := 1.75
const PHYSICS_HZ := 60.0
const MIN_APPROACH_TICKS := 120
const MAX_APPROACH_TICKS := 210
const REQUIRED_CLIPPED_STREAK := 20
const MAX_TRAVEL_M := 1.70
const HOLD_STEPS := 24
var checks := 0
var failures: Array[String] = []

func _initialize() -> void:
	call_deferred("_probe")

func _probe() -> void:
	_check(current_scene == null, "default game not started")
	var fixture := Preview.instantiate() as Node3D
	root.add_child(fixture)
	_check(fixture.get("water_bound") == true, "exact water and prior ground fixture bound")
	if fixture.get("water_bound") != true:
		_finish(fixture, {})
		return

	var axis := River.tangent_at_x(4.8)
	var north := Vector2(-axis.y, axis.x)
	var center := River.center_at_x(4.8)
	var half := River.width_at_x(4.8) * 0.5
	var start := center + north * (half + 2.8)
	var opposite := center - north * (half + 1.65)
	var opposite_request := opposite - start
	var long_legal := Sweep.allowed_delta(start, opposite_request, RADIUS, 1.0)
	_check(Sweep.dry_footprint(start, RADIUS, 1.0) and Sweep.dry_footprint(opposite, RADIUS, -1.0),
		"positive control sides both valid at endpoints")
	_check(opposite_request.length() <= Sweep.MAX_SWEEP and long_legal.length() > 0.5 and
		long_legal.length() < opposite_request.length() and Sweep.dry_footprint(start + long_legal, RADIUS, 1.0),
		"sampled whole-segment prevents dry-to-dry tunneling")
	_check(Sweep.allowed_delta(center, north, RADIUS, 1.0).is_zero_approx(),
		"invalid starting bank does not teleport or migrate")
	_check(Sweep.allowed_delta(start, Vector2(INF, 0), RADIUS, 1.0).is_zero_approx() and
		Sweep.allowed_delta(start, north * 10.0, RADIUS, 1.0).is_zero_approx(),
		"nonfinite and over-budget sweep rejected closed")
	_check(not Sweep.dry_footprint(start, -RADIUS, 1.0) and
		not Sweep.dry_footprint(start, RADIUS, 0.0), "invalid capsule and bank inputs rejected")

	var proxy := CharacterBody3D.new()
	proxy.name = "InvisibleFixtureCapsule"
	proxy.collision_layer = 0
	proxy.collision_mask = GroundContact.GROUND_LAYER
	proxy.motion_mode = CharacterBody3D.MOTION_MODE_GROUNDED
	proxy.floor_snap_length = 0.22
	proxy.floor_max_angle = deg_to_rad(45.0)
	proxy.safe_margin = 0.001
	proxy.max_slides = 4
	var collider := CollisionShape3D.new()
	var capsule := CapsuleShape3D.new()
	capsule.height = HEIGHT
	capsule.radius = RADIUS
	collider.shape = capsule
	collider.position.y = HEIGHT * 0.5
	proxy.add_child(collider)
	fixture.add_child(proxy)
	proxy.position = Vector3(start.x, float(Terrain.sample(start).height) + 0.23, start.y)
	_check(proxy.get_child_count() == 1 and proxy.find_children("*", "MeshInstance3D", true, false).is_empty(),
		"temporary capsule owns one shape and no visible model")
	_check(Engine.physics_ticks_per_second == int(PHYSICS_HZ), "matches sealed physics tick rate")
	await physics_frame
	await physics_frame
	for i: int in range(60):
		await physics_frame
		proxy.velocity = Vector3(0, -3.0, 0)
		proxy.move_and_slide()
	_check(proxy.is_on_floor(), "capsule actually settles on exact terrain")
	var settled := proxy.position
	var settled_xz := Vector2(settled.x, settled.z)
	_check(settled_xz.distance_to(start) < 0.08 and Sweep.dry_footprint(settled_xz, RADIUS, 1.0),
		"settled at intended dry start without fake position writes")

	var observed_floor_ticks := 0
	var owned_ground_contacts := 0
	var all_dry := true
	var height_delta_max := 0.0
	var support_error_max := 0.0
	var clipped := 0
	var clipped_streak := 0
	var approach_ticks := 0
	var travel_limit_breached := false
	var request := -north * 2.25 / PHYSICS_HZ
	var known_body := fixture.get_node("AcceptedGround/GroundBody")
	for i: int in range(MAX_APPROACH_TICKS):
		await physics_frame
		approach_ticks += 1
		var pose := Vector2(proxy.position.x, proxy.position.z)
		var allowed := Sweep.allowed_delta(pose, request, RADIUS, 1.0)
		if allowed.length() < request.length() - 0.0001:
			clipped += 1
			clipped_streak += 1
		else:
			clipped_streak = 0
		# Keep the original floor snap; do not drive a settled capsule into the slope.
		var grounded_y := 0.0 if proxy.is_on_floor() else proxy.velocity.y - 9.8 / PHYSICS_HZ
		proxy.velocity = Vector3(allowed.x * PHYSICS_HZ, grounded_y, allowed.y * PHYSICS_HZ)
		proxy.move_and_slide()
		if proxy.is_on_floor():
			observed_floor_ticks += 1
		for hit_index: int in range(proxy.get_slide_collision_count()):
			if proxy.get_slide_collision(hit_index).get_collider() == known_body:
				owned_ground_contacts += 1
		var observed := Vector2(proxy.position.x, proxy.position.z)
		var sample := Terrain.sample(observed)
		all_dry = all_dry and Sweep.dry_footprint(observed, RADIUS, 1.0)
		height_delta_max = maxf(height_delta_max, absf(proxy.position.y - settled.y))
		if bool(sample.valid):
			support_error_max = maxf(support_error_max, absf(proxy.position.y - float(sample.height)))
		else:
			all_dry = false
		if observed.distance_to(settled_xz) >= MAX_TRAVEL_M:
			travel_limit_breached = true
			break
		if approach_ticks >= MIN_APPROACH_TICKS and clipped_streak >= REQUIRED_CLIPPED_STREAK:
			break
	var stopped := Vector2(proxy.position.x, proxy.position.z)
	var stopped_sample := Terrain.sample(stopped)
	_check(not travel_limit_breached and stopped.distance_to(settled_xz) > 0.85 and stopped.distance_to(settled_xz) < MAX_TRAVEL_M,
		"actual observed inward movement followed by shore stop")
	_check(approach_ticks >= MIN_APPROACH_TICKS and observed_floor_ticks >= approach_ticks - 3 and owned_ground_contacts >= 20,
		"real grounded ticks and slide contacts belonging to exact terrain body")
	_check(height_delta_max >= 0.055 and support_error_max <= 0.075,
		"physical Y follows genuine relief with capsule support tolerance")
	_check(all_dry and bool(stopped_sample.valid) and float(stopped_sample.bank_side) == 1.0,
		"all observed footprints remain dry and on the original bank")
	_check(clipped_streak >= REQUIRED_CLIPPED_STREAK and float(stopped_sample.shore_distance) >= River.DEFAULT_DRY_MARGIN + RADIUS and
		float(stopped_sample.shore_distance) <= River.DEFAULT_DRY_MARGIN + RADIUS + 0.14,
		"stops near a reachable dry edge, rather than no movement or crossing")

	var hold_dry := true
	for i: int in range(HOLD_STEPS):
		await physics_frame
		var before := Vector2(proxy.position.x, proxy.position.z)
		var allowed := Sweep.allowed_delta(before, request, RADIUS, 1.0)
		# Keep the original floor snap; do not drive a settled capsule into the slope.
		var grounded_y := 0.0 if proxy.is_on_floor() else proxy.velocity.y - 9.8 / PHYSICS_HZ
		proxy.velocity = Vector3(allowed.x * PHYSICS_HZ, grounded_y, allowed.y * PHYSICS_HZ)
		proxy.move_and_slide()
		var after := Vector2(proxy.position.x, proxy.position.z)
		hold_dry = hold_dry and Sweep.dry_footprint(after, RADIUS, 1.0)
	var final_xz := Vector2(proxy.position.x, proxy.position.z)
	_check(hold_dry and stopped.distance_to(final_xz) <= 0.06 and proxy.is_on_floor(),
		"continued input cannot push through or cause bank drift")
	_check(current_scene == null, "default remains unmodified and inactive")
	_finish(fixture, {"travel_m":stopped.distance_to(settled_xz), "floor_ticks":observed_floor_ticks,
		"owned_ground_contacts":owned_ground_contacts, "observed_relief_m":height_delta_max,
		"max_center_height_error_m":support_error_max, "guard_clipped_ticks":clipped,
		"approach_ticks":approach_ticks, "terminal_clipped_streak":clipped_streak,
		"travel_limit_breached":travel_limit_breached, "stopped_shore_distance_m":float(stopped_sample.shore_distance)})

func _check(ok: bool, label: String) -> void:
	checks += 1
	if not ok:
		failures.append(label)

func _finish(fixture: Node3D, observations: Dictionary) -> void:
	fixture.free()
	print(JSON.stringify({"suite":"fixture_same_bank_capsule_motion", "checks":checks, "failures":failures,
		"observations":observations, "visible_actor":false, "pixels_reviewed":false, "gameplay_bound":false}))
	for label in failures:
		push_error(label)
	quit(0 if failures.is_empty() else 1)
