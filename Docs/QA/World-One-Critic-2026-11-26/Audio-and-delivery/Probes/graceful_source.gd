extends SceneTree
func _initialize() -> void:
	run.call_deferred()
func run():
	var field=load("res://field_opening.tscn").instantiate()
	root.add_child(field)
	current_scene=field
	for tick in 90: await physics_frame
	print("FIELD_AUDIO_CLOSE_CONTROL ",field.sound._loops.size()," loops before normal close; score ",field.sound._state)
	root.close_requested.emit()
