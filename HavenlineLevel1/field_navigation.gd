extends Panel
## A fixed, touch-through compass. The arrow follows the actual camera projection, including
## pitch, fold/rotation and pinch zoom; the meter follows a legal route around the palisade.
const Route := preload("res://field_home_route.gd")
const TYPE := preload("res://assets/field_ui/type/BarlowSemiCondensed-SemiBold.ttf")
const POINTER := [Vector2(12,0),Vector2(-8,8),Vector2(-4,0),Vector2(-8,-8)]
const OCTANTS := ["right","lower right","down","lower left","left","upper left","up","upper right"]
const PANEL_HEIGHT := 47.0
const LABEL_LEFT := 49.0
const LABEL_RIGHT := 13.0
const TYPE_SIZE := 24
var route := Route.new()
var world
var hud
var needle := Polygon2D.new()
var label := Label.new()
var meters := -1
var destination := ""
var octant := -1
var at_plot := false

func install(host, owner_hud) -> void:
	world = host
	hud = owner_hud
	name = "HomeCompass"
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	focus_mode = Control.FOCUS_NONE
	# The covered and unfolded displays use the same logical font. Keep a stable
	# width for every bearing, including the full unit after four-digit distances.
	var longest := 0.
	for title: String in ["Camp gate", "Camp plot"]:
		for digit in 10:
			var example := "%s  %s m" % [title,str(digit).repeat(4)]
			longest = maxf(longest,TYPE.get_string_size(example,HORIZONTAL_ALIGNMENT_LEFT,-1,TYPE_SIZE).x)
	size = Vector2(LABEL_LEFT+ceilf(longest)+LABEL_RIGHT,PANEL_HEIGHT)
	var skin := StyleBoxFlat.new()
	skin.bg_color = Color("#15314af5")
	skin.border_color = Color("#7798a9")
	skin.set_border_width_all(1)
	skin.set_corner_radius_all(16)
	add_theme_stylebox_override("panel",skin)
	needle.polygon = POINTER
	needle.color = Color("#ffcf80")
	needle.position = Vector2(25,23.5)
	add_child(needle)
	label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	label.add_theme_font_override("font",TYPE)
	label.add_theme_font_size_override("font_size",TYPE_SIZE)
	label.add_theme_color_override("font_color",Color("#f5f6ed"))
	label.position = Vector2(LABEL_LEFT,0)
	label.size = Vector2(size.x-LABEL_LEFT-LABEL_RIGHT,size.y)
	label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	add_child(label)
	hide()
	get_viewport().size_changed.connect(reflow)
	reflow()

func _draw() -> void:
	draw_circle(Vector2(25,23.5),16.,Color("#233f53"),true,-1,true)
	draw_arc(Vector2(25,23.5),16.,0.,TAU,40,Color("#8da9ad"),1.,true)

func reflow() -> void:
	var safe: Rect2 = hud._safe_rect()
	position = Vector2(roundf(safe.get_center().x-size.x*.5),roundf(safe.end.y-size.y-2))

func _process(_dt: float) -> void:
	refresh()

func refresh() -> void:
	if not world.field_ready or world.closing or world.persist_blocked or world.player_hp<=0 or world.reset_time>0:
		hide()
		return
	var feet: Vector3 = world.actor.global_position
	if world.field_env.is_inside_camp(feet):
		hide()
		return
	var flat := Vector2(feet.x,feet.z)
	if not route.update(world,flat):
		hide()
		return
	if not world.camp_active:
		at_plot = route.distance < (2.05 if at_plot else 1.55)
		if at_plot:
			hide()
			return
	var aim := Vector3(route.direction_target.x,feet.y,route.direction_target.y)
	var camera: Camera3D = world.camera
	var angle := (camera.unproject_position(aim)-camera.unproject_position(feet)).angle()
	if absf(angle_difference(needle.rotation,angle))>.003: needle.rotation = angle
	var next_meters := maxi(1,roundi(route.distance))
	var next_name := "Camp gate" if world.camp_active else "Camp plot"
	var next_octant := posmod(roundi(angle/(PI/4.)),8)
	if destination!=next_name or meters!=next_meters:
		destination = next_name
		meters = next_meters
		label.text = "%s  %d m"%[destination,meters]
		octant = -1
	if octant!=next_octant:
		octant=next_octant
		label.accessibility_name = "%s, %d metres, %s on screen"%[destination,meters,OCTANTS[octant]]
	show()
