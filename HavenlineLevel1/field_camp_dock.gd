extends Control
## Landscape concept navigation, adapted to the current paid camp. Buttons
## guide the player to the actual interaction rather than performing it remotely.
const P=preload("res://field_progression.gd")
const Crew = preload("res://field_crew.gd")
const TYPE=preload("res://assets/field_ui/type/BarlowSemiCondensed-SemiBold.ttf")
const PAPER=Color("#fbf1e8")
const INK=Color("#142236")
const MUTED=Color("#5b656e")
const ORANGE=Color("#ff6907")
# Sprites are cropped from the selected 9f7460328 modern camp HUD sheet.
# Black-on-ivory glyph masks keep the renderer's touch and focus states live.
const GLYPHS={
	"Camp":preload("res://assets/field_ui/modern/camp.png"),
	"Storage":preload("res://assets/field_ui/modern/storage.png"),
	"Survivors":preload("res://assets/field_ui/modern/survivors.png")}
const BUILD=preload("res://assets/field_ui/modern/build.png")
var world
var hud
var tab:=""
var active_tab:="Camp"
var tracking:=""
var tracking_name:=""
var nav:=Panel.new()
var build:=TextureButton.new()
var build_art:=TextureRect.new()
var pack_button:=Button.new()
var sheet:=Panel.new()
var title:=Label.new()
var subtitle:=Label.new()
var close:=Button.new()
var actions:=VBoxContainer.new()
var tabs:Dictionary={}
var commands:Array=[]
var finger:=-2
var sheet_key:=""
var list_page := 0
var poll_time:=0.

func face(fill:Color,edge:Color,r:=13)->StyleBoxFlat:
	var skin:=StyleBoxFlat.new()
	skin.bg_color=fill
	skin.border_color=edge
	skin.set_border_width_all(1)
	skin.set_corner_radius_all(r)
	skin.shadow_color=Color("#16253626")
	skin.shadow_size=3
	skin.shadow_offset=Vector2(0,2)
	return skin

