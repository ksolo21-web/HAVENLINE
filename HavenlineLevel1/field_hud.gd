extends "res://orbit_hud.gd"

const Ledger = preload("res://field_inventory.gd")
const FACE = preload("res://assets/field_ui/character1_portrait.png")
const FRAME = preload("res://assets/field_ui/portrait_medallion.gdshader")
const TYPE = preload("res://assets/field_ui/type/BarlowSemiCondensed-SemiBold.ttf")
const MATERIAL_ICONS := {
	"wood": preload("res://assets/field_ui/wood.png"),
	"stone": preload("res://assets/field_ui/stone.png"),
	"meat": preload("res://assets/field_ui/meat.png"),
	"coal": preload("res://assets/field_ui/coal.png"),
	"slate": preload("res://assets/field_ui/slate.png"),
	"metal": preload("res://assets/field_ui/metal.png"),
}
const NAVY:=Color("#15314a")
const ICE:=Color("#7396a9")
const AMBER:=Color("#ffcb76")
const WHITE:=Color("#f5f6ed")
const RUBY:=Color("#ff6c59")
const HEALTH:=Color("#69db96")

class DisplayMark extends Control:
	func _draw() -> void:
		var line:=Color("#dce8ed")
		for y:float in [5.,11.,17.]:
			draw_line(Vector2(1,y),Vector2(20,y),line,1.8,true)
		for knob:Vector2 in [Vector2(6,5),Vector2(15,11),Vector2(9,17)]:
			draw_circle(knob,3.3,Color("#1c384c"),true,-1,true)
			draw_circle(knob,2.4,Color("#ffcf80"),true,-1,true)

class ObjectiveMark extends Control:
	func _draw() -> void:
		var center:=size*.5
		draw_set_transform(center,0,Vector2.ONE)
		var a:=PackedVector2Array([Vector2(0,-11),Vector2(8,0),Vector2(0,11),Vector2(-8,0)])
		draw_colored_polygon(a,Color("#fbc475"))
		draw_colored_polygon(PackedVector2Array([Vector2(0,-6),Vector2(4,0),Vector2(0,6),Vector2(-4,0)]),Color("#865523"))
		draw_line(Vector2(0,-13),Vector2(0,-10),Color("#fff2ce"),1.5,true)

var portrait:=TextureRect.new()
var objective:=Panel.new()
var objective_mark:=ObjectiveMark.new()
var row: HBoxContainer
var mineral_row: HBoxContainer
var numbers := {}
var cells := {}
var pulses := {}
var health_bar:=ProgressBar.new()
var health_trail:=ProgressBar.new()
var level_continue: Button
var chapter: Label
var purse: Label
var workshop_stock: Label
var work_plate:=Panel.new()
var operation:=ProgressBar.new()
var health_text: Label
var damage_text: Label
var threat_text: Label
var health_fill:=StyleBoxFlat.new()
var health_tween: Tween
var hit_tween: Tween
var shown_hp:=-1
var hp_capacity:=-1
var nearby_threat:=false
var shown_balances:=Vector4i(-1,-1,-1,-1)
var shown_level:=-1
var quality:Button
var display_mark:=DisplayMark.new()

func _skin(fill:Color,outline:Color,radius:int,shadow:=true) -> StyleBoxFlat:
	var skin:=StyleBoxFlat.new()
	skin.bg_color=fill
	skin.border_color=outline
	skin.set_border_width_all(1)
	skin.set_corner_radius_all(radius)
	if shadow:
		skin.shadow_color=Color("#0b172c64")
		skin.shadow_size=2
		skin.shadow_offset=Vector2(0,2)
	return skin

func _type(label:Label,points:int,tint:Color) -> void:
	label.add_theme_font_override("font",TYPE)
	label.add_theme_font_size_override("font_size",points)
	label.add_theme_color_override("font_color",tint)
	label.mouse_filter=Control.MOUSE_FILTER_IGNORE

func _label(points:int,tint:Color) -> Label:
	var label:=_text_line(points,tint)
	_type(label,points,tint)
	return label

func _action(button:Button,fill:Color,outline:Color,tint:Color) -> void:
	for state:String in ["normal","hover","pressed","hover_pressed"]:
		var style:=_skin(fill if state=="normal" else fill.lightened(.10),outline,13)
		# The touch target extends above and below the visible enamel face.
		style.expand_margin_top=-13
		style.expand_margin_bottom=-13
		if button==quality:
			style.content_margin_left=25
			style.content_margin_right=5
		button.add_theme_stylebox_override(state,style)
	button.add_theme_font_override("font",TYPE)
	button.add_theme_font_size_override("font_size",22)
	button.add_theme_color_override("font_color",tint)
	button.add_theme_color_override("font_hover_color",tint)

