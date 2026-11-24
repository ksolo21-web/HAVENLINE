extends SceneTree
## Headless uses real theme/layout, labels and routed input; pixels and world
## occlusion need separate visual review on the exact candidate.
const Combined = preload("res://previews/integrated_opening.tscn")
const DefaultHUD = preload("res://opening_hud.gd")
var checks := 0
var failures := 0
var game

func _initialize() -> void:
	call_deferred("run")

func check(ok: bool, label: String) -> void:
	checks += 1
	if not ok:
		failures += 1
	print("%s %s" % ["PASS" if ok else "FAIL", label])

func touch(idx: int, at: Vector2, down: bool) -> InputEventScreenTouch:
	var event := InputEventScreenTouch.new()
	event.index = idx
	event.position = at
	event.pressed = down
	event.device = 1
	return event

func fits_label(button: Button, phrase: String) -> bool:
	button.text = phrase
	var font := button.get_theme_font("font")
	var size := button.get_theme_font_size("font_size")
	var measured := font.get_string_size(phrase, HORIZONTAL_ALIGNMENT_LEFT, -1, size)
	var minimum := button.get_theme_stylebox("normal").get_minimum_size()
	return measured.x <= button.size.x - minimum.x and font.get_height(size) <= button.size.y - minimum.y

func check_viewport(viewport: SubViewport, want: Vector2i) -> void:
	viewport.size = want
	await process_frame
	await process_frame
	var hud = game.opening_hud
	var visible := Rect2(Vector2.ZERO, Vector2(want))
	var center := Rect2(Vector2(want) * Vector2(.18, .20), Vector2(want) * Vector2(.64, .59))
	var label_prefix := "%sx%s " % [want.x, want.y]
	check(game.touch_id == -1, label_prefix + "resize released existing touch owner")
	check(hud.get_script() != DefaultHUD and hud.stock.get_theme_font_size("font_size") >= 19 and hud.prompt.get_theme_font_size("font_size") >= 19, label_prefix + "compact script and legible objective font")
	for region: Control in [hud.plate, hud.gate, hud.tree]:
		check(visible.encloses(region.get_global_rect()), label_prefix + "region inside viewport: " + str(region.get_global_rect()))
		check(not center.intersects(region.get_global_rect()), label_prefix + "region leaves central actor/map clear: " + str(region.get_global_rect()))
	check(hud.plate.size.x <= (420 if want.x >= 500 else 370), label_prefix + "bounded objective plate")
	check(hud.stock.mouse_filter == Control.MOUSE_FILTER_IGNORE and hud.prompt.mouse_filter == Control.MOUSE_FILTER_IGNORE and hud.plate.mouse_filter == Control.MOUSE_FILTER_IGNORE, label_prefix + "status overlays do not take pointer ownership")
	for status in ["Fell one tree (F), collect two pickups, then reach the build marker.", "Hearth paid once. Check the South and East passages."]:
		hud.show_status(3, status)
		await process_frame
		check(hud.prompt.get_visible_line_count() == hud.prompt.get_line_count() and hud.plate.get_global_rect().encloses(hud.prompt.get_global_rect()), label_prefix + "entire objective visible: " + status)
	hud.gate.show()
	hud.tree.show()
	check(hud.gate.size.y >= 48.0 and hud.tree.size.y >= 48.0 and not hud.gate.get_global_rect().intersects(hud.tree.get_global_rect()), label_prefix + "48 logical pixel minimum and separate targets")
	for gate_id in ["gate-south", "gate-east"]:
		for held in [false, true]:
			for open in [false, true]:
				var phrase: String = game.gate_action_label(gate_id, held, open)
				check(fits_label(hud.gate, phrase), label_prefix + "gate phrase fits: " + phrase)
	for strikes in range(4):
		var phrase: String = game.tree_action_label(strikes)
		check(fits_label(hud.tree, phrase), label_prefix + "tree phrase fits: " + phrase)
	var gate_center: Vector2 = hud.gate.get_global_rect().get_center()
	var tree_center: Vector2 = hud.tree.get_global_rect().get_center()
	check(game.touches_gate_button(gate_center) and not game.touches_tree_button(gate_center), label_prefix + "existing actual gate hit exclusive")
	check(game.touches_tree_button(tree_center) and not game.touches_gate_button(tree_center), label_prefix + "existing actual tree hit exclusive")
	var attempt_before: int = game.tree_input_sequence
	game._input(touch(3, tree_center, true))
	check(game.tree_input_sequence == attempt_before + 1 and game.touch_id == -1, label_prefix + "tree touch routed without stealing movement")
	game._input(touch(4, gate_center, true))
	check(game.touch_id == -1, label_prefix + "gate touch taken by existing control handler")
	hud.tree.hide()
	game._input(touch(5, tree_center, true))
	check(game.touch_id == 5, label_prefix + "hidden action has no hit rectangle")
	var previous_slot: Vector2 = hud.gate.position
	hud.tree.show()
	hud.reflow()
	check(hud.gate.position == previous_slot, label_prefix + "other target stays put across visibility and reflow")
	game.clear_touch()

func run() -> void:
	var sub := SubViewport.new()
	sub.size = Vector2i(1280, 720)
	root.add_child(sub)
	game = Combined.instantiate()
	sub.add_child(game)
	game.set_physics_process(false)
	await process_frame
	game._input(touch(1, Vector2(650, 375), true))
	check(game.bound and game.touch_id == 1, "combined preview bound, center is conventional movement input")
	await check_viewport(sub, Vector2i(1160, 720))
	game._input(touch(2, Vector2(600, 375), true))
	check(game.touch_id == 2, "normal movement owner captured before narrow resize")
	await check_viewport(sub, Vector2i(414, 720))
	print("compact HUD checks=", checks, " failures=", failures)
	quit(0 if failures == 0 else 1)