func configure(host,owner_hud)->void:
	world=host
	hud=owner_hud
	name="CampNavigation"
	mouse_filter=Control.MOUSE_FILTER_IGNORE
	set_anchors_and_offsets_preset(PRESET_FULL_RECT)
	add_child(nav)
	nav.mouse_filter=Control.MOUSE_FILTER_IGNORE
	nav.add_theme_stylebox_override("panel",face(PAPER,Color("#c5bdbe")))
	for key:String in GLYPHS:
		var button:=Button.new()
		button.name=key
		button.text=""
		button.icon=null
		button.expand_icon=true
		button.add_theme_constant_override("icon_max_width",31)
		button.add_theme_constant_override("h_separation",8)
		button.add_theme_font_override("font",TYPE)
		button.add_theme_font_size_override("font_size",24)
		button.add_theme_color_override("font_color",INK)
		button.add_theme_color_override("font_hover_color",INK)
		button.add_theme_color_override("icon_normal_color",Color.WHITE)
		button.add_theme_stylebox_override("normal",StyleBoxEmpty.new())
		button.add_theme_stylebox_override("hover",StyleBoxEmpty.new())
		button.add_theme_stylebox_override("pressed",StyleBoxEmpty.new())
		button.accessibility_name=key
		button.mouse_filter=Control.MOUSE_FILTER_IGNORE
		nav.add_child(button)
		button.pressed.connect(toggle.bind(key))
		tabs[key]=button
		var group:=HBoxContainer.new()
		group.name="TabLabel"
		group.mouse_filter=Control.MOUSE_FILTER_IGNORE
		group.alignment=BoxContainer.ALIGNMENT_CENTER
		group.add_theme_constant_override("separation",9)
		button.add_child(group)
		var glyph:=TextureRect.new()
		glyph.texture=GLYPHS[key]
		glyph.custom_minimum_size=Vector2(30.,32.)
		glyph.expand_mode=TextureRect.EXPAND_IGNORE_SIZE
		glyph.stretch_mode=TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		glyph.mouse_filter=Control.MOUSE_FILTER_IGNORE
		group.add_child(glyph)
		var caption:=Label.new()
		caption.text=key
		caption.add_theme_font_override("font",TYPE)
		caption.add_theme_font_size_override("font_size",24)
		caption.add_theme_color_override("font_color",INK)
		caption.mouse_filter=Control.MOUSE_FILTER_IGNORE
		group.add_child(caption)
		if key!="Camp":
			var divider:=ColorRect.new()
			divider.name="Divider"
			divider.color=Color("#c5bcbc")
			divider.mouse_filter=Control.MOUSE_FILTER_IGNORE
			button.add_child(divider)
		var active:=ColorRect.new()
		active.name="Active"
		active.color=ORANGE
		active.mouse_filter=Control.MOUSE_FILTER_IGNORE
		button.add_child(active)
	add_child(build)
	build.name="Build"
	build_art.texture=BUILD
	build_art.expand_mode=TextureRect.EXPAND_IGNORE_SIZE
	build_art.stretch_mode=TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	build_art.mouse_filter=Control.MOUSE_FILTER_IGNORE
	build.add_child(build_art)
	build.ignore_texture_size=true
	build.stretch_mode=TextureButton.STRETCH_KEEP_ASPECT_CENTERED
	build.mouse_filter=Control.MOUSE_FILTER_IGNORE
	build.accessibility_name="Build. View available plots and camp equipment."
	build.pressed.connect(toggle.bind("Build"))
	add_child(pack_button)
	pack_button.name="ViewResourceBalances"
	pack_button.accessibility_name="View carried resources and workshop stock"
	pack_button.mouse_filter=Control.MOUSE_FILTER_IGNORE
	for state:String in ["normal","hover","pressed","disabled"]:pack_button.add_theme_stylebox_override(state,StyleBoxEmpty.new())
	pack_button.pressed.connect(toggle.bind("Pack"))
	add_child(sheet)
	sheet.name="CampContext"
	sheet.mouse_filter=Control.MOUSE_FILTER_IGNORE
	sheet.add_theme_stylebox_override("panel",face(PAPER,Color("#c7babb")))
	sheet.add_child(title)
	title.add_theme_font_override("font",TYPE)
	title.add_theme_font_size_override("font_size",34)
	title.add_theme_color_override("font_color",INK)
	title.mouse_filter=Control.MOUSE_FILTER_IGNORE
	sheet.add_child(subtitle)
	subtitle.add_theme_font_override("font",TYPE)
	subtitle.add_theme_font_size_override("font_size",22)
	subtitle.add_theme_color_override("font_color",MUTED)
	subtitle.mouse_filter=Control.MOUSE_FILTER_IGNORE
	subtitle.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART
	sheet.add_child(actions)
	actions.mouse_filter=Control.MOUSE_FILTER_IGNORE
	actions.add_theme_constant_override("separation",5)
	sheet.add_child(close)
	close.name="Close"
	close.text="×"
	close.accessibility_name="Close details"
	close.add_theme_font_size_override("font_size",31)
	close.add_theme_color_override("font_color",INK)
	close.add_theme_stylebox_override("normal",StyleBoxEmpty.new())
	close.mouse_filter=Control.MOUSE_FILTER_IGNORE
	close.pressed.connect(dismiss)
	sheet.hide()
	reflow()

func dismiss()->void:
	tab=""
	sheet.hide()
	reflow()

func toggle(key:String)->void:
	if tab==key:
		dismiss()
		return
	active_tab=key
	list_page=0
	tab=key
	sheet_key=""
	sheet.show()
	refresh()
	reflow()

func _entry(label:String,id:String)->Array:return [label,id]

