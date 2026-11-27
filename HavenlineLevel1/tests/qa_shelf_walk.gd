extends "res://tests/qa_personal_goods.gd"
## Physical cashier earnings and ordinary controller movement in the field scene.
var measured:Dictionary={}
var exchange
var house
var frame_dir:=OS.get_environment("WAREHOUSE_WALK_CAPTURE")
var take_frames:=false
var frame_number:=0
var capture_tick:=0

func film_tick()->void:
	if not take_frames or frame_dir.is_empty():return
	if capture_tick%4==0:
		RenderingServer.force_draw(false)
		root.get_texture().get_image().save_jpg(frame_dir.path_join("walk-%03d.jpg"%frame_number),.90)
		frame_number+=1
	capture_tick+=1

func photo(label:String)->void:
	if frame_dir.is_empty():return
	await process_frame
	RenderingServer.force_draw(false)
	root.get_texture().get_image().save_jpg(frame_dir.path_join(label+".jpg"),.96)

func walk_stop(at:Vector3, settle:=true)->bool:
	var reached:=false
	for i in 240:
		if move_to([at.x,at.z],.055):
			reached=true
			break
		await physics_frame
	steer(Vector2.ZERO)
	if settle:await ticks(24)
	if not reached:print("WALK_BLOCK goal=",house.to_local(at)," actual=",house.to_local(field.actor.global_position)," house=",house.global_position)
	return reached

func center_aisle()->bool:
	return await walk_stop(house.to_global(Vector3(0,0,.20)),false)

func take_shelf(kind:String)->void:
	await center_aisle()
	var count:int=exchange._shelf_amount(kind)
	var before:int=bank.carried[kind] if kind in bank.KINDS else bank.hand_goods()[kind]
	var at:Vector3=exchange.pickup_position(kind)
	var reached:=await walk_stop(at)
	var after:int=bank.carried[kind] if kind in bank.KINDS else bank.hand_goods()[kind]
	check(kind+" taken with ordinary movement at its own stocked bay",count>0 and reached and after==before+count and exchange._shelf_amount(kind)==0 and exchange.bay_at(field.actor.global_position)==kind)
	measured[kind]={"before":before,"available":count,"carried_after":after,"local_floor":str(house.to_local(field.actor.global_position))}
	if not reached or after!=before+count:print("BAY_MISS ",kind," actual=",house.to_local(field.actor.global_position)," goal=",house.to_local(at)," selected=",exchange.bay_at(field.actor.global_position)," balances=",bank.hand_goods(),"/",bank.carried)

func enter()->void:
	var door:Vector3=house.to_global(Vector3(0,0,1.2))
	check("centered doorway traversed on foot",await walk_stop(door,false) and await center_aisle())

func tap_item(kind:String)->void:
	var screen:Vector2=field.camera.unproject_position(exchange._shelf(kind)+Vector3.UP*.06)
	for pressed in [true,false]:
		var event:=InputEventScreenTouch.new()
		event.index=5
		event.position=screen
		event.pressed=pressed
		root.push_input(event,true)
		await physics_frame