func _material_row(kinds:Array) -> HBoxContainer:
	var group:=HBoxContainer.new()
	group.mouse_filter=Control.MOUSE_FILTER_IGNORE
	group.add_theme_constant_override("separation",5)
	add_child(group)
	for kind:String in kinds:
		var cell:=PanelContainer.new()
		cell.name=kind.capitalize()
		cell.mouse_filter=Control.MOUSE_FILTER_IGNORE
		var style:=_skin(NAVY,ICE,12)
		style.content_margin_left=5
		style.content_margin_right=10
		style.content_margin_top=2
		style.content_margin_bottom=2
		cell.add_theme_stylebox_override("panel",style)
		group.add_child(cell)
		var pair:=HBoxContainer.new()
		pair.mouse_filter=Control.MOUSE_FILTER_IGNORE
		pair.add_theme_constant_override("separation",2)
		cell.add_child(pair)
		var icon:=TextureRect.new()
		icon.texture=MATERIAL_ICONS[kind]
		icon.custom_minimum_size=Vector2(41,39)
		icon.expand_mode=TextureRect.EXPAND_IGNORE_SIZE
		icon.stretch_mode=TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		icon.mouse_filter=Control.MOUSE_FILTER_IGNORE
		pair.add_child(icon)
		var amount:=Label.new()
		_type(amount,26,WHITE)
		amount.text="0"
		amount.custom_minimum_size.x=14.
		amount.horizontal_alignment=HORIZONTAL_ALIGNMENT_CENTER
		pair.add_child(amount)
		numbers[kind]=amount
		cells[kind]=cell
	return group

func _ready() -> void:
	super()
	stock.hide()
	plate.name="SurvivorStatus"
	plate.add_theme_stylebox_override("panel",_skin(NAVY,ICE,15))
	portrait.name="Character1Portrait"
	portrait.texture=FACE
	portrait.expand_mode=TextureRect.EXPAND_IGNORE_SIZE
	portrait.mouse_filter=Control.MOUSE_FILTER_IGNORE
	var enamel:=ShaderMaterial.new()
	enamel.shader=FRAME
	portrait.material=enamel
	add_child(portrait)
	chapter=_label(22,WHITE)
	chapter.text="Level 1  ·  Snow camp"
	health_text=_label(18,Color("#cfebdf"))
	threat_text=_label(16,Color("#ffbd9f"))
	threat_text.text="Wolves nearby"
	threat_text.hide()
	damage_text=_label(22,RUBY)
	damage_text.hide()
	for bar in [health_trail,health_bar,operation]:
		bar.mouse_filter=Control.MOUSE_FILTER_IGNORE
		bar.show_percentage=false
		bar.step=0.
		add_child(bar)
	health_trail.name="HealthLost"
	health_bar.name="PlayerHealth"
	health_trail.add_theme_stylebox_override("background",_skin(Color("#081d29"),Color("#3d5d6b"),4,false))
	health_trail.add_theme_stylebox_override("fill",_skin(AMBER,AMBER,4,false))
	health_bar.add_theme_stylebox_override("background",StyleBoxEmpty.new())
	health_fill.set_corner_radius_all(4)
	health_bar.add_theme_stylebox_override("fill",health_fill)
	row=_material_row(Ledger.ORIGINAL_KINDS)
	mineral_row=_material_row(Ledger.MINERALS)
	mineral_row.name="CarriedMinerals"
	mineral_row.hide()
	objective.name="ObjectiveStrip"
	objective.mouse_filter=Control.MOUSE_FILTER_IGNORE
	var strip:=_skin(Color("#19354dee"),Color("#b59660"),10)
	strip.border_width_left=3
	strip.border_color=AMBER
	objective.add_theme_stylebox_override("panel",strip)
	add_child(objective)
	_type(prompt,23,WHITE)
	move_child(prompt,-1)
	objective_mark.mouse_filter=Control.MOUSE_FILTER_IGNORE
	add_child(objective_mark)
	operation.name="TransferProgress"
	operation.max_value=1.
	operation.add_theme_stylebox_override("background",_skin(Color("#1c3847"),Color("#1c3847"),3,false))
	operation.add_theme_stylebox_override("fill",_skin(AMBER,AMBER,3,false))
	move_child(operation,-1)
	operation.hide()
	purse=_label(19,Color("#ceefbd"))
	work_plate.mouse_filter=Control.MOUSE_FILTER_IGNORE
	work_plate.add_theme_stylebox_override("panel",_skin(Color("#173146ec"),ICE,9))
	add_child(work_plate)
	move_child(purse,-1)
	workshop_stock=_label(18,Color("#e3edf0"))
	workshop_stock.hide()
	work_plate.hide()
	level_continue=_button()
	level_continue.name="ContinueToLevel2"
	level_continue.text="Preview Level 2  ›"
	_action(level_continue,Color("#94551e"),AMBER,Color("#fff0cd"))
	reflow()

