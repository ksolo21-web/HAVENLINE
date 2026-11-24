extends "res://opening_hud.gd"
## Combined-preview only. Keep the inherited labels, buttons, styling and event
## ownership, but leave the scene's center free and reserve stable edge targets.
const EDGE := 14.0
const PADDING := 12.0
const ACTION_GAP := 8.0
const OBJECTIVE_MAX := 410.0
const OBJECTIVE_FRACTION := .87
const BUTTON_MAX := 238.0
const BUTTON_HEIGHT := 54.0

func reflow() -> void:
	var viewport_size := get_viewport_rect().size
	var rail_width := maxf(1.0, minf(OBJECTIVE_MAX, minf(viewport_size.x * OBJECTIVE_FRACTION, viewport_size.x - EDGE * 2.0)))
	var content_width := maxf(1.0, rail_width - PADDING * 2.0)
	stock.add_theme_font_size_override("font_size", 22)
	prompt.add_theme_font_size_override("font_size", 19)
	plate.position = Vector2(EDGE, EDGE)
	stock.position = plate.position + Vector2.ONE * PADDING
	stock.size = Vector2(content_width, 30.0)
	prompt.position = stock.position + Vector2(0.0, stock.size.y + 2.0)
	prompt.size = Vector2(content_width, 0.0)
	prompt.size.y = maxf(25.0, prompt.get_minimum_size().y)
	plate.size = Vector2(rail_width, prompt.position.y + prompt.size.y - EDGE + PADDING)

	var button_width := maxf(1.0, minf(BUTTON_MAX, viewport_size.x - EDGE * 2.0))
	var right := maxf(0.0, viewport_size.x - EDGE - button_width)
	var bottom := viewport_size.y - EDGE - BUTTON_HEIGHT
	for action: Button in [gate, tree]:
		action.add_theme_font_size_override("font_size", 20)
		action.size = Vector2(button_width, BUTTON_HEIGHT)
	var row_top := maxf(0.0, bottom - BUTTON_HEIGHT - ACTION_GAP)
	# Both slots are reserved even when invisible, so a held target will not move.
	gate.position = Vector2(right, row_top)
	tree.position = Vector2(right, maxf(0.0, bottom))
