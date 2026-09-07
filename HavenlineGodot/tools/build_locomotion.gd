extends SceneTree

# Derived animation resources only. Original meshes, UVs, joints and weights stay untouched.
# These are review candidates, not a whole-rig quality certification.
const MAP := {
	"Hips":"Pelvis", "Spine":"Waist", "Spine1":"Spine01", "Spine2":"Spine02",
	"Neck":"NeckTwist01", "Head":"Head",
	"LeftShoulder":"L_Clavicle", "LeftArm":"L_Upperarm", "LeftForeArm":"L_Forearm", "LeftHand":"L_Hand",
	"RightShoulder":"R_Clavicle", "RightArm":"R_Upperarm", "RightForeArm":"R_Forearm", "RightHand":"R_Hand",
	"LeftUpLeg":"L_Thigh", "LeftLeg":"L_Calf", "LeftFoot":"L_Foot", "LeftToeBase":"L_ToeBase",
	"RightUpLeg":"R_Thigh", "RightLeg":"R_Calf", "RightFoot":"R_Foot", "RightToeBase":"R_ToeBase"
}

func skeleton(node: Node) -> Skeleton3D:
	if node is Skeleton3D: return node
	for child in node.get_children():
		var s := skeleton(child)
		if s: return s
	return null

func animation_player(node: Node) -> AnimationPlayer:
	if node is AnimationPlayer: return node
	for child in node.get_children():
		var player := animation_player(child)
		if player: return player
	return null

func _initialize():
	call_deferred("build")

func build():
	DirAccess.make_dir_recursive_absolute("res://assets/animations")
	var source: Node3D = load("res://assets/characters/Character1.glb").instantiate()
	root.add_child(source)
	var src := skeleton(source)
	var player := animation_player(source)
	player.callback_mode_process = AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_MANUAL
	var src_ids := {}
	for value in MAP.values():
		src_ids[value] = src.find_bone(value)
		if src_ids[value] < 0:
			push_error("Missing source bone: " + value)
			quit(1)
			return
	var manifest := {"schema":1, "source":"Character1.glb", "source_sha256":FileAccess.get_sha256("res://assets/characters/Character1.glb"), "status":"UNAPPROVED_RETARGET_CANDIDATE", "characters":{}}
	for id in [2,3,4]:
		var target: Node3D = load("res://assets/characters/Character%d.glb" % id).instantiate()
		root.add_child(target)
		var sk := skeleton(target)
		var mapping := {}
		var rest_rotations: Array[Quaternion] = []
		for bone in range(sk.get_bone_count()):
			rest_rotations.append(sk.get_bone_global_rest(bone).basis.get_rotation_quaternion())
			var suffix := sk.get_bone_name(bone).trim_prefix("mixamorig")
			if MAP.has(suffix): mapping[bone] = src_ids[MAP[suffix]]
		if mapping.size() != MAP.size():
			push_error("Incomplete locomotion mapping for C%d" % id)
			quit(1)
			return
		var hips := sk.find_bone("mixamorigHips")
		var foot := sk.find_bone("mixamorigLeftFoot")
		var src_hip: int = src_ids.Pelvis
		var src_foot: int = src_ids.L_Foot
		var leg_ratio := absf(sk.get_bone_global_rest(hips).origin.y - sk.get_bone_global_rest(foot).origin.y) / maxf(.01, absf(src.get_bone_global_rest(src_hip).origin.y - src.get_bone_global_rest(src_foot).origin.y))
		var library := AnimationLibrary.new()
		var report: Array = []
		for clip_name in player.get_animation_list():
			var suffix := ""
			for expected in ["idle", "walk", "run"]:
				if clip_name.to_lower().ends_with(expected): suffix = expected
			if suffix not in ["idle","walk","run"]: continue
			var original := player.get_animation(clip_name)
			var clip := Animation.new()
			clip.length = original.length
			clip.loop_mode = Animation.LOOP_LINEAR
			var tracks := {}
			for bone in mapping:
				var track := clip.add_track(Animation.TYPE_ROTATION_3D)
				clip.track_set_path(track, NodePath(str(target.get_path_to(sk)) + ":" + sk.get_bone_name(bone)))
				tracks[bone] = track
			var hip_track := clip.add_track(Animation.TYPE_POSITION_3D)
			clip.track_set_path(hip_track, NodePath(str(target.get_path_to(sk)) + ":" + sk.get_bone_name(hips)))
			player.play(clip_name)
			var samples := maxi(2, int(ceil(clip.length * 30)))
			for sample in range(samples + 1):
				var time := clip.length * float(sample) / samples
				player.seek(minf(time, clip.length - .000001), true)
				var globals: Array[Quaternion] = []
				globals.resize(sk.get_bone_count())
				for bone in range(sk.get_bone_count()):
					var parent := sk.get_bone_parent(bone)
					if mapping.has(bone):
						var source_bone: int = mapping[bone]
						var delta := src.get_bone_global_pose(source_bone).basis.orthonormalized().get_rotation_quaternion() * src.get_bone_global_rest(source_bone).basis.orthonormalized().get_rotation_quaternion().inverse()
						globals[bone] = (delta * rest_rotations[bone]).normalized()
						var local := globals[bone] if parent < 0 else globals[parent].inverse() * globals[bone]
						clip.rotation_track_insert_key(tracks[bone], time, local.normalized())
					else:
						var local := sk.get_bone_rest(bone).basis.get_rotation_quaternion()
						globals[bone] = local if parent < 0 else globals[parent] * local
				var hips_position := sk.get_bone_rest(hips).origin
				hips_position.y += (src.get_bone_global_pose(src_hip).origin.y - src.get_bone_global_rest(src_hip).origin.y) * leg_ratio
				clip.position_track_insert_key(hip_track, time, hips_position)
			library.add_animation(suffix, clip)
			report.append({"clip":suffix, "samples":samples+1, "length":clip.length, "mapped_bones":mapping.size()})
		if library.get_animation_list().size() != 3:
			push_error("Expected idle/walk/run for C%d" % id)
			quit(1)
			return
		var error := ResourceSaver.save(library, "res://assets/animations/Character%d.res" % id)
		if error != OK:
			push_error("Cannot save retarget library: %s" % error)
			quit(1)
			return
		manifest.characters[str(id)] = {"source_sha256":FileAccess.get_sha256("res://assets/characters/Character%d.glb" % id), "clips":report}
		target.free()
	var file := FileAccess.open("res://assets/animations/provenance.json", FileAccess.WRITE)
	file.store_string(JSON.stringify(manifest, "\t") + "\n")
	file.close()
	print(JSON.stringify(manifest))
	source.free()
	quit()
