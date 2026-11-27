extends "res://orbit_hud.gd"

const Ledger = preload("res://field_inventory.gd")
const FACE = preload("res://assets/field_ui/camp_portrait.png")
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

const ObjectiveTicket = preload("res://field_hud_objective.gd")
const MovementStick = preload("res://field_thumbstick.gd")
const PAPER := Color("#fbf1e8")
const INK := Color("#142236")
const OCHRE := Color("#a15d22")

class DisplayMark extends Control:
	const GEAR=preload("res://assets/field_ui/modern/gear.png")
	func _draw() -> void:
		draw_texture_rect(GEAR,Rect2(Vector2.ZERO,size),false)

class Supply extends Control:
	var art: TextureRect
	var amount: Label
	func install(icon: TextureRect, label: Label) -> void:
		mouse_filter = Control.MOUSE_FILTER_IGNORE
		art = icon
		amount = label
		add_child(art)
		add_child(amount)
		resized.connect(arrange)
		measure()
	func measure() -> void:
		custom_minimum_size = Vector2(ceilf(amount.get_minimum_size().x)+69,55)
		arrange()
	func arrange() -> void:
		art.position = Vector2(5,3)
		art.size = Vector2(41,47)
		amount.position = Vector2(54,3)
		amount.size = Vector2(maxf(1.,size.x-58),44)
		queue_redraw()
	func _draw() -> void:
		if get_index()>0:draw_line(Vector2(0,12),Vector2(0,size.y-12),Color("#d0c5c2"),1.1,true)

var portrait:=TextureRect.new()
var camp_dock=preload("res://field_camp_dock.gd").new()
var chapter_detail:=Label.new()
var objective_caption:=Label.new()
var accent:=ColorRect.new()
var rail_backs:Array[Panel]=[]
var overflow:=Label.new()
var counts_area:=Rect2()
var group_rule:=ColorRect.new()
var objective:=Panel.new()
var ticket := ObjectiveTicket.new()
var thumbstick := MovementStick.new()
var row: HBoxContainer
var mineral_row: HBoxContainer
var numbers := {}
var cells := {}
var pulses := {}
var health_bar:=ProgressBar.new()
var health_trail:=ProgressBar.new()
var level_continue: Button
var chapter: Label
const GOODS = {"cash":8,"planks":9,"blocks":10,"meals":11}
var stock_row: HBoxContainer
var outputs := {}
var display_goods := {}
var operation:=ProgressBar.new()
var payment_track:=ProgressBar.new()
var health_text: Label
var damage_text: Label
var threat_text: Label
var health_fill:=StyleBoxFlat.new()
var threat_chip := Panel.new()
var quality_help := Label.new()
var quality_fade: Tween
var quality_initialized := false
var was_ultra := true
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
	for state: String in ["normal","hover","pressed","hover_pressed"]:
		var face := _skin(fill if state=="normal" else fill.lightened(.13),outline,17)
		face.border_width_bottom=3
		face.expand_margin_top=-16.
		face.expand_margin_bottom=-16.
		if button==quality:
			face.expand_margin_left=-12.
			face.expand_margin_right=-12.
			face.content_margin_left=29.
			face.content_margin_right=6.
		button.add_theme_stylebox_override(state,face)
	button.add_theme_font_override("font",TYPE)
	button.add_theme_font_size_override("font_size",22)
	button.add_theme_color_override("font_color",tint)
	button.add_theme_color_override("font_hover_color",tint)

