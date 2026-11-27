extends "res://tests/qa_personal_goods.gd"
## Warmup uses a real paid kitchen, genuine stock and four paid customers.
## After checkpoint, the two camera runs replay the same three meals/four notes.
func prepare()->void:
	field.counter.arrival_clock=180.
	await at_bay("meat")
	check("six earned raw inputs collected at their actual shelf",bank.carried.meat==6)
	park(anchor)
	await ticks(4)
	park(station_floor("meat"))
	check("four real servings picked from the paid cooker's output",await until(func():return j.held_meal==4,1500))
	park(anchor)
	await ticks(3)
	park(field.counter.service_point.global_position)
	await ticks(3)
	park(anchor)
	field.counter.arrival_clock=0.
	check("four portions actually sold",await until(func():return j.served==4 and bank.till_balance()==4,2200))
	park(station_floor("meat"))
	check("three remaining genuine cooked portions picked up",await until(func():return j.held_meal==3,1200))
	var start:Vector3=field.counter.service_point.global_position+Vector3.BACK*2.40
	park(start)
	await ticks(65)
	field._checkpoint_lifecycle()
	check("checkpoint contains four paid notes and three meals",bank.till_balance()==4 and j.held_meal==3)
	print("EXCHANGE_WARMUP ",JSON.stringify(results))

func view(dir:String, zoom:float)->void:
	var target:Vector3=field.counter.service_point.global_position
	var before:int=j.served
	var start:Vector3=target+Vector3.BACK*2.40
	park(start)
	field.set_zoom_ratio(zoom)
	await ticks(24)
	var frames:=0
	var first:=-1
	var last:=-1
	var airborne:=0
	var evidence:Array=[]
	for k in 155:
		if k>9 and k<65:move_to([target.x,target.z+.15],.06)
		else:steer(Vector2.ZERO)
		await physics_frame
		var visible_goods:=0
		for flight in loop.exchange.flights:
			if flight.mesh.is_visible_in_tree():visible_goods+=1
		airborne=maxi(airborne,visible_goods)
		if not loop.exchange.flights.is_empty():
			if first<0:first=k
			last=k
		if k%3==0:
			await process_frame
			RenderingServer.force_draw(false)
			var shot:=root.get_texture().get_image()
			shot.save_jpg(dir.path_join("%04d.jpg"%frames),.93)
			frames+=1
			evidence.append({"tick":k,"player_xz":[field.actor.position.x,field.actor.position.z],"airborne":visible_goods,"pack":bank.hand_goods(),"till":bank.till_balance(),"counter":j.counter_stock,"sold":j.served})
		# After the full transfer the FIFO may legitimately sell another plate.
	check("walk delivered three meals and collected four existing notes",j.pocket_cash>=4 and j.held_meal==0 and j.counter_stock+j.served==before+3)
	check("visible two-way exchange on screen",first>=0 and airborne>=4)
	var log:=FileAccess.open(dir.path_join("readback.json"),FileAccess.WRITE)
	log.store_string(JSON.stringify({"checks":results,"source_size":[root.size.x,root.size.y],"zoom":zoom,"renderer":RenderingServer.get_video_adapter_name(),"first_freight_tick":first,"last_freight_tick":last,"max_rendered_goods":airborne,"frame_stride":3,"physics_hz":60,"samples":evidence},"  "))
	log.close()
	print("EXCHANGE_VIEWS ",JSON.stringify(results))

func run()->void:
	var args:=OS.get_cmdline_user_args()
	var guard=Store.Profile.new()
	if not guard.configure(args):quit(2);return
	field=load("res://field_opening.tscn").instantiate()
	root.add_child(field)
	current_scene=field
	camera=field.camera
	origin=root.get_visible_rect().size*Vector2(.3,.70)
	bank=field.inventory
	j=bank.settlement
	loop=field.settlement_loop
	if "--exchange-warmup" in args:await prepare()
	else:await view(OS.get_environment("ECONOMY_FRAME_DIR"),float(OS.get_environment("ECONOMY_ZOOM")))
	field.set_physics_process(false)
	await Session.drain_field_audio(self,field)
	field.queue_free()
	await process_frame
	quit(1 if false in results.values() else 0)
