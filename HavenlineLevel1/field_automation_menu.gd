extends Control
## Optional purchases share one active plot. Passing the workshops on foot
## can never authorize a purchase that the player hasn't selected.
const P=preload("res://field_progression.gd")
var world
var selected:=""
var expanded:=false
var launcher:=Button.new()
var choices:Dictionary={}
var finger:=-2

func install(host)->void:
	world=host
	name="AutomationUpgrades"
	mouse_filter=Control.MOUSE_FILTER_IGNORE
	set_anchors_and_offsets_preset(PRESET_FULL_RECT)
	var hud=world.opening_hud
	for id:String in ["",P.FOOD_LINE,P.SUPPLY_LINE]:
		var button:=launcher if id=="" else Button.new()
		add_child(button)
		button.focus_mode=Control.FOCUS_NONE
		button.mouse_filter=Control.MOUSE_FILTER_IGNORE
		hud._action(button,hud.NAVY,hud.AMBER,hud.WHITE)
		for state:String in ["normal","pressed","hover","hover_pressed"]:
			var skin:=button.get_theme_stylebox(state).duplicate() as StyleBoxFlat
			skin.expand_margin_top=0.
			skin.expand_margin_bottom=0.
			button.add_theme_stylebox_override(state,skin)
		if id!="":choices[id]=button
	launcher.text="Automate"
	launcher.accessibility_name="Choose optional conveyor upgrades"
	hide()

func _process(_dt:float)->void:
	if not world.field_ready:return
	var book=world.inventory
	var relevant:bool=(book.offer_open(P.FOOD_LINE) or book.offer_open(P.SUPPLY_LINE))
	visible=relevant and world.camp_active and world.field_env.is_inside_camp(world.actor.global_position) and not world.persist_blocked and world.reset_time<=0.
	if not visible:
		finger=-2
		expanded=false
		return
	var safe:Rect2=world.opening_hud._safe_rect()
	var beside:Rect2=world.camp_layout.overlay.launcher.get_rect()
	launcher.size=Vector2(128.,50.)
	launcher.position=beside.position-Vector2(launcher.size.x+8.,0)
	launcher.text="Close" if expanded else "Automate"
	var y:=launcher.position.y
	for id:String in P.LINES:
		var button:Button=choices[id]
		button.visible=expanded and book.offer_open(id)
		if not button.visible:continue
		button.text=("Cancel "+P.TITLES[id].to_lower()) if selected==id else P.TITLES[id]+" · "+P.price_text(book.remaining(id))
		button.add_theme_font_size_override("font_size",22)
		var width:=minf(maxf(button.get_minimum_size().x+28.,350.),safe.size.x)
		button.size=Vector2(width,53.)
		y-=62.
		button.position=Vector2(safe.end.x-width,y)

func select(id:String)->void:
	selected="" if selected==id else id
	expanded=false
	world._refresh_field()

func handle(event:InputEvent)->bool:
	if not is_visible_in_tree():return false
	if not (event is InputEventScreenTouch or event is InputEventMouseButton or event is InputEventScreenDrag):return false
	if event.device==InputEvent.DEVICE_ID_EMULATION:return false
	if event is InputEventMouseButton and event.button_index!=MOUSE_BUTTON_LEFT:return false
	var idx:int=event.index if event is InputEventScreenTouch or event is InputEventScreenDrag else -1
	if finger==idx:
		if not event is InputEventScreenDrag and not event.pressed:finger=-2
		return true
	if event is InputEventScreenDrag or not event.pressed or finger!=-2:return false
	var point:Vector2=event.position
	if expanded:
		for id:String in P.LINES:
			var btn:Button=choices[id]
			if btn.visible and btn.get_global_rect().has_point(point):
				finger=idx
				select(id)
				return true
	if launcher.get_global_rect().has_point(point):
		expanded=not expanded
		finger=idx
		return true
	expanded=false
	return false
