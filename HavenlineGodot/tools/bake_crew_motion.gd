extends SceneTree

# Reproducible locomotion transfer from the supplied C1 clips. Original GLBs are
# read-only. This is a motion candidate, NOT whole-rig or visual approval.
const MAP = {
	"mixamorigHips":"Pelvis", "mixamorigSpine":"Waist",
	"mixamorigSpine1":"Spine01", "mixamorigSpine2":"Spine02",
	"mixamorigNeck":"NeckTwist01", "mixamorigHead":"Head",
	"mixamorigLeftShoulder":"L_Clavicle", "mixamorigLeftArm":"L_Upperarm",
	"mixamorigLeftForeArm":"L_Forearm", "mixamorigLeftHand":"L_Hand",
	"mixamorigRightShoulder":"R_Clavicle", "mixamorigRightArm":"R_Upperarm",
	"mixamorigRightForeArm":"R_Forearm", "mixamorigRightHand":"R_Hand",
	"mixamorigLeftUpLeg":"L_Thigh", "mixamorigLeftLeg":"L_Calf",
	"mixamorigLeftFoot":"L_Foot", "mixamorigLeftToeBase":"L_ToeBase",
	"mixamorigRightUpLeg":"R_Thigh", "mixamorigRightLeg":"R_Calf",
	"mixamorigRightFoot":"R_Foot", "mixamorigRightToeBase":"R_ToeBase"
}
const RATE := 30.0
var source: Node3D
var source_rig: Skeleton3D
var source_player: AnimationPlayer
var failures: Array = []

func find_type(node: Node, kind: String) -> Node:
	if node.is_class(kind): return node
	for child in node.get_children():
		var found := find_type(child, kind)
		if found: return found
	return null

func _initialize(): call_deferred("run")

func run():
	source = load("res://assets/characters/Character1.glb").instantiate()
	root.add_child(source)
	source_rig = find_type(source, "Skeleton3D")
	source_player = find_type(source, "AnimationPlayer")
	if not source_rig or not source_player:
		push_error("Supplied character is missing its skeleton or animation player")
		quit(1); return
	DirAccess.make_dir_recursive_absolute("res://assets/motion")
	for id in [2,3,4]: bake(id)
	source.queue_free()
	print(JSON.stringify({"suite":"crew_motion_bake", "passed":failures.is_empty(), "failures":failures,"sample_rate":RATE,"source":"Character1.glb","production_approved":false}))
	quit(0 if failures.is_empty() else 1)

func bake(id: int):
	var target: Node3D = load("res://assets/characters/Character%d.glb" % id).instantiate()
	root.add_child(target)
	var rig: Skeleton3D = find_type(target, "Skeleton3D")
	var library := AnimationLibrary.new()
	var source_indices := {}
	for bone in MAP:
		var index := source_rig.find_bone(MAP[bone])
		if index < 0 or rig.find_bone(bone) < 0:
			failures.append("Character%d missing bone %s" % [id,bone]); target.queue_free(); return
		source_indices[bone] = index
	var hips := rig.find_bone("mixamorigHips")
	var source_hips := source_rig.find_bone("Pelvis")
	var rest_hips := rig.get_bone_global_rest(hips)
	var source_rest_hips := source_rig.get_bone_global_rest(source_hips)
	var source_toe := source_rig.find_bone("L_ToeBase")
	var target_toe := rig.find_bone("mixamorigLeftToeBase")
	var source_leg_length := absf(source_rest_hips.origin.y - source_rig.get_bone_global_rest(source_toe).origin.y)
	var target_leg_length := absf(rest_hips.origin.y - rig.get_bone_global_rest(target_toe).origin.y)
	var ratio := target_leg_length / maxf(0.01, source_leg_length)
	for clip in source_player.get_animation_list():
		if not (clip.ends_with("idle") or clip.ends_with("walk") or clip.ends_with("run")): continue
		var animation := Animation.new()
		animation.length = source_player.get_animation(clip).length
		animation.loop_mode = Animation.LOOP_LINEAR
		var tracks: Dictionary = {}
		for bone in MAP:
			var track := animation.add_track(Animation.TYPE_ROTATION_3D)
			animation.track_set_path(track, NodePath(".:" + bone))
			tracks[bone] = track
		var hip_track := animation.add_track(Animation.TYPE_POSITION_3D)
		animation.track_set_path(hip_track, NodePath(".:mixamorigHips"))
		source_player.play(clip)
		var frames := int(ceil(animation.length * RATE))
		for frame in range(frames + 1):
			var t := minf(animation.length, frame / RATE)
			source_player.seek(t, true)
			source_rig.force_update_all_bone_transforms()
			var desired: Array[Basis] = []
			for i in range(rig.get_bone_count()):
				var bone := rig.get_bone_name(i)
				var parent := rig.get_bone_parent(i)
				var parent_basis := desired[parent] if parent >= 0 else Basis.IDENTITY
				var local_basis := rig.get_bone_rest(i).basis
				var global_basis := parent_basis * local_basis
				if source_indices.has(bone):
					var si: int = source_indices[bone]
					global_basis = source_rig.get_bone_global_pose(si).basis * source_rig.get_bone_global_rest(si).basis.inverse() * rig.get_bone_global_rest(i).basis
					global_basis = global_basis.orthonormalized()
					local_basis = parent_basis.inverse() * global_basis
					animation.rotation_track_insert_key(tracks[bone], t, local_basis.get_rotation_quaternion().normalized())
				desired.append(global_basis)
			# Preserve target proportions: only root displacement is translated.
			# Limb translations/scales are NEVER copied between different bodies.
			var displacement := (source_rig.get_bone_global_pose(source_hips).origin - source_rest_hips.origin) * ratio
			animation.position_track_insert_key(hip_track, t, rig.get_bone_rest(hips).origin + displacement)
		library.add_animation(clip.get_slice(":", 2), animation)
	var path := "res://assets/motion/Character%d.res" % id
	var error := ResourceSaver.save(library, path, ResourceSaver.FLAG_COMPRESS)
	if error != OK: failures.append("Save failed for " + path)
	print("Baked Character%d: %s" % [id, str(library.get_animation_list())])
	target.queue_free()
