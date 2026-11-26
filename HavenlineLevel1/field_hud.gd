extends "res://orbit_hud.gd"

const Ledger = preload("res://field_inventory.gd")
const MATERIAL_ICONS := {
	"wood": preload("res://assets/field_ui/wood.png"),
	"stone": preload("res://assets/field_ui/stone.png"),
	"meat": preload("res://assets/field_ui/meat.png"),
	"coal": preload("res://assets/field_ui/coal.png"),
	"slate": preload("res://assets/field_ui/slate.png"),
	"metal": preload("res://assets/field_ui/metal.png"),
}
var row: HBoxContainer
var mineral_row: HBoxContainer
var numbers := {}
var health_bar := ProgressBar.new()
var health_trail := ProgressBar.new()
var health_text: Label
var health_fill := StyleBoxFlat.new()
var health_tween: Tween
var shown_hp := -1

func _bar_skin(color: Color) -> StyleBoxFlat:
	var skin := StyleBoxFlat.new()
	skin.bg_color = color
	skin.set_corner_radius_all(4)
	return skin

func set_health(amount: int, maximum: int) -> void:
	if not health_text or amount == shown_hp: return
	var previous := shown_hp
	shown_hp = amount
	health_text.text = "HP  %d / %d" % [amount,maximum]
	for bar in [health_bar,health_trail]: bar.max_value = maximum
	if health_tween: health_tween.kill()
	health_bar.value = amount
	health_fill.bg_color = Color("#fb785d") if amount*2 <= maximum else Color("#79e2a2")
	if previous > amount:
		health_trail.value = maxf(previous,health_trail.value)
		health_tween = create_tween()
		health_tween.tween_interval(.13)
		health_tween.tween_property(health_trail,"value",float(amount),.34)
	else:
		health_trail.value = amount

func _ready() -> void:
	super()
	stock.hide()
	row = HBoxContainer.new()
	row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	row.add_theme_constant_override("separation",5)
	add_child(row)
	for kind: String in Ledger.ORIGINAL_KINDS:
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
	mineral_row = HBoxContainer.new()
	mineral_row.name = "CarriedMinerals"
	mineral_row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	mineral_row.add_theme_constant_override("separation",6)
	add_child(mineral_row)
	for kind: String in Ledger.MINERALS:
		var cell := HBoxContainer.new()
		cell.add_theme_constant_override("separation",2)
		mineral_row.add_child(cell)
		var icon := TextureRect.new()
		icon.texture=MATERIAL_ICONS[kind]
		icon.expand_mode=TextureRect.EXPAND_IGNORE_SIZE
		icon.stretch_mode=TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		icon.custom_minimum_size=Vector2(24,24)
		icon.mouse_filter=Control.MOUSE_FILTER_IGNORE
		cell.add_child(icon)
		var details := VBoxContainer.new()
		details.add_theme_constant_override("separation",-3)
		cell.add_child(details)
		var title := Label.new()
		title.text=Ledger.TITLES[kind]
		title.add_theme_font_size_override("font_size",13)
		title.add_theme_color_override("font_color",Color("cad7e1"))
		details.add_child(title)
		var number := Label.new()
		number.text="0"
		number.add_theme_font_size_override("font_size",16)
		number.add_theme_color_override("font_color",Color("fff0ca"))
		details.add_child(number)
		numbers[kind]=number
	mineral_row.hide()
	health_text = _text_line(16,Color("#edf4f7"))
	health_trail.name = "HealthLost"
	health_bar.name = "PlayerHealth"
	for bar in [health_trail,health_bar]:
		bar.mouse_filter = Control.MOUSE_FILTER_IGNORE
		bar.show_percentage = false
		bar.step = 0
		add_child(bar)
	health_trail.add_theme_stylebox_override("background",_bar_skin(Color("#0b1926")))
	health_trail.add_theme_stylebox_override("fill",_bar_skin(Color("#ffce86")))
	health_bar.add_theme_stylebox_override("background",StyleBoxEmpty.new())
	health_fill.set_corner_radius_all(4)
	health_bar.add_theme_stylebox_override("fill",health_fill)
	prompt.add_theme_font_size_override("font_size",17)
	reflow()

func field_status(counts: Dictionary, message: String) -> void:
	for kind in numbers:
		numbers[kind].text = str(counts.get(kind,0))
	mineral_row.visible = Ledger.MINERALS.any(func(kind):return counts.get(kind,0)>0)
	prompt.text = message
	reflow()

func reflow() -> void:
	if not row:
		super()
		return
	var rack_size := row.get_combined_minimum_size()
	var minerals_size := mineral_row.get_combined_minimum_size() if mineral_row.visible else Vector2.ZERO
	var desired_width := maxf(296.,maxf(rack_size.x+20.,minerals_size.x+24.))
	var width := minf(desired_width,get_viewport_rect().size.x-2.0*EDGE)
	plate.position = Vector2(EDGE,EDGE)
	row.position = plate.position+Vector2(10,5)
	row.size = rack_size
	row.scale = Vector2.ONE*minf(1.,(width-20.)/maxf(1.,rack_size.x))
	var mineral_height := 0.
	if mineral_row.visible:
		mineral_row.position=plate.position+Vector2(12,36)
		mineral_row.size=minerals_size
		mineral_row.scale=Vector2.ONE*minf(1.,(width-24.)/maxf(1.,minerals_size.x))
		mineral_height=minerals_size.y*mineral_row.scale.y+2.
	health_text.position = plate.position+Vector2(12,36+mineral_height)
	for bar in [health_bar,health_trail]:
		bar.position = plate.position+Vector2(89,44+mineral_height)
		bar.size = Vector2(maxf(8,width-105),9)
	prompt.position = plate.position+Vector2(12,61+mineral_height)
	prompt.size = Vector2(width-24,0)
	prompt.size.y = prompt.get_minimum_size().y
	plate.size = Vector2(width,67+mineral_height+prompt.size.y)
	gate.position = Vector2(EDGE,EDGE+plate.size.y+7)
	gate.size = Vector2(minf(width,208),46)
	tree.position = gate.position+Vector2(0,50)
	tree.size = gate.size