func refresh()->void:
	if tab.is_empty() or not world.field_ready:return
	var book=world.inventory
	var journal:Dictionary=book.settlement
	var description:=""
	var list:Array=[]
	match tab:
		"Pack":
			title.text="Carried resources"
			var lines:=PackedStringArray()
			var counts:=PackedStringArray()
			for kind:String in book.KINDS:
				if not kind in book.ORIGINAL_KINDS and int(book.carried[kind])==0:continue
				counts.append("%d %s"%[P.units(book.carried[kind]),str(book.TITLES[kind]).to_lower()])
				if counts.size()==3:
					lines.append("   ·   ".join(counts))
					counts.clear()
			if not counts.is_empty():lines.append("   ·   ".join(counts))
			var hand:Dictionary=book.hand_goods()
			lines.append("%d planks   ·   %d blocks"%[hand.planks,hand.blocks])
			lines.append("%d cooked meat   ·   $%d"%[hand.meal,hand.money])
			description="\n".join(lines)
			list.append(_entry("Storage details","storage_details"))
		"Camp":
			title.text="Snow camp" if world.camp_active else "Found your camp"
			description="Level %d  •  %d camp purchases"%[journal.level,book.build_order.size()]
			list.append(_entry("Guide to camp" if world.camp_active else "Find the hearth plot","home"))
			if world.camp_active:list.append(_entry("Move equipment","move"))
			if not world.player_wardrobe.CHARACTERS.is_empty():
				list.append(_entry("Choose character","character_open"))
		"Characters":
			title.text="Choose character"
			var current:int=world.player_character()
			for number in [1]+world.player_wardrobe.CHARACTERS.keys():
				var label:="Character %d"%number
				if number==current:label+="  ·  Active"
				list.append(_entry(label,"character_"+str(number)))
		"Storage":
			var tier:int=P.house_tier(book)
			title.text=["Storage house","Starter storehouse","Reinforced storehouse","Advanced storehouse"][clampi(tier,0,3)]
			if tier:
				description="%d wood   ·   %d stone   ·   %d meat"%[P.units(book.stored.wood),P.units(book.stored.stone),P.units(book.stored.meat)]
				var stock:Dictionary=book.house_goods()
				description+="\n%d planks   ·   %d blocks   ·   %d meals   ·   $%d"%[stock.planks,stock.blocks,stock.meal,stock.money]
				description+="\nStop beside a stocked shelf to collect."
				list.append(_entry("Guide to loading apron","depot"))
			else:description="A camp expansion opens the first storage purchase."
			var stage:=P.next_storage(book)
			if not stage.is_empty() and book.offer_open(stage):list.append(_entry(P.TITLES[stage]+"  ·  "+P.price_text(book.remaining(stage)),stage))
			if list.is_empty():list.append(_entry("Find next camp purchase","project"))
		"Survivors":
			title.text="Camp crew"
			if journal.rescued:
				var duty:=str(world.survivor.phase).replace("_"," ").capitalize()
				description=duty+"  •  "+str(journal.worker_deliveries)+" deliveries"
				list.append(_entry("Find survivor","worker"))
			elif journal.survivor_paid:
				description="Rescue is funded. Meet the survivor in the field."
				list.append(_entry("Find survivor","worker"))
			elif world.camp_active:
				var due:=maxi(0,int(book.survivor_cost)-int(journal.survivor_wood))
				description="Rescue plot  ·  "+str(P.units(due))+" wood left"
				list.append(_entry("Find the rescue plot","rescue"))
			else:
				description="Found the camp to open the rescue plot."
				list.append(_entry("Find the hearth plot","home"))
			if world.camp_active:
				if Crew.owns_owl(journal):
					description+="\nOwl companion · "+str(journal.owl_hits)+" hits"
				else:
					list.append(_entry("Owl roost  ·  %d meat"%P.units(Crew.owl_due(journal)),Crew.OWL_PLOT))
		"Build":
			title.text="Build"
			description=""
			for id:String in book.costs:
				if not book.offer_open(id):continue
				if id in P.STORAGE and id!=P.next_storage(book):continue
				if id in P.LINES:continue
				list.append(_entry(P.TITLES[id]+"  ·  "+P.price_text(book.remaining(id)),id))
				if list.size()>=3:break
			if world.camp_active and not journal.survivor_paid and list.size()<3:
				list.append(_entry("Rescue survivor  ·  "+str(P.units(maxi(0,int(book.survivor_cost)-int(journal.survivor_wood))))+" wood","rescue"))
			if world.camp_active and not Crew.owns_owl(journal) and list.size()<3:
				list.append(_entry("Owl roost  ·  %d meat"%P.units(Crew.owl_due(journal)),Crew.OWL_PLOT))
			var inside:bool=world.camp_active and world.field_env.is_inside_camp(world.actor.global_position)
			if inside:
				for line:String in P.LINES:
					if book.offer_open(line):list.append(_entry(P.TITLES[line]+"  ·  "+P.price_text(book.remaining(line)),line))
			if world.camp_active:list.append(_entry("Move equipment","move"))
			if list.is_empty():description="All available camp purchases are complete."
	# Page long purchase lists within the visible, safe canvas in both Fold orientations.
	var safe:Rect2=hud._safe_rect()
	var target:=touch_height(safe)
	var description_height:=0. if description.is_empty() else 30.*description.split("\n").size()+7.
	if description.length()>45 and not description.contains("\n"):description_height+=24.
	var usable:=safe.size.y-170.-maxf(63.,target)-description_height
	var slots:=maxi(2,floori(usable/(maxf(57.,target)+5.)))
	if list.size()>slots:
		var per_page:=slots-1
		var pages:=ceili(float(list.size())/per_page)
		list_page=posmod(list_page,pages)
		list=list.slice(list_page*per_page,(list_page+1)*per_page)
		list.append(_entry("More  ·  %d of %d"%[list_page+1,pages],"list_next"))
	else:
		list_page=0
	var state:=str([tab,title.text,description,list])
	if sheet_key==state:return
	sheet_key=state
	subtitle.text=description
	subtitle.visible=not description.is_empty()
	for child in actions.get_children():
		actions.remove_child(child)
		child.queue_free()
	commands.clear()
	for item in list:
		var row:=Button.new()
		row.text=str(item[0])+"   ›"
		row.alignment=HORIZONTAL_ALIGNMENT_LEFT
		row.custom_minimum_size=Vector2(0,57)
		row.accessibility_name=item[0]
		row.mouse_filter=Control.MOUSE_FILTER_IGNORE
		row.add_theme_font_override("font",TYPE)
		row.add_theme_font_size_override("font_size",23)
		row.add_theme_color_override("font_color",INK)
		row.add_theme_color_override("font_hover_color",INK)
		var skin:=face(Color("#fffaf5"),Color("#dfd3c9"),8)
		skin.shadow_size=0
		skin.content_margin_left=15
		row.add_theme_stylebox_override("normal",skin)
		row.add_theme_stylebox_override("hover",skin)
		actions.add_child(row)
		commands.append([row,item[1]])
		row.pressed.connect(choose.bind(str(item[1])))
	reflow()

