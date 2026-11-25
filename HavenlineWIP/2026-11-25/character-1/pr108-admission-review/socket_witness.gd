extends SceneTree
# Isolated engine negative control, no game scene, model, or renderer.
var failures := 0
func require(ok: bool, msg: String) -> void:
	if not ok:
		failures += 1
		push_error(msg)
func _initialize() -> void:
	call_deferred("run")
func run() -> void:
	var rig := Skeleton3D.new()
	root.add_child(rig)
	var bone := rig.add_bone("Hand")
	rig.set_bone_rest(bone, Transform3D.IDENTITY)
	rig.set_bone_pose(bone, Transform3D(Basis.IDENTITY, Vector3(.2, .55, -.1)))
	var palm := Vector3(-.010943975069872653, .011581463822213485, -.009901172622213655)
	var original := BoneAttachment3D.new()
	original.bone_name = "Hand"
	rig.add_child(original)
	original.position = palm
	var preserved := BoneAttachment3D.new()
	preserved.bone_name = "Hand"
	rig.add_child(preserved)
	var socket := Node3D.new()
	preserved.add_child(socket)
	socket.position = palm
	# Our comparison is world-space with a nontrivial skeleton placement.
	rig.position = Vector3(2.0, .3, 4.0)
	await process_frame
	for angle: float in [0.0, .35, -.95, 1.14]:
		rig.set_bone_pose_rotation(bone, Quaternion(Vector3.FORWARD, angle))
		rig.set_bone_pose_position(bone, Vector3(.2 + angle*.03, .55, -.1))
		rig.force_update_all_dirty_bones()
		await process_frame
		var expected_wrist := rig.global_transform * rig.get_bone_global_pose(bone)
		var expected_palm := expected_wrist * palm
		require(original.global_position.distance_to(expected_wrist.origin) < 1e-5, "PR model attachment must collapse to bone origin")
		require(absf(original.global_position.distance_to(expected_palm)-palm.length()) < 1e-5, "PR local offset must be absent after bone update")
		require(socket.global_position.distance_to(expected_palm) < 1e-5, "child marker must follow full bone transform and offset")
	print("socket negative control stages=4 failures=", failures)
	quit(0 if failures == 0 else 1)
