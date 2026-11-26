extends "res://orbit_hud.gd"

const MATERIAL_ICONS := {
	"wood": preload("res://assets/field_ui/wood.png"),
	"stone": preload("res://assets/field_ui/stone.png"),
	"meat": preload("res://assets/field_ui/meat.png"),
}
var row: HBoxContainer
var numbers := {}

func _ready() -> void:
	super()
	stock.hide()
	row = HBoxContainer.new()
	row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	row.add_theme_constant_override("separation",5)
	add_child(row)
	for kind: String in MATERIAL_ICONS:
		var icon := TextureRect.new()
		icon.texture = MATERIAL_ICONS[kind]
		icon.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		icon.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		icon.custom_minimum_size = Vector2(32,30)
		icon.mouse_filter = Control.MOUSE_FILTER_IGNORE
		row.add_child(icon)
		var count := Label.new()
		count.text = "0"
		count.add_theme_color_override("font_color",Color("fff0ca"))
		count.add_theme_font_size_override("font_size",21)
		count.custom_minimum_size.x = 26
		row.add_child(count)
		numbers[kind] = count
	prompt.add_theme_font_size_override("font_size",17)
	reflow()

func field_status(counts: Dictionary, message: String) -> void:
	for kind in numbers:
		numbers[kind].text = str(counts[kind])
	prompt.text = message
	reflow()

func reflow() -> void:
	if not row:
		super()
		return
	var width := minf(296.0,get_viewport_rect().size.x-2.0*EDGE)
	plate.position = Vector2(EDGE,EDGE)
	row.position = plate.position+Vector2(10,5)
	row.size = row.get_combined_minimum_size()
	prompt.position = plate.position+Vector2(12,38)
	prompt.size = Vector2(width-24,0)
	prompt.size.y = prompt.get_minimum_size().y
	plate.size = Vector2(width,43+prompt.size.y)
	gate.position = Vector2(EDGE,EDGE+plate.size.y+7)
	gate.size = Vector2(minf(width,208),46)
	tree.position = gate.position+Vector2(0,50)
	tree.size = gate.size
