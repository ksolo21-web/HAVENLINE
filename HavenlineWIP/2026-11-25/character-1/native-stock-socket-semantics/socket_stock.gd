extends SceneTree
# Exact stock Character1 GLB, not external PR asset. Socket semantics only.
const OFFSETS := {
	"L_Hand": Vector3(-0.010943975069872653, 0.011581463822213485, -0.009901172622213655),
	"R_Hand": Vector3(0.01337302578632694, 0.00701647497518859, -0.002696041771999337),
	"Spine02": Vector3(-0.02058618283480289, 0.04160797084615776, 0.10929311889756534)
}
var failures: Array[String] = []
var checks := 0

func require(ok: bool, reason: String) -> void:
	checks += 1
	if not ok:
		failures.append(reason)

func _initialize() -> void:
	call_deferred("run")

func run() -> void:
	var doc := GLTFDocument.new()
	var state := GLTFState.new()
	var code := doc.append_from_buffer(FileAccess.get_file_as_bytes("res://source.input"), "res://", state)
	if code != OK:
		push_error("Pinned source GLTF could not be imported: " + str(code))
		quit(2)
		return
	var host := Node3D.new()
	root.add_child(host)
	host.position = Vector3(1.75, -0.25, 2.4)
	host.rotation.y = 0.67
	var actor := doc.generate_scene(state)
	host.add_child(actor)
	var rigs := actor.find_children("*", "Skeleton3D", true, false)
	var players := actor.find_children("*", "AnimationPlayer", true, false)
	if rigs.size() != 1 or players.size() != 1:
		push_error("Unexpected native stock character structure")
		quit(2)
		return
	var rig := rigs[0] as Skeleton3D
	var player := players[0] as AnimationPlayer
	player.callback_mode_process = AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_MANUAL
	var slots := {}
	for bone: String in OFFSETS:
		var idx := rig.find_bone(bone)
		if idx < 0:
			push_error("Missing exact source bone: " + bone)
			quit(2)
			return
		var direct := BoneAttachment3D.new()
		direct.name = "PRModeled_" + bone
		direct.bone_name = bone
		rig.add_child(direct)
		direct.position = OFFSETS[bone]
		var follow := BoneAttachment3D.new()
		follow.name = "FixedParent_" + bone
		follow.bone_name = bone
		rig.add_child(follow)
		var child := Node3D.new()
		follow.add_child(child)
		child.position = OFFSETS[bone]
		slots[bone] = {"idx":idx,"direct":direct,"child":child}
	await process_frame
	var per_bone := {}
	for bone: String in OFFSETS:
		per_bone[bone] = {"direct_origin_error_max_m":0.0, "direct_offset_loss_min_m":10.0,
			"direct_offset_loss_max_m":0.0, "fixed_offset_error_max_m":0.0,"bone_origin_travel_max_m":0.0}
	var previous := {}
	var phases: Array[String] = []
	for name: StringName in player.get_animation_list():
		var token := String(name).to_lower()
		if not (token.ends_with("idle") or token.ends_with("walk") or token.ends_with("run")):
			continue
		player.play(name)
		var duration := player.get_animation(name).length
		for ratio: float in [0.13, 0.49, 0.82]:
			player.seek(duration * ratio, true)
			player.advance(0.0)
			rig.force_update_all_bone_transforms()
			await process_frame
			var tag := String(name) + "@" + str(ratio)
			phases.append(tag)
			for bone: String in OFFSETS:
				var slot: Dictionary = slots[bone]
				var expected := rig.global_transform * rig.get_bone_global_pose(slot.idx)
				var raw_offset: Vector3 = OFFSETS[bone]
				var desired := expected * raw_offset
				var bad: Vector3 = slot.direct.global_position
				var preserved: Vector3 = slot.child.global_position
				var err_origin := bad.distance_to(expected.origin)
				var err_offset := bad.distance_to(desired)
				var err_fixed := preserved.distance_to(desired)
				require(err_origin < 0.00001, tag + " original direct marker was not pinned to joint origin: " + bone)
				require(err_offset > 0.001, tag + " direct marker unexpectedly retained its declared offset: " + bone)
				require(err_fixed < 0.00001, tag + " child did not retain offset after native clip: " + bone)
				var row: Dictionary = per_bone[bone]
				row.direct_origin_error_max_m = maxf(row.direct_origin_error_max_m, err_origin)
				row.direct_offset_loss_min_m = minf(row.direct_offset_loss_min_m, err_offset)
				row.direct_offset_loss_max_m = maxf(row.direct_offset_loss_max_m, err_offset)
				row.fixed_offset_error_max_m = maxf(row.fixed_offset_error_max_m, err_fixed)
				if previous.has(bone):
					row.bone_origin_travel_max_m = maxf(row.bone_origin_travel_max_m, expected.origin.distance_to(previous[bone]))
				previous[bone] = expected.origin
	require(phases.size()==9, "Not exact expected 3 locomotion clips x3 phases")
	require(per_bone["L_Hand"].bone_origin_travel_max_m > .001 and per_bone["R_Hand"].bone_origin_travel_max_m > .001, "No independently varying evaluated stock palm poses")
	print(JSON.stringify({"source":"11c14a1c pinned stock Character1; native attachment semantics only",
		"checks":checks,"failures":failures,"phases":phases,"bones":per_bone}, "  "))
	quit(0 if failures.is_empty() else 1)
