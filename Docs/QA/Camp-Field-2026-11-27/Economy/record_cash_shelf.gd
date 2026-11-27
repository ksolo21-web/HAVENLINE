extends "res://tests/qa_personal_goods.gd"
## Record genuine, migrated sales with the normal gameplay camera and home.
func shot(path:String)->void:
	await process_frame
	RenderingServer.force_draw(false)
	root.get_texture().get_image().save_png(path)

func run()->void:
	var args:=OS.get_cmdline_user_args()
	var guard=Store.Profile.new()
	if not guard.configure(args):quit(2);return
	field=load("res://field_opening.tscn").instantiate()
	root.add_child(field)
	current_scene=field
	bank=field.inventory
	j=bank.settlement
	loop=field.settlement_loop
	park(field.depot.house.to_global(Vector3(0,0,1.06)))
	field.set_zoom_ratio(1.70)
	await ticks(55)
	var dest:=OS.get_environment("ECONOMY_CAPTURE")
	check("seven historical notes are present in the open storehouse",cash_on_shelf()==7 and bank.house_goods().money==7)
	await shot(dest.path_join("Cash-shelf-stocked.png"))
	var projected_labels:Array=[]
	for note:Node3D in loop.exchange.shelf_notes:
		var position_on_screen:Vector2=field.camera.unproject_position(note.global_position+Vector3.UP*.045)
		projected_labels.append([position_on_screen.x,position_on_screen.y])
	await at_bay("money")
	check("the actor collects all seven notes upon reaching their stocked bay",bank.hand_goods().money==7 and bank.house_goods().money==0)
	await ticks(63)
	check("the shelf is visibly empty and the actor owns the notes",cash_on_shelf()==0 and bank.hand_goods().money==7)
	await shot(dest.path_join("Cash-shelf-empty.png"))
	var file:=FileAccess.open(dest.path_join("Cash-shelf.json"),FileAccess.WRITE)
	file.store_string(JSON.stringify({"checks":results,"display_size":[root.size.x,root.size.y],"camera_zoom":1.70,"shelf_screen_positions":projected_labels,"shelf_position_local":[1.15,.746,-.77],"renderer":RenderingServer.get_video_adapter_name()},"  "))
	file.close()
	print("CASH_SHELF ",JSON.stringify(results))
	field.set_physics_process(false)
	await Session.drain_field_audio(self,field)
	field.queue_free()
	await process_frame
	quit(1 if false in results.values() else 0)
