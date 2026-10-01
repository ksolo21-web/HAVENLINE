extends RefCounted

## Shipping camera policy for T04. It owns composition math only; Camera3D
## application remains an integration-only call site in main.gd.

const BASE_FULL_HEIGHT := 14.30
const MAX_FULL_HEIGHT := 16.00
const MIN_HORIZONTAL_SPAN := 19.50
const FOCUS_HEIGHT := 0.95
const LOOK_AHEAD := 0.72
const TARGET_BLEND := 0.36
const TARGET_MAX_DISTANCE := 8.00
const MAX_TARGET_SHIFT := 2.20
const FOLLOW_SHARPNESS := 8.60
const ZOOM_SHARPNESS := 6.40
const VIEW_OFFSET := Vector3(0.0, 6.8, 8.6)
const VIEW_RAY_PADDING := 18.0
const WORLD_MIN := Vector2(-14.2, -16.2)
const WORLD_MAX := Vector2(14.2, 16.2)

var smoothed_focus := Vector3.ZERO
var smoothed_full_height := BASE_FULL_HEIGHT
var initialized := false

static func finite_vector3(value: Vector3) -> bool:
	return is_finite(value.x) and is_finite(value.y) and is_finite(value.z)

static func safe_aspect(viewport_size: Vector2) -> float:
	if not is_finite(viewport_size.x) or not is_finite(viewport_size.y):
		return 16.0 / 9.0
	if viewport_size.x <= 0.0 or viewport_size.y <= 0.0:
		return 16.0 / 9.0
	return clampf(viewport_size.x / viewport_size.y, 1.0, 3.0)

static func full_height_for(viewport_size: Vector2) -> float:
	var aspect := safe_aspect(viewport_size)
	return clampf(maxf(BASE_FULL_HEIGHT, MIN_HORIZONTAL_SPAN / aspect), BASE_FULL_HEIGHT, MAX_FULL_HEIGHT)

static func bounded_focus(value: Vector3) -> Vector3:
	return Vector3(
		clampf(value.x, WORLD_MIN.x, WORLD_MAX.x),
		value.y,
		clampf(value.z, WORLD_MIN.y, WORLD_MAX.y)
	)

static func movement_direction(velocity: Vector3, facing: Vector3) -> Vector3:
	var direction := Vector3(velocity.x, 0.0, velocity.z)
	if not finite_vector3(direction) or direction.length_squared() < 0.0225:
		direction = Vector3(facing.x, 0.0, facing.z)
	if not finite_vector3(direction) or direction.length_squared() < 0.0001:
		return Vector3(0.0, 0.0, -1.0)
	return direction.normalized()

static func desired_focus(
	player_world: Vector3,
	velocity: Vector3,
	facing: Vector3,
	action_target: Variant = null
) -> Vector3:
	var player := player_world if finite_vector3(player_world) else Vector3.ZERO
	var focus := player + Vector3(0.0, FOCUS_HEIGHT, 0.0)
	focus += movement_direction(velocity, facing) * LOOK_AHEAD
	if action_target is Vector3 and finite_vector3(action_target):
		var target: Vector3 = action_target
		var delta := Vector3(target.x - player.x, 0.0, target.z - player.z)
		if delta.length() <= TARGET_MAX_DISTANCE:
			focus += (delta * TARGET_BLEND).limit_length(MAX_TARGET_SHIFT)
	return bounded_focus(focus)

static func desired_full_height(viewport_size: Vector2, player_world: Vector3, action_target: Variant = null) -> float:
	var height := full_height_for(viewport_size)
	if action_target is Vector3 and finite_vector3(action_target) and finite_vector3(player_world):
		var distance := Vector2(action_target.x - player_world.x, action_target.z - player_world.z).length()
		if distance <= TARGET_MAX_DISTANCE:
			height = maxf(height, BASE_FULL_HEIGHT + maxf(0.0, distance - 5.0) * 0.25)
	return minf(height, MAX_FULL_HEIGHT)

func reset(player_world: Vector3, viewport_size := Vector2(1920.0, 1080.0)) -> void:
	smoothed_focus = desired_focus(player_world, Vector3.ZERO, Vector3(0.0, 0.0, -1.0))
	smoothed_full_height = full_height_for(viewport_size)
	initialized = true

func compose(
	player_world: Vector3,
	velocity: Vector3,
	facing: Vector3,
	action_target: Variant,
	viewport_size: Vector2,
	delta: float,
	snap := false
) -> Dictionary:
	var target_focus := desired_focus(player_world, velocity, facing, action_target)
	var target_height := desired_full_height(viewport_size, player_world, action_target)
	if snap or not initialized:
		smoothed_focus = target_focus
		smoothed_full_height = target_height
		initialized = true
	else:
		var safe_delta := clampf(delta if is_finite(delta) else 0.0, 0.0, 0.25)
		var focus_alpha := 1.0 - exp(-FOLLOW_SHARPNESS * safe_delta)
		var zoom_alpha := 1.0 - exp(-ZOOM_SHARPNESS * safe_delta)
		smoothed_focus = smoothed_focus.lerp(target_focus, focus_alpha)
		# Widen immediately on a narrower layout or farther target so an active
		# subject is never cropped during a resize. Ease inward afterward.
		if target_height > smoothed_full_height:
			smoothed_full_height = target_height
		else:
			smoothed_full_height = lerpf(smoothed_full_height, target_height, zoom_alpha)
	var offset := VIEW_OFFSET
	var camera_position := smoothed_focus + offset + offset.normalized() * VIEW_RAY_PADDING
	return {
		"focus": smoothed_focus,
		"camera_position": camera_position,
		"full_height": smoothed_full_height,
		"keep_aspect": Camera3D.KEEP_HEIGHT,
		"aspect": safe_aspect(viewport_size),
		"target_in_range": action_target is Vector3 and finite_vector3(action_target) and Vector2(action_target.x - player_world.x, action_target.z - player_world.z).length() <= TARGET_MAX_DISTANCE
	}

static func descriptor() -> Dictionary:
	return {
		"authority_id": "T04-reference-camera-v1",
		"projection": "orthographic",
		"base_full_height": BASE_FULL_HEIGHT,
		"maximum_full_height": MAX_FULL_HEIGHT,
		"minimum_horizontal_span": MIN_HORIZONTAL_SPAN,
		"focus_height": FOCUS_HEIGHT,
		"look_ahead": LOOK_AHEAD,
		"follow_sharpness": FOLLOW_SHARPNESS,
		"view_offset": [VIEW_OFFSET.x, VIEW_OFFSET.y, VIEW_OFFSET.z],
		"automatic_target_inclusion": true,
		"automatic_landscape_aspect_adaptation": true,
		"adds_render_content": false,
		"physical_4k60_certified": false
	}
