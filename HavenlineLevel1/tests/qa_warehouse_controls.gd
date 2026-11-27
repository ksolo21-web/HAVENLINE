extends SceneTree
## Replay a real prior paid camp, including its seven already-earned banked notes.
const Profile=preload("res://tests/lifecycle_test_profile.gd")
const Save=preload("res://field_save.gd")
const Guard=preload("res://opening_save.gd")
const SELF="res://tests/qa_warehouse_controls.gd"
const FIXTURE="res://tests/fixtures/storehouse-cash-build11.json"
var field
var dock
var checks:Dictionary={}
func _initialize()->void:
	call_deferred("run")

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

func run()->void:
	if not "--warehouse-ui" in OS.get_cmdline_user_args():
		var directory:=Profile.make_directory()
		if directory.is_empty():quit(2);return
		var file:=FileAccess.open(directory.path_join(Save.PRIMARY),FileAccess.WRITE)
		file.store_buffer(FileAccess.get_file_as_bytes(FIXTURE))
		file.close()
		var code:=Profile.child(SELF,directory,"--warehouse-ui")
		Profile.remove_owned(directory)
		quit(code)
		return
	if not Guard.new().configure(OS.get_cmdline_user_args()):quit(2);return
	field=load("res://field_opening.tscn").instantiate()
	root.add_child(field)
	current_scene=field
	for i in 5:await physics_frame
	dock=field.opening_hud.camp_dock
	var book=field.inventory
	check("old earned cash remains in the storehouse",book.house_goods().money==7 and book.hand_goods().money==0)
	# Start this focused touchscreen transaction on the public warehouse apron.
	field.actor.global_position=field.depot.apron.global_position
	for i in 4:await physics_frame
	for raw:String in book.KINDS:
		check("withdrawal amount matches available shelf for "+raw,dock._stock_amount(raw)==(field.carry.available_on_shelf(raw) if book.storage_open(raw) else 0))
	await tap(dock.tabs.Storage.get_global_rect().get_center())
	check("withdrawal is available on the loading apron",await pick("stock_open"))
	for i in 10:
		if dock.stock_kind=="money" or not await pick("stock_next"):break
	photo("Cash-withdrawal")
	check("cash page",dock.stock_kind=="money" and dock.title.text=="Cash")
	check("choose exact amount",await pick("stock_number") and dock.quantity_dialog.visible)
	photo("Exact-quantity")
	dock.quantity_input.text="3"
	dock.quantity_input.text_submitted.emit("3")
	for i in 5:await physics_frame
	check("confirm three cash",book.hand_goods().money==3 and book.house_goods().money==4)
	check("take every remaining note in one press",await pick("stock_all"))
	for i in 24:await physics_frame
	check("same visit keeps the whole withdrawal in pack",book.hand_goods().money==7 and book.house_goods().money==0)
	check("real carried cash on HUD",field.opening_hud.outputs.cash.text=="7")
	var pack=field.carry.finished_goods
	check("bounded authored note stack on rack",pack.visible and pack.pools.get("money",[]).size() in [1,2,3,4])
	check("raw-material ranks independent",field.carry.planned_counts.values().all(func(n):return n==0))
	dock.dismiss()
	photo("Cash-on-foot")
	await tap(dock.tabs.Camp.get_global_rect().get_center())
	check("character customization reachable",await pick("character_open"))
	check("character three selector",await pick("character_3") and field.player_character()==3)
	await tap(dock.tabs.Camp.get_global_rect().get_center())
	await pick("character_open")
	check("original model can be reselected",await pick("character_1") and field.player_character()==1)
	print("CAMP_WAREHOUSE_CONTROLS ",JSON.stringify(checks))
	await Profile.drain_field_audio(self,field)
	field.queue_free()
	await process_frame
	await process_frame
	quit(int(checks.values().has(false)))
