extends Node3D
## Non-authoritative mesh only; visibility is still set by Opening from ledger IDs.
const ExactLod = preload("res://assets/studio/starter_ground_wood_lod.glb")

func _ready() -> void:
	var bundle := ExactLod.instantiate() as Node3D
	add_child(bundle)