func full_run()->void:
	# The finite test stock comes from one collected receipt per bundle; each
	# staged product debits raw once. Live and restart self-check conservation.
	field.counter.arrival_clock=10000.
	for raw:String in bank.KINDS:
		for i in 7:
			bank.collect("house-foot-"+raw+str(i),raw)
			bank.deposit(raw)
	for kind:String in ["planks","blocks","meal"]:
		var raw:String=exchange.RAW_FOR[kind]
		bank.stored[raw]-=3
		j.product_store[kind]+=3
		if kind=="meal":j.cooked+=3
		else:j["processed_"+raw]+=3
	field._inventory_changed()
	check("fixture is balanced on the ordinary inventory",not field.persist_blocked)
	# Tender a finished roast and see a genuine staffed customer pay, then
	# carry that note to the house. No cash is assigned by the harness.
	park(station_floor("meat"))
	await ticks(4)
	park(field.counter.service_point.global_position)
	await ticks(8)
	park(anchor)
	field.counter.arrival_clock=0.
	check("first genuine diner paid",await until(func():return j.served==1,1100))
	await ticks(66)
	park(field.counter.service_point.global_position)
	await ticks(4)
	check("actual note picked up at registered counter",j.pocket_cash==1)
	park(house.to_global(Vector3(0,0,3.1)))
	for n in 4:bank.collect("passer-timber-"+str(n),"wood")
	field.carry.sync(true)
	var older:int=bank.stored.wood
	await walk_stop(field.depot.apron.global_position)
	await ticks(75)
	check("outside visit unloads the carried raw lumber and earned money",bank.stored.wood==older+4 and j.house_cash==1 and bank.carried.wood==0 and j.pocket_cash==0)
	check("cash cannot be directly withdrawn from the exterior approach",not loop.withdraw_goods("money"))
	await enter()
	for kind:String in ["wood","planks","stone","blocks","slate","meat","meal","metal","coal","money"]:
		await take_shelf(kind)
	check("all ten withdrawals remain protected during this visit",j.withdrawn.size()==10)
	await center_aisle()
	await walk_stop(house.to_global(Vector3(0,0,1.30)),false)
	await walk_stop(field.depot.apron.global_position)
	await ticks(60)
	check("walking out through the unloading door retains every withdrawn family",j.withdrawn.size()==10 and j.pocket_cash==1 and bank.carried.wood==older+4)
	await walk_stop(house.to_global(Vector3(0,0,4.7)))
	await walk_stop(field.depot.apron.global_position)
	await ticks(120)
	await enter()
	# Two vertically separated stocked meshes on one timber rack. Direct
	# world touch can select the lower stack without lifting the upper one.
	await walk_stop(house.to_global(Vector3(-.50,0,.22)),false)
	var boards:int=bank.house_goods().planks
	var logs:int=bank.stored.wood
	# The second finger of a camera gesture can land on a displayed bundle.
	# Neither its release nor a stationary pinch is a stock selection.
	var board_screen:Vector2=field.camera.unproject_position(exchange._shelf("planks")+Vector3.UP*.06)
	var first:=board_screen+Vector2(-80,44)
	for row in [[4,first,true],[5,board_screen,true],[5,board_screen,false],[4,first,false]]:
		touch(row[0],row[1],row[2])
	await physics_frame
	check("two-finger camera gesture over stock takes nothing and releases both fingers",bank.house_goods().planks==boards and bank.stored.wood==logs and field.trial_camera.fingers.is_empty())
	await tap_item("planks")
	check("touching lower timber stock takes only its planks",boards>0 and j.hand_products.planks==boards and bank.stored.wood==logs and bank.carried.wood==0)
	await tap_item("planks")
	check("retapping the emptied lower tray leaves adjacent stock on its shelf",bank.stored.wood==logs and j.hand_products.planks==boards)
	await tap_item("wood")
	check("touching the upper stock retrieves its own real logs",logs>0 and bank.carried.wood==logs and bank.stored.wood==0)
	field._checkpoint_lifecycle()

func starter()->void:
	for id:String in [P.FIRST,"storage_wood"]:
		for raw:String in bank.remaining(id):
			var due:int=bank.remaining(id)[raw]
			for i in due:
				bank.collect("starter-house14-"+id+raw+str(i),raw)
				bank.payment(id,raw,false)
		field._finish_purchase(id)
	field._apply_hearth(true,false)
	field.reveal_countdown=-1.
	field._inventory_changed()
	park(house.to_global(Vector3(0,0,2.35)))
	for i in 4:bank.collect("starter-stock-"+str(i),"wood")
	field.carry.sync(true)
	await ticks(100)
	check("starter shell admits stocked timber before higher tiers",house.tier==1 and bank.stored.wood>=4)
	await enter()
	await take_shelf("wood")
	var held:int=bank.carried.wood
	await walk_stop(exchange.pickup_position("stone"))
	check("a closed mineral bay cannot dispense timber or unlock itself",not bank.storage_open("stone") and held==bank.carried.wood and bank.carried.stone==0)

