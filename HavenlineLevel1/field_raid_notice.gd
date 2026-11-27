extends Control
## The warning always uses the same HUD space and remains readable while muted.
const Typeface = preload("res://assets/field_ui/type/BarlowSemiCondensed-SemiBold.ttf")
var panel := Panel.new()
var notice := Label.new()
var repair := Button.new()

func _ready() -> void:
	name = "CampRaidHUD"
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var style := StyleBoxFlat.new()
	style.bg_color = Color("#693633f2")
	style.border_color = Color("#e3b174")
	style.set_border_width_all(1)
	style.set_corner_radius_all(8)
	panel.add_theme_stylebox_override("panel", style)
	add_child(panel)
	notice.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	notice.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	notice.mouse_filter = Control.MOUSE_FILTER_IGNORE
	notice.add_theme_font_override("font", Typeface)
	notice.add_theme_font_size_override("font_size", 24)
	notice.modulate = Color("#fff2dd")
	panel.add_child(notice)
	panel.hide()
	repair.focus_mode = Control.FOCUS_NONE
	repair.add_theme_font_override("font", Typeface)
	repair.add_theme_font_size_override("font_size", 22)
	add_child(repair)
	repair.hide()
	get_viewport().size_changed.connect(_reflow)

func _reflow() -> void:
	var hud = get_parent()
	var safe: Rect2 = hud._safe_rect()
	var banner_width := minf(safe.size.x - 36., 300.)
	panel.size = Vector2(banner_width, 36.)
	var ticket_bottom: float = hud.objective.position.y + hud.objective.size.y
	panel.position = Vector2(safe.position.x, maxf(ticket_bottom + 61., safe.position.y + 177.))
	notice.size = panel.size
	repair.size = Vector2(minf(safe.size.x - 30., 304.), 44.)
	repair.position = Vector2(safe.get_center().x - repair.size.x * .5, safe.end.y - 151.)

func display(text: String, repair_text: String, can_repair: bool) -> void:
	if notice.text != text or repair.visible == repair_text.is_empty():
		_reflow()
	if notice.text != text:
		notice.text = text
	panel.visible = not text.is_empty()
	repair.text = repair_text
	repair.visible = not repair_text.is_empty()
	repair.disabled = not can_repair
