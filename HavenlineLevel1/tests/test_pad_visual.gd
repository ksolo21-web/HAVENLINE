extends SceneTree
const Opening = preload("res://opening.tscn")
var failures := 0

func check(ok: bool, desc: String) -> void:
	if not ok:
		failures += 1
		push_error(desc)

func _initialize() -> void:
	if not OS.get_cmdline_user_args().is_empty():
		quit(2)
		return
	call_deferred("run")

func run() -> void:
	var game = Opening.instantiate()
	root.add_child(game)
	game.set_physics_process(false)
	var pad = game.purchase_pad_view
	if not pad.binding_ready:
		push_error("Exact V5 asset binding failed")
		quit(2)
		return
	var box: AABB = pad.fitted_bounds
	check(is_equal_approx(maxf(box.size.x, box.size.z), .80) and minf(box.size.x, box.size.z) > .75, "uniform horizontal fit")
	check(is_equal_approx(box.position.y, .008), "seat")
	check(Vector2(box.get_center().x, box.get_center().z).length() < .0001, "centered on original trigger")
	check(pad.position.is_equal_approx(Vector3(0, 0, 2.4)) and pad.find_children("*", "CollisionObject3D", true, false).is_empty(), "same seat has no collision")
	var action := pad.scene_view.get_node("Action") as Label3D
	var cost := pad.scene_view.get_node("Cost") as Label3D
	check(action != null and cost != null and action.text == "BUILD" and cost.text == "3 WOOD" and pad.scene_view.visible, "offer readout")
	game.actor.position = game.point(game.layout.pad_xz)
	game.fund_opening_receiver("center-hearth", "wood")
	check(game.ledger.stock.wood == 0 and game.ledger.receipt.is_empty() and pad.scene_view.visible, "insufficient does not hide")
	for id in ["wood-a", "wood-b", "wood-c"]:
		game._collect_wood_source(id)
	check(pad.scene_view.visible and game.ledger.stock.wood == 3, "adequate stock alone does not hide")
	game.fund_opening_receiver("center-hearth", "wood")
	check(game.ledger.stock.wood == 0 and not game.ledger.receipt.is_empty() and not pad.scene_view.visible, "published acceptance hides exact pad")
	game.fund_opening_receiver("center-hearth", "wood")
	check(game.ledger.stock.wood == 0 and not pad.scene_view.visible, "duplicate request has no transition")
	var restored = Opening.instantiate()
	root.add_child(restored)
	restored.set_physics_process(false)
	check(restored.ledger.restore(game.ledger.snapshot()), "restored specimen")
	restored.sync_progress_visuals()
	check(not restored.purchase_pad_view.scene_view.visible, "restored receipt hides pad")
	print(JSON.stringify({"failures":failures,"raw_box": str(pad.original_bounds),"fitted_box":str(box),"note":"fixture only, no ordinary input or rendered proof"}))
	quit(0 if failures == 0 else 1)
