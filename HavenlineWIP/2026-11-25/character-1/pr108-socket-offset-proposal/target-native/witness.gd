extends SceneTree
# Target-only real PR rig+kit. Uses naturally advancing mixer and skeleton.
const Kit = preload("res://character_kit.gd")
const Hero = preload("res://assets/characters/Character1.glb")
var failures: Array[String] = []
var checks := 0

func check(ok: bool, label: String) -> void:
	checks += 1
	if not ok:
		failures.append(label)

func _initialize() -> void:
	call_deferred("run")

func run() -> void:
	var flags := OS.get_cmdline_user_args()
	if flags.size() != 1 or flags[0] not in ["original", "offset-only"]:
		quit(2)
		return
	var patched := flags[0] == "offset-only"
	var host := Node3D.new()
	root.add_child(host)
	host.position = Vector3(1.7, -0.2, 2.4)
	host.rotation.y = 0.63
	var hero := Hero.instantiate() as Node3D
	host.add_child(hero)
	var kit = Kit.new()
	if not kit.install(host, hero, null):
		push_error("Exact PR rig/kit did not install")
		quit(2)
		return
	var rig: Skeleton3D = kit._skeleton
	var player: AnimationPlayer = kit._player
	var manifest: Dictionary = kit._sockets
	var slots := [
		[kit._palm_l, manifest.left_palm_bone, manifest.left_palm_local],
		[kit._palm_r, manifest.right_palm_bone, manifest.right_palm_local],
		[kit._sheath, manifest.sheath_bone, manifest.sheath_local],
	]
	for row: Array in slots:
		var att: BoneAttachment3D = row[0]
		check(att.get_parent() == rig and att.name == "Socket_" + String(row[1]) and att.bone_name == row[1] and rig.find_bone(row[1]) >= 0, "socket identity")
		check(att.has_node("LocalOffset") == patched, "matching child variant")
	var maxima := {"marker_error_m":0.0, "direct_offset_loss_m":0.0, "tool_input_error_m":0.0}
	var motions := {}
	var samples_by_action := {}
	for action in ["chop", "mine", "carry"]:
		kit.begin_action(action)
		check(kit.action == action and not player.current_animation.is_empty(), action + " installed")
		var phases: Array[float] = []
		var first := Vector3.ZERO
		var travel := 0.0
		# No seek/advance/force updates, no manual callback mode. Wall time only
		# paces observations; the current native clip position verifies growth.
		for i in range(8):
			await create_timer(0.025).timeout
			await process_frame
			phases.append(player.current_animation_position)
			var expected_points: Array[Vector3] = []
			var represented_points: Array[Vector3] = []
			for row: Array in slots:
				var att: BoneAttachment3D = row[0]
				var off: Array = row[2]
				var offset := Vector3(float(off[0]), float(off[1]), float(off[2]))
				var bone_world := rig.global_transform * rig.get_bone_global_pose(rig.find_bone(row[1]))
				var expected := bone_world * offset
				var marker: Node3D = att.get_node_or_null("LocalOffset") as Node3D if patched else att
				if not is_instance_valid(marker):
					push_error("Missing expected socket marker")
					quit(2)
					return
				var oracle := expected if patched else bone_world.origin
				var error := marker.global_position.distance_to(oracle)
				maxima.marker_error_m = maxf(maxima.marker_error_m,error)
				check(error <= 0.0001, action + " natural bone/marker comparison " + String(row[1]))
				if not patched:
					var loss := marker.global_position.distance_to(expected)
					maxima.direct_offset_loss_m = maxf(maxima.direct_offset_loss_m,loss)
					check(loss > 0.001, "original drops nonzero offset")
				expected_points.append(expected)
				represented_points.append(marker.global_position)
			if i == 0:
				first = expected_points[0]
			travel = maxf(travel,first.distance_to(expected_points[0]))
			kit.equipped = "pickaxe" if action == "mine" else "axe"
			var tool: Node3D = kit._pick if action == "mine" else kit._axe
			kit._place(true)
			var sheath_residual := tool.global_position.distance_to(represented_points[2])
			check(sheath_residual <= 0.0001 and tool.visible, action + " sheath placement follows represented socket")
			maxima.tool_input_error_m = maxf(maxima.tool_input_error_m,sheath_residual)
			var lower := represented_points[1]
			var upper := represented_points[0]
			if lower.y > upper.y:
				var tmp := lower
				lower = upper
				upper = tmp
			var span := upper - lower
			var predicted := represented_points[2]
			if span.length() >= 0.05:
				var axis := span.normalized()
				var side := axis.cross(Vector3.FORWARD)
				if side.length() < 0.001:
					side = axis.cross(Vector3.RIGHT)
				var bands: Array = manifest.pick_grip_y if action == "mine" else manifest.axe_grip_y
				predicted = (upper + lower) * 0.5 - axis * (float(bands[0])+float(bands[1])) * 0.5 * (0.95/0.70) + side.normalized() * 0.08
			kit._place(false)
			var held_residual := tool.global_position.distance_to(predicted)
			maxima.tool_input_error_m = maxf(maxima.tool_input_error_m,held_residual)
			check(held_residual <= 0.0001 and tool.visible, action + " held placement uses expected socket input, including known unresolved 80 mm shift")
		check(phases.back() - phases.front() > 0.07, action + " naturally advanced")
		motions[action] = travel
		samples_by_action[action] = phases
	check(maxf(motions.chop,motions.mine) > 0.005, "animated target rig hand moved")
	print(JSON.stringify({"variant":flags[0],"checks":checks,"failures":failures,"samples_by_action":samples_by_action,"motion_m":motions,"maxima":maxima}, "  "))
	quit(0 if failures.is_empty() else 1)
