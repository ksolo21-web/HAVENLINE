extends Control
## The purchase ticket keeps the price vocabulary on the mat and on the HUD identical.
## Other hints remain ordinary, wrapping text (including save and quest recovery).
const TYPE = preload("res://assets/field_ui/type/BarlowSemiCondensed-SemiBold.ttf")
const INK := Color("#193851")
const TEAL := Color("#31596d")
const ATLAS = preload("res://assets/field_ui/camp_goods.png")
const TILE := 144
const CONVEYOR_MARK = preload("res://assets/conveyors/conveyor_mark.png")
const LINE_TITLES := ["Automate meal service","Connect storehouse supply"]
const ART := {
	"Build hearth": 0,
	"Expand camp": 1,
	"Expand east": 1,
	"Build storehouse": 2,
	"Reinforce storehouse": 12,
	"Advance storehouse": 13,
	"Build watchtower": 3,
	"Equip extra axes": 4,
	"Build cooker": 5,
	"Build saw bench": 6,
	"Build quarry drill": 7
}
var guide_supplies_bearing := false
const CAPTION_SIZE := 27
const COST_SIZE := 22
const PAD := 15.
var heading := ""
var bearing := ""
var costs: Array[Dictionary] = []
var icons := {}
var next_upgrade := ""
var remaining := RegEx.new()
var route := RegEx.new()
var fallback := false
var intro := 1.0
var intro_tween: Tween


func _init() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	remaining.compile(r"^(\d+) (wood|stone|meat|coal|slate|metal(?: ore)?)(?: left)?$")
	route.compile(r"\s*([→↘↓↙←↖↑↗]\s*\d+\s*m)\s*$")


func set_message(message: String, artwork: Dictionary) -> void:
	icons = artwork
	var raw := message.strip_edges()
	next_upgrade = ""
	var lines := raw.split("\n", false)
	if lines.size() == 2:
		if lines[1] == "Approach the plot to pay" or lines[1] == "Stand on this plot to pay":
			raw = lines[0]
		elif lines[1].begins_with("Stored · ") and lines[0].contains("Next: "):
			next_upgrade = lines[0].get_slice("Next: ", 1).trim_suffix(" on the nearby plot")
			raw = lines[1]
	var compass := route.search(raw)
	bearing = compass.get_string(1) if compass else ""
	if compass:
		raw = raw.substr(0, compass.get_start()).strip_edges()
	var parts := raw.split("·", false)
	var previous := heading
	heading = parts[0].strip_edges() if parts.size() else ""
	costs.clear()
	fallback = parts.size() < 2
	for index in range(1, parts.size()):
		var word := parts[index].strip_edges()
		if heading=="Rescue survivor":word=word.trim_suffix(" at the southwest plot")
		var entry := remaining.search(word)
		if not entry:
			fallback = true
			break
		costs.append(
			{"amount": entry.get_string(1), "kind": entry.get_string(2).trim_suffix(" ore")}
		)
	if fallback:
		heading = raw
		costs.clear()
	if previous != heading and not previous.is_empty() and not fallback:
		if intro_tween:
			intro_tween.kill()
		intro = 0.
		intro_tween = create_tween()
		intro_tween.tween_method(_reveal, 0., 1., .20).set_trans(Tween.TRANS_QUAD).set_ease(
			Tween.EASE_OUT
		)
	queue_redraw()


func _reveal(value: float) -> void:
	intro = value
	queue_redraw()


func text_width(value: String, points: int) -> float:
	return TYPE.get_string_size(value, HORIZONTAL_ALIGNMENT_LEFT, -1, points).x


func natural_width() -> float:
	var cost_width := 0.
	for item in costs:
		cost_width += 33. + text_width(item.amount, COST_SIZE) + 11.
	var illustration := art_width()
	var route_width := text_width(bearing, 19) + 18. if shows_bearing() else 0.
	return (
		illustration
		+ maxf(
			maxf(text_width(heading, CAPTION_SIZE) + route_width, cost_width),
			text_width(next_upgrade, 19) + 60.
		)
		+ PAD * 2.
	)


func art_width() -> float:
	return 65. if ART.has(heading) or heading in LINE_TITLES else 0.


func cost_positions(width: float) -> Array[Vector2]:
	var positions: Array[Vector2] = []
	var x := 0.
	var y := 39.
	var available := maxf(1., width - PAD * 2. - art_width())
	for item in costs:
		var cell_width := 33. + text_width(item.amount, COST_SIZE) + 11.
		if x > 0. and x + cell_width > available:
			x = 0.
			y += 29.
		positions.append(Vector2(PAD + art_width() + x, y))
		x += cell_width
	return positions


func content_height(width: float) -> float:
	var positions := cost_positions(width)
	var last_row := positions[-1].y if not positions.is_empty() else 39.
	return last_row + 31. + (26. if not next_upgrade.is_empty() else 0.)


func shows_bearing() -> bool:
	return not bearing.is_empty() and not (guide_supplies_bearing and heading == "Build hearth")


func _draw() -> void:
	if fallback:
		return
	var text_x := PAD + 5. * (1. - intro)
	var height := size.y
	if art_width()>0.:
		var art_rect:=Rect2(Vector2(4,2),Vector2(66,66))
		if heading in LINE_TITLES:
			draw_texture_rect(CONVEYOR_MARK,art_rect,false)
		else:
			var index: int = ART[heading]
			var region := Rect2((index % 4) * TILE, (index / 4) * TILE, TILE, TILE)
			draw_texture_rect_region(ATLAS, art_rect, region)
		draw_line(Vector2(72, 11), Vector2(72, height - 11), Color("#d6c9a4"), 1.5, true)
		text_x += 65.
	draw_string(
		TYPE, Vector2(text_x, 33.), heading, HORIZONTAL_ALIGNMENT_LEFT, -1, CAPTION_SIZE, INK
	)
	var positions := cost_positions(size.x)
	for index in costs.size():
		var item: Dictionary = costs[index]
		var pos := positions[index]
		draw_texture_rect(icons[item.kind], Rect2(pos + Vector2(0,-2), Vector2(31,28)), false)
		draw_string(TYPE, pos + Vector2(33,20), item.amount, HORIZONTAL_ALIGNMENT_LEFT, -1, COST_SIZE, TEAL)

	if not next_upgrade.is_empty():
		draw_string(
			TYPE,
			Vector2(text_x, height - 10),
			"Next · " + next_upgrade,
			HORIZONTAL_ALIGNMENT_LEFT,
			-1,
			19,
			TEAL
		)
	if shows_bearing():
		var w := text_width(bearing, 19)
		if size.x >= text_x + text_width(heading, CAPTION_SIZE) + w + PAD + 12.:
			draw_string(
				TYPE,
				Vector2(size.x - PAD - w, 31),
				bearing,
				HORIZONTAL_ALIGNMENT_LEFT,
				-1,
				19,
				TEAL
			)
		else:
			draw_string(
				TYPE,
				Vector2(size.x - PAD - w, height - 11),
				bearing,
				HORIZONTAL_ALIGNMENT_LEFT,
				-1,
				19,
				TEAL
			)