func set_health(amount:int,maximum:int) -> void:
	if not health_text or (amount==shown_hp and maximum==hp_capacity):return
	var before:=shown_hp
	shown_hp=amount
	hp_capacity=maximum
	health_text.text="HP  %d / %d"%[amount,maximum]
	for bar in [health_bar,health_trail]:bar.max_value=maximum
	if health_tween:health_tween.kill()
	health_bar.value=amount
	health_fill.bg_color=RUBY if amount*3<=maximum else HEALTH
	if before>amount:
		health_trail.value=maxf(before,health_trail.value)
		health_tween=create_tween()
		health_tween.tween_interval(.18)
		health_tween.tween_property(health_trail,"value",float(amount),.43)
		if hit_tween:hit_tween.kill()
		damage_text.text="−%d"%(before-amount)
		damage_text.modulate.a=1.
		damage_text.show()
		threat_text.hide()
		hit_tween=create_tween()
		hit_tween.tween_interval(.58)
		hit_tween.tween_property(damage_text,"modulate:a",0.,.35)
		hit_tween.tween_callback(_finish_damage_notice)
	else:
		health_trail.value=amount
		_finish_damage_notice()

func _finish_damage_notice() -> void:
	damage_text.hide()
	threat_text.visible=nearby_threat

func set_threat(nearby:bool) -> void:
	nearby_threat=nearby
	if threat_text:threat_text.visible=nearby and not damage_text.visible

func field_status(counts:Dictionary,message:String) -> void:
	var changed:=false
	for kind:String in numbers:
		var amount:Label=numbers[kind]
		var next:=str(counts.get(kind,0))
		if amount.text!=next:
			if int(next)>int(amount.text):
				if pulses.has(kind): (pulses[kind] as Tween).kill()
				var cell:Control=cells[kind]
				cell.modulate=Color(1.24,1.19,.80)
				var pulse:=create_tween()
				pulse.tween_property(cell,"modulate",Color.WHITE,.35)
				pulses[kind]=pulse
			amount.text=next
			changed=true
	var show_minerals:=Ledger.MINERALS.any(func(k):return counts.get(k,0)>0)
	if mineral_row.visible!=show_minerals:
		mineral_row.visible=show_minerals
		changed=true
	if prompt.text!=message:
		prompt.text=message
		changed=true
	if changed:reflow()

func settlement_status(journal:Dictionary,activity:float) -> void:
	if not chapter:return
	var trays:=int(journal.cooked)-int(journal.served)-int(journal.get("held_meal",0))
	var totals:=Vector4i(journal.served,journal.processed_wood,journal.processed_stone,trays)
	operation.value=activity
	if shown_balances==totals and shown_level==int(journal.level) and operation.visible==(activity>0):
		return
	shown_balances=totals
	shown_level=int(journal.level)
	var heading:="Level 2  ·  Preview" if shown_level==2 else "Level 1  ·  Snow camp"
	var cash:="Cash  %d"%int(journal.served) if journal.served>0 else ""
	var balances:=PackedStringArray()
	if journal.processed_wood>0:balances.append("Planks %d"%journal.processed_wood)
	if journal.processed_stone>0:balances.append("Blocks %d"%journal.processed_stone)
	if trays>0:balances.append("Meals on tray %d"%trays)
	var stock_line:="  ·  ".join(balances)
	var change:=chapter.text!=heading or purse.text!=cash or workshop_stock.text!=stock_line or operation.visible!=(activity>0)
	chapter.text=heading
	purse.text=cash
	workshop_stock.text=stock_line
	purse.visible=not cash.is_empty()
	workshop_stock.visible=not stock_line.is_empty()
	work_plate.visible=purse.visible or workshop_stock.visible
	operation.visible=activity>0
	if change:reflow()

func _safe_rect() -> Rect2:
	var area:=get_viewport_rect()
	if OS.has_feature("mobile"):
		var window_size:=Vector2(get_window().size)
		var window_origin:=Vector2(get_window().position)
		var pixels:=Rect2(DisplayServer.get_display_safe_area()).intersection(Rect2(window_origin,window_size))
		if pixels.has_area() and window_size.x>0 and window_size.y>0:
			var ratio:=area.size/window_size
			area=Rect2(area.position+(pixels.position-window_origin)*ratio,pixels.size*ratio)
	return area.grow(-EDGE)

