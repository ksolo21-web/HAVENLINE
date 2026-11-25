extends RefCounted
## Two-handed axe and pickaxe on the existing Character 1 rig.
const Select = preload("res://tool_select.gd")
const HeroLocomotion = preload("res://previews/hero_locomotion.gd")
const AXE_SCENE = preload("res://assets/tools/axe.glb")
const PICK_SCENE = preload("res://assets/tools/pickaxe.glb")
const ACTION_LIBRARY := &"l1_actions"
const MOVE_MIN := 0.08

var ready := false
var equipped := ""
var action := ""
var action_left := 0.0
var locomotion: HeroLocomotion
var _player: AnimationPlayer
var _skeleton: Skeleton3D
var _axe: Node3D
var _pick: Node3D
var _palm_l: BoneAttachment3D
var _palm_r: BoneAttachment3D
var _sheath: BoneAttachment3D
var _sockets: Dictionary = {}
var _host: Node

func install(host: Node, visual: Node3D, existing_locomotion) -> bool:
	if ready or not is_instance_valid(visual):
		return ready
	var skins := visual.find_children("*", "Skeleton3D", true, false)
	var players := visual.find_children("*", "AnimationPlayer", true, false)
	if skins.is_empty() or players.is_empty():
		return false
	_skeleton = skins[0]
	_player = players[0]
	_host = host
	var parsed = JSON.parse_string(FileAccess.get_file_as_string("res://assets/characters/character1_sockets.json"))
	if typeof(parsed) != TYPE_DICTIONARY:
		return false
	_sockets = parsed
	if existing_locomotion != null:
		locomotion = existing_locomotion
	else:
		locomotion = HeroLocomotion.new()
		if not locomotion.bind(visual):
			return false
	if not _claim_actions():
		return false
	_palm_l = _socket(String(_sockets.left_palm_bone), _vec(_sockets.left_palm_local))
	_palm_r = _socket(String(_sockets.right_palm_bone), _vec(_sockets.right_palm_local))
	_sheath = _socket(String(_sockets.sheath_bone), _vec(_sockets.sheath_local))
	_axe = _host_tool(AXE_SCENE, "TwoHandAxe")
	_pick = _host_tool(PICK_SCENE, "TwoHandPickaxe")
	ready = _axe != null and _pick != null
	return ready

func resolve_tool(tree_ready: bool, rock_ready: bool) -> String:
	if action == "mine" or (rock_ready and not tree_ready and action != "chop"):
		return Select.for_target("rock")
	if action == "chop" or tree_ready:
		return Select.for_target("tree")
	if action == "carry":
		return Select.for_target("tree")
	return ""

func begin_action(name: String) -> void:
	if not ready or not _player.has_animation(_clip(name)):
		return
	action = name
	locomotion.suspend = true
	_player.play(_clip(name))
	action_left = _player.get_animation(_clip(name)).length

func drive(dt: float, speed: float, grounded: bool, tree_ready: bool, rock_ready: bool, carrying: bool) -> void:
	if not ready:
		return
	if action_left > 0.0:
		action_left = maxf(action_left - maxf(dt, 0.0), 0.0)
		if action_left == 0.0:
			action = ""
			locomotion.suspend = false
			locomotion.current = ""
	else:
		action = ""
	var moving := grounded and speed >= MOVE_MIN
	if action_left > 0.0:
		pass
	elif not moving and tree_ready:
		_hold("chop")
	elif not moving and rock_ready:
		_hold("mine")
	elif not moving and carrying:
		_hold("carry")
	else:
		locomotion.suspend = false
		locomotion.observe(speed, grounded)
	equipped = resolve_tool(tree_ready, rock_ready)
	var gripping := action == "chop" or action == "mine" or action == "carry"
	_place(not gripping)

func _hold(name: String) -> void:
	var clip := _clip(name)
	if not _player.has_animation(clip):
		return
	locomotion.suspend = true
	if _player.current_animation != clip:
		_player.play(clip)
	_player.seek(_player.get_animation(clip).length, true)
	_player.pause()
	action = name