func _material_row(kinds:Array, finished:=false) -> HBoxContainer:
	var group:=HBoxContainer.new()
	group.mouse_filter=Control.MOUSE_FILTER_IGNORE
	group.add_theme_constant_override("separation",4)
	add_child(group)
	for kind: String in kinds:
		var cell := Supply.new()
		cell.name = kind.capitalize()
		group.add_child(cell)
		var icon := TextureRect.new()
		if finished:
			var atlas:=AtlasTexture.new()
			atlas.atlas=ObjectiveTicket.ATLAS
			var index:int=GOODS[kind]
			var side:=ObjectiveTicket.TILE
			atlas.region=Rect2((index%4)*side,(index/4)*side,side,side)
			icon.texture=atlas
		else:
			icon.texture=MATERIAL_ICONS[kind]
		icon.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		icon.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		icon.mouse_filter = Control.MOUSE_FILTER_IGNORE
		var amount := Label.new()
		_type(amount,25,INK)
		amount.text = "0"
		amount.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
		amount.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		cell.install(icon,amount)
		cell.accessibility_name=kind.capitalize()
		if finished:
			outputs[kind]=amount
			display_goods[kind]=cell
			cell.hide()
		else:
			numbers[kind]=amount
			cells[kind]=cell
	return group

func _ready() -> void:
	super()
	stock.hide()
	plate.name="SurvivorStatus"
	var hero_plate := _skin(PAPER,Color("#bfbec1"),13)
	hero_plate.border_width_bottom=1
	plate.add_theme_stylebox_override("panel",hero_plate)
	thumbstick.install(get_parent().get_parent())
	add_child(thumbstick)
	move_child(thumbstick,0)
	portrait.name="Character1Portrait"
	portrait.texture=FACE
	portrait.expand_mode=TextureRect.EXPAND_IGNORE_SIZE
	portrait.mouse_filter=Control.MOUSE_FILTER_IGNORE
	var enamel:=ShaderMaterial.new()
	enamel.shader=FRAME
	portrait.material=enamel
	add_child(portrait)
	chapter=_label(29,INK)
	chapter.text="HAVENLINE"
	_type(chapter_detail,17,Color("#5a5a65"))
	chapter_detail.text="Camp  ·  Level 1"
	add_child(chapter_detail)
	health_text=_label(15,INK)
	threat_text=_label(16,Color("#ffbd9f"))
	threat_text.text="Wolves nearby"
	threat_chip.mouse_filter=Control.MOUSE_FILTER_IGNORE
	var threat_style:=_skin(Color("#753b35f6"),Color("#e7b67e"),9)
	threat_chip.add_theme_stylebox_override("panel",threat_style)
	add_child(threat_chip)
	move_child(threat_text,-1)
	threat_chip.hide()
	threat_text.hide()
	damage_text=_label(22,RUBY)
	damage_text.hide()
	for bar in [health_trail,health_bar,operation,payment_track]:
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
	var strip:=_skin(PAPER,Color("#cbbdbe"),13)
	strip.border_width_bottom=1
	objective.add_theme_stylebox_override("panel",strip)
	add_child(objective)
	objective.add_child(ticket)
	_type(objective_caption,17,Color("#59505a"))
	objective_caption.text="CAMP OBJECTIVE"
	objective.add_child(objective_caption)
	accent.mouse_filter=Control.MOUSE_FILTER_IGNORE
	accent.color=Color("#ff6907")
	objective.add_child(accent)
	_type(prompt,24,INK)
	move_child(prompt,-1)
	payment_track.name="PurchaseProgress"
	payment_track.max_value=1.
	payment_track.mouse_filter=Control.MOUSE_FILTER_IGNORE
	payment_track.add_theme_stylebox_override("background",_skin(Color("#d5ccae"),Color("#d5ccae"),3,false))
	payment_track.add_theme_stylebox_override("fill",_skin(Color("#408b4e"),Color("#408b4e"),3,false))
	move_child(payment_track,-1)
	payment_track.hide()
	operation.name="WorkshopProgress"
	operation.accessibility_name="Workshop cycle progress"
	operation.max_value=1.
	operation.add_theme_stylebox_override("background",_skin(Color("#1c3847"),Color("#1c3847"),3,false))
	operation.add_theme_stylebox_override("fill",_skin(AMBER,AMBER,3,false))
	move_child(operation,-1)
	operation.hide()
	stock_row=_material_row(GOODS.keys(),true)
	stock_row.name="FinishedGoods"
	stock_row.hide()
	for group:HBoxContainer in [row,mineral_row,stock_row]:
		var rail:=Panel.new()
		rail.mouse_filter=Control.MOUSE_FILTER_IGNORE
		rail.add_theme_stylebox_override("panel",_skin(PAPER,Color("#c5bdbe"),11))
		add_child(rail)
		move_child(rail,group.get_index())
		rail_backs.append(rail)
	_type(overflow,22,INK)
	overflow.horizontal_alignment=HORIZONTAL_ALIGNMENT_CENTER
	overflow.vertical_alignment=VERTICAL_ALIGNMENT_CENTER
	overflow.hide()
	add_child(overflow)
	group_rule.mouse_filter=Control.MOUSE_FILTER_IGNORE
	group_rule.color=Color("#d0c5c2")
	add_child(group_rule)
	add_child(camp_dock)
	camp_dock.configure(get_parent().get_parent(),self)
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
	health_text.text="%d / %d"%[amount,maximum]
	health_bar.accessibility_name="Health %d of %d"%[amount,maximum]
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
		threat_chip.hide()
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
	threat_chip.visible=nearby_threat

