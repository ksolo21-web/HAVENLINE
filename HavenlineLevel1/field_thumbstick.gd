extends Control
## Track the game's existing movable touch origin. Pointer events keep going to the world.
const DRAG_LIMIT := 82.0
const DRAG_DISPLAY_SCALE := 0.52
const RING_RADIUS := 50.0
const THUMB_SHADOW_RADIUS := 21.0
# Allow for the displaced thumb, its one-pixel shadow offset and antialiasing.
const EDGE_MARGIN := DRAG_LIMIT * DRAG_DISPLAY_SCALE + THUMB_SHADOW_RADIUS + 2.0

var world
var offset := Vector2.ZERO
var resting:=true


func install(host) -> void:
	world = host
	name = "MovementThumbstick"
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	hide()


func _process(_delta: float) -> void:
	if not is_instance_valid(world) or not world.get("field_ready"):
		return
	if world.trial_camera.pinching:
		hide()
		return
	var hud=get_parent()
	if not hud.has_method("_safe_rect") or not world.field_ready or (world.camp_layout and world.camp_layout.active):
		hide()
		return
	var area: Rect2 = hud._safe_rect()
	if not area.has_area():
		hide()
		return
	var display_scale := minf(1.0, minf(area.size.x, area.size.y) / (2.0 * EDGE_MARGIN))
	scale = Vector2.ONE * display_scale
	var centers := area.grow(-EDGE_MARGIN * display_scale)
	if world.touch_id<0:
		if hud.camp_dock and not hud.camp_dock.tab.is_empty():
			hide()
			return
		var edge_x:=area.end.x-65. if world.access.values.right_stick else area.position.x+65.
		position=Vector2(edge_x,area.end.y-maxf(135.,hud.camp_dock.touch_height(area)+58.)).clamp(centers.position,centers.end)
		resting=true
		offset=Vector2.ZERO
		queue_redraw()
		show()
		return
	resting=false
	var offset_now: Vector2 = (world.touch_now - world.touch_origin).limit_length(DRAG_LIMIT) * DRAG_DISPLAY_SCALE
	if not visible or offset.distance_squared_to(offset_now) > .04:
		offset = offset_now
		queue_redraw()
	# Clamp only the visual center. The world keeps the original drag coordinates.
	position = world.touch_origin.clamp(centers.position, centers.end)
	show()


func _draw() -> void:
	var strength:=.68 if resting else 1.
	draw_circle(Vector2.ZERO,RING_RADIUS,Color(.29,.34,.43,.40*strength),true,-1,true)
	draw_arc(Vector2.ZERO,RING_RADIUS,0.,TAU,48,Color(.12,.16,.22,.44*strength),2.25,true)
	draw_arc(Vector2.ZERO,48.,0.,TAU,48,Color(.99,.96,.93,.68*strength),1.75,true)
	for i in 4:
		var dir:=Vector2.UP.rotated(i*PI*.5)
		var side:=dir.orthogonal()
		draw_colored_polygon(PackedVector2Array([dir*43.,dir*35.+side*5.,dir*35.-side*5.]),Color(1.,.98,.94,.80*strength))
	draw_circle(offset+Vector2(0,1),THUMB_SHADOW_RADIUS,Color(.12,.16,.22,.20),true,-1,true)
	draw_circle(offset,20.,Color(1.,.98,.94,.86*strength),true,-1,true)
