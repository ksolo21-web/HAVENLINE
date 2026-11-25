extends SceneTree
const Bridge = preload("res://chop_impact_bridge.gd")
const TreeScript = preload("res://resource_tree.gd")
var checks := 0
var failed := 0

func _initialize() -> void:
	call_deferred("run")

func expect(value: bool, text: String) -> void:
	checks += 1
	failed += 0 if value else 1
	print(("PASS " if value else "FAIL ") + text)

func lane(case: String) -> void:
	var wrapper := Node3D.new()
	root.add_child(wrapper)
	var owner := Node3D.new()
	wrapper.add_child(owner)
	var actor_parent := Node3D.new()
	owner.add_child(actor_parent)
	var pawn := Node3D.new()
	actor_parent.add_child(pawn)
	pawn.position = Vector3(-1.17,0,6)
	pawn.rotation_degrees.y = -90.0
	var tree := TreeScript.new()
	owner.add_child(tree)
	tree.position = Vector3(-2,0,6)
	var donor := PackedScene.new()
	var dummy := Node3D.new()
	donor.pack(dummy)
	dummy.free()
	tree.build(donor,true)
	var marker := RefCounted.new()
	var bridge := Bridge.new()
	var live := func() -> Dictionary:
		return {"actor":pawn,"tree":tree,"authorized":true}
	expect(bridge.configure(marker,owner,live),case+" configured")
	var ticket := bridge.press(&"key_f")
	expect(ticket != null,case+" valid request before retirement")
	var candidate: Node = null
	match case:
		"actor":
			candidate = pawn
		"tree":
			candidate = tree
		"owner":
			candidate = owner
		"owner ancestor":
			candidate = wrapper
		"intermediate actor ancestor":
			candidate = actor_parent
	if candidate != null:
		candidate.queue_free()
		expect(pawn.is_inside_tree() and tree.is_inside_tree() and owner.is_inside_tree() and candidate.is_queued_for_deletion(),case+" still in tree in exact queue_free frame")
	var hit := bridge.marker_reached(marker,ticket)
	var stock_unchanged := tree.strikes==0 and tree.last_sequence==0
	if candidate != null:
		expect(not hit and stock_unchanged,case+" queued hierarchy denies marker before first sequence or notch; saw "+str([hit,tree.strikes,tree.last_sequence]))
		expect(not bridge.marker_reached(marker,ticket) and not bridge.marker_reached(marker,ticket),case+" consumed denial cannot replay")
	else:
		expect(hit and tree.strikes==1 and tree.last_sequence==1,case+" active identical context still strikes exactly once")
	expect(bridge.finish_or_cancel(marker,ticket),case+" playback owner closes exact ticket")
	wrapper.queue_free()
	await process_frame

func run() -> void:
	for case: String in ["healthy","actor","tree","owner","owner ancestor","intermediate actor ancestor"]:
		await lane(case)
	print("RETIREMENT ",checks," checks ",failed," failures")
	quit(0 if failed==0 else 1)
