extends SceneTree
var field
var camera:Camera3D
var origin:=Vector2.ZERO
var touch_held:=false
var last_input:=Vector2.ZERO
func _initialize()->void:
	call_deferred("run")


func touch(id:int,pos:Vector2,pressed:bool)->void:
	var e:=InputEventScreenTouch.new()
	e.index=id
	e.position=pos
	e.pressed=pressed
	root.push_input(e,true)


func steer(direction:Vector2)->void:
	if direction.is_zero_approx():
		if touch_held:
			touch(0,origin,false)
			touch_held=false
			last_input=Vector2.ZERO
		return
	if not touch_held:
		touch(0,origin,true)
		touch_held=true
	if last_input.distance_to(direction)<.006: return
	var e:=InputEventScreenDrag.new()
	e.index=0
	e.position=origin+direction*82.
	e.relative=(direction-last_input)*82.
	e.screen_relative=e.relative
	root.push_input(e,true)
	last_input=direction


func move_to(p:Array,tol:float)->bool:
	var pos:Vector3=field.actor.global_position
	var delta:=Vector3(float(p[0])-pos.x,0.,float(p[1])-pos.z)
	if delta.length()<=tol:
		steer(Vector2.ZERO);return true
	var right:=camera.global_basis.x
	var near:=right.cross(Vector3.UP)
	var d:=Vector2(delta.dot(right),delta.dot(near)).normalized()
	steer(d*clampf(delta.length()*1.25,.3,.98))
	return false


## Replay a real prior paid camp, including its seven already-earned banked notes.
const Guard=preload("res://opening_save.gd")
var dock
var checks:Dictionary={}
func check(label:String,value:bool)->void:
	checks[label]=value
	if not value:push_error(label)

func tap(at:Vector2)->void:
	for down in [true,false]:
		var event:=InputEventScreenTouch.new()
		event.index=2
		event.position=at
		event.pressed=down
		root.push_input(event,true)
		await physics_frame

func pick(id:String)->bool:
	await process_frame
	for entry in dock.commands:
		if entry[1]==id:
			await tap(entry[0].get_global_rect().get_center())
			return true
	return false

func photo(label:String)->void:
	var directory:=OS.get_environment("WAREHOUSE_EVIDENCE")
	if directory.is_empty():return
	RenderingServer.force_draw(false,0.)
	root.get_texture().get_image().save_jpg(directory.path_join(label+".jpg"),.9)

func walk_to(target:Vector3)->bool:
	for frame in 300:
		if move_to([target.x,target.z],.055):return true
		await physics_frame
	steer(Vector2.ZERO)
	return false

func run()->void:
	if not Guard.new().configure(OS.get_cmdline_user_args()):quit(2);return
	field=load("res://field_opening.tscn").instantiate()
	root.add_child(field)
	current_scene=field
	for i in 5:await physics_frame
	dock=field.opening_hud.camp_dock
	var book=field.inventory
	check("old earned cash remains in the storehouse",book.house_goods().money==7 and book.hand_goods().money==0)
	camera=field.camera
	origin=root.get_visible_rect().size*Vector2(.29,.70)
	field.actor.global_position=field.depot.apron.global_position
	for i in 6:await physics_frame
	await tap(dock.tabs.Storage.get_global_rect().get_center())
	check("storage tab shows cash and other inventory",dock.tab=="Storage" and "$7" in dock.subtitle.text and "wood" in dock.subtitle.text)
	check("stock detail has navigation and no withdrawal commands",dock.commands.any(func(row):return row[1]=="depot") and not dock.commands.any(func(row):return str(row[1]).begins_with("stock_")))
	await tap(dock.close.get_global_rect().get_center())
	var house=field.depot.house
	var exchange=field.settlement_loop.exchange
	check("walk through the warehouse door",await walk_to(house.to_global(Vector3(0,0,1.2))))
	check("walk into the warehouse aisle",await walk_to(house.to_global(Vector3(0,0,.20))))
	check("no transaction popup on entry",dock.tab.is_empty() and not dock.sheet.visible)
	photo("Enter-storehouse")
	check("player reaches the actual cash shelf",await walk_to(exchange.pickup_position("money")))
	for i in 85:await physics_frame
	check("seven notes collected in one stop",book.hand_goods().money==7 and book.house_goods().money==0)
	check("screen remains available for gameplay",dock.tab.is_empty() and not dock.sheet.visible)
	check("real carried cash on HUD",field.opening_hud.outputs.cash.text=="7")
	var pack=field.carry.finished_goods
	check("bounded authored note stack on rack",pack.visible and pack.pools.get("money",[]).size() in [1,2,3,4])
	check("ordinary shelf receipt remains protected during the visit",int(book.settlement.withdrawn.get("money",0))==7)
	dock.dismiss()
	photo("Shelf-cash-in-pack")
	await tap(dock.tabs.Camp.get_global_rect().get_center())
	check("character customization reachable",await pick("character_open"))
	for n in [2,3,4]:
		check("character %d selector"%n,await pick("character_"+str(n)) and field.player_character()==n)
		check("portrait matches selected character %d"%n,field.opening_hud.portrait.texture==field.opening_hud.PORTRAITS[n])
		if n!=4:
			await tap(dock.tabs.Camp.get_global_rect().get_center())
			await pick("character_open")
	await tap(dock.tabs.Camp.get_global_rect().get_center())
	await pick("character_open")
	check("original model can be reselected",await pick("character_1") and field.player_character()==1)
	print("CAMP_WAREHOUSE_CONTROLS ",JSON.stringify(checks))
	field.sound.stop_playback()
	for count in 12:
		OS.delay_msec(20)
		await process_frame
	field.queue_free()
	await process_frame
	await process_frame
	quit(int(checks.values().has(false)))