func set_threat(nearby:bool) -> void:
	var changed:=nearby_threat!=nearby
	nearby_threat=nearby
	if threat_text:
		threat_text.visible=nearby and not damage_text.visible
		threat_chip.visible=threat_text.visible
	if changed:reflow()

func field_status(counts:Dictionary,message:String) -> void:
	var changed:=false
	for kind:String in numbers:
		var amount:Label=numbers[kind]
		var next:=str(Ledger.Progress.units(counts.get(kind,0)))
		if amount.text!=next:
			if int(next)>int(amount.text):
				if pulses.has(kind): (pulses[kind] as Tween).kill()
				var cell:Control=cells[kind]
				cell.modulate=Color(1.24,1.19,.80)
				var pulse:=create_tween()
				pulse.tween_property(cell,"modulate",Color.WHITE,.35)
				pulses[kind]=pulse
			amount.text=next
			cells[kind].accessibility_name="%s %s"%[Ledger.TITLES[kind],next]
			cells[kind].measure()
			changed=true
	var show_minerals:=Ledger.MINERALS.any(func(k):return counts.get(k,0)>0)
	if mineral_row.visible!=show_minerals:
		mineral_row.visible=show_minerals
		changed=true
	if prompt.text!=message:
		prompt.text=message
		ticket.set_message(message,MATERIAL_ICONS)
		var id=Ledger.Progress.TITLES.find_key(ticket.heading)
		var world=get_parent().get_parent()
		var fraction:=0.
		if id!=null and world.inventory.costs.has(id) and world.inventory.offer_open(id):
			var total:=0
			var paid:=0
			for kind in world.inventory.costs[id]:
				total+=int(world.inventory.costs[id][kind])
				paid+=int(world.inventory.paid[id][kind])
			fraction=float(paid)/maxi(1,total)
		payment_track.value=fraction
		payment_track.visible=fraction>0.
		payment_track.accessibility_name="%d percent paid"%roundi(fraction*100)
		objective.accessibility_name=message
		prompt.visible=ticket.fallback
		changed=true
	if changed:reflow()

