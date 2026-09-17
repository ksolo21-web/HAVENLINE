extends Node3D

const Character1Motion = preload("res://scripts/character1_motion.gd")
const CHARACTER_SCENE = preload("res://assets/characters/Character1.glb")

func gather_meshes(node: Node, meshes: Array[MeshInstance3D]) -> void:
	if node is MeshInstance3D:
		meshes.append(node as MeshInstance3D)
	for child in node.get_children():
		gather_meshes(child, meshes)

func _ready() -> void:
	# QA-only PackedScene consumed by the production C5 motion harness. It uses
	# the immutable shipping Character 1 GLB and the same T06 animation installer
	# as gameplay; it does not provide alternate runtime motion or gameplay state.
	var visual := CHARACTER_SCENE.instantiate() as Node3D
	visual.name = "Character1Visual"
	add_child(visual)
	var meshes: Array[MeshInstance3D] = []
	gather_meshes(visual, meshes)
	var bounds := AABB()
	var first := true
	for mesh in meshes:
		var box := global_transform.affine_inverse()*mesh.global_transform*mesh.get_aabb()
		bounds = box if first else bounds.merge(box)
		first = false
	assert(not first and bounds.size.y > 0.01, "T09 C5 fixture requires Character 1 render geometry")
	var scale_factor := 1.75/bounds.size.y
	visual.scale *= scale_factor
	visual.position = Vector3(-bounds.get_center().x,-bounds.position.y,-bounds.get_center().z)*scale_factor
	var installed := Character1Motion.install(self,"player_lead")
	assert(bool(installed.get("passed",false)), "T09 C5 fixture failed to install shipping Character 1 motion")
	set_meta("t09_qa_only",true)
	set_meta("t09_motion_profiles",["human_player_chop","human_player_mine","human_player_dismantle"])