func _anchor_right(control:Control,right:float,y:float,width:float) -> void:
	var natural:=control.get_combined_minimum_size()
	control.size=natural
	var factor:=minf(1.,width/maxf(1.,natural.x))
	control.scale=Vector2.ONE*factor
	control.position=Vector2(right-natural.x*factor,y)

func position_quality_button(button:Button,ultra:bool) -> void:
	if not is_instance_valid(quality):
		quality=button
		display_mark.mouse_filter=Control.MOUSE_FILTER_IGNORE
		quality.add_child(display_mark)
		display_mark.size=Vector2(22,22)
		display_mark.position=Vector2(12,31)
		_action(quality,Color("#214059f5"),ICE,WHITE)
	quality.text="Ultra" if ultra else "Standard"
	quality.tooltip_text="Graphics quality"
	var safe:=_safe_rect()
	quality.size=Vector2(132,82)
	quality.position=safe.end-quality.size

func reflow() -> void:
	if not is_instance_valid(row) or not is_instance_valid(level_continue):
		super()
		return
	var safe:=_safe_rect()
	var top:=safe.position
	var width:=safe.size.x
	var right:=safe.end.x
	portrait.position=top+Vector2(0,-1)
	portrait.size=Vector2(74,74)
	plate.position=top+Vector2(25,3)
	var threat_x:=maxf(168.,77.+health_text.get_minimum_size().x+11.)
	var hero_width:=maxf(ceilf(chapter.get_minimum_size().x)+91.,threat_x+threat_text.get_minimum_size().x+12.)
	plate.size=Vector2(hero_width-25,64)
	chapter.position=top+Vector2(76,5)
	health_text.position=top+Vector2(77,29)
	threat_text.position=top+Vector2(threat_x,30)
	damage_text.position=top+Vector2(hero_width-32,24)
	for bar in [health_trail,health_bar]:
		bar.position=top+Vector2(77,53)
		bar.size=Vector2(hero_width-91,7)
	var resource_width:=maxf(134.,width-hero_width-12.)
	_anchor_right(row,right,top.y+4,resource_width)
	var resource_end:=row.position.y+row.size.y*row.scale.y
	var resource_left:=row.position.x
	if mineral_row.visible:
		_anchor_right(mineral_row,right,resource_end+4,resource_width)
		resource_end=mineral_row.position.y+mineral_row.size.y*mineral_row.scale.y
		resource_left=minf(resource_left,mineral_row.position.x)
	if work_plate.visible:
		var stock_size:=workshop_stock.get_minimum_size() if workshop_stock.visible else Vector2.ZERO
		var cash_size:=purse.get_minimum_size() if purse.visible else Vector2.ZERO
		var stock_width:=maxf(stock_size.x,cash_size.x)
		var text_scale:=minf(1.,(resource_width-16)/maxf(1.,stock_width))
		work_plate.size=Vector2(ceilf(stock_width*text_scale)+16,(cash_size.y+stock_size.y)*text_scale+6)
		work_plate.position=Vector2(right-work_plate.size.x,resource_end+4)
		purse.position=work_plate.position+Vector2(8,2)
		workshop_stock.position=purse.position+Vector2(0,cash_size.y*text_scale)
		for label:Label in [purse,workshop_stock]:label.scale=Vector2.ONE*text_scale
		resource_end=work_plate.position.y+work_plate.size.y
		resource_left=minf(resource_left,work_plate.position.x)
	var hint_y:=top.y+79
	var max_hint:=minf(width,395.)
	var room:=resource_left-top.x-10.
	if resource_end>hint_y-3 and room<max_hint:
		if room>=225.:max_hint=room
		else:hint_y=resource_end+7
	var text_width:=TYPE.get_string_size(prompt.text,HORIZONTAL_ALIGNMENT_LEFT,-1,23).x
	var hint_width:=clampf(text_width+56,126.,max_hint)
	prompt.position=Vector2(top.x+37,hint_y+4)
	prompt.size=Vector2(maxf(1.,hint_width-47),0)
	prompt.size.y=prompt.get_minimum_size().y
	var hint_height:=maxf(40.,prompt.size.y+12)+(4. if operation.visible else 0.)
	objective.position=Vector2(top.x,hint_y)
	objective.size=Vector2(hint_width,hint_height)
	objective_mark.position=objective.position+Vector2(5,0)
	objective_mark.size=Vector2(27,hint_height)
	operation.position=objective.position+Vector2(11,hint_height-6)
	operation.size=Vector2(hint_width-22,3)
	gate.position=objective.position+Vector2(0,hint_height+7)
	gate.size=Vector2(200,54)
	tree.position=gate.position+Vector2(0,60)
	tree.size=gate.size
	level_continue.size=Vector2(187,82)
	level_continue.position=safe.end-Vector2(187,164)
	if is_instance_valid(quality):
		quality.position=safe.end-quality.size
