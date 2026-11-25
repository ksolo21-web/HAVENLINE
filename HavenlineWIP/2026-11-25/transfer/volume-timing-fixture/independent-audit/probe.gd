extends SceneTree
const Presenter = preload("res://presenter.gd")
func _initialize() -> void: call_deferred("run")
func run() -> void:
	var p := Presenter.new()
	root.add_child(p)
	var sources: Array[Vector3] = [Vector3.ZERO]
	var targets: Array[Vector3] = [Vector3.ONE]
	var first := ["a","r","wood",1]
	var second := ["distinct-but-matching","r","wood",1]
	var committed := {"a":["r","wood",1]}
	var supplied := committed.duplicate(true)
	supplied[second[0]] = ["r","wood",1]
	var result := {}
	var old_clock := []
	p.completed.connect(func(_a,_b,_c): old_clock.append(not p.admit(second,supplied,4,11,sources,targets)))
	result["original"] = p.bind(4, 9, "r", "wood") and p.admit(first,committed,4,10,sources,targets)
	result["duplicate_epoch_denied"] = not p.bind(4, 10, "r", "wood")
	result["active_distinct_denied"] = not p.admit(second,supplied,4,11,sources,targets)
	p.sample_elapsed("a",4,285000)
	result["callback_dispatch_denied"] = old_clock == [true]
	result["same_ticket_bumped_sequence_denied"] = not p.admit(first,committed,4,11,sources,targets)
	result["new_ticket_without_entry_denied"] = not p.admit(second,committed,4,11,sources,targets)
	result["copied_matching_entry_with_stale_sequence_denied"] = not p.admit(second,supplied,4,10,sources,targets)
	result["copied_matching_entry_with_new_ticket_and_claimed_sequence_admitted"] = p.admit(second,supplied,4,11,sources,targets)
	result["observed_really_instantiated"] = p.get_child_count() == 1
	result["original_unchanged"] = committed == {"a":["r","wood",1]}
	print(JSON.stringify(result))
	quit(0 if not result.values().has(false) else 1)