func _place(sheathed: bool) -> void:
	_axe.hide()
	_pick.hide()
	var tool: Node3D = _axe if equipped == "axe" else (_pick if equipped == "pickaxe" else null)
	if tool == null:
		return
	if sheathed or action.is_empty():
		_stick(tool, _sheath.global_transform, 0.72)
		tool.show()
		return
	var lower := _palm_r.global_position
	var upper := _palm_l.global_position
	if lower.y > upper.y:
		var swap := lower
		lower = upper
		upper = swap
	var span := upper - lower
	if span.length() < 0.05:
		_stick(tool, _sheath.global_transform, 0.95)
		tool.show()
		return
	var axis := span.normalized()
	# Keep a readable tool length. The haft still runs through both palms.
	var scale := 0.95 / 0.70
	var grips: Array = _sockets.axe_grip_y if equipped == "axe" else _sockets.pick_grip_y
	var grip_mid := (float(grips[0]) + float(grips[1])) * 0.5
	var hands_mid := (lower + upper) * 0.5
	var side := axis.cross(Vector3.FORWARD)
	if side.length() < 0.001:
		side = axis.cross(Vector3.RIGHT)
	side = side.normalized()
	tool.top_level = true
	tool.global_position = hands_mid - axis * grip_mid * scale + side * 0.08
	tool.global_basis = _basis_y(axis)
	tool.scale = Vector3.ONE * scale
	tool.show()

func _stick(tool: Node3D, xform: Transform3D, length: float) -> void:
	tool.top_level = true
	tool.global_position = xform.origin
	var up := xform.basis.y.normalized()
	if up.length() < 0.2:
		up = Vector3.UP
	tool.global_basis = _basis_y(up)
	tool.scale = Vector3.ONE * (length / 0.70)

func _basis_y(y_axis: Vector3) -> Basis:
	var x_axis := y_axis.cross(Vector3.FORWARD)
	if x_axis.length() < 0.001:
		x_axis = y_axis.cross(Vector3.RIGHT)
	x_axis = x_axis.normalized()
	var z_axis := x_axis.cross(y_axis).normalized()
	return Basis(x_axis, y_axis.normalized(), z_axis)

func _claim_actions() -> bool:
	if _player.has_animation_library(ACTION_LIBRARY):
		return true
	var library := AnimationLibrary.new()
	for token in ["chop", "mine", "carry"]:
		var source_name := _imported(token)
		if source_name.is_empty():
			return false
		var copy := _player.get_animation(source_name).duplicate() as Animation
		copy.loop_mode = Animation.LOOP_LINEAR if token == "carry" else Animation.LOOP_NONE
		if library.add_animation(token, copy) != OK:
			return false
	return _player.add_animation_library(ACTION_LIBRARY, library) == OK

func _imported(token: String) -> String:
	var want := "presetbiped" + token
	for animation_name in _player.get_animation_list():
		var full := String(animation_name)
		var leaf := full.get_slice("/", full.get_slice_count("/") - 1)
		var key := leaf.to_lower().replace(":", "").replace("_", "").replace(" ", "")
		if key == want:
			return full
	return ""

func _clip(token: String) -> StringName:
	return StringName(String(ACTION_LIBRARY) + "/" + token)

func _socket(bone: String, local: Vector3) -> BoneAttachment3D:
	var attachment := BoneAttachment3D.new()
	attachment.name = "Socket_" + bone
	attachment.bone_name = bone
	_skeleton.add_child(attachment)
	attachment.position = local
	return attachment

func _host_tool(scene: PackedScene, node_name: String) -> Node3D:
	var tool := scene.instantiate() as Node3D
	if tool == null:
		return null
	tool.name = node_name
	var mount := _skeleton.get_parent().get_parent() if _skeleton.get_parent() != null and _skeleton.get_parent().get_parent() != null else _host
	mount.add_child(tool)
	tool.top_level = true
	tool.hide()
	return tool

func _vec(values: Array) -> Vector3:
	return Vector3(float(values[0]), float(values[1]), float(values[2]))