func choose(id:String)->void:
	if id=="list_next":
		list_page+=1
		refresh()
		return
	if id=="character_open":
		toggle("Characters")
		active_tab="Camp"
		return
	if id.begins_with("character_"):
		if world.set_player_character(id.trim_prefix("character_").to_int()):
			dismiss()
		return
	dismiss()
	if id=="storage_details":
		toggle("Storage")
		return
	if id=="move":
		world.camp_layout.open()
		return
	if id=="project":id=world.next_project if not str(world.next_project).is_empty() else "home"
	if id in P.LINES:
		var automation=world.settlement_loop.conveyors.menu
		if automation.selected!=id:automation.select(id)
	tracking=id
	tracking_name={"home":"Camp","depot":"Storehouse","worker":"Survivor","rescue":"Rescue plot",Crew.OWL_PLOT:"Owl roost"}.get(id,P.TITLES.get(id,"Camp"))
	if not world.camp_active and id=="home":tracking_name="Camp plot"
	if world.has_method("_refresh_hud_field"):world._refresh_hud_field(false)

func tracked_point()->Vector3:
	match tracking:
		"":return Vector3.INF
		"home":
			return Vector3(1.72,0,1.8) if world.camp_active else world.field_env.buy_anchor.global_position
		"depot":return world.depot.apron.global_position
		"worker":return world.survivor.actor.global_position
		"rescue":return world.settlement_loop.works.plot.global_position
		Crew.OWL_PLOT:
			if Crew.owns_owl(world.inventory.settlement):
				tracking=""
				return Vector3.INF
			return world.settlement_loop.works.owl_plot.global_position
	if not world.inventory.offer_open(tracking):
		tracking=""
		return Vector3.INF
	var node:Node3D=world.carry.receivers.get(tracking)
	return node.global_position if is_instance_valid(node) else Vector3.INF

func touch_height(safe:Rect2)->float:
	return 96. if safe.size.y>safe.size.x*1.65 else 76.