func connected_cash()->void:
	check("connected house retained seven previously paid dollars",bank.complete(P.FOOD_LINE) and bank.complete(P.SUPPLY_LINE) and j.house_cash==7 and j.pocket_cash==0)
	var start:Vector3=house.to_global(Vector3(0,0,2.35))
	park(start)
	await ticks(18)
	await enter()
	await photo("01-stocked-before")
	var dest:Vector3=exchange.pickup_position("money")
	if not frame_dir.is_empty():
		physics_frame.connect(film_tick)
		take_frames=true
	check("right rear cash shelf reached by walking in a live connected camp",await walk_stop(dest))
	check("seven real notes collected without opening any interface",j.pocket_cash==7 and j.house_cash==0 and exchange.bay_at(field.actor.global_position)=="money")
	await ticks(44)
	take_frames=false
	await photo("02-money-on-back")
	field._checkpoint_lifecycle()

func cold_cash()->void:
	var pos:Vector3=exchange.pickup_position("money")
	check("connected camp restores player physically beside their empty cash shelf",field.actor.global_position.distance_to(pos)<.21 and j.pocket_cash==7 and j.house_cash==0)
	await walk_stop(house.to_global(Vector3(0,0,.22)),false)
	await walk_stop(house.to_global(Vector3(0,0,1.25)),false)
	await walk_stop(field.depot.apron.global_position)
	await ticks(40)
	check("cold return to same door keeps the withdrawn notes",j.pocket_cash==7 and bank.house_goods().money==0)
	await walk_stop(house.to_global(Vector3(0,0,4.7)))
	await ticks(4)
	check("a complete exit ends that protected visit",j.withdrawn.is_empty())
	await walk_stop(field.depot.apron.global_position)
	await ticks(30)
	check("coming back to the exterior deposits exactly seven",j.pocket_cash==0 and j.house_cash==7)
	# A purchased utility outfeed can reserve wood while the player heads
	# indoors. Only unreserved stock may become the player's property.
	var finished_before:int=j.processed_wood
	for i in 18:bank.collect("connected-bay-public-"+str(i),"wood")
	field.carry.sync(true)
	await ticks(115)
	await enter()
	var at:Vector3=exchange.pickup_position("wood")
	check("live connected timber rack can be approached on foot",await walk_stop(at))
	check("player and autonomous saw receive disjoint parts of the same real load",j.withdrawn.get("wood",0)==bank.carried.wood and bank.carried.wood>0 and bank.carried.wood<18 and j.processed_wood>finished_before)

func run()->void:
	var args:=OS.get_cmdline_user_args()
	if not Store.Profile.new().configure(args):quit(2);return
	field=load("res://field_opening.tscn").instantiate()
	root.add_child(field)
	current_scene=field
	bank=field.inventory
	j=bank.settlement
	loop=field.settlement_loop
	house=field.depot.house
	exchange=loop.exchange
	camera=field.camera
	origin=root.get_visible_rect().size*Vector2(.38,.70)
	if not frame_dir.is_empty():field.set_zoom_ratio(float(OS.get_environment("WAREHOUSE_WALK_ZOOM")))
	for arg in args:
		match arg:
			"--walk-shelf=full":await full_run()
			"--walk-shelf=starter":await starter()
			"--walk-shelf=money":await connected_cash()
			"--walk-shelf=cold":await cold_cash()
	check("normal live receipt conserves every raw and finished item",not field.persist_blocked and bank.restore(bank.snapshot()))
	print("SHELF_WALK ",JSON.stringify({"checks":results,"floor":measured,"position":str(field.actor.global_position),"money":bank.hand_goods().money}))
	field.set_physics_process(false)
	await Session.drain_field_audio(self,field)
	field.queue_free()
	await process_frame
	quit(1 if false in results.values() or results.size()<2 else 0)
