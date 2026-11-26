extends "res://opening_hud.gd"

const EDGE := 16.0
const PAD := 12.0
const MAX_WIDTH := 308.0

func _ready() -> void:
	super()
	stock.add_theme_font_size_override("font_size", 20)
	prompt.add_theme_font_size_override("font_size", 18)
	for action: Button in [gate, tree]:
		action.add_theme_font_size_override("font_size", 20)
	reflow()

func reflow() -> void:
	var available := maxf(1.0, get_viewport_rect().size.x - 2.0 * EDGE)
	var stock_width := stock.get_theme_font("font").get_string_size(stock.text, HORIZONTAL_ALIGNMENT_LEFT, -1, stock.get_theme_font_size("font_size")).x
	var hint_width := prompt.get_theme_font("font").get_string_size(prompt.text, HORIZONTAL_ALIGNMENT_LEFT, -1, prompt.get_theme_font_size("font_size")).x
	var width := minf(available, minf(MAX_WIDTH, ceilf(maxf(stock_width, hint_width)) + 2.0 * PAD + 2.0))
	var inner_width := maxf(1.0, width - 2.0 * PAD)
	plate.position = Vector2(EDGE, EDGE)
	stock.position = plate.position + Vector2(PAD, 8)
	stock.size = Vector2(inner_width, stock.get_minimum_size().y)
	prompt.position = Vector2(stock.position.x, stock.position.y + stock.size.y + 2)
	prompt.size = Vector2(inner_width, 0)
	prompt.size.y = prompt.get_minimum_size().y
	plate.size = Vector2(width, prompt.position.y + prompt.size.y + 10 - plate.position.y)
	var action_width := minf(available, MAX_WIDTH)
	gate.position = Vector2(EDGE, EDGE + plate.size.y + 8)
	gate.size = Vector2(action_width, 56)
	tree.position = gate.position + Vector2(0, gate.size.y + 8)
	tree.size = gate.size
