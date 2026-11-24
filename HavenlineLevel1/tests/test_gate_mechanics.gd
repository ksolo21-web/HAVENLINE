extends SceneTree
const Gate = preload("res://technical_gate.gd")
var failures := 0

func check(ok: bool, desc: String) -> void:
	if not ok:
		failures += 1
		push_error(desc)

func _initialize() -> void:
	call_deferred("run")

func run() -> void:
	var south := Gate.new()
	var east := Gate.new()
	root.add_child(south)
	root.add_child(east)
	south.position = Vector3(0, 0, 4)
	east.position = Vector3(5, 0, 0)
	east.rotation_degrees.y = 90
	south.build("gate-south")
	east.build("gate-east")
	var south_safe := Vector3(0, 0, 5.3)
	check(not south.request_toggle(south_safe), "unearned gate inert")
	south.set_earned(true)
	east.set_earned(true)
	check(is_zero_approx(south.angle) and is_zero_approx(east.angle), "earned closed")
	check(south.request_toggle(south_safe), "south only toggle")
	south.advance(.016, Vector3(0, 0, 4), .31)
	check(south.holding_for_occupancy and is_zero_approx(south.angle), "threshold occupant holds opening without motion")
	for tick in 90:
		south.advance(.016, south_safe, .31)
		east.advance(.016, south_safe, .31)
	check(is_equal_approx(south.angle, PI * .5) and is_zero_approx(east.angle), "independent state; south fully open")
	var left := south.get_node("HingeLeft") as Node3D
	var body := left.get_child(0) as AnimatableBody3D
	var shape := body.get_child(0) as CollisionShape3D
	var mesh := body.get_child(1) as MeshInstance3D
	check(shape.global_transform.is_equal_approx(mesh.global_transform), "moving body visual and collision align")
	check(body.collision_layer == 1 and body.global_position.z < 3.5, "open leaf collider rotates inward")
	check(south.request_toggle(south_safe), "closing requested")
	south.advance(.016, Vector3(-.8, 0, 3.5), .31)
	check(south.holding_for_occupancy and is_equal_approx(south.angle, PI * .5), "occupied inward sweep holds close")
	for tick in 90:
		south.advance(.016, south_safe, .31)
	check(is_zero_approx(south.angle), "closing resumes once empty")
	var east_safe := Vector3(6.3, 0, 0)
	check(east.request_toggle(east_safe), "east only toggle")
	for tick in 90:
		east.advance(.016, east_safe, .31)
	var east_left := east.get_node("HingeLeft") as Node3D
	var east_body := east_left.get_child(0) as AnimatableBody3D
	check(east_body.global_position.x < 4.5 and is_zero_approx(south.angle), "east rotates into its own camp side")
	east.set_earned(false)
	check(not east.visible and east_body.collision_layer == 0, "unearned leafs must not obstruct")
	print("Gate mechanics fixture failures: ", failures)
	quit(0 if failures == 0 else 1)