func reflow()->void:
	if not hud or not is_instance_valid(build) or not nav.is_inside_tree():return
	var safe:Rect2=hud._safe_rect()
	pack_button.position=hud.counts_area.position
	pack_button.size=hud.counts_area.size
	var maxw:=minf(safe.size.x,970.)
	var build_w:=clampf(maxw*.235,134.,197.)
	var nav_w:=minf(630.,maxw-build_w-14.)
	var h:=68.
	var target:=touch_height(safe)
	var x:=safe.get_center().x-(nav_w+build_w+14.)*.5
	var y:=safe.end.y-h
	if safe.size.x>1000.:x=safe.end.x-nav_w-build_w-14.
	nav.position=Vector2(x,y+3.)
	nav.size=Vector2(nav_w,h-6.)
	var used:=0.
	for key:String in tabs:
		var btn:Button=tabs[key]
		var w:=nav_w*({"Camp":.285,"Storage":.335,"Survivors":.380}[key] as float)
		btn.position=Vector2(used,safe.end.y-target-nav.position.y)
		btn.size=Vector2(w,target)
		used+=w
		var group:HBoxContainer=btn.get_node("TabLabel")
		group.position=Vector2(8.,-btn.position.y)
		group.size=Vector2(btn.size.x-16,nav.size.y-3)
		if btn.has_node("Divider"):
			var divider:ColorRect=btn.get_node("Divider")
			divider.position=Vector2(0,12.-btn.position.y)
			divider.size=Vector2(1,nav.size.y-24.)
		var active:ColorRect=btn.get_node("Active")
		active.position=Vector2(13.,nav.size.y-5.-btn.position.y)
		active.size=Vector2(btn.size.x-26.,3.)
		active.visible=active_tab==key
	build.position=Vector2(x+nav_w+14.,safe.end.y-target)
	build.size=Vector2(build_w,target)
	build_art.position=Vector2(0, y-1.-build.position.y)
	build_art.size=Vector2(build_w,h+2.)
	pack_button.size.y=target
	if not sheet.visible:return
	var panel_w:=minf(465.,safe.size.x-8.)
	var head_height:=maxf(63.,target)
	var desc_height:=0.
	if subtitle.visible:
		desc_height=30.*subtitle.text.split("\n").size()+7.
		if subtitle.text.length()>45 and not subtitle.text.contains("\n"):desc_height+=24.
	var row_height:=maxf(57.,target)
	var height:=head_height+desc_height+commands.size()*(row_height+5.)+14.
	height=minf(height,safe.size.y-156.)
	var left:=nav.position.x if tab!="Build" else build.position.x+build.size.x-panel_w
	sheet.position=Vector2(clampf(left,safe.position.x,safe.end.x-panel_w),nav.position.y-height-12.)
	sheet.size=Vector2(panel_w,height)
	title.position=Vector2(20,9)
	close.position=Vector2(panel_w-target,0.)
	close.size=Vector2(target,target)
	subtitle.position=Vector2(20,head_height-6.)
	subtitle.size=Vector2(panel_w-40,desc_height)
	for entry in commands:entry[0].custom_minimum_size.y=row_height
	actions.position=Vector2(14,head_height+desc_height)
	actions.size=Vector2(panel_w-28.,maxf(1.,height-head_height-desc_height-12.))

func _process(dt:float)->void:
	if not world or not world.get("field_ready"):return
	var enabled:bool=not world.camp_layout.active and not world.closing and not world.persist_blocked and world.reset_time<=0.
	visible=enabled
	if not enabled:
		finger=-2
		if not tab.is_empty():dismiss()
		return
	poll_time-=dt
	if poll_time<=0.:
		poll_time=.20
		if not tab.is_empty():refresh()

func _notification(what:int)->void:
	if what in [NOTIFICATION_APPLICATION_FOCUS_OUT,NOTIFICATION_APPLICATION_PAUSED,NOTIFICATION_WM_WINDOW_FOCUS_OUT]:
		finger=-2

func handle(event:InputEvent)->bool:
	if not visible or world.camp_layout.active:return false
	if event is InputEventKey and event.is_pressed() and not event.is_echo() and event.keycode==KEY_ESCAPE and not tab.is_empty():
		dismiss()
		return true
	if not (event is InputEventScreenTouch or event is InputEventScreenDrag or event is InputEventMouseButton):return false
	if event.device==InputEvent.DEVICE_ID_EMULATION:return false
	if event is InputEventMouseButton and event.button_index!=MOUSE_BUTTON_LEFT:return false
	var idx:int=event.index if event is InputEventScreenTouch or event is InputEventScreenDrag else -1
	if event is InputEventScreenTouch and event.canceled:
		if idx!=finger:return false
		finger=-2
		return true
	if idx==finger:
		if not event is InputEventScreenDrag and not event.pressed:finger=-2
		return true
	if event is InputEventScreenDrag or not event.pressed or finger!=-2:return false
	var pt:Vector2=event.position
	if sheet.visible and sheet.get_global_rect().has_point(pt):
		finger=idx
		if close.get_global_rect().has_point(pt):dismiss();return true
		for pair in commands:
			if pair[0].get_global_rect().has_point(pt):choose(str(pair[1]));break
		return true
	if pack_button.get_global_rect().has_point(pt):finger=idx;toggle("Pack");return true
	if build.get_global_rect().has_point(pt):finger=idx;toggle("Build");return true
	for key:String in tabs:
		if tabs[key].get_global_rect().has_point(pt):finger=idx;toggle(key);return true
	if not tab.is_empty():dismiss()
	return false
