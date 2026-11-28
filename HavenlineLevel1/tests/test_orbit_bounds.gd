extends SceneTree
const Trial = preload("res://orbit_opening.tscn")
class ContactProbe extends Node3D:
	var impacts: Array[int] = []
	func can_receive_swirl() -> bool:
		return true
	func take_swirl_hit(turn: int) -> bool:
		impacts.append(turn)
		return true

func _initialize() -> void:
	call_deferred("run")

func run() -> void:
	var world = Trial.instantiate()
	root.add_child(world)
	await process_frame
	var all_ok := true
	var initial := Vector3(4,0,-9)
	world.actor.global_position = initial
	var friendly := ContactProbe.new()
	world.add_child(friendly)
	friendly.global_position = initial + Vector3(0,0,2.65)
	var visual := MeshInstance3D.new()
	var box := BoxMesh.new()
	box.size = Vector3(.30,1.5,.30)
	visual.mesh = box
	friendly.add_child(visual)
	visual.position.y=.75
	visual.hide()
	world.register_hostile(friendly,visual)
	for i in 85: await physics_frame
	all_ok = all_ok and friendly.impacts.is_empty() and world.character_kit.active
	friendly.add_to_group("swirl_hostiles")
	world.register_hostile(friendly, visual)
	for i in 145: await physics_frame
	var seen := {}
	for turn in friendly.impacts: seen[turn]=true
	all_ok = all_ok and friendly.impacts.size() >= 2 and friendly.impacts.size()==seen.size()
	world.actor.global_position += Vector3(4,0,0)
	var before := friendly.impacts.size()
	for i in 88: await physics_frame
	all_ok = all_ok and before==friendly.impacts.size() and world.character_kit.active
	# Test exit/re-entry and removal during a turn.
	world.actor.global_position = initial
	for i in 10: await physics_frame
	friendly.queue_free()
	for i in 3: await physics_frame
	all_ok = all_ok and world.character_kit.active and world.surfaces.size()==2
	print("No friendly damage, repeated turn deduplication, out-of-range and removed hostile: ", all_ok)
	quit(0 if all_ok else 1)
