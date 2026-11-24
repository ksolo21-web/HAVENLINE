extends Control
## Visual-only canvas rail. All button intent stays with Opening._input.
const MARGIN := 22.0
const INSET := 18.0
const GUTTER := 12.0
const ACTION_HEIGHT := 96.0

var stock: Label
var prompt: Label
var gate: Button
var tree: Button
var plate: Panel

func _ready() -> void:
	name = "OpeningResponsiveHUD"
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	plate = Panel.new()
	plate.mouse_filter = Control.MOUSE_FILTER_IGNORE
	plate.add_theme_stylebox_override("panel", _plate_style(Color("#14283c"), Color("#5781a0")))
	add_child(plate)
	stock = _text_line(36, Color("#fff3d2"))
	prompt = _text_line(32, Color("#e7f3ff"))
	prompt.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	gate = _button()
	tree = _button()
	reflow()

func _plate_style(fill: Color, outline: Color) -> StyleBoxFlat:
	var style := StyleBoxFlat.new()
	style.bg_color = fill
	style.border_color = outline
	style.set_border_width_all(2)
	style.set_corner_radius_all(16)
	style.content_margin_left = INSET
	style.content_margin_right = INSET
	return style

func _text_line(font_size: int, tint: Color) -> Label:
	var label := Label.new()
	label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	label.add_theme_font_size_override("font_size", font_size)
	label.add_theme_color_override("font_color", tint)
	add_child(label)
	return label

func _button() -> Button:
	var button := Button.new()
	button.mouse_filter = Control.MOUSE_FILTER_IGNORE
	button.focus_mode = Control.FOCUS_NONE
	button.clip_text = true
	button.add_theme_font_size_override("font_size", 33)
	button.add_theme_color_override("font_color", Color("#fff8e9"))
	button.add_theme_stylebox_override("normal", _plate_style(Color("#264662"), Color("#86b5cc")))
	add_child(button)
	button.hide()
	return button

func show_status(wood: int, message: String) -> void:
	stock.text = "Wood: %d" % wood
	prompt.text = message
	reflow()

func reflow() -> void:
	# Visible rect is expressed in the same logical canvas as Opening._input.
	# Keep the status rail and both action slots inside the viewport with a
	# permanent gutter. Reserving action slots avoids moving a held target.
	var viewport_size := get_viewport_rect().size
	var rail_width := minf(880.0, maxf(1.0, viewport_size.x - 2.0 * MARGIN))
	var content_width := maxf(1.0, rail_width - 2.0 * INSET)
	plate.position = Vector2(MARGIN, MARGIN)
	stock.position = Vector2(MARGIN + INSET, MARGIN + INSET)
	stock.size = Vector2(content_width, 46.0)
	prompt.position = Vector2(MARGIN + INSET, stock.position.y + stock.size.y + 4.0)
	prompt.size = Vector2(content_width, 0.0)
	prompt.size.y = maxf(43.0, prompt.get_minimum_size().y)
	plate.size = Vector2(rail_width, prompt.position.y + prompt.size.y + INSET - MARGIN)
	var action_top := MARGIN + plate.size.y + GUTTER
	gate.position = Vector2(MARGIN, action_top)
	gate.size = Vector2(rail_width, ACTION_HEIGHT)
	tree.position = Vector2(MARGIN, action_top + gate.size.y + GUTTER)
	tree.size = Vector2(rail_width, ACTION_HEIGHT)