func settlement_status(journal:Dictionary,activity:float) -> void:
	if not chapter:return
	var trays:=Ledger.Settlement.waiting_meals(journal)
	var totals:=Vector4i(journal.served,journal.processed_wood,journal.processed_stone,trays)
	operation.value=activity
	if shown_balances==totals and shown_level==int(journal.level) and operation.visible==(activity>0):
		return
	shown_balances=totals
	shown_level=int(journal.level)
	var heading:="Camp  ·  Level 2" if shown_level==2 else "Camp  ·  Level 1"
	var quantity:={"cash":totals.x,"planks":totals.y,"blocks":totals.z,"meals":totals.w}
	chapter_detail.text=heading
	stock_row.visible=totals!=Vector4i.ZERO
	for kind: String in quantity:
		var amount: int=quantity[kind]
		var cell: Supply=display_goods[kind]
		cell.visible=amount>0
		outputs[kind].text=str(amount)
		cell.accessibility_name="%s %d"%[kind.capitalize(),amount]
		cell.measure()
	operation.visible=activity>0
	reflow()

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
		display_mark.size=Vector2(32,32)
		display_mark.position=Vector2(32,20)
		_action(quality,PAPER,Color("#c5bdbe"),INK)
		for state:String in ["normal","pressed","hover","hover_pressed"]:
			var gear_skin:=_skin(PAPER,Color("#c5bdbe"),13)
			gear_skin.expand_margin_left=-18.
			gear_skin.expand_margin_right=-18.
			gear_skin.expand_margin_top=-10.
			gear_skin.expand_margin_bottom=-30.
			quality.add_theme_stylebox_override(state,gear_skin)
		_type(quality_help,18,WHITE)
		quality_help.horizontal_alignment=HORIZONTAL_ALIGNMENT_CENTER
		quality_help.add_theme_stylebox_override("normal",_skin(NAVY,ICE,8))
		quality.add_child(quality_help)
		quality_help.hide()
	quality.text=""
	var setting:="Ultra" if ultra else "Standard"
	quality.accessibility_name="Graphics quality, "+setting+". Tap to switch."
	quality.tooltip_text=quality.accessibility_name
	if quality_initialized and was_ultra!=ultra:
		if quality_fade:quality_fade.kill()
		quality_help.text=setting
		quality_help.modulate.a=1.
		quality_help.show()
		quality_fade=create_tween()
		quality_fade.tween_interval(1.1)
		quality_fade.tween_property(quality_help,"modulate:a",0.,.25)
		quality_fade.tween_callback(quality_help.hide)
	was_ultra=ultra
	quality_initialized=true
	var safe:=_safe_rect()
	quality.size=Vector2(96,96)
	quality.position=Vector2(safe.end.x-quality.size.x,safe.position.y)
	quality_help.size=Vector2(74,28)
	quality_help.position=Vector2(-12,64)

