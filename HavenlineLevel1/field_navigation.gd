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
	skin.bg_color = Color("#214359ee")
	skin.border_color = Color("#a3bbc1")
	skin.set_border_width_all(1)
	skin.set_corner_radius_all(18)
	skin.border_width_bottom = 2
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
	var ticket_bottom:float=hud.objective.position.y+hud.objective.size.y
	position=Vector2(roundf(safe.position.x),roundf(ticket_bottom+8.))

func _process(_dt: float) -> void:
	refresh()

func refresh() -> void:
	if not world.field_ready or (world.camp_layout and world.camp_layout.active) or world.closing or world.persist_blocked or world.player_hp<=0 or world.reset_time>0:
		hide()
		return
	var feet: Vector3 = world.actor.global_position
	var selected:Vector3=hud.camp_dock.tracked_point()
	if selected.is_finite():
		if feet.distance_to(selected)<1.65:
			hud.camp_dock.tracking=""
		else:
			var aim_at:=selected
			var distance:=feet.distance_to(selected)
			var from_inside:bool=world.field_env.is_inside_camp(feet)
			var to_inside:bool=world.camp_active and world.camp_layout.bounds().has_point(Vector2(selected.x,selected.z))
			if to_inside and not from_inside and route.update(world,Vector2(feet.x,feet.z)):
				aim_at=Vector3(route.direction_target.x,feet.y,route.direction_target.y)
				distance=route.distance
			elif from_inside and not to_inside:
				var shortest:=INF
				for gate in world.gates:
					if not gate.active:continue
					var gate_at:Vector3=gate.global_position
					var via:=feet.distance_to(gate_at)+gate_at.distance_to(selected)
					if via<shortest:
						shortest=via
						aim_at=gate_at
						distance=via
			elif from_inside and to_inside:
				aim_at=world.camp_layout.next_waypoint(feet,selected)
			var bearing:Vector2=world.camera.unproject_position(aim_at)-world.camera.unproject_position(feet)
			needle.rotation=bearing.angle()
			var caption:String=hud.camp_dock.tracking_name
			label.text="%s  %d m"%[caption,roundi(distance)]
			size.x=maxf(194.,label.get_theme_font("font").get_string_size(label.text,HORIZONTAL_ALIGNMENT_LEFT,-1,TYPE_SIZE).x+LABEL_LEFT+LABEL_RIGHT)
			label.size.x=size.x-LABEL_LEFT-LABEL_RIGHT
			label.accessibility_name=label.text
			reflow()
			show()
			return
	if world.field_env.is_inside_camp(feet):
		hide()
		return
	var flat := Vector2(feet.x,feet.z)
	if not route.update(world,flat):
		hide()
		return
	if not world.camp_active:
		var ticket=hud.ticket
		var hearth: Vector3=world.field_env.buy_anchor.global_position
		var direct_goal: bool=route.direction_target.distance_squared_to(Vector2(hearth.x,hearth.z))<.03
		# Near the first plot, its visible ticket already gives the same direct
		# bearing and distance. At range or around a lake, keep the route compass.
		if route.distance<9. and direct_goal and ticket.heading=="Build hearth" and not ticket.bearing.is_empty():
			if ticket.guide_supplies_bearing:
				ticket.guide_supplies_bearing=false
				hud.reflow()
			hide()
			return
		at_plot = route.distance < (2.05 if at_plot else 1.55)
		if at_plot:
			hide()
			return
	if hud.ticket.guide_supplies_bearing == world.camp_active:
		hud.ticket.guide_supplies_bearing=not world.camp_active
		hud.reflow()
	var aim := Vector3(route.direction_target.x,feet.y,route.direction_target.y)
	var camera: Camera3D = world.camera
	var angle := (camera.unproject_position(aim)-camera.unproject_position(feet)).angle()
	if absf(angle_difference(needle.rotation,angle))>.003: needle.rotation = angle
	var next_meters := maxi(1,roundi(route.distance))
	var next_name := "Camp gate" if world.camp_active else "Camp plot"
	var next_octant := posmod(roundi(angle/(PI/4.)),8)
	reflow()
	if destination!=next_name or meters!=next_meters:
		destination = next_name
		meters = next_meters
		label.text = "%s  %d m"%[destination,meters]
		octant = -1
	if octant!=next_octant:
		octant=next_octant
		label.accessibility_name = "%s, %d metres, %s on screen"%[destination,meters,OCTANTS[octant]]
	show()
