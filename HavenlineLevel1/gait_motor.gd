extends RefCounted

const MAX_SPEED := 2.80
const DEAD_ZONE := 0.035
const ACCELERATION := 8.0
const BRAKING := 11.0
const MOVING_TURN := 5.9
const PIVOT_TURN := 10.8

func step(world: Node3D, input: Vector2, dt: float) -> float:
	var body: CharacterBody3D = world.actor
	var start := body.global_position
	var requested := remap(clampf(input.length(), DEAD_ZONE, 1.0), DEAD_ZONE, 1.0, 0.0, MAX_SPEED)
	var forward := Vector3(sin(body.rotation.y), 0.0, cos(body.rotation.y))
	var speed := body.velocity.slide(Vector3.UP).length()
	if requested > 0.0:
		var view_right: Vector3 = world.camera.global_basis.x
		var view_near: Vector3 = view_right.cross(Vector3.UP)
		var wish: Vector3 = (view_right * input.x + view_near * input.y).normalized()
		var turn_speed := lerpf(PIVOT_TURN, MOVING_TURN, clampf(speed / MAX_SPEED, 0.0, 1.0))
		body.rotation.y = rotate_toward(body.rotation.y, atan2(wish.x, wish.z), turn_speed * dt)
		forward = Vector3(sin(body.rotation.y), 0.0, cos(body.rotation.y))
		# Brake into an about-face so the player redirects their weight before taking off.
		requested *= smoothstep(-0.45, 0.85, forward.dot(wish))
	speed = move_toward(speed, requested, (ACCELERATION if requested > speed else BRAKING) * dt)
	body.velocity = forward * speed
	body.move_and_slide()
	world.constrain_private_snow_travel()
	var traveled := (body.global_position - start).slide(Vector3.UP)
	# A wall or the edge of the map can shorten a stride. Drive the gait from that result.
	return traveled.length() / maxf(dt, 0.00001)