func reflow() -> void:
	if not is_instance_valid(row) or not is_instance_valid(level_continue):
		super()
		return
	var safe:=_safe_rect()
	var top:=safe.position
	var right:=safe.end.x
	var width:=safe.size.x
	var hero_width:=220.
	plate.position=top
	plate.size=Vector2(hero_width,78.)
	portrait.position=top+Vector2(5,5)
	portrait.size=Vector2(67,67)
	chapter.position=top+Vector2(78,1)
	chapter.size=chapter.get_minimum_size()
	chapter_detail.position=top+Vector2(79,32)
	chapter_detail.size=chapter_detail.get_minimum_size()
	health_text.position=top+Vector2(hero_width-62.,51.)
	health_text.size=health_text.get_minimum_size()
	for bar in [health_trail,health_bar]:
		bar.position=top+Vector2(79,62)
		bar.size=Vector2(hero_width-148,7)
	threat_text.position=top+Vector2(16,83)
	threat_chip.position=threat_text.position-Vector2(7,1)
	threat_chip.size=threat_text.get_minimum_size()+Vector2(14,2)
	threat_text.add_theme_color_override("font_color",Color("#ffddb0"))
	threat_text.add_theme_color_override("font_outline_color",Color("#79363a"))
	threat_text.add_theme_constant_override("outline_size",0)
	damage_text.position=health_text.position+Vector2(0,23)
	damage_text.add_theme_color_override("font_outline_color",Color("#542b28"))
	damage_text.add_theme_constant_override("outline_size",4)
	var resource_width:=maxf(120.,width-hero_width-106.)
	var rail_right:=right-99.
	var groups:Array[HBoxContainer]=[row,stock_row,mineral_row]
	var full_width:=0.
	var extras:=0
	for group in groups:
		if group.visible:
			full_width+=group.get_combined_minimum_size().x
			if group!=row:
				for cell in group.get_children():
					if cell.visible:extras+=1
	var compressed:=extras>0 and full_width*.82>resource_width
	var panel_width:=minf(full_width,resource_width)
	var chip_width:=53. if compressed else 0.
	if compressed:panel_width=minf(resource_width,row.get_combined_minimum_size().x+chip_width)
	if width>1100.:rail_right=minf(rail_right,safe.get_center().x+panel_width*.5)
	var x:=rail_right-panel_width
	var start_x:=x
	var factor:=minf(1.,(panel_width-chip_width)/maxf(1.,row.get_combined_minimum_size().x if compressed else full_width))
	var rail_height:=55.*factor
	for group in groups:
		group.modulate.a=0. if compressed and group!=row else 1.
		if not group.visible:continue
		if group.modulate.a==0.:
			group.position=Vector2(start_x,top.y)
			group.scale=Vector2.ONE*minf(1.,panel_width/maxf(1.,group.get_combined_minimum_size().x))
			continue
		group.size=group.get_combined_minimum_size()
		group.scale=Vector2.ONE*factor
		group.position=Vector2(x,top.y)
		x+=group.size.x*factor
	counts_area=Rect2(start_x,top.y,panel_width,rail_height)
	for i in rail_backs.size():rail_backs[i].visible=i==0
	rail_backs[0].position=counts_area.position
	rail_backs[0].size=counts_area.size
	overflow.visible=compressed
	overflow.text="+%d"%extras
	overflow.accessibility_name="Show all carried resources and workshop goods"
	overflow.position=Vector2(rail_right-chip_width,top.y)
	overflow.size=Vector2(chip_width,rail_height)
	group_rule.visible=stock_row.visible or mineral_row.visible
	group_rule.position=Vector2(start_x+row.size.x*factor,top.y+12.*factor)
	group_rule.size=Vector2(1.,31.*factor)
	var resource_end:=top.y+rail_height
	operation.position=Vector2(rail_right-87.,resource_end+2.)
	operation.size=Vector2(87.,5.)
	var available:=minf(width-100.,500.)
	var card_width:=clampf(ticket.natural_width(),190.,available)
	var card_height:=ticket.content_height(card_width)
	if ticket.fallback:
		card_width=clampf(ticket.text_width(prompt.text,24)+30.,190.,available)
		prompt.size=Vector2(card_width-30.,0)
		prompt.size.y=prompt.get_minimum_size().y
		card_height=maxf(48.,prompt.size.y+20.)
	if payment_track.visible:card_height+=6.
	var notice_offset:=31. if nearby_threat or damage_text.visible else 0.
	var objective_y:=top.y+89.+notice_offset
	var base_height:=card_height
	card_height+=27.
	objective_y=maxf(objective_y,resource_end+6.)
	objective.size=Vector2(card_width+10.,card_height)
	objective.position=Vector2(top.x,objective_y)
	objective_caption.position=Vector2(18,5)
	objective_caption.size=Vector2(card_width-28,23)
	accent.position=Vector2(5,9)
	accent.size=Vector2(4,card_height-18.)
	ticket.position=Vector2(7,25)
	ticket.size=Vector2(card_width,base_height-(6. if payment_track.visible else 0.))
	ticket.queue_redraw()
	prompt.position=objective.position+Vector2(19.,30.)
	payment_track.position=objective.position+Vector2(15.,card_height-8.)
	payment_track.size=Vector2(card_width-24.,4.)
	gate.position=Vector2(top.x,objective.position.y+objective.size.y+56.)
	gate.size=Vector2(200,54)
	tree.position=gate.position+Vector2(0,60)
	tree.size=gate.size
	level_continue.size=Vector2(187,82)
	level_continue.position=safe.end-Vector2(187,167)
	if is_instance_valid(quality):
		quality.position=Vector2(safe.end.x-quality.size.x,top.y)
	if is_instance_valid(camp_dock):camp_dock.reflow()
