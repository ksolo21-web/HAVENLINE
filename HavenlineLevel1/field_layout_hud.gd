extends Control
## A camp-wide isometric edit view. Outlined tiles show the building, dashed
## amber edges show the loading/upgrade surfaces which must stay accessible.
const TYPE = preload("res://assets/field_ui/type/BarlowSemiCondensed-SemiBold.ttf")
const INK := Color("#193b50")
const IVORY := Color("#fcf3dc")
const GOLD := Color("#dfb569")
const GREEN := Color("#58cd9a")
const RED := Color("#e87566")
var layout
var launcher := Button.new()
var done := Button.new()
var back := Button.new()
var place := Button.new()
var caption := Label.new()
var hint := Label.new()
var tray := Panel.new()
var rail := Panel.new()

func _skin(fill:Color, rim:Color, curve:int) -> StyleBoxFlat:
	var face:=StyleBoxFlat.new()
	face.bg_color=fill
	face.border_color=rim
	face.set_border_width_all(2)
	face.border_width_bottom=3
	face.set_corner_radius_all(curve)
	face.shadow_color=Color("#152a3c50")
	face.shadow_offset=Vector2(0,2)
	face.shadow_size=3
	return face

func _button(node:Button,title:String,primary:=false) -> void:
	node.text=title
	node.focus_mode=Control.FOCUS_NONE
	node.mouse_filter=Control.MOUSE_FILTER_IGNORE
	node.add_theme_font_override("font",TYPE)
	node.add_theme_font_size_override("font_size",25)
	var fill:=Color("#237857") if primary else INK
	for state:String in ["normal","hover","pressed","disabled"]:
		var face:=_skin(fill if state!="disabled" else Color("#727f84"),Color("#c6d6cf"),15)
		node.add_theme_stylebox_override(state,face)
	node.add_theme_color_override("font_color",IVORY)
	node.add_theme_color_override("font_disabled_color",Color("#efeee4"))
	add_child(node)

func install(host) -> void:
	layout=host
	name="CampLayoutControls"
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter=Control.MOUSE_FILTER_IGNORE
	for panel in [rail,tray]:
		panel.mouse_filter=Control.MOUSE_FILTER_IGNORE
		add_child(panel)
		panel.add_theme_stylebox_override("panel",_skin(INK if panel==rail else IVORY,GOLD,15))
	for label:Label in [caption,hint]:
		add_child(label)
		label.mouse_filter=Control.MOUSE_FILTER_IGNORE
		label.add_theme_font_override("font",TYPE)
		label.add_theme_font_size_override("font_size",29 if label==caption else 23)
		label.add_theme_color_override("font_color",IVORY if label==caption else INK)
		label.vertical_alignment=VERTICAL_ALIGNMENT_CENTER
	_button(launcher,"Move")
	launcher.accessibility_name="Move camp equipment"
	launcher.tooltip_text="Move camp equipment (M)"
	_button(done,"Done")
	_button(back,"Reselect")
	_button(place,"Place here",true)
	resized.connect(sync)
	sync()

func _process(_dt:float) -> void:
	if not layout or not layout.world.field_ready: return
	var available:bool=layout.world.camp_active and not layout.world.persist_blocked and layout.world.reset_time<=0
	if layout.active and not available:
		layout.close()
		return
	if launcher.visible:launcher.hide()
	if layout.active: queue_redraw()

func sync() -> void:
	if not layout or not layout.world: return
	var active:bool=layout.active
	var host=layout.world
	var safe:Rect2=host.opening_hud._safe_rect()
	launcher.hide()
	var target: float=host.opening_hud.min_touch_canvas()
	launcher.size=Vector2(maxf(93.,target),maxf(50.,target))
	var continued:bool = host.opening_hud.level_continue and host.opening_hud.level_continue.visible
	launcher.position=Vector2(safe.end.x-launcher.size.x,safe.end.y-(225. if continued else 131.))
	for node in [done,rail,caption,tray,hint]: node.visible=active
	var selected:bool=active and not layout.chosen.is_empty()
	back.visible=selected
	place.visible=selected and layout.preview_set
	place.disabled=not layout.candidate_reason.is_empty()
	if not active:
		queue_redraw()
		return
	rail.position=safe.position
	caption.text=layout.NAMES[layout.chosen] if selected else "Camp layout"
	rail.size=Vector2(maxf(163.,caption.get_minimum_size().x+30.),55.)
	caption.position=rail.position+Vector2(15,0)
	caption.size=rail.size-Vector2(30,0)
	done.size=Vector2(maxf(88.,target),maxf(53.,target))
	done.position=Vector2(safe.end.x-done.size.x,safe.position.y)
	var label:="Select a building to move"
	if selected:
		label="Tap or drag to a new spot"
		if layout.chosen==layout.COUNTER: label="Choose a spot on the north fence"
		if layout.preview_set:
			label="Ready to place" if layout.candidate_reason.is_empty() else layout.candidate_reason
	hint.text=label
	hint.add_theme_color_override("font_color",Color("#9a3e2d") if layout.preview_set and not layout.candidate_reason.is_empty() else INK)
	back.size=Vector2(maxf(111.,target),maxf(54.,target))
	place.size=Vector2(maxf(135.,target),maxf(54.,target))
	place.position=Vector2(safe.end.x-place.size.x,safe.end.y-place.size.y)
	back.position=Vector2((place.position.x-10. if place.visible else safe.end.x)-back.size.x,safe.end.y-back.size.y)
	var room:float=back.position.x-safe.position.x-16. if selected else safe.size.x
	var w:=minf(hint.get_minimum_size().x+32.,safe.size.x)
	var extra:=back.size.y+10. if room<w else 0.
	tray.size=Vector2(w,52)
	tray.position=Vector2(safe.position.x,safe.end.y-tray.size.y-extra)
	hint.position=tray.position+Vector2(16,0)
	hint.size=tray.size-Vector2(32,0)
	queue_redraw()

func _poly(points:PackedVector2Array, y:float) -> PackedVector2Array:
	var result:=PackedVector2Array()
	for p:Vector2 in points:
		result.append(layout.map_camera.unproject_position(Vector3(p.x,y,p.y)))
	return result

func _tile(outline:PackedVector2Array,col:Color,fill:float,dash:bool=false) -> void:
	var polygon:=_poly(outline,.062)
	draw_colored_polygon(polygon,Color(col,fill))
	for i in polygon.size():
		if dash: draw_dashed_line(polygon[i],polygon[(i+1)%polygon.size()],col,2.4,8.,true,true)
		else:
			draw_line(polygon[i],polygon[(i+1)%polygon.size()],Color("#182e3eaf"),5.,true)
			draw_line(polygon[i],polygon[(i+1)%polygon.size()],col,2.6,true)

func _draw() -> void:
	if not layout or not layout.active: return
	for id:String in layout.NAMES:
		if not layout.owned(id): continue
		var center:Vector2=layout.center(id)
		var col:=Color("#ffeab3") if layout.chosen==id else Color("#f3e2a6a5")
		_tile(layout.footprint_outline(id,center),col,.06)
	if layout.chosen.is_empty(): return
	var point:Vector2=layout.candidate if layout.preview_set else layout.center(layout.chosen)
	var col:=GREEN if layout.candidate_reason.is_empty() else RED
	for space:Rect2 in layout.service_areas(layout.chosen,point): _tile(layout.corners(space),GOLD,.14,true)
	_tile(layout.footprint_outline(layout.chosen,point),col,.34)
