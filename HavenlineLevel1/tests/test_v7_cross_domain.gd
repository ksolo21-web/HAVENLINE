extends SceneTree
const Opening = preload("res://opening.tscn")
const ResourceTreeScript = preload("res://resource_tree.gd")
const SAFE := Vector3(-.52, 0, 6)
var checks := 0
var failures := 0

func _initialize() -> void:
	if not OS.get_cmdline_user_args().is_empty():
		push_error("Cross-domain fixture must run without profile arguments")
		quit(2)
		return
	call_deferred("run")

func check(value: bool, label: String) -> void:
	checks += 1
	if not value:
		failures += 1
		push_error(label)

func touch(game, at: Vector2, device_id: int) -> void:
	var event := InputEventScreenTouch.new()
	event.position = at
	event.index = 12
	event.pressed = true
	event.device = device_id
	game._input(event)

func click(game, at: Vector2, device_id: int) -> void:
	var event := InputEventMouseButton.new()
	event.position = at
	event.button_index = MOUSE_BUTTON_LEFT
	event.pressed = true
	event.device = device_id
	game._input(event)

func run() -> void:
	var game = Opening.instantiate()
	root.add_child(game)
	game.set_physics_process(false)
	var pad = game.purchase_pad_view
	if not pad.binding_ready:
		push_error("exact imported pad unavailable")
		quit(2)
		return
	var tree: ResourceTreeScript = game.resource_tree
	var south = game.gates[0]
	var east = game.gates[1]
	game.actor.position = SAFE
	check(not south.active and not east.active and pad.scene_view.visible, "fresh pad offered, gates not earned")
	game._collect_wood_source("wood-b")
	game._collect_wood_source("wood-c")
	for seq in range(1, 4):
		check(tree.strike("wood-a", seq, SAFE, Vector3.LEFT), "deliberate valid tree contact")
		if seq < 3:
			for step in 10:
				game.step_tree(.04)
			check(game.ledger.stock.wood == 2 and pad.scene_view.visible, "first two strikes do not change available stock or hide pad")
	for tick in 60:
		if tree.falling_clock >= ResourceTreeScript.FALL_SECONDS:
			break
		game.step_tree(.04)
		if tree.blocked:
			push_error("fixture safe stance is blocked")
			quit(2)
			return
	check(tree.falling_clock >= ResourceTreeScript.FALL_SECONDS and is_zero_approx(tree.settle_clock) and game.ledger.stock.wood == 2, "terminal mesh pose is not payment")
	game.actor.position = game.point(game.layout.pad_xz)
	game.fund_opening_receiver("center-hearth", "wood")
	check(game.ledger.receipt.is_empty() and pad.scene_view.visible and not south.active, "premature payment remains unavailable")
	game.actor.position = SAFE
	for step in 12:
		game.step_tree(.04)
	check(game.ledger.stock.wood == 3 and tree.phase == "credited" and pad.scene_view.visible, "settled credit alone does not hide offered pad")
	game.actor.position = game.point(game.layout.pad_xz)
	game.fund_opening_receiver("center-hearth", "wood")
	check(game.ledger.stock.wood == 0 and not pad.scene_view.visible and south.active and east.active, "published payment drives pad hide and earned gates")
	check(not south.target_open and not east.target_open, "newly earned gates closed")
	game.actor.position = Vector3(0, 0, 5.3)
	game.nearest_gate = south
	game.gate_button.position = Vector2(20, 20)
	game.tree_button.position = Vector2(20, 20)
	game.gate_button.size = Vector2(200, 50)
	game.tree_button.size = Vector2(200, 50)
	game.gate_button.show()
	game.tree_button.show()
	var at := Vector2(45, 38)
	var prev: int = game.tree_input_sequence
	click(game, at, 3)
	check(south.target_open and not east.target_open and game.tree_input_sequence == prev, "overlap real mouse routes gate first")
	touch(game, at, 2)
	check(south.target_open and game.tree_input_sequence == prev + 1, "overlap real touch routes tree first")
	click(game, at, InputEvent.DEVICE_ID_EMULATION)
	touch(game, at, InputEvent.DEVICE_ID_EMULATION)
	check(south.target_open and game.tree_input_sequence == prev + 1 and game.touch_id == -1, "tagged mirrors on overlap activate neither action nor stick")
	check(game.ledger.stock.wood == 0 and not pad.scene_view.visible, "pointer actions cannot regrant stock or rearm pad")
	print("V7 cross-domain checks: ", checks, ", failures: ", failures)
	quit(0 if failures == 0 else 1)
