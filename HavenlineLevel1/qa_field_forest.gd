extends SceneTree

var world
var origin := Vector2(374,545)
var holding := false

func _initialize() -> void:
	var hz := OS.get_environment("HAVENLINE_FIELD_PHYSICS_HZ").to_int()
	if hz in [30,60,120]: Engine.physics_ticks_per_second = hz
	call_deferred("_run")

func ticks(seconds: float) -> int:
	return ceili(seconds * Engine.physics_ticks_per_second)

func drive(direction: Vector3) -> void:
	if direction.length()<.01:
		if holding:
			var release := InputEventScreenTouch.new()
			release.index = 0
			release.position = origin
			release.pressed = false
			root.push_input(release,true)
			holding = false
		return
	if not holding:
		var press := InputEventScreenTouch.new()
		press.index = 0
		press.position = origin
		press.pressed = true
		root.push_input(press,true)
		holding = true
	var drag := InputEventScreenDrag.new()
	drag.index = 0
	var right: Vector3 = world.camera.global_basis.x
	var near := right.cross(Vector3.UP)
	drag.position = origin + 82.0*Vector2(direction.dot(right),direction.dot(near)).limit_length()
	root.push_input(drag,true)

func approach(at: Vector3) -> void:
	for tick in ticks(10):
		await physics_frame
		var delta: Vector3 = at-world.actor.position
		delta.y = 0
		if delta.length()<.12: break
		drive(delta*1.15)
	drive(Vector3.ZERO)
	for tick in ticks(.25): await physics_frame

func _run() -> void:
	world = load("res://field_opening.tscn").instantiate()
	root.add_child(world)
	for tick in 8: await physics_frame
	var best := INF
	var row: Dictionary
	for entry in world.forest.records:
		var at: Vector3 = entry.transform.origin
		if entry.index < 0 or at.x >= -5.0 or at.z < 4: continue
		var d := at.distance_squared_to(world.actor.position)
		if d<best:
			best = d
			row = entry
	if row.is_empty():
		push_error("No batched pine in the western snowfield.")
		quit(1)
		return
	var target: Vector3 = row.transform.origin
	var approach_side: Vector3 = (world.actor.position-target).normalized()
	await approach(target+approach_side*2.52)
	for tick in ticks(7.0):
		await physics_frame
		if is_instance_valid(row.live) and row.live.phase in ["credited","ready_to_credit"]: break
	var tree = row.live
	var struck: bool = is_instance_valid(tree) and tree.strikes == 3
	var dropped := false
	for token in world.drops:
		var drop: Dictionary = world.drops[token]
		if drop.kind=="wood" and (drop.at as Vector3).distance_to(target)<.9: dropped = true
	await approach(target)
	var picked: bool = world.inventory.carried.wood>0
	await approach(Vector3(1.0,0,5.5))
	for tick in ticks(6): await physics_frame
	# One more real input movement lets the grove reconcile a regrown distant pine.
	await approach(Vector3(1.3,0,5.7))
	var restored := not is_instance_valid(row.live)
	print(JSON.stringify({"physics_hz":Engine.physics_ticks_per_second,"scene":"field_opening.tscn","addressable_grove_pines":world.forest.records.size(),"tested_at":str(target),"three_cutting_contacts":struck,"typed_loose_wood":dropped,"wood_on_back":picked,"unloaded_back_to_batch_after_regrow":restored}))
	world.queue_free()
	for tick in 12:
		OS.delay_msec(20)
		await process_frame
	quit(0 if struck and dropped and picked and restored else 1)
