extends SceneTree

const Hud := preload("res://opening_hud.gd")
const Opening := preload("res://opening.tscn")
var failures := 0

func _initialize() -> void:
	call_deferred("_run")

func check(ok: bool, message: String) -> void:
	if not ok:
		failures += 1
		push_error(message)

func touch(index: int, at: Vector2, pressed: bool) -> InputEventScreenTouch:
	var e := InputEventScreenTouch.new()
	e.index = index
	e.position = at
	e.pressed = pressed
	return e

func _run() -> void:
	var sub := SubViewport.new()
	root.add_child(sub)
	var rail := Hud.new()
	sub.add_child(rail)
	rail.gate.text = "Exit swing area south [E]"
	rail.tree.text = "Strike wood-a [F] (2/3)"
	rail.show_status(3, "Fell one tree (F), collect two pickups, then reach the build marker.")
	for dims in [Vector2i(414, 896), Vector2i(600, 900), Vector2i(1280, 720), Vector2i(1920, 1080)]:
		sub.size = dims
		await process_frame
		rail.reflow()
		await process_frame
		rail.reflow()
		var page := Rect2(Vector2.ZERO, Vector2(dims))
		var plate_rect := rail.plate.get_global_rect()
		var g := rail.gate.get_global_rect()
		var t := rail.tree.get_global_rect()
		check(page.encloses(plate_rect) and page.encloses(g) and page.encloses(t), "layout escaped %s" % str(dims))
		check(plate_rect.encloses(rail.stock.get_global_rect()) and plate_rect.encloses(rail.prompt.get_global_rect()), "text escaped plate %s" % str(dims))
		check(not plate_rect.intersects(g) and not g.intersects(t), "overlap %s" % str(dims))
		check(g.size.y >= 96.0 and t.size.y >= 96.0, "logical action strip height under target")
		check(rail.prompt.get_line_count() == rail.prompt.get_visible_line_count(), "prompt clipped")
		if dims.x < 500:
			check(rail.prompt.get_line_count() > 1, "synthetic compact viewport did not wrap")
	sub.queue_free()

	var game = Opening.instantiate()
	root.add_child(game)
	game.set_physics_process(false)
	game.gate_button.show()
	game.tree_button.show()
	var g: Vector2 = game.gate_button.get_global_rect().get_center()
	var t: Vector2 = game.tree_button.get_global_rect().get_center()
	check(game.touches_gate_button(g) and not game.touches_tree_button(g), "gate rect not unique")
	check(game.touches_tree_button(t) and not game.touches_gate_button(t), "tree rect not unique")
	game._input(touch(1, game.get_viewport().get_visible_rect().size - Vector2(10, 10), true))
	check(game.touch_id == 1, "outside press did not start normal owner touch")
	game._input(touch(2, g, true))
	game._input(touch(2, g, false))
	check(game.touch_id == 1, "side control changed existing owner")
	game._input(touch(3, t, true))
	game._input(touch(3, t, false))
	check(game.touch_id == 1, "tree press changed existing owner")
	game._input(touch(1, t, false))
	check(game.touch_id == -1, "actual owner release over rail did not clear")
	game.gate_button.hide()
	game._input(touch(4, g, true))
	check(game.touch_id == 4 and not game.touches_gate_button(g), "hidden slot intercepted/claimed target")
	game.clear_touch()
	print("HUD fixture failures: ", failures)
	quit(1 if failures else 0)
